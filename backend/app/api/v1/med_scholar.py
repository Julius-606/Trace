
################################################################################
#FILE: backend/app/api/v1/med_scholar.py
#VERSION: 1.0.1 | SYSTEM: Jarvis Protocol
################################################################################

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# 🚀 FIX: Added 'app.' prefixes
from app.db.orbit_session import get_orbit_db
from app.models.study import StudyTask
from pydantic import BaseModel
from typing import List

router = APIRouter()

class TaskCreate(BaseModel):
    title: str
    subject: str
    brain_rot_level: str = "mid"

@router.post("/tasks/", response_model=dict)
async def create_study_task(task: TaskCreate, db: AsyncSession = Depends(get_orbit_db)):
    """Drop a new task into the syllabus vault."""
    new_task = StudyTask(
        title=task.title,
        subject=task.subject,
        brain_rot_level=task.brain_rot_level
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return {"status": "W", "message": "Task added. Time to lock in.", "task_id": new_task.id}

@router.get("/tasks/pending", response_model=List[dict])
async def get_pending_tasks(db: AsyncSession = Depends(get_orbit_db)):
    """Shows you exactly how behind you are in Med School."""
    result = await db.execute(select(StudyTask).where(StudyTask.completed == False))
    tasks = result.scalars().all()

    if not tasks:
        return [{"message": "Zero pending tasks. You're either a genius or you forgot to write them down."}]

    return [{"id": t.id, "title": t.title, "subject": t.subject} for t in tasks]
