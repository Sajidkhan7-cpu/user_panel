"""
routers/student.py
Endpoints a logged-in student can call: view profile, view their own
chat history.
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
def get_my_profile(payload: dict = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me/chat-history", response_model=list[ChatHistoryOut])
def get_my_chat_history(payload: dict = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    user_id = int(payload["sub"])
    records = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.desc())
        .all()
    )
    return records
