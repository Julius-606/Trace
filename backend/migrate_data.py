
# IDENTITY: backend/migrate_data.py
# ⚙️ GEAR: Data Migration (SQLite -> PostgreSQL)

import sqlite3
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
SQLITE_DB_PATH = "edu_ai_vault.db"
POSTGRES_URL = os.getenv("TRACE_DATABASE_URL")

if not POSTGRES_URL:
    print("❌ Error: TRACE_DATABASE_URL not found in .env file.")
    exit(1)

# Fix for Neon/Heroku: SQLAlchemy requires 'postgresql://' instead of 'postgres://'
if POSTGRES_URL.startswith("postgres://"):
    POSTGRES_URL = POSTGRES_URL.replace("postgres://", "postgresql://", 1)

def migrate():
    print(f"🚀 Starting migration from {SQLITE_DB_PATH} to Neon PostgreSQL...")

    # Connect to SQLite
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"❌ Error: SQLite file {SQLITE_DB_PATH} not found.")
        return

    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_engine = create_engine(POSTGRES_URL)
    PgSession = sessionmaker(bind=pg_engine)
    pg_session = PgSession()

    try:
        # 1. Migrate Users
        print("👤 Migrating Users...")
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        for row in users:
            # We use raw SQL to ensure IDs are preserved
            pg_session.execute(
                text("INSERT INTO users (id, username, role, sensory_mode, difficulty, ai_persona, semester_status, interests) "
                     "VALUES (:id, :username, :role, :sensory_mode, :difficulty, :ai_persona, :semester_status, :interests) "
                     "ON CONFLICT (id) DO NOTHING"),
                dict(row)
            )

        # 2. Migrate Units
        print("📚 Migrating Units...")
        sqlite_cursor.execute("SELECT * FROM units")
        units = sqlite_cursor.fetchall()
        for row in units:
            pg_session.execute(
                text("INSERT INTO units (id, name, is_active, category, owner_id) "
                     "VALUES (:id, :name, :is_active, :category, :owner_id) "
                     "ON CONFLICT (id) DO NOTHING"),
                dict(row)
            )

        # New: Migrate Modules
        print("📦 Migrating Modules...")
        try:
            sqlite_cursor.execute("SELECT * FROM modules")
            modules = sqlite_cursor.fetchall()
            for row in modules:
                pg_session.execute(
                    text("INSERT INTO modules (id, name, unit_id) "
                         "VALUES (:id, :name, :unit_id) "
                         "ON CONFLICT (id) DO NOTHING"),
                    dict(row)
                )
        except Exception as e:
            print(f"⚠️ Could not migrate modules: {e}")

        # New: Migrate Subtopics
        print("📍 Migrating Subtopics...")
        try:
            sqlite_cursor.execute("SELECT * FROM subtopics")
            subtopics = sqlite_cursor.fetchall()
            for row in subtopics:
                pg_session.execute(
                    text("INSERT INTO subtopics (id, name, is_completed, module_id) "
                         "VALUES (:id, :name, :is_completed, :module_id) "
                         "ON CONFLICT (id) DO NOTHING"),
                    dict(row)
                )
        except Exception as e:
            print(f"⚠️ Could not migrate subtopics: {e}")

        # 3. Migrate Quiz History
        print("📊 Migrating Quiz History...")
        sqlite_cursor.execute("SELECT * FROM quiz_history")
        quizzes = sqlite_cursor.fetchall()
        for row in quizzes:
            pg_session.execute(
                text("INSERT INTO quiz_history (id, unit_name, score, total, pnl, timestamp, owner_id) "
                     "VALUES (:id, :unit_name, :score, :total, :pnl, :timestamp, :owner_id) "
                     "ON CONFLICT (id) DO NOTHING"),
                dict(row)
            )

        # 4. Migrate Chat Messages
        print("💬 Migrating Chat Messages...")
        sqlite_cursor.execute("SELECT * FROM chat_messages")
        chats = sqlite_cursor.fetchall()
        for row in chats:
            pg_session.execute(
                text("INSERT INTO chat_messages (id, role, content, timestamp, owner_id) "
                     "VALUES (:id, :role, :content, :timestamp, :owner_id) "
                     "ON CONFLICT (id) DO NOTHING"),
                dict(row)
            )

        pg_session.commit()
        print("✅ Migration successful! All records synced to Neon.")

        # Update sequences in Postgres (Important for ID generation)
        print("🔄 Updating ID sequences...")
        tables = ["users", "units", "modules", "subtopics", "quiz_history", "chat_messages"]
        for table in tables:
            try:
                pg_session.execute(text(f"SELECT setval('{table}_id_seq', (SELECT MAX(id) FROM {table}))"))
            except Exception as e:
                print(f"⚠️ Could not update sequence for {table}: {e}")
        pg_session.commit()

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        pg_session.rollback()
    finally:
        sqlite_conn.close()
        pg_session.close()

if __name__ == "__main__":
    migrate()


 