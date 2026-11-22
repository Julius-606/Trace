"""
Cryptographic Token Generation, Hashing, and Verification Service.
Enforces strict security best practices:
- Cryptographically secure 6-digit numeric generation (via python secrets module).
- Max 10-minute expiration lifecycle.
- Hashing at rest with salt and HMAC pepper (never plaintext).
- Brute-force attempt tracking and rate-limiting cooldowns.
- Constant-time verification comparisons and single-use token burning.
- Codes are NEVER written to logs or API responses in production.
  (Set ENABLE_DEV_OTP_BYPASS=true for local development only.)
"""

import os
import time
import secrets
import hashlib
import logging
import smtplib
from typing import Dict, Tuple, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr
from app.core.config import settings

logger = logging.getLogger("trace_otp_security")

# Configuration Constants
OTP_EXPIRATION_SECONDS = 600  # 10 minutes maximum lifetime
RESEND_COOLDOWN_SECONDS = 60   # 60 seconds resend cooldown
MAX_VERIFICATION_ATTEMPTS = 5  # Invalidate token after 5 failed attempts
MAX_REQUESTS_PER_WINDOW = 3    # Max 3 requests per 5 minutes per email
RATE_LIMIT_WINDOW = 300        # 5 minutes

# Well-known code accepted ONLY when ENABLE_DEV_OTP_BYPASS is explicitly enabled.
DEV_OTP_BYPASS_CODE = "123456"

# In-memory tracking for rate-limiting: email -> list of request timestamps
_REQUEST_HISTORY: Dict[str, list] = {}

# In-memory ephemeral active OTP sessions: (email, action) -> session metadata.
# Never stores the plaintext code; holds the PBKDF2 hash only.
PENDING_OTPS: Dict[Tuple[str, str], Dict[str, Any]] = {}

PEPPER = os.getenv("OTP_PEPPER_SECRET") or getattr(settings, "SECRET_KEY", "")
if not os.getenv("OTP_PEPPER_SECRET") and not getattr(settings, "SECRET_KEY", None):
    logger.warning(
        "[OTP] Neither OTP_PEPPER_SECRET nor ORBIT_SECRET_KEY/JWT_SECRET_KEY is set. "
        "Using an ephemeral-insecure default pepper. Set OTP_PEPPER_SECRET in production."
    )
if not PEPPER:
    PEPPER = "trace-vault-crypto-pepper-2026"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def dev_otp_bypass_enabled() -> bool:
    """
    Development escape hatch. ONLY honored when ENABLE_DEV_OTP_BYPASS is explicitly
    set to a truthy value in the environment. Defaults OFF. Never enable in production.
    When enabled, the fixed code 123456 is accepted for any (email, action) and
    otp_preview is included in API responses to ease local testing.
    """
    return _env_bool("ENABLE_DEV_OTP_BYPASS", False)


def generate_cryptographic_otp(length: int = 6) -> str:
    """
    Generates a cryptographically secure numeric OTP using Python's secrets module.
    Guarantees true randomness rather than pseudo-random functions like random.random().
    """
    lower_bound = 10 ** (length - 1)
    upper_bound = (10 ** length) - 1
    code = secrets.randbelow(upper_bound - lower_bound + 1) + lower_bound
    return str(code)


def hash_otp_token(email: str, otp: str) -> str:
    """
    Hashes the OTP token for secure storage at rest using PBKDF2-HMAC-SHA256
    with an email-derived salt and environment pepper.
    """
    salt = f"{email.lower().strip()}:{PEPPER}".encode("utf-8")
    derived = hashlib.pbkdf2_hmac("sha256", otp.encode("utf-8"), salt, 100_000)
    return derived.hex()


def verify_otp_token(email: str, candidate_otp: str, stored_hash: str) -> bool:
    """
    Validates candidate OTP against stored hash using constant-time string comparison
    to prevent side-channel timing attacks.
    """
    candidate_hash = hash_otp_token(email, candidate_otp)
    return secrets.compare_digest(candidate_hash, stored_hash)


def check_request_rate_limit(email: str) -> Tuple[bool, Optional[str], int]:
    """
    Validates rate limiting for OTP generation:
    - Minimum 60-second cooldown between consecutive requests.
    - Maximum 3 requests per 5-minute rolling window.
    Returns: (is_allowed, error_message, remaining_cooldown_seconds)
    """
    email_clean = email.lower().strip()
    now = time.time()

    history = _REQUEST_HISTORY.get(email_clean, [])
    # Filter to active window
    history = [t for t in history if now - t < RATE_LIMIT_WINDOW]
    _REQUEST_HISTORY[email_clean] = history

    if history:
        last_request = history[-1]
        elapsed = now - last_request
        if elapsed < RESEND_COOLDOWN_SECONDS:
            cooldown_left = int(RESEND_COOLDOWN_SECONDS - elapsed)
            return False, f"Please wait {cooldown_left}s before requesting a new verification code.", cooldown_left

    if len(history) >= MAX_REQUESTS_PER_WINDOW:
        oldest = history[0]
        wait_time = int(RATE_LIMIT_WINDOW - (now - oldest))
        return False, f"Too many verification requests. Please try again in {wait_time}s.", wait_time

    return True, None, 0


def record_request_timestamp(email: str):
    """Logs the timestamp of a successful OTP request for rate limiting."""
    email_clean = email.lower().strip()
    now = time.time()
    history = _REQUEST_HISTORY.get(email_clean, [])
    history.append(now)
    _REQUEST_HISTORY[email_clean] = history


def _burn_token(db, record, cache_key) -> None:
    """Single-use enforcement: invalidates the DB record and drops the memory entry."""
    if record is not None:
        record.is_used = True
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("[OTP] Failed to burn OTP record: %s", exc)
    if cache_key in PENDING_OTPS:
        del PENDING_OTPS[cache_key]


def _set_attempts(db, record, entry, attempts: int) -> None:
    if record is not None:
        record.attempt_count = attempts
        try:
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error("[OTP] Failed to persist attempt counter: %s", exc)
    if entry is not None:
        entry["attempt_count"] = attempts


def validate_otp(
    db,
    email: str,
    otp: str,
    action: str = "signup",
    *,
    consume: bool = True,
) -> Tuple[bool, Optional[str]]:
    """
    Shared, constant-time OTP validator used by every verification surface
    (JSON signup, browser signup, forgot-password reset, verify-otp probe).

    Args:
        db: SQLAlchemy session.
        email: Recipient email (case-insensitive).
        otp: Candidate 6-digit code supplied by the user.
        action: "signup" | "forgot_password" (namespaces the token).
        consume: When True (default), a successful verification burns the token.
                 Pass consume=False for a non-destructive pre-check.

    Returns:
        (is_valid, error_message). error_message is None on success.
    """
    from app.models import database_models as models  # lazy import: avoids cycles

    clean_email = (email or "").lower().strip()
    clean_otp = (otp or "").strip()
    action = (action or "signup").strip().lower()
    now = time.time()

    if not clean_otp:
        return False, "Please enter the 6-digit verification code."

    # Development escape hatch (disabled by default). Never active in production.
    if dev_otp_bypass_enabled() and clean_otp == DEV_OTP_BYPASS_CODE:
        return True, None

    cache_key = (clean_email, action)
    entry = PENDING_OTPS.get(cache_key)

    record = (
        db.query(models.EmailVerificationOTP)
        .filter(
            models.EmailVerificationOTP.email == clean_email,
            models.EmailVerificationOTP.action == action,
            models.EmailVerificationOTP.is_used == False,  # noqa: E712
        )
        .order_by(models.EmailVerificationOTP.id.desc())
        .first()
    )

    if not record and not entry:
        return False, "No active verification code found for this email. Please request a new code."

    # Expiration lifecycle (strict 10-minute maximum)
    expires_at = record.expires_at if record else entry.get("expires_at", 0)
    if expires_at < now:
        _burn_token(db, record, cache_key)
        return False, "This verification code has expired (10 minutes maximum). Please request a new code."

    # Brute-force pre-check: the code is already burned after MAX_VERIFICATION_ATTEMPTS failures.
    current_attempts = (record.attempt_count if record else entry.get("attempt_count", 0))
    if current_attempts >= MAX_VERIFICATION_ATTEMPTS:
        _burn_token(db, record, cache_key)
        return False, "Too many failed verification attempts. This code has been invalidated for security. Please request a new code."

    # Constant-time comparison against the PBKDF2 hash at rest.
    is_valid = False
    if record and record.hashed_otp:
        is_valid = verify_otp_token(clean_email, clean_otp, record.hashed_otp)
    elif record and record.otp:  # legacy rows written before hash-only storage
        is_valid = secrets.compare_digest(str(record.otp), clean_otp)
    elif entry and entry.get("hashed_otp"):
        is_valid = verify_otp_token(clean_email, clean_otp, entry["hashed_otp"])
    elif entry and entry.get("otp"):  # legacy in-memory entries
        is_valid = secrets.compare_digest(str(entry["otp"]), clean_otp)

    if not is_valid:
        # Only FAILURES count toward the lockout budget — successful probes never do.
        attempts = current_attempts + 1
        if attempts >= MAX_VERIFICATION_ATTEMPTS:
            _set_attempts(db, record, entry, attempts)
            _burn_token(db, record, cache_key)
            return False, "Too many failed verification attempts. This code has been invalidated for security. Please request a new code."
        _set_attempts(db, record, entry, attempts)
        remaining = MAX_VERIFICATION_ATTEMPTS - attempts
        return False, f"Invalid verification code. {remaining} attempt(s) remaining before the code is locked."

    if consume:
        _burn_token(db, record, cache_key)
    return True, None


class EmailDispatcher:
    """
    Transactional email delivery via generic SMTP (SendGrid, Resend, AWS SES,
    Brevo, Mailgun, Gmail App Passwords, local Mailpit/MailHog, ...).

    Environment variables:
        SMTP_HOST     - e.g. smtp.gmail.com (required to deliver; unset = delivery disabled)
        SMTP_PORT     - default 587 (use 465 with SMTP_USE_SSL=true, or 25/1025 plain relays)
        SMTP_USER     - SMTP username (omit for unauthenticated internal relays)
        SMTP_PASSWORD - SMTP password / app password / API key
        SMTP_FROM     - From address (defaults to SMTP_USER)
        SMTP_USE_TLS  - "true" (default) to issue STARTTLS on connect
        SMTP_USE_SSL  - "true" to use implicit SSL (port 465); disables STARTTLS
    """

    @staticmethod
    def send_otp_email(
        recipient_email: str,
        otp_code: str,
        action: str = "signup"
    ) -> bool:
        smtp_host = os.environ.get("SMTP_HOST")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_password = os.environ.get("SMTP_PASSWORD")
        smtp_sender = os.environ.get("SMTP_FROM") or smtp_user or "noreply@trace-learning.edu"
        use_ssl = _env_bool("SMTP_USE_SSL", False)
        use_tls = _env_bool("SMTP_USE_TLS", True) and not use_ssl

        is_reset = (action.lower() == "forgot_password")
        action_name = "Password Reset" if is_reset else "Account Verification"
        subject = "Trace Password Reset Code" if is_reset else "Trace Verification Code"

        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 540px; margin: 0 auto; padding: 24px; background: #0f172a; border-radius: 16px; border: 1px solid #1e293b; color: #f8fafc;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h2 style="color: #6366f1; margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.5px;">Trace Academic &amp; Multi-Disciplinary Engine</h2>
                <p style="color: #94a3b8; font-size: 13px; margin-top: 4px;">{action_name} Protocol</p>
            </div>
            <div style="background: #1e293b; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #334155;">
                <p style="color: #cbd5e1; font-size: 14px; margin: 0 0 16px 0;">Use the single-use authorization code below to verify your email address:</p>
                <div style="font-size: 32px; font-weight: 900; letter-spacing: 8px; color: #38bdf8; font-family: monospace; padding: 12px; background: #0b0f19; border-radius: 8px; display: inline-block;">
                    {otp_code}
                </div>
                <p style="color: #64748b; font-size: 12px; margin: 16px 0 0 0;">This code expires in <strong>10 minutes</strong> and can only be used once.</p>
            </div>
            <p style="color: #475569; font-size: 11px; text-align: center; margin-top: 24px; line-height: 1.5;">
                If you did not initiate this request, you can safely ignore this email. Never share your verification code with anyone.
            </p>
        </div>
        """

        plain_text = f"""Trace Verification Code: {otp_code}
Action: {action_name}
Valid for: 10 minutes (single-use)

Enter this code on the application verification screen. If you did not request this, please ignore this email."""

        if not smtp_host:
            logger.error(
                "[EMAIL] SMTP_HOST is not configured. Verification email to '%s' was NOT delivered. "
                "Set SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD/SMTP_FROM to enable delivery.",
                recipient_email,
            )
            return False

        # Never log the code itself — only delivery metadata.
        logger.info("[EMAIL] Dispatching %s email to '%s' via %s:%s (ssl=%s tls=%s)",
                    action, recipient_email, smtp_host, smtp_port, use_ssl, use_tls)
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = smtp_sender
            message["To"] = recipient_email
            message.attach(MIMEText(plain_text, "plain"))
            message.attach(MIMEText(html_body, "html"))

            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)

            # Envelope sender MUST be a bare address, even if SMTP_FROM has a display name
            envelope_from = parseaddr(smtp_sender)[1] or smtp_sender

            with server:
                server.ehlo()
                if use_tls:
                    server.starttls()
                    server.ehlo()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                else:
                    logger.warning("[EMAIL] SMTP credentials not set; attempting unauthenticated relay to %s:%s", smtp_host, smtp_port)
                server.sendmail(envelope_from, [recipient_email], message.as_string())

            logger.info("[EMAIL] Verification email delivered to '%s'", recipient_email)
            return True
        except Exception as exc:
            logger.warning("[EMAIL] Delivery to '%s' failed: %s", recipient_email, exc)
            return False
