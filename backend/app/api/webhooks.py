################################################################################
# FILE: backend/app/api/webhooks.py
# VERSION: 2.0.0 | SYSTEM: Trace & Orbit External Bot Integrations
# IDENTITY: Unified Webhook Endpoints for Meta WhatsApp, Twilio & Telegram Bots
################################################################################

import logging
from fastapi import APIRouter, Request, Query, Response, HTTPException, status, Depends
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import database_models as models
from app.services.wa_notify import whatsapp_notifier
from app.services.telegram_mod import telegram_bouncer
from app.sync.sync_manager import sync_manager
from app.core.config import settings

logger = logging.getLogger("Trace-Webhooks")

router = APIRouter(prefix="/webhooks", tags=["External Bot Webhooks"])


class MagicTokenRequest(BaseModel):
    user_id: int


class MagicTokenVerifyRequest(BaseModel):
    token: str
    platform: str # "telegram" | "whatsapp"
    platform_id: str


@router.get("/whatsapp")
async def verify_meta_whatsapp_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    Verification handshake endpoint for Meta WhatsApp Cloud API.
    Meta sends GET request with hub.challenge when registering the webhook callback URL.
    """
    logger.info(f"Meta WhatsApp webhook verification request: mode={hub_mode}")
    challenge = whatsapp_notifier.verify_webhook(hub_mode, hub_verify_token, hub_challenge)
    if challenge:
        return PlainTextResponse(content=challenge, status_code=200)
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch")


@router.post("/whatsapp")
async def handle_whatsapp_inbound_webhook(request: Request):
    """
    Receives incoming WhatsApp messages from Meta Graph API or Twilio.
    Dispatches automated conversational quizzes, micro-learning pearls, and Socratic guidance.
    """
    content_type = request.headers.get("content-type", "")
    payload = {}

    if "application/json" in content_type:
        payload = await request.json()
    elif "application/x-www-form-urlencoded" in content_type:
        form_data = await request.form()
        payload = dict(form_data)
    else:
        try:
            payload = await request.json()
        except Exception:
            payload = {}

    result = await whatsapp_notifier.process_inbound_webhook(payload)
    return JSONResponse(content={"status": "received", "result": result}, status_code=200)


@router.post("/telegram")
async def handle_telegram_inbound_webhook(request: Request):
    """
    Receives incoming webhook updates from Telegram Bot API.
    Handles academic commands (/syllabus, /quiz, /progress, /neurons), inline keyboards, and Socratic AI mentoring.
    """
    # Optional secret verification
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    expected_secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)
    if expected_secret and secret_header != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")

    try:
        update = await request.json()
    except Exception as e:
        logger.warning(f"Malformed Telegram update JSON: {e}")
        return JSONResponse(content={"status": "error", "detail": "Invalid JSON"}, status_code=400)

    result = await telegram_bouncer.process_webhook_update(update)
    return JSONResponse(content={"status": "ok", "result": result}, status_code=200)


@router.post("/magic-token/generate")
async def generate_account_link_token(req: MagicTokenRequest, db: Session = Depends(get_db)):
    """
    Generates a secure deep linking magic token for a student to link their Telegram or WhatsApp.
    """
    try:
        token = sync_manager.generate_magic_token(db, req.user_id)
        bot_username = "TraceEduAiBot" # Default fallback
        return {
            "status": "success",
            "token": token,
            "telegram_deep_link": f"https://t.me/{bot_username}?start={token}",
            "whatsapp_link_instruction": f"Text 'LINK {token}' to our WhatsApp Bot number"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/magic-token/verify")
async def verify_account_link_token(req: MagicTokenVerifyRequest, db: Session = Depends(get_db)):
    """
    Verifies magic token and attaches external platform ID to User entity.
    """
    success, user, msg = sync_manager.verify_and_link_magic_token(
        db=db,
        token=req.token,
        platform=req.platform,
        platform_id=req.platform_id
    )
    if not success or not user:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "status": "success",
        "message": msg,
        "user_id": user.id,
        "username": user.username,
        "platform": req.platform,
        "neurons_balance": user.neurons
    }


@router.get("/user/{user_id}/channels")
async def get_user_linked_channels(user_id: int, db: Session = Depends(get_db)):
    """
    Lists all active communication channels attached to a student account.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    channels = db.query(models.UserChannel).filter(
        models.UserChannel.user_id == user_id,
        models.UserChannel.is_active == True
    ).all()

    return {
        "user_id": user.id,
        "username": user.username,
        "telegram_chat_id": user.telegram_chat_id,
        "phone_number": user.phone_number,
        "channels": [
            {
                "id": c.id,
                "type": c.channel_type,
                "identifier": c.channel_identifier,
                "linked_at": c.linked_at
            }
            for c in channels
        ]
    }


@router.get("/status")
async def get_webhooks_status():
    """Returns telemetry status for all configured bot channels and external assets."""
    return {
        "status": "healthy",
        "channels": {
            "meta_whatsapp": {
                "configured": bool(settings.WHATSAPP_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID),
                "phone_number_id": settings.WHATSAPP_PHONE_NUMBER_ID or "unconfigured",
                "webhook_callback": "/api/webhooks/whatsapp"
            },
            "twilio_whatsapp": {
                "configured": bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN),
                "sender": settings.TWILIO_WHATSAPP_NUMBER or "unconfigured"
            },
            "telegram_bot": {
                "configured": bool(settings.TELEGRAM_BOT_TOKEN),
                "webhook_callback": "/api/webhooks/telegram"
            }
        }
    }
