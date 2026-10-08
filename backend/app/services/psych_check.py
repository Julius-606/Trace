
# ==========================================
# IDENTITY: The Therapist / Psych-Check Engine
# FILEPATH: backend/app/services/psych_check.py
# COMPONENT: Proactive Intelligence
# ROLE: Monitors your "heart rate" to lock trading if you're panicking.
# VIBE: "Bro your BPM is 140, step away from the terminal. You are about to revenge trade." 🛑💔
# ==========================================

import logging

logger = logging.getLogger("Psych-Check")

class PsychCheckEngine:
    def __init__(self):
        self.trading_locked = False
        self.baseline_bpm = 70
        self.panic_threshold = 110 # If BPM hits this, we cut the MT5 bridge

    def evaluate_biometrics(self, current_bpm: int):
        """
        In the future, this hooks into your smartwatch API.
        For now, we simulate the vibe check.
        """
        logger.info(f"Psych-Check running. Current BPM: {current_bpm}")

        if current_bpm >= self.panic_threshold:
            self.trading_locked = True
            logger.warning("🚨 PANIC DETECTED 🚨. User is stressing. Locking MT5 terminal.")
            return {
                "status": "LOCKED",
                "message": "Heart rate too high. Trading disabled for 15 minutes. Touch grass."
            }
        
        elif self.trading_locked and current_bpm <= (self.baseline_bpm + 10):
            self.trading_locked = False
            logger.info("User has calmed down. Unlocking terminal. Let him cook.")
            return {
                "status": "UNLOCKED",
                "message": "Vitals stable. You may resume trading."
            }
            
        return {"status": "ACTIVE", "message": "Stay frosty."}

# Global instance
psych_ward = PsychCheckEngine()

