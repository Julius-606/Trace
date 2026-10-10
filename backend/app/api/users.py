
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
import time
from app.db.session import get_db
from app.models import database_models as models
from app.schemas import api_schemas as schemas
from app.services.ai_service import ai_service
# from app.core.security import get_current_user # To be implemented in core

router = APIRouter(prefix="/users", tags=["User Management"])

def find_user(user_id_or_name: str, db: Session):
    user = None
    if str(user_id_or_name).isdigit():
        user = db.query(models.User).filter(models.User.id == int(user_id_or_name)).first()
    if not user:
        user = db.query(models.User).filter(models.User.username == str(user_id_or_name)).first()
    return user

def user_response(user: models.User) -> schemas.UserResponseSchema:
    response = schemas.UserResponseSchema.model_validate(user)
    response.active_units = user.active_units_list
    return response

@router.get("/{user_id}", response_model=schemas.UserResponseSchema)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        # Auto-create logic from main.py
        role = "Student"
        if "teacher" in user_id.lower(): role = "Teacher"
        user = models.User(username=user_id, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user_response(user)

def populate_default_syllabus(db: Session, user_id: int):
    # Disabled by design: new users start with clean dashboard without hardcoded placeholders (Biochemistry, General Surgery, Internal Medicine)
    return

@router.get("/{user_id}/dashboard", response_model=schemas.DashboardResponse)
def get_dashboard(user_id: str, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        user = models.User(username=user_id, role="Student")
        db.add(user)
        db.commit()
        db.refresh(user)

    active_units = db.query(models.Unit).filter(models.Unit.owner_id == user.id, models.Unit.is_active == True).all()

    unit_names = [u.name for u in active_units]
    quizzes = db.query(models.QuizHistory).filter(models.QuizHistory.owner_id == user.id).all()
    total_quizzes = len(quizzes)
    average_pnl = sum([q.pnl for q in quizzes]) / total_quizzes if total_quizzes > 0 else 0.0
    chat_messages = db.query(models.ChatMessage).filter(models.ChatMessage.owner_id == user.id).order_by(models.ChatMessage.id.asc()).all()

    return schemas.DashboardResponse(
        username=user.username,
        role=user.role,
        sensory_mode=user.sensory_mode,
        semester_status=user.semester_status,
        difficulty=user.difficulty,
        ai_persona=user.ai_persona,
        active_units=unit_names,
        units=active_units,
        average_pnl=round(average_pnl, 2),
        total_quizzes=total_quizzes,
        quiz_history=[schemas.QuizHistoryResponse(unit_name=q.unit_name, pnl=q.pnl, timestamp=q.timestamp) for q in quizzes],
        chat_history=[schemas.ChatMessageResponse(role=c.role, content=c.content, timestamp=c.timestamp or "") for c in chat_messages]
    )

@router.get("/{user_id}/timetable", response_model=schemas.TimetableResponse)
def get_ai_timetable(user_id: str, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    one_week_ago = time.time() - (7 * 24 * 60 * 60)
    existing_timetable = db.query(models.Timetable).filter(models.Timetable.owner_id == user.id, models.Timetable.timestamp > one_week_ago).order_by(models.Timetable.timestamp.desc()).first()

    if existing_timetable:
        return schemas.TimetableResponse(weekly_plan=existing_timetable.weekly_plan_json, ai_brief=existing_timetable.ai_brief)

    last_timetable = db.query(models.Timetable).filter(models.Timetable.owner_id == user.id).order_by(models.Timetable.timestamp.desc()).first()
    previous_plan = last_timetable.weekly_plan_json if last_timetable else None
    quiz_history = db.query(models.QuizHistory).filter(models.QuizHistory.owner_id == user.id).all()
    active_units = [u.name for u in user.units if u.is_active]
    recent_sessions = db.query(models.ChatSession).filter(models.ChatSession.owner_id == user.id).order_by(models.ChatSession.id.desc()).limit(10).all()
    chat_titles = [s.title for s in recent_sessions]

    weak = [q.unit_name for q in quiz_history if q.pnl < 70]
    mastered = [q.unit_name for q in quiz_history if q.pnl >= 80]
    db_context = schemas.StudyContextPayload(
        mastered_topics=list(set(mastered)),
        weak_topics=list(set(weak)),
        total_quizzes_taken=len(quiz_history)
    )

    user_info = {"username": user.username, "semester_status": user.semester_status}
    new_timetable_data = ai_service.generate_timetable(user_info, quiz_history, active_units, chat_titles, previous_plan, study_context=db_context)

    if not new_timetable_data:
        raise HTTPException(status_code=500, detail="The AI is still drafting your plan. Try again in a moment.")

    new_db_timetable = models.Timetable(owner_id=user.id, weekly_plan_json=new_timetable_data["weekly_plan"], ai_brief=new_timetable_data["ai_brief"], timestamp=time.time())
    db.add(new_db_timetable)
    db.commit()

    return schemas.TimetableResponse(weekly_plan=new_timetable_data["weekly_plan"], ai_brief=new_timetable_data["ai_brief"])

@router.post("/{user_id}/timetable", response_model=schemas.TimetableResponse)
def get_personalized_ai_timetable(
    user_id: str,
    payload: Optional[schemas.StudyContextPayload] = None,
    db: Session = Depends(get_db)
):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_force = False
    if payload and getattr(payload, 'force_refresh', False):
        is_force = True

    if not is_force:
        one_week_ago = time.time() - (7 * 24 * 60 * 60)
        existing_timetable = db.query(models.Timetable).filter(
            models.Timetable.owner_id == user.id,
            models.Timetable.timestamp > one_week_ago
        ).order_by(models.Timetable.timestamp.desc()).first()
        if existing_timetable:
            return schemas.TimetableResponse(
                weekly_plan=existing_timetable.weekly_plan_json,
                ai_brief=existing_timetable.ai_brief
            )

    quiz_history = db.query(models.QuizHistory).filter(models.QuizHistory.owner_id == user.id).all()
    active_units = [u.name for u in user.units if u.is_active]
    recent_sessions = db.query(models.ChatSession).filter(models.ChatSession.owner_id == user.id).order_by(models.ChatSession.id.desc()).limit(10).all()
    chat_titles = [s.title for s in recent_sessions]

    user_info = {"username": user.username, "semester_status": user.semester_status}
    new_timetable_data = ai_service.generate_timetable(user_info, quiz_history, active_units, chat_titles, None, study_context=payload)

    if not new_timetable_data:
        raise HTTPException(status_code=500, detail="The AI is still drafting your personalized plan. Try again in a moment.")

    new_db_timetable = models.Timetable(owner_id=user.id, weekly_plan_json=new_timetable_data["weekly_plan"], ai_brief=new_timetable_data["ai_brief"], timestamp=time.time())
    db.add(new_db_timetable)
    db.commit()

    return schemas.TimetableResponse(weekly_plan=new_timetable_data["weekly_plan"], ai_brief=new_timetable_data["ai_brief"])

@router.put("/{user_id}", response_model=schemas.UserResponseSchema)
def update_user(user_id: str, user_update: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = user_update.dict(exclude_unset=True)

    if "active_units" in update_data:
        new_unit_names = update_data.pop("active_units")
        db.query(models.Unit).filter(models.Unit.owner_id == user.id).update({"is_active": False})
        for name in new_unit_names:
            existing_unit = db.query(models.Unit).filter(models.Unit.owner_id == user.id, models.Unit.name == name).first()
            if existing_unit:
                existing_unit.is_active = True
            else:
                db.add(models.Unit(name=name, owner_id=user.id, is_active=True))

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    return user_response(user)


 