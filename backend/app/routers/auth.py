"""
routers/auth.py
Student & admin registration and login (JWT-based).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserRegister, AdminRegister, UserLogin, UserOut, Token
from app.utils.password import hash_password, verify_password
from app.utils.jwt_handler import create_access_token
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role="student",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return Token(access_token=token, user=user)


@router.post("/admin-register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def admin_register(payload: AdminRegister, db: Session = Depends(get_db)):
    """
    Creates a new admin account. Requires `registration_key` to match
    ADMIN_REGISTRATION_KEY in .env, so random visitors can't self-promote
    to admin just by finding the registration page.
    """
    if payload.registration_key != settings.ADMIN_REGISTRATION_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin registration key")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    admin = User(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@router.post("/admin-login", response_model=Token)
def admin_login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.role == "admin").first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return Token(access_token=token, user=user)
