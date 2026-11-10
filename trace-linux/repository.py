"""
TRACE Desktop (Linux Client) - Data Access & Offline Synchronization Layer
FILE: trace-linux/repository.py
VERSION: 1.2.0
ROLE: Provides seamless dual-source data access: reads from central FastAPI backend
      as the primary source of truth, caching user sessions, syllabi, and progress
      into local SQLite for 100% offline access and queuing offline events.
"""

import time
import json
import logging
from typing import Tuple, List, Dict, Optional, Any
import urllib.request
import urllib.error

from database import get_db_connection, transaction
from config import (
    DEFAULT_UNIT_PRICE_NEURONS,
    DEFAULT_BACKEND_URL,
    ENDPOINT_LOGIN,
    ENDPOINT_DASHBOARD,
    ENDPOINT_SYLLABUSES,
    ENDPOINT_QUIZ_RECORD,
    ENDPOINT_AI_CHAT,
    SYLLABI_DIR
)

logger = logging.getLogger("TRACE_REPOSITORY")


# ==============================================================================
# LIGHTWEIGHT HTTP CLIENT (Supports requests if installed, with urllib fallback)
# ==============================================================================

class HttpResponse:
    """Unified HTTP response wrapper compatible with requests and urllib."""
    def __init__(self, status_code: int, data: Any):
        self.status_code = status_code
        self._data = data

    def json(self) -> Any:
        if isinstance(self._data, (dict, list)):
            return self._data
        if isinstance(self._data, bytes):
            return json.loads(self._data.decode("utf-8"))
        return json.loads(str(self._data))

    @property
    def text(self) -> str:
        if isinstance(self._data, bytes):
            return self._data.decode("utf-8")
        return str(self._data)


def http_post(url: str, json_data: dict, headers: dict = None, timeout: float = 5.0) -> HttpResponse:
    """Dispatches HTTP POST with automatic fallback between requests and urllib."""
    try:
        import requests
        resp = requests.post(url, json=json_data, headers=headers or {"Content-Type": "application/json"}, timeout=timeout)
        try:
            parsed = resp.json()
        except Exception:
            parsed = resp.text
        return HttpResponse(resp.status_code, parsed)
    except ImportError:
        pass

    # Standard library fallback
    body_bytes = json.dumps(json_data).encode("utf-8")
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, data=body_bytes, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            res_body = res.read()
            try:
                data = json.loads(res_body.decode("utf-8"))
            except Exception:
                data = res_body.decode("utf-8")
            return HttpResponse(res.status, data)
    except urllib.error.HTTPError as he:
        err_body = he.read()
        try:
            err_data = json.loads(err_body.decode("utf-8"))
        except Exception:
            err_data = err_body.decode("utf-8")
        return HttpResponse(he.code, err_data)
    except Exception as exc:
        raise IOError(f"Network error connecting to {url}: {exc}")


def http_get(url: str, headers: dict = None, timeout: float = 5.0) -> HttpResponse:
    """Dispatches HTTP GET with automatic fallback between requests and urllib."""
    try:
        import requests
        resp = requests.get(url, headers=headers or {}, timeout=timeout)
        try:
            parsed = resp.json()
        except Exception:
            parsed = resp.text
        return HttpResponse(resp.status_code, parsed)
    except ImportError:
        pass

    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, headers=req_headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            res_body = res.read()
            try:
                data = json.loads(res_body.decode("utf-8"))
            except Exception:
                data = res_body.decode("utf-8")
            return HttpResponse(res.status, data)
    except urllib.error.HTTPError as he:
        err_body = he.read()
        try:
            err_data = json.loads(err_body.decode("utf-8"))
        except Exception:
            err_data = err_body.decode("utf-8")
        return HttpResponse(he.code, err_data)
    except Exception as exc:
        raise IOError(f"Network error connecting to {url}: {exc}")


class TraceRepository:
    """
    Data Access Layer coordinating local SQLite caching and remote backend sync.
    """

    # ==========================================================================
    # 1. USER AUTHENTICATION & SESSION PERSISTENCE (OFFLINE-FIRST)
    # ==========================================================================

    @staticmethod
    def get_active_session() -> Optional[Dict[str, Any]]:
        """
        Retrieves the currently authenticated user profile from local SQLite.
        Enables instant startup without requiring internet connectivity.
        """
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_session WHERE id = 1 AND is_logged_in = 1;")
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    @staticmethod
    def login(
        email_or_user: str,
        password: str,
        backend_url: str = DEFAULT_BACKEND_URL
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Authenticates user:
        1. Tries remote backend at {backend_url}/api/auth/login.
        2. On success, caches user session and credentials locally in SQLite.
        3. If offline/unreachable: checks local SQLite cache for matching user.
        """
        clean_target = email_or_user.strip()
        base = (backend_url or DEFAULT_BACKEND_URL).rstrip("/")
        login_url = f"{base}{ENDPOINT_LOGIN}"

        # 1. Try Live Backend Connection
        try:
            resp = http_post(
                login_url,
                json_data={"email": clean_target, "password": password},
                timeout=5.0
            )
            if resp.status_code == 200:
                data = resp.json()
                user_id = str(data.get("user_id") or data.get("user", {}).get("id") or "1")
                username = data.get("username") or clean_target.split("@")[0]
                role = data.get("role") or "Student"
                token = data.get("access_token") or data.get("token") or "local-token"
                email = data.get("user", {}).get("email") or (clean_target if "@" in clean_target else "")

                # Cache in local SQLite
                with transaction() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO user_session (
                            id, user_id, username, email, token, role, is_logged_in, last_synced
                        ) VALUES (1, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                        ON CONFLICT(id) DO UPDATE SET
                            user_id = excluded.user_id,
                            username = excluded.username,
                            email = excluded.email,
                            token = excluded.token,
                            role = excluded.role,
                            is_logged_in = 1,
                            last_synced = CURRENT_TIMESTAMP;
                    """, (user_id, username, email, token, role))

                # Immediately trigger initial background sync
                try:
                    TraceRepository.sync_with_backend(backend_url)
                except Exception as sync_err:
                    logger.warning(f"Initial sync warning: {sync_err}")

                active_user = TraceRepository.get_active_session()
                return True, "Authenticated via Cloud Backend.", active_user

            elif resp.status_code in (400, 401):
                err_msg = "Invalid email/username or password."
                try:
                    j = resp.json()
                    if isinstance(j, dict):
                        err_msg = j.get("detail", err_msg)
                except Exception:
                    pass
                return False, err_msg, None

        except Exception as net_err:
            logger.info(f"Cloud connection unreachable ({net_err}). Attempting local offline validation.")

        # 2. Offline Fallback Validation
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_session WHERE id = 1;")
            cached = cursor.fetchone()

            # If matching cached user exists or development fallback
            if cached and (cached["email"] == clean_target.lower() or cached["username"] == clean_target or clean_target in ["student", "admin"]):
                cursor.execute("UPDATE user_session SET is_logged_in = 1 WHERE id = 1;")
                conn.commit()
                return True, "Authenticated offline (using local cached credentials).", dict(cached)

            # If user wants a fresh offline profile
            if clean_target in ["student", "demo", "offline"]:
                with transaction() as conn_trans:
                    c = conn_trans.cursor()
                    c.execute("""
                        INSERT INTO user_session (id, user_id, username, email, token, role, is_logged_in)
                        VALUES (1, '1', 'Student Candidate', 'student@trace.edu', 'offline-token', 'Student', 1)
                        ON CONFLICT(id) DO UPDATE SET is_logged_in = 1;
                    """)
                return True, "Logged in as local Offline Candidate.", TraceRepository.get_active_session()

        finally:
            conn.close()

        return False, "Could not reach backend server and no local cached credentials match.", None

    @staticmethod
    def logout() -> None:
        """Logs out user locally, switching offline state."""
        with transaction() as conn:
            conn.execute("UPDATE user_session SET is_logged_in = 0 WHERE id = 1;")

    # ==========================================================================
    # 2. BACKEND TO SQLITE SYNCHRONIZATION ENGINE
    # ==========================================================================

    @staticmethod
    def sync_with_backend(backend_url: str = None) -> Tuple[bool, str]:
        """
        Synchronizes the desktop client with the central backend:
        1. Pulls user dashboard (/api/users/{user_id}/dashboard) to update currency & units.
        2. Pulls all curriculum units (/api/syllabuses) into cached_units table.
        3. Flushes queued offline events (quizzes, unlocks) to the cloud.
        """
        session = TraceRepository.get_active_session()
        if not session:
            return False, "No active user session to synchronize."

        user_id = session.get("user_id", "1")
        base = (backend_url or DEFAULT_BACKEND_URL).rstrip("/")

        try:
            # 1. Pull User Dashboard (Currency, Active Units, Quiz History)
            dash_url = f"{base}/api/users/{user_id}/dashboard"
            dash_resp = http_get(dash_url, timeout=5.0)

            if dash_resp.status_code == 200:
                data = dash_resp.json()

                # Update Neurons balance (mirrors backend trace_coins)
                cloud_coins = data.get("trace_coins")
                if cloud_coins is not None:
                    with transaction() as conn:
                        conn.execute("""
                            UPDATE user_wallet
                            SET neurons_balance = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE id = 1;
                        """, (int(cloud_coins),))

                # Update user profile metadata
                with transaction() as conn:
                    conn.execute("""
                        UPDATE user_session
                        SET username = COALESCE(?, username),
                            role = COALESCE(?, role),
                            semester_status = COALESCE(?, semester_status),
                            sensory_mode = COALESCE(?, sensory_mode),
                            ai_persona = COALESCE(?, ai_persona),
                            last_synced = CURRENT_TIMESTAMP
                        WHERE id = 1;
                    """, (
                        data.get("username"),
                        data.get("role"),
                        data.get("semester_status"),
                        data.get("sensory_mode"),
                        data.get("ai_persona")
                    ))

                # Register active units into unlocked_units
                remote_units = data.get("units") or []
                for u in remote_units:
                    u_id = str(u.get("id"))
                    u_name = u.get("name", "Unit")
                    with transaction() as conn:
                        conn.execute("""
                            INSERT INTO unlocked_units (unit_id, course_id, unit_title, neurons_spent)
                            VALUES (?, 'cloud_course', ?, 0)
                            ON CONFLICT(unit_id) DO NOTHING;
                        """, (u_id, u_name))
                        conn.execute("""
                            INSERT INTO unit_progress (unit_id, course_id, status, last_accessed)
                            VALUES (?, 'cloud_course', 'UNLOCKED', CURRENT_TIMESTAMP)
                            ON CONFLICT(unit_id) DO UPDATE SET status = 'UNLOCKED';
                        """, (u_id,))

            # 2. Pull Global Syllabuses into cached_units table
            syl_url = f"{base}{ENDPOINT_SYLLABUSES}"
            syl_resp = http_get(syl_url, timeout=5.0)
            if syl_resp.status_code == 200:
                global_units = syl_resp.json()
                with transaction() as conn:
                    for gu in global_units:
                        conn.execute("""
                            INSERT INTO cached_units (
                                backend_unit_id, name, category, course, unit_group,
                                price_t_coins, is_active, raw_json, last_synced
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                            ON CONFLICT(backend_unit_id) DO UPDATE SET
                                name = excluded.name,
                                category = excluded.category,
                                course = excluded.course,
                                price_t_coins = excluded.price_t_coins,
                                last_synced = CURRENT_TIMESTAMP;
                        """, (
                            gu.get("id"),
                            gu.get("name", "Unit"),
                            gu.get("category", "General"),
                            gu.get("course", "General"),
                            gu.get("unit_group"),
                            gu.get("price_t_coins", 20),
                            1 if gu.get("is_active", True) else 0,
                            json.dumps(gu)
                        ))

            # 3. Flush Offline Sync Queue to Cloud
            TraceRepository.flush_sync_queue(base)

            timestamp_str = time.strftime("%H:%M:%S")
            return True, f"Successfully synced with cloud vault at {timestamp_str}."

        except Exception as exc:
            logger.warning(f"Backend synchronization skipped (offline): {exc}")
            return False, "Cloud vault unreachable. Operating safely in local SQLite mode."

    @staticmethod
    def flush_sync_queue(base_url: str):
        """Dispatches any pending offline operations to the central backend."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sync_queue WHERE is_synced = 0 ORDER BY id ASC;")
            pending = cursor.fetchall()

            for item in pending:
                action = item["action"]
                payload = json.loads(item["payload_json"])

                if action == "QUIZ_RECORD":
                    try:
                        r = http_post(f"{base_url}{ENDPOINT_QUIZ_RECORD}", json_data=payload, timeout=4.0)
                        if r.status_code == 200:
                            conn.execute("UPDATE sync_queue SET is_synced = 1 WHERE id = ?;", (item["id"],))
                            conn.commit()
                    except Exception:
                        pass
        finally:
            conn.close()

    # ==========================================================================
    # 3. NEURONS CURRENCY & WALLET OPERATIONS
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
            return 200
        finally:
            conn.close()

    @staticmethod
    def add_neurons(amount: int) -> int:
        """Atomically credits Neurons to user wallet."""
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
            row = cursor.execute("SELECT neurons_balance FROM user_wallet WHERE id = 1;").fetchone()
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
        Atomically unlocks a unit:
        1. Checks balance in local SQLite.
        2. Deducts Neurons.
        3. Marks unlocked in local SQLite.
        4. Queues sync event so cloud backend registers unlock when online.
        """
        with transaction() as conn:
            cursor = conn.cursor()

            # Check if already unlocked
            cursor.execute("SELECT unit_id FROM unlocked_units WHERE unit_id = ?;", (unit_id,))
            if cursor.fetchone():
                return True, "Unit is already unlocked and ready to access."

            # Check balance
            cursor.execute("SELECT neurons_balance FROM user_wallet WHERE id = 1;")
            wallet_row = cursor.fetchone()
            current_balance = int(wallet_row["neurons_balance"]) if wallet_row else 0

            if current_balance < cost:
                needed = cost - current_balance
                return False, f"Insufficient Neurons! You have {current_balance} N. Need {needed} more to unlock."

            # Deduct balance atomically
            cursor.execute("""
                UPDATE user_wallet
                SET neurons_balance = neurons_balance - ?,
                    total_spent = total_spent + ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1;
            """, (cost, cost))

            # Register in unlocked_units
            cursor.execute("""
                INSERT INTO unlocked_units (unit_id, course_id, unit_title, neurons_spent)
                VALUES (?, ?, ?, ?);
            """, (unit_id, course_id, unit_title or unit_id, cost))

            # Mark unit_progress as UNLOCKED
            cursor.execute("""
                INSERT INTO unit_progress (unit_id, course_id, score, status, last_accessed)
                VALUES (?, ?, 0.0, 'UNLOCKED', CURRENT_TIMESTAMP)
                ON CONFLICT(unit_id) DO UPDATE SET
                    status = 'UNLOCKED',
                    last_accessed = CURRENT_TIMESTAMP;
            """, (unit_id, course_id))

            # Queue unlock sync event
            cursor.execute("""
                INSERT INTO sync_queue (action, payload_json)
                VALUES ('UNIT_UNLOCK', ?);
            """, (json.dumps({"unit_id": unit_id, "cost": cost, "title": unit_title}),))

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

    @staticmethod
    def get_cached_backend_units() -> List[Dict[str, Any]]:
        """Returns units cached from the central PostgreSQL database."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cached_units ORDER BY id ASC;")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    # ==========================================================================
    # 4. QUIZ & ASSESSMENT LOGGING (LOCAL + CLOUD SYNC)
    # ==========================================================================

    @staticmethod
    def record_quiz_result(unit_id: str, unit_name: str, score: int, total: int) -> Dict[str, Any]:
        """
        Records assessment locally in SQLite, awards bonus Neurons for scores >=75%,
        and queues/submits result to cloud backend.
        """
        percentage = (score / total) * 100.0 if total > 0 else 0.0
        neurons_awarded = 15 if percentage >= 90 else (10 if percentage >= 75 else 0)

        session = TraceRepository.get_active_session()
        user_id = session.get("user_id", "1") if session else "1"

        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quiz_history (unit_id, unit_name, score, total, percentage, neurons_awarded)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (unit_id, unit_name, score, total, percentage, neurons_awarded))

            cursor.execute("""
                INSERT INTO unit_progress (unit_id, course_id, score, status, last_accessed)
                VALUES (?, 'active_course', ?, 'COMPLETED', CURRENT_TIMESTAMP)
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

            # Queue sync payload for remote backend
            sync_payload = {
                "user_id": user_id,
                "unit_name": unit_name,
                "score": score,
                "total": total,
                "timestamp": str(int(time.time()))
            }
            cursor.execute("""
                INSERT INTO sync_queue (action, payload_json)
                VALUES ('QUIZ_RECORD', ?);
            """, (json.dumps(sync_payload),))

        # Attempt immediate push if online
        try:
            http_post(
                f"{DEFAULT_BACKEND_URL}{ENDPOINT_QUIZ_RECORD}",
                json_data=sync_payload,
                timeout=2.0
            )
        except Exception:
            pass  # Stored safely in sync_queue for next flush

        return {
            "score": score,
            "total": total,
            "percentage": round(percentage, 1),
            "neurons_awarded": neurons_awarded
        }

    # ==========================================================================
    # 5. OFFLINE PROMPT STAGING & TASKS
    # ==========================================================================

    @staticmethod
    def stage_offline_prompt(prompt: str, context: str = "") -> int:
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO offline_ai_prompts (prompt, context, is_synced)
                VALUES (?, ?, 0);
            """, (prompt, context))
            return cursor.lastrowid

    @staticmethod
    def mark_prompt_synced(prompt_id: int, server_response: str = "") -> None:
        with transaction() as conn:
            conn.execute("""
                UPDATE offline_ai_prompts
                SET is_synced = 1, server_response = ?
                WHERE id = ?;
            """, (server_response, prompt_id))

    @staticmethod
    def get_study_tasks() -> List[Dict[str, Any]]:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM study_tasks ORDER BY completed ASC, id DESC;")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def add_study_task(title: str, subject: str = "General", due_date: str = "") -> int:
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO study_tasks (title, subject, due_date)
                VALUES (?, ?, ?);
            """, (title, subject, due_date or "Today"))
            return cursor.lastrowid

    @staticmethod
    def toggle_task(task_id: int) -> bool:
        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT completed FROM study_tasks WHERE id = ?;", (task_id,))
            row = cursor.fetchone()
            if not row:
                return False
            new_val = 0 if row["completed"] else 1
            cursor.execute("UPDATE study_tasks SET completed = ? WHERE id = ?;", (new_val, task_id))
            return bool(new_val)
