"""
services/chatbot_service.py — the "brain".

Pipeline
 1. Classify intent (word-boundary keyword match; greeting/thanks only if nothing else matches)
 2. Detect the course: from the message, or from the conversation so far ("and its fees?")
 3. If the student names a course we DON'T offer -> say so + suggest related courses
 4. Build an exact answer from the DB (fees / seats / eligibility / admission / courses)
 5. If the course is FULL -> add related courses that still have seats
 6. FAQ table -> course summary -> LLM fallback -> default message
 7. Optional: LLM rewrites the DB answer in a human voice (numbers verified, never changed)
 8. Attach follow-up suggestion chips

Returns: (reply, intent, suggestions)
"""
import random
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.chat import ChatHistory
from app.models.course import Course
from app.models.faq import FAQ
from app.services.llm_service import (
    BOT_NAME, COLLEGE_NAME, CONTACT_EMAIL, CONTACT_PHONE,
    generate_followups, generate_llm_reply, polish_reply,
)
from app.services.nlp import best_match, clean_text, extract_percentage
from app.services.suggestion_service import (
    build_suggestions, course_tokens, normalize_tokens, related_courses_ex,
)
from app.utils.helper import format_currency

# ---------------------------------------------------------------------------
# Intents
# ---------------------------------------------------------------------------
INTENT_KEYWORDS = {
    "greeting": ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"],
    "thanks": ["thank", "thanks", "thank you", "ok thanks", "great"],
    "seats": ["seat", "seats", "vacancy", "vacancies", "available seat", "seats left", "seats available"],
    "fees": ["fee", "fees", "cost", "price", "tuition", "charges", "how much", "scholarship",
             "installment", "instalment", "refund", "concession"],
    "eligibility": ["percentage", "eligibility", "eligible", "marks", "cutoff", "cut off", "qualify",
                    "minimum marks", "required percentage"],
    "admission": ["admission", "apply", "enroll", "enrol", "registration", "how to join",
                  "join college", "admission process"],
    "courses": ["course", "courses", "branch", "branches", "program", "programs", "programme",
                "specialization", "stream", "streams"],
    "contact": ["contact", "phone number", "email", "address", "location", "reach", "call"],
}
SOCIAL = ("greeting", "thanks")
COURSE_INTENTS = {"fees", "seats", "eligibility", "admission"}


def _compile(kws):
    # short words ("hi", "fee") need whole-word match so "which"/"feel" don't trigger them
    return [re.compile(rf"\b{re.escape(k)}\b" if len(k) <= 3 else rf"\b{re.escape(k)}") for k in kws]


_PATTERNS = {intent: _compile(kws) for intent, kws in INTENT_KEYWORDS.items()}


def classify_intent(message: str) -> str:
    text = clean_text(message)
    for intent, pats in _PATTERNS.items():
        if intent not in SOCIAL and any(p.search(text) for p in pats):
            return intent
    for intent in SOCIAL:  # "hi, fees for MBA?" should be answered as fees, not as a greeting
        if any(p.search(text) for p in _PATTERNS[intent]):
            return intent
    return "unknown"


_GENERIC_ASK = re.compile(r"\b(which|any|all|other)\s+(courses?|programs?|branches)\b")
_ABOUT = re.compile(r"\b(about|details?|info|information|overview)\b")
_FEE_POLICY = re.compile(r"installment|instalment|scholarship|refund|concession|discount|payment")

# Distinctive degree / stream words used to notice a course we don't offer.
_DEGREE_WORDS = {"btech", "mtech", "bsc", "msc", "bcom", "mcom", "bba", "bca", "mba", "mca",
                 "mbbs", "bds", "bpharm", "mpharm", "llb", "llm", "barch", "bed", "pgdm",
                 "bams", "bhms", "bms"}
_STREAM_WORDS = {"mechanical", "civil", "electrical", "electronics", "chemical", "cse", "ece",
                 "eee", "aiml", "cyber", "pharmacy", "nursing", "law", "architecture",
                 "journalism", "psychology", "agriculture", "aviation", "hotel"}


# ---------------------------------------------------------------------------
# Course detection
# ---------------------------------------------------------------------------
def _match_course(courses: List[Course], message: str) -> Tuple[Optional[Course], float]:
    if not courses:
        return None, 0
    lookup = {}
    for c in courses:
        lookup[c.name.lower()] = c
        if c.short_code:
            lookup[c.short_code.lower()] = c
    match_str, score = best_match(clean_text(message), list(lookup.keys()))
    if score >= 60:
        return lookup[match_str], score
    return None, score


def find_course(db: Session, message: str, courses: Optional[List[Course]] = None) -> Optional[Course]:
    courses = courses if courses is not None else db.query(Course).all()
    return _match_course(courses, message)[0]


def _unavailable_terms(message: str, courses: List[Course]) -> List[str]:
    """Degree/stream words in the message that no course in our DB contains."""
    asked = normalize_tokens(message) & (_DEGREE_WORDS | _STREAM_WORDS)
    if not asked:
        return []
    known = set()
    for c in courses:
        known |= course_tokens(c)
    return sorted(asked - known)


# ---------------------------------------------------------------------------
# Conversation memory (uses the ChatHistory table you already have)
# ---------------------------------------------------------------------------
def _load_history(db: Session, session_id: Optional[str], limit: int = 6) -> List[ChatHistory]:
    if not session_id:
        return []
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


def _last_context(history: List[ChatHistory], courses: List[Course]):
    last_intent = history[-1].intent if history else None
    for h in reversed(history):
        c, _ = _match_course(courses, h.question or "")
        if c is not None:
            return c, last_intent
    return None, last_intent


# ---------------------------------------------------------------------------
# Small human touches
# ---------------------------------------------------------------------------
def _pick(*options: str) -> str:
    return random.choice(options)


def _time_greeting() -> str:
    hour = datetime.now(timezone(timedelta(hours=5, minutes=30))).hour  # IST
    return "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"


def greeting_reply() -> str:
    return _pick(
        f"{_time_greeting()}! 👋 I'm {BOT_NAME} from {COLLEGE_NAME}. Ask me anything about courses, fees, seats or eligibility.",
        f"Hey there! I'm {BOT_NAME}, your admissions buddy at {COLLEGE_NAME}. What would you like to know?",
        f"Hi! 😊 {BOT_NAME} here. Looking for a course, fee details or seat availability? I've got you.",
    )


def thanks_reply() -> str:
    return _pick(
        "You're most welcome! 😊 I'm right here if anything else comes to mind.",
        "Happy to help! Good luck with your admission journey 🎓",
        "Anytime! Ask away if you'd like to know anything else.",
    )


def contact_reply() -> str:
    return (
        f"Sure! You can reach our admission office at {CONTACT_EMAIL} or call {CONTACT_PHONE}. "
        "They're available Monday to Saturday, 9 AM to 5 PM."
    )


DEFAULT_REPLY = (
    "Hmm, I didn't quite catch that 🤔 I can help with courses, fees, seat availability, "
    "eligibility and the admission process. Try something like 'Fees for MBA' or 'Seats in BCA'."
)


def _alt_lines(alts: List[Course]) -> str:
    return "\n".join(
        f"• {c.name} — {c.available_seats} seats open, {format_currency(c.fees_per_year)}/year, "
        f"min {c.eligibility_percentage}%"
        for c in alts
    )


def _full_note(db: Session, courses: List[Course], course: Course) -> str:
    """Empty if seats are open; otherwise suggests related courses that still have seats."""
    if (course.available_seats or 0) > 0:
        return ""
    alts, close = related_courses_ex(db, course, 3, courses)
    note = f"\n\nHeads-up: {course.name} is full right now."
    if alts:
        note += (
            " These similar courses still have seats:\n" if close
            else " These courses still have seats and might interest you:\n"
        ) + _alt_lines(alts)
    return note


# ---------------------------------------------------------------------------
# Answer builders (all facts come straight from the database)
# ---------------------------------------------------------------------------
def answer_fees(course: Optional[Course]) -> str:
    if course is None:
        return ("Happy to help with fees! Which course do you have in mind? "
                "For example: 'Fees for B.Tech CSE'.")
    reply = (
        f"{_pick('Sure!', 'Of course!', 'Here you go.')} Fees for {course.name} ({course.duration_years} years):\n"
        f"• Admission/registration fee: {format_currency(course.admission_fee)} (one-time)\n"
        f"• Fee per year: {format_currency(course.fees_per_year)}\n"
        f"• Total course fees: {format_currency(course.total_fees)}"
    )
    if course.scholarship_available:
        reply += f"\n• Scholarship: {course.scholarship_available}"
    reply += (
        "\n\nFee condition: the admission fee must be paid at the time of admission to confirm "
        "your seat; the remaining fees can be paid year-wise/semester-wise as per the college fee "
        "schedule. Fees once paid are non-refundable after the seat is confirmed, except as per "
        "the official refund policy."
    )
    return reply


def answer_seats(db: Session, courses: List[Course], course: Optional[Course]) -> str:
    if course is None:
        if not courses:
            return "Seat details aren't available right now. Please check back soon."
        lines = ["Here's where seats stand right now:"]
        for c in courses:
            status = "FULL" if (c.available_seats or 0) <= 0 else f"{c.available_seats}/{c.total_seats} open"
            lines.append(f"• {c.name}: {status}")
        lines.append("\nTell me a course and I'll share its fees and eligibility too.")
        return "\n".join(lines)

    if (course.available_seats or 0) <= 0:
        alts, close = related_courses_ex(db, course, 3, courses)
        reply = (
            f"Oh no, {course.name} is completely full at the moment (intake: {course.total_seats}). "
            "You can still join the waiting list."
        )
        if alts:
            reply += (
                "\n\nIn the meantime, these similar courses still have seats:\n" if close
                else "\n\nIn the meantime, these courses still have seats and might interest you:\n"
            ) + _alt_lines(alts)
        return reply
    low = course.available_seats / max(1, course.total_seats) <= 0.2
    return (
        f"Good news! {course.name} has {course.available_seats} seat(s) open out of {course.total_seats}."
        + (" They're going fast, so I'd apply soon!" if low else " You have time, but earlier is always safer.")
    )


def answer_eligibility(db: Session, courses: List[Course], course: Optional[Course], message: str) -> str:
    if course is None:
        return ("Sure! Which course's eligibility would you like to check? "
                "For example: 'What percentage is required for BCA?'")
    student_pct = extract_percentage(message)
    base = f"For {course.name}, the minimum requirement is {course.eligibility_percentage}%"
    if course.eligibility_note:
        base += f" ({course.eligibility_note})"
    base += "."
    if student_pct is not None:
        if student_pct >= course.eligibility_percentage:
            base += (f"\n\nGood news, with {student_pct}% you meet the requirement for "
                     f"{course.name}! You can go ahead with the admission process.")
        else:
            shortfall = round(course.eligibility_percentage - student_pct, 2)
            base += (f"\n\nWith {student_pct}% you're {shortfall}% short for {course.name}, but don't "
                     "lose hope. Please check with the admission office, as some seats may have "
                     "relaxed criteria under management/NRI quota.")
    return base + _full_note(db, courses, course)


def answer_admission(db: Session, courses: List[Course], course: Optional[Course]) -> str:
    reply = (
        "It's simple, here's how admission works:\n"
        "1. Fill the online application form on our website.\n"
        "2. Upload the required documents (10th & 12th marksheets, ID proof, photo).\n"
        "3. Pay the admission fee to confirm your seat.\n"
        "4. Attend document verification/counselling (if applicable).\n"
        "5. Receive your admission confirmation letter."
    )
    if course:
        reply += (
            f"\n\nFor {course.name}: minimum eligibility is {course.eligibility_percentage}%"
            + (f" ({course.eligibility_note})" if course.eligibility_note else "")
            + f", and {course.available_seats} of {course.total_seats} seats are open."
            + _full_note(db, courses, course)
        )
    return reply


def answer_courses_list(courses: List[Course]) -> str:
    if not courses:
        return "Course information isn't available right now. Please check back later."
    lines = ["Here's what we offer right now:"]
    for c in courses:
        seats = "FULL" if (c.available_seats or 0) <= 0 else f"{c.available_seats}/{c.total_seats} seats open"
        lines.append(
            f"• {c.name} ({c.duration_years} yrs): min {c.eligibility_percentage}%, {seats}, "
            f"{format_currency(c.fees_per_year)}/year"
        )
    lines.append("\nPick one and I'll give you the full picture!")
    return "\n".join(lines)


def answer_unavailable(db: Session, courses: List[Course], terms: List[str]) -> str:
    label = " / ".join(t.upper() if len(t) <= 5 else t.title() for t in terms)
    alts, close = related_courses_ex(db, " ".join(terms), 3, courses)
    reply = f"I checked our course list, and we don't offer {label} right now."
    if alts:
        reply += (
            "\n\nThese are the closest options and they still have seats:\n" if close
            else "\n\nHere are some programs with open seats that you might like:\n"
        ) + _alt_lines(alts) + "\n\nTap one below and I'll share the full details."
    return reply


def answer_from_faq(db: Session, message: str) -> Optional[str]:
    faqs = db.query(FAQ).all()
    if not faqs:
        return None
    candidates, faq_map = [], {}
    for f in faqs:
        key = f.question.lower()
        candidates.append(key)
        faq_map[key] = f
        for kw in (f.keywords or "").split(","):
            kw = kw.strip().lower()
            if kw:
                candidates.append(kw)
                faq_map[kw] = f
    match_str, score = best_match(clean_text(message), candidates)
    return faq_map[match_str].answer if score >= 65 else None


def course_summary(db: Session, courses: List[Course], c: Course) -> str:
    return (
        f"{c.name} is a {c.duration_years}-year program. "
        f"Eligibility: {c.eligibility_percentage}%"
        + (f" ({c.eligibility_note})" if c.eligibility_note else "")
        + f". Seats open: {c.available_seats}/{c.total_seats}. "
        f"Fees: {format_currency(c.fees_per_year)}/year ({format_currency(c.total_fees)} total)."
        + _full_note(db, courses, c)
    )


# LLM "humanize" is applied only to these data-driven intents.
POLISH_INTENTS = {"fees", "seats", "eligibility", "admission", "courses", "course_info",
                  "course_unavailable", "faq"}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def get_chatbot_reply(db: Session, message: str, session_id: Optional[str] = None) -> Tuple[str, str, List[str]]:
    courses = db.query(Course).all()
    history = _load_history(db, session_id)
    llm_history = [(h.question, h.answer) for h in history[-3:]]
    intent = classify_intent(message)
    clean = clean_text(message)

    asked = [h.question for h in history] + [message]  # never re-suggest what was already asked

    def suggest(reply, final_intent, course=None, missing_ref=None):
        rule_based = build_suggestions(db, final_intent, course, missing_ref, courses, asked=asked)
        ai = generate_followups(db, message, reply)  # None unless USE_LLM_SUGGESTIONS=True
        if not ai:
            return rule_based
        merged = []
        for q in ai + rule_based:  # AI questions first, rule-based fill the rest
            if q not in merged and q.lower() != message.strip().lower():
                merged.append(q)
        return merged[:4]

    def done(reply, final_intent, course=None, missing_ref=None):
        if final_intent in POLISH_INTENTS:
            reply = polish_reply(message, reply, llm_history) or reply
        return reply, final_intent, suggest(reply, final_intent, course, missing_ref)

    if intent == "greeting":
        return done(greeting_reply(), intent)
    if intent == "thanks":
        return done(thanks_reply(), intent)
    if intent == "contact":
        return done(contact_reply(), intent)

    # ---- which course is the student talking about? ----
    generic = bool(_GENERIC_ASK.search(clean))
    course, score = (None, 0) if generic else _match_course(courses, message)
    missing = [] if generic else _unavailable_terms(message, courses)
    if missing and score < 90:
        course = None
    else:
        missing = []

    if missing:  # asked for a course we don't have
        return done(answer_unavailable(db, courses, missing), "course_unavailable",
                    missing_ref=" ".join(missing))

    if intent == "courses":
        return done(answer_courses_list(courses), intent)

    course_in_message = course
    last_course, last_intent = _last_context(history, courses)

    # "and for MBA?" right after a fees question -> answer fees for MBA
    if (intent == "unknown" and course and not generic and len(message.split()) <= 6
            and not _ABOUT.search(clean) and last_intent in COURSE_INTENTS):
        intent = last_intent

    # "what about the fees?" -> use the course we were just discussing
    if course is None and not generic and last_course and intent in COURSE_INTENTS:
        course = last_course

    if intent == "fees":
        if course_in_message is None and _FEE_POLICY.search(clean):
            faq = answer_from_faq(db, message)
            if faq:
                return done(faq, "faq")
        return done(answer_fees(course) + (_full_note(db, courses, course) if course else ""),
                    intent, course)
    if intent == "seats":
        return done(answer_seats(db, courses, course), intent, course)
    if intent == "eligibility":
        return done(answer_eligibility(db, courses, course, message), intent, course)
    if intent == "admission":
        return done(answer_admission(db, courses, course), intent, course)

    # ---- unknown intent ----
    faq = answer_from_faq(db, message)
    if faq:
        return done(faq, "faq")

    if course_in_message:
        return done(course_summary(db, courses, course_in_message), "course_info", course_in_message)

    llm_answer = generate_llm_reply(db, message, llm_history)
    if llm_answer:
        return llm_answer, "llm", suggest(llm_answer, "llm")

    return DEFAULT_REPLY, "unknown", suggest(DEFAULT_REPLY, "unknown")