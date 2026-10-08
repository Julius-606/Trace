
################################################################################
#FILE: backend/app/services/llm.py
#VERSION: 1.0.1 | SYSTEM: Jarvis Protocol
################################################################################

import google.generativeai as genai
# 🚀 FIX: Added 'app.' prefix
from app.core.config import settings
import logging

logger = logging.getLogger("Orbit-Speak")

class OrbitSpeak:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("Orbit-Speak initialized. Gemini is online and ready to judge you.")
        else:
            self.model = None
            logger.warning("No Gemini API key found. Orbit is currently mute. 🤐")

    async def generate_response(self, prompt: str, context: str = "chilling") -> str:
        if not self.model:
            return "Bro, you forgot to give me my API key. Check the .env file."

        system_prompt = f"""
        You are Orbit, an advanced Life-OS assistant. 
        Current user context: {context}.
        Keep your responses concise, slightly Gen-Z, and highly pragmatic. 
        If the user is over-leveraging in Forex, tell them to touch grass.
        If they are avoiding Med School studying, roast them.
        """

        full_prompt = f"{system_prompt}\nUser says: {prompt}"

        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API hit a stop loss: {e}")
            return "My brain is fried right now (API Error). Ask me later."

orbit_brain = OrbitSpeak()

