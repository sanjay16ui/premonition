"""Authentication routes — login, refresh, profile, API keys, and OTP."""

from __future__ import annotations

import logging
from typing import Annotated
import time

import jwt
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from premonition.auth.dependencies import AuthCtxDep, get_user_store, require_perm
from premonition.auth.email_service import ResendEmailService
from premonition.auth.jwt_handler import (
    ACCESS_TOKEN_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_token,
    is_jwt_enabled,
)
from premonition.auth.otp_store import OTPStore
from premonition.auth.roles import Role
from premonition.auth.schemas import (
    ApiKeyCreateRequest,
    ApiKeyResponse,
    LoginRequest,
    OTPRequestBody,
    OTPRequestResponse,
    OTPResendBody,
    OTPVerifyBody,
    OTPVerifyResponse,
    RefreshRequest,
    TokenResponse,
    UserPublic,
)
from premonition.auth.user_store import UserStore
from premonition.api.dependencies import get_email_service, get_otp_store

DEMO_EMAIL = "doctor@premonition.health"
DEMO_ROLE = Role.CLINICIAN

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# ── Background task helpers ───────────────────────────────────────────────────

async def _send_otp_background(email_svc: ResendEmailService, email: str, otp: str) -> None:
    """Send OTP email in background after API response has been returned."""
    try:
        import time as _time
        start = _time.perf_counter()
        sent = await email_svc.send_otp_email(email, otp)
        elapsed = _time.perf_counter() - start
        if sent:
            logger.info("[OTP-EMAIL-BG] Delivered to %s in %.3fs", email, elapsed)
        else:
            logger.error("[OTP-EMAIL-BG] FAILED delivery to %s after %.3fs", email, elapsed)
    except Exception as exc:
        logger.error("[OTP-EMAIL-BG] Exception sending to %s: %s", email, exc)



# ── Helpers ──────────────────────────────────────────────────────────────────

def _mask_email(email: str) -> str:
    """Return partially masked email for safe display. e.g. d***r@example.com"""
    local, _, domain = email.partition("@")
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def _guest_role() -> Role:
    """Default role for users not found in the user store."""
    return Role.CLINICIAN


# ── Existing password routes ──────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, store: Annotated[UserStore, Depends(get_user_store)]) -> TokenResponse:
    if not is_jwt_enabled():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "JWT authentication not configured")
    user = store.authenticate(body.email, body.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenResponse(
        access_token=create_access_token(user.email, user.role),
        refresh_token=create_refresh_token(user.email, user.role),
        expires_in=ACCESS_TOKEN_MINUTES * 60,
        role=user.role,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest) -> TokenResponse:
    if not is_jwt_enabled():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "JWT not configured")
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
        role = Role(payload["role"])
        subject = payload["sub"]
        return TokenResponse(
            access_token=create_access_token(subject, role),
            refresh_token=create_refresh_token(subject, role),
            expires_in=ACCESS_TOKEN_MINUTES * 60,
            role=role,
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token") from exc


@router.get("/me", response_model=UserPublic)
async def me(ctx: AuthCtxDep, store: Annotated[UserStore, Depends(get_user_store)]) -> UserPublic:
    if ctx.auth_method == "dev":
        return UserPublic(email="dev@local", role=ctx.role)
    user = store.get_user(ctx.subject)
    if user:
        return UserPublic(email=user.email, role=user.role, active=user.active)
    return UserPublic(email=ctx.subject, role=ctx.role)


@router.post("/api-keys", response_model=ApiKeyResponse, dependencies=[Depends(require_perm("users:manage"))])
async def create_api_key(
    body: ApiKeyCreateRequest,
    store: Annotated[UserStore, Depends(get_user_store)],
) -> ApiKeyResponse:
    result = store.create_api_key(body.name, body.role)
    return ApiKeyResponse(**result)


# ── OTP Routes ────────────────────────────────────────────────────────────────

@router.post("/request-otp", response_model=OTPRequestResponse, status_code=200)
async def request_otp(
    body: OTPRequestBody,
    request: Request,
    background_tasks: BackgroundTasks,
    otp_store: Annotated[OTPStore, Depends(get_otp_store)],
    email_svc: Annotated[ResendEmailService, Depends(get_email_service)],
) -> OTPRequestResponse:
    """
    Step 1 of OTP login.
    Generates OTP instantly, returns 200 immediately.
    Email is sent in a background task (non-blocking).
    """
    email = body.email.lower()
    logger.info("[OTP-REQUEST] Email entered: %s", email)
    total_start = time.perf_counter()

    try:
        otp_store.cleanup_expired()
    except Exception:
        pass

    locked, secs = otp_store.is_locked(email)
    if locked:
        mins = secs // 60
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked. Please try again in {mins} minute(s).",
        )

    try:
        gen_start = time.perf_counter()
        otp, expires_in = otp_store.create_otp(email)
        gen_end = time.perf_counter()
        logger.info("[OTP-STORE] Generated OTP for %s in %.4fs | expires_in=%ds", email, gen_end - gen_start, expires_in)
        logger.info(
            "\n"
            "***** OTP CONSOLE FALLBACK *****\n"
            "  Email : %s\n"
            "  Code  : %s\n"
            "  Valid : %d minutes\n"
            "*******************************",
            email, otp, expires_in // 60,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    # Fire email in background — do NOT await, return instantly
    background_tasks.add_task(_send_otp_background, email_svc, email, otp)

    total_end = time.perf_counter()
    logger.info("[OTP-API] Response time for %s: %.4fs (email sending in background)", email, total_end - total_start)
    logger.info("[OTP-REQUEST] Completed for %s from %s", email, request.client)

    return OTPRequestResponse(
        message="Verification code sent. Check your email.",
        expires_in_seconds=expires_in,
        masked_email=_mask_email(email),
    )


@router.post("/verify-otp", response_model=OTPVerifyResponse, status_code=200)
async def verify_otp(
    body: OTPVerifyBody,
    request: Request,
    otp_store: Annotated[OTPStore, Depends(get_otp_store)],
    user_store: Annotated[UserStore, Depends(get_user_store)],
) -> OTPVerifyResponse:
    """
    Step 2 of OTP login.
    Verifies the 4-digit code. On success issues JWT tokens.
    Max 3 wrong attempts → 2-hour lockout.
    """
    if not is_jwt_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT authentication not configured. Set PREMONITION_JWT_SECRET.",
        )

    email = body.email.lower()
    success, message = otp_store.verify_otp(email, body.code)

    logger.info(
        "OTP verification %s for %s from %s — %s",
        "SUCCESS" if success else "FAILURE",
        email,
        request.client,
        message,
    )

    if not success:
        # Determine if locked after this failure
        locked, secs = otp_store.is_locked(email)
        if locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=message,
            )
        if "expired" in message.lower():
            raise HTTPException(status_code=status.HTTP_410_GONE, detail=message)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)

    # Determine role — use existing user role if registered, else default to CLINICIAN
    existing_user = user_store.get_user(email)
    role = existing_user.role if existing_user else _guest_role()

    return OTPVerifyResponse(
        message="Login successful.",
        access_token=create_access_token(email, role),
        refresh_token=create_refresh_token(email, role),
        expires_in=ACCESS_TOKEN_MINUTES * 60,
        role=role,
    )


@router.post("/resend-otp", response_model=OTPRequestResponse, status_code=200)
async def resend_otp(
    body: OTPResendBody,
    request: Request,
    background_tasks: BackgroundTasks,
    otp_store: Annotated[OTPStore, Depends(get_otp_store)],
    email_svc: Annotated[ResendEmailService, Depends(get_email_service)],
) -> OTPRequestResponse:
    """
    Invalidates the previous OTP and issues a new one.
    Returns instantly — email sent in background.
    """
    email = body.email.lower()

    locked, secs = otp_store.is_locked(email)
    if locked:
        mins = secs // 60
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account locked. Please try again in {mins} minute(s).",
        )

    otp_store.invalidate_otp(email)

    try:
        otp, expires_in = otp_store.create_otp(email)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    background_tasks.add_task(_send_otp_background, email_svc, email, otp)
    logger.info("OTP resend queued for %s from %s", email, request.client)

    return OTPRequestResponse(
        message="New verification code sent. Previous code is now invalid.",
        expires_in_seconds=expires_in,
        masked_email=_mask_email(email),
    )


# ── Demo Login (OTP fallback) ─────────────────────────────────────────────────

@router.post("/demo-login", response_model=OTPVerifyResponse, status_code=200)
async def demo_login(request: Request) -> OTPVerifyResponse:
    """
    Instant demo login — issues real JWT tokens for the built-in demo account.
    No OTP required. Intended as a fallback when email delivery is unavailable.
    The issued role is CLINICIAN (read-only clinical access).
    """
    if not is_jwt_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT authentication not configured. Set PREMONITION_JWT_SECRET.",
        )

    logger.info("[DEMO-LOGIN] Demo login used from %s", request.client)

    return OTPVerifyResponse(
        message="Demo login successful. Welcome to PREMONITION.",
        access_token=create_access_token(DEMO_EMAIL, DEMO_ROLE),
        refresh_token=create_refresh_token(DEMO_EMAIL, DEMO_ROLE),
        expires_in=ACCESS_TOKEN_MINUTES * 60,
        role=DEMO_ROLE,
    )
