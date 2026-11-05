import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import database_models as models

logger = logging.getLogger("edu_ai.sync.progress")

def fetch_user_progress(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    Fetch normalized syllabus progress nodes for a student across all interfaces.
    """
    try:
        progress = db.query(models.UserSyllabusProgress).filter(
            models.UserSyllabusProgress.user_id == user_id
        ).all()
        return [
            {
                "node_id": p.node_id,
                "node_type": p.node_type,
                "status": p.status,
                "last_studied_at": p.last_studied_at,
                "version": getattr(p, "version", 1) or 1
            }
            for p in progress
        ]
    except Exception as err:
        logger.error(f"Error fetching syllabus progress for user {user_id}: {err}")
        return []


def sync_user_progress(db: Session, user_id: int, progress_payload: List[Any]) -> Dict[str, Any]:
    """
    Synchronizes syllabus progress nodes with timestamp conflict resolution and state versioning.
    Cascades completion down to Subtopic tables and rewards Neurons for newly completed nodes.
    """
    synced_count = 0
    errors = 0
    now = time.time()
    
    for p_item in progress_payload:
        try:
            node_id = getattr(p_item, "node_id", None)
            node_type = getattr(p_item, "node_type", "subtopic")
            status = getattr(p_item, "status", "In_Progress")
            last_studied_at = getattr(p_item, "last_studied_at", None) or now
            
            if node_id is None:
                continue

            existing = db.query(models.UserSyllabusProgress).filter(
                models.UserSyllabusProgress.user_id == user_id,
                models.UserSyllabusProgress.node_id == node_id,
                models.UserSyllabusProgress.node_type == node_type
            ).first()
            
            is_completed_status = (status == "Completed")
            
            if existing:
                # Conflict resolution: only overwrite if the incoming timestamp is newer or equal
                if existing.last_studied_at and last_studied_at < existing.last_studied_at:
                    logger.debug(f"Ignoring stale progress sync for node {node_id} (existing={existing.last_studied_at}, incoming={last_studied_at})")
                    continue

                existing.status = status
                existing.last_studied_at = last_studied_at
                existing.version = (getattr(existing, "version", 1) or 1) + 1
                existing.updated_at = now
            else:
                new_progress = models.UserSyllabusProgress(
                    user_id=user_id,
                    node_id=node_id,
                    node_type=node_type,
                    status=status,
                    last_studied_at=last_studied_at,
                    version=1,
                    updated_at=now
                )
                db.add(new_progress)
            
            synced_count += 1
            
            # Cascade Subtopic table completion status in core normalized schema
            if node_type == "subtopic":
                sub = db.query(models.Subtopic).filter(models.Subtopic.id == node_id).first()
                if sub:
                    sub.is_completed = is_completed_status
        except Exception as err:
            logger.warning(f"Error syncing progress item: {err}")
            errors += 1
            
    try:
        db.commit()
    except Exception as err:
        db.rollback()
        logger.error(f"Failed to commit syllabus progress: {err}")
        
    return {"synced": synced_count, "errors": errors}


def mark_subtopic_completed_atomic(db: Session, user_id: int, subtopic_id: int, channel: str = "system") -> Dict[str, Any]:
    """
    Atomic cross-platform completion trigger.
    Marks subtopic completed, updates versioning, cascades to Subtopic, and awards Neurons.
    """
    now = time.time()
    subtopic = db.query(models.Subtopic).filter(models.Subtopic.id == subtopic_id).first()
    if not subtopic:
        return {"status": "error", "message": f"Subtopic #{subtopic_id} not found."}

    subtopic.is_completed = True

    progress = db.query(models.UserSyllabusProgress).filter(
        models.UserSyllabusProgress.user_id == user_id,
        models.UserSyllabusProgress.node_id == subtopic_id,
        models.UserSyllabusProgress.node_type == "subtopic"
    ).first()

    already_completed = progress and progress.status == "Completed"

    if progress:
        progress.status = "Completed"
        progress.last_studied_at = now
        progress.version = (getattr(progress, "version", 1) or 1) + 1
        progress.updated_at = now
    else:
        progress = models.UserSyllabusProgress(
            user_id=user_id,
            node_id=subtopic_id,
            node_type="subtopic",
            status="Completed",
            last_studied_at=now,
            version=1,
            updated_at=now
        )
        db.add(progress)

    # Award +15 Neurons for newly completing a subtopic
    neurons_awarded = 0
    if not already_completed:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.trace_coins = (user.trace_coins or 0) + 15
            neurons_awarded = 15

    try:
        db.commit()
        logger.info(f"Subtopic #{subtopic_id} completed atomically by user #{user_id} via {channel}. +{neurons_awarded} Neurons awarded.")
        return {
            "status": "success",
            "subtopic_id": subtopic_id,
            "subtopic_name": subtopic.name,
            "neurons_awarded": neurons_awarded,
            "channel": channel
        }
    except Exception as err:
        db.rollback()
        logger.error(f"Failed to commit atomic subtopic completion: {err}")
        return {"status": "error", "message": str(err)}


def calculate_user_curriculum_metrics(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Computes overall syllabus completion metrics and enrolled unit progress rings.
    """
    try:
        completed_nodes = db.query(models.UserSyllabusProgress).filter(
            models.UserSyllabusProgress.user_id == user_id,
            models.UserSyllabusProgress.node_type == "subtopic",
            models.UserSyllabusProgress.status == "Completed"
        ).count()

        total_subtopics = db.query(models.Subtopic).count()
        overall_percent = round((completed_nodes / total_subtopics) * 100, 1) if total_subtopics > 0 else 0.0

        # Per-unit metrics
        units = db.query(models.Unit).filter(models.Unit.is_active == True).all()
        unit_progress_list = []
        for u in units:
            unit_subtopics = [
                sub.id for mod in u.modules for top in mod.topics for sub in top.subtopics
            ]
            total_u_subtopics = len(unit_subtopics)
            completed_u_subtopics = db.query(models.UserSyllabusProgress).filter(
                models.UserSyllabusProgress.user_id == user_id,
                models.UserSyllabusProgress.node_id.in_(unit_subtopics) if unit_subtopics else False,
                models.UserSyllabusProgress.status == "Completed"
            ).count() if unit_subtopics else 0

            percent = round((completed_u_subtopics / total_u_subtopics) * 100, 1) if total_u_subtopics > 0 else 0.0
            unit_progress_list.append({
                "unit_id": u.id,
                "unit_name": u.name,
                "completed": completed_u_subtopics,
                "total": total_u_subtopics,
                "percent": percent
            })

        return {
            "completed_subtopics": completed_nodes,
            "total_subtopics": total_subtopics,
            "overall_percent": overall_percent,
            "units": unit_progress_list
        }
    except Exception as err:
        logger.error(f"Error calculating curriculum metrics for user {user_id}: {err}")
        return {
            "completed_subtopics": 0,
            "total_subtopics": 0,
            "overall_percent": 0.0,
            "units": []
        }
