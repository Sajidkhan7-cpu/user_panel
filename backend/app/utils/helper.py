"""
utils/helper.py
Small reusable helper functions used across the app.
"""
import uuid


def generate_session_id() -> str:
    """Generates a random session id for guest chatbot users."""
    return str(uuid.uuid4())


def format_currency(amount: float) -> str:
    """Formats a number as Indian Rupees, e.g. 125000 -> '₹1,25,000'."""
    amount = int(amount)
    s = str(amount)
    if len(s) <= 3:
        return f"₹{s}"
    last3 = s[-3:]
    rest = s[:-3]
    parts = []
    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.insert(0, rest)
    return f"₹{','.join(parts)},{last3}"
