
# ==========================================
# IDENTITY: The Manager / Life-Governor
# FILEPATH: backend/app/services/governor.py
# COMPONENT: Chronotype Scheduling Logic
# ROLE: Decides what you should be doing based on the time of day.
# VIBE: "Bro it's 2 AM, why are you trying to learn Cardiology? Go to sleep." 🛏️
# ==========================================

from datetime import datetime
import logging

logger = logging.getLogger("Life-Governor")

class LifeGovernor:
    def __init__(self):
        # Kisumu timezone vibes. 
        # Hardcoding the prime hours based on your chronotype.
        self.peak_focus_hours = range(8, 12)   # 8 AM to 12 PM - Internal Med time
        self.grind_hours = range(14, 18)       # 2 PM to 6 PM - Coding / SHOFCO time
        self.london_session = range(10, 19)    # Forex London crossover vibes

    def get_current_recommendation(self) -> str:
        """
        Returns a string recommending what you should be doing right now.
        """
        current_hour = datetime.now().hour
        
        if current_hour in range(0, 5):
            return "SLEEP_MODE: The markets are dead and your brain is cooked. Go to bed. 💀"
            
        elif current_hour in self.peak_focus_hours:
            return "DEEP_WORK: Highest cognitive load recommended. Lock in on that Med School syllabus."
            
        elif current_hour in self.grind_hours:
            return "EXECUTION: Good time for coding the VM or handling SHOFCO tasks."
            
        elif current_hour >= 20:
            return "WIND_DOWN: Backtest your Forex strategies, review Anki flashcards, and chill."
            
        else:
            return "FLEX_TIME: Do whatever. Maybe grab some fish by the lake?"

governor = LifeGovernor()

