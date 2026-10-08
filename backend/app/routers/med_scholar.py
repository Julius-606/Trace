
################################################################################
#FILE: backend/app/routers/med_scholar.py
#VERSION: 3.1.5 | SYSTEM: Jarvis Protocol
################################################################################

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any
import logging

from app.db.orbit_session import get_orbit_db
from app.models.study import StudyTask

logger = logging.getLogger("Orbit-MedScholar")

router = APIRouter(prefix="/study/tasks", tags=["med-scholar"])

@router.get("/pending")
async def get_pending_tasks(db: AsyncSession = Depends(get_orbit_db)) -> List[Dict[str, Any]]:
    """Fetches pending study tasks."""
    result = await db.execute(select(StudyTask).where(StudyTask.completed == False))
    tasks = result.scalars().all()

    if not tasks:
        return []

    return [{
        "id": t.id,
        "title": t.title,
        "subject": t.subject,
        "brainRotLevel": getattr(t, 'brain_rot_level', 'LOW').name if hasattr(getattr(t, 'brain_rot_level', 'LOW'), 'name') else str(getattr(t, 'brain_rot_level', 'LOW')).split('.')[-1],
        "isCompleted": getattr(t, 'completed', False),
        "dueDate": t.due_date.isoformat() if getattr(t, 'due_date', None) else None
    } for t in tasks]

# 🔥 THE FIX: The VM endpoint to actually receive the completion signal and update Postgres!
@router.put("/{task_id}/complete", status_code=status.HTTP_200_OK)
async def complete_task(task_id: int, db: AsyncSession = Depends(get_orbit_db)):
    """Marks a task as completed in the Matrix."""
    result = await db.execute(select(StudyTask).where(StudyTask.id == task_id))
    task = result.scalars().first()

    if not task:
        logger.warning(f"Attempted to complete ghost task ID: {task_id}")
        raise HTTPException(status_code=404, detail="Task not found. Bro is hallucinating.")

    task.completed = True
    await db.commit()

    logger.info(f"W Secured! Task '{task.title}' marked as completed. Let's go! 🚀")

    # Ideally, we trigger a Blast Protocol here to update the Workstation UI too!
    return {"status": "success", "message": "Bag secured. Task wiped."}
