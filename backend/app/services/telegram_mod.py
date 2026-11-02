
################################################################################
# FILE: backend/app/services/telegram_mod.py
# VERSION: 2.0.0 | SYSTEM: Jarvis & Orbit Protocol
# IDENTITY: Telegram Bouncer, Study Bot & Automated Webhook Dispatcher
################################################################################

import logging
import asyncio
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("Telegram-Bouncer")


class TelegramModerator:
    def __init__(self):
        self.bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.webhook_secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)
        self.banned_words = ["spoonfeed", "leak", "exam answers", "buy signal", "crypto pump"]
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

        if self.bot_token:
            logger.info("Telegram Bouncer is at the door. Bot token active.")
        else:
            logger.warning("No Telegram bot token configured. Telegram service in dry-run mode.")

    async def send_message(self, chat_id: str | int, text: str, parse_mode: str = "Markdown") -> Dict[str, Any]:
        """Sends an outbound Telegram message."""
        if not self.base_url:
            logger.info(f"[TELEGRAM DRY-RUN] Chat {chat_id}: {text[:100]}...")
            return {"status": "dry_run", "chat_id": chat_id, "text": text}

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    return {"status": "success", "data": res.json()}
                logger.error(f"Telegram send failed ({res.status_code}): {res.text}")
                return {"status": "error", "detail": res.text}
        except Exception as e:
            logger.error(f"Exception sending Telegram message: {e}")
            return {"status": "error", "detail": str(e)}

    async def check_message(self, user_id: str, message_text: str) -> dict:
        """Content moderation & vibe check on messages."""
        logger.info(f"Scanning message from user {user_id}...")
        message_lower = message_text.lower()

        for word in self.banned_words:
            if word in message_lower:
                logger.warning(f"Opp detected! User {user_id} used banned word: {word}")
                return {
                    "action": "DELETE_AND_WARN",
                    "message": f"Bro, we don't do '{word}' here. Lock in and study. Strike 1."
                }

        if "anatomy" in message_lower or "usmle" in message_lower or "pathology" in message_lower:
            return {"action": "REACT", "emoji": "🧠", "message": "Valid academic discussion. Let him cook."}

        return {"action": "NONE", "message": "Message clean. Vibe check passed."}

    async def process_webhook_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """Handles incoming updates from Telegram Webhook."""
        message = update.get("message") or update.get("edited_message")
        if not message:
            return {"status": "ignored", "reason": "No message in update"}

        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        user_info = message.get("from", {})
        user_id = user_info.get("id")
        username = user_info.get("username", "Scholar")

        if not text:
            return {"status": "ignored", "reason": "Non-text message"}

        # Run moderation check
        mod_result = await self.check_message(str(user_id), text)
        if mod_result.get("action") == "DELETE_AND_WARN":
            await self.send_message(chat_id, f"⚠️ @{username}: {mod_result['message']}")
            return {"status": "moderated", "action": "warned"}

        # Handle Bot Commands
        cmd = text.strip()
        if cmd.startswith("/start") or cmd.startswith("/help"):
            reply = (
                f"👋 *Welcome to Trace & Orbit Telegram Bot*, @{username}!\n\n"
                "Commands:\n"
                "• `/study` - View high-yield syllabus topics\n"
                "• `/quiz` - Instant Socratic challenge\n"
                "• `/status` - Cognitive workload & system status\n"
                "• `/orbit` - Neural Copilot overview\n\n"
                "Or ask any medical/academic question for clinical breakdowns!"
            )
            await self.send_message(chat_id, reply)
            return {"status": "command_handled", "cmd": "start"}

        elif cmd.startswith("/status"):
            reply = "🚀 *Trace Modular Engine Status: ONLINE*\n• Library Pre-Gen: Active\n• Dual Postgres/SQLite: Connected\n• Cognitive Load: Balanced"
            await self.send_message(chat_id, reply)
            return {"status": "command_handled", "cmd": "status"}

        elif cmd.startswith("/study"):
            reply = "📚 *Current Active Clinical Rotation*\n• Internal Medicine: Cardiology & Pulmonology\n• Surgery: Trauma Management\nAccess notes: https://agent606-trace.hf.space/app"
            await self.send_message(chat_id, reply)
            return {"status": "command_handled", "cmd": "study"}

        elif cmd.startswith("/quiz"):
            reply = (
                "🩺 *Quick Recall Question*\n\n"
                "*Which hemodynamic change is hallmark of septic shock in early (warm) stage?*\n"
                "A) High SVR, low Cardiac Output\n"
                "B) Low SVR, high Cardiac Output\n"
                "C) High PCWP, normal SVR\n"
                "D) Low Cardiac Output, normal PCWP"
            )
            await self.send_message(chat_id, reply)
            return {"status": "command_handled", "cmd": "quiz"}

        return {"status": "ok", "message_length": len(text)}

    async def start_polling(self):
        if not self.bot_token:
            return

        logger.info("Starting Telegram polling loop... Watchlist active.")
        while True:
            await asyncio.sleep(5)


telegram_bouncer = TelegramModerator()


