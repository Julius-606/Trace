"""
TRACE Desktop (Linux Client) - Data Access & Repository Layer
FILE: trace-linux/repository.py
VERSION: 1.0.0
ROLE: Provides atomic operations for the Neurons virtual currency economy,
      unit unlocking engine, local progress tracking, and client-satellite sync.
"""

import time
import json
import logging
from typing import Tuple, List, Dict, Optional, Any
from database import get_db_connection, transaction
from config import DEFAULT_UNIT_PRICE_NEURONS, DEFAULT_BACKEND_URL

logger = logging.getLogger("TRACE_REPOSITORY")


class TraceRepository:
    """
    Data Access Layer implementing atomic SQLite transactions for desktop operations.
    """

    # ==========================================================================
    # 1. NEURONS CURRENCY & WALLET OPERATIONS
    # ==========================================================================

    @staticmethod
    def get_wallet_balance() -> int:
        """Retrieves the current Neurons balance for user profile id = 1."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT neurons_balance FROM user_wallet WHERE id = 1;")
            row = cursor.fetchone()
            if row:
                return int(row["neurons_balance"])
            return 0
        finally:
            conn.close()

    @staticmethod
    def add_neurons(amount: int) -> int:
        """
        Atomically credits Neurons to the user's wallet (e.g. from quiz rewards or top-ups).
        Returns the new total balance.
        """
        if amount <= 0:
            return TraceRepository.get_wallet_balance()

        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_wallet
                SET neurons_balance = neurons_balance + ?,
                    total_earned = total_earned + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1;
            """, (amount, amount))

            cursor.execute("SELECT neurons_balance FROM user_wallet WHERE id = 1;")
            row = cursor.fetchone()
            new_balance = int(row["neurons_balance"])

        logger.info(f"Credited {amount} Neurons. New balance: {new_balance}")
        return new_balance

    @staticmethod
    def unlock_unit(
        unit_id: str,
        course_id: str,
        cost: int = DEFAULT_UNIT_PRICE_NEURONS,
        unit_title: str = ""
    ) -> Tuple[bool, str]:
        """
        Executes an atomic transaction for the Neurons unlocking engine:
        1. Verifies if unit is already unlocked.
        2. Checks available Neurons balance against required cost.
        3. Atomically deducts cost from user_wallet.
        4. Inserts unit record into unlocked_units.
        5. Updates or creates unit_progress entry with status 'UNLOCKED'.

        Returns: (success: bool, message: str)
        """
        with transaction() as conn:
            cursor = conn.cursor()

            # Step 1: Check existing unlock
            cursor.execute("SELECT unit_id FROM unlocked_units WHERE unit_id = ?;", (unit_id,))
            if cursor.fetchone():
                return True, "Unit is already unlocked and ready to access."

            # Step 2: Check balance
            cursor.execute("SELECT neurons_balance FROM user_wallet WHERE id = 1;")
            wallet_row = cursor.fetchone()
            current_balance = int(wallet_row["neurons_balance"]) if wallet_row else 0

            if current_balance < cost:
                needed = cost - current_balance
                return False, f"Insufficient Neurons! You have {current_balance} N. Need {needed} more to unlock."

            # Step 3: Deduct balance atomically
            cursor.execute("""
                UPDATE user_wallet
                SET neurons_balance = neurons_balance - ?,
                    total_spent = total_spent + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1;
            """, (cost, cost))

            # Step 4: Register in unlocked_units
            cursor.execute("""
                INSERT INTO unlocked_units (unit_id, course_id, unit_title, neurons_spent)
                VALUES (?, ?, ?, ?);
            """, (unit_id, course_id, unit_title or unit_id, cost))

            # Step 5: Mark unit_progress as UNLOCKED
            cursor.execute("""
                INSERT INTO unit_progress (unit_id, course_id, score, status, last_accessed)
                VALUES (?, ?, 0.0, 'UNLOCKED', CURRENT_TIMESTAMP)
                ON CONFLICT(unit_id) DO UPDATE SET
                    status = 'UNLOCKED',
                    last_accessed = CURRENT_TIMESTAMP;
            """, (unit_id, course_id))

        logger.info(f"Successfully unlocked unit '{unit_id}' for {cost} Neurons.")
        return True, f"Unit successfully unlocked! Spent {cost} Neurons."

    @staticmethod
    def is_unit_unlocked(unit_id: str) -> bool:
        """Checks if a unit is currently unlocked in local SQLite."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT unit_id FROM unlocked_units WHERE unit_id = ?;", (unit_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    @staticmethod
    def get_all_unlocked_unit_ids() -> List[str]:
        """Returns a list of all unit_id strings unlocked on this desktop."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT unit_id FROM unlocked_units;")
            return [row["unit_id"] for row in cursor.fetchall()]
        finally:
            conn.close()

    # ==========================================================================
    # 2. UNIT PROGRESS & ACADEMIC MASTERY
    # ==========================================================================

    @staticmethod
    def get_unit_progress(unit_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves progress data (score, status, last_accessed) for a unit."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM unit_progress WHERE unit_id = ?;", (unit_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    @staticmethod
    def update_unit_progress(unit_id: str, status: str, score: float = 0.0, course_id: str = "") -> None:
        """Updates or inserts the progress record for a unit."""
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO unit_progress (unit_id, course_id, score, status, last_accessed)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(unit_id) DO UPDATE SET
                    score = MAX(score, excluded.score),
                    status = excluded.status,
                    last_accessed = CURRENT_TIMESTAMP;
            """, (unit_id, course_id, score, status))

    # ==========================================================================
    # 3. QUIZ & ASSESSMENT LOGGING
    # ==========================================================================

    @staticmethod
    def record_quiz_result(unit_id: str, unit_name: str, score: int, total: int) -> Dict[str, Any]:
        """
        Records an assessment score, marks unit progress, and awards bonus Neurons
        for high academic performance (>75%).
        """
        percentage = (score / total) * 100.0 if total > 0 else 0.0
        neurons_awarded = 0
        if percentage >= 90:
            neurons_awarded = 15
        elif percentage >= 75:
            neurons_awarded = 10

        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quiz_history (unit_id, unit_name, score, total, percentage, neurons_awarded)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (unit_id, unit_name, score, total, percentage, neurons_awarded))

            if percentage >= 70:
                cursor.execute("""
                    INSERT INTO unit_progress (unit_id, score, status, last_accessed)
                    VALUES (?, ?, 'COMPLETED', CURRENT_TIMESTAMP)
                    ON CONFLICT(unit_id) DO UPDATE SET
                        score = MAX(score, ?),
                        status = 'COMPLETED',
                        last_accessed = CURRENT_TIMESTAMP;
                """, (unit_id, percentage, percentage))

            if neurons_awarded > 0:
                cursor.execute("""
                    UPDATE user_wallet
                    SET neurons_balance = neurons_balance + ?,
                        total_earned = total_earned + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1;
                """, (neurons_awarded, neurons_awarded))

        return {
            "score": score,
            "total": total,
            "percentage": round(percentage, 1),
            "neurons_awarded": neurons_awarded
        }

    @staticmethod
    def get_recent_quizzes(limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent assessment runs."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM quiz_history
                ORDER BY id DESC LIMIT ?;
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # ==========================================================================
    # 4. OFFLINE PROMPT STAGING (CLIENT SATELLITE ENGINE)
    # ==========================================================================

    @staticmethod
    def stage_offline_prompt(prompt: str, context: str = "") -> int:
        """Stages an AI prompt locally when offline, for subsequent server sync."""
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO offline_ai_prompts (prompt, context, is_synced)
                VALUES (?, ?, 0);
            """, (prompt, context))
            return cursor.lastrowid

    @staticmethod
    def get_pending_prompts() -> List[Dict[str, Any]]:
        """Fetches all prompts waiting to be synced with the server."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM offline_ai_prompts WHERE is_synced = 0 ORDER BY id ASC;")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def mark_prompt_synced(prompt_id: int, server_response: str = "") -> None:
        """Marks a staged prompt as synchronized with server."""
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE offline_ai_prompts
                SET is_synced = 1, server_response = ?
                WHERE id = 1;
            """, (server_response,))

    # ==========================================================================
    # 5. STUDY TASKS & DESKTOP CHRONOTYPE PLANNER
    # ==========================================================================

    @staticmethod
    def get_study_tasks() -> List[Dict[str, Any]]:
        """Returns all study tasks."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM study_tasks ORDER BY completed ASC, id DESC;")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def add_study_task(title: str, subject: str = "General", due_date: str = "") -> int:
        """Adds a study task to the desktop schedule."""
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO study_tasks (title, subject, due_date)
                VALUES (?, ?, ?);
            """, (title, subject, due_date or "Today"))
            return cursor.lastrowid

    @staticmethod
    def toggle_task(task_id: int) -> bool:
        """Toggles completion status of a task."""
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT completed FROM study_tasks WHERE id = ?;", (task_id,))
            row = cursor.fetchone()
            if not row:
                return False
            new_val = 0 if row["completed"] else 1
            cursor.execute("UPDATE study_tasks SET completed = ? WHERE id = ?;", (new_val, task_id))
            return bool(new_val)
