"""
routers/chatbot.py
Authenticated student chatbot + per-user chat history.
"""

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.database import get_db
from app.schemas.chat_schema import ChatRequest, ChatResponse, ChatHistoryOut
from app.models.chat import ChatHistory
from app.services.chatbot_service import get_chatbot_reply
from app.utils.helper import generate_session_id
from app.utils.jwt_handler import get_current_user_payload
from app.config import settings

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


def _try_get_user_id(authorization: str | None) -> int | None:
    """Backward-compatible helper for optional auth headers."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ", 1)[1]

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None


@router.post("/ask", response_model=ChatResponse)
def ask_chatbot(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    """
    Only logged-in users can use the chatbot.

    Every question and answer is stored against the authenticated
    user's database ID.
    """

    user_id = int(current_user["sub"])

    # Keep one conversation session per browser login.
    session_id = payload.session_id or generate_session_id()

    reply, intent, suggestions = get_chatbot_reply(
        db,
        payload.message,
        session_id,
    )

    history = ChatHistory(
        user_id=user_id,
        session_id=session_id,
        question=payload.message,
        answer=reply,
        intent=intent,
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return ChatResponse(
        reply=reply,
        intent=intent,
        session_id=session_id,
        suggestions=suggestions,
    )


@router.get("/history/{session_id}", response_model=list[ChatHistoryOut])
def get_history(
    session_id: str,
    current_user: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
):
    """
    Return history only when the session belongs to the logged-in user.
    """

    user_id = int(current_user["sub"])

    return (
        db.query(ChatHistory)
        .filter(
            ChatHistory.user_id == user_id,
            ChatHistory.session_id == session_id,
        )
        .order_by(ChatHistory.created_at.asc())
        .all()
    )
