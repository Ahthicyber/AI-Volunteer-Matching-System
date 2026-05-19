"""
auth/auth_service.py
─────────────────────
Authentication service for the Volunteer Matching System.

Provides password hashing, user creation, and login verification.
No ORM — raw SQLite only.

Public API
----------
    hash_password(password)               → str
    verify_password(password, hash)       → bool
    create_user(email, password, role)    → (bool, str)
    authenticate_user(email, password)    → (bool, dict | str)
    get_user_by_email(email)              → dict | None
"""

import sqlite3
import logging
import secrets
from datetime import datetime, timedelta
from passlib.context import CryptContext

from db.database import get_connection

logger = logging.getLogger(__name__)

# ── Passlib bcrypt context ────────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

VALID_ROLES = {"volunteer", "ngo", "admin"}
MIN_PASSWORD_LEN = 6

DEMO_ACCOUNTS = {
    "admin@volmatch.local": ("Admin@123", "admin"),
    "volunteer@volmatch.local": ("Volunteer@123", "volunteer"),
    "ngo@volmatch.local": ("Ngo@123", "ngo"),
}


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return True if *password* matches *password_hash*."""
    try:
        return _pwd_context.verify(password, password_hash)
    except Exception:
        return False


# ── User queries ──────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> dict | None:
    """
    Return a user row as a plain dict, or None if not found.

    Keys: id, email, password_hash, role, created_at
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, password_hash, role, created_at "
            "FROM Users WHERE email = ?",
            (email.strip().lower(),),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)
    except sqlite3.Error as exc:
        logger.error("get_user_by_email error: %s", exc)
        return None
    finally:
        conn.close()



def get_user_by_id(user_id: int) -> dict | None:
    """Return a safe user dict by id, or None if not found."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, email, role, created_at FROM Users WHERE id = ?",
            (int(user_id),),
        ).fetchone()
        return dict(row) if row else None
    except Exception as exc:
        logger.error("get_user_by_id error: %s", exc)
        return None
    finally:
        conn.close()


def ensure_demo_accounts() -> None:
    """
    Ensure seeded demo accounts exist with the correct roles and passwords.

    This is intentionally safe to call during startup and before login. It
    repairs old demo password hashes without duplicating accounts, which fixes
    invalid-demo-login issues after project ZIP updates.
    """
    conn = get_connection()
    try:
        for email, (password, role) in DEMO_ACCOUNTS.items():
            row = conn.execute(
                "SELECT id, password_hash, role FROM Users WHERE email = ?",
                (email,),
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO Users (email, password_hash, role) VALUES (?, ?, ?)",
                    (email, hash_password(password), role),
                )
                continue

            needs_update = row["role"] != role or not verify_password(password, row["password_hash"])
            if needs_update:
                # Avoid depending on optional columns in older databases.
                cols = {r["name"] for r in conn.execute("PRAGMA table_info(Users)").fetchall()}
                if "updated_at" in cols:
                    conn.execute(
                        "UPDATE Users SET password_hash = ?, role = ?, updated_at = datetime('now') WHERE id = ?",
                        (hash_password(password), role, row["id"]),
                    )
                else:
                    conn.execute(
                        "UPDATE Users SET password_hash = ?, role = ? WHERE id = ?",
                        (hash_password(password), role, row["id"]),
                    )
        conn.commit()
    except sqlite3.Error as exc:
        logger.error("ensure_demo_accounts error: %s", exc)
    finally:
        conn.close()


def _repair_demo_login_if_valid(email: str, password: str) -> dict | None:
    """
    If a canonical demo credential is entered but the stored hash is stale,
    repair demo accounts and return the matching user. This keeps demos reliable
    even when an old SQLite database is reused.
    """
    demo = DEMO_ACCOUNTS.get(email)
    if not demo:
        return None
    expected_password, expected_role = demo
    if password != expected_password:
        return None

    ensure_demo_accounts()
    user = get_user_by_email(email)
    if user and user.get("role") == expected_role and verify_password(password, user["password_hash"]):
        return {"id": user["id"], "email": user["email"], "role": user["role"]}
    return None



# ── Persistent login session helpers ─────────────────────────────────────────

def create_login_session(user_id: int, days_valid: int = 7) -> str | None:
    """Create and persist a random login session token for the given user."""
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(days=days_valid)).strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO Sessions (user_id, session_token, expires_at, is_active)
            VALUES (?, ?, ?, 1)
            """,
            (int(user_id), token, expires_at),
        )
        conn.commit()
        return token
    except sqlite3.Error as exc:
        logger.error("create_login_session error: %s", exc)
        return None
    finally:
        conn.close()


def validate_login_session(session_token: str | None) -> dict | None:
    """Validate a session token and return the associated safe user dict."""
    if not session_token:
        return None
    token = str(session_token).strip()
    if not token:
        return None

    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT s.id AS session_id, s.user_id, s.expires_at,
                   u.email, u.role
            FROM Sessions s
            JOIN Users u ON u.id = s.user_id
            WHERE s.session_token = ? AND s.is_active = 1
            """,
            (token,),
        ).fetchone()
        if row is None:
            return None

        expires_at = row["expires_at"]
        if expires_at:
            try:
                if datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S") < datetime.utcnow():
                    conn.execute("UPDATE Sessions SET is_active = 0 WHERE id = ?", (row["session_id"],))
                    conn.commit()
                    return None
            except ValueError:
                return None

        return {"id": row["user_id"], "email": row["email"], "role": row["role"]}
    except sqlite3.Error as exc:
        logger.error("validate_login_session error: %s", exc)
        return None
    finally:
        conn.close()


def deactivate_login_session(session_token: str | None) -> None:
    """Deactivate a persisted session token, if present."""
    if not session_token:
        return
    conn = get_connection()
    try:
        conn.execute("UPDATE Sessions SET is_active = 0 WHERE session_token = ?", (str(session_token),))
        conn.commit()
    except sqlite3.Error as exc:
        logger.error("deactivate_login_session error: %s", exc)
    finally:
        conn.close()



# Compatibility aliases requested by the session persistence phase.
def create_session_token(user_id: int) -> str | None:
    return create_login_session(user_id)

def validate_session_token(token: str | None) -> dict | None:
    return validate_login_session(token)

def deactivate_session_token(token: str | None) -> None:
    deactivate_login_session(token)

# ── Registration ──────────────────────────────────────────────────────────────

def create_user(email: str, password: str, role: str) -> tuple[bool, str]:
    """
    Register a new user.

    Returns
    -------
    (True, "")          on success
    (False, reason)     on validation failure or DB error
    """
    # --- Input validation ---
    email = email.strip().lower()
    role  = role.strip().lower()

    if not email:
        return False, "Email address is required."

    if "@" not in email or "." not in email.split("@")[-1]:
        return False, "Please enter a valid email address."

    if len(password) < MIN_PASSWORD_LEN:
        return False, f"Password must be at least {MIN_PASSWORD_LEN} characters."

    if role not in VALID_ROLES:
        return False, f"Invalid role '{role}'."

    # Prevent UI registration as admin
    if role == "admin":
        return False, "Admin accounts cannot be created through the registration form."

    # --- Duplicate check ---
    if get_user_by_email(email) is not None:
        return False, "An account with this email already exists."

    # --- Insert ---
    password_hash = hash_password(password)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO Users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, password_hash, role),
        )
        conn.commit()
        logger.info("User created: %s (%s)", email, role)
        return True, ""
    except sqlite3.IntegrityError:
        # Race-condition duplicate
        return False, "An account with this email already exists."
    except sqlite3.Error as exc:
        logger.error("create_user error: %s", exc)
        return False, "A database error occurred. Please try again."
    finally:
        conn.close()


# ── Login ─────────────────────────────────────────────────────────────────────

def authenticate_user(email: str, password: str) -> tuple[bool, dict | str]:
    """
    Verify credentials.

    Returns
    -------
    (True,  user_dict)   on success  — dict has keys: id, email, role
    (False, reason_str)  on failure
    """
    email = email.strip().lower()

    if not email or not password:
        return False, "Email and password are required."

    user = get_user_by_email(email)
    if user is None:
        repaired_demo = _repair_demo_login_if_valid(email, password)
        if repaired_demo is not None:
            return True, repaired_demo
        # Constant-time-ish response — don't reveal "no account" vs "wrong password"
        hash_password("dummy_timing_guard")
        return False, "Invalid email or password."

    if not verify_password(password, user["password_hash"]):
        repaired_demo = _repair_demo_login_if_valid(email, password)
        if repaired_demo is not None:
            return True, repaired_demo
        return False, "Invalid email or password."

    # Return a safe subset (no hash)
    safe_user = {
        "id":    user["id"],
        "email": user["email"],
        "role":  user["role"],
    }
    logger.info("Login success: %s (%s)", email, user["role"])
    return True, safe_user
