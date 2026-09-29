"""
routers/student.py
Authenticated student profile and private chat history.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.chat import ChatHistory
from app.schemas.user_schema import UserOut
from app.schemas.chat_schema import ChatHistoryOut
from app.utils.jwt_handler import get_current_user_payload

router = APIRouter(prefix="/api/student", tags=["Student"])


@router.get("/me", response_model=UserOut)
def get_my_profile(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
):
    user_id = int(payload["sub"])

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


@router.get(
    "/me/chat-history",
    response_model=list[ChatHistoryOut],
)
def get_my_chat_history(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
):
    """Return only the logged-in student's own conversations."""

    user_id = int(payload["sub"])

    return (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )


@router.delete("/me/chat-history")
def delete_my_chat_history(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
):
    """Delete only the logged-in student's own chat history."""

    user_id = int(payload["sub"])

    deleted = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .delete(synchronize_session=False)
    )

    db.commit()

    return {
        "message": "Your chat history has been deleted.",
        "deleted_count": deleted,
    }
