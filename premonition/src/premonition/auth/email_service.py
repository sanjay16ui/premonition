"""SMTP email service for OTP delivery.

Replaces Resend with Gmail SMTP as requested.
Uses standard library smtplib via asyncio.to_thread for non-blocking execution.
"""

from __future__ import annotations

import logging
import os
import time
import smtplib
import asyncio
from email.message import EmailMessage

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USERNAME or "splenzer790@gmail.com")


def _build_html(otp: str, expires_minutes: int = 10) -> str:
    return (
        f"<div style='font-family:sans-serif;max-width:480px;margin:0 auto'>"
        f"<h2 style='color:#4f46e5'>PREMONITION</h2>"
        f"<p>Your login verification code is:</p>"
        f"<h1 style='font-size:48px;letter-spacing:12px;color:#1e293b'>{otp}</h1>"
        f"<p>Valid for <strong>{expires_minutes} minutes</strong>. Do not share this code.</p>"
        f"<hr style='border:none;border-top:1px solid #e2e8f0;margin:24px 0'>"
        f"<p style='font-size:12px;color:#94a3b8'>PREMONITION · Agentic AI Healthcare</p>"
        f"</div>"
    )


def _build_text(otp: str, expires_minutes: int = 10) -> str:
    return (
        f"PREMONITION — Login Verification Code\n\n"
        f"Your code: {otp}\n\n"
        f"Valid for {expires_minutes} minutes.\n"
        f"Do not share this code.\n\n"
        f"— PREMONITION AI"
    )


def _send_sync(to_email: str, otp: str) -> None:
    """Synchronous SMTP sending logic."""
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        raise ValueError("SMTP_USERNAME or SMTP_PASSWORD not set in environment.")

    msg = EmailMessage()
    msg['Subject'] = "PREMONITION Login Verification Code"
    msg['From'] = EMAIL_FROM
    msg['To'] = to_email

    msg.set_content(_build_text(otp))
    msg.add_alternative(_build_html(otp), subtype='html')

    logger.debug("Connecting to SMTP server %s:%s", SMTP_HOST, SMTP_PORT)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


class ResendEmailService:
    """Sends OTP emails via Gmail SMTP.
    
    Name kept as ResendEmailService for compatibility with the rest of the application
    without changing dependency injection bindings.
    """

    def __init__(self) -> None:
        self._dev_mode = not bool(SMTP_PASSWORD)

        if self._dev_mode:
            logger.warning(
                "SMTP_PASSWORD not set — email service running in DEV MODE. "
                "OTPs will be printed to the server console."
            )
        else:
            logger.info(
                "SMTP Email Service initialised (LIVE mode). from=%s host=%s",
                EMAIL_FROM, SMTP_HOST
            )

    # ──────────────────────────── Lifecycle ──────────────────────────────────

    async def close(self) -> None:
        """Cleanup if needed. No persistent connection pool used for SMTP currently."""
        logger.debug("SMTP EmailService closed.")

    # ──────────────────────────── Send ───────────────────────────────────────

    async def send_otp_email(self, to_email: str, otp: str) -> bool:
        """Send OTP email to *to_email* (the exact address typed by the user).

        Timing logged at INFO level:
          - email_entered  : the exact recipient
          - total_delivery : wall-clock from call start to return
        """
        total_start = time.perf_counter()

        # ── DEV MODE ──────────────────────────────────────────────────────────
        if self._dev_mode:
            elapsed = time.perf_counter() - total_start
            logger.info(
                "\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  [DEV MODE] PREMONITION OTP\n"
                f"  Email entered : {to_email}\n"
                f"  Code          : {otp}\n"
                f"  Delivery time : {elapsed:.4f}s\n"
                "  (No email sent — SMTP credentials not set)\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
            return True

        # ── LIVE MODE ─────────────────────────────────────────────────────────
        try:
            logger.info("[OTP-EMAIL-START] Sending OTP to %s via SMTP", to_email)
            
            # Run blocking SMTP operations in a thread pool
            await asyncio.to_thread(_send_sync, to_email, otp)
            
            total_elapsed = time.perf_counter() - total_start
            logger.info(
                "[OTP-EMAIL-SUCCESS] Delivered OTP to %s successfully in %.4fs",
                to_email, total_elapsed
            )
            return True

        except Exception as exc:
            total_elapsed = time.perf_counter() - total_start
            logger.error(
                "[OTP-EMAIL-FAILED] Failed to send OTP email to %s after %.4fs: %s",
                to_email, total_elapsed, exc,
                exc_info=True
            )
            return False
