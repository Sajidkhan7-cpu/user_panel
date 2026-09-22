"""
models/course.py
Stores each course offered by the college along with the exact data
the chatbot needs to answer admission / fees / seats / eligibility
questions.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False, unique=True)      # e.g. "B.Tech Computer Science"
    short_code = Column(String(20), nullable=True)                 # e.g. "CSE"
    duration_years = Column(Integer, nullable=False, default=4)

    total_seats = Column(Integer, nullable=False, default=0)
    available_seats = Column(Integer, nullable=False, default=0)

    total_fees = Column(Float, nullable=False, default=0)          # full course fees
    fees_per_year = Column(Float, nullable=False, default=0)
    admission_fee = Column(Float, nullable=False, default=0)       # one-time admission/registration fee

    eligibility_percentage = Column(Float, nullable=False, default=0)  # min % required in qualifying exam
    eligibility_note = Column(String(255), nullable=True)           # e.g. "10+2 with PCM"

    scholarship_available = Column(String(255), nullable=True)      # short text description

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
