
################################################################################
#FILE: backend/app/api/v1/auth.py
#VERSION: 1.0.1 | SYSTEM: Jarvis Protocol
################################################################################

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
# 🚀 FIX: Added 'app.' prefix
from app.core.config import settings

router = APIRouter()

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Your laptop/phone sends a username and password here.
    If it matches the Vault, we give them a token.
    """
    if form_data.username != "orbit_admin" or form_data.password != "admin_password":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password. Are you an opp?",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": settings.SECRET_KEY, "token_type": "bearer"}

