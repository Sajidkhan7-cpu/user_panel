"""
services/llm_service.py
Optional AI (LLM) layer, called through the OpenAI Python SDK.

Works with ANY provider that offers an OpenAI-compatible endpoint — not
just OpenAI itself. This project defaults to Google Gemini's free tier
(no credit card required), since OpenAI's API has no free tier. Swap
providers anytime by changing OPENAI_BASE_URL / OPENAI_API_KEY /
OPENAI_MODEL in .env — no code changes needed.

  - Google Gemini (default, free):
      OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
      OPENAI_MODEL=gemini-2.5-flash
      Get a key (no card): https://aistudio.google.com/apikey

  - Groq (also free, very fast, open models):
      OPENAI_BASE_URL=https://api.groq.com/openai/v1
      OPENAI_MODEL=llama-3.3-70b-versatile
      Get a key (no card): https://console.groq.com/keys

  - OpenAI (paid, requires billing set up):
      OPENAI_BASE_URL=   (leave blank — uses OpenAI's default endpoint)
      OPENAI_MODEL=gpt-5.4-mini
      Get a key: https://platform.openai.com/api-keys

This is used ONLY as a fallback — when the rule-based keyword/FAQ engine
in chatbot_service.py can't classify a question at all. Precise facts
(fees, seats, eligibility %) are always answered by the rule-based engine
directly from the database, never by the LLM, so numbers can't be
hallucinated.

To enable:
  1. pip install openai   (already in requirements.txt)
  2. Set OPENAI_API_KEY (and OPENAI_BASE_URL/OPENAI_MODEL if needed) in .env
  3. USE_LLM_FALLBACK=True in backend/.env (this is the default)

If OPENAI_API_KEY is blank, this module safely no-ops and the chatbot
keeps working on rules + FAQ only, with zero external calls and zero cost.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.course import Course
from app.models.faq import FAQ

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are the admissions enquiry assistant for Greenfield Institute of Technology.

Answer the student's question in a warm, concise way (2-4 sentences max).

CRITICAL RULE: only use the facts listed below. Never invent or guess at
fees, seat counts, eligibility percentages, or dates. If the answer isn't
contained in the data below, say you don't have that specific information
and suggest the student contact the admissions office at
admissions@college.edu.in or +91-9876543210.

--- COLLEGE DATA ---
{context}
--- END COLLEGE DATA ---
"""


def _build_context(db: Session) -> str:
    """Formats current courses & FAQs as plain text for the LLM prompt."""
    courses = db.query(Course).all()
    faqs = db.query(FAQ).all()

    lines = ["COURSES:"]
    for c in courses:
        line = (
            f"- {c.name} ({c.short_code or 'N/A'}): {c.duration_years}-year program. "
            f"Eligibility: {c.eligibility_percentage}%"
            + (f" ({c.eligibility_note})" if c.eligibility_note else "")
            + f". Seats: {c.available_seats}/{c.total_seats} available. "
            f"Admission fee: ₹{c.admission_fee}. Fees/year: ₹{c.fees_per_year}. "
            f"Total fees: ₹{c.total_fees}."
        )
        if c.scholarship_available:
            line += f" Scholarship: {c.scholarship_available}."
        lines.append(line)

    if faqs:
        lines.append("\nFREQUENTLY ASKED QUESTIONS:")
        for f in faqs:
            lines.append(f"Q: {f.question}\nA: {f.answer}")

    return "\n".join(lines)


def is_llm_available() -> bool:
    """True only if the feature is enabled AND an API key is configured."""
    return bool(settings.USE_LLM_FALLBACK and settings.OPENAI_API_KEY.strip())


def generate_llm_reply(db: Session, message: str) -> Optional[str]:
    """
    Calls the OpenAI API with the student's question, grounded in real
    course/FAQ data. Returns None (never raises) if the LLM is disabled,
    unconfigured, or the API call fails for any reason — callers should
    fall back to the rule-based DEFAULT_REPLY in that case.
    """
    if not is_llm_available():
        return None

    try:
        # Imported lazily so the package is only required when this
        # feature is actually used.
        from openai import OpenAI
    except ImportError:
        logger.warning("openai package not installed — run: pip install openai")
        return None

    try:
        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL.strip():
            client_kwargs["base_url"] = settings.OPENAI_BASE_URL.strip()

        client = OpenAI(**client_kwargs)
        context = _build_context(db)
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            max_tokens=250,
            temperature=0.4,
        )
        reply = response.choices[0].message.content
        return reply.strip() if reply else None

    except Exception as exc:  # noqa: BLE001 — any API/network error should degrade gracefully
        logger.warning("LLM fallback call failed: %s", exc)
        return None
