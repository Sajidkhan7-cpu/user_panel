"""
schemas/chat_schema.py
"""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = None
    session_id: Optional[str] = None
    suggestions: list[str] = []


class ChatHistoryOut(BaseModel):
    id: int
    session_id: Optional[str] = None
    question: str
    answer: str
    intent: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
