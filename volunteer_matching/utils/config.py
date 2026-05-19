"""
utils/config.py
───────────────
Environment-variable loader for the Volunteer Matching System.

Reads from a .env file (if present) via python-dotenv, then exposes
typed helper functions for every config value the app needs.

Usage
-----
    from utils.config import get_groq_api_key, get_db_path, settings

    key = get_groq_api_key()   # None until Phase 3
    print(settings)            # full config snapshot (safe — no secrets)
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# ── Load .env on import ───────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"

if _ENV_FILE.exists():
    load_dotenv(_ENV_FILE)
    logger.debug("Loaded environment from %s", _ENV_FILE)
else:
    logger.debug(".env not found at %s — relying on shell environment.", _ENV_FILE)


# ── Accessors ─────────────────────────────────────────────────────────────────

def _clean_config_value(value: object | None) -> str:
    """Return a safely stripped config value without surrounding quotes."""
    if value is None:
        return ""
    return str(value).strip().strip('"').strip("'").strip()


def _get_streamlit_secret(key: str) -> str:
    """Read one Streamlit secret safely. Works outside Streamlit too."""
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            return _clean_config_value(st.secrets.get(key, ""))
    except Exception:
        pass
    return ""


def get_groq_api_key() -> str | None:
    """
    Return the optional Groq API key.

    Lookup order:
      1. Streamlit secrets: GROQ_API_KEY
      2. Streamlit secrets section: [groq] api_key = "..."
      3. .env / shell environment variable: GROQ_API_KEY

    Missing, empty, quoted, or placeholder values return None so AI features
    can fail gracefully without breaking the app.
    """
    placeholders = {
        "",
        "your_groq_api_key_here",
        "your-api-key-here",
        "gsk_your_actual_key_here",
        "GROQ_API_KEY",
    }

    secret_value = _get_streamlit_secret("GROQ_API_KEY")
    if not secret_value:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "groq" in st.secrets:
                secret_value = _clean_config_value(st.secrets["groq"].get("api_key", ""))
        except Exception:
            secret_value = ""

    if secret_value and secret_value not in placeholders:
        return secret_value

    env_value = _clean_config_value(os.getenv("GROQ_API_KEY", ""))
    if env_value and env_value not in placeholders:
        return env_value

    return None


def get_tesseract_cmd() -> str | None:
    """Return optional Tesseract executable path for local OCR.

    On Windows, pytesseract often needs the explicit path to
    tesseract.exe. The app first checks Streamlit secrets, then .env, then
    common Windows install locations. Missing values return None so OCR can
    fail gracefully instead of crashing.
    """
    candidates: list[str] = []

    secret_value = _get_streamlit_secret("TESSERACT_CMD")
    if secret_value:
        candidates.append(secret_value)

    env_value = _clean_config_value(os.getenv("TESSERACT_CMD", ""))
    if env_value:
        candidates.append(env_value)

    candidates.extend([
        r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
    ])

    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return str(path)

    return None

def get_db_path() -> Path:
    """
    Return the path to the SQLite database file.

    Defaults to <project_root>/data/volunteer_matching.db.
    Override via DB_PATH env var if needed.
    """
    raw = _clean_config_value(os.getenv("DB_PATH", ""))
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else (_PROJECT_ROOT / path)
    return _PROJECT_ROOT / "data" / "volunteer_matching.db"


def get_app_secret() -> str:
    """
    Return the application secret used for session tokens (Phase 2).

    Falls back to a hard-coded insecure default so Phase 1 never errors —
    this MUST be overridden via APP_SECRET in production.
    """
    secret = os.getenv("APP_SECRET", "").strip()
    if not secret:
        logger.warning(
            "APP_SECRET not set — using insecure default. "
            "Set APP_SECRET in your .env for Phase 2."
        )
        return "INSECURE_DEFAULT_CHANGE_ME"
    return secret


# ── Convenience snapshot (no secrets) ────────────────────────────────────────

settings: dict = {
    "db_path":          str(get_db_path()),
    "groq_configured":  get_groq_api_key() is not None,
    "tesseract_configured": get_tesseract_cmd() is not None,
    "secret_set":       os.getenv("APP_SECRET", "") not in ("", None),
    "env_file_loaded":  _ENV_FILE.exists(),
    "project_root":     str(_PROJECT_ROOT),
}
