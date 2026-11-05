
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models import database_models as models
from app.schemas import api_schemas as schemas
try:
    from ingestion_engine import parse_syllabus_markdown
except ImportError:
    from app.ingestion_engine import parse_syllabus_markdown

router = APIRouter(tags=["Structured Learning"])

def find_user(user_id_or_name: str, db: Session):
    if str(user_id_or_name).isdigit():
        return db.query(models.User).filter(models.User.id == int(user_id_or_name)).first()
    return db.query(models.User).filter(models.User.username == str(user_id_or_name)).first()

@router.get("/syllabuses")
def get_all_syllabuses(db: Session = Depends(get_db)):
    units = db.query(models.Unit).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "category": u.category or "General",
            "course": getattr(u, "course", "Core Sciences") or "Core Sciences",
            "unit_group": getattr(u, "unit_group", None),
            "owner_id": u.owner_id,
            "is_active": getattr(u, "is_active", True)
        }
        for u in units
    ]

@router.get("/syllabuses/{unit_id}/tree", response_model=schemas.UnitResponse)
def get_syllabus_tree(unit_id: int, db: Session = Depends(get_db)):
    unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Syllabus/Unit not found")
    return unit

@router.patch("/progress/subtopic/{subtopic_id}")
def update_subtopic_progress(subtopic_id: int, is_completed: bool, db: Session = Depends(get_db)):
    subtopic = db.query(models.Subtopic).filter(models.Subtopic.id == subtopic_id).first()
    if not subtopic:
        raise HTTPException(status_code=404, detail="Subtopic not found")

    subtopic.is_completed = is_completed
    db.commit()
    db.refresh(subtopic)
    return {"status": "success", "subtopic_id": subtopic_id, "is_completed": is_completed}

from pydantic import BaseModel

class SyllabusIngestRequest(BaseModel):
    user_id: str
    markdown_text: str

@router.post("/syllabuses/ingest-markdown")
def ingest_syllabus_markdown(
    payload: SyllabusIngestRequest,
    db: Session = Depends(get_db)
):
    """
    Parses Markdown syllabus and uploads it to the database for the specified user.
    """
    structured_data = parse_syllabus_markdown(payload.markdown_text)
    return upload_syllabus(structured_data, payload.user_id, db)

@router.post("/syllabuses/upload")
def upload_syllabus(payload: dict, user_id: str, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    created_units = []
    for unit_data in payload.get("units", []):
        new_unit = models.Unit(
            name=unit_data.get("unit_title"),
            owner_id=user.id,
            category=payload.get("syllabus_title", "General")
        )
        db.add(new_unit)
        db.commit()
        db.refresh(new_unit)

        for module_data in unit_data.get("modules", []):
            new_module = models.Module(
                name=module_data.get("module_title"),
                unit_id=new_unit.id
            )
            db.add(new_module)
            db.commit()
            db.refresh(new_module)

            for topic_data in module_data.get("topics", []):
                new_topic = models.Topic(
                    name=topic_data.get("topic_title"),
                    module_id=new_module.id
                )
                db.add(new_topic)
                db.commit()
                db.refresh(new_topic)

                for subtopic_data in topic_data.get("subtopics", []):
                    new_subtopic = models.Subtopic(
                        name=subtopic_data.get("subtopic_title"),
                        topic_id=new_topic.id
                    )
                    db.add(new_subtopic)
                    db.commit()
                    db.refresh(new_subtopic)

                    for objective_text in subtopic_data.get("learning_objectives", []):
                        new_objective = models.LearningObjective(
                            description=objective_text,
                            subtopic_id=new_subtopic.id
                        )
                        db.add(new_objective)

        db.commit()
        created_units.append(new_unit.id)

    # Immediately trigger asynchronous pre-generation pipeline for new units
    if created_units:
        try:
            from app.services.content_pipeline import post_syllabus_event
            post_syllabus_event(created_units, syllabus_title=payload.get("syllabus_title", "General"))
        except Exception as e:
            pass

    return {"status": "success", "created_unit_ids": created_units}

@router.get("/enrichment/subtopic/{subtopic_id}", response_model=schemas.NodeEnrichmentResponse)
def get_subtopic_enrichment(subtopic_id: int, db: Session = Depends(get_db)):
    """
    Fetches pre-generated multi-perspective notes and Mermaid diagram for a subtopic.
    If not yet piped, automatically generates and persists it on-the-fly.
    """
    enrichment = db.query(models.NodeEnrichment).filter(
        models.NodeEnrichment.node_id == subtopic_id,
        models.NodeEnrichment.node_type == "subtopic"
    ).first()

    if not enrichment:
        subtopic = db.query(models.Subtopic).filter(models.Subtopic.id == subtopic_id).first()
        if not subtopic:
            raise HTTPException(status_code=404, detail="Subtopic not found")
        # On-demand JIT generation and immediate database persistence
        from app.services.content_pipeline import ensure_subtopic_content_enriched
        try:
            ensure_subtopic_content_enriched(db, subtopic_id)
            enrichment = db.query(models.NodeEnrichment).filter(
                models.NodeEnrichment.node_id == subtopic_id,
                models.NodeEnrichment.node_type == "subtopic"
            ).first()
        except Exception as e:
            pass

    if not enrichment:
        # Extreme emergency fallback
        from app.services.content_pipeline import generate_fallback_diagram
        diagram = generate_fallback_diagram(subtopic.name, "subtopic")
        return schemas.NodeEnrichmentResponse(
            node_id=subtopic.id,
            node_type="subtopic",
            node_name=subtopic.name,
            intuitive_explanation=f"Conceptual intuition: {subtopic.name}.",
            technical_explanation=f"Technical specification of {subtopic.name}.",
            clinical_takeaway=f"High-yield takeaway: Master core fundamentals of {subtopic.name}.",
            diagram_type=diagram["diagram_type"],
            diagram_code=diagram["diagram_code"],
            diagram_caption=diagram["diagram_caption"],
            metadata_json={}
        )

    return enrichment


@router.get("/subtopics/{subtopic_id}/content")
@router.get("/learning/subtopic/{subtopic_id}")
def get_subtopic_learning_bundle(subtopic_id: int, db: Session = Depends(get_db)):
    """
    Returns the comprehensive, expansive learning module for a subtopic.
    If the subtopic has NOT yet been piped through the background queue,
    the backend automatically generates the expansive content on-the-fly and
    commits it to the database (JUST AS in the pipes), returning the newly saved data.
    """
    from app.services.content_pipeline import ensure_subtopic_content_enriched
    try:
        data = ensure_subtopic_content_enriched(db, subtopic_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/quiz-pool/{unit_name}")
def get_unit_quiz_pool(unit_name: str, db: Session = Depends(get_db)):
    """Fetches all pre-generated questions stored in the library for this unit."""
    questions = db.query(models.GeneratedQuizBank).filter(
        models.GeneratedQuizBank.unit_name.ilike(f"%{unit_name}%")
    ).all()

    return {
        "unit_name": unit_name,
        "total_cached_questions": len(questions),
        "questions": [
            {
                "id": q.id,
                "subtopic_name": q.subtopic_name,
                "question": q.question,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "explanation": q.explanation,
                "difficulty": q.difficulty,
                "scenario": q.clinical_scenario
            }
            for q in questions
        ]
    }

@router.post("/quiz/record")
def record_quiz(history: schemas.QuizRecordRequest, db: Session = Depends(get_db)):
    user = find_user(str(history.user_id), db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_record = models.QuizHistory(
        unit_name=history.unit_name,
        score=history.score,
        total=history.total,
        pnl=(history.score / history.total) * 100 if history.total > 0 else 0,
        owner_id=user.id,
        timestamp=str(history.timestamp)
    )
    db.add(new_record)
    db.commit()
    return {"status": "Success", "message": "Result recorded."}



 