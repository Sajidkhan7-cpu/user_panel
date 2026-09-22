"""
schemas/faq_schema.py
"""
from typing import Optional
from pydantic import BaseModel


class FAQBase(BaseModel):
    category: str = "general"
    question: str
    keywords: Optional[str] = None
    answer: str


class FAQCreate(FAQBase):
    pass


class FAQUpdate(BaseModel):
    category: Optional[str] = None
    question: Optional[str] = None
    keywords: Optional[str] = None
    answer: Optional[str] = None


class FAQOut(FAQBase):
    id: int

    class Config:
        from_attributes = True
