"""
TRACE Desktop (Linux Client) - SQLite Database Layer
FILE: trace-linux/database.py
VERSION: 1.0.0
ROLE: Manages the local SQLite database at ~/.local/share/trace/trace_local.db,
      enforcing row factories, atomic schema initialization, and integrity constraints.
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Generator
from config import DATABASE_FILE, INITIAL_NEURONS_BALANCE

logger = logging.getLogger("TRACE_DB")


def get_db_connection() -> sqlite3.Connection:
    """
    Returns an active SQLite database connection configured with:
    - Row factory enabled (dict-like accessibility).
    - Foreign key constraints enabled.
    - Write-Ahead Logging (WAL) for high concurrency and speed on Linux.
    """
    conn = sqlite3.connect(DATABASE_FILE, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def transaction() -> Generator[sqlite3.Connection, None, None]:
    """
    Thread-safe context manager providing atomic transaction execution.
    Automatically commits on success or rolls back upon any exception.
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error(f"Transaction rolled back due to error: {exc}")
        raise
    finally:
        conn.close()


def init_database() -> None:
    """
    Initializes all core schema tables required for the TRACE desktop client:
    1. user_wallet: Stores user's virtual Neurons currency (single-row enforced id = 1).
    2. unlocked_units: Tracks unlocked/purchased units with timestamp and neurons spent.
    3. unit_progress: Tracks unit mastery, score, and status (LOCKED/UNLOCKED/COMPLETED).
    4. offline_ai_prompts: Staged local queries for synchronization with server.
    5. quiz_history: Detailed records of past active recall assessments.
    6. study_tasks: Chronotype study plan and daily tasks.
    """
    with transaction() as conn:
        cursor = conn.cursor()

        # 1. user_wallet table (Single-row constraint where id = 1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_wallet (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                neurons_balance INTEGER NOT NULL DEFAULT 200,
                total_earned INTEGER NOT NULL DEFAULT 200,
                total_spent INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Seed initial wallet balance if table is empty
        cursor.execute("SELECT COUNT(*) AS cnt FROM user_wallet WHERE id = 1;")
        row = cursor.fetchone()
        if row["cnt"] == 0:
            cursor.execute("""
                INSERT INTO user_wallet (id, neurons_balance, total_earned, total_spent)
                VALUES (1, ?, ?, 0);
            """, (INITIAL_NEURONS_BALANCE, INITIAL_NEURONS_BALANCE))

        # 2. unlocked_units table (Tracks purchased course units)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unlocked_units (
                unit_id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                unit_title TEXT,
                unlocked_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                neurons_spent INTEGER NOT NULL DEFAULT 20
            );
        """)

        # 3. unit_progress table (Tracks mastery & completion state)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unit_progress (
                unit_id TEXT PRIMARY KEY,
                course_id TEXT,
                score REAL DEFAULT 0.0,
                status TEXT NOT NULL CHECK(status IN ('LOCKED', 'UNLOCKED', 'COMPLETED')),
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 4. offline_ai_prompts table (Staging for client-satellite synchronization)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS offline_ai_prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_synced INTEGER NOT NULL DEFAULT 0,
                server_response TEXT
            );
        """)

        # 5. quiz_history table (Active recall assessment outcomes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unit_id TEXT NOT NULL,
                unit_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                neurons_awarded INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 6. study_tasks table (Desktop task manager)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT DEFAULT 'Core Curriculum',
                due_date TEXT,
                completed INTEGER NOT NULL DEFAULT 0,
                brain_rot_level TEXT DEFAULT 'MID',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 7. bookmarks table (Saved references and notes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                target TEXT,
                category TEXT DEFAULT 'general',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

    logger.info(f"TRACE database schema successfully initialized at {DATABASE_FILE}")
