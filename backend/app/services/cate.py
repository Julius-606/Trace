
# ==========================================
# IDENTITY: The AI Big Brother / CATE
# FILEPATH: backend/app/services/cate.py
# COMPONENT: Proactive Intelligence
# ROLE: Decides WHEN to bother you based on your context.
# VIBE: Your toxic but highly organized manager. 💅🧠
# ==========================================

import datetime
import logging

logger = logging.getLogger("CATE")

class ContextAwareTriggerEngine:
    def __init__(self):
        self.user_status = "CHILLING" # Could be "TRADING", "STUDYING", "SLEEPING"
    
    def update_context(self, new_status: str):
        self.user_status = new_status
        logger.info(f"CATE updated user context to: {self.user_status}")

    def evaluate_trigger(self, event_type: str, priority: str) -> bool:
        """
        Decides if an event should actually interrupt you.
        Because we don't want a "Study Pharma" notification while you're
        monitoring a heavy lot size on Gold (XAUUSD).
        """
        current_hour = datetime.datetime.now().hour
        
        # Rule 1: Never interrupt deep sleep unless it's a margin call 💀
        if 2 <= current_hour <= 5 and priority != "CRITICAL":
            logger.info("CATE blocked notification. Let bro sleep.")
            return False
            
        # Rule 2: If we are trading, block low-priority study alerts
        if self.user_status == "TRADING" and event_type == "STUDY_REMINDER":
            logger.info("CATE blocked study reminder. Bro is watching the charts.")
            return False
            
        # If it passes the vibe check, blast it
        logger.info(f"CATE approved trigger: {event_type}")
        return True

# Initialize CATE
cate = ContextAwareTriggerEngine()

