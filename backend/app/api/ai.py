
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import time
from app.db.session import get_db
from app.models import database_models as models
from app.schemas import api_schemas as schemas
from app.services.ai_service import ai_service
from app.services.curriculum_service import get_unit_learning_outcomes

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])

def find_user(user_id_or_name: str, db: Session):
    if str(user_id_or_name).isdigit():
        return db.query(models.User).filter(models.User.id == int(user_id_or_name)).first()
    return db.query(models.User).filter(models.User.username == str(user_id_or_name)).first()

@router.post("/chat", response_model=schemas.ChatResponse)
def ai_chat(request: schemas.ChatRequest, db: Session = Depends(get_db)):
    user = find_user(str(request.user_id), db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_msg = models.ChatMessage(role="user", content=request.prompt, owner_id=user.id)
    db.add(user_msg)
    db.commit()

    system_instruction = (
        f"You are {user.ai_persona}. "
        "Pedagogical Instruction: When teaching, answering inquiries, or making notes, do NOT view, consider, or adapt to any student status or perceived level. "
        "Your notes and explanations must be strictly objective, comprehensive, and conclusive. "
        "Make clear, structured notes that start with foundational concepts and core definitions first, "
        "and nicely work their way up to intermediate mechanisms and major concepts. Provide definitive, unambiguous, and conclusive academic takeaways."
    )

    history_text = ""
    for msg in request.history:
        history_text += f"{msg.role}: {msg.content}\n"

    full_prompt = f"{history_text}User: {request.prompt}"
    response_text = ai_service.ask(prompt=full_prompt, system_instruction=system_instruction)

    if not response_text:
        raise HTTPException(status_code=500, detail="AI engine is currently unavailable.")

    ai_msg = models.ChatMessage(role="model", content=response_text, owner_id=user.id)
    db.add(ai_msg)
    db.commit()

    return schemas.ChatResponse(response=response_text)

@router.post("/quiz", response_model=schemas.QuizResponse)
def generate_quiz(
    request: schemas.QuizRequest,
    topic: Optional[str] = Query(None),
    subtopic: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    user = find_user(str(request.user_id), db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    chosen_subtopic = request.subtopic or request.topic or subtopic or topic

    # Refer directly to that particular unit's learning outcomes from the curriculum database
    learning_outcomes = get_unit_learning_outcomes(
        unit_name=request.unit_name,
        db=db,
        user=user,
        subtopic_name=chosen_subtopic,
        client_outcomes=request.learning_outcomes
    )

    # 1. Instant Cached Retrieval from Pre-Generated DB Library (Task 1.7)
    query = db.query(models.GeneratedQuizBank).filter(
        models.GeneratedQuizBank.unit_name.ilike(f"%{request.unit_name}%")
    )
    if chosen_subtopic:
        sub_query = query.filter(
            (models.GeneratedQuizBank.subtopic_name.ilike(f"%{chosen_subtopic}%")) |
            (models.GeneratedQuizBank.topic_name.ilike(f"%{chosen_subtopic}%"))
        )
        cached_questions = sub_query.limit(5).all()
    else:
        cached_questions = query.limit(5).all()

    if cached_questions and len(cached_questions) >= 3:
        formatted_questions = []
        for q in cached_questions:
            # Map into schemas.QuizQuestion format
            correct_idx = 0
            if q.options and q.correct_answer in q.options:
                correct_idx = q.options.index(q.correct_answer)
            formatted_questions.append(
                schemas.QuizQuestion(
                    question_text=q.question,
                    options=q.options if isinstance(q.options, list) else list(q.options),
                    correct_option_index=correct_idx,
                    explanation=q.explanation or "Verified clinical reasoning from the pre-generated curriculum library.",
                    learning_outcome=q.learning_outcomes[0] if (q.learning_outcomes and len(q.learning_outcomes) > 0) else None
                )
            )
        return schemas.QuizResponse(
            quiz_title=f"{request.unit_name} - {chosen_subtopic or 'Active Recall'}",
            questions=formatted_questions,
            learning_outcomes=learning_outcomes
        )

    # 2. Fall back to on-demand generation only if the pool is empty
    quiz_data = ai_service.generate_quiz(
        unit_name=request.unit_name,
        student_level=user.semester_status,
        topic=chosen_subtopic,
        learning_outcomes=learning_outcomes
    )
    if not quiz_data:
        raise HTTPException(status_code=500, detail="Failed to ignite the Quiz Engine.")

    if isinstance(quiz_data, dict):
        if "learning_outcomes" not in quiz_data or not quiz_data["learning_outcomes"]:
            quiz_data["learning_outcomes"] = learning_outcomes

        # Asynchronously store new questions into GeneratedQuizBank for future instant hits
        try:
            import time
            for q_obj in quiz_data.get("questions", []):
                q_text = getattr(q_obj, "question_text", None) or q_obj.get("question_text", "")
                opts = getattr(q_obj, "options", None) or q_obj.get("options", [])
                correct_idx = getattr(q_obj, "correct_option_index", 0) or q_obj.get("correct_option_index", 0)
                corr_ans = opts[correct_idx] if opts and correct_idx < len(opts) else (opts[0] if opts else "")
                expl = getattr(q_obj, "explanation", "") or q_obj.get("explanation", "")
                
                db.add(models.GeneratedQuizBank(
                    unit_name=request.unit_name,
                    topic_name=chosen_subtopic,
                    subtopic_name=chosen_subtopic,
                    question=q_text,
                    options=opts,
                    correct_answer=corr_ans,
                    explanation=expl,
                    difficulty="Medium",
                    learning_outcomes=learning_outcomes,
                    created_at=time.time()
                ))
            db.commit()
        except Exception:
            db.rollback()

    return quiz_data


@router.get("/recommendations/{user_id}", response_model=schemas.RecommendationResponse)
def get_recommendations(user_id: str, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    import time
    one_day_ago = time.time() - 86400
    existing_rec = db.query(models.Recommendation).filter(
        models.Recommendation.owner_id == user.id,
        models.Recommendation.timestamp > one_day_ago
    ).order_by(models.Recommendation.timestamp.desc()).first()

    if existing_rec:
        return schemas.RecommendationResponse(recommendation=existing_rec.recommendation)

    quiz_history = db.query(models.QuizHistory).filter(models.QuizHistory.owner_id == user.id).all()
    active_units = [u.name for u in user.units if u.is_active]

    user_info = {
        "username": user.username,
        "ai_persona": user.ai_persona,
        "semester_status": user.semester_status
    }

    # Extract database syllabus progress
    progress_records = db.query(models.UserSyllabusProgress).filter(models.UserSyllabusProgress.user_id == user.id).all()
    completed_nodes = [p.node_id for p in progress_records if p.status == "Completed"]
    
    # Calculate weak and mastered topics from quiz history
    weak = [q.unit_name for q in quiz_history if q.pnl < 70]
    mastered = [q.unit_name for q in quiz_history if q.pnl >= 80]
    
    db_context = schemas.StudyContextPayload(
        mastered_topics=list(set(mastered)),
        weak_topics=list(set(weak)),
        total_quizzes_taken=len(quiz_history),
        average_quiz_score=round(sum([q.pnl for q in quiz_history]) / len(quiz_history), 1) if quiz_history else None
    )

    rec_text = ai_service.get_recommendations(user_info, quiz_history, active_units, study_context=db_context)
    
    if rec_text:
        new_db_rec = models.Recommendation(
            owner_id=user.id,
            recommendation=rec_text,
            timestamp=time.time()
        )
        db.add(new_db_rec)
        db.commit()

    return schemas.RecommendationResponse(recommendation=rec_text or "Keep going!")

@router.post("/recommendations/{user_id}", response_model=schemas.RecommendationResponse)
def get_personalized_recommendations(
    user_id: str,
    payload: Optional[schemas.StudyContextPayload] = None,
    db: Session = Depends(get_db)
):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    import time
    is_force = False
    if payload and getattr(payload, 'force_refresh', False):
        is_force = True

    if not is_force:
        one_day_ago = time.time() - 86400
        existing_rec = db.query(models.Recommendation).filter(
            models.Recommendation.owner_id == user.id,
            models.Recommendation.timestamp > one_day_ago
        ).order_by(models.Recommendation.timestamp.desc()).first()

        if existing_rec:
            return schemas.RecommendationResponse(recommendation=existing_rec.recommendation)

    quiz_history = db.query(models.QuizHistory).filter(models.QuizHistory.owner_id == user.id).all()
    active_units = [u.name for u in user.units if u.is_active]

    user_info = {
        "username": user.username,
        "ai_persona": user.ai_persona,
        "semester_status": user.semester_status
    }

    rec_text = ai_service.get_recommendations(user_info, quiz_history, active_units, study_context=payload)
    
    if rec_text:
        new_db_rec = models.Recommendation(
            owner_id=user.id,
            recommendation=rec_text,
            timestamp=time.time()
        )
        db.add(new_db_rec)
        db.commit()

    return schemas.RecommendationResponse(recommendation=rec_text or "Keep pushing your boundaries!")


 