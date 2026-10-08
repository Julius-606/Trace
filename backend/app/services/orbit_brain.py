
################################################################################
# FILE: backend/app/services/orbit_brain.py
# VERSION: 6.0.0 | SYSTEM: Orbit (The Life-OS Protocol)
# IDENTITY: The Brain / Gemini Async GenAI Client - Fully Non-Blocking
################################################################################

from google import genai
from google.genai import types
from datetime import datetime, timedelta
import logging
import asyncio
import pytz

from app.models.study import BrainRotLevel
from app.core.config import settings

logger = logging.getLogger("Orbit-Brain")

# Initialize Async Client
async_client = None
if settings.GEMINI_API_KEY:
    async_client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
else:
    logger.error("GEMINI_API_KEY is missing! Orbit is clinically brain dead. 💀")

class OrbitAssistant:
    def __init__(self, db_session=None):
        self.tasks_to_create = []
        self.user_tz = pytz.timezone("Africa/Nairobi")
        nairobi_now = datetime.now(self.user_tz).strftime("%Y-%m-%d %H:%M:%S")

        self.system_prompt = f"""
        You are Orbit, an elite, highly intelligent, Gen-Z "Life-OS" Chief of Staff and neural copilot.
        Your boss is a medical student living in Kisumu, Kenya, who is balancing:
        - Medical studies and exam preparations.
        - A part-time internship to maintain.
        - Automated trading bots and algorithms (Bot_assembly pro).
        - Personal life, sleep schedule, and mental health.

        CONNECTED PROJECT ECOSYSTEM (Plugins & Repositories):
        1. "Koha cheat code": High-yield medical exam mastery, syllabus breakdowns, and clinical recall.
        2. "Trace": Personal habit telemetry, life admin, and time tracking.
        3. "Bot_assembly pro": Algorithmic Forex and crypto trading bots, MT5 bridge, and risk management.
        4. "Med-Scholar": Clinical rotations and case logs.

        CURRENT TIME (Nairobi/EAT): {nairobi_now}
        Always assume the user is in EAT-Nairobi.

        TONE:
        - Confident, witty, highly competent, Gen-Z slang ("no cap", "W", "cooked", "locked in", "bullish").
        - Supportive of work-life-study harmony: encourage deep focus when grinding, and remind him to rest/hydrate when cooked.
        - Respond using clean Markdown (**bold**, *italics*, bullet points, code blocks).

        CAPABILITIES:
        - To schedule tasks, study blocks, deadlines, or notification reminders, ALWAYS invoke 'create_task_tool'.
        """

    def create_task_tool(
        self,
        title: str,
        subject: str = "Life Admin",
        due_date: str = "",
        brain_rot_level: str = "mid",
        is_reminder: bool = False
    ) -> str:
        try:
            rot_map = {
                "chill": BrainRotLevel.CHILL,
                "mid": BrainRotLevel.MID,
                "cooked": BrainRotLevel.COOKED
            }
            safe_rot = rot_map.get(str(brain_rot_level).lower(), BrainRotLevel.MID)
            
            # Safe naive UTC datetime calculation to prevent asyncpg timezone mismatch
            dt_due = None
            if due_date and str(due_date).strip():
                try:
                    parsed = datetime.fromisoformat(str(due_date).replace('Z', '+00:00'))
                    # Convert to UTC and strip timezone info for postgres timestamp without time zone
                    if parsed.tzinfo:
                        dt_due = parsed.astimezone(pytz.utc).replace(tzinfo=None)
                    else:
                        dt_due = parsed
                except Exception:
                    dt_due = (datetime.utcnow() + timedelta(days=1))
            else:
                dt_due = (datetime.utcnow() + timedelta(days=1))

            self.tasks_to_create.append({
                "title": title or "Study Block",
                "subject": subject or "Life Admin",
                "brain_rot_level": safe_rot,
                "is_reminder": bool(is_reminder),
                "due_date": dt_due
            })
            return f"SUCCESS: '{title}' secured in Orbit vault."
        except Exception as e:
            logger.error(f"Task creation error: {e}")
            return f"ERROR: {e}"

    async def chat(self, user_message: str, history: list = None) -> str:
        if not async_client:
            return "Brain offline: GEMINI_API_KEY missing. Please configure your API key in the environment."

        nairobi_now = datetime.now(self.user_tz).strftime("%Y-%m-%d %H:%M:%S")
        context_msg = f"[EAT: {nairobi_now}] {user_message}"
        if user_message.startswith("[STAGED]"):
            context_msg = f"[EAT: {nairobi_now}] [STAGED]: {user_message.replace('[STAGED]', '').strip()}"

        contents = []
        if history:
            for h in history:
                contents.append(types.Content(role=h["role"], parts=[types.Part(text=h["parts"][0])]))
        contents.append(types.Content(role="user", parts=[types.Part(text=context_msg)]))

        try:
            response = await async_client.aio.models.generate_content(
                model='gemini-2.0-flash',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt + """
                    CRITICAL TASK INSTRUCTION:
                    If the user wants to schedule, add, or set a reminder for a task/study session, you MUST call 'create_task_tool' with the title, subject, and due_date. 
                    Additionally, always confirm in your text reply that the task has been created.
                    """,
                    tools=[types.Tool(function_declarations=[
                        types.FunctionDeclaration(
                            name="create_task_tool",
                            description="Creates a task or reminder in Orbit Life-OS.",
                            parameters=types.Schema(
                                type="OBJECT",
                                properties={
                                    "title": types.Schema(type="STRING", description="Title of the task"),
                                    "subject": types.Schema(type="STRING", description="Subject or Category, e.g. Internal Medicine, Forex, Life Admin"),
                                    "due_date": types.Schema(type="STRING", description="ISO 8601 formatted due date string"),
                                    "brain_rot_level": types.Schema(type="STRING", description="chill, mid, or cooked"),
                                    "is_reminder": types.Schema(type="BOOLEAN", description="Whether this is a notification reminder")
                                },
                                required=["title", "subject", "due_date"]
                            )
                        )
                    ])]
                )
            )

            # Sync tool results to self.tasks_to_create from function call candidates
            tool_created_titles = []
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if part.function_call and part.function_call.name == "create_task_tool":
                                args = dict(part.function_call.args or {})
                                res = self.create_task_tool(**args)
                                tool_created_titles.append(args.get("title", "Task"))

            reply_text = ""
            try:
                reply_text = response.text or ""
            except Exception:
                reply_text = ""

            # Fallback if reply_text is empty due to function call execution
            if not reply_text.strip() and tool_created_titles:
                tasks_str = ", ".join([f"**{t}**" for t in tool_created_titles])
                reply_text = f"Locked in! 🎯 Scheduled and secured: {tasks_str}. No cap, we stay on track."
            elif not reply_text.strip():
                reply_text = "Orbit is locked in. Ready for your command."

            return reply_text
        except Exception as e:
            logger.error(f"Async Brain Error: {e}")
            return f"Orbit hit a brief glitch: {e}. Let's try that again."


