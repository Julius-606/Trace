################################################################################
# FILE: backend/app/services/wa_notify.py
# VERSION: 2.0.0 | SYSTEM: Orbit & SSS WhatsApp Gateway
# IDENTITY: Multi-Provider WhatsApp & Meta Graph API Notification Engine
################################################################################

import logging
import re
from typing import Dict, Any, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("WhatsApp-Notifier")


class WhatsAppNotifier:
    """
    Modular WhatsApp notification service supporting Meta Cloud API (WhatsApp Business Graph API)
    with seamless fallback to Twilio WhatsApp API.
    """

    def __init__(self):
        self.meta_token = settings.WHATSAPP_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.verify_token = settings.WHATSAPP_VERIFY_TOKEN
        self.business_account_id = settings.WHATSAPP_BUSINESS_ACCOUNT_ID

        self.twilio_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_auth = settings.TWILIO_AUTH_TOKEN
        self.twilio_from = settings.TWILIO_WHATSAPP_NUMBER

        # Determine active driver
        if self.meta_token and self.phone_number_id:
            self.provider = "META"
            logger.info("WhatsAppNotifier initialized via Meta Cloud API.")
        elif self.twilio_sid and self.twilio_auth and self.twilio_from:
            self.provider = "TWILIO"
            logger.info("WhatsAppNotifier initialized via Twilio WhatsApp API.")
        else:
            self.provider = "STUB"
            logger.warning("WhatsApp credentials absent. WhatsAppNotifier running in audit/dry-run mode.")

    def _sanitize_recipient(self, phone: str) -> str:
        """Format phone number to clean international E.164 digits without symbols."""
        cleaned = re.sub(r"[^\d+]", "", phone.strip())
        if cleaned.startswith("+"):
            return cleaned[1:]
        if cleaned.startswith("0") and len(cleaned) == 10:
            # Default Kenyan local numbers (07xx -> 2547xx)
            return f"254{cleaned[1:]}"
        return cleaned

    async def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """
        Sends an outbound WhatsApp text message to the specified recipient phone number.
        """
        dest = self._sanitize_recipient(recipient)
        logger.info(f"Dispatching WhatsApp message to {dest} via {self.provider} provider.")

        if self.provider == "META":
            url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.meta_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": dest,
                "type": "text",
                "text": {"preview_url": True, "body": message},
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    data = resp.json()
                    if resp.status_code in (200, 201):
                        logger.info(f"Meta WhatsApp dispatched successfully: {data.get('messages', [{}])[0].get('id')}")
                        return {"status": "sent", "provider": "meta", "id": data.get("messages", [{}])[0].get("id")}
                    else:
                        logger.error(f"Meta WhatsApp failed ({resp.status_code}): {data}")
                        return {"status": "error", "provider": "meta", "detail": data}
            except Exception as e:
                logger.error(f"Exception during Meta WhatsApp dispatch: {e}")
                return {"status": "error", "provider": "meta", "detail": str(e)}

        elif self.provider == "TWILIO":
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"
            from_number = f"whatsapp:{self.twilio_from.replace('whatsapp:', '')}"
            to_number = f"whatsapp:+{dest}"
            data = {
                "From": from_number,
                "To": to_number,
                "Body": message,
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(url, data=data, auth=(self.twilio_sid, self.twilio_auth))
                    res_json = resp.json()
                    if resp.status_code in (200, 201):
                        logger.info(f"Twilio WhatsApp dispatched successfully: {res_json.get('sid')}")
                        return {"status": "sent", "provider": "twilio", "id": res_json.get("sid")}
                    else:
                        logger.error(f"Twilio WhatsApp failed ({resp.status_code}): {res_json}")
                        return {"status": "error", "provider": "twilio", "detail": res_json}
            except Exception as e:
                logger.error(f"Exception during Twilio WhatsApp dispatch: {e}")
                return {"status": "error", "provider": "twilio", "detail": str(e)}

        # Dry-run stub mode for development / sandbox
        logger.info(f"[WHATSAPP DRY-RUN] To: +{dest}\nBody:\n{message}")
        return {"status": "stubbed", "provider": "stub", "recipient": dest, "message_preview": message[:100]}

    async def send_study_reminder(self, recipient: str, task_title: str, due_date: str) -> Dict[str, Any]:
        """Formatted clinical study reminder."""
        msg = (
            f"🧠 *Trace Study Telemetry Alert*\n\n"
            f"Hey, it's time to lock in on *{task_title}*!\n"
            f"📅 Scheduled Due Date: `{due_date}`\n\n"
            f"Launch your workspace: https://agent606-trace.hf.space/app\n"
            f"Stay frosty and keep that active recall sharp. 🎯"
        )
        return await self.send_message(recipient, msg)

    async def send_quiz_summary(self, recipient: str, unit_name: str, score: int, total: int, pnl: float) -> Dict[str, Any]:
        """Summary of active recall quiz performance."""
        status_emoji = "🏆" if pnl >= 75 else ("📈" if pnl >= 50 else "⚡")
        msg = (
            f"{status_emoji} *Trace Active Recall PnL Report*\n\n"
            f"Unit: *{unit_name}*\n"
            f"Score: *{score}/{total}* ({round(pnl, 1)}% Mastery)\n\n"
            f"Review explanations and high-yield notes in your library vault."
        )
        return await self.send_message(recipient, msg)

    async def send_syllabus_published_alert(self, recipient: str, syllabus_title: str, unit_count: int) -> Dict[str, Any]:
        """Notification for newly ingested syllabus curriculums."""
        msg = (
            f"📚 *New Academic Syllabus Published!*\n\n"
            f"Title: *{syllabus_title}*\n"
            f"Units Ingested: *{unit_count}*\n\n"
            f"The Trace Rich Library Engine has automatically pre-generated quizzes, structured clinical summaries, and diagrams for this course.\n"
            f"Access now at: https://agent606-trace.hf.space/app"
        )
        return await self.send_message(recipient, msg)

    def verify_webhook(self, hub_mode: Optional[str], hub_token: Optional[str], hub_challenge: Optional[str]) -> Optional[str]:
        """
        Validates the Meta WhatsApp Webhook handshake verification query parameters.
        """
        if hub_mode == "subscribe" and hub_token == self.verify_token:
            logger.info("Meta WhatsApp webhook verified successfully.")
            return hub_challenge
        logger.warning(f"Meta WhatsApp webhook verification failed: mode={hub_mode}, token={hub_token}")
        return None

    async def process_inbound_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses inbound WhatsApp webhook events from Meta or Twilio.
        Supports natural commands like 'QUIZ', 'STUDY', 'TASKS', 'HELP'.
        """
        sender_phone = None
        message_body = None

        # Check for Meta Cloud API format
        entry = payload.get("entry", [])
        if entry and isinstance(entry, list):
            changes = entry[0].get("changes", [])
            if changes and isinstance(changes, list):
                value = changes[0].get("value", {})
                messages = value.get("messages", [])
                if messages and isinstance(messages, list):
                    msg_obj = messages[0]
                    sender_phone = msg_obj.get("from")
                    if msg_obj.get("type") == "text":
                        message_body = msg_obj.get("text", {}).get("body", "")

        # Check for Twilio format
        if not sender_phone and "From" in payload:
            sender_phone = payload.get("From", "").replace("whatsapp:", "").replace("+", "")
            message_body = payload.get("Body", "")

        if not sender_phone or not message_body:
            return {"status": "ignored", "reason": "No actionable text message found"}

        cmd = message_body.strip().upper()
        logger.info(f"Received inbound WhatsApp message from {sender_phone}: '{message_body}'")

        reply_text = ""
        if cmd in ("HELP", "MENU", "START"):
            reply_text = (
                "🤖 *Trace & Orbit WhatsApp Copilot*\n\n"
                "Available commands:\n"
                "• *STUDY*: View your highest-priority study blocks\n"
                "• *QUIZ*: Instant clinical reasoning question\n"
                "• *STATUS*: Check cognitive workload and system health\n"
                "• *RELOAD*: Trigger syllabus sync\n\n"
                "Or simply send your question for Socratic clinical guidance!"
            )
        elif cmd == "STATUS":
            reply_text = "🟢 *Trace Engine Online*\nSyllabus tree synced. Pre-generated library active. All neural nodes nominal."
        elif cmd == "STUDY":
            reply_text = "📖 *Current Study Focus*: Pharmacology & Internal Medicine.\nDeep work session recommended for peak retention."
        elif cmd == "QUIZ":
            reply_text = (
                "🎯 *Clinical Mini-Quiz*\n\n"
                "Q: A 45-year-old male presents with acute epigastric pain radiating to the back. Which serum enzyme is most specific for acute pancreatitis?\n"
                "A) Amylase\nB) Lipase\nC) AST\nD) Alkaline Phosphatase\n\n"
                "Reply with your answer (A, B, C, or D)!"
            )
        else:
            reply_text = f"Received: \"{message_body}\". Copilot acknowledged. Keep locked into your study goals! 🚀"

        # Send automated reply
        await self.send_message(sender_phone, reply_text)
        return {"status": "processed", "sender": sender_phone, "command": cmd}


# Global Singleton instance
whatsapp_notifier = WhatsAppNotifier()
