"""
db/database.py
──────────────
SQLite connection handler for the Volunteer Matching System.

Usage
-----
    from db.database import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users")
    rows = cursor.fetchall()
    conn.close()          # always close when done
"""

import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv


# Resolve project root → data/ directory regardless of where Python is invoked
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

_DATA_DIR = _PROJECT_ROOT / "data"

def _resolve_db_path() -> Path:
    raw = os.getenv("DB_PATH", "").strip().strip('"').strip("'")
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else (_PROJECT_ROOT / path)
    return _DATA_DIR / "volunteer_matching.db"

_DB_PATH = _resolve_db_path()


def get_connection() -> sqlite3.Connection:
    """
    Return a sqlite3 Connection to the project database.

    - Creates the data/ directory if it does not exist.
    - Creates the .db file on first connection (SQLite behaviour).
    - Enables foreign-key enforcement.
    - Sets row_factory to sqlite3.Row so columns are accessible by name.

    Returns
    -------
    sqlite3.Connection
        An open connection — caller is responsible for closing it.
    """
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row          # access columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")   # better concurrency
    return conn


def get_db_path() -> Path:
    """Return the absolute path to the SQLite database file."""
    return _DB_PATH
