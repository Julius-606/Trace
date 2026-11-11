import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import database_models as models

logger = logging.getLogger("edu_ai.sync.user")

def fetch_user_profile(db: Session, user: models.User) -> Dict[str, Any]:
    """
    Serializes user profile and active units safely.
    """
    try:
        active_units = []
        if hasattr(user, "units") and user.units:
            active_units = [u.name for u in user.units if getattr(u, "is_active", True)]
        
        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "difficulty": getattr(user, "difficulty", "Standard") or "Standard",
            "semesterStatus": getattr(user, "semester_status", "Active Session") or "Active Session",
            "aiPersona": getattr(user, "ai_persona", "Academic Mentor") or "Academic Mentor",
            "sensoryMode": getattr(user, "sensory_mode", "Visual") or "Visual",
            "activeUnits": active_units,
            "traceCoins": user.trace_coins if getattr(user, "trace_coins", None) is not None else 200,
            "trace_coins": user.trace_coins if getattr(user, "trace_coins", None) is not None else 200
        }
    except Exception as err:
        logger.error(f"Error serializing user profile for {user.id}: {err}")
        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "traceCoins": getattr(user, "trace_coins", 200) or 200,
            "trace_coins": getattr(user, "trace_coins", 200) or 200
        }

def sync_user_profile(db: Session, user: models.User, payload: Any) -> Dict[str, Any]:
    """
    Updates user settings and enrolled unit associations from payload.
    """
    try:
        user_meta = getattr(payload, "user", None)
        if user_meta:
            if hasattr(user_meta, "difficulty") and user_meta.difficulty:
                user.difficulty = user_meta.difficulty
            if hasattr(user_meta, "semesterStatus") and user_meta.semesterStatus:
                user.semester_status = user_meta.semesterStatus
            if hasattr(user_meta, "aiPersona") and user_meta.aiPersona:
                user.ai_persona = user_meta.aiPersona
            if hasattr(user_meta, "sensoryMode") and user_meta.sensoryMode:
                user.sensory_mode = user_meta.sensoryMode
            db.commit()
            return {"updated": True}
    except Exception as err:
        db.rollback()
        logger.warning(f"Error syncing user profile: {err}")
    return {"updated": False}
