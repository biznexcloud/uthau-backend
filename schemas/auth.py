from pydantic import BaseModel
from typing import Optional


class RegisterRequest(BaseModel):
    name: str
    phone: str
    password: str
    role: str = "customer"


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SendOTPRequest(BaseModel):
    phone: str


class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str


class OTPResponse(BaseModel):
    message: str
    access_token: str
    user_id: int
    name: str
    role: str


class ForgotPasswordRequest(BaseModel):
    phone: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class LogoutRequest(BaseModel):
    token: str


class MessageResponse(BaseModel):
    message: str
