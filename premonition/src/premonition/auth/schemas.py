"""Auth request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from premonition.auth.roles import Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: Role


class RefreshRequest(BaseModel):
    refresh_token: str


class UserPublic(BaseModel):
    email: str
    role: Role
    active: bool = True


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=64)
    role: Role = Role.CLINICIAN


class ApiKeyResponse(BaseModel):
    name: str
    key: str
    role: Role
    created_at: str


# ── OTP schemas ──────────────────────────────────────────────────────────────

class OTPRequestBody(BaseModel):
    email: EmailStr


class OTPVerifyBody(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")


class OTPResendBody(BaseModel):
    email: EmailStr


class OTPRequestResponse(BaseModel):
    message: str
    expires_in_seconds: int
    masked_email: str


class OTPVerifyResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: Role


class OTPErrorResponse(BaseModel):
    detail: str
    locked: bool = False
    lockout_remaining_seconds: int = 0

