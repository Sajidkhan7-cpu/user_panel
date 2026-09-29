"""
services/suggestion_service.py
Two jobs:
  1. related_courses()   -> finds similar courses (used when a course is full
                            or the student asks for one we don't offer)
  2. build_suggestions() -> the tappable follow-up chips shown after each answer

No AI call is needed here, so it is instant, free and predictable.
"""
import random
import re
from difflib import SequenceMatcher
from typing import Iterable, List, Optional, Tuple, Union

from sqlalchemy.orm import Session

from app.models.course import Course

# Courses sharing a group are treated as "related". A course can be in several.
STREAM_GROUPS = {
    "computer": {"cse", "cs", "it", "bca", "mca", "computer", "software", "ai", "aiml",
                 "data", "cyber", "informatics", "technology"},
    "engineering": {"btech", "mtech", "be", "me", "mechanical", "civil", "ece", "eee",
                    "electrical", "electronics", "cse", "chemical", "engineering"},
    "business": {"mba", "bba", "pgdm", "bcom", "mcom", "bms", "management", "business",
                 "commerce", "accounting", "finance", "banking", "taxation", "hr",
                 "marketing", "economics"},
    "science": {"bsc", "msc", "science", "physics", "chemistry", "maths", "biology"},
    "arts": {"ba", "ma", "arts", "journalism", "psychology", "english", "history"},
    "law": {"llb", "llm", "law"},
    "medical": {"mbbs", "bds", "bpharm", "mpharm", "pharmacy", "nursing", "bams", "bhms"},
}

UG = {"btech", "be", "bca", "bba", "bcom", "bsc", "ba", "bpharm", "llb", "bds", "mbbs", "barch", "bed"}
PG = {"mtech", "me", "mca", "mba", "mcom", "msc", "ma", "mpharm", "llm", "pgdm"}

_STOP = {"of", "in", "and", "the", "for", "with"}
MIN_RELATED_SCORE = 30


def normalize_tokens(text: str) -> set:
    """'B.Tech CSE' -> {'btech', 'cse'}"""
    return set(re.findall(r"[a-z0-9]+", (text or "").lower().replace(".", "")))


def course_tokens(course: Course) -> set:
    toks = normalize_tokens(f"{course.name} {course.short_code or ''}")
    words = [w for w in re.findall(r"[A-Za-z]+", course.name or "") if w.lower() not in _STOP]
    if len(words) >= 2:  # 'Master of Business Administration' -> 'mba'
        toks.add("".join(w[0].lower() for w in words))
    return toks


def _groups(tokens: set) -> set:
    return {g for g, kws in STREAM_GROUPS.items() if tokens & kws}


def _level(tokens: set) -> Optional[str]:
    if tokens & UG:
        return "UG"
    if tokens & PG:
        return "PG"
    return None


def _norm_cat(value) -> Optional[str]:
    return (str(value).strip().lower() or None) if value else None


def _similarity(ref_text: str, ref_tokens: set, ref_cat: Optional[str], other: Course) -> float:
    ot = course_tokens(other)
    score = 0.0
    if _groups(ref_tokens) & _groups(ot):  # name-based guess
        score += 50
    other_cat = _norm_cat(getattr(other, "category", None))
    if ref_cat and other_cat and ref_cat == other_cat:  # admin-set Course.category
        score += 40
    score += 25 * len(ref_tokens & ot) / max(1, len(ref_tokens | ot))
    if _level(ref_tokens) and _level(ref_tokens) == _level(ot):
        score += 10
    score += 15 * SequenceMatcher(None, ref_text.lower(), (other.name or "").lower()).ratio()
    return score


def related_courses_ex(
    db: Session,
    reference: Union[Course, str],
    limit: int = 3,
    courses: Optional[List[Course]] = None,
    only_available: bool = True,
) -> Tuple[List[Course], bool]:
    """Returns (courses, is_close_match). Falls back to 'most seats open' if nothing is similar."""
    courses = courses if courses is not None else db.query(Course).all()
    if isinstance(reference, Course):
        ref_text = f"{reference.name} {reference.short_code or ''}"
        ref_id = reference.id
        ref_cat = _norm_cat(getattr(reference, "category", None))
    else:
        ref_text, ref_id, ref_cat = str(reference), None, None
    ref_tokens = normalize_tokens(ref_text)

    pool = [
        c for c in courses
        if c.id != ref_id and (not only_available or (c.available_seats or 0) > 0)
    ]
    scored = sorted(((_similarity(ref_text, ref_tokens, ref_cat, c), c) for c in pool),
                    key=lambda x: x[0], reverse=True)
    close = [c for s, c in scored if s >= MIN_RELATED_SCORE][:limit]
    if close:
        return close, True
    fallback = sorted(pool, key=lambda c: c.available_seats or 0, reverse=True)[:limit]
    return fallback, False


def related_courses(db, reference, limit=3, courses=None, only_available=True) -> List[Course]:
    return related_courses_ex(db, reference, limit, courses, only_available)[0]


# ---------------------------------------------------------------------------
# Follow-up QUESTION suggestions
# Every suggestion is a full, natural question about what the student just asked.
# Each one is phrased so the chatbot can really answer it (intent keywords match).
# Several phrasings per slot, so the chips don't feel copy-pasted every time.
# ---------------------------------------------------------------------------
FEES_Q = ["What are the fees for {c}?", "How much is the fee for {c}?", "What is the total fee of {c}?"]
SEATS_Q = ["Are seats still available in {c}?", "How many seats are left in {c}?"]
ELIG_Q = ["What percentage is required for {c}?", "What is the eligibility for {c}?"]
APPLY_Q = ["How do I apply for {c}?", "What is the admission process for {c}?"]
SCHOLAR_Q = ["Is there any scholarship for {c}?"]

SEATS_LEFT_Q = "Which courses have seats left?"
COURSES_Q = "What courses are available?"
APPLY_GENERIC_Q = "How can I apply for admission?"
DOCS_Q = "What documents are required for admission?"
INSTALLMENT_Q = "Can I pay the fees in installments?"
CONTACT_Q = "What is the college contact number?"


def _q(templates: List[str], course: Course) -> str:
    # Long names ("Bachelor of Computer Applications") make long chips -> use the short code.
    label = course.name if len(course.name or "") <= 22 or not course.short_code else course.short_code
    return random.choice(templates).format(c=label)


def _norm_q(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (text or "").lower()).strip()


def build_suggestions(
    db: Session,
    intent: str,
    course: Optional[Course] = None,
    missing_ref: Optional[str] = None,
    courses: Optional[List[Course]] = None,
    max_items: int = 4,
    asked: Optional[Iterable[str]] = None,
) -> List[str]:
    """
    `asked` = questions already asked in this chat; they are never suggested again.
    Tapping a chip sends it as a normal message.
    """
    courses = courses if courses is not None else db.query(Course).all()
    asked_norm = {_norm_q(q) for q in (asked or [])}
    out: List[str] = []

    def add(q: Optional[str]):
        if q and q not in out and _norm_q(q) not in asked_norm:
            out.append(q)

    open_courses = [c for c in courses if (c.available_seats or 0) > 0]

    if missing_ref:  # asked about a course we don't offer -> questions about real alternatives
        alts = related_courses(db, missing_ref, 2, courses)
        for alt in alts:
            add(_q(FEES_Q, alt))
        if alts:
            add(_q(ELIG_Q, alts[0]))
        add(SEATS_LEFT_Q)
        add(COURSES_Q)

    elif course is not None:
        if (course.available_seats or 0) <= 0:  # full -> questions about similar open courses first
            for alt in related_courses(db, course, 2, courses):
                add(_q(FEES_Q, alt))
            add(SEATS_LEFT_Q)

        if intent == "fees":
            add(_q(SEATS_Q, course))
            add(_q(ELIG_Q, course))
            if course.scholarship_available:
                add(_q(SCHOLAR_Q, course))
            add(_q(APPLY_Q, course))
            add(INSTALLMENT_Q)
        elif intent == "seats":
            add(_q(FEES_Q, course))
            add(_q(ELIG_Q, course))
            add(_q(APPLY_Q, course))
        elif intent == "eligibility":
            add(_q(FEES_Q, course))
            add(_q(SEATS_Q, course))
            add(_q(APPLY_Q, course))
            add(DOCS_Q)
        elif intent == "admission":
            add(_q(FEES_Q, course))
            add(_q(ELIG_Q, course))
            add(_q(SEATS_Q, course))
            add(CONTACT_Q)
        else:  # course_info, faq, llm ...
            add(_q(FEES_Q, course))
            add(_q(SEATS_Q, course))
            add(_q(ELIG_Q, course))
            add(_q(APPLY_Q, course))

    else:  # no specific course yet -> steer towards a concrete, answerable question
        first = open_courses[0] if open_courses else (courses[0] if courses else None)
        second = open_courses[1] if len(open_courses) > 1 else first
        if intent == "courses":
            if first:
                add(_q(FEES_Q, first))
            if second:
                add(_q(ELIG_Q, second))
            add(SEATS_LEFT_Q)
            add(APPLY_GENERIC_Q)
        elif intent == "admission":
            add(DOCS_Q)
            add(COURSES_Q)
            add(SEATS_LEFT_Q)
            add(CONTACT_Q)
        elif intent == "contact":
            add(COURSES_Q)
            add(APPLY_GENERIC_Q)
        else:  # greeting, thanks, unknown, llm, fees/seats/eligibility without a course
            if intent != "courses":
                add(COURSES_Q)
            if intent != "seats":
                add(SEATS_LEFT_Q)
            if first and intent in ("fees", "greeting", "thanks", "unknown", "llm"):
                add(_q(FEES_Q, first))
            if first and intent == "eligibility":
                add(_q(ELIG_Q, first))
            add(APPLY_GENERIC_Q)
            add(CONTACT_Q)

    for filler in (COURSES_Q, APPLY_GENERIC_Q, SEATS_LEFT_Q, CONTACT_Q):
        add(filler)
    return out[:max_items]