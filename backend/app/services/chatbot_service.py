"""
services/chatbot_service.py
The "brain" of the chatbot.

Pipeline:
 1. Clean & tokenize the incoming question (services/nlp.py)
 2. Classify intent using keyword matching (admission, fees, seats,
    courses, eligibility/percentage, contact, greeting, thanks)
 3. Try to detect which course the student is asking about (fuzzy
    match against course names/short codes in the database)
 4. Build a precise answer from the `courses` table for that intent
 5. If no course-specific intent matches, fall back to the FAQ table
 6. If still nothing matches, fall back to the OpenAI LLM (services/
    llm_service.py), grounded in the same course/FAQ data — only if
    USE_LLM_FALLBACK is enabled and an API key is configured
 7. If the LLM is disabled/unavailable/fails, return a helpful default
    message

Note: fees, seats, and eligibility % are ALWAYS answered by steps 2-4
directly from the database — never by the LLM — so numbers can never
be hallucinated for those intents.
"""
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.faq import FAQ
from app.services.nlp import clean_text, tokenize, best_match, extract_percentage
from app.services.llm_service import generate_llm_reply
from app.utils.helper import format_currency

# ---------------------------------------------------------------------------
# Intent keyword dictionary. Order matters: more specific intents first.
# ---------------------------------------------------------------------------
INTENT_KEYWORDS = {
    "greeting": ["hi", "hello", "hey", "good morning", "good evening", "good afternoon"],
    "thanks": ["thank", "thanks", "thank you", "ok thanks", "great"],
    "seats": ["seat", "seats", "vacancy", "vacancies", "available seat", "seats left", "seats available"],
    "fees": ["fee", "fees", "cost", "price", "tuition", "charges", "how much", "scholarship", "installment", "instalment"],
    "eligibility": ["percentage", "eligibility", "eligible", "marks", "cutoff", "cut off", "qualify", "minimum marks", "required percentage"],
    "admission": ["admission", "apply", "enroll", "enrol", "registration", "how to join", "join college", "admission process"],
    "courses": ["course", "courses", "branch", "branches", "program", "programs", "programme", "specialization", "stream", "streams"],
    "contact": ["contact", "phone number", "email", "address", "location", "reach", "call"],
}


def classify_intent(message: str) -> str:
    text = clean_text(message)
    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return intent
    return "unknown"


def find_course(db: Session, message: str) -> Optional[Course]:
    """Fuzzy-matches the student's message against course names & short codes."""
    courses = db.query(Course).all()
    if not courses:
        return None

    lookup = {}
    for c in courses:
        lookup[c.name.lower()] = c
        if c.short_code:
            lookup[c.short_code.lower()] = c

    candidate_strings = list(lookup.keys())
    match_str, score = best_match(clean_text(message), candidate_strings)

    if score >= 60:  # confidence threshold
        return lookup[match_str]
    return None


def answer_fees(course: Optional[Course]) -> str:
    if course is None:
        return (
            "Could you tell me which course you'd like fee details for? "
            "For example: 'What are the fees for B.Tech CSE?'"
        )
    admission_fee = format_currency(course.admission_fee)
    per_year = format_currency(course.fees_per_year)
    total = format_currency(course.total_fees)
    reply = (
        f"Fees for {course.name} ({course.duration_years} years):\n"
        f"• Admission/registration fee: {admission_fee} (one-time)\n"
        f"• Fee per year: {per_year}\n"
        f"• Total course fees: {total}"
    )
    if course.scholarship_available:
        reply += f"\n• Scholarship: {course.scholarship_available}"
    reply += (
        "\n\nFee condition: the admission fee must be paid at the time of admission to "
        "confirm your seat; remaining fees can be paid year-wise/semester-wise as per the "
        "college fee schedule. Fees once paid are non-refundable after the seat is confirmed, "
        "except as per the official refund policy."
    )
    return reply


def answer_seats(course: Optional[Course]) -> str:
    if course is None:
        return (
            "Which course's seat availability would you like to check? "
            "For example: 'Are seats available in B.Tech ECE?'"
        )
    if course.available_seats <= 0:
        return (
            f"Sorry, all seats for {course.name} are currently full "
            f"(total intake: {course.total_seats}). You can still register on the waiting list."
        )
    return (
        f"Yes! {course.name} currently has {course.available_seats} seat(s) available "
        f"out of {course.total_seats} total seats. We'd recommend applying soon as seats fill quickly."
    )


def answer_eligibility(course: Optional[Course], message: str) -> str:
    student_pct = extract_percentage(message)
    if course is None:
        return (
            "Which course's eligibility criteria would you like to know? "
            "For example: 'What percentage is required for B.Tech CSE?'"
        )
    base = f"Eligibility for {course.name}: minimum {course.eligibility_percentage}% required"
    if course.eligibility_note:
        base += f" ({course.eligibility_note})"
    base += "."

    if student_pct is not None:
        if student_pct >= course.eligibility_percentage:
            base += (
                f"\n\nGood news — with {student_pct}%, you meet the eligibility requirement "
                f"for {course.name}! You can proceed with the admission process."
            )
        else:
            shortfall = round(course.eligibility_percentage - student_pct, 2)
            base += (
                f"\n\nWith {student_pct}%, you currently fall short by {shortfall}% for "
                f"{course.name}. Please check with the admission office as some seats may have "
                f"relaxed criteria under management/NRI quota."
            )
    return base


def answer_admission(course: Optional[Course]) -> str:
    common = (
        "Admission process:\n"
        "1. Fill the online application form on our website.\n"
        "2. Upload required documents (10th & 12th marksheets, ID proof, photo).\n"
        "3. Pay the admission fee to confirm your seat.\n"
        "4. Attend document verification/counselling (if applicable).\n"
        "5. Receive your admission confirmation letter."
    )
    if course:
        common += (
            f"\n\nFor {course.name}: minimum eligibility is {course.eligibility_percentage}%"
            + (f" ({course.eligibility_note})" if course.eligibility_note else "")
            + f", and {course.available_seats} of {course.total_seats} seats are currently available."
        )
    return common


def answer_courses_list(db: Session) -> str:
    courses = db.query(Course).all()
    if not courses:
        return "Course information isn't available right now. Please check back later."
    lines = ["Here are the courses currently offered:"]
    for c in courses:
        lines.append(
            f"• {c.name} ({c.duration_years} yrs) — Eligibility: {c.eligibility_percentage}%, "
            f"Seats available: {c.available_seats}/{c.total_seats}, "
            f"Fees/year: {format_currency(c.fees_per_year)}"
        )
    lines.append("\nAsk me about any specific course for full fee and eligibility details!")
    return "\n".join(lines)


def answer_from_faq(db: Session, message: str) -> Optional[str]:
    faqs = db.query(FAQ).all()
    if not faqs:
        return None
    candidates = []
    faq_map = {}
    for f in faqs:
        key = f.question.lower()
        candidates.append(key)
        faq_map[key] = f
        if f.keywords:
            for kw in f.keywords.split(","):
                kw = kw.strip().lower()
                if kw:
                    candidates.append(kw)
                    faq_map[kw] = f

    match_str, score = best_match(clean_text(message), candidates)
    if score >= 65:
        return faq_map[match_str].answer
    return None


DEFAULT_REPLY = (
    "I can help you with admission process, fees, seat availability, courses offered, "
    "and eligibility percentage for any course. Could you please rephrase your question? "
    "For example: 'What is the fee for B.Tech CSE?' or 'How many seats are left in MBA?'"
)

GREETING_REPLY = (
    "Hello! 👋 I'm the college enquiry assistant. I can help with admission, fees, "
    "seat availability, available courses, and eligibility criteria. What would you like to know?"
)

THANKS_REPLY = "You're welcome! Feel free to ask if you have any more questions about admissions."

CONTACT_REPLY = (
    "You can reach the admission office at admissions@college.edu.in or call +91-9876543210. "
    "Our office is open Monday to Saturday, 9 AM to 5 PM."
)


def get_chatbot_reply(db: Session, message: str) -> Tuple[str, str]:
    """
    Main entry point used by the chatbot router.
    Returns a tuple: (reply_text, intent_name)
    """
    intent = classify_intent(message)

    if intent == "greeting":
        return GREETING_REPLY, intent
    if intent == "thanks":
        return THANKS_REPLY, intent
    if intent == "contact":
        return CONTACT_REPLY, intent

    if intent == "courses":
        return answer_courses_list(db), intent

    course = find_course(db, message)

    if intent == "fees":
        # Generic fee-policy questions, such as installment availability, are
        # answered by the FAQ instead of requiring a course name.
        if course is None:
            faq_answer = answer_from_faq(db, message)
            if faq_answer:
                return faq_answer, "faq"
        return answer_fees(course), intent
    if intent == "seats":
        return answer_seats(course), intent
    if intent == "eligibility":
        return answer_eligibility(course, message), intent
    if intent == "admission":
        return answer_admission(course), intent

    # unknown intent -> try FAQ table next
    faq_answer = answer_from_faq(db, message)
    if faq_answer:
        return faq_answer, "faq"

    # maybe they only typed a course name — give a quick summary
    if course:
        return (
            f"{course.name}: {course.duration_years}-year program. "
            f"Eligibility: {course.eligibility_percentage}%"
            + (f" ({course.eligibility_note})" if course.eligibility_note else "")
            + f". Seats available: {course.available_seats}/{course.total_seats}. "
            f"Fees/year: {format_currency(course.fees_per_year)}, "
            f"Total fees: {format_currency(course.total_fees)}.\n"
            "Ask me about fees, seats, or eligibility specifically for more detail!",
            "course_info",
        )

    # last resort: ask the LLM (OpenAI), grounded in the same course/FAQ
    # data, so it can handle chit-chat or oddly-phrased questions without
    # inventing facts. Safely returns None if disabled/unconfigured/failed.
    llm_answer = generate_llm_reply(db, message)
    if llm_answer:
        return llm_answer, "llm"

    return DEFAULT_REPLY, "unknown"
