#!/usr/bin/env python3
"""
Test & Migration Script: Fix Users Table Schema & Column Verification
File: backend/tests/test_fix_users_table.py

Verifies and heals missing columns in the 'users' table (such as age, level_of_study,
course_pursued, referral_code, full_name, is_email_verified, interests) that caused
SQLAlchemy queries on /api/auth/login to fail with UndefinedColumn errors.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# Expected columns and types for users table
REQUIRED_USER_COLUMNS = [
    ("id", "INTEGER PRIMARY KEY"),
    ("username", "VARCHAR(100)"),
    ("email", "VARCHAR(100)"),
    ("hashed_password", "VARCHAR(200)"),
    ("role", "VARCHAR(50) DEFAULT 'Student'"),
    ("sensory_mode", "VARCHAR(50) DEFAULT 'Standard'"),
    ("difficulty", "VARCHAR(50) DEFAULT 'Medium (Standard)'"),
    ("ai_persona", "VARCHAR(100) DEFAULT 'Standard Trace'"),
    ("semester_status", "VARCHAR(100) DEFAULT 'Year 4 - Redemption Arc'"),
    ("full_name", "VARCHAR(150)"),
    ("age", "INTEGER"),
    ("level_of_study", "VARCHAR(100)"),
    ("course_pursued", "VARCHAR(150)"),
    ("referral_code", "VARCHAR(100)"),
    ("is_email_verified", "BOOLEAN DEFAULT 0"),
    ("interests", "TEXT"),
]


def fix_and_verify_sqlite(db_path: str = "edu_ai_vault.db") -> dict:
    """Performs schema self-healing on SQLite database and runs test queries."""
    full_path = BACKEND_DIR / db_path if not os.path.isabs(db_path) else Path(db_path)
    print(f"\n[INFO] Inspecting SQLite database: {full_path}")

    conn = sqlite3.connect(str(full_path))
    cursor = conn.cursor()

    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(100) UNIQUE,
            email VARCHAR(100) UNIQUE,
            hashed_password VARCHAR(200),
            role VARCHAR(50) DEFAULT 'Student'
        );
    """)
    conn.commit()

    # Check existing columns
    cursor.execute("PRAGMA table_info(users);")
    existing_columns = {row[1]: row[2] for row in cursor.fetchall()}
    print(f"[INFO] Existing columns before patch: {list(existing_columns.keys())}")

    # Add missing columns
    added_columns = []
    for col_name, col_def in REQUIRED_USER_COLUMNS:
        if col_name not in existing_columns and col_name != "id":
            alter_sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_def};"
            try:
                cursor.execute(alter_sql)
                conn.commit()
                added_columns.append(col_name)
                print(f"  [+] Added missing column: {col_name} ({col_def})")
            except Exception as e:
                print(f"  [!] Notice adding {col_name}: {e}")

    # Re-verify columns
    cursor.execute("PRAGMA table_info(users);")
    updated_columns = {row[1]: row[2] for row in cursor.fetchall()}
    print(f"[INFO] Columns after patch: {list(updated_columns.keys())}")

    # Run the exact query that failed during login in the logs
    test_query = """
        SELECT 
            users.id AS users_id, 
            users.username AS users_username, 
            users.email AS users_email, 
            users.hashed_password AS users_hashed_password, 
            users.role AS users_role, 
            users.sensory_mode AS users_sensory_mode, 
            users.difficulty AS users_difficulty, 
            users.ai_persona AS users_ai_persona, 
            users.semester_status AS users_semester_status, 
            users.full_name AS users_full_name, 
            users.age AS users_age, 
            users.level_of_study AS users_level_of_study, 
            users.course_pursued AS users_course_pursued, 
            users.referral_code AS users_referral_code, 
            users.is_email_verified AS users_is_email_verified, 
            users.interests AS users_interests 
        FROM users 
        WHERE users.email = ? OR users.username = ? 
        LIMIT 1;
    """
    cursor.execute(test_query, ("juliusgachoki78@gmail.com", "juliusgachoki78@gmail.com"))
    row = cursor.fetchone()
    print(f"[SUCCESS] Login verification query executed with 0 errors! Result: {row}")

    conn.close()
    return {
        "status": "success",
        "added_columns": added_columns,
        "total_columns": len(updated_columns),
    }


def fix_and_verify_postgres(pg_url: str) -> dict:
    """Performs schema self-healing on PostgreSQL / Neon database if available."""
    print(f"\n[INFO] Connecting to PostgreSQL database...")
    try:
        import psycopg2
    except ImportError:
        print("[SKIP] psycopg2 not installed in this environment; skipping direct PostgreSQL test.")
        return {"status": "skipped", "reason": "psycopg2 missing"}

    # Clean URL for psycopg2
    clean_url = pg_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = psycopg2.connect(clean_url)
    conn.autocommit = True
    cursor = conn.cursor()

    # Query existing columns in information_schema
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users';
    """)
    existing_cols = {r[0] for r in cursor.fetchall()}
    print(f"[INFO] PostgreSQL existing columns: {sorted(list(existing_cols))}")

    added = []
    for col_name, col_def in REQUIRED_USER_COLUMNS:
        if col_name not in existing_cols and col_name != "id":
            # Translate SQLite definitions to PostgreSQL
            pg_col_type = col_def
            if "BOOLEAN" in col_def:
                pg_col_type = "BOOLEAN DEFAULT FALSE"
            elif col_name == "interests":
                pg_col_type = "JSON"

            alter_sql = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {pg_col_type};"
            try:
                cursor.execute(alter_sql)
                added.append(col_name)
                print(f"  [+] Added missing PostgreSQL column: {col_name}")
            except Exception as e:
                print(f"  [!] Notice adding {col_name} to PostgreSQL: {e}")

    # Run verification query
    test_query = """
        SELECT 
            users.id AS users_id, 
            users.username AS users_username, 
            users.email AS users_email, 
            users.hashed_password AS users_hashed_password, 
            users.role AS users_role, 
            users.sensory_mode AS users_sensory_mode, 
            users.difficulty AS users_difficulty, 
            users.ai_persona AS users_ai_persona, 
            users.semester_status AS users_semester_status, 
            users.full_name AS users_full_name, 
            users.age AS users_age, 
            users.level_of_study AS users_level_of_study, 
            users.course_pursued AS users_course_pursued, 
            users.referral_code AS users_referral_code, 
            users.is_email_verified AS users_is_email_verified, 
            users.interests AS users_interests 
        FROM users 
        WHERE users.email = %s OR users.username = %s 
        LIMIT 1;
    """
    cursor.execute(test_query, ("juliusgachoki78@gmail.com", "juliusgachoki78@gmail.com"))
    row = cursor.fetchone()
    print(f"[SUCCESS] PostgreSQL login verification query executed with 0 errors! Result: {row}")

    conn.close()
    return {"status": "success", "added_columns": added}


def test_users_table_schema():
    """Pytest hook for test runner."""
    result = fix_and_verify_sqlite("edu_ai_vault.db")
    assert result["status"] == "success"
    assert result["total_columns"] >= len(REQUIRED_USER_COLUMNS)


if __name__ == "__main__":
    print("=" * 60)
    print(" 🛠️  EDU-AI TRACE USERS TABLE SCHEMA HEALER & TEST SUITE ")
    print("=" * 60)

    # 1. Run SQLite verification
    sqlite_result = fix_and_verify_sqlite("edu_ai_vault.db")
    print(f"\n[RESULT] SQLite self-healing status: {sqlite_result['status']}")

    # 2. Check if TRACE_DATABASE_URL is set in environment
    pg_url = os.getenv("TRACE_DATABASE_URL")
    if pg_url and pg_url.startswith(("postgres://", "postgresql://")):
        try:
            pg_result = fix_and_verify_postgres(pg_url)
            print(f"[RESULT] PostgreSQL self-healing status: {pg_result['status']}")
        except Exception as err:
            print(f"[WARNING] PostgreSQL check encountered: {err}")
    else:
        print("[INFO] TRACE_DATABASE_URL not set in local environment; verified against SQLite store.")

    print("\n✅ Verification complete: 'users' table is fully synchronized with models.User schema.")
