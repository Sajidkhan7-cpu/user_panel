"""
routers/chatbot.py
Main chatbot endpoint used by frontend/assets/js/chatbot.js.
Works for logged-in students and anonymous guests (session_id).
"""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database import get_db
from app.schemas.chat_schema import ChatRequest, ChatResponse, ChatHistoryOut
from app.models.chat import ChatHistory
from app.services.chatbot_service import get_chatbot_reply
from app.utils.helper import generate_session_id
from app.config import settings

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


def _try_get_user_id(authorization: str | None) -> int | None:
    """Optionally decodes a Bearer token if present, without requiring login."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None


@router.post("/ask", response_model=ChatResponse)
def ask_chatbot(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    # FIX: without Header(), FastAPI treated this as a query parameter, so the
    # Authorization header was never read.
    authorization: str | None = Header(default=None),
):
    session_id = payload.session_id or generate_session_id()

    # The session_id lets the bot remember the last few turns ("and its fees?").
    reply, intent, suggestions = get_chatbot_reply(db, payload.message, session_id)

    db.add(ChatHistory(
        user_id=_try_get_user_id(authorization),
        session_id=session_id,
        question=payload.message,
        answer=reply,
        intent=intent,
    ))
    db.commit()

    return ChatResponse(reply=reply, intent=intent, session_id=session_id, suggestions=suggestions)


@router.get("/history/{session_id}", response_model=list[ChatHistoryOut])
def get_history(session_id: str, db: Session = Depends(get_db)):
    return (
        db.query(ChatHistory)
        .filter(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )