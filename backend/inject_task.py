
# ================================================================================
# FILE: /Projects/Orbit/backend/inject_task.py
# PURPOSE: Direct Market Access to PostgreSQL 🪐
# ================================================================================

import sys
import os

# 🛠️ THE HEDGE: Python is having amnesia. We forcefully inject the backend 
# folder into its memory (sys.path) so it knows where the 'app' module lives.
# No more fakeouts!
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.task import Task
from datetime import datetime, timedelta

def inject_liquidity():
    print("Opening connection to the dark pool (Postgres)... 🏦")
    db = SessionLocal()

    try:
        # Create a new limit order (Task)
        new_task = Task(
            title="Review Pharmacology Flashcards",
            subject="Internal Medicine",
            brain_rot_level="HIGH", # Bro is cooked 💀
            completed=False,
            due_date=datetime.now() + timedelta(days=2)
        )

        # Add to the session and commit the transaction
        db.add(new_task)
        db.commit()

        print(f"✅ W Secured! Task '{new_task.title}' injected into Orbit.")
        print("Go tap the Refresh button on your phone now! 📱✨")

    except Exception as e:
        print(f"❌ Stop Loss Hit! Transaction failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    inject_liquidity()

