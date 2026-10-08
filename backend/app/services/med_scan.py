
################################################################################
#FILE: backend/app/services/med_scan.py
#VERSION: 1.0.1 | SYSTEM: Jarvis Protocol
################################################################################

import logging
import google.generativeai as genai
# 🚀 FIX: Added 'app.' prefix
from app.core.config import settings

logger = logging.getLogger("Med-Scan")

class RadiologistEngine:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("Med-Scan OCR initialized. Ready to decode hieroglyphics.")
        else:
            self.model = None
            logger.warning("No Gemini API key. Good luck reading that prescription yourself.")

    async def scan_chart(self, image_bytes: bytes) -> dict:
        if not self.model:
            return {"status": "error", "message": "API Key missing. Cannot process image."}

        logger.info("Processing new medical chart... Hold tight.")

        prompt = """
        You are an expert radiologist, medical scribe, and top-tier Med School professor.
        Read this patient chart, ECG, or medical notes image.
        Extract the key information (Symptoms, Diagnosis, Plan, Pathophysiology) and format it cleanly using Markdown.
        If the handwriting is absolutely cooked and illegible, just do your best and flag it for manual review.
        """

        try:
            response = self.model.generate_content([prompt, image_bytes])
            return {"status": "success", "extracted_data": response.text}
        except Exception as e:
            logger.error(f"Med-Scan hit a snag: {e}")
            return {"status": "error", "message": "Failed to decode the chart. Might actually be a demon spell."}

radiologist = RadiologistEngine()

