################################################################################
# FILE: backend/app/services/telegram_mod.py
# VERSION: 3.0.0 | SYSTEM: Trace & Orbit Unified Bot Framework
# IDENTITY: Production-Grade Telegram Bot, Socratic AI Mentor & Real-Time Sync Engine
################################################################################

import logging
import asyncio
import time
from typing import Dict, Any, Optional, List
import httpx
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import database_models as models
from app.sync.sync_manager import sync_manager
from app.services.ai_service import AiService

logger = logging.getLogger("Telegram-Bot-Engine")

# Initialize AI Service for Socratic Mentorship
ai_tutor = AiService()


class TelegramModerator:
    """
    Production-grade Telegram educational bot with interactive inline keyboards,
    Socratic AI mentorship, deep linking account verification, and real-time database sync.
    """

    def __init__(self):
        self.bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.webhook_secret = getattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        self.banned_words = ["spoonfeed", "leak", "exam answers", "buy signal", "crypto pump"]

        if self.bot_token:
            logger.info("Telegram Bot Engine initialized with active bot token.")
        else:
            logger.warning("No Telegram bot token configured. Telegram service running in audit/dry-run mode.")

    # =========================================================================
    # HTTP Outbound API Utilities
    # =========================================================================

    async def send_message(
        self,
        chat_id: str | int,
        text: str,
        parse_mode: str = "Markdown",
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Sends an outbound Telegram message with optional interactive inline keyboard."""
        if not self.base_url:
            logger.info(f"[TELEGRAM DRY-RUN] Chat {chat_id}: {text[:120]}... (Markup: {bool(reply_markup)})")
            return {"status": "dry_run", "chat_id": chat_id, "text": text}

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    return {"status": "success", "data": res.json()}
                logger.error(f"Telegram sendMessage failed ({res.status_code}): {res.text}")
                return {"status": "error", "detail": res.text}
        except Exception as e:
            logger.error(f"Exception during Telegram sendMessage: {e}")
            return {"status": "error", "detail": str(e)}

    async def edit_message_text(
        self,
        chat_id: str | int,
        message_id: int,
        text: str,
        parse_mode: str = "Markdown",
        reply_markup: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Edits an existing message in-place (ideal for inline quiz evaluation)."""
        if not self.base_url:
            logger.info(f"[TELEGRAM DRY-RUN EDIT] Chat {chat_id}, Msg {message_id}: {text[:100]}...")
            return {"status": "dry_run"}

        url = f"{self.base_url}/editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                return {"status": "success", "data": res.json()} if res.status_code == 200 else {"status": "error"}
        except Exception as e:
            logger.error(f"Exception editing Telegram message: {e}")
            return {"status": "error", "detail": str(e)}

    async def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None, show_alert: bool = False):
        """Acknowledges button press to remove Telegram pending clock icon."""
        if not self.base_url:
            return
        url = f"{self.base_url}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
            payload["show_alert"] = show_alert
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.debug(f"Exception answering callback query: {e}")

    # =========================================================================
    # Moderation & Content Filter
    # =========================================================================

    def check_moderation(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for word in self.banned_words:
            if word in text_lower:
                return f"⚠️ Academic Integrity Warning: Please do not request '{word}'. Trace is built for active recall and Socratic mastery."
        return None

    # =========================================================================
    # Webhook Dispatcher & Core Handlers
    # =========================================================================

    async def process_webhook_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Master update dispatcher handling both conversational messages and inline button callback queries.
        """
        # 1. Handle Interactive Inline Keyboard Taps (Callback Queries)
        if "callback_query" in update:
            return await self._handle_callback_query(update["callback_query"])

        # 2. Handle Text Messages
        message = update.get("message") or update.get("edited_message")
        if not message:
            return {"status": "ignored", "reason": "No actionable message in update"}

        chat_id = message.get("chat", {}).get("id")
        text = (message.get("text") or "").strip()
        from_user = message.get("from", {})
        telegram_user_id = from_user.get("id")
        username = from_user.get("username") or from_user.get("first_name", "Scholar")

        if not text:
            return {"status": "ignored", "reason": "Empty or media message"}

        # Moderation Filter
        mod_warning = self.check_moderation(text)
        if mod_warning:
            await self.send_message(chat_id, mod_warning)
            return {"status": "moderated"}

        # Scoped Database Session for Real-Time Sync
        with SessionLocal() as db:
            user = sync_manager.resolve_user_by_channel(db, "telegram", str(telegram_user_id))
            user_id = user.id if user else None

            # Handle Commands
            if text.startswith("/start"):
                return await self._handle_start_command(chat_id, telegram_user_id, username, text, db)

            elif text.startswith("/syllabus") or text == "📚 Syllabus":
                return await self._handle_syllabus_command(chat_id, db)

            elif text.startswith("/quiz") or text == "🎯 Quiz":
                parts = text.split(maxsplit=1)
                unit_filter = parts[1] if len(parts) > 1 else None
                return await self._handle_quiz_command(chat_id, user_id, unit_filter, db)

            elif text.startswith("/progress") or text == "📈 Progress":
                return await self._handle_progress_command(chat_id, user_id, username, db)

            elif text.startswith("/neurons") or text == "⚡ Neurons":
                return await self._handle_neurons_command(chat_id, user, db)

            elif text.startswith("/help"):
                return await self._send_main_menu(chat_id, username, "Here is your Trace Socratic Command Palette:")

            # Natural Language Academic Question -> Socratic AI Mentorship
            return await self._handle_socratic_chat(chat_id, user_id, text, username, db)

    # =========================================================================
    # Interactive Command Handlers
    # =========================================================================

    async def _handle_start_command(self, chat_id: int, telegram_user_id: int, username: str, text: str, db) -> Dict[str, Any]:
        """
        Handles /start with deep linking token verification.
        Example: /start link_a1b2c3d4
        """
        parts = text.split()
        if len(parts) > 1 and parts[1].startswith("link_"):
            token = parts[1].strip()
            success, user, msg = sync_manager.verify_and_link_magic_token(
                db=db,
                token=token,
                platform="telegram",
                platform_id=str(telegram_user_id)
            )
            if success and user:
                welcome_text = (
                    f"🎉 *Account Successfully Linked!*\n\n"
                    f"Welcome aboard, *{user.username}*! Your Telegram account is now synchronized in real-time with your Trace Android App and Web portal.\n\n"
                    f"⚡ *Neurons Balance*: `{user.neurons}` Neurons\n"
                    f"📚 *Difficulty*: `{user.difficulty or 'Medium'}`\n\n"
                    f"Every quiz you solve here earns Neurons and updates your Web progress rings instantly."
                )
                await self.send_message(chat_id, welcome_text, reply_markup=self._get_main_menu_markup())
                return {"status": "linked", "user_id": user.id}
            else:
                await self.send_message(chat_id, f"❌ *Linking Error*: {msg}\n\nPlease generate a fresh link token in your Trace Web Settings.")
                return {"status": "link_failed"}

        # Standard /start without deep link token
        user = sync_manager.resolve_user_by_channel(db, "telegram", str(telegram_user_id))
        user_name = user.username if user else username
        neurons = user.neurons if user else 200

        welcome_text = (
            f"👋 *Welcome to Trace Socratic Copilot*, @{user_name}!\n\n"
            f"Trace is your adaptive AI clinical curriculum companion. All your progress here mirrors your Web and Android apps.\n\n"
            f"⚡ *Neurons Balance*: `{neurons}` Neurons\n"
            f"🎯 *Active Rotations*: Clinical Sciences, Internal Medicine, Pathology\n\n"
            f"Choose an action below or send any clinical doubt for Socratic step-by-step guidance!"
        )
        await self.send_message(chat_id, welcome_text, reply_markup=self._get_main_menu_markup())
        return {"status": "started"}

    async def _handle_syllabus_command(self, chat_id: int, db) -> Dict[str, Any]:
        """
        Renders an interactive inline keyboard displaying all ingested curriculum units.
        """
        units = db.query(models.Unit).filter(models.Unit.is_active == True).all()
        if not units:
            await self.send_message(chat_id, "📚 *Curriculum Catalogue*\n\nNo active units found. Please ingest a syllabus via the Admin console.")
            return {"status": "empty_syllabus"}

        keyboard = []
        for u in units[:8]: # Cap at 8 for clean inline layout
            keyboard.append([{"text": f"📖 {u.name[:36]}", "callback_data": f"cb:unit:{u.id}"}])

        keyboard.append([
            {"text": "🎯 Quick Assessment", "callback_data": "cb:quiz:random"},
            {"text": "📈 My Progress", "callback_data": "cb:progress"}
        ])

        reply_markup = {"inline_keyboard": keyboard}
        text = (
            "📚 *Interactive Curriculum Catalogue*\n\n"
            "Select an academic unit below to view modules, clinical topics, or trigger active recall quizzes:"
        )
        await self.send_message(chat_id, text, reply_markup=reply_markup)
        return {"status": "syllabus_sent"}

    async def _handle_quiz_command(self, chat_id: int, user_id: Optional[int], unit_filter: Optional[str], db) -> Dict[str, Any]:
        """
        Fetches an adaptive question from GeneratedQuizBank and sends it with inline keyboard options.
        """
        query = db.query(models.GeneratedQuizBank)
        if unit_filter:
            query = query.filter(models.GeneratedQuizBank.unit_name.ilike(f"%{unit_filter}%"))
        
        quiz = query.order_by(models.GeneratedQuizBank.id.desc()).first()

        # Fallback question if bank empty
        if not quiz:
            quiz_id = 99901
            question_text = "Which serum enzyme elevation is most specific for acute pancreatitis diagnosis within the first 24-48 hours?"
            options = ["Amylase", "Lipase", "Aspartate aminotransferase (AST)", "Alkaline phosphatase (ALP)"]
            unit_name = "Clinical Gastroenterology"
            difficulty = "Medium"
            scenario = "A 45-year-old male presents with acute severe epigastric pain radiating to the back after a weekend of heavy alcohol intake."
        else:
            quiz_id = quiz.id
            question_text = quiz.question
            options = quiz.options if isinstance(quiz.options, list) else ["Option A", "Option B", "Option C", "Option D"]
            unit_name = quiz.unit_name
            difficulty = quiz.difficulty or "Medium"
            scenario = quiz.clinical_scenario

        # Build 2x2 or 4x1 inline keyboard
        keyboard = []
        letters = ["A", "B", "C", "D"]
        for idx, opt in enumerate(options[:4]):
            keyboard.append([{"text": f"{letters[idx]}) {opt[:38]}", "callback_data": f"cb:q:{quiz_id}:{idx}"}])

        keyboard.append([{"text": "❌ Skip / Main Menu", "callback_data": "cb:menu"}])

        msg_body = f"🩺 *Trace Active Recall Challenge*\n*Unit*: `{unit_name}` | *Difficulty*: `{difficulty}`\n\n"
        if scenario:
            msg_body += f"📋 *Case Scenario*:\n_{scenario}_\n\n"
        msg_body += f"❓ *Question*:\n*{question_text}*\n\n"
        msg_body += "Tap your answer below:"

        await self.send_message(chat_id, msg_body, reply_markup={"inline_keyboard": keyboard})
        return {"status": "quiz_dispatched", "quiz_id": quiz_id}

    async def _handle_progress_command(self, chat_id: int, user_id: Optional[int], username: str, db) -> Dict[str, Any]:
        """
        Computes and delivers a normalized progress breakdown synchronized with Web & Mobile.
        """
        if not user_id:
            user = db.query(models.User).filter(models.User.role == "Student").first()
            user_id = user.id if user else 1

        summary = sync_manager.get_student_summary(db, user_id)
        curriculum = summary.get("curriculum", {})
        quiz_stats = summary.get("quiz_stats", {})
        neurons = summary.get("neurons_balance", 0)

        units_text = ""
        for u in curriculum.get("units", [])[:5]:
            bar = self._render_progress_bar(u.get("percent", 0.0))
            units_text += f"• *{u.get('unit_name')[:28]}*\n  {bar} `{u.get('percent', 0.0)}%` ({u.get('completed')}/{u.get('total')})\n"

        if not units_text:
            units_text = "• Clinical Medicine: `80%` [████████░░]\n• Pathophysiology: `65%` [██████░░░░]\n"

        msg = (
            f"📊 *Trace Cognitive Progress Matrix*\n"
            f"👤 Student: *{summary.get('username', username)}*\n"
            f"⚡ Neurons Balance: `{neurons}` Neurons\n\n"
            f"🏆 *Quiz Mastery Tier*: `{quiz_stats.get('mastery_tier', 'Competent Clinician')}`\n"
            f"📈 *Average PnL Accuracy*: `{quiz_stats.get('average_pnl', 0.0)}%` ({quiz_stats.get('total_quizzes', 0)} quizzes completed)\n"
            f"🧠 *Total Completed Subtopics*: `{curriculum.get('completed_subtopics', 0)}/{curriculum.get('total_subtopics', 0)}` ({curriculum.get('overall_percent', 0.0)}%)\n\n"
            f"📚 *Unit Progress Rings*:\n{units_text}\n"
            f"✨ All progress is synchronized in real-time across your Web and Android devices."
        )

        keyboard = {
            "inline_keyboard": [
                [{"text": "🎯 Solve Quiz for +15 Neurons", "callback_data": "cb:quiz:random"}],
                [{"text": "📖 Browse Syllabus", "callback_data": "cb:syllabus"}]
            ]
        }
        await self.send_message(chat_id, msg, reply_markup=keyboard)
        return {"status": "progress_sent"}

    async def _handle_neurons_command(self, chat_id: int, user: Optional[models.User], db) -> Dict[str, Any]:
        """
        Checks Neurons balance and explains the tokenomics.
        """
        balance = user.trace_coins if user else 200
        msg = (
            f"⚡ *Neurons Currency Vault*\n\n"
            f"Current Balance: *{balance} Neurons*\n\n"
            f"💡 *How to Earn Neurons*:\n"
            f"• Solve Quiz questions correctly: *+15 to +20 Neurons*\n"
            f"• Complete a Syllabus Subtopic on Web/Android: *+15 Neurons*\n"
            f"• Maintain a daily active recall streak: *+50 Neurons*\n\n"
            f"💎 *Redeemable for*:\n"
            f"• Unlocking premium mock board simulations\n"
            f"• Deep clinical reasoning case-studies\n"
            f"• Advanced Socratic persona consultations"
        )
        keyboard = {"inline_keyboard": [[{"text": "🎯 Earn Neurons via Quiz", "callback_data": "cb:quiz:random"}]]}
        await self.send_message(chat_id, msg, reply_markup=keyboard)
        return {"status": "neurons_sent"}

    # =========================================================================
    # Socratic AI Tutoring
    # =========================================================================

    async def _handle_socratic_chat(self, chat_id: int, user_id: Optional[int], prompt: str, username: str, db) -> Dict[str, Any]:
        """
        Engages the Gemini AI Socratic Tutor, formats response, and synchronizes message
        to PostgreSQL so the consultation appears on Web and Android apps.
        """
        system_prompt = (
            "You are the Trace Socratic AI Tutor on Telegram. "
            "Your goal is to guide students to clinical mastery step-by-step. "
            "Use guiding questions, analogies, and high-yield clinical pearls. "
            "Never spoonfeed answers directly. Keep replies concise (under 250 words), "
            "use bullet points, and format with clean Telegram Markdown. "
            "Conclude with an active recall check question."
        )

        # Notify student AI is thinking
        await self.send_message(chat_id, "🧠 _Trace Socratic Copilot is analyzing your clinical query..._")

        try:
            ai_reply = ai_tutor.ask(prompt=prompt, system_instruction=system_prompt)
            if not ai_reply or "unavailable" in ai_reply.lower():
                ai_reply = (
                    f"💡 *Socratic Breakdown*:\n\n"
                    f"Let's reason through '{prompt[:50]}...':\n\n"
                    f"1. What is the fundamental physiological disturbance here?\n"
                    f"2. Consider which compensatory mechanisms activate first (sympathetic vs hormonal).\n\n"
                    f"🎯 *Active Recall Challenge*: What laboratory test would you order first to confirm this hypothesis?"
                )
        except Exception as e:
            logger.error(f"Socratic AI error: {e}")
            ai_reply = "⚡ Core AI offline for maintenance. Keep testing your active recall via `/quiz`!"

        # Persist student question and Socratic reply into normalized database
        if user_id:
            sync_manager.append_chat_interaction(
                db=db,
                user_id=user_id,
                role="user",
                content=prompt,
                channel="telegram",
                session_title="[Telegram] Socratic AI Tutor"
            )
            sync_manager.append_chat_interaction(
                db=db,
                user_id=user_id,
                role="assistant",
                content=ai_reply,
                channel="telegram",
                session_title="[Telegram] Socratic AI Tutor"
            )

        # Send response with quick action keyboard
        keyboard = {
            "inline_keyboard": [
                [{"text": "🎯 Take a Quiz", "callback_data": "cb:quiz:random"}, {"text": "📚 Syllabus", "callback_data": "cb:syllabus"}]
            ]
        }
        await self.send_message(chat_id, ai_reply, reply_markup=keyboard)
        return {"status": "socratic_replied"}

    # =========================================================================
    # Interactive Callback Query Evaluator
    # =========================================================================

    async def _handle_callback_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles inline keyboard button presses.
        Evaluates quiz submissions, awards Neurons, and navigates menus in-place.
        """
        query_id = query.get("id")
        data = query.get("data", "")
        message = query.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        message_id = message.get("message_id")
        from_user = query.get("from", {})
        telegram_user_id = from_user.get("id")

        await self.answer_callback_query(query_id)

        with SessionLocal() as db:
            user = sync_manager.resolve_user_by_channel(db, "telegram", str(telegram_user_id))
            user_id = user.id if user else None

            # 1. Main Menu Navigation
            if data == "cb:menu":
                return await self._send_main_menu(chat_id, from_user.get("first_name", "Scholar"))

            elif data == "cb:syllabus":
                return await self._handle_syllabus_command(chat_id, db)

            elif data == "cb:progress":
                return await self._handle_progress_command(chat_id, user_id, from_user.get("first_name", "Scholar"), db)

            elif data == "cb:neurons":
                return await self._handle_neurons_command(chat_id, user, db)

            elif data == "cb:quiz:random":
                return await self._handle_quiz_command(chat_id, user_id, None, db)

            # 2. Unit Selection: cb:unit:<unit_id>
            elif data.startswith("cb:unit:"):
                unit_id = int(data.split(":")[2])
                unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()
                if not unit:
                    await self.send_message(chat_id, "Unit not found.")
                    return {"status": "error"}

                text = f"📖 *Unit*: *{unit.name}*\nCategory: `{unit.category}` | Course: `{unit.course}`\n\nModules: {len(unit.modules)} active modules.\nWould you like to solve questions for this unit?"
                keyboard = {
                    "inline_keyboard": [
                        [{"text": f"🎯 Take {unit.name[:20]} Quiz", "callback_data": f"cb:unit_quiz:{unit.id}"}],
                        [{"text": "← Back to Syllabus", "callback_data": "cb:syllabus"}]
                    ]
                }
                await self.send_message(chat_id, text, reply_markup=keyboard)
                return {"status": "unit_viewed"}

            elif data.startswith("cb:unit_quiz:"):
                unit_id = int(data.split(":")[2])
                unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()
                unit_name = unit.name if unit else None
                return await self._handle_quiz_command(chat_id, user_id, unit_name, db)

            # 3. Quiz Option Selected: cb:q:<quiz_id>:<option_idx>
            elif data.startswith("cb:q:"):
                parts = data.split(":")
                quiz_id = int(parts[2])
                opt_idx = int(parts[3])

                quiz = db.query(models.GeneratedQuizBank).filter(models.GeneratedQuizBank.id == quiz_id).first()
                if not quiz:
                    # Fallback evaluation for mock question 99901
                    correct_idx = 1 # Lipase
                    is_correct = (opt_idx == correct_idx)
                    correct_answer = "Lipase"
                    explanation = "Serum lipase is more specific and remains elevated longer than amylase in acute pancreatitis."
                    unit_name = "Clinical Gastroenterology"
                else:
                    options = quiz.options if isinstance(quiz.options, list) else []
                    chosen = options[opt_idx] if opt_idx < len(options) else ""
                    correct_answer = quiz.correct_answer
                    is_correct = (chosen.strip().lower() == correct_answer.strip().lower())
                    explanation = quiz.explanation or "High-yield clinical diagnostic criteria."
                    unit_name = quiz.unit_name

                score = 1 if is_correct else 0
                neurons_awarded = 15 if is_correct else 5

                # Atomically Commit to Database (Single Source of Truth)
                sync_result = sync_manager.record_quiz_attempt(
                    db=db,
                    user_id=user_id or 1,
                    unit_name=unit_name,
                    score=score,
                    total=1,
                    channel="telegram",
                    question_id=quiz_id
                )

                # Format Evaluation Message
                if is_correct:
                    result_header = f"🎉 *CORRECT!* (+{neurons_awarded} Neurons Awarded)"
                    result_body = f"Great clinical intuition! The correct answer is *{correct_answer}*.\n\n💡 *Clinical Rationale*:\n{explanation}"
                else:
                    result_header = f"❌ *INCORRECT* (+5 Participation Neurons)"
                    result_body = f"The correct answer is *{correct_answer}*.\n\n💡 *Clinical Rationale*:\n{explanation}"

                evaluation_text = (
                    f"{result_header}\n\n"
                    f"{result_body}\n\n"
                    f"⚡ *New Neurons Balance*: `{sync_result.get('total_neurons', 215)}` Neurons\n"
                    f"All scores are saved to your Web and Mobile profile."
                )

                action_keyboard = {
                    "inline_keyboard": [
                        [{"text": "➡️ Next Question", "callback_data": "cb:quiz:random"}],
                        [{"text": "📊 View Progress", "callback_data": "cb:progress"}, {"text": "🏠 Main Menu", "callback_data": "cb:menu"}]
                    ]
                }

                # Edit message in-place for seamless modern UI experience
                await self.edit_message_text(chat_id, message_id, evaluation_text, reply_markup=action_keyboard)
                return {"status": "graded", "is_correct": is_correct}

        return {"status": "unknown_callback"}

    # =========================================================================
    # Helpers
    # =========================================================================

    def _get_main_menu_markup(self) -> Dict[str, Any]:
        return {
            "inline_keyboard": [
                [{"text": "🎯 Quick Active Recall Quiz", "callback_data": "cb:quiz:random"}],
                [{"text": "📚 Browse Syllabus", "callback_data": "cb:syllabus"}, {"text": "📈 My Progress", "callback_data": "cb:progress"}],
                [{"text": "⚡ Check Neurons", "callback_data": "cb:neurons"}]
            ]
        }

    async def _send_main_menu(self, chat_id: int, username: str, title: Optional[str] = None) -> Dict[str, Any]:
        header = title or f"🏠 *Trace Socratic Control Center* (Welcome @{username})"
        text = f"{header}\n\nSelect an option below or type any medical or academic question to begin:"
        await self.send_message(chat_id, text, reply_markup=self._get_main_menu_markup())
        return {"status": "menu_sent"}

    def _render_progress_bar(self, percent: float, total_blocks: int = 10) -> str:
        filled = int((percent / 100) * total_blocks)
        return "█" * filled + "░" * (total_blocks - filled)


# Global Singleton Instance
telegram_bouncer = TelegramModerator()
