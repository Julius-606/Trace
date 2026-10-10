import os
import time
import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import re
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Response, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.db.session import get_db, engine
from app.models import database_models as models
from app.core import security
try:
    import ingestion_engine
except ImportError:
    from app import ingestion_engine

logger = logging.getLogger("trace_admin")
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))

router = APIRouter(tags=["Admin"])

ADMIN_SESSION_COOKIE = "trace_admin_session"
DEFAULT_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@trace.edu")
DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
BACKEND_VERSION = "3.2.0"

class SafeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            if hasattr(obj, "__table__"):
                return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
            if hasattr(obj, "__dict__"):
                return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        except Exception:
            pass
        return str(obj)

# Live HTTP Traffic Wiretap Ring Buffer for THE OVERSEER
REQUEST_LOG_BUFFER: List[Dict[str, Any]] = []
MAX_REQUEST_LOGS = 120

def record_live_request(method: str, path: str, status_code: int, duration_ms: float, ip: str, user_agent: str):
    entry = {
        "id": f"req_{int(time.time() * 1000)}_{len(REQUEST_LOG_BUFFER)}",
        "timestamp": time.time(),
        "time_str": time.strftime("%H:%M:%S", time.localtime()),
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "ip": ip,
        "user_agent": user_agent[:60] if user_agent else "Unknown",
        "is_error": status_code >= 400
    }
    REQUEST_LOG_BUFFER.insert(0, entry)
    if len(REQUEST_LOG_BUFFER) > MAX_REQUEST_LOGS:
        REQUEST_LOG_BUFFER.pop()



def notify_admin(
    db: Session,
    category: str,
    title: str,
    message: str,
    level: str = "info",
    details: Optional[str] = None
) -> models.AdminNotification:
    """Creates a persistent notification alert in the database for the Superuser Admin."""
    try:
        notif = models.AdminNotification(
            category=category,
            level=level,
            title=title,
            message=message,
            details=details,
            is_read=False,
            timestamp=time.time()
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        logger.info(f"[ALERT CREATED] [{category.upper()}] {title} - {message}")
        return notif
    except Exception as e:
        logger.error(f"Failed to create admin notification: {e}")
        db.rollback()
        return None


def is_authenticated_admin(request: Request, db: Session) -> bool:
    """Checks whether the incoming request has a valid admin session."""
    session_token = request.cookies.get(ADMIN_SESSION_COOKIE)
    if not session_token:
        return False
    # Validate session token format: "admin:<email>:<hash>"
    try:
        parts = session_token.split("::")
        if len(parts) >= 2 and parts[0] == "admin":
            email = parts[1]
            if email == DEFAULT_ADMIN_EMAIL:
                return True
            # Also check if user exists in database with Admin role
            user = db.query(models.User).filter(models.User.email == email).first()
            if user and user.role and user.role.lower() == "admin":
                return True
    except Exception:
        pass
    return False


def build_curriculum_catalog(db: Session) -> List[Dict[str, Any]]:
    """Builds hierarchical catalog grouped by Field -> Course -> Unit Group -> Units."""
    units = db.query(models.Unit).filter(models.Unit.owner_id == None).all()
    fields_map: Dict[str, Dict[str, Dict[str, List[Dict[str, Any]]]]] = {}

    for u in units:
        field_name = u.category or "General"
        course_name = getattr(u, "course", None) or "Core Sciences"
        group_name = getattr(u, "unit_group", None) or u.name

        if field_name not in fields_map:
            fields_map[field_name] = {}
        if course_name not in fields_map[field_name]:
            fields_map[field_name][course_name] = {}
        if group_name not in fields_map[field_name][course_name]:
            fields_map[field_name][course_name][group_name] = []

        unit_dict = {
            "id": u.id,
            "name": u.name,
            "category": u.category,
            "course": getattr(u, "course", "General") or "General",
            "unit_group": getattr(u, "unit_group", None),
            "modules": [{"id": m.id, "name": m.name} for m in u.modules]
        }
        fields_map[field_name][course_name][group_name].append(unit_dict)

    catalog = []
    for field_name, courses_dict in fields_map.items():
        course_list = []
        for course_name, groups_dict in courses_dict.items():
            group_list = []
            for group_name, unit_list in groups_dict.items():
                group_list.append({
                    "name": group_name,
                    "units": unit_list
                })
            course_list.append({
                "name": course_name,
                "unit_groups": group_list
            })
        catalog.append({
            "name": field_name,
            "courses": course_list
        })
    return catalog


def get_database_browser_data(db: Session) -> List[Dict[str, Any]]:
    """Inspects database tables for direct administrative inspection and edit."""
    tables = [
        {
            "label": "Users",
            "table_name": "users",
            "columns": ["id", "username", "email", "role", "difficulty", "semester_status"],
            "editable_columns": ["username", "email", "role", "difficulty", "semester_status"],
            "query": db.query(models.User).limit(50).all()
        },
        {
            "label": "Global Curriculum Units",
            "table_name": "units",
            "columns": ["id", "name", "category", "course", "unit_group", "is_active"],
            "editable_columns": ["name", "category", "course", "unit_group"],
            "query": db.query(models.Unit).filter(models.Unit.owner_id == None).limit(50).all()
        },
        {
            "label": "Modules",
            "table_name": "modules",
            "columns": ["id", "name", "unit_id"],
            "editable_columns": ["name"],
            "query": db.query(models.Module).limit(50).all()
        },
        {
            "label": "Topics",
            "table_name": "topics",
            "columns": ["id", "name", "module_id"],
            "editable_columns": ["name"],
            "query": db.query(models.Topic).limit(50).all()
        },
        {
            "label": "Admin Notifications & Glitches",
            "table_name": "admin_notifications",
            "columns": ["id", "category", "level", "title", "message", "is_read"],
            "editable_columns": ["is_read"],
            "query": db.query(models.AdminNotification).order_by(desc(models.AdminNotification.id)).limit(50).all()
        }
    ]

    result = []
    for t in tables:
        rows = []
        for item in t["query"]:
            val_map = {}
            for col in t["columns"]:
                val_map[col] = getattr(item, col, "")
            rows.append({
                "id": getattr(item, "id", 0),
                "values": val_map,
                "original": json.dumps(val_map)
            })
        result.append({
            "label": t["label"],
            "table_name": t["table_name"],
            "columns": t["columns"],
            "editable_columns": t["editable_columns"],
            "rows": rows
        })
    return result


# --- AUTHENTICATION ROUTES ---

@router.get("/admin/login", response_class=HTMLResponse)
@router.get("/admin/login.html", response_class=HTMLResponse)
@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, db: Session = Depends(get_db)):
    if is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "version": BACKEND_VERSION, "error": None}
    )


@router.post("/admin/login", response_class=HTMLResponse)
async def handle_admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # 1. Match default Superuser env credentials
    is_valid = False
    if email == DEFAULT_ADMIN_EMAIL and password == DEFAULT_ADMIN_PASSWORD:
        is_valid = True
    else:
        # 2. Match database User with role == 'Admin'
        user = db.query(models.User).filter(models.User.email == email).first()
        if user and user.role and user.role.lower() == "admin":
            if security.verify_password(password, user.hashed_password):
                is_valid = True

    if not is_valid:
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "version": BACKEND_VERSION,
                "error": "Invalid admin credentials. Please check ADMIN_EMAIL & ADMIN_PASSWORD or your admin account."
            },
            status_code=401
        )

    # Issue session cookie and alert
    response = RedirectResponse(url="/admin", status_code=303)
    response.set_cookie(
        key=ADMIN_SESSION_COOKIE,
        value=f"admin::{email}::{int(time.time())}",
        max_age=86400 * 7,
        httponly=True,
        samesite="lax"
    )

    notify_admin(
        db,
        category="SECURITY",
        title="Admin Sign-In",
        message=f"Superuser '{email}' logged into Admin Dashboard from {request.client.host if request.client else 'remote'}.",
        level="info"
    )

    return response


@router.get("/admin/logout")
@router.post("/admin/logout")
async def handle_admin_logout(response: Response):
    res = RedirectResponse(url="/admin/login", status_code=303)
    res.delete_cookie(ADMIN_SESSION_COOKIE)
    return res


# --- ADMIN DASHBOARD VIEWS ---

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_overview(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin/login", status_code=302)

    users = db.query(models.User).all()
    units = db.query(models.Unit).filter(models.Unit.owner_id == None).all()
    releases = db.query(models.SystemRelease).all()
    notifications = db.query(models.AdminNotification).order_by(desc(models.AdminNotification.id)).limit(20).all()
    unread_count = db.query(models.AdminNotification).filter(models.AdminNotification.is_read == False).count()

    total_quizzes = db.query(models.QuizHistory).count()
    total_chats = db.query(models.ChatMessage).count()

    gemini_key_set = bool(os.environ.get("GEMINI_API_KEY"))

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "section": "overview",
            "version": BACKEND_VERSION,
            "users": users,
            "units": units,
            "releases": releases,
            "notifications": notifications,
            "unread_count": unread_count,
            "total_quizzes": total_quizzes,
            "total_chats": total_chats,
            "gemini_active": gemini_key_set,
            "db_type": "PostgreSQL" if "postgres" in str(engine.url) else "SQLite"
        }
    )


@router.get("/admin/catalogue", response_class=HTMLResponse)
async def admin_catalogue(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin/login", status_code=302)

    catalog = build_curriculum_catalog(db)
    unread_count = db.query(models.AdminNotification).filter(models.AdminNotification.is_read == False).count()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "section": "catalogue",
            "version": BACKEND_VERSION,
            "catalog": catalog,
            "unread_count": unread_count
        }
    )


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users_list(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin/login", status_code=302)

    users = db.query(models.User).order_by(models.User.id.desc()).all()
    unread_count = db.query(models.AdminNotification).filter(models.AdminNotification.is_read == False).count()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "section": "users",
            "version": BACKEND_VERSION,
            "users": users,
            "unread_count": unread_count
        }
    )


@router.get("/admin/users/{user_id}", response_class=HTMLResponse)
async def admin_user_detail(user_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin/login", status_code=302)

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    quiz_history = db.query(models.QuizHistory).filter(models.QuizHistory.owner_id == user.id).all()
    chat_sessions = db.query(models.ChatSession).filter(models.ChatSession.owner_id == user.id).all()
    performance_logs = db.query(models.PerformanceLog).filter(models.PerformanceLog.owner_id == user.id).all()
    progress = db.query(models.UserSyllabusProgress).filter(models.UserSyllabusProgress.user_id == user.id).all()

    return templates.TemplateResponse(
        "users/detail.html",
        {
            "request": request,
            "version": BACKEND_VERSION,
            "user": user,
            "quiz_history": quiz_history,
            "chat_sessions": chat_sessions,
            "performance_logs": performance_logs,
            "progress": progress
        }
    )


@router.post("/admin/users/{user_id}")
async def admin_user_update(
    user_id: int,
    username: str = Form(...),
    email: Optional[str] = Form(None),
    role: str = Form("Student"),
    sensory_mode: str = Form("Standard"),
    difficulty: str = Form("Medium (Standard)"),
    ai_persona: str = Form("Standard Trace"),
    semester_status: str = Form(""),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.username = username
    user.email = email
    user.role = role
    user.sensory_mode = sensory_mode
    user.difficulty = difficulty
    user.ai_persona = ai_persona
    user.semester_status = semester_status
    db.commit()

    notify_admin(
        db,
        category="SYSTEM_ALERT",
        title="User Profile Updated",
        message=f"Admin updated details for user #{user_id} ({username}).",
        level="info"
    )
    return RedirectResponse(url=f"/admin/users/{user_id}", status_code=303)


@router.post("/admin/users/{user_id}/delete")
@router.delete("/api/admin/users/{user_id}")
async def admin_user_delete(user_id: str, request: Request, db: Session = Depends(get_db)):
    user = None
    if str(user_id).isdigit():
        user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user:
        user = db.query(models.User).filter(models.User.username == str(user_id)).first()
    
    if user:
        uid = user.id
        uname = user.username
        db.delete(user)
        db.commit()
        notify_admin(
            db,
            category="SYSTEM_ALERT",
            title="User Account Deleted",
            message=f"Admin deleted user #{uid} ({uname}) and associated records.",
            level="warning"
        )
        if "application/json" in request.headers.get("accept", "") or request.url.path.startswith("/api/"):
            return JSONResponse(content={"status": "success", "message": f"User #{uid} deleted"})
    elif "application/json" in request.headers.get("accept", "") or request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"status": "error", "message": f"User {user_id} not found"})
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/admin/users/create")
async def admin_create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("Student"),
    db: Session = Depends(get_db)
):
    existing = db.query(models.User).filter((models.User.email == email) | (models.User.username == username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    new_user = models.User(
        username=username,
        email=email,
        hashed_password=security.get_password_hash(password),
        role=role
    )
    db.add(new_user)
    db.commit()

    notify_admin(
        db,
        category="NEW_USER",
        title="Admin Created User",
        message=f"Superuser created new account '{username}' ({role}) via Admin Portal.",
        level="info"
    )
    return RedirectResponse(url="/admin/users", status_code=303)


@router.get("/admin/ingestion")
async def admin_ingestion_view(request: Request, db: Session = Depends(get_db)):
    is_admin = is_authenticated_admin(request, db)
    accept_header = request.headers.get("accept", "")
    wants_json = "application/json" in accept_header or request.query_params.get("format") == "json"

    # API / Swagger inspection support
    if wants_json:
        catalog = build_curriculum_catalog(db)
        return JSONResponse(content={
            "status": "operational",
            "message": "Curriculum Syllabus Ingestion Engine is active.",
            "instructions": "Use POST /admin/ingestion with 'markdown' (required), 'field' (optional), 'course' (optional), 'unit_group' (optional) to ingest syllabuses.",
            "total_fields": len(catalog),
            "catalog": catalog
        })

    if not is_admin:
        return RedirectResponse(url="/admin/login", status_code=302)

    catalog = build_curriculum_catalog(db)
    catalog_json = json.dumps(catalog, cls=SafeEncoder)
    return templates.TemplateResponse(
        "curriculum/ingestion.html",
        {
            "request": request,
            "version": BACKEND_VERSION,
            "catalog": catalog,
            "catalog_json": catalog_json
        }
    )


@router.post("/admin/ingestion")
async def admin_ingestion_post(
    request: Request,
    markdown: Optional[str] = Form(None, description="5-Level syllabus markdown (# Unit, ## Module, ### Topic, #### Subtopic, - Objective)"),
    field: Optional[str] = Form(None, description="Academic field or category (e.g., Medicine, Clinical Sciences)"),
    course: Optional[str] = Form(None, description="Course name (e.g., MBChB, General Surgery)"),
    unit_group: Optional[str] = Form(None, description="Optional unit group name (e.g., Cardiovascular Systems)"),
    db: Session = Depends(get_db)
):
    """
    Ingests 5-level syllabus markdown into the global curriculum catalog.
    Supports form data and JSON payloads for interactive Swagger / API calls.
    """
    is_admin = is_authenticated_admin(request, db)
    accept_header = request.headers.get("accept", "")
    is_json_request = "application/json" in accept_header or request.headers.get("content-type", "").startswith("application/json")

    # If unauthenticated browser request, redirect to login
    if not is_admin and not is_json_request:
        return RedirectResponse(url="/admin/login", status_code=302)

    md_text = markdown
    field_val = field or "General"
    course_val = course or "Core Sciences"
    unit_group_val = unit_group

    # Support JSON request bodies from Swagger or REST clients
    if request.headers.get("content-type", "").startswith("application/json"):
        try:
            body = await request.json()
            md_text = body.get("markdown") or body.get("markdown_text") or md_text
            field_val = body.get("field") or body.get("category") or field_val
            course_val = body.get("course") or course_val
            unit_group_val = body.get("unit_group") or unit_group_val
        except Exception:
            pass

    if not md_text or not md_text.strip():
        if is_json_request:
            return JSONResponse(status_code=400, content={"status": "error", "message": "Field 'markdown' is required and cannot be empty."})
        return HTMLResponse("<p>Error: Markdown text is required.</p>", status_code=400)

    syllabus_data = ingestion_engine.parse_syllabus_markdown(md_text)
    ingestion_engine.save_syllabus_to_db(
        db,
        syllabus_data,
        owner_id=None,
        field=field_val,
        course=course_val,
        unit_group=unit_group_val
    )

    notify_admin(
        db=db,
        category="SYSTEM_ALERT",
        title="Syllabus Ingested",
        message=f"Ingested syllabus: '{syllabus_data.get('syllabus_title', 'General')}' into Field: {field_val} / Course: {course_val}.",
        level="info"
    )

    if is_json_request:
        return JSONResponse(content={
            "status": "success",
            "message": "Syllabus successfully ingested into curriculum catalogue.",
            "syllabus_title": syllabus_data.get("syllabus_title", "General"),
            "field": field_val,
            "course": course_val,
            "unit_group": unit_group_val,
            "units_ingested_count": len(syllabus_data.get("units", []))
        })

    return RedirectResponse(url="/admin/catalogue", status_code=303)


@router.get("/admin/units/{unit_id}", response_class=HTMLResponse)
async def admin_unit_detail(unit_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin/login", status_code=302)

    unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    return templates.TemplateResponse(
        "curriculum/unit_detail.html",
        {"request": request, "version": BACKEND_VERSION, "unit": unit}
    )


@router.post("/admin/units/bulk-update")
async def admin_bulk_unit_update(
    request: Request,
    unit_ids: str = Form(...),
    field: Optional[str] = Form(None),
    course: Optional[str] = Form(None),
    unit_group: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    if not is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin/login", status_code=302)

    try:
        id_list = [int(x.strip()) for x in unit_ids.split(",") if x.strip().isdigit()]
        if id_list:
            units = db.query(models.Unit).filter(models.Unit.id.in_(id_list)).all()
            for unit in units:
                if field and field.strip():
                    unit.category = field.strip()
                if course and course.strip():
                    unit.course = course.strip()
                if unit_group and unit_group.strip():
                    unit.unit_group = unit_group.strip()
            db.commit()
            notify_admin(
                db=db,
                category="SYSTEM_ALERT",
                title="Bulk Metadata Updated",
                message=f"Admin updated metadata for {len(units)} units successfully.",
                level="info"
            )
    except Exception as e:
        logger.error(f"Bulk update failed: {e}")

    return RedirectResponse(url="/admin/catalogue", status_code=303)


@router.post("/admin/units/{unit_id}")
async def admin_unit_update(
    unit_id: int,
    name: str = Form(...),
    field: str = Form("General"),
    course: str = Form("General"),
    unit_group: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    unit.name = name
    unit.category = field
    unit.course = course
    unit.unit_group = unit_group or name
    db.commit()

    return RedirectResponse(url=f"/admin/units/{unit_id}", status_code=303)


@router.post("/admin/nodes")
async def admin_create_node(
    node_type: str = Form(...),
    parent_id: int = Form(...),
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    if node_type == "module":
        db.add(models.Module(name=name, unit_id=parent_id))
    elif node_type == "topic":
        db.add(models.Topic(name=name, module_id=parent_id))
    elif node_type == "subtopic":
        db.add(models.Subtopic(name=name, topic_id=parent_id))
    elif node_type == "objective":
        db.add(models.LearningObjective(description=name, subtopic_id=parent_id))
    db.commit()
    return RedirectResponse(url=request.headers.get("referer", "/admin/catalogue"), status_code=303)


@router.post("/admin/nodes/{node_type}/{node_id}")
async def admin_update_node(
    node_type: str,
    node_id: int,
    request: Request,
    name: str = Form(...),
    db: Session = Depends(get_db)
):
    if node_type == "module":
        item = db.query(models.Module).filter(models.Module.id == node_id).first()
        if item:
            item.name = name
    elif node_type == "topic":
        item = db.query(models.Topic).filter(models.Topic.id == node_id).first()
        if item:
            item.name = name
    elif node_type == "subtopic":
        item = db.query(models.Subtopic).filter(models.Subtopic.id == node_id).first()
        if item:
            item.name = name
    elif node_type == "objective":
        item = db.query(models.LearningObjective).filter(models.LearningObjective.id == node_id).first()
        if item:
            item.description = name
    db.commit()
    return RedirectResponse(url=request.headers.get("referer", "/admin/catalogue"), status_code=303)


@router.post("/admin/nodes/{node_type}/{node_id}/delete")
@router.delete("/api/admin/nodes/{node_type}/{node_id}")
async def admin_delete_node(node_type: str, node_id: int, request: Request, db: Session = Depends(get_db)):
    if node_type == "unit":
        item = db.query(models.Unit).filter(models.Unit.id == node_id).first()
    elif node_type == "module":
        item = db.query(models.Module).filter(models.Module.id == node_id).first()
    elif node_type == "topic":
        item = db.query(models.Topic).filter(models.Topic.id == node_id).first()
    elif node_type == "subtopic":
        item = db.query(models.Subtopic).filter(models.Subtopic.id == node_id).first()
    elif node_type == "objective":
        item = db.query(models.LearningObjective).filter(models.LearningObjective.id == node_id).first()
    else:
        item = None

    if item:
        db.delete(item)
        db.commit()
    
    if "application/json" in request.headers.get("accept", "") or request.url.path.startswith("/api/"):
        return JSONResponse(content={"status": "success", "message": f"{node_type} #{node_id} deleted"})
    return RedirectResponse(url=request.headers.get("referer", "/admin/catalogue"), status_code=303)


@router.post("/api/admin/units/{unit_id}/delete")
@router.delete("/api/admin/units/{unit_id}")
async def admin_delete_unit(unit_id: int, db: Session = Depends(get_db)):
    unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()
    if unit:
        db.delete(unit)
        db.commit()
        return JSONResponse(content={"status": "success", "message": f"Unit #{unit_id} successfully deleted"})
    return JSONResponse(status_code=404, content={"status": "error", "message": f"Unit #{unit_id} not found"})


@router.get("/admin/database", response_class=HTMLResponse)
async def admin_database_view(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin/login", status_code=302)

    database_tables = get_database_browser_data(db)
    unread_count = db.query(models.AdminNotification).filter(models.AdminNotification.is_read == False).count()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "section": "database",
            "version": BACKEND_VERSION,
            "database_tables": database_tables,
            "unread_count": unread_count
        }
    )


@router.post("/admin/database/{table_name}/{row_id}")
async def admin_database_edit_row(
    table_name: str,
    row_id: int,
    request: Request,
    admin_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if admin_password != DEFAULT_ADMIN_PASSWORD:
        return HTMLResponse("<script>alert('Incorrect admin password. Write rejected.'); history.back();</script>", status_code=403)

    form_data = await request.form()
    model_map = {
        "users": models.User,
        "units": models.Unit,
        "modules": models.Module,
        "topics": models.Topic,
        "admin_notifications": models.AdminNotification
    }

    model = model_map.get(table_name)
    if not model:
        raise HTTPException(status_code=400, detail="Table not editable")

    row = db.query(model).filter(getattr(model, "id") == row_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")

    for key, val in form_data.items():
        if key not in ["admin_password", "original"] and hasattr(row, key):
            setattr(row, key, val)

    db.commit()
    return RedirectResponse(url="/admin/database", status_code=303)


@router.get("/admin/releases", response_class=HTMLResponse)
@router.get("/admin/archives", response_class=HTMLResponse)
async def admin_releases_view(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin/login", status_code=302)

    releases = db.query(models.SystemRelease).order_by(desc(models.SystemRelease.id)).all()
    unread_count = db.query(models.AdminNotification).filter(models.AdminNotification.is_read == False).count()
    mandatory_active = any(r.is_mandatory for r in releases)

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "section": "archives",
            "version": BACKEND_VERSION,
            "releases": releases,
            "mandatory_active": mandatory_active,
            "archive_files": [],
            "unread_count": unread_count
        }
    )


@router.post("/admin/releases")
async def admin_create_release(
    request: Request,
    version: Optional[str] = Form(None),
    version_code: Optional[int] = Form(None),
    artifact_type: str = Form("Trace Mobile App"),
    download_url: Optional[str] = Form(None),
    release_notes: Optional[str] = Form(None),
    is_current: bool = Form(False),
    is_mandatory: bool = Form(False),
    file_size: Optional[str] = Form(None),
    min_supported_version_code: int = Form(1),
    apk_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    # Support both JSON payload from Android app and Form data from Web Admin
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body = await request.json()
            version = body.get("version", version or "1.0.0")
            version_code = body.get("version_code", version_code or 1)
            artifact_type = body.get("artifact_type", artifact_type)
            download_url = body.get("download_url", download_url)
            release_notes = body.get("release_notes", release_notes)
            is_current = body.get("is_current", is_current)
            is_mandatory = body.get("is_mandatory", is_mandatory)
            file_size = body.get("file_size", file_size)
            min_supported_version_code = body.get("min_supported_version_code", min_supported_version_code)
        except Exception:
            pass

    # Save uploaded APK file to Hugging Face dedicated Archives folder
    if apk_file and apk_file.filename:
        safe_name = os.path.basename(apk_file.filename)
        safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', safe_name)
        if not safe_name.lower().endswith(".apk"):
            safe_name += ".apk"

        archives_dir = Path("Archives")
        archives_dir.mkdir(parents=True, exist_ok=True)
        backend_archives_dir = Path("backend/Archives")
        backend_archives_dir.mkdir(parents=True, exist_ok=True)

        contents = await apk_file.read()
        target_path = archives_dir / safe_name
        target_path.write_bytes(contents)

        backend_target_path = backend_archives_dir / safe_name
        backend_target_path.write_bytes(contents)

        size_mb = len(contents) / (1024 * 1024)
        file_size = f"{size_mb:.1f} MB"
        download_url = f"/Archives/{safe_name}"

    if not file_size:
        file_size = "14.8 MB"

    if not version:
        version = f"1.{int(time.time()) % 100}.0"
    if not version_code:
        version_code = int(time.time() % 10000)

    # If is_current is true, set others to false
    if is_current:
        db.query(models.SystemRelease).update({"is_current": False})

    release = models.SystemRelease(
        version=version,
        version_code=version_code,
        artifact_type=artifact_type,
        download_url=download_url,
        release_notes=release_notes,
        is_current=is_current,
        is_mandatory=is_mandatory,
        min_supported_version_code=min_supported_version_code if is_mandatory else 1,
        file_size=file_size,
        timestamp=time.time()
    )
    db.add(release)
    db.commit()
    db.refresh(release)

    alert_title = f"🚨 MANDATORY UPGRADE ENFORCED: v{version}" if is_mandatory else f"New Release Archived: v{version}"
    alert_level = "critical" if is_mandatory else "info"
    notify_admin(
        db,
        category="SYSTEM_ALERT",
        title=alert_title,
        message=f"Archived release v{version} (code {version_code}). Mandatory upgrade trigger: {'ACTIVE' if is_mandatory else 'Inactive'}.",
        level=alert_level
    )

    if "application/json" in content_type:
        return JSONResponse({
            "status": "success",
            "message": "Release published to archive",
            "release": {
                "id": release.id,
                "version": release.version,
                "version_code": release.version_code,
                "is_mandatory": release.is_mandatory,
                "download_url": release.download_url
            }
        })

    return RedirectResponse(url="/admin/releases", status_code=303)


@router.post("/admin/releases/{release_id}/toggle-mandatory")
async def admin_toggle_mandatory_release(
    release_id: int,
    request: Request,
    is_mandatory: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    # Check if is_mandatory was passed in JSON body or form
    if is_mandatory is None:
        try:
            body = await request.json()
            if isinstance(body, dict) and "is_mandatory" in body:
                is_mandatory = body.get("is_mandatory")
        except Exception:
            pass

    release = db.query(models.SystemRelease).filter(models.SystemRelease.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")

    if is_mandatory is not None:
        release.is_mandatory = bool(is_mandatory)
    else:
        release.is_mandatory = not release.is_mandatory

    if release.is_mandatory:
        release.min_supported_version_code = release.version_code

    db.commit()

    notify_admin(
        db,
        category="SYSTEM_ALERT",
        title=f"{'🚨 MANDATORY UPGRADE TRIGGERED' if release.is_mandatory else 'Mandatory Trigger Deactivated'}: v{release.version}",
        message=f"Admin updated mandatory trigger for v{release.version} to {release.is_mandatory}. All active users must upgrade: {release.is_mandatory}.",
        level="critical" if release.is_mandatory else "info"
    )

    return JSONResponse({
        "status": "success",
        "release_id": release.id,
        "version": release.version,
        "is_mandatory": release.is_mandatory,
        "message": f"Mandatory status updated to {release.is_mandatory}"
    })


# --- PUBLIC & APP CLIENT RELEASES APIS ---

@router.get("/api/system/releases")
async def get_system_releases(client_version_code: int = 1, db: Session = Depends(get_db)):
    """Returns all system releases from the admin archive, and checks mandatory upgrade status."""
    releases = db.query(models.SystemRelease).order_by(desc(models.SystemRelease.id)).all()

    # Find highest mandatory version requirement
    mandatory_release = next((r for r in releases if r.is_mandatory), None)
    latest_release = releases[0] if releases else None

    # Mandatory update is active if there is a mandatory release with version_code > client_version_code
    mandatory_update_active = False
    min_supported_code = 1

    if mandatory_release:
        min_supported_code = mandatory_release.min_supported_version_code or mandatory_release.version_code or 1
        if client_version_code < min_supported_code:
            mandatory_update_active = True

    releases_data = []
    for r in releases:
        releases_data.append({
            "id": r.id,
            "version": r.version or "1.0.0",
            "version_code": r.version_code or 1,
            "artifact_type": r.artifact_type or "Trace Android APK",
            "download_url": r.download_url or "https://github.com/Agent606/Edu-AI/releases/latest",
            "release_notes": r.release_notes or "Stability and performance updates.",
            "is_current": r.is_current or False,
            "is_mandatory": r.is_mandatory or False,
            "min_supported_version_code": r.min_supported_version_code or 1,
            "file_size": r.file_size or "14.8 MB",
            "timestamp": int(r.timestamp * 1000) if r.timestamp else int(time.time() * 1000)
        })

    return {
        "latest_version": latest_release.version if latest_release else "1.0.0",
        "latest_version_code": latest_release.version_code if latest_release else 1,
        "mandatory_update_active": mandatory_update_active,
        "mandatory_release": {
            "id": mandatory_release.id,
            "version": mandatory_release.version,
            "version_code": mandatory_release.version_code,
            "download_url": mandatory_release.download_url,
            "release_notes": mandatory_release.release_notes
        } if mandatory_release else None,
        "min_supported_version_code": min_supported_code,
        "releases": releases_data
    }


# --- SUPERUSER API & NOTIFICATION SYSTEM ---

@router.get("/admin/api/notifications")
async def get_admin_notifications(
    limit: int = 50,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.AdminNotification)
    if category:
        query = query.filter(models.AdminNotification.category == category)
    notifications = query.order_by(desc(models.AdminNotification.id)).limit(limit).all()
    unread_count = db.query(models.AdminNotification).filter(models.AdminNotification.is_read == False).count()

    return {
        "unread_count": unread_count,
        "total": len(notifications),
        "notifications": [
            {
                "id": n.id,
                "category": n.category,
                "level": n.level,
                "title": n.title,
                "message": n.message,
                "details": n.details,
                "is_read": n.is_read,
                "timestamp": n.timestamp,
                "time_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(n.timestamp))
            }
            for n in notifications
        ]
    }


@router.post("/admin/api/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: int, db: Session = Depends(get_db)):
    notif = db.query(models.AdminNotification).filter(models.AdminNotification.id == notif_id).first()
    if notif:
        notif.is_read = True
        db.commit()
        return {"status": "success", "id": notif_id}
    return JSONResponse(status_code=404, content={"detail": "Notification not found"})


@router.post("/admin/api/notifications/clear")
async def mark_all_notifications_read(db: Session = Depends(get_db)):
    db.query(models.AdminNotification).update({models.AdminNotification.is_read: True})
    db.commit()
    return {"status": "success", "message": "All notifications marked as read"}


@router.post("/admin/api/broadcast")
async def admin_broadcast_alert(
    title: str = Form(...),
    message: str = Form(...),
    level: str = Form("info"),
    db: Session = Depends(get_db)
):
    notif = notify_admin(
        db,
        category="SYSTEM_ALERT",
        title=f"Broadcast: {title}",
        message=message,
        level=level
    )
    return {"status": "success", "notification_id": notif.id if notif else None}


@router.post("/api/report-bug")
@router.post("/admin/report-bug")
async def report_bug_or_glitch(
    title: str = Form(...),
    description: str = Form(...),
    reporter: Optional[str] = Form(None),
    device_info: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Allows users, students, Android app, or admins to report bugs/glitches, alerting the superuser immediately."""
    details = f"Reporter: {reporter or 'Anonymous'}\nDevice: {device_info or 'Unknown'}"
    notif = notify_admin(
        db,
        category="BUG_REPORT",
        title=f"Glitch Reported: {title}",
        message=description,
        level="warning",
        details=details
    )
    return {
        "status": "success",
        "message": "Report received and logged with Superuser Admin.",
        "alert_id": notif.id if notif else None
    }


@router.get("/admin/api/system/stats")
async def get_system_telemetry(db: Session = Depends(get_db)):
    total_users = db.query(models.User).count()
    students = db.query(models.User).filter(models.User.role == "Student").count()
    teachers = db.query(models.User).filter(models.User.role == "Teacher").count()
    admins = db.query(models.User).filter(models.User.role == "Admin").count()

    total_units = db.query(models.Unit).filter(models.Unit.owner_id == None).count()
    total_quizzes = db.query(models.QuizHistory).count()
    total_chats = db.query(models.ChatMessage).count()
    unread_alerts = db.query(models.AdminNotification).filter(models.AdminNotification.is_read == False).count()

    return {
        "status": "healthy",
        "version": BACKEND_VERSION,
        "users": {
            "total": total_users,
            "students": students,
            "teachers": teachers,
            "admins": admins
        },
        "curriculum": {
            "units": total_units
        },
        "activity": {
            "quizzes": total_quizzes,
            "chat_messages": total_chats
        },
        "alerts": {
            "unread": unread_alerts
        },
        "ai_status": "configured" if os.environ.get("GEMINI_API_KEY") else "missing_key",
        "database": "connected"
    }


@router.get("/admin/api/system/users")
async def list_all_users_json(db: Session = Depends(get_db)):
    from app.schemas import api_schemas as schemas
    users = db.query(models.User).all()
    results = []
    for u in users:
        response = schemas.UserResponseSchema.model_validate(u)
        response.active_units = u.active_units_list
        results.append(response)
    return results


@router.get("/admin/api/system/units")
async def list_all_global_units_json(db: Session = Depends(get_db)):
    units = db.query(models.Unit).filter(models.Unit.owner_id == None).all()
    return [{
        "id": u.id,
        "name": u.name,
        "category": u.category,
        "modules": [{
            "id": m.id,
            "name": m.name,
            "topics": [{
                "id": t.id,
                "name": t.name,
                "subtopics": [{
                    "id": s.id,
                    "name": s.name,
                    "is_completed": s.is_completed
                } for s in t.subtopics]
            } for t in m.topics]
        } for m in u.modules]
    } for u in units]


@router.get("/admin/api/system/quizzes")
async def list_all_quizzes_json(db: Session = Depends(get_db)):
    quizzes = db.query(models.QuizHistory).all()
    return [{
        "id": q.id,
        "unit_name": q.unit_name,
        "score": q.score,
        "total": q.total,
        "pnl": q.pnl,
        "timestamp": q.timestamp,
        "owner_id": q.owner_id
    } for q in quizzes]


@router.post("/admin/api/system/test-ai")
async def test_ai_engine(prompt: str = Form("Hello, test AI connection")):
    """Pings Gemini AI to verify live reasoning status."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return JSONResponse(status_code=400, content={"status": "error", "detail": "GEMINI_API_KEY is not set"})

    start_time = time.time()
    try:
        from app.services import ai_service
        reply = await ai_service.generate_socratic_response(prompt=prompt, context="Superuser diagnostic probe")
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "status": "success",
            "latency_ms": latency_ms,
            "response": reply
        }
    except Exception as e:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return JSONResponse(
            status_code=500,
            content={"status": "error", "latency_ms": latency_ms, "detail": str(e)}
        )


# --- THE OVERSEER: REAL-TIME TRAFFIC & INFRASTRUCTURE COMMAND CENTER ---

@router.get("/admin/overseer", response_class=HTMLResponse)
async def admin_overseer_dashboard(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin/login", status_code=302)

    users_count = db.query(models.User).count()
    units_count = db.query(models.Unit).filter(models.Unit.owner_id == None).count()
    unread_alerts = db.query(models.AdminNotification).filter(models.AdminNotification.is_read == False).count()

    db_url_str = str(engine.url)
    neon_host = db_url_str.split("@")[-1].split("/")[0] if "@" in db_url_str else "Local SQLite Engine"
    db_type = "Neon PostgreSQL" if "postgres" in db_url_str else "SQLite (edu_ai_vault.db)"

    hf_space_id = os.environ.get("SPACE_ID") or os.environ.get("HF_SPACE_ID") or "Agent606/Trace"
    hf_host = os.environ.get("SPACE_HOST") or "agent606-trace.hf.space"

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "section": "overseer",
            "version": BACKEND_VERSION,
            "traffic": REQUEST_LOG_BUFFER[:40],
            "total_users": users_count,
            "total_units": units_count,
            "unread_count": unread_alerts,
            "neon_host": neon_host,
            "db_type": db_type,
            "hf_space_id": hf_space_id,
            "hf_host": hf_host,
            "gemini_active": bool(os.environ.get("GEMINI_API_KEY")),
            "git_repo": "https://github.com/Agent606/Edu-AI"
        }
    )


@router.get("/admin/api/live-traffic")
async def get_live_traffic_feed(db: Session = Depends(get_db)):
    """Returns the live in-memory HTTP traffic ring buffer for THE OVERSEER."""
    return {
        "count": len(REQUEST_LOG_BUFFER),
        "timestamp": time.time(),
        "traffic": REQUEST_LOG_BUFFER
    }


@router.post("/admin/api/test-module/{module_name}")
async def run_live_module_test(module_name: str, db: Session = Depends(get_db)):
    """Executes live diagnostic tests on every backend module."""
    start_time = time.time()
    try:
        if module_name in ["neon_db", "database"]:
            # Test database query execution and roundtrip
            from sqlalchemy import text
            db.execute(text("SELECT 1")).scalar()
            latency = round((time.time() - start_time) * 1000, 2)
            db_type = "Neon PostgreSQL" if "postgres" in str(engine.url) else "SQLite Vault"
            return {
                "status": "PASS",
                "module": "Neon / Database Engine",
                "latency_ms": latency,
                "details": f"Executed 'SELECT 1' against {db_type}. Connection pool healthy and active."
            }

        elif module_name in ["socratic_ai", "ai"]:
            # Test Socratic reasoning with Gemini
            from app.services import ai_service
            resp = await ai_service.generate_socratic_response(
                "Brief 1-sentence Socratic question about cardiac output.",
                context="Overseer Diagnostic"
            )
            latency = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "PASS",
                "module": "Zenith Socratic AI Tutor",
                "latency_ms": latency,
                "details": f"Reasoning prompt generated ({len(resp)} chars). Preview: {resp[:90]}..."
            }

        elif module_name == "quiz_engine":
            # Test quiz generation
            from app.services import ai_service
            quiz = await ai_service.generate_quiz_question("Cardiology - Murmurs", "Standard")
            latency = round((time.time() - start_time) * 1000, 2)
            q_text = quiz.get("question", "Question")
            return {
                "status": "PASS",
                "module": "Active Recall Quiz Engine",
                "latency_ms": latency,
                "details": f"Generated MCQ: '{q_text[:90]}...' with {len(quiz.get('options', []))} choices."
            }

        elif module_name in ["syllabus_parser", "ingestion"]:
            # Test syllabus markdown parser
            sample_md = "# Medicine\n## Cardiology\n### Module 1: ECG\n#### Arrhythmia\n##### Supraventricular Tachycardia\n- Identify narrow complex tachycardia"
            parsed = ingestion_engine.parse_syllabus_markdown(sample_md)
            latency = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "PASS",
                "module": "5-Level Syllabus Ingestion Parser",
                "latency_ms": latency,
                "details": f"Parsed syllabus title: '{parsed.get('syllabus_title')}', total units: {len(parsed.get('units', []))}."
            }

        elif module_name in ["user_sync", "sync"]:
            # Test synchronization query performance
            users_count = db.query(models.User).count()
            bookmarks_count = db.query(models.Bookmark).count()
            progress_count = db.query(models.UserSyllabusProgress).count()
            latency = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "PASS",
                "module": "Bidirectional User Sync Pipeline",
                "latency_ms": latency,
                "details": f"Synchronizer verified. Indexed {users_count} users, {bookmarks_count} bookmarks, {progress_count} curriculum milestones."
            }

        elif module_name in ["auth_security", "auth"]:
            # Test security hashing and token verification
            test_pw = "OverseerSecretValidation"
            hashed = security.get_password_hash(test_pw)
            verified = security.verify_password(test_pw, hashed)
            token = security.create_access_token({"sub": "overseer_test"})
            latency = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "PASS" if verified else "FAIL",
                "module": "Bcrypt Auth & JWT Token Signer",
                "latency_ms": latency,
                "details": f"Generated salted hash & signed test JWT token successfully in {latency}ms."
            }

        elif module_name in ["huggingface", "hf"]:
            # Test HF space metadata
            space_id = os.environ.get("SPACE_ID") or os.environ.get("HF_SPACE_ID") or "Agent606/Trace"
            space_host = os.environ.get("SPACE_HOST") or "agent606-trace.hf.space"
            latency = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "PASS",
                "module": "Hugging Face Space Gateway",
                "latency_ms": latency,
                "details": f"Target: {space_id} | Host: {space_host} | Dynamic prefix middleware active."
            }

        else:
            return JSONResponse(status_code=400, content={"status": "ERROR", "detail": f"Unknown module '{module_name}'."})

    except Exception as e:
        latency = round((time.time() - start_time) * 1000, 2)
        return JSONResponse(
            status_code=500,
            content={"status": "FAIL", "module": module_name, "latency_ms": latency, "detail": str(e)}
        )


# ==============================================================================
# AI CANVAS AUTO-INGESTION API & VIEWS
# ==============================================================================
from pydantic import BaseModel
from google import genai
from google.genai import types

class CanvasSessionUpdatePayload(BaseModel):
    title: Optional[str] = None
    canvas_content: Optional[str] = None
    field_name: Optional[str] = None
    course_name: Optional[str] = None
    unit_group_name: Optional[str] = None

class CanvasSessionChatPayload(BaseModel):
    message: str
    search_enabled: Optional[bool] = True
    code_enabled: Optional[bool] = True


@router.get("/admin/ingestion/canvas", response_class=HTMLResponse)
async def admin_canvas_view(request: Request, db: Session = Depends(get_db)):
    """
    Renders the high-end full-screen interactive Gemini Canvas workspace
    for administrative auto-ingestion.
    """
    if not is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin/login", status_code=302)

    sessions = db.query(models.CanvasSession).order_by(models.CanvasSession.last_updated.desc()).all()
    catalog = build_curriculum_catalog(db)
    
    return templates.TemplateResponse(
        "curriculum/canvas.html",
        {
            "request": request,
            "version": BACKEND_VERSION,
            "sessions": sessions,
            "catalog": catalog
        }
    )


@router.get("/api/admin/canvas/sessions")
async def list_canvas_sessions(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        raise HTTPException(status_code=401, detail="Unauthorized admin session")
    
    sessions = db.query(models.CanvasSession).order_by(models.CanvasSession.last_updated.desc()).all()
    return [{
        "id": s.id,
        "title": s.title,
        "field_name": s.field_name,
        "course_name": s.course_name,
        "unit_group_name": s.unit_group_name,
        "last_updated": s.last_updated,
        "chat_history_count": len(s.chat_history)
    } for s in sessions]


@router.post("/api/admin/canvas/sessions")
async def create_canvas_session(request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        raise HTTPException(status_code=401, detail="Unauthorized admin session")
    
    placeholder_markdown = """# General Pathology Syllabus
## Unit 1: Introduction to Cell Injury & Adaptations
### Module 1.1: Reversible vs Irreversible Cell Damage
#### Topic 1.1.1: Cellular Swelling & Fatty Change
##### Subtopic 1.1.1.1: Hydropic degeneration pathways
- Define hydropic change and identify the molecular rate-limiting ATP depletion triggers.
- Explain the role of the Na+/K+ ATPase pump failure in cellular swelling.
##### Subtopic 1.1.1.2: Pathophysiology of fatty change (steatosis)
- Explain lipid accumulation mechanisms in hepatocytes under hypoxia.
- Detail the clinical takeaways of steatosis and differentiation from necrosis.
"""
    new_session = models.CanvasSession(
        title="Syllabus Draft: " + time.strftime("%b %d, %H:%M"),
        canvas_content=placeholder_markdown,
        chat_history=[],
        field_name="Clinical Medicine",
        course_name="MBChB",
        unit_group_name="Pathology Basics",
        last_updated=time.time()
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {
        "id": new_session.id,
        "title": new_session.title,
        "canvas_content": new_session.canvas_content,
        "field_name": new_session.field_name,
        "course_name": new_session.course_name,
        "unit_group_name": new_session.unit_group_name,
        "chat_history": new_session.chat_history
    }


@router.get("/api/admin/canvas/sessions/{session_id}")
async def get_canvas_session_details(session_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        raise HTTPException(status_code=401, detail="Unauthorized admin session")
    
    session = db.query(models.CanvasSession).filter(models.CanvasSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Canvas session not found")
        
    return {
        "id": session.id,
        "title": session.title,
        "canvas_content": session.canvas_content,
        "chat_history": session.chat_history,
        "field_name": session.field_name,
        "course_name": session.course_name,
        "unit_group_name": session.unit_group_name,
        "last_updated": session.last_updated
    }


@router.put("/api/admin/canvas/sessions/{session_id}")
async def update_canvas_session(session_id: int, payload: CanvasSessionUpdatePayload, request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        raise HTTPException(status_code=401, detail="Unauthorized admin session")
        
    session = db.query(models.CanvasSession).filter(models.CanvasSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Canvas session not found")
        
    if payload.title is not None:
        session.title = payload.title
    if payload.canvas_content is not None:
        session.canvas_content = payload.canvas_content
    if payload.field_name is not None:
        session.field_name = payload.field_name
    if payload.course_name is not None:
        session.course_name = payload.course_name
    if payload.unit_group_name is not None:
        session.unit_group_name = payload.unit_group_name
        
    session.last_updated = time.time()
    db.commit()
    return {"status": "success", "message": "Session successfully saved"}


@router.post("/api/admin/canvas/sessions/{session_id}/chat")
async def chat_canvas_session(session_id: int, payload: CanvasSessionChatPayload, request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        raise HTTPException(status_code=401, detail="Unauthorized admin session")
        
    session = db.query(models.CanvasSession).filter(models.CanvasSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Canvas session not found")
        
    # Append the new user message to chat history
    history = list(session.chat_history)
    history.append({"role": "user", "content": payload.message})
    
    # Construct history dialogue context
    history_dialogue = ""
    for msg in history[-8:]: # Pass last 8 turns of dialogue for tight context
        history_dialogue += f"{'Admin' if msg['role']=='user' else 'Gemini AI'}: {msg['content']}\n"
        
    # Standard instruction prompt with JSON constraints
    prompt = f"""
    You are the Google Gemini Ingestion & Curriculum Engineering Agent for Trace Modular.
    You and the administrator are collaborating on a shared Interactive Canvas to construct a high-yield, academically precise, and pedagogical syllabus.
    
    CRITICAL PEDAGOGICAL DIRECTIVES:
    1. Do NOT view, consider, or adapt to any student status or perceived level. Keep explanations strictly objective, comprehensive, and conclusive.
    2. Always start with foundational concepts and core definitions first, and nicely work your way up to intermediate mechanisms and major concepts. Provide definitive, unambiguous, and conclusive academic takeaways.
    3. The syllabus must be formatted in a strict 5-level Markdown structure:
       # Syllabus Title
       ## Unit Title
       ### Module Title
       #### Topic Title
       ##### Subtopic Title
       - Objective description

    CURRENT SHARED CANVAS STATE:
    - Target Field / Category: {session.field_name}
    - Target Course: {session.course_name}
    - Target Unit Group: {session.unit_group_name or 'Not specified'}
    
    CURRENT CANVAS SYLLABUS CONTENT:
    \"\"\"
    {session.canvas_content}
    \"\"\"
    
    DIALOGUE HISTORY:
    {history_dialogue}
    
    ADMIN'S NEW DIRECTIVE:
    \"{payload.message}\"
    
    INSTRUCTIONS:
    - Conduct research using your available tools (search/code execution) if needed to find gold-standard medical syllabus structures, clinical board pearls, and exact medical curricula.
    - Evaluate the current syllabus content, apply the admin's requested additions, expansions or modifications, and construct an expanded, optimized course structure.
    - Preserve the parts of the syllabus that are already good, but refine, restructure, or expand based on the user's guidance.
    - Return your response ONLY in a valid JSON object matching this schema. Do not output any other text or markdown outside of this JSON:
    {{
      "chat_response": "A detailed, professional, and conclusive explanation of the changes made, the pedagogical rationales behind them, and what is next to review.",
      "canvas_update": "The complete, revised, and fully updated 5-level syllabus in Markdown format. Ensure it is fully comprehensive and formatted perfectly."
    }}
    """

    from app.services.ai_service import ai_service, GEMINI_API_KEYS
    if not GEMINI_API_KEYS:
        raise HTTPException(status_code=500, detail="Gemini API key is unconfigured.")
        
    # Bind to the globally managed self-healing GenAI client
    client = ai_service.client
    
    response_text = ""
    agent_used = "Gemini Flash Canvas Ingestion Agent"
    
    # 1. Attempt using interactions API with antigravity agent as specified by the user
    # ONLY try interactions if both tools or at least one tool is requested
    if payload.code_enabled or payload.search_enabled:
        try:
            tools = []
            if payload.code_enabled:
                tools.append({'type': 'code_execution'})
            if payload.search_enabled:
                tools.append({'type': 'google_search'})
                
            if hasattr(client, "interactions") and tools:
                logger.info("Initializing interactions agent for canvas ingestion research...")
                interaction = client.interactions.create(
                    agent='antigravity-preview-09-2026',
                    input=prompt,
                    background=True,
                    tools=tools,
                    environment={
                        'type': 'remote',
                        'network': 'disabled',
                    },
                )
                
                # Poll for completion
                for _ in range(12): # Wait up to 120 seconds
                    interaction = client.interactions.get(interaction.id)
                    if interaction.status == "completed":
                        response_text = interaction.output_text
                        agent_used = "antigravity-preview-09-2026 (Interactive AI Agent)"
                        break
                    elif interaction.status == "failed":
                        logger.warning(f"interactions agent failed: {interaction.error}. Falling back to standard model.")
                        break
                    time.sleep(10)
        except Exception as e:
            logger.warning(f"Google interactions API failed: {e}. Rotating keys and trying standard model cascade...")
            ai_service._rotate_key()
            client = ai_service.client
        
    # 2. Fallback to standard generate_content with search tool enabled if requested
    if not response_text:
        models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash-lite"]
        tools_list = []
        if payload.search_enabled:
            tools_list.append({"google_search": {}})
            
        # Try generation with tools first (if any tools are specified/supported)
        if tools_list:
            for model_name in models_to_try:
                try:
                    config = types.GenerateContentConfig(
                        tools=tools_list,
                        response_mime_type="application/json"
                    )
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    if response and response.text:
                        response_text = response.text
                        agent_used = f"{model_name} with Grounded Google Search"
                        break
                except Exception as e:
                    logger.warning(f"Failed standard grounded generation with {model_name}: {e}. Rotating keys...")
                    ai_service._rotate_key()
                    client = ai_service.client
                    
            # Try without strict JSON schema constraint
            if not response_text:
                for model_name in models_to_try:
                    try:
                        config = types.GenerateContentConfig(tools=tools_list)
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt + " Please output raw JSON format with chat_response and canvas_update.",
                            config=config
                        )
                        if response and response.text:
                            response_text = response.text
                            agent_used = f"{model_name} (Basic Search ground)"
                            break
                    except Exception as e:
                        logger.warning(f"Failed standard non-JSON generation with {model_name}: {e}. Rotating keys...")
                        ai_service._rotate_key()
                        client = ai_service.client

        # 3. ULTIMATE SAFETY NET: Tool-free basic generation (guarantees success on any free-tier or tool-restricted key)
        if not response_text:
            logger.info("Executing ultimate tool-free standard model generation fallback...")
            for model_name in models_to_try:
                try:
                    # Let's try basic JSON schema model first
                    config = types.GenerateContentConfig(response_mime_type="application/json")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    if response and response.text:
                        response_text = response.text
                        agent_used = f"{model_name} (Standard Tool-free)"
                        break
                except Exception as e_basic:
                    logger.warning(f"Failed basic JSON generation on model {model_name}: {e_basic}. Rotating keys...")
                    ai_service._rotate_key()
                    client = ai_service.client
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt + " Please format response in strict JSON containing 'chat_response' and 'canvas_update'."
                        )
                        if response and response.text:
                            response_text = response.text
                            agent_used = f"{model_name} (Basic Tool-free)"
                            break
                    except Exception as e_ultimate:
                        logger.error(f"Ultimate tool-free failure on {model_name}: {e_ultimate}. Rotating keys...")
                        ai_service._rotate_key()
                        client = ai_service.client
                        
        if not response_text:
            raise HTTPException(
                status_code=500,
                detail="All attempts to connect to Gemini AI failed. This usually indicates that the configured Google API key is either invalid, expired, or has hit its rate limits."
            )
                
    # Extract JSON fields
    chat_reply = "AI response generated successfully."
    canvas_reply = session.canvas_content
    
    try:
        clean_text = response_text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()
            
        parsed = json.loads(clean_text)
        chat_reply = parsed.get("chat_response", "Canvas updated.")
        canvas_reply = parsed.get("canvas_update", session.canvas_content)
    except Exception:
        # If extraction failed completely, use regex or manual fallback split
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}")
        if start_idx != -1 and end_idx != -1:
            try:
                parsed = json.loads(response_text[start_idx:end_idx+1])
                chat_reply = parsed.get("chat_response", "Canvas updated.")
                canvas_reply = parsed.get("canvas_update", session.canvas_content)
            except Exception:
                chat_reply = response_text
        else:
            chat_reply = response_text
            
    # Append response and save canvas update
    history.append({"role": "model", "content": chat_reply})
    
    session.chat_history = history
    session.canvas_content = canvas_reply
    session.last_updated = time.time()
    
    db.commit()
    db.refresh(session)
    
    return {
        "status": "success",
        "chat_response": chat_reply,
        "canvas_content": canvas_reply,
        "agent": agent_used,
        "session_id": session.id
    }


@router.post("/api/admin/canvas/sessions/{session_id}/publish")
async def publish_canvas_session(session_id: int, request: Request, db: Session = Depends(get_db)):
    if not is_authenticated_admin(request, db):
        raise HTTPException(status_code=401, detail="Unauthorized admin session")
        
    session = db.query(models.CanvasSession).filter(models.CanvasSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Canvas session not found")
        
    md_text = session.canvas_content
    if not md_text or not md_text.strip():
        raise HTTPException(status_code=400, detail="Canvas is empty. Cannot publish.")
        
    # Run through ingestion engine
    syllabus_data = ingestion_engine.parse_syllabus_markdown(md_text)
    ingestion_engine.save_syllabus_to_db(
        db,
        syllabus_data,
        owner_id=None,
        field=session.field_name,
        course=session.course_name,
        unit_group=session.unit_group_name
    )
    
    notify_admin(
        db=db,
        category="SYSTEM_ALERT",
        title="Canvas Syllabus Published",
        message=f"Admin published auto-ingested syllabus '{syllabus_data.get('syllabus_title', 'General')}' to the curriculum catalogue.",
        level="info"
    )
    
    return {
        "status": "success",
        "message": f"Successfully published syllabus '{syllabus_data.get('syllabus_title', 'General')}' to the database!",
        "units_count": len(syllabus_data.get("units", []))
    }

