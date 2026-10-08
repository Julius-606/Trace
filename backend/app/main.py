
import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("trace_backend")

# Load .env BEFORE any other app imports to ensure environment variables are available
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.session import engine, Base, get_db
from app.db.orbit_session import initialize_orbit_database
from app.api import auth, users, ai, teacher, parent, learning, admin
from app.api.v1.api import api_router as orbit_api_router
from app.core import security
from app.models import database_models as models
from app.schemas import api_schemas as schemas
from typing import List, Optional, Dict, Any
import httpx
try:
    import ingestion_engine
except ImportError:
    from app import ingestion_engine

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))
WEBAPP_DIST_DIR = Path(__file__).resolve().parents[1] / "webapp_dist"

# Safe database initialization on startup
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas verified successfully.")
    with Session(bind=engine) as init_db:
        # Smart automated migrations: Ensure columns exist on 'bookmarks' table
        from sqlalchemy import text
        is_postgres = "postgresql" in str(engine.url)
        
        # 1. Ensure all columns on 'bookmarks' table exist (auto-healing schema)
        bookmark_columns = [
            ("type", "VARCHAR(50) DEFAULT 'general'"),
            ("title", "VARCHAR(200) DEFAULT 'Saved Item'"),
            ("target", "VARCHAR(500) DEFAULT ''"),
            ("context", "TEXT"),
            ("notes", "TEXT"),
            ("timestamp", "DOUBLE PRECISION DEFAULT 0" if is_postgres else "FLOAT DEFAULT 0"),
            ("owner_id", "INTEGER")
        ]
        for col_name, col_type in bookmark_columns:
            try:
                if is_postgres:
                    init_db.execute(text(f"ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                else:
                    init_db.execute(text(f"ALTER TABLE bookmarks ADD COLUMN {col_name} {col_type};"))
                init_db.commit()
            except Exception as err:
                init_db.rollback()

        # 4. 'category' column on units
        try:
            if is_postgres:
                init_db.execute(text("ALTER TABLE units ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'General';"))
            else:
                init_db.execute(text("ALTER TABLE units ADD COLUMN category VARCHAR(100) DEFAULT 'General';"))
            init_db.commit()
        except Exception as err:
            init_db.rollback()

        # 5. 'course' column on units
        try:
            if is_postgres:
                init_db.execute(text("ALTER TABLE units ADD COLUMN IF NOT EXISTS course VARCHAR(100) DEFAULT 'General';"))
            else:
                init_db.execute(text("ALTER TABLE units ADD COLUMN course VARCHAR(100) DEFAULT 'General';"))
            init_db.commit()
        except Exception as err:
            init_db.rollback()

        # 6. 'unit_group' column on units
        try:
            if is_postgres:
                init_db.execute(text("ALTER TABLE units ADD COLUMN IF NOT EXISTS unit_group VARCHAR(100);"))
            else:
                init_db.execute(text("ALTER TABLE units ADD COLUMN unit_group VARCHAR(100);"))
            init_db.commit()
        except Exception as err:
            init_db.rollback()

        # 6b. 'learning_outcomes' column on units
        try:
            if is_postgres:
                init_db.execute(text("ALTER TABLE units ADD COLUMN IF NOT EXISTS learning_outcomes TEXT;"))
            else:
                init_db.execute(text("ALTER TABLE units ADD COLUMN learning_outcomes TEXT;"))
            init_db.commit()
        except Exception as err:
            init_db.rollback()

        # 7. 'system_releases' columns
        try:
            if is_postgres:
                init_db.execute(text("ALTER TABLE system_releases ADD COLUMN IF NOT EXISTS version_code INTEGER DEFAULT 1;"))
                init_db.execute(text("ALTER TABLE system_releases ADD COLUMN IF NOT EXISTS is_mandatory BOOLEAN DEFAULT FALSE;"))
                init_db.execute(text("ALTER TABLE system_releases ADD COLUMN IF NOT EXISTS min_supported_version_code INTEGER DEFAULT 1;"))
                init_db.execute(text("ALTER TABLE system_releases ADD COLUMN IF NOT EXISTS file_size VARCHAR(50) DEFAULT '14.8 MB';"))
            else:
                init_db.execute(text("ALTER TABLE system_releases ADD COLUMN version_code INTEGER DEFAULT 1;"))
                init_db.execute(text("ALTER TABLE system_releases ADD COLUMN is_mandatory BOOLEAN DEFAULT 0;"))
                init_db.execute(text("ALTER TABLE system_releases ADD COLUMN min_supported_version_code INTEGER DEFAULT 1;"))
                init_db.execute(text("ALTER TABLE system_releases ADD COLUMN file_size VARCHAR(50) DEFAULT '14.8 MB';"))
            init_db.commit()
        except Exception as err:
            init_db.rollback()

        # Seed initial release if table is empty
        try:
            existing_releases_count = init_db.query(models.SystemRelease).count()
            if existing_releases_count == 0:
                init_db.add(models.SystemRelease(
                    version="1.0.0",
                    version_code=1,
                    artifact_type="Trace Android APK",
                    download_url="https://github.com/Agent606/Edu-AI/releases/tag/v1.0.0",
                    release_notes="Initial production build of Trace Medical & Academic Engine.\n- Socratic clinical reasoning\n- Dynamic weekly study timetable\n- Active recall quiz interface",
                    is_current=True,
                    is_mandatory=False,
                    min_supported_version_code=1,
                    file_size="14.2 MB",
                    timestamp=time.time() - 86400 * 7
                ))
                init_db.commit()
        except Exception as err:
            init_db.rollback()

        logger.info("Database migrations: Self-healing schema validation complete.")

        admin_email = os.environ.get("ADMIN_EMAIL", "admin@trace.edu")
        existing_admin = init_db.query(models.User).filter(models.User.email == admin_email).first()
        if not existing_admin:
            admin_pwd = os.environ.get("ADMIN_PASSWORD", "admin123")
            super_user = models.User(
                username="SuperAdmin",
                email=admin_email,
                hashed_password=security.get_password_hash(admin_pwd),
                role="Admin",
                difficulty="Hard (Advanced)",
                ai_persona="Superuser",
                semester_status="Superuser Administrator"
            )
            init_db.add(super_user)
            init_db.commit()
            logger.info(f"Default Superuser created: {admin_email}")
except Exception as e:
    logger.warning(f"Initial schema migration or admin setup warning: {e}. Tables will initialize on request if needed.")

app = FastAPI(title="Trace Modular API", version="3.0.0")


@app.on_event("startup")
async def initialize_orbit_schema():
    try:
        await initialize_orbit_database()
        logger.info("Orbit database schema verified successfully.")
    except Exception as exc:
        logger.warning("Orbit database schema initialization deferred: %s", exc)

DEBATEHUB_INTERNAL_URL = os.getenv("DEBATEHUB_INTERNAL_URL", "http://127.0.0.1:3000")

@app.api_route(
    "/DebateHub",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    include_in_schema=False,
)
@app.api_route(
    "/DebateHub/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    include_in_schema=False,
)
async def debatehub_proxy(request: Request, path: str = ""):
    """Forward DebateHub traffic to its independent internal Express service."""
    target = f"{DEBATEHUB_INTERNAL_URL}/{path}" if path else f"{DEBATEHUB_INTERNAL_URL}/"
    if request.url.query:
        target = f"{target}?{request.url.query}"

    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            upstream = await client.request(
                request.method,
                target,
                headers=headers,
                content=body,
            )
        excluded = {"content-encoding", "content-length", "transfer-encoding", "connection"}
        response_headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.lower() not in excluded
        }
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
            media_type=upstream.headers.get("content-type"),
        )
    except httpx.HTTPError as exc:
        logger.warning("DebateHub proxy request failed for %s: %s", target, exc)
        return JSONResponse(
            status_code=503,
            content={
                "service": "DebateHub",
                "status": "unavailable",
                "detail": "The independent DebateHub service is not ready.",
            },
        )

class HFSpacePrefixMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            prefix = "/spaces/Agent606/Edu-AI"
            if path.startswith(prefix):
                scope["path"] = path[len(prefix):] or "/"
                if "raw_path" in scope:
                    raw_path = scope["raw_path"].decode("ascii", "ignore")
                    if raw_path.startswith(prefix):
                        scope["raw_path"] = raw_path[len(prefix):].encode("ascii")
        await self.app(scope, receive, send)

app.add_middleware(HFSpacePrefixMiddleware)

INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY", "64923e4d8f1a2c5b9e0f3d7a6c5b9eX0f3d7a6c5b9e0f3d7a")

# Global Security Middleware
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    # Paths that bypass API key (root, health, docs, web signup, admin, syllabus ingestion, public home, web app)
    path = request.url.path
    if (
        path in [
            "/", "/health", "/api/health", "/docs", "/openapi.json", "/favicon.ico",
            "/home", "/welcome", "/index.html",
            "/app", "/student", "/learn",
            "/orbit", "/DebateHub",
            "/login", "/signup", "/signup.html", "/Edu_AI/signup.html", "/Edu_AI/sign up.html",
            "/api/auth/login", "/api/auth/signup-form", "/api/report-bug",
            "/ingest", "/delete-unit", "/update-unit"
        ]
        or path.startswith("/app")
        or path.startswith("/assets")
        or path.startswith("/DebateHub/")
        or path.startswith("/admin")
        or path.startswith("/Edu_AI")
        or path.startswith("/delete-unit/")
        or path.startswith("/update-unit/")
        or path.startswith("/api/")
    ):
        return await call_next(request)

    x_api_key = request.headers.get("X-Internal-Api-Key")
    if x_api_key != INTERNAL_API_KEY:
        return JSONResponse(status_code=403, content={"detail": "Unauthorized: Invalid API Key"})

    return await call_next(request)


# Real-Time Request and Error Logger Middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        status_code = response.status_code
        log_msg = f"[BACKEND API] {request.method} {request.url.path} -> {status_code} ({process_time_ms}ms)"
        
        # Stream into OVERSEER live wiretap buffer
        admin.record_live_request(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=process_time_ms,
            ip=request.client.host if request.client else "local",
            user_agent=request.headers.get("user-agent", "")
        )

        if status_code >= 500:
            logger.error(log_msg)
            try:
                with Session(bind=engine) as db_log:
                    admin.notify_admin(
                        db=db_log,
                        category="BACKEND_ERROR",
                        title=f"HTTP 500: {request.method} {request.url.path}",
                        message=f"Request failed with status {status_code} after {process_time_ms}ms.",
                        level="error",
                        details=f"Path: {request.url.path}\nMethod: {request.method}\nClient: {request.client.host if request.client else 'unknown'}"
                    )
            except Exception:
                pass
        elif status_code >= 400:
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
        return response
    except Exception as exc:
        process_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"[BACKEND ERROR] {request.method} {request.url.path} -> 500 ({process_time_ms}ms): {exc}")
        
        admin.record_live_request(
            method=request.method,
            path=request.url.path,
            status_code=500,
            duration_ms=process_time_ms,
            ip=request.client.host if request.client else "local",
            user_agent=request.headers.get("user-agent", "")
        )

        try:
            with Session(bind=engine) as db_log:
                admin.notify_admin(
                    db=db_log,
                    category="BACKEND_ERROR",
                    title=f"Exception on {request.method} {request.url.path}",
                    message=str(exc),
                    level="critical",
                    details=f"Path: {request.url.path}\nMethod: {request.method}\nError: {str(exc)}"
                )
        except Exception:
            pass
        raise exc

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(admin.router)
app.include_router(auth.router, prefix="/api/auth")
app.include_router(users.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(teacher.router, prefix="/api")
app.include_router(parent.router, prefix="/api")
app.include_router(learning.router, prefix="/api")
app.include_router(orbit_api_router, prefix="/api/v1")

# ==============================================================================
# Web App Module (React Frontend Embedded Directly in FastAPI Backend)
# ==============================================================================
assets_dir = WEBAPP_DIST_DIR / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="webapp_assets")

@app.get("/app", response_class=HTMLResponse)
@app.get("/app/{full_path:path}", response_class=HTMLResponse)
@app.get("/student", response_class=HTMLResponse)
@app.get("/learn", response_class=HTMLResponse)
async def serve_webapp(request: Request, full_path: str = ""):
    """Hosts the complete interactive React Web Application 24/7 directly from the backend."""
    index_file = WEBAPP_DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse(
        """<!DOCTYPE html><html><head><title>Edu-AI Web App</title></head>
        <body style="background:#020617;color:#f8fafc;font-family:sans-serif;padding:60px;text-align:center;">
        <h2 style="font-size:24px;font-weight:bold;">Edu-AI Web App Module</h2>
        <p style="color:#94a3b8;margin-top:8px;">The web application is active. Return to <a href="/home" style="color:#818cf8;">Home</a>.</p>
        </body></html>"""
    )

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Trace FastAPI Backend",
        "hasGeminiKey": bool(os.environ.get("GEMINI_API_KEY"))
    }

# Public Homepage (Inspiring, Welcoming, Quotes of the Day, Architecture Tour)
@app.get("/home", response_class=HTMLResponse)
@app.get("/welcome", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def public_home_page(request: Request, db: Session = Depends(get_db)):
    total_users = db.query(models.User).count()
    db_name = "PostgreSQL" if "postgres" in str(engine.url) else "SQLite Vault"
    return templates.TemplateResponse(
        "public/home.html",
        {
            "request": request,
            "version": admin.BACKEND_VERSION,
            "total_users": total_users,
            "db_type": db_name
        }
    )

@app.get("/")
def root(request: Request, db: Session = Depends(get_db)):
    # Support Hugging Face container health and logs probing
    if request.query_params.get("logs") == "container":
        return JSONResponse({
            "status": "healthy",
            "service": "Trace FastAPI Backend",
            "container": "active",
            "timestamp": time.time()
        })

    # Default landing screen opens at Admin Login
    if admin.is_authenticated_admin(request, db):
        return RedirectResponse(url="/admin", status_code=302)

    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "version": admin.BACKEND_VERSION, "error": None}
    )

@app.get("/orbit", include_in_schema=False)
async def orbit_entrypoint():
    """Keep Orbit's public entrypoint distinct from Trace's admin home."""
    return RedirectResponse(url="/docs")

@app.post("/ingest", response_class=HTMLResponse)
async def handle_ingestion(
    request: Request,
    markdown: str = Form(...),
    field: Optional[str] = Form(None),
    course: Optional[str] = Form(None),
    unit: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    syllabus_data = ingestion_engine.parse_syllabus_markdown(markdown)
    ingestion_engine.save_syllabus_to_db(
        db, syllabus_data, owner_id=None,
        field=field, course=course, unit_group=unit
    )
    admin.notify_admin(
        db=db,
        category="SYSTEM_ALERT",
        title="Syllabus Ingested",
        message=f"Admin ingested syllabus: {syllabus_data.get('syllabus_title', 'General')}.",
        level="info"
    )
    return RedirectResponse(url="/admin/catalogue", status_code=303)

@app.post("/delete-unit/{unit_id}", response_class=HTMLResponse)
async def handle_delete_unit(request: Request, unit_id: int, db: Session = Depends(get_db)):
    ingestion_engine.delete_unit(db, unit_id)
    return RedirectResponse(url="/admin/catalogue", status_code=303)

@app.post("/update-unit/{unit_id}", response_class=HTMLResponse)
async def handle_update_unit(request: Request, unit_id: int, name: str = Form(...), db: Session = Depends(get_db)):
    ingestion_engine.update_unit(db, unit_id, name)
    return RedirectResponse(url="/admin/catalogue", status_code=303)

@app.post("/api/units/library/add/{unit_id}")
async def add_unit_to_user(unit_id: int, user_id: int, db: Session = Depends(get_db)):
    new_unit = ingestion_engine.clone_unit_to_user(db, unit_id, user_id)
    if new_unit:
        return {"status": "success", "unit_id": new_unit.id}
    return JSONResponse(status_code=404, content={"detail": "Unit not found"})

@app.get("/api/units/library")
async def get_library_units(db: Session = Depends(get_db)):
    units = ingestion_engine.get_global_units(db)
    return [{"id": u.id, "name": u.name, "category": u.category} for u in units]

# Public Signup routes (supporting direct /signup, /signup.html, /Edu_AI/signup.html, etc.)
@app.get("/signup", response_class=HTMLResponse)
@app.get("/signup.html", response_class=HTMLResponse)
@app.get("/Edu_AI/signup.html", response_class=HTMLResponse)
@app.get("/Edu_AI/sign up.html", response_class=HTMLResponse)
@app.get("/Edu_AI/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("public/signup.html", {"request": request})

@app.post("/signup", response_class=HTMLResponse)
@app.post("/signup.html", response_class=HTMLResponse)
@app.post("/Edu_AI/signup.html", response_class=HTMLResponse)
@app.post("/Edu_AI/sign up.html", response_class=HTMLResponse)
async def handle_browser_signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
):
    existing_user = db.query(models.User).filter((models.User.email == email) | (models.User.username == username)).first()
    if existing_user:
        return HTMLResponse(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head><meta charset="UTF-8"><title>Registration Error</title><script src="https://cdn.tailwindcss.com"></script></head>
            <body class="bg-slate-950 text-slate-100 flex items-center justify-center min-h-screen p-4">
                <div class="max-w-md w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 text-center shadow-2xl">
                    <div class="w-12 h-12 bg-rose-500/20 text-rose-400 rounded-xl flex items-center justify-center mx-auto text-xl font-bold mb-3">!</div>
                    <h2 class="text-xl font-bold text-white mb-2">Account Already Exists</h2>
                    <p class="text-slate-400 text-xs">An account with that username or email address is already registered.</p>
                    <a href="/signup" class="mt-6 inline-block bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold px-4 py-2.5 rounded-xl">&larr; Return to Sign Up</a>
                </div>
            </body>
            </html>
            """,
            status_code=400
        )

    new_user = models.User(
        username=username,
        email=email,
        hashed_password=security.get_password_hash(password),
        role=role,
    )
    db.add(new_user)
    db.commit()

    # Instant Superuser Alert: Every time a new user enters the system!
    admin.notify_admin(
        db=db,
        category="NEW_USER",
        title="New User Registration",
        message=f"User '{username}' registered as {role} ({email}).",
        level="info",
        details=f"Username: {username}\nRole: {role}\nEmail: {email}\nSource: Web Signup Portal ({request.client.host if request.client else 'remote'})"
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Account Created | Edu-AI</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-slate-950 text-slate-100 flex items-center justify-center min-h-screen p-4">
        <div class="max-w-md w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 text-center shadow-2xl">
            <div class="w-14 h-14 bg-emerald-500/20 text-emerald-400 rounded-2xl flex items-center justify-center mx-auto text-2xl font-black mb-4">
                ✓
            </div>
            <h1 class="text-2xl font-black text-white">Account Created Successfully!</h1>
            <p class="text-slate-300 text-sm mt-2">Welcome to Edu-AI, <strong class="text-indigo-400">{username}</strong> ({role}).</p>
            <p class="text-xs text-slate-500 mt-2">You can now return to the Edu-AI app and log in.</p>
            <div class="mt-6 pt-6 border-t border-slate-800 flex flex-col gap-2.5">
                <a href="/signup" class="text-xs text-indigo-400 hover:underline">Create another account</a>
                <a href="/admin/login" class="text-xs text-slate-500 hover:text-slate-400">Admin Login Portal &rarr;</a>
            </div>
        </div>
    </body>
    </html>
    """

# Helper to find user by ID (int) or Username (string)
def find_user(user_id_or_name: str, db: Session):
    user = None
    if str(user_id_or_name).isdigit():
        user = db.query(models.User).filter(models.User.id == int(user_id_or_name)).first()
    if not user:
        user = db.query(models.User).filter(models.User.username == str(user_id_or_name)).first()
    return user

@app.get("/api/user/{user_id}/bookmarks", response_model=List[schemas.BookmarkResponse])
def get_bookmarks(user_id: str, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return db.query(models.Bookmark).filter(models.Bookmark.owner_id == user.id).all()

@app.post("/api/user/{user_id}/bookmarks", response_model=schemas.BookmarkResponse)
def create_bookmark(user_id: str, bookmark: schemas.BookmarkCreate, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_bookmark = models.Bookmark(
        type=bookmark.type,
        title=bookmark.title,
        target=bookmark.target,
        context=bookmark.context,
        timestamp=bookmark.timestamp,
        owner_id=user.id
    )
    db.add(new_bookmark)
    db.commit()
    db.refresh(new_bookmark)
    return new_bookmark

@app.delete("/api/user/{user_id}/bookmarks/{bookmark_id}")
def delete_bookmark(user_id: str, bookmark_id: int, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    bk = db.query(models.Bookmark).filter(models.Bookmark.id == bookmark_id, models.Bookmark.owner_id == user.id).first()
    if not bk:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    db.delete(bk)
    db.commit()
    return {"status": "success", "message": "Bookmark deleted"}

@app.get("/api/user/{user_id}/sync")
def get_user_sync_data(user_id: str, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from app.sync import sync_manager
    return sync_manager.get_full_sync_data(db, user)

@app.post("/api/user/{user_id}/sync", response_model=schemas.SyncResponse)
def sync_user_data(user_id: str, payload: schemas.SyncRequest, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from app.sync import sync_manager
    return sync_manager.process_full_sync(db, user, payload)

# RESTful delete endpoints for units and users
@app.delete("/api/units/{unit_id}")
@app.post("/api/units/{unit_id}/delete")
async def delete_unit_api(unit_id: int, db: Session = Depends(get_db)):
    success = ingestion_engine.delete_unit(db, unit_id)
    if success:
        return {"status": "success", "message": f"Unit #{unit_id} successfully deleted"}
    return JSONResponse(status_code=404, content={"detail": "Unit not found"})

@app.delete("/api/users/{user_id}")
@app.post("/api/users/{user_id}/delete")
async def delete_user_api(user_id: str, db: Session = Depends(get_db)):
    user = find_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"status": "success", "message": f"User #{user_id} deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


 