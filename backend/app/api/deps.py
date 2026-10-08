
################################################################################
#SFILE: backend/app/api/deps.py
#VERSION: 1.0.1 | SYSTEM: Jarvis Protocol
################################################################################

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
# 🚀 FIX: Added 'app.' prefix
from app.core.config import settings
import logging

logger = logging.getLogger("API-Bouncer")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def verify_device_access(token: str = Depends(oauth2_scheme)):
    """
    If someone finds your server IP, this stops them from randomly adding
    fake tasks or closing your MT5 trades.
    """
    if token != settings.SECRET_KEY:
        logger.warning("Intruder alert! Someone tried to breach Orbit with a fake token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Opps detected. Access denied.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

