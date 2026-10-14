"""Async database session for Orbit's isolated database."""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass

try:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
except ImportError:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker as async_sessionmaker
from app.models.study import Base
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

raw_db_url = os.getenv("ORBIT_DATABASE_URL") or os.getenv("TRACE_DATABASE_URL", "sqlite:///./orbit_vault.db")
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

if raw_db_url.startswith("postgresql://"):
    asyncpg_url = raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    parsed = urlparse(asyncpg_url)
    query_params = parse_qs(parsed.query)

    # asyncpg does NOT accept 'sslmode' or 'channel_binding' as connect kwargs.
    # Determine SSL intent from query params or hostname (Neon requires SSL).
    ssl_mode = query_params.pop("sslmode", [None])[0]
    query_params.pop("channel_binding", None)

    asyncpg_connect_args = {"timeout": 10}
    is_cloud_db = ("neon.tech" in parsed.netloc) or ("aws" in parsed.netloc)
    if (ssl_mode and ssl_mode != "disable") or is_cloud_db or "ssl" in query_params:
        asyncpg_connect_args["ssl"] = "require"
    query_params.pop("ssl", None)

    # Rebuild URL without libpq-specific parameters
    clean_query = urlencode(query_params, doseq=True)
    clean_asyncpg_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        clean_query,
        parsed.fragment
    ))

    try:
        orbit_engine = create_async_engine(
            clean_asyncpg_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args=asyncpg_connect_args,
            pool_size=5,
            max_overflow=10,
        )
    except Exception:
        try:
            fallback_sqlite = "sqlite+aiosqlite:///./orbit_vault.db"
            orbit_engine = create_async_engine(fallback_sqlite, connect_args={"check_same_thread": False})
        except Exception:
            from sqlalchemy import create_engine
            from sqlalchemy.ext.asyncio import AsyncEngine
            sync_engine = create_engine("sqlite:///./orbit_vault.db", connect_args={"check_same_thread": False})
            orbit_engine = AsyncEngine(sync_engine)
else:
    try:
        if raw_db_url.startswith("sqlite:///"):
            raw_db_url = raw_db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        orbit_engine = create_async_engine(raw_db_url, connect_args={"check_same_thread": False})
    except Exception:
        from sqlalchemy import create_engine
        from sqlalchemy.ext.asyncio import AsyncEngine
        sync_engine = create_engine("sqlite:///./orbit_vault.db", connect_args={"check_same_thread": False})
        orbit_engine = AsyncEngine(sync_engine)

orbit_database_url = orbit_engine.url.render_as_string(hide_password=False)

OrbitSessionLocal = async_sessionmaker(
    bind=orbit_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_orbit_db():
    async with OrbitSessionLocal() as db:
        yield db


async def initialize_orbit_database() -> None:
    async with orbit_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
