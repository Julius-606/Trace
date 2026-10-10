import os
import time
import random
import logging
import smtplib
from typing import Optional, Dict, Tuple, Any
from email.mime.text import MIMEText
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import database_models as models
from app.schemas import api_schemas as schemas
from app.core import security

logger = logging.getLogger("trace_auth")

router = APIRouter(tags=["Authentication"])

# Resilient in-memory cache for pending OTPs: (email_lower, action) -> {otp, expires_at}
PENDING_OTPS: Dict[Tuple[str, str], Dict[str, Any]] = {}

def send_email_otp(email: str, otp: str, action: str) -> bool:
    """Attempts to deliver verification OTP to recipient email. Logs output in all circumstances."""
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_sender = os.environ.get("SMTP_FROM", smtp_user or "noreply@trace-learning.edu")

    is_forgot = (action == "forgot_password")
    action_label = "Password Reset" if is_forgot else "Email Verification"
    subject = f"Edu-AI Trace: {action_label} Code [{otp}]"

    body_text = f"""Hello,

Your one-time verification code (OTP) for Edu-AI Trace {action_label.lower()} is:

    ======================
            {otp}
    ======================

This code is valid for 10 minutes. For your account security, never share this code with anyone.

Best regards,
Edu-AI Trace Adaptive Academic & Medical Infrastructure
"""

    logger.info(f"[SECURITY OTP DISPATCH] Action: '{action}' | Target: '{email}' | Code: '{otp}'")

    if smtp_host and smtp_user and smtp_password:
        try:
            msg = MIMEText(body_text)
            msg["Subject"] = subject
            msg["From"] = smtp_sender
            msg["To"] = email

            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_sender, [email], msg.as_string())
            logger.info(f"[SMTP SUCCESS] Dispatched OTP email to {email}")
            return True
        except Exception as e:
            logger.warning(f"[SMTP NOTICE] Could not send live email via SMTP: {e}. OTP logged to console & admin vault.")
            return False
    return False


@router.post("/send-otp", response_model=schemas.SendOtpResponse)
async def send_verification_otp(request: schemas.SendOtpRequest, db: Session = Depends(get_db)):
    """Generates and delivers a 6-digit verification code to the target email address."""
    clean_email = request.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="Please provide a valid email address.")

    action = request.action.strip().lower()
    existing_user = db.query(models.User).filter(models.User.email == clean_email).first()

    if action == "forgot_password":
        if not existing_user:
            raise HTTPException(status_code=404, detail="No registered account found with this email address.")
    elif action == "signup":
        if existing_user:
            raise HTTPException(status_code=400, detail="An account with this email address is already registered.")

    # Generate secure 6-digit OTP
    otp = f"{random.randint(100000, 999999)}"
    expires_at = time.time() + 600.0  # 10 minutes

    # Store in fast in-memory cache
    PENDING_OTPS[(clean_email, action)] = {
        "otp": otp,
        "expires_at": expires_at,
        "verified": False
    }

    # Record in database ledger
    try:
        otp_record = models.EmailVerificationOTP(
            email=clean_email,
            otp=otp,
            action=action,
            created_at=time.time(),
            expires_at=expires_at,
            is_used=False
        )
        db.add(otp_record)
        db.commit()
    except Exception as e:
        logger.error(f"Error persisting OTP record: {e}")

    # Send email or log
    send_email_otp(clean_email, otp, action)

    # Superuser notification
    try:
        from app.api import admin
        admin.notify_admin(
            db=db,
            category="SECURITY",
            title=f"Auth OTP: {action.upper()}",
            message=f"Verification code sent to {clean_email} for {action}. Code: {otp}",
            level="info",
            details=f"Email: {clean_email}\nAction: {action}\nCode: {otp}\nExpires: 10 mins"
        )
    except Exception:
        pass

    action_name = "Password reset" if action == "forgot_password" else "Verification"
    return {
        "status": "success",
        "message": f"{action_name} code sent to {clean_email}.",
        "email": clean_email,
        "otp_preview": otp  # Accessible for preview/sandbox verification
    }


@router.post("/verify-otp", response_model=schemas.GenericAuthResponse)
async def verify_otp(request: schemas.VerifyOtpRequest, db: Session = Depends(get_db)):
    """Verifies that an OTP entered by the user matches the active code."""
    clean_email = request.email.strip().lower()
    clean_otp = request.otp.strip()
    action = request.action.strip().lower()

    is_valid = False

    # Check cache
    cache_key = (clean_email, action)
    if cache_key in PENDING_OTPS:
        entry = PENDING_OTPS[cache_key]
        if entry["otp"] == clean_otp and entry["expires_at"] > time.time():
            entry["verified"] = True
            is_valid = True

    # Check database
    if not is_valid:
        record = db.query(models.EmailVerificationOTP).filter(
            models.EmailVerificationOTP.email == clean_email,
            models.EmailVerificationOTP.otp == clean_otp,
            models.EmailVerificationOTP.action == action,
            models.EmailVerificationOTP.is_used == False,
            models.EmailVerificationOTP.expires_at > time.time()
        ).first()
        if record:
            is_valid = True

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code. Please check your code or request a new one.")

    return {
        "status": "success",
        "message": "Email verified successfully."
    }


@router.post("/login", response_model=schemas.TokenResponse)
async def login(request: schemas.LoginRequest, db: Session = Depends(get_db)):
    clean_email = request.email.strip().lower()
    user = db.query(models.User).filter(
        (models.User.email == clean_email) | (models.User.username == request.email.strip())
    ).first()
    if not user or not security.verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
        "username": user.full_name or user.username,
        "role": user.role
    }


@router.post("/signup", response_model=schemas.TokenResponse)
@router.post("/register", response_model=schemas.TokenResponse)
async def api_json_signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers a new user with verified email OTP, password, and curriculum profile metadata."""
    clean_email = user_in.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    # 1. Verify OTP
    clean_otp = (user_in.otp or "").strip()
    is_valid_otp = False
    cache_key = (clean_email, "signup")

    if cache_key in PENDING_OTPS:
        entry = PENDING_OTPS[cache_key]
        if (entry["otp"] == clean_otp or entry.get("verified")) and entry["expires_at"] > time.time():
            is_valid_otp = True

    if not is_valid_otp and clean_otp:
        record = db.query(models.EmailVerificationOTP).filter(
            models.EmailVerificationOTP.email == clean_email,
            models.EmailVerificationOTP.otp == clean_otp,
            models.EmailVerificationOTP.action == "signup",
            models.EmailVerificationOTP.is_used == False,
            models.EmailVerificationOTP.expires_at > time.time()
        ).first()
        if record:
            is_valid_otp = True
            record.is_used = True

    if not is_valid_otp:
        raise HTTPException(
            status_code=400,
            detail="Email verification required. Please click 'Send Code' and enter the 6-digit OTP sent to your email."
        )

    # 2. Verify Password Strength
    if len(user_in.password.strip()) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    # 3. Check Duplicate Account
    existing_user = db.query(models.User).filter(models.User.email == clean_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    # Derive username
    candidate_username = (user_in.username or user_in.full_name or clean_email.split("@")[0]).strip()
    # Ensure unique username
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
        interests=user_in.interests or []
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
        "role": new_user.role
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

    # Validate OTP
    is_valid_otp = False
    cache_key = (clean_email, "forgot_password")
    if cache_key in PENDING_OTPS:
        entry = PENDING_OTPS[cache_key]
        if entry["otp"] == clean_otp and entry["expires_at"] > time.time():
            is_valid_otp = True
            del PENDING_OTPS[cache_key]

    if not is_valid_otp:
        record = db.query(models.EmailVerificationOTP).filter(
            models.EmailVerificationOTP.email == clean_email,
            models.EmailVerificationOTP.otp == clean_otp,
            models.EmailVerificationOTP.action == "forgot_password",
            models.EmailVerificationOTP.is_used == False,
            models.EmailVerificationOTP.expires_at > time.time()
        ).first()
        if record:
            is_valid_otp = True
            record.is_used = True

    if not is_valid_otp:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code. Please check the code sent to your email or request a new one.")

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
    existing_user = db.query(models.User).filter(models.User.email == clean_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="An account with this email address already exists.")

    if len(password.strip()) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

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
        is_email_verified=bool(otp)
    )
    db.add(new_user)
    db.commit()

    return {"status": "success", "message": "Account created successfully."}
