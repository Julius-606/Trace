
################################################################################
# FILE: backend/app/routers/orbit_ai.py
# VERSION: 4.1.0 | SYSTEM: Orbit (The Life-OS Protocol)
# IDENTITY: The Voice / Chat Endpoint - Dementia Fix Applied
################################################################################

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.orbit_session import get_orbit_db
from app.models.study import BrainRotLevel, StudyTask
from app.services.orbit_brain import OrbitAssistant
import asyncio
import logging

logger = logging.getLogger("Orbit-Voice")

router = APIRouter(prefix="/orbit", tags=["Orbit-AI"])

class ChatMessage(BaseModel):
    role: str # "user" or "model"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    reply: str
    status: str = "success"

@router.post("/converse", response_model=ChatResponse)
async def converse_with_orbit(request: ChatRequest, db: AsyncSession = Depends(get_orbit_db)):
    """The main neural link for talking to Orbit. Now with memory!"""
    try:
        assistant = OrbitAssistant(db_session=db)

        user_msg = request.message
        is_staged = user_msg.startswith("[STAGED]")

        # Inject context for staged messages
        if is_staged:
            logger.info("Processing [STAGED] message from offline sync.")
            # We'll let the AI know it's a late processing

        # Run the AI chat with history (Now fully async W)
        ai_reply = await assistant.chat(
            user_msg,
            history=[{"role": h.role, "parts": [h.content]} for h in request.history] if request.history else []
        )

        # Handle task creation from AI tools safely
        if hasattr(assistant, 'tasks_to_create') and assistant.tasks_to_create:
            try:
                from sqlalchemy import text
                await db.execute(text("ALTER TABLE study_tasks ADD COLUMN IF NOT EXISTS is_reminder BOOLEAN DEFAULT FALSE;"))
                await db.execute(text("ALTER TABLE study_tasks ADD COLUMN IF NOT EXISTS remarks TEXT;"))
                await db.commit()
            except Exception as ddl_err:
                await db.rollback()

            for task_data in assistant.tasks_to_create:
                try:
                    new_task = StudyTask(
                        title=task_data.get("title", "Study Task"),
                        subject=task_data.get("subject", "Life Admin"),
                        brain_rot_level=task_data.get("brain_rot_level", BrainRotLevel.MID),
                        is_reminder=task_data.get("is_reminder", False),
                        due_date=task_data.get("due_date")
                    )
                    db.add(new_task)
                    await db.commit()
                    logger.info(f"Task committed: {task_data.get('title')}")
                except Exception as task_err:
                    logger.error(f"Failed to commit full task: {task_err}")
                    await db.rollback()
                    try:
                        simple_task = StudyTask(
                            title=task_data.get("title", "Study Task"),
                            subject=task_data.get("subject", "Life Admin")
                        )
                        db.add(simple_task)
                        await db.commit()
                        logger.info(f"Simplified task committed: {task_data.get('title')}")
                    except Exception as fb_err:
                        logger.error(f"Simple task fallback failed: {fb_err}")
                        await db.rollback()

        return ChatResponse(reply=ai_reply)

    except Exception as e:
        logger.error(f"Orbit's brain crashed: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Orbit's brain crashed: {str(e)}")

