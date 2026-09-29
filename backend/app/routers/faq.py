"""
routers/faq.py
Public read endpoints for FAQs (admin CRUD lives in routers/admin.py).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.faq import FAQ
from app.schemas.faq_schema import FAQOut

router = APIRouter(prefix="/api/faq", tags=["FAQ"])


@router.get("/", response_model=list[FAQOut])
def list_faqs(category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(FAQ)
    if category:
        query = query.filter(FAQ.category == category)
    return query.all()
