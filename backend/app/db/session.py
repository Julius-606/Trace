
import os
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

logger = logging.getLogger("trace_db")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# Backend directory and modular data vault path
BACKEND_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOCAL_DB_FILE = DATA_DIR / "edu_ai_vault.db"
LOCAL_SQLITE_URL = f"sqlite:///{LOCAL_DB_FILE}"

# Trace owns this database. Look for TRACE_DATABASE_URL first, then DATABASE_URL, then fallback to local SQLite
raw_db_url = os.getenv("TRACE_DATABASE_URL") or os.getenv("DATABASE_URL")
if not raw_db_url or not raw_db_url.strip():
    logger.info(f"[DATABASE] No remote Neon database URL detected. Using modular local SQLite database at: {LOCAL_DB_FILE}")
    raw_db_url = LOCAL_SQLITE_URL
else:
    raw_db_url = raw_db_url.strip()

# Fix for Neon/Heroku: SQLAlchemy requires 'postgresql://' instead of 'postgres://'
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

engine_args = {}

if "postgresql" in raw_db_url:
    # Ensure proper SSL mode for Neon/Cloud PostgreSQL
    if "sslmode" not in raw_db_url:
        separator = "&" if "?" in raw_db_url else "?"
        raw_db_url += f"{separator}sslmode=require"

    engine_args["connect_args"] = {
        "connect_timeout": 5,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5
    }
    engine_args["pool_size"] = 5
    engine_args["max_overflow"] = 10
elif "sqlite" in raw_db_url:
    engine_args["connect_args"] = {"check_same_thread": False}

SQLALCHEMY_DATABASE_URL = raw_db_url

def create_configured_engine(url, args):
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=300,
        **args
    )

try:
    engine = create_configured_engine(SQLALCHEMY_DATABASE_URL, engine_args)
    # Test connection with a fast probe
    with engine.connect() as conn:
        pass
    logger.info(f"Database connection initialized successfully with {SQLALCHEMY_DATABASE_URL.split('@')[-1] if '@' in SQLALCHEMY_DATABASE_URL else 'local SQLite'}")
except Exception as e:
    logger.warning(f"Primary Neon connection absent or unreachable ({e}). Seamlessly engaging local SQLite database fallback at '{LOCAL_DB_FILE}'.")
    SQLALCHEMY_DATABASE_URL = LOCAL_SQLITE_URL
    engine = create_configured_engine(SQLALCHEMY_DATABASE_URL, {"connect_args": {"check_same_thread": False}})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


 