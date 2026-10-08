
################################################################################
#FILE: backend/app/db/init_db.py
#VERSION: 1.0.1 | SYSTEM: Jarvis Protocol
################################################################################

import asyncio
# 🚀 FIX: Slapped 'app.' on the DB and Model imports
from app.db.session import async_session, engine
from app.models.study import Base, StudyTask, BrainRotLevel
import logging

logger = logging.getLogger("Orbit-Genesis")

async def init_models():
    """Creates the tables if Alembic hasn't done it yet."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables forged successfully. 🔨")

async def seed_data():
    """Drops some default tasks into the syllabus vault."""
    async with async_session() as db:
        task1 = StudyTask(title="Master the Cardiac Cycle", subject="Cardiology", brain_rot_level=BrainRotLevel.COOKED)
        task2 = StudyTask(title="Review Prop Firm Drawdown Rules", subject="Forex", brain_rot_level=BrainRotLevel.CHILL)

        db.add(task1)
        db.add(task2)
        await db.commit()
        logger.info("Genesis data injected. Orbit is alive.")

async def main():
    await init_models()
    await seed_data()

if __name__ == "__main__":
    logger.info("Initiating Project Orbit Genesis Protocol...")
    asyncio.run(main())

