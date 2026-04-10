import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from config import settings
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas import UserRegister, UserLogin, Token, UserOut
from auth import hash_password, verify_password, create_access_token, get_current_user
import models

_otp_store: dict = {}

def _send_otp_email(to_email: str, otp: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "BingeBuddy — Your Password Reset OTP"
    msg["From"] = settings.EMAIL_USER
    msg["To"] = to_email
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:auto;background:#080b12;color:#f1f1f1;padding:32px;border-radius:16px;">
      <h1 style="font-size:2rem;color:#e63946;">BingeBuddy</h1>
      <p>Use this OTP to reset your password. Expires in <strong>10 minutes</strong>.</p>
      <div style="font-size:2.5rem;font-weight:700;letter-spacing:12px;text-align:center;background:#0f1420;padding:24px;border-radius:12px;margin:24px 0;color:#e63946;">{otp}</div>
      <p style="color:#7a8099;font-size:0.85rem;">If you didn't request this, ignore this email.</p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
        server.sendmail(settings.EMAIL_USER, to_email, msg.as_string())

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Create a new user account."""

    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return a JWT access token."""

    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    """Return the currently logged in user's details."""
    return current_user

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        return {"message": "If this email is registered, an OTP has been sent."}
    otp = "".join(random.choices(string.digits, k=6))
    _otp_store[payload.email] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
    }
    try:
        _send_otp_email(payload.email, otp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
    return {"message": "OTP sent to your email."}


@router.post("/reset-password")
def reset_password(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    entry = _otp_store.get(payload.email)
    if not entry:
        raise HTTPException(status_code=400, detail="No OTP requested for this email")
    if datetime.utcnow() > entry["expires_at"]:
        _otp_store.pop(payload.email, None)
        raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
    if entry["otp"] != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    _otp_store.pop(payload.email, None)
    return {"message": "Password reset successfully. You can now log in."}
