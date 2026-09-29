"""
models/faq.py
Generic Q&A pairs used as a fallback knowledge base by the chatbot
(admin can add/edit these from the dashboard).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, default="general")  # admission, fees, seats, courses, general
    question = Column(String(255), nullable=False)
    keywords = Column(String(255), nullable=True)   # comma separated keywords used for matching
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
