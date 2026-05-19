"""Deployment health check for the AI Volunteer Matching System."""
from __future__ import annotations

import importlib.util
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db.database import get_connection, get_db_path  # noqa: E402
from db.schema import initialize_database, get_table_names  # noqa: E402
from utils.config import get_groq_api_key, get_tesseract_cmd  # noqa: E402

REQUIRED_TABLES = {
    "Users", "VolunteerProfiles", "NGOProfiles", "Events", "MatchScores",
    "Applications", "Feedback", "VolunteerDocuments", "Notifications",
}
DEMO_EMAILS = {
    "admin@volmatch.local",
    "volunteer@volmatch.local",
    "ngo@volmatch.local",
}


def _line(status: str, message: str) -> None:
    print(f"{status:<8} {message}")


def main() -> int:
    fail = False
    print("VolunteerAI deployment health check\n")

    try:
        initialize_database()
        conn = get_connection()
        conn.execute("SELECT 1").fetchone()
        _line("PASS", f"Database connection OK: {get_db_path()}")
    except Exception as exc:
        _line("FAIL", f"Database connection failed: {exc}")
        return 1

    try:
        tables = set(get_table_names(conn))
        missing = sorted(REQUIRED_TABLES - tables)
        if missing:
            fail = True
            _line("FAIL", f"Missing required tables: {', '.join(missing)}")
        else:
            _line("PASS", "All required tables exist")
    except sqlite3.Error as exc:
        fail = True
        _line("FAIL", f"Could not inspect tables: {exc}")

    for directory in [ROOT / "uploads", ROOT / "data" / "models", ROOT / "data" / "dataset"]:
        if directory.exists():
            _line("PASS", f"Directory exists: {directory.relative_to(ROOT)}")
        else:
            directory.mkdir(parents=True, exist_ok=True)
            _line("WARNING", f"Directory was missing and has been created: {directory.relative_to(ROOT)}")

    try:
        rows = conn.execute(
            "SELECT email FROM Users WHERE email IN (?,?,?)",
            tuple(DEMO_EMAILS),
        ).fetchall()
        found = {r["email"] for r in rows}
        missing = sorted(DEMO_EMAILS - found)
        if missing:
            _line("WARNING", f"Demo accounts missing: {', '.join(missing)}. Run scripts/seed_demo_data.py")
        else:
            _line("PASS", "Demo accounts exist")
    except sqlite3.Error as exc:
        _line("WARNING", f"Could not verify demo accounts: {exc}")
    finally:
        conn.close()

    if get_groq_api_key():
        _line("PASS", "Groq API key configured")
    else:
        _line("WARNING", "Groq API key missing; AI features will use safe fallback messages")

    configured_tesseract = get_tesseract_cmd()
    if shutil.which("tesseract") or configured_tesseract:
        _line("PASS", f"Tesseract OCR binary found{': ' + configured_tesseract if configured_tesseract else ''}")
    else:
        _line("WARNING", "Tesseract OCR binary not found. Install Tesseract or set TESSERACT_CMD in .env")

    for module in ["streamlit", "pandas", "numpy", "sklearn", "groq", "pytesseract", "PIL", "pdfplumber", "fitz"]:
        if importlib.util.find_spec(module):
            _line("PASS", f"Python package available: {module}")
        else:
            _line("WARNING", f"Python package missing: {module}")

    print("\nHealth check complete.")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
