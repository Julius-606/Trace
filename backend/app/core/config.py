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
    """Runtime settings shared by Orbit services without sharing its database."""

    SECRET_KEY: str = os.getenv("ORBIT_SECRET_KEY", os.getenv("JWT_SECRET_KEY", "development-orbit-secret"))
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    MT5_LOGIN: str | None = os.getenv("MT5_LOGIN")
    MT5_PASSWORD: str | None = os.getenv("MT5_PASSWORD")
    MT5_SERVER: str | None = os.getenv("MT5_SERVER")
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")

settings = Settings()
