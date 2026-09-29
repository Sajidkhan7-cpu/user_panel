"""
routers/course.py
Public read endpoints for course info (used by the About/Chatbot pages).
Admin write endpoints (create/update/delete) live in routers/admin.py.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.course import Course
from app.schemas.course_schema import CourseOut

router = APIRouter(prefix="/api/courses", tags=["Courses"])


@router.get("/", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db)):
    return db.query(Course).all()


@router.get("/{course_id}", response_model=CourseOut)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course
