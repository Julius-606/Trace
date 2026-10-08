"""Async database session for Orbit's isolated database."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.study import Base

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

raw_db_url = os.getenv("ORBIT_DATABASE_URL", "sqlite:///./orbit_vault.db")
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

if raw_db_url.startswith("postgresql://"):
    orbit_database_url = raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "sslmode" not in orbit_database_url:
        separator = "&" if "?" in orbit_database_url else "?"
        orbit_database_url += f"{separator}sslmode=require"
    orbit_engine = create_async_engine(
        orbit_database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"timeout": 10},
        pool_size=5,
        max_overflow=10,
    )
else:
    if raw_db_url.startswith("sqlite:///"):
        raw_db_url = raw_db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    orbit_engine = create_async_engine(raw_db_url, connect_args={"check_same_thread": False})

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
