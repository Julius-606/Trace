"""Deployment-aware environment loading for local runs and Hugging Face Spaces."""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv


def running_on_huggingface() -> bool:
    """Detect the environment variables injected by Hugging Face Spaces."""
    return bool(
        os.getenv("SPACE_ID")
        or os.getenv("HF_SPACE_ID")
        or os.getenv("SPACE_HOST")
    )


def load_runtime_environment() -> bool:
    """Load local .env values only outside hosted Hugging Face Spaces."""
    if running_on_huggingface():
        return False
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    return True


load_runtime_environment()


@dataclass(frozen=True)
class Settings:
    """Runtime settings shared by Trace & Orbit services without sharing its database."""

    SECRET_KEY: str = os.getenv("ORBIT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "development-orbit-secret"))
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY_1") or os.getenv("GEMINI_API_KEY_2")
    MT5_LOGIN: str | None = os.getenv("MT5_LOGIN")
    MT5_PASSWORD: str | None = os.getenv("MT5_PASSWORD")
    MT5_SERVER: str | None = os.getenv("MT5_SERVER")
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_SECRET: str | None = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    
    # WhatsApp / Meta Bot Cloud API & Twilio Fallback (SSS Project Orbit Integration)
    WHATSAPP_TOKEN: str | None = os.getenv("WHATSAPP_TOKEN") or os.getenv("META_ACCESS_TOKEN")
    WHATSAPP_PHONE_NUMBER_ID: str | None = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    WHATSAPP_VERIFY_TOKEN: str | None = os.getenv("WHATSAPP_VERIFY_TOKEN", "orbit_trace_verify_token_2026")
    WHATSAPP_BUSINESS_ACCOUNT_ID: str | None = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
    TWILIO_ACCOUNT_SID: str | None = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str | None = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: str | None = os.getenv("TWILIO_WHATSAPP_NUMBER")
    ADMIN_PHONE_NUMBER: str | None = os.getenv("ADMIN_PHONE_NUMBER")

settings = Settings()

