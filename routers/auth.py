import random
import hmac
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import (
    verify_password,
    create_access_token,
    decode_token,
    create_reset_token,
    hash_password,
)
from core.deps import get_current_user
from core.config import settings
from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    RefreshTokenResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    SendOTPRequest,
    VerifyOTPRequest,
    OTPResponse,
    LogoutRequest,
    MessageResponse,
)
from schemas.user import UserResponse
from crud import user as user_crud
from crud import auth as auth_crud
from services.notification import send_otp_sms
from models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if body.role not in ("customer", "driver"):
        raise HTTPException(status_code=400, detail="Role must be customer or driver")
    if len(body.password) < settings.PASSWORD_MIN_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
    existing = user_crud.get_by_phone(db, body.phone)
    if existing:
        raise HTTPException(status_code=400, detail="Phone already registered")
    user = user_crud.create_user(
        db,
        name=body.name,
        phone=body.phone,
        password=body.password,
        role=body.role,
    )
    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        role=user.role.value,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = user_crud.get_by_phone(db, body.phone)
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        role=user.role.value,
    )


@router.post("/send-otp", response_model=MessageResponse)
def send_otp(body: SendOTPRequest, db: Session = Depends(get_db)):
    if not body.phone or len(body.phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")
    user = user_crud.get_by_phone(db, body.phone)
    if not user:
        return MessageResponse(message="OTP sent if phone is registered")
    otp = "".join([str(random.randint(0, 9)) for _ in range(settings.OTP_LENGTH)])
    otp_hash = hash_password(otp)
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    user.otp_code = otp_hash
    user.otp_expires_at = expires
    db.commit()
    send_otp_sms(body.phone, otp)
    return MessageResponse(message="OTP sent if phone is registered")


@router.post("/verify-otp", response_model=OTPResponse)
def verify_otp(body: VerifyOTPRequest, db: Session = Depends(get_db)):
    user = user_crud.get_by_phone(db, body.phone)
    if not user:
        raise HTTPException(status_code=404, detail="Phone not registered. Please register first.")
    if not user.otp_code or not hmac.compare_digest(user.otp_code, hash_password(body.otp)):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if not user.otp_expires_at or user.otp_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired")
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return OTPResponse(
        message="Login successful",
        access_token=token,
        user_id=user.id,
        name=user.name,
        role=user.role.value,
    )


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = user_crud.get_by_phone(db, body.phone)
    if not user:
        return MessageResponse(message="If that phone is registered, an OTP has been sent")
    otp = "".join([str(random.randint(0, 9)) for _ in range(settings.OTP_LENGTH)])
    otp_hash = hash_password(otp)
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    user.otp_code = otp_hash
    user.otp_expires_at = expires
    db.commit()
    send_otp_sms(body.phone, otp)
    return MessageResponse(message="If that phone is registered, an OTP has been sent")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            User.reset_password_token == body.token,
            User.reset_password_token_expires > datetime.now(timezone.utc),
        )
        .first()
    )
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if len(body.new_password) < settings.PASSWORD_MIN_LENGTH:
        raise HTTPException(status_code=400, detail=f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
    auth_crud.reset_password(db, user, body.new_password)
    return MessageResponse(message="Password reset successfully")


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = user_crud.get_user(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    new_token = create_access_token({"user_id": user.id, "role": user.role.value})
    return RefreshTokenResponse(access_token=new_token)


@router.post("/logout", response_model=MessageResponse)
def logout(body: LogoutRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.token)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc) if payload.get("exp") else None
    except Exception:
        exp = None
    auth_crud.blacklist_token(db, body.token, exp)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
