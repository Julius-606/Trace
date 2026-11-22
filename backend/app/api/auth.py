import os
import time
import logging
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Form, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import database_models as models
from app.schemas import api_schemas as schemas
from app.core import security
from app.core.app_dispatcher import identify_target_app

logger = logging.getLogger("trace_auth")

router = APIRouter(tags=["Authentication"])

from app.core.otp_service import (
    generate_cryptographic_otp,
    hash_otp_token,
    check_request_rate_limit,
    record_request_timestamp,
    validate_otp,
    dev_otp_bypass_enabled,
    PENDING_OTPS,
    EmailDispatcher,
    OTP_EXPIRATION_SECONDS,
    RESEND_COOLDOWN_SECONDS
)


@router.post("/send-otp", response_model=schemas.RequestOtpResponse)
@router.post("/request-otp", response_model=schemas.RequestOtpResponse)
async def request_verification_otp(request: schemas.RequestOtpRequest, db: Session = Depends(get_db)):
    """
    Generates and securely dispatches a cryptographically secure 6-digit numeric OTP.
    Enforces rate-limiting (60s cooldown, max 3 requests / 5 mins) and hashes tokens at rest.
    """
    clean_email = request.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")

    action = request.action.strip().lower()

    # 1. Enforce Rate Limiting & Cooldown
    allowed, rate_err, cooldown_left = check_request_rate_limit(clean_email)
    if not allowed:
        raise HTTPException(status_code=429, detail=rate_err)

    existing_user = db.query(models.User).filter(models.User.email == clean_email).first()

    if action == "forgot_password":
        if not existing_user:
            # Check if this email exists in DebateHub members pool
            debatehub_member = False
            try:
                debatehub_url = os.getenv("DEBATEHUB_INTERNAL_URL", "http://127.0.0.1:3000")
                with httpx.Client(timeout=2.0) as client:
                    resp = client.get(f"{debatehub_url}/api/members")
                    if resp.status_code == 200:
                        members = resp.json()
                        if any(isinstance(m, dict) and m.get("email", "").lower() == clean_email for m in members):
                            debatehub_member = True
            except Exception:
                pass
            if not debatehub_member:
                raise HTTPException(status_code=404, detail="No registered account found with this email address. Please check your email or sign up.")
    elif action == "signup":
        if existing_user:
            raise HTTPException(status_code=400, detail="An account with this email address is already registered.")

    # 2. Cryptographically secure 6-digit generation (secrets module)
    otp = generate_cryptographic_otp(length=6)
    hashed_otp = hash_otp_token(clean_email, otp)
    now = time.time()
    expires_at = now + OTP_EXPIRATION_SECONDS  # 10 minutes strict maximum lifecycle

    # Record rate-limit trigger up-front so the mail path cannot be abused to
    # bombard an inbox even when delivery fails.
    record_request_timestamp(clean_email)

    # 3. Deliver via Transactional Email Dispatcher (generic SMTP). Fail LOUD:
    #    if the email cannot be delivered, do NOT persist a code the user will never receive.
    sent_live_smtp = EmailDispatcher.send_otp_email(clean_email, otp, action)

    if not sent_live_smtp and not dev_otp_bypass_enabled():
        try:
            from app.api import admin
            admin.notify_admin(
                db=db,
                category="SECURITY",
                title=f"Auth OTP delivery FAILED: {action.upper()}",
                message=f"Could not deliver a verification email to {clean_email} ({action}). SMTP delivery failed or is unconfigured.",
                level="warning",
                details=f"Email: {clean_email}\nAction: {action}\nHint: check SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD/SMTP_FROM on the server."
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=503,
            detail="We could not deliver the verification email right now. The issue has been logged. Please try again later."
        )

    # 4. Invalidate any previous unverified tokens for this (email, action) in DB
    db.query(models.EmailVerificationOTP).filter(
        models.EmailVerificationOTP.email == clean_email,
        models.EmailVerificationOTP.action == action,
        models.EmailVerificationOTP.is_used == False  # noqa: E712
    ).update({"is_used": True})

    # 5. Record new secure token hash in database ledger (hash only — never plaintext)
    cache_key = (clean_email, action)
    PENDING_OTPS[cache_key] = {
        "hashed_otp": hashed_otp,
        "expires_at": expires_at,
        "attempt_count": 0,
        "verified": False
    }

    try:
        otp_record = models.EmailVerificationOTP(
            email=clean_email,
            hashed_otp=hashed_otp,
            otp=None,  # Never persist the plaintext code
            action=action,
            attempt_count=0,
            created_at=now,
            expires_at=expires_at,
            is_used=False
        )
        db.add(otp_record)
        db.commit()
    except Exception as e:
        logger.error(f"Error persisting OTP record: {e}")
        db.rollback()

    # Admin Audit Notification
    try:
        from app.api import admin
        admin.notify_admin(
            db=db,
            category="SECURITY",
            title=f"Auth OTP: {action.upper()}",
            message=f"Cryptographic verification token generated for {clean_email} ({action}).",
            level="info",
            details=f"Email: {clean_email}\nAction: {action}\nExpires: 10 mins\nLive SMTP: {sent_live_smtp}"
        )
    except Exception:
        pass

    action_name = "Password reset" if action == "forgot_password" else "Verification"
    if sent_live_smtp:
        note = " Verification code sent to your inbox."
    else:
        note = " Email delivery unavailable; development bypass code accepted instead."
    return {
        "status": "success",
        "message": f"{action_name} code generated for {clean_email}.{note}",
        "email": clean_email,
        "expires_in_seconds": OTP_EXPIRATION_SECONDS,
        "resend_cooldown_seconds": RESEND_COOLDOWN_SECONDS,
        # The plaintext code is returned ONLY when the development escape hatch
        # (ENABLE_DEV_OTP_BYPASS) is explicitly enabled. Never in production.
        "otp_preview": otp if dev_otp_bypass_enabled() else None
    }


@router.post("/verify-otp", response_model=schemas.VerifyOtpResponse)
async def verify_otp(request: schemas.VerifyOtpRequest, db: Session = Depends(get_db)):
    """
    Non-destructive verification probe: proves possession of the code WITHOUT burning it,
    so the completing action (signup / password reset) can still consume it afterwards.
    Enforces maximum failure attempt limits (brute-force defense).

    Note: single-use enforcement happens when the code is consumed by the completing
    action (e.g. /signup, /forgot-password/reset).
    """
    clean_email = request.email.strip().lower()
    clean_otp = request.otp.strip()
    action = request.action.strip().lower()

    is_valid, err = validate_otp(db, clean_email, clean_otp, action, consume=False)
    if not is_valid:
        detail = err or "Invalid verification code."
        status = 429 if "invalidated" in detail else 400
        raise HTTPException(status_code=status, detail=detail)

    # Generate ephemeral auth verification session token
    auth_token = security.create_access_token(
        data={"sub": clean_email, "action": action, "type": "otp_verified"},
        expires_delta=None
    )

    return {
        "status": "success",
        "message": "Email verified successfully.",
        "token": auth_token,
        "email": clean_email,
        "expires_in": OTP_EXPIRATION_SECONDS
    }


@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    """Authenticates users across Trace Medical Academic Engine and GLUK DebateHub."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    raw_email = str(body.get("email") or "").strip()
    clean_email = raw_email.lower()
    password = str(body.get("password") or "")

    if not raw_email:
        raise HTTPException(status_code=400, detail="Email is required")

    target_app, reason = identify_target_app(request)

    # If the request is explicitly targeted for DebateHub (by header, referer, path, or institution email)
    if target_app == "DebateHub" or "@gluk." in clean_email or clean_email == "juliusgachoki26@gmail.com":
        try:
            debatehub_url = os.getenv("DEBATEHUB_INTERNAL_URL", "http://127.0.0.1:3000")
            async with httpx.AsyncClient(timeout=10.0) as client:
                upstream = await client.post(
                    f"{debatehub_url}/api/auth/login",
                    json=body,
                    headers={"Content-Type": "application/json"}
                )
                if upstream.status_code == 200:
                    return upstream.json()
                elif upstream.status_code >= 400:
                    err_detail = upstream.json().get("error", "Invalid DebateHub credentials")
                    raise HTTPException(status_code=upstream.status_code, detail=err_detail)
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning(f"DebateHub direct auth dispatch error: {exc}")

    # 1. Trace user database check
    user = db.query(models.User).filter(
        (models.User.email == clean_email) | (models.User.username == raw_email)
    ).first()

    is_trace_authenticated = False
    if user:
        if security.verify_password(password, user.hashed_password):
            is_trace_authenticated = True
        elif dev_otp_bypass_enabled() and password in ["admin123", "student123", "teacher123", "parent123", "trace2026", "gluk2026", "password123"]:
            # Development escape hatch only (ENABLE_DEV_OTP_BYPASS). Never honored in production.
            is_trace_authenticated = True

    if is_trace_authenticated and user:
        access_token = security.create_access_token(data={"sub": str(user.id)})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": str(user.id),
            "username": user.full_name or user.username,
            "role": user.role,
            "success": True,
            "token": f"token-{user.id}-{int(time.time() * 1000)}",
            "user": {
                "id": str(user.id),
                "fullName": user.full_name or user.username,
                "email": user.email,
                "role": "executive" if user.role == "Admin" else "member",
                "membershipStatus": "Paid"
            }
        }

    # 2. Fallback check on DebateHub Express if not already targeted
    if target_app != "DebateHub":
        try:
            debatehub_url = os.getenv("DEBATEHUB_INTERNAL_URL", "http://127.0.0.1:3000")
            async with httpx.AsyncClient(timeout=10.0) as client:
                upstream = await client.post(
                    f"{debatehub_url}/api/auth/login",
                    json=body,
                    headers={"Content-Type": "application/json"}
                )
                if upstream.status_code == 200:
                    return upstream.json()
        except Exception as exc:
            logger.warning(f"DebateHub auth proxy forward notice: {exc}")

    raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/signup")
@router.post("/register")
async def api_json_signup(request: Request, db: Session = Depends(get_db)):
    """Registers a new user with verified email OTP, password, and curriculum profile metadata."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # If this is a DebateHub registration payload
    is_debatehub_payload = (
        "studentId" in body
        or "faculty" in body
        or "executivePosition" in body
        or "yearOfStudy" in body
        or "duesAmountKes" in body
        or (body.get("role") in ["member", "executive", "alumni"] and not body.get("otp"))
    )

    if is_debatehub_payload:
        try:
            debatehub_url = os.getenv("DEBATEHUB_INTERNAL_URL", "http://127.0.0.1:3000")
            async with httpx.AsyncClient(timeout=10.0) as client:
                upstream = await client.post(
                    f"{debatehub_url}/api/auth/signup",
                    json=body,
                    headers={"Content-Type": "application/json"}
                )
                if upstream.status_code in [200, 201]:
                    return upstream.json()
                elif upstream.status_code >= 400:
                    err_msg = upstream.json().get("error", "Registration failed")
                    raise HTTPException(status_code=upstream.status_code, detail=err_msg)
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning(f"DebateHub signup forward failed: {exc}")

    # Standard Trace student registration
    user_in = schemas.UserCreate(**body)
    clean_email = user_in.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    # 1. Verify Password Strength (checked before consuming the OTP)
    if len(user_in.password.strip()) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    # 2. Check Duplicate Account (checked before consuming the OTP)
    existing_user = db.query(models.User).filter(models.User.email == clean_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    # 3. Verify OTP (single-use; consumed only now that everything else checks out)
    clean_otp = (user_in.otp or "").strip()
    otp_ok, otp_err = validate_otp(db, clean_email, clean_otp, "signup", consume=True)
    if not otp_ok:
        raise HTTPException(
            status_code=400,
            detail=otp_err or "Email verification required. Please click 'Send Code' and enter the 6-digit OTP sent to your email."
        )

    # Derive username
    candidate_username = (user_in.username or user_in.full_name or clean_email.split("@")[0]).strip()
    base_user = candidate_username
    suffix = 1
    while db.query(models.User).filter(models.User.username == candidate_username).first():
        candidate_username = f"{base_user}_{suffix}"
        suffix += 1

    semester_status = user_in.level_of_study or user_in.semester_status or "Year 1"

    new_user = models.User(
        username=candidate_username,
        full_name=user_in.full_name or candidate_username,
        email=clean_email,
        hashed_password=security.get_password_hash(user_in.password),
        role=user_in.role or "Student",
        age=user_in.age,
        level_of_study=user_in.level_of_study,
        course_pursued=user_in.course_pursued,
        referral_code=user_in.referral_code,
        sensory_mode=user_in.sensory_mode,
        difficulty=user_in.difficulty,
        ai_persona=user_in.ai_persona,
        semester_status=semester_status,
        is_email_verified=True,
        interests=user_in.interests or [],
        trace_coins=200,
        active_units=["Biochemistry II", "General Surgery", "Internal Medicine"]
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Superuser alert
    try:
        from app.api import admin
        admin.notify_admin(
            db=db,
            category="NEW_USER",
            title="New User Verified & Registered",
            message=f"{new_user.full_name} ({clean_email}) enrolled in {new_user.course_pursued or 'General Curriculum'} [{new_user.level_of_study or 'Year 1'}].",
            level="info",
            details=f"Name: {new_user.full_name}\nEmail: {clean_email}\nAge: {new_user.age}\nCourse: {new_user.course_pursued}\nLevel: {new_user.level_of_study}\nReferral: {new_user.referral_code}"
        )
    except Exception:
        pass

    access_token = security.create_access_token(data={"sub": str(new_user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(new_user.id),
        "username": new_user.full_name or new_user.username,
        "role": new_user.role,
        "success": True,
        "token": f"token-{new_user.id}-{int(time.time() * 1000)}",
        "user": {
            "id": str(new_user.id),
            "fullName": new_user.full_name or new_user.username,
            "email": new_user.email,
            "role": "member",
            "membershipStatus": "Pending"
        }
    }


@router.post("/forgot-password/reset", response_model=schemas.GenericAuthResponse)
async def forgot_password_reset(request: schemas.ForgotPasswordResetRequest, db: Session = Depends(get_db)):
    """Resets user password after verifying the 6-digit OTP sent to their registered email."""
    clean_email = request.email.strip().lower()
    clean_otp = request.otp.strip()

    if len(request.new_password.strip()) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters.")

    user = db.query(models.User).filter(models.User.email == clean_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No registered account found with this email address.")

    # Validate OTP (single-use; consumed on success)
    otp_ok, otp_err = validate_otp(db, clean_email, clean_otp, "forgot_password", consume=True)
    if not otp_ok:
        raise HTTPException(
            status_code=400,
            detail=otp_err or "Invalid or expired reset code. Please check the code sent to your email or request a new one."
        )

    # Update password
    user.hashed_password = security.get_password_hash(request.new_password)
    db.commit()

    try:
        from app.api import admin
        admin.notify_admin(
            db=db,
            category="SECURITY",
            title="Password Reset Completed",
            message=f"User {user.username} ({clean_email}) successfully reset their password via OTP.",
            level="info",
            details=f"Email: {clean_email}\nTimestamp: {time.ctime()}"
        )
    except Exception:
        pass

    return {
        "status": "success",
        "message": "Password reset successfully. You can now log in with your new password."
    }


@router.post("/signup-form")  # Form submission for HTML web pages
async def handle_signup(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("Student"),
    age: Optional[int] = Form(None),
    level_of_study: Optional[str] = Form(None),
    course_pursued: Optional[str] = Form(None),
    referral_code: Optional[str] = Form(None),
    otp: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    clean_email = email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    existing_user = db.query(models.User).filter(models.User.email == clean_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    if len(password.strip()) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    # Verify OTP (single-use; consumed only now that everything else checks out)
    otp_ok, otp_err = validate_otp(db, clean_email, (otp or "").strip(), "signup", consume=True)
    if not otp_ok:
        raise HTTPException(
            status_code=400,
            detail=otp_err or "Email verification required. Please enter the 6-digit code sent to your email."
        )

    candidate_username = (full_name or clean_email.split("@")[0]).strip()
    base_user = candidate_username
    suffix = 1
    while db.query(models.User).filter(models.User.username == candidate_username).first():
        candidate_username = f"{base_user}_{suffix}"
        suffix += 1

    new_user = models.User(
        username=candidate_username,
        full_name=full_name,
        email=clean_email,
        hashed_password=security.get_password_hash(password),
        role=role,
        age=age,
        level_of_study=level_of_study,
        course_pursued=course_pursued,
        referral_code=referral_code,
        semester_status=level_of_study or "Year 1",
        is_email_verified=True,
        trace_coins=200
    )
    db.add(new_user)
    db.commit()

    return {"status": "success", "message": "Account created successfully."}
