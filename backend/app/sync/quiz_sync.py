import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import database_models as models

logger = logging.getLogger("edu_ai.sync.quiz")

def fetch_user_quizzes(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    Fetch normalized quiz history records for a student across all interfaces.
    """
    try:
        quizzes = db.query(models.QuizHistory).filter(
            models.QuizHistory.owner_id == user_id
        ).order_by(models.QuizHistory.id.desc()).all()
        return [
            {
                "id": q.id,
                "unit_name": q.unit_name,
                "score": q.score,
                "total": q.total,
                "pnl": q.pnl,
                "timestamp": q.timestamp
            }
            for q in quizzes
        ]
    except Exception as err:
        logger.error(f"Error fetching quiz history for user {user_id}: {err}")
        return []


def sync_user_quizzes(db: Session, user_id: int, quizzes_payload: List[Any]) -> Dict[str, Any]:
    """
    Synchronizes quiz attempts from client with deduplication.
    """
    synced_count = 0
    for q_item in quizzes_payload:
        try:
            unit_name = getattr(q_item, "unit_name", "General Assessment") or "General Assessment"
            score = int(getattr(q_item, "score", 0) or 0)
            total = int(getattr(q_item, "total", 5) or 5)
            pnl = float(getattr(q_item, "pnl", 0.0) or 0.0)
            timestamp = str(getattr(q_item, "timestamp", "")) or str(time.time())
            
            # Idempotency: avoid duplicate records with identical timestamp and unit
            existing = db.query(models.QuizHistory).filter(
                models.QuizHistory.owner_id == user_id,
                models.QuizHistory.unit_name == unit_name,
                models.QuizHistory.timestamp == timestamp
            ).first()
            
            if not existing:
                db.add(models.QuizHistory(
                    unit_name=unit_name,
                    score=score,
                    total=total,
                    pnl=pnl,
                    timestamp=timestamp,
                    owner_id=user_id
                ))
                synced_count += 1
        except Exception as err:
            logger.warning(f"Error syncing quiz record: {err}")
            
    try:
        db.commit()
    except Exception as err:
        db.rollback()
        logger.error(f"Failed to commit quiz sync: {err}")
        
    return {"synced": synced_count}


def record_quiz_attempt_atomic(
    db: Session,
    user_id: int,
    unit_name: str,
    score: int,
    total: int = 1,
    channel: str = "system",
    question_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Atomic cross-platform quiz submission.
    Calculates mastery, persists to QuizHistory, and awards Neurons.
    Ensures Web, Android, WhatsApp, and Telegram reflect identical scores & Neurons.
    """
    now = time.time()
    total = max(total, 1)
    pnl = round((score / total) * 100, 1)
    timestamp = str(int(now))

    # 1. Deduplication guard (prevent rapid duplicate taps within 4 seconds)
    recent = db.query(models.QuizHistory).filter(
        models.QuizHistory.owner_id == user_id,
        models.QuizHistory.unit_name == unit_name
    ).order_by(models.QuizHistory.id.desc()).first()

    if recent and recent.timestamp and abs(float(recent.timestamp) - now) < 4.0:
        logger.info(f"Deduplicated rapid quiz tap for user {user_id} on {unit_name}")
        user = db.query(models.User).filter(models.User.id == user_id).first()
        return {
            "status": "deduplicated",
            "quiz_id": recent.id,
            "score": recent.score,
            "total": recent.total,
            "pnl": recent.pnl,
            "neurons_awarded": 0,
            "total_neurons": user.trace_coins if user else 0
        }

    # 2. Persist Quiz History
    entry = models.QuizHistory(
        unit_name=unit_name,
        score=score,
        total=total,
        pnl=pnl,
        timestamp=timestamp,
        owner_id=user_id
    )
    db.add(entry)
    db.flush()

    # 3. Award Neurons Currency based on performance
    # Perfect score: +20 Neurons; Passing (>=60%): +10 Neurons; Participation: +5 Neurons
    neurons_awarded = 5
    if score == total and total > 0:
        neurons_awarded = 20
    elif pnl >= 60.0:
        neurons_awarded = 10

    user = db.query(models.User).filter(models.User.id == user_id).first()
    total_neurons = 0
    if user:
        user.trace_coins = (user.trace_coins or 0) + neurons_awarded
        total_neurons = user.trace_coins

    try:
        db.commit()
        logger.info(
            f"Quiz committed atomically: User #{user_id} scored {score}/{total} ({pnl}%) on '{unit_name}' via {channel}. "
            f"+{neurons_awarded} Neurons awarded (Balance: {total_neurons})."
        )
        return {
            "status": "success",
            "quiz_id": entry.id,
            "unit_name": unit_name,
            "score": score,
            "total": total,
            "pnl": pnl,
            "neurons_awarded": neurons_awarded,
            "total_neurons": total_neurons,
            "channel": channel
        }
    except Exception as err:
        db.rollback()
        logger.error(f"Failed to commit atomic quiz attempt: {err}")
        return {"status": "error", "message": str(err)}


def calculate_user_quiz_stats(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Computes aggregated performance metrics across all quiz attempts.
    """
    try:
        quizzes = db.query(models.QuizHistory).filter(models.QuizHistory.owner_id == user_id).all()
        total_attempts = len(quizzes)
        if total_attempts == 0:
            return {
                "total_quizzes": 0,
                "average_pnl": 0.0,
                "mastery_tier": "New Recruit",
                "recent_history": []
            }

        avg_pnl = round(sum(q.pnl for q in quizzes) / total_attempts, 1)
        if avg_pnl >= 85.0:
            tier = "Clinical Master"
        elif avg_pnl >= 70.0:
            tier = "Advanced Scholar"
        elif avg_pnl >= 50.0:
            tier = "Competent Clinician"
        else:
            tier = "Active Learning Foundation"

        recent = [
            {"unit": q.unit_name, "score": f"{q.score}/{q.total}", "pnl": q.pnl, "timestamp": q.timestamp}
            for q in quizzes[-5:]
        ]
        recent.reverse()

        return {
            "total_quizzes": total_attempts,
            "average_pnl": avg_pnl,
            "mastery_tier": tier,
            "recent_history": recent
        }
    except Exception as err:
        logger.error(f"Error computing quiz stats for user {user_id}: {err}")
        return {"total_quizzes": 0, "average_pnl": 0.0, "mastery_tier": "Standard", "recent_history": []}
