"""
models/chat.py
Stores every question asked to the chatbot and the answer given,
so admins can review common queries and students can see history.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # null for guest/anonymous chats
    session_id = Column(String(100), nullable=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)  # e.g. fees, seats, admission, courses, eligibility
    created_at = Column(DateTime(timezone=True), server_default=func.now())
