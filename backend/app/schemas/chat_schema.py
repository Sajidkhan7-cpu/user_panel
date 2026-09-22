"""
schemas/chat_schema.py
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None   # used to group a guest's conversation


class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    session_id: Optional[str] = None


class ChatHistoryOut(BaseModel):
    id: int
    question: str
    answer: str
    intent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
