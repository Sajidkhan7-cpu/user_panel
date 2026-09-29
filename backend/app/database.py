"""
database.py
Sets up the SQLAlchemy engine, session factory and declarative Base
for the Supabase (PostgreSQL) database defined in config.py.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,   # avoids stale-connection errors after idle periods
    pool_recycle=1800,    # Supabase's pooler recycles idle connections; refresh before that
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables (used for first-time setup / testing)."""
    from app.models import user, faq, chat, course  # noqa: F401 (register models)
    Base.metadata.create_all(bind=engine)
