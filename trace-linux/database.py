"""
TRACE Desktop (Linux Client) - SQLite Database Layer
FILE: trace-linux/database.py
VERSION: 1.1.0
ROLE: Manages the local SQLite database at ~/.local/share/trace/trace_local.db,
      enforcing offline caching of user credentials, backend syllabi, progress,
      and synchronization queues alongside the Neurons currency economy.
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
    Initializes all core schema tables required for offline-first operation:
    1. user_session: Stores active user profile & JWT token cached from backend.
    2. user_wallet: Stores local Neurons virtual currency balance.
    3. unlocked_units: Local registry of unlocked course units.
    4. unit_progress: Completion status (LOCKED / UNLOCKED / COMPLETED) & scores.
    5. cached_units: Units and syllabi cached from the central backend.
    6. sync_queue: Queued offline events (quiz results, unlocks) to sync to cloud.
    7. offline_ai_prompts: Staged local AI queries for synchronization.
    8. quiz_history: Assessment outcomes and performance tracking.
    9. study_tasks: Chronotype study plan and schedule tasks.
    10. bookmarks: Saved academic notes and references.
    """
    with transaction() as conn:
        cursor = conn.cursor()

        # 1. user_session table (Cached authentication state from backend)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_session (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                email TEXT,
                token TEXT,
                role TEXT DEFAULT 'Student',
                semester_status TEXT DEFAULT 'Year 4 - Academic Candidate',
                sensory_mode TEXT DEFAULT 'Visual',
                ai_persona TEXT DEFAULT 'Socratic Mentor',
                is_logged_in INTEGER NOT NULL DEFAULT 1,
                last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. user_wallet table (Single-row constraint where id = 1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_wallet (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                neurons_balance INTEGER NOT NULL DEFAULT 200,
                total_earned INTEGER NOT NULL DEFAULT 200,
                total_spent INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        cursor.execute("SELECT COUNT(*) AS cnt FROM user_wallet WHERE id = 1;")
        row = cursor.fetchone()
        if row["cnt"] == 0:
            cursor.execute("""
                INSERT INTO user_wallet (id, neurons_balance, total_earned, total_spent)
                VALUES (1, ?, ?, 0);
            """, (INITIAL_NEURONS_BALANCE, INITIAL_NEURONS_BALANCE))

        # 3. unlocked_units table (Tracks purchased course units)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unlocked_units (
                unit_id TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                unit_title TEXT,
                unlocked_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                neurons_spent INTEGER NOT NULL DEFAULT 20
            );
        """)

        # 4. unit_progress table (Tracks mastery & completion state)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unit_progress (
                unit_id TEXT PRIMARY KEY,
                course_id TEXT,
                score REAL DEFAULT 0.0,
                status TEXT NOT NULL CHECK(status IN ('LOCKED', 'UNLOCKED', 'COMPLETED')),
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 5. cached_units table (Locally mirrors units from central PostgreSQL backend)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cached_units (
                id INTEGER PRIMARY KEY,
                backend_unit_id INTEGER UNIQUE,
                name TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                course TEXT DEFAULT 'General',
                unit_group TEXT,
                price_t_coins INTEGER DEFAULT 20,
                is_active INTEGER DEFAULT 1,
                is_unlocked INTEGER DEFAULT 0,
                raw_json TEXT,
                last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 6. sync_queue table (Queues offline events to commit to remote backend)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,  -- 'QUIZ_RECORD', 'UNIT_UNLOCK', 'NOTE_SYNC'
                payload_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_synced INTEGER NOT NULL DEFAULT 0
            );
        """)

        # 7. offline_ai_prompts table (Staging for client-satellite synchronization)
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

        # 8. quiz_history table (Active recall assessment outcomes)
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

        # 9. study_tasks table (Desktop task manager)
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

        # 10. bookmarks table (Saved references and notes)
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
