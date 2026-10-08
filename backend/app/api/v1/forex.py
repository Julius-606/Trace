
# ==========================================
# IDENTITY: The Risk Manager / Forex Guardian
# FILEPATH: backend/app/api/v1/forex.py
# COMPONENT: Backend API Routes
# ROLE: Bridges MT5 to Orbit. Watches for SL/TP, checks leverage.
# VIBE: The friend who takes your phone away when you try to revenge trade. 📉✋
# ==========================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

router = APIRouter()
logger = logging.getLogger("Forex-Guardian")

# Schema for incoming MT5 alerts
class TradeAlert(BaseModel):
    pair: str
    action: str # e.g., "TP_HIT", "SL_HIT", "OVER_LEVERAGED"
    pnl: float
    message: str

@router.post("/alert")
async def trigger_trade_alert(alert: TradeAlert):
    """
    Endpoint hit by the local MT5 bridge when something spicy happens in the market.
    """
    logger.info(f"Forex Alert: {alert.pair} - {alert.action}. PNL: {alert.pnl}")
    
    # Priority scaling based on what happened
    priority = "HIGH" if alert.action in ["SL_HIT", "OVER_LEVERAGED"] else "NORMAL"
    
    # TODO: Inject the WebSockets manager here to blast the notification
    # to the Android app and Laptop UI simultaneously.
    
    # Guardian Psych-Check Logic Placeholder
    if alert.action == "OVER_LEVERAGED":
        warning_msg = f"Yo, we're over-leveraged on {alert.pair}. Orbit is advising you to close a position. Don't be a hero!"
        # This message gets sent to the TTS engine on the phone/laptop
        return {"status": "Alert Broadcasted", "tts_payload": warning_msg, "priority": priority}
        
    return {"status": "Alert Processed", "data": alert}

@router.get("/risk-audit")
async def run_risk_audit():
    """
    Checks total exposure. Keeps you from revenge trading when Anatomy gets too stressful.
    """
    # Placeholder for MT5 Python API logic
    exposure_safe = True 
    
    if not exposure_safe:
        raise HTTPException(status_code=400, detail="Risk limit exceeded. Step away from the charts.")
        
    return {"status": "Risk levels acceptable. Let him cook."}

