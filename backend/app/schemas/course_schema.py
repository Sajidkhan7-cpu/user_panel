"""
schemas/course_schema.py
"""
from typing import Optional
from pydantic import BaseModel


class CourseBase(BaseModel):
    name: str
    short_code: Optional[str] = None
    duration_years: int = 4
    total_seats: int = 0
    available_seats: int = 0
    total_fees: float = 0
    fees_per_year: float = 0
    admission_fee: float = 0
    eligibility_percentage: float = 0
    eligibility_note: Optional[str] = None
    scholarship_available: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    name: Optional[str] = None
    short_code: Optional[str] = None
    duration_years: Optional[int] = None
    total_seats: Optional[int] = None
    available_seats: Optional[int] = None
    total_fees: Optional[float] = None
    fees_per_year: Optional[float] = None
    admission_fee: Optional[float] = None
    eligibility_percentage: Optional[float] = None
    eligibility_note: Optional[str] = None
    scholarship_available: Optional[str] = None


class CourseOut(CourseBase):
    id: int

    class Config:
        from_attributes = True
