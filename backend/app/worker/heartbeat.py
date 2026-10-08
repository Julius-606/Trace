
################################################################################
#FILE: backend/app/worker/heartbeat.py
#VERSION: 1.0.1 | SYSTEM: Jarvis Protocol
################################################################################

import asyncio
import logging
# 🚀 FIX: Added 'app.' prefix to all service imports!
from app.services.governor import governor
from app.services.cate import cate
from app.services.blast import blast_engine

logger = logging.getLogger("Orbit-Heartbeat")

async def forex_market_watch():
    """Simulates a 24/7 background loop checking MT5."""
    while True:
        logger.debug("Scanning Forex charts... XAUUSD looking mid.")
        fake_tp_event = False

        if fake_tp_event:
            await blast_engine.blast_event(
                "TRADE_UPDATE",
                {"pair": "XAUUSD", "status": "TP_HIT", "pnl": "+$500", "message": "Bag secured. Go buy some fish."}
            )

        await asyncio.sleep(60)

async def study_nag_loop():
    """Checks the Governor to see if you should be studying."""
    while True:
        vibe = governor.get_current_recommendation()
        if "DEEP_WORK" in vibe:
            if cate.evaluate_trigger("STUDY_REMINDER", "HIGH"):
                await blast_engine.blast_event(
                    "MED_SCHOLAR",
                    {"message": "Bro, Internal Med isn't going to read itself. Open the textbook."}
                )
        await asyncio.sleep(3600)

async def start_heartbeat():
    logger.info("Starting Orbit Heartbeat... 🫀")
    asyncio.create_task(forex_market_watch())
    asyncio.create_task(study_nag_loop())

