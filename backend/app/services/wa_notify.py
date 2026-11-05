################################################################################
# FILE: backend/app/services/wa_notify.py
# VERSION: 3.0.0 | SYSTEM: Orbit & SSS WhatsApp Gateway
# IDENTITY: Production-Grade Multi-Provider WhatsApp Engine, Socratic Bot & Sync Coordinator
################################################################################

import logging
import re
import time
from typing import Dict, Any, Optional, List
import httpx
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import database_models as models
from app.sync.sync_manager import sync_manager
from app.services.ai_service import AiService

logger = logging.getLogger("WhatsApp-Bot-Engine")

# Initialize AI Service for Socratic Mentorship
ai_tutor = AiService()

# In-memory ephemeral quiz state cache for active WhatsApp threads
# Maps normalized phone number -> { quiz_id, question, correct_answer, explanation, unit_name, options, timestamp }
_ACTIVE_QUIZ_CACHE: Dict[str, Dict[str, Any]] = {}


class WhatsAppNotifier:
    """
    Production-grade WhatsApp educational service supporting Meta Cloud API (Graph API v18+)
    with fallback to Twilio WhatsApp API. Integrates conversational active recall quizzes,
    Socratic mentoring, micro-learning pearls, and atomic PostgreSQL state synchronization.
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
            logger.info("WhatsAppNotifier initialized with Meta Cloud API.")
        elif self.twilio_sid and self.twilio_auth and self.twilio_from:
            self.provider = "TWILIO"
            logger.info("WhatsAppNotifier initialized with Twilio WhatsApp API.")
        else:
            self.provider = "STUB"
            logger.warning("WhatsApp credentials absent. WhatsAppNotifier running in audit/dry-run mode.")

    def _sanitize_recipient(self, phone: str) -> str:
        """Format phone number to clean international E.164 digits without symbols."""
        cleaned = re.sub(r"[^\d+]", "", phone.strip())
        if cleaned.startswith("+"):
            return cleaned[1:]
        if cleaned.startswith("0") and len(cleaned) == 10:
            # Kenyan numbers default: 07xx -> 2547xx
            return f"254{cleaned[1:]}"
        return cleaned

    # =========================================================================
    # Outbound Dispatch Engine
    # =========================================================================

    async def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """
        Dispatches an outbound WhatsApp text message via Meta Cloud API or Twilio fallback.
        """
        dest = self._sanitize_recipient(recipient)
        logger.info(f"Dispatching WhatsApp message to +{dest} via {self.provider} driver.")

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
                        return {"status": "sent", "provider": "twilio", "id": res_json.get("sid")}
                    else:
                        logger.error(f"Twilio WhatsApp failed ({resp.status_code}): {res_json}")
                        return {"status": "error", "provider": "twilio", "detail": res_json}
            except Exception as e:
                logger.error(f"Exception during Twilio WhatsApp dispatch: {e}")
                return {"status": "error", "provider": "twilio", "detail": str(e)}

        # Development / Sandbox Dry-Run Stub
        logger.info(f"[WHATSAPP DRY-RUN] To: +{dest}\nBody:\n{message}")
        return {"status": "stubbed", "provider": "stub", "recipient": dest, "preview": message[:100]}

    def verify_webhook(self, hub_mode: Optional[str], hub_token: Optional[str], hub_challenge: Optional[str]) -> Optional[str]:
        """
        Validates the Meta WhatsApp Webhook handshake verification query parameters.
        """
        if hub_mode == "subscribe" and hub_token == self.verify_token:
            logger.info("Meta WhatsApp webhook verified successfully.")
            return hub_challenge
        logger.warning(f"Meta WhatsApp webhook verification failed: mode={hub_mode}")
        return None

    # =========================================================================
    # Inbound Webhook Processor & Conversational Quiz Engine
    # =========================================================================

    async def process_inbound_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses incoming WhatsApp webhook payloads from Meta Cloud API or Twilio.
        Supports active recall quizzes, spaced-repetition micro-learning, account linking,
        and synchronized Socratic AI consultations.
        """
        sender_phone = None
        message_body = None

        # 1. Parse Meta Cloud API Format
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
                    elif msg_obj.get("type") == "interactive":
                        # Interactive button reply
                        interactive = msg_obj.get("interactive", {})
                        if interactive.get("type") == "button_reply":
                            message_body = interactive.get("button_reply", {}).get("title", "")

        # 2. Parse Twilio Format
        if not sender_phone and "From" in payload:
            sender_phone = payload.get("From", "").replace("whatsapp:", "").replace("+", "")
            message_body = payload.get("Body", "")

        if not sender_phone or not message_body:
            return {"status": "ignored", "reason": "No actionable text message found"}

        clean_phone = self._sanitize_recipient(sender_phone)
        raw_text = message_body.strip()
        cmd = raw_text.upper()
        logger.info(f"Received inbound WhatsApp message from +{clean_phone}: '{raw_text}'")

        # Open Scoped Database Session for Synchronization
        with SessionLocal() as db:
            user = sync_manager.resolve_user_by_channel(db, "whatsapp", clean_phone)
            user_id = user.id if user else 1

            # -----------------------------------------------------------------
            # A. Account Linking via Magic Token (e.g., "LINK link_a1b2c3d4")
            # -----------------------------------------------------------------
            if cmd.startswith("LINK "):
                token = raw_text.split(maxsplit=1)[1].strip()
                success, linked_user, link_msg = sync_manager.verify_and_link_magic_token(
                    db=db,
                    token=token,
                    platform="whatsapp",
                    platform_id=clean_phone
                )
                if success and linked_user:
                    reply = (
                        f"🎉 *Trace Account Connected!*\n\n"
                        f"Hello, *{linked_user.username}*! Your WhatsApp is now linked directly to your Trace curriculum.\n"
                        f"⚡ *Neurons Balance*: `{linked_user.neurons}` Neurons\n\n"
                        f"Text *QUIZ* to solve a clinical case, *PROGRESS* to view stats, or ask any clinical question!"
                    )
                else:
                    reply = f"❌ *Linking Error*: {link_msg}\n\nPlease generate a new verification token from your Trace Web profile settings."
                await self.send_message(clean_phone, reply)
                return {"status": "link_processed"}

            # -----------------------------------------------------------------
            # B. Conversational Quiz Evaluation (Student answers A, B, C, D)
            # -----------------------------------------------------------------
            active_quiz = _ACTIVE_QUIZ_CACHE.get(clean_phone)
            if active_quiz and cmd in ("A", "B", "C", "D", "1", "2", "3", "4"):
                letter_map = {"1": 0, "2": 1, "3": 2, "4": 3, "A": 0, "B": 1, "C": 2, "D": 3}
                selected_idx = letter_map.get(cmd, 0)
                options = active_quiz.get("options", [])
                correct_answer = active_quiz.get("correct_answer", "")
                selected_opt = options[selected_idx] if selected_idx < len(options) else ""

                is_correct = (selected_opt.strip().lower() == correct_answer.strip().lower())
                score = 1 if is_correct else 0
                neurons_awarded = 15 if is_correct else 5

                # Atomically Commit Quiz Attempt to Single Source of Truth
                sync_result = sync_manager.record_quiz_attempt(
                    db=db,
                    user_id=user_id,
                    unit_name=active_quiz.get("unit_name", "Clinical Medicine"),
                    score=score,
                    total=1,
                    channel="whatsapp",
                    question_id=active_quiz.get("quiz_id")
                )

                # Clear active quiz from cache
                _ACTIVE_QUIZ_CACHE.pop(clean_phone, None)

                if is_correct:
                    eval_msg = (
                        f"🎉 *CORRECT!* (+{neurons_awarded} Neurons Awarded)\n\n"
                        f"The correct answer is indeed *{correct_answer}*.\n\n"
                        f"💡 *Clinical Rationale*:\n{active_quiz.get('explanation')}\n\n"
                        f"⚡ *Current Balance*: `{sync_result.get('total_neurons', 215)}` Neurons\n"
                        f"Text *QUIZ* for the next challenge or *PROGRESS* to check your mastery rings!"
                    )
                else:
                    eval_msg = (
                        f"❌ *INCORRECT* (+5 Participation Neurons)\n\n"
                        f"The correct answer is *{correct_answer}*.\n\n"
                        f"💡 *Clinical Rationale*:\n{active_quiz.get('explanation')}\n\n"
                        f"⚡ *Current Balance*: `{sync_result.get('total_neurons', 205)}` Neurons\n"
                        f"Text *QUIZ* to try another question!"
                    )

                await self.send_message(clean_phone, eval_msg)
                return {"status": "quiz_graded", "is_correct": is_correct}

            # -----------------------------------------------------------------
            # C. Standard Bot Commands
            # -----------------------------------------------------------------
            if cmd in ("HELP", "MENU", "START"):
                user_greet = user.username if user else "Scholar"
                reply = (
                    f"🤖 *Trace WhatsApp Socratic Copilot* (Hello @{user_greet}!)\n\n"
                    f"Commands:\n"
                    f"• *QUIZ*: Delivers an active recall clinical case MCQ\n"
                    f"• *STUDY*: High-yield clinical concept pearl\n"
                    f"• *PROGRESS*: Synchronized curriculum metrics\n"
                    f"• *NEURONS*: Check token currency balance\n"
                    f"• *LINK <token>*: Link your web account\n\n"
                    f"Or simply ask any medical question for step-by-step Socratic reasoning!"
                )

            elif cmd == "QUIZ":
                # Pull question from GeneratedQuizBank
                quiz_item = db.query(models.GeneratedQuizBank).order_by(models.GeneratedQuizBank.id.desc()).first()
                if quiz_item:
                    q_id = quiz_item.id
                    q_text = quiz_item.question
                    options = quiz_item.options if isinstance(quiz_item.options, list) else ["Option A", "Option B", "Option C", "Option D"]
                    correct = quiz_item.correct_answer
                    explanation = quiz_item.explanation or "Verified clinical diagnostic protocol."
                    unit_name = quiz_item.unit_name
                    scenario = quiz_item.clinical_scenario
                else:
                    q_id = 99901
                    q_text = "A 45-year-old male presents with acute severe epigastric pain radiating to the back. Which serum enzyme elevation is most specific for acute pancreatitis within 24-48 hours?"
                    options = ["Amylase", "Lipase", "AST", "Alkaline Phosphatase"]
                    correct = "Lipase"
                    explanation = "Serum lipase is more specific and remains elevated longer than amylase in acute pancreatitis."
                    unit_name = "Clinical Gastroenterology"
                    scenario = None

                # Cache in-flight quiz for this phone
                _ACTIVE_QUIZ_CACHE[clean_phone] = {
                    "quiz_id": q_id,
                    "question": q_text,
                    "options": options,
                    "correct_answer": correct,
                    "explanation": explanation,
                    "unit_name": unit_name,
                    "timestamp": time.time()
                }

                letters = ["A", "B", "C", "D"]
                options_str = "\n".join([f"*{letters[i]}*) {opt}" for i, opt in enumerate(options[:4])])

                reply = (
                    f"🩺 *Trace Active Recall Mini-Quiz*\n"
                    f"*Unit*: `{unit_name}`\n\n"
                )
                if scenario:
                    reply += f"📋 *Case*:\n_{scenario}_\n\n"
                reply += (
                    f"❓ *Question*:\n*{q_text}*\n\n"
                    f"{options_str}\n\n"
                    f"👉 *Reply with your chosen letter (A, B, C, or D)*"
                )

            elif cmd == "STUDY":
                # Pull a high-yield concept from NodeEnrichment
                enrichment = db.query(models.NodeEnrichment).filter(
                    models.NodeEnrichment.clinical_takeaway != None
                ).order_by(models.NodeEnrichment.id.desc()).first()

                if enrichment and enrichment.clinical_takeaway:
                    reply = (
                        f"💡 *Trace Micro-Learning Pearl: {enrichment.node_name}*\n\n"
                        f"🔬 *High-Yield Takeaway*:\n{enrichment.clinical_takeaway}\n\n"
                    )
                    if enrichment.intuitive_explanation:
                        reply += f"🧠 *Intuitive Analogy*:\n_{enrichment.intuitive_explanation[:200]}..._\n\n"
                    reply += "Review full diagrams in your Web vault: https://agent606-trace.hf.space/app"
                else:
                    reply = (
                        "💡 *Trace Daily Clinical Pearl: Septic Shock*\n\n"
                        "In early (warm) septic shock, systemic vascular resistance (SVR) decreases due to peripheral vasodilation, "
                        "while cardiac output temporarily increases. First-line vasopressor: *Norepinephrine*."
                    )

            elif cmd == "PROGRESS":
                summary = sync_manager.get_student_summary(db, user_id)
                curriculum = summary.get("curriculum", {})
                quiz_stats = summary.get("quiz_stats", {})
                neurons = summary.get("neurons_balance", 0)

                reply = (
                    f"📊 *Trace Student Progress Report*\n"
                    f"👤 User: *{summary.get('username', 'Student')}*\n"
                    f"⚡ Neurons Balance: `{neurons}` Neurons\n\n"
                    f"🏆 *Mastery Tier*: {quiz_stats.get('mastery_tier', 'Competent Clinician')}\n"
                    f"📈 *Average PnL*: `{quiz_stats.get('average_pnl', 0.0)}%` ({quiz_stats.get('total_quizzes', 0)} quizzes)\n"
                    f"🧠 *Subtopics Completed*: `{curriculum.get('completed_subtopics', 0)}/{curriculum.get('total_subtopics', 0)}` ({curriculum.get('overall_percent', 0.0)}%)\n\n"
                    f"Progress is identical across Web, Android, and Telegram."
                )

            elif cmd == "NEURONS":
                balance = user.trace_coins if user else 200
                reply = (
                    f"⚡ *Neurons Balance*: *{balance} Neurons*\n\n"
                    f"Solve questions on WhatsApp by texting *QUIZ* to earn +15 Neurons per correct answer!"
                )

            else:
                # -------------------------------------------------------------
                # D. Socratic AI Mentorship for Clinical Doubts
                # -------------------------------------------------------------
                system_prompt = (
                    "You are the Trace Socratic AI Tutor on WhatsApp. "
                    "Guide the medical/academic student step-by-step. "
                    "Keep explanations compact, high-yield, and easy to read on a mobile phone (under 160 words). "
                    "End with a short active recall question."
                )

                try:
                    ai_reply = ai_tutor.ask(prompt=raw_text, system_instruction=system_prompt)
                    if not ai_reply or "unavailable" in ai_reply.lower():
                        ai_reply = f"Acknowledged '{raw_text[:40]}...'. What core physiological principle governs this scenario?"
                except Exception as e:
                    logger.error(f"WhatsApp Socratic AI error: {e}")
                    ai_reply = "⚡ AI assistant momentarily offline. Text *QUIZ* to test your knowledge!"

                reply = f"🧠 *Trace Socratic Copilot*:\n\n{ai_reply}"

                # Persist in synchronized chat history
                if user_id:
                    sync_manager.append_chat_interaction(
                        db=db,
                        user_id=user_id,
                        role="user",
                        content=raw_text,
                        channel="whatsapp",
                        session_title="[WhatsApp] Socratic Copilot"
                    )
                    sync_manager.append_chat_interaction(
                        db=db,
                        user_id=user_id,
                        role="assistant",
                        content=ai_reply,
                        channel="whatsapp",
                        session_title="[WhatsApp] Socratic Copilot"
                    )

            # Send automated WhatsApp message
            await self.send_message(clean_phone, reply)
            return {"status": "processed", "phone": clean_phone, "command": cmd}


# Global Singleton Instance
whatsapp_notifier = WhatsAppNotifier()
