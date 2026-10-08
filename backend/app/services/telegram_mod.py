
################################################################################
#FILE: backend/app/services/telegram_mod.py
#VERSION: 1.0.1 | SYSTEM: Jarvis Protocol
################################################################################

import logging
import asyncio
# 🚀 FIX: Added 'app.' prefix
from app.core.config import settings

logger = logging.getLogger("Telegram-Bouncer")

class TelegramModerator:
    def __init__(self):
        self.bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.banned_words = ["spoonfeed", "leak", "exam answers", "buy signal", "crypto pump"]

        if self.bot_token:
            logger.info("Telegram Bouncer is at the door. Checking IDs.")
        else:
            logger.warning("No Telegram bot token. The group chat is currently the Wild West.")

    async def check_message(self, user_id: str, message_text: str) -> dict:
        logger.info(f"Scanning message from user {user_id}...")
        message_lower = message_text.lower()

        for word in self.banned_words:
            if word in message_lower:
                logger.warning(f"Opp detected! User {user_id} used banned word: {word}")
                return {
                    "action": "DELETE_AND_WARN",
                    "message": f"Bro, we don't do '{word}' here. Lock in and study. Strike 1."
                }

        if "anatomy" in message_lower or "usmle" in message_lower:
            return {"action": "REACT", "emoji": "🧠", "message": "Valid academic discussion. Let him cook."}

        return {"action": "NONE", "message": "Message clean. Vibe check passed."}

    async def start_polling(self):
        if not self.bot_token:
            return

        logger.info("Starting Telegram polling loop... Watchlist active.")
        while True:
            await asyncio.sleep(5)

telegram_bouncer = TelegramModerator()

