"""Final smoke test for the AI-Based Volunteer Matching System.

Run from the project root:
    python scripts/smoke_test.py

The script intentionally treats Groq, OCR, and ML model availability as optional
warnings because the app is designed to fail gracefully when those integrations
are not configured.
"""
from __future__ import annotations

import importlib
import importlib.util
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED_FILES = [
    "app.py",
    "requirements.txt",
    "README.md",
    "DEPLOYMENT.md",
    "db/schema.py",
    "db/database.py",
    "utils/config.py",
]

REQUIRED_DIRS = [
    "ai", "analytics", "applications", "auth", "data", "db", "documents",
    "events", "feedback", "matching", "ml", "notifications", "pages",
    "scripts", "ui", "uploads", "utils", "volunteer", "ngo", "admin", "qa",
]

REQUIRED_PAGES = [
    "pages/1_Login.py",
    "pages/2_Volunteer_Dashboard.py",
    "pages/3_NGO_Dashboard.py",
    "pages/4_Admin_Dashboard.py",
    "pages/5_Recommendations.py",
    "pages/6_My_Applications.py",
    "pages/7_Evaluation.py",
    "pages/8_ML_Evaluation.py",
    "pages/9_Advanced_Analytics.py",
]

CORE_MODULES = [
    "db.database", "db.schema", "utils.config", "utils.session",
    "auth.auth_service", "volunteer.volunteer_service", "volunteer.document_service",
    "ngo.ngo_service", "events.event_service", "applications.application_service",
    "feedback.feedback_service", "matching.matching_engine", "ml.ml_matcher",
    "ai.groq_client", "ai.ai_service", "documents.ocr_service",
    "documents.document_analysis_service", "notifications.notification_service",
    "analytics.analytics_service", "analytics.insight_service", "ui.components",
]

REQUIRED_TABLES = {
    "Users", "VolunteerProfiles", "NGOProfiles", "Events", "MatchScores",
    "Applications", "Feedback", "VolunteerDocuments", "Notifications",
}

DEMO_ACCOUNTS = {
    "admin@volmatch.local": "admin",
    "volunteer@volmatch.local": "volunteer",
    "ngo@volmatch.local": "ngo",
}

OPTIONAL_PACKAGES = {
    "streamlit": "Streamlit UI",
    "pandas": "analytics tables",
    "numpy": "ML/data utilities",
    "sklearn": "ML enhancement",
    "groq": "optional Groq AI",
    "pytesseract": "optional OCR wrapper",
    "PIL": "image OCR support",
    "pdfplumber": "PDF text extraction",
    "fitz": "PyMuPDF PDF fallback",
}


class ResultCounter:
    def __init__(self) -> None:
        self.pass_count = 0
        self.warning_count = 0
        self.fail_count = 0

    def line(self, status: str, message: str) -> None:
        status = status.upper()
        if status == "PASS":
            self.pass_count += 1
        elif status == "WARNING":
            self.warning_count += 1
        elif status == "FAIL":
            self.fail_count += 1
        print(f"{status:<8} {message}")


def _exists(counter: ResultCounter, rel_path: str, is_dir: bool = False) -> None:
    path = ROOT / rel_path
    ok = path.is_dir() if is_dir else path.is_file()
    counter.line("PASS" if ok else "FAIL", f"{'Directory' if is_dir else 'File'} check: {rel_path}")


KNOWN_EXTERNAL_IMPORTS = ("streamlit", "passlib", "groq", "pytesseract", "PIL", "pdfplumber", "fitz", "sklearn")


def _import_module(counter: ResultCounter, module_name: str) -> None:
    try:
        importlib.import_module(module_name)
        counter.line("PASS", f"Import OK: {module_name}")
    except ModuleNotFoundError as exc:
        missing = str(exc).split("No module named ")[-1].strip("'\"")
        if missing.startswith(KNOWN_EXTERNAL_IMPORTS):
            counter.line("WARNING", f"Import skipped until dependencies are installed: {module_name} — missing {missing}")
        else:
            counter.line("FAIL", f"Import failed: {module_name} — {exc}")
    except Exception as exc:
        counter.line("FAIL", f"Import failed: {module_name} — {exc}")


def main() -> int:
    counter = ResultCounter()
    print("AI-Based Volunteer Matching System — final smoke test\n")

    for item in REQUIRED_FILES:
        _exists(counter, item)
    for item in REQUIRED_DIRS:
        _exists(counter, item, is_dir=True)
    for item in REQUIRED_PAGES:
        _exists(counter, item)

    print("\nCore module imports")
    for module_name in CORE_MODULES:
        _import_module(counter, module_name)

    print("\nDatabase and schema")
    try:
        from db.database import get_connection, get_db_path
        from db.schema import get_table_names, initialize_database

        initialize_database()
        conn = get_connection()
        conn.execute("SELECT 1").fetchone()
        counter.line("PASS", f"Database initializes: {get_db_path()}")

        tables = set(get_table_names(conn))
        missing = sorted(REQUIRED_TABLES - tables)
        if missing:
            counter.line("FAIL", f"Missing required tables: {', '.join(missing)}")
        else:
            counter.line("PASS", "All required schema tables exist")

        try:
            rows = conn.execute(
                "SELECT email, role FROM Users WHERE email IN (?,?,?)",
                tuple(DEMO_ACCOUNTS.keys()),
            ).fetchall()
            found = {row["email"]: row["role"] for row in rows}
            missing_accounts = [email for email in DEMO_ACCOUNTS if email not in found]
            if missing_accounts:
                counter.line("WARNING", "Demo accounts missing; run python scripts/seed_demo_data.py")
            else:
                role_mismatch = [email for email, role in DEMO_ACCOUNTS.items() if found.get(email) != role]
                if role_mismatch:
                    counter.line("WARNING", f"Demo account role mismatch: {', '.join(role_mismatch)}")
                else:
                    counter.line("PASS", "Demo accounts exist with expected roles")
        except sqlite3.Error as exc:
            counter.line("WARNING", f"Could not verify demo accounts: {exc}")
        finally:
            conn.close()
    except ModuleNotFoundError as exc:
        counter.line("WARNING", f"Database initialization needs installed dependency: {exc}")
    except Exception as exc:
        counter.line("FAIL", f"Database smoke test failed: {exc}")

    print("\nRuntime directories")
    for directory in [ROOT / "uploads", ROOT / "data" / "models", ROOT / "data" / "dataset"]:
        if directory.exists():
            counter.line("PASS", f"Runtime directory exists: {directory.relative_to(ROOT)}")
        else:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                counter.line("WARNING", f"Runtime directory was missing and was created: {directory.relative_to(ROOT)}")
            except Exception as exc:
                counter.line("FAIL", f"Could not create runtime directory {directory}: {exc}")

    print("\nOptional integrations")
    try:
        from utils.config import get_groq_api_key
        counter.line("PASS" if get_groq_api_key() else "WARNING", "Groq key configured" if get_groq_api_key() else "Groq key missing; AI fallback expected")
    except Exception as exc:
        counter.line("WARNING", f"Could not inspect Groq configuration: {exc}")

    for package, purpose in OPTIONAL_PACKAGES.items():
        if importlib.util.find_spec(package):
            counter.line("PASS", f"Package available: {package} ({purpose})")
        else:
            counter.line("WARNING", f"Package missing: {package} ({purpose})")

    model_path = ROOT / "data" / "models" / "match_model.pkl"
    if model_path.exists():
        counter.line("PASS", "Optional ML model file exists")
    else:
        counter.line("WARNING", "Optional ML model file missing; deterministic matching still works")

    print("\nSummary")
    print(f"PASS: {counter.pass_count} | WARNING: {counter.warning_count} | FAIL: {counter.fail_count}")
    return 1 if counter.fail_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
