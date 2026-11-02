################################################################################
# FILE: backend/app/api/webhooks.py
# VERSION: 1.0.0 | SYSTEM: Trace & Orbit External Bot Integrations
# IDENTITY: Unified Webhook Endpoints for Meta WhatsApp, Twilio & Telegram Bots
################################################################################

import logging
from fastapi import APIRouter, Request, Query, Response, HTTPException, status
from fastapi.responses import PlainTextResponse, JSONResponse
from app.services.wa_notify import whatsapp_notifier
from app.services.telegram_mod import telegram_bouncer
from app.core.config import settings

logger = logging.getLogger("Trace-Webhooks")

router = APIRouter(prefix="/webhooks", tags=["External Bot Webhooks"])


@router.get("/whatsapp")
async def verify_meta_whatsapp_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    Verification handshake endpoint for Meta WhatsApp Cloud API.
    Meta sends GET request with hub.challenge when setting up the webhook callback URL.
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
    Dispatches automated Socratic replies and study commands.
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
    Handles academic commands (/study, /quiz, /status) and message moderation.
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
