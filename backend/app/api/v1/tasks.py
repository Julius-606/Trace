
################################################################################
# FILE: backend/app/api/v1/tasks.py
# VERSION: 4.0.0 | SYSTEM: Orbit Protocol
# IDENTITY: Task Management / Life Admin Router - V4.0.0 Upgrades
################################################################################

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.orbit_session import get_orbit_db
from app.models.study import StudyTask, BrainRotLevel

from app.services.governor import governor

logger = logging.getLogger("orbit_tasks")
router = APIRouter()

class TaskCreatePayload(BaseModel):
    title: str
    subject: str = "Life Admin"
    brain_rot_level: str = "mid"
    is_reminder: bool = False
    due_date: Optional[datetime] = None

class TaskCompletePayload(BaseModel):
    remarks: Optional[str] = None

@router.get("/", status_code=status.HTTP_200_OK)
async def get_all_tasks(db: AsyncSession = Depends(get_orbit_db)):
    """Fetch all active tasks with full metadata."""
    try:
        current_vibe = governor.get_current_recommendation() if hasattr(governor, 'get_current_recommendation') else "Grind Mode Activated"

        result = await db.execute(select(StudyTask))
        tasks = result.scalars().all()

        task_list = [
            {
                "id": t.id,
                "title": t.title,
                "subject": t.subject,
                "brain_rot_level": t.brain_rot_level.value if hasattr(t.brain_rot_level, 'value') else t.brain_rot_level,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "is_reminder": t.is_reminder,
                "completed": t.completed,
                "remarks": t.remarks
            } for t in tasks
        ]

        return {
            "status": "bullish 📈",
            "message": "Tasks loaded successfully.",
            "governor_status": current_vibe,
            "data": task_list
        }
    except Exception as e:
        logger.error(f"Task fetch liquidated: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch tasks.")

@router.get("/pending", status_code=status.HTTP_200_OK)
async def get_pending_tasks(db: AsyncSession = Depends(get_orbit_db)):
    """Fetch only the pending tasks for the Android sorting logic."""
    try:
        logger.info("Mobile hit /pending. Sorting by Brain Rot level soon.")

        result = await db.execute(select(StudyTask).where(StudyTask.completed == False))
        tasks = result.scalars().all()

        task_list = [
            {
                "id": t.id,
                "title": t.title,
                "subject": t.subject,
                "brain_rot_level": t.brain_rot_level.value if hasattr(t.brain_rot_level, 'value') else t.brain_rot_level,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "is_reminder": t.is_reminder
            } for t in tasks
        ]

        return {
            "status": "bullish 📈",
            "message": "Pending tasks secured.",
            "data": task_list
        }
    except Exception as e:
        logger.error(f"Pending tasks fetch liquidated: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch pending tasks.")

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreatePayload, db: AsyncSession = Depends(get_orbit_db)):
    """Inject a new task into the Brain. 🧠"""
    try:
        rot_map = {"chill": BrainRotLevel.CHILL, "mid": BrainRotLevel.MID, "cooked": BrainRotLevel.COOKED}
        safe_rot = rot_map.get(task_data.brain_rot_level.lower(), BrainRotLevel.MID)

        new_task = StudyTask(
            title=task_data.title,
            subject=task_data.subject,
            brain_rot_level=safe_rot,
            is_reminder=task_data.is_reminder,
            due_date=task_data.due_date
        )
        db.add(new_task)
        await db.commit()

        return {
            "status": "success",
            "message": "Task injected into Orbit. 🎯"
        }
    except Exception as e:
        logger.error(f"Failed to create task: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=400, detail="Task creation failed.")

@router.post("/{task_id}/complete", status_code=status.HTTP_200_OK)
async def complete_task(task_id: int, payload: TaskCompletePayload, db: AsyncSession = Depends(get_orbit_db)):
    """The CompleteTask Endpoint: Captures remarks and marks as finished."""
    try:
        logger.info(f"Completing task {task_id} with remarks: {payload.remarks}")
        result = await db.execute(select(StudyTask).where(StudyTask.id == task_id))
        task = result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")

        task.completed = True
        task.remarks = payload.remarks

        await db.commit()
        return {"status": "success", "message": "Task secured and remarks filed. ✅"}
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to complete task: {str(e)}")
        raise HTTPException(status_code=500, detail="Error completing task.")

@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_orbit_db)):
    """Wipe a task from existence. Hard delete."""
    try:
        result = await db.execute(select(StudyTask).where(StudyTask.id == task_id))
        task = result.scalars().first()
        if task:
            await db.delete(task)
            await db.commit()
            return {"status": "deleted", "message": "Task wiped."}
        return {"status": "error", "message": "Task not found."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting task.")

