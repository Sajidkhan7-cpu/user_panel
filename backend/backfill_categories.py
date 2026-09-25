"""
backfill_categories.py
One-time helper: adds the `category` column (if missing) and fills it for
existing courses by guessing from the course name. Review the printed
result and correct any guess from your admin panel afterwards.

Run from the backend folder:
    python backfill_categories.py
"""
from sqlalchemy import inspect, text

from app.database import engine, get_db
from app.models.course import Course
from app.services.suggestion_service import STREAM_GROUPS, course_tokens

# First match wins. Adjust the order if your college needs different rules.
PRIORITY = ["medical", "law", "computer", "business", "engineering", "science", "arts"]


def guess_category(course: Course):
    tokens = course_tokens(course)
    for group in PRIORITY:
        if tokens & STREAM_GROUPS[group]:
            return group
    return None


def main():
    # 1) create_all() never alters an existing table, so add the column ourselves.
    cols = [c["name"] for c in inspect(engine).get_columns("courses")]
    if "category" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE courses ADD COLUMN category VARCHAR(50)"))
        print("Added column: courses.category")

    # 2) Fill blanks only. Never overwrites a category you set manually.
    db = next(get_db())
    for c in db.query(Course).all():
        if not c.category:
            c.category = guess_category(c)
        print(f"{c.name:40} -> {c.category}")
    db.commit()


if __name__ == "__main__":
    main()