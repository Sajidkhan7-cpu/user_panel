"""
services/nlp.py
Lightweight NLP preprocessing: cleaning, tokenizing, and fuzzy keyword
matching. Deliberately dependency-light (no heavy ML models) so the
project runs anywhere, but still gives good matching using RapidFuzz.
"""
import re
from typing import List
from rapidfuzz import fuzz

STOPWORDS = {
    "a", "an", "the", "is", "are", "am", "of", "for", "to", "in", "on",
    "and", "or", "what", "how", "much", "many", "does", "do", "i", "my",
    "can", "you", "please", "tell", "me", "about", "your", "this", "that",
    "college", "there", "any", "it", "will", "be", "need", "needed",
}


def clean_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9%.\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text: str) -> List[str]:
    """Clean + split into meaningful tokens (stopwords removed)."""
    cleaned = clean_text(text)
    tokens = [t for t in cleaned.split() if t not in STOPWORDS and t.strip()]
    return tokens


def similarity(a: str, b: str) -> float:
    """Fuzzy match score (0-100) between two strings."""
    return fuzz.token_set_ratio(a, b)


def best_match(text: str, candidates: List[str]) -> tuple[str, float]:
    """Returns the candidate string with the highest fuzzy similarity to `text`."""
    best_candidate, best_score = "", 0.0
    for c in candidates:
        score = similarity(text, c)
        if score > best_score:
            best_candidate, best_score = c, score
    return best_candidate, best_score


def extract_percentage(text: str):
    """Extracts a numeric percentage value mentioned by the student, if any."""
    match = re.search(r"(\d{1,3}(?:\.\d+)?)\s*%?", text)
    if match:
        value = float(match.group(1))
        if 0 <= value <= 100:
            return value
    return None
