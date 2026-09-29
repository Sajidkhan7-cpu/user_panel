"""
services/llm_service.py
Optional AI layer via the OpenAI SDK (works with Gemini / Groq / OpenAI —
just change OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL in .env).

The LLM does TWO jobs, and never invents facts:

  1. polish_reply()       Takes an exact, database-built answer and rewrites it
                          in a warm human voice. Numbers are verified afterwards;
                          if any number changed, the original answer is used.
  2. generate_llm_reply() Last-resort fallback for chit-chat / odd questions,
                          grounded in course + FAQ data and recent chat history.

Optional .env / config settings (all have defaults, nothing breaks if absent):
  USE_LLM_HUMANIZE=True   COLLEGE_NAME   BOT_NAME   CONTACT_EMAIL   CONTACT_PHONE
"""
import json
import logging
import re
from typing import List, Optional, Sequence, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.models.course import Course
from app.models.faq import FAQ

logger = logging.getLogger(__name__)

COLLEGE_NAME = getattr(settings, "COLLEGE_NAME", "Vivek College of Commerce")
BOT_NAME = getattr(settings, "BOT_NAME", "Vivi")
CONTACT_EMAIL = getattr(settings, "CONTACT_EMAIL", "admissions@college.edu.in")
CONTACT_PHONE = getattr(settings, "CONTACT_PHONE", "+91-9876543210")

SYSTEM_PROMPT_TEMPLATE = """You are {bot}, a friendly and sharp admissions counsellor at {college}.
You chat like a real person, not a brochure.

STYLE
- Warm, natural, conversational. 2-4 short sentences. Contractions are good. At most one emoji.
- Mirror the student's language (English, Hindi or Hinglish).
- If the student shares a worry (low marks, tight budget, confusion), acknowledge it kindly first.
- Casual chit-chat: answer briefly and kindly, then gently steer back to admissions.
- Do NOT end with a list of follow-up questions; suggestion buttons are shown separately.

FACT RULES (critical)
- Use ONLY the facts below. Never invent or guess fees, seats, eligibility %, dates or policies.
- If the answer isn't in the data, say you don't have that detail and point them to the admissions
  office: {email} or {phone}.
- If they ask about a course that is not listed, say we don't currently offer it and mention the
  closest listed courses that still have seats.

--- COLLEGE DATA ---
{context}
--- END COLLEGE DATA ---
"""

POLISH_PROMPT = """You are {bot}, a friendly admissions counsellor at {college}.
Rewrite the DRAFT answer so it sounds like a helpful human replying in chat.

RULES
- Keep EVERY number, rupee amount, percentage, email and phone number exactly as written.
- Do not add, remove or change any fact. Do not invent anything.
- Keep line breaks and bullet/numbered lists if the draft has them; just make the wording warmer.
- Do not add follow-up questions or suggestions (shown separately as buttons).
- Mirror the student's language (English / Hindi / Hinglish). At most one emoji.
- Output only the rewritten reply, nothing else.
"""


def _build_context(db: Session) -> str:
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
    return bool(settings.USE_LLM_FALLBACK and settings.OPENAI_API_KEY.strip())


def _complete(messages: list, max_tokens: int, temperature: float) -> Optional[str]:
    """Single place that talks to the API. Never raises."""
    if not is_llm_available():
        return None
    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai package not installed — run: pip install openai")
        return None
    try:
        kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL.strip():
            kwargs["base_url"] = settings.OPENAI_BASE_URL.strip()
        client = OpenAI(**kwargs)
        resp = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = resp.choices[0].message.content
        return text.strip() if text else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM call failed: %s", exc)
        return None


def _history_messages(history: Optional[Sequence[Tuple[str, str]]]) -> list:
    msgs = []
    for q, a in (history or []):
        if q:
            msgs.append({"role": "user", "content": q})
        if a:
            msgs.append({"role": "assistant", "content": a})
    return msgs


def _numbers(text: str) -> set:
    return {n.replace(",", "").rstrip(".") for n in re.findall(r"\d[\d,]*\.?\d*", text)}


def polish_reply(message: str, draft: str, history=None) -> Optional[str]:
    """Humanises a database-built answer. Returns None if unavailable or if any number changed."""
    if not getattr(settings, "USE_LLM_HUMANIZE", True):
        return None
    system = POLISH_PROMPT.format(bot=BOT_NAME, college=COLLEGE_NAME)
    user = f"Student asked: {message}\n\nDRAFT:\n{draft}"
    new = _complete(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=600, temperature=0.6,
    )
    if not new:
        return None
    # Safety net: every number in the draft must still be in the rewrite.
    if not _numbers(draft) <= _numbers(new):
        logger.info("Humanize rejected: numbers changed. Using original draft.")
        return None
    return new


def generate_llm_reply(db: Session, message: str, history=None) -> Optional[str]:
    """Grounded fallback answer with short conversation memory. Returns None on any failure."""
    if not is_llm_available():
        return None
    system = SYSTEM_PROMPT_TEMPLATE.format(
        bot=BOT_NAME, college=COLLEGE_NAME, email=CONTACT_EMAIL, phone=CONTACT_PHONE,
        context=_build_context(db),
    )
    messages = [{"role": "system", "content": system}]
    messages += _history_messages(history)
    messages.append({"role": "user", "content": message})
    return _complete(messages, max_tokens=500, temperature=0.5)


FOLLOWUP_PROMPT = """You help an admissions chatbot for {college}.
Given the student's question, the bot's answer and the college data, write {n} short follow-up
questions the student is most likely to ask NEXT.

RULES
- Each question is under 10 words, natural, and directly related to the topic just discussed.
- Use exact course names from the data. Only ask things answerable from the data
  (fees, seats, eligibility, scholarship, admission process, documents, contact).
- If the course discussed is full or not offered, ask about a similar course that has seats.
- Never repeat the question the student just asked.
- Output ONLY a JSON array of strings, nothing else.

--- COLLEGE DATA ---
{context}
--- END COLLEGE DATA ---
"""


def generate_followups(db: Session, message: str, reply: str, n: int = 3) -> Optional[List[str]]:
    """AI-written related questions. Opt-in: set USE_LLM_SUGGESTIONS=True (adds one LLM call per reply)."""
    if not getattr(settings, "USE_LLM_SUGGESTIONS", False):
        return None
    system = FOLLOWUP_PROMPT.format(college=COLLEGE_NAME, n=n, context=_build_context(db))
    user = f"Student asked: {message}\nBot answered: {reply}"
    raw = _complete(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        max_tokens=250, temperature=0.7,
    )
    if not raw:
        return None
    try:
        raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
        items = json.loads(raw)
        cleaned = [q.strip() for q in items if isinstance(q, str) and 3 <= len(q.strip()) <= 80]
        return cleaned[:n] or None
    except (ValueError, TypeError):
        return None