################################################################################
# FILE: backend/app/ingestion_engine.py
# VERSION: 2.0.0 | SYSTEM: Trace Rich Library Engine
# IDENTITY: Standardized Markdown Syllabus Parser, Database Ingestion & Pipeline Kickoff
################################################################################

import re
import json
import logging
from sqlalchemy.orm import Session
from app.models import database_models as models

logger = logging.getLogger("Trace-IngestionEngine")


def parse_syllabus_markdown(text: str) -> dict:
    """
    Parses a markdown string into a structured 5-level syllabus dictionary.
    Level 1: Syllabus Title (# ...)
    Level 2: Unit (## ...)
    Level 3: Module (### ...)
    Level 4: Topic (#### ...)
    Level 5: Subtopic (##### ...) & Learning Objectives (- ...)
    """
    lines = text.split('\n')
    syllabus = {
        "syllabus_title": "General Syllabus",
        "units": []
    }

    current_unit = None
    current_module = None
    current_topic = None
    current_subtopic = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith('# '):
            syllabus["syllabus_title"] = line[2:].strip()
        elif line.startswith('## '):
            current_unit = {
                "unit_title": line[3:].strip(),
                "modules": []
            }
            syllabus["units"].append(current_unit)
            current_module = current_topic = current_subtopic = None
        elif line.startswith('### '):
            if current_unit is not None:
                current_module = {
                    "module_title": line[4:].strip(),
                    "topics": []
                }
                current_unit["modules"].append(current_module)
                current_topic = current_subtopic = None
        elif line.startswith('#### '):
            if current_module is not None:
                current_topic = {
                    "topic_title": line[5:].strip(),
                    "subtopics": []
                }
                current_module["topics"].append(current_topic)
                current_subtopic = None
        elif line.startswith('##### '):
            if current_topic is not None:
                current_subtopic = {
                    "subtopic_title": line[6:].strip(),
                    "learning_objectives": []
                }
                current_topic["subtopics"].append(current_subtopic)
        elif line.startswith('- ') or line.startswith('* '):
            if current_subtopic is not None:
                current_subtopic["learning_objectives"].append(line[2:].strip())

    return syllabus


def save_syllabus_to_db(
    db: Session,
    syllabus_data: dict,
    owner_id=None,
    field: str = None,
    course: str = None,
    unit_group: str = None,
    price_t_coins: int = 20
) -> list:
    """
    Saves parsed syllabus data into the database and immediately kicks off
    the asynchronous Trace Rich Library Engine content_pipeline for pre-generation.
    """
    category_val = (field.strip() if field and field.strip() else None) or syllabus_data.get("syllabus_title") or ("Global" if owner_id is None else "Personal")
    course_val = (course.strip() if course and course.strip() else None) or "Core Sciences"
    group_val = unit_group.strip() if unit_group and unit_group.strip() else None
    coin_price = int(price_t_coins if price_t_coins is not None else 20)

    created_unit_ids = []

    for unit_data in syllabus_data.get("units", []):
        db_unit = models.Unit(
            name=unit_data["unit_title"],
            owner_id=owner_id,
            category=category_val,
            course=course_val,
            unit_group=group_val or unit_data["unit_title"],
            price_t_coins=coin_price
        )
        db.add(db_unit)
        db.flush()
        created_unit_ids.append(db_unit.id)

        for module_data in unit_data.get("modules", []):
            db_module = models.Module(name=module_data["module_title"], unit_id=db_unit.id)
            db.add(db_module)
            db.flush()

            for topic_data in module_data.get("topics", []):
                db_topic = models.Topic(name=topic_data["topic_title"], module_id=db_module.id)
                db.add(db_topic)
                db.flush()

                for subtopic_data in topic_data.get("subtopics", []):
                    db_subtopic = models.Subtopic(name=subtopic_data["subtopic_title"], topic_id=db_topic.id)
                    db.add(db_subtopic)
                    db.flush()

                    for obj in subtopic_data.get("learning_objectives", []):
                        db_obj = models.LearningObjective(description=obj, subtopic_id=db_subtopic.id)
                        db.add(db_obj)

    db.commit()

    # Automatically kick off content_pipeline upon successful syllabus creation
    if created_unit_ids:
        try:
            from app.services.content_pipeline import post_syllabus_event
            post_syllabus_event(created_unit_ids, syllabus_title=category_val)
            logger.info(f"Dispatched content_pipeline pre-generation for units: {created_unit_ids}")
        except Exception as e:
            logger.warning(f"Failed to trigger async content_pipeline: {e}")

    return created_unit_ids


def get_global_units(db: Session):
    return db.query(models.Unit).filter(models.Unit.owner_id.is_(None)).all()


def delete_unit(db: Session, unit_id: int) -> bool:
    unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()
    if unit:
        # Also clean up generated quiz bank and enrichments
        try:
            db.query(models.GeneratedQuizBank).filter(models.GeneratedQuizBank.unit_id == unit_id).delete()
        except Exception:
            pass
        db.delete(unit)
        db.commit()
        return True
    return False


def update_unit(db: Session, unit_id: int, name: str, price_t_coins: int = None) -> bool:
    unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()
    if unit:
        unit.name = name
        if price_t_coins is not None:
            unit.price_t_coins = int(price_t_coins)
        db.commit()
        return True
    return False


def clone_unit_to_user(db: Session, unit_id: int, user_id: int):
    """
    Clones a global unit (and its hierarchy) to a specific user.
    Grandfathers previously enrolled units without charging.
    For new enrollments, verifies Trace coin balance and deducts unit cost.
    """
    global_unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()
    if not global_unit:
        return None

    # Check if user already owns/has this unit grandfathered
    existing_unit = db.query(models.Unit).filter(
        models.Unit.owner_id == user_id,
        models.Unit.name == global_unit.name
    ).first()

    if existing_unit:
        existing_unit.is_active = True
        db.commit()
        db.refresh(existing_unit)
        return existing_unit

    # Check coin balance and deduct for new enrollment
    unit_cost = global_unit.price_t_coins if global_unit.price_t_coins is not None else 20
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        current_coins = user.trace_coins if user.trace_coins is not None else 200
        if current_coins < unit_cost:
            raise ValueError(f"Insufficient Trace coins. Required: {unit_cost} T, Available: {current_coins} T")
        user.trace_coins = current_coins - unit_cost

    new_unit = models.Unit(
        name=global_unit.name,
        owner_id=user_id,
        category="Ongoing",
        course=global_unit.course or "Core Sciences",
        unit_group=global_unit.unit_group or global_unit.name,
        price_t_coins=unit_cost
    )
    db.add(new_unit)
    db.flush()

    for module in global_unit.modules:
        new_module = models.Module(name=module.name, unit_id=new_unit.id)
        db.add(new_module)
        db.flush()

        for topic in module.topics:
            new_topic = models.Topic(name=topic.name, module_id=new_module.id)
            db.add(new_topic)
            db.flush()

            for subtopic in topic.subtopics:
                new_subtopic = models.Subtopic(name=subtopic.name, topic_id=new_topic.id)
                db.add(new_subtopic)
                db.flush()

                for obj in subtopic.learning_objectives:
                    new_obj = models.LearningObjective(description=obj.description, subtopic_id=new_subtopic.id)
                    db.add(new_obj)

    db.commit()

    # Trigger pre-generation pipeline for cloned unit if not already generated
    try:
        from app.services.content_pipeline import post_syllabus_event
        post_syllabus_event([new_unit.id], syllabus_title=new_unit.name)
    except Exception:
        pass

    return new_unit
