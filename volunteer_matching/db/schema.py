"""
db/schema.py  —  Phase 8.5
──────────────────────────
Adds:
  * Extended VolunteerProfiles columns (address, gender, education, etc.)
  * Extended NGOProfiles columns (address, aim, objectives, services, etc.)
  * Extended Events columns (required_gender, min/max age, education, detailed_location)
  * VolunteerDocuments table
All changes are migration-safe (ALTER TABLE on existing DBs).
"""

import sqlite3
import logging
from db.database import get_connection

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# DDL
# ─────────────────────────────────────────────────────────────────────────────

_CREATE_USERS = """CREATE TABLE IF NOT EXISTS Users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'volunteer'
                       CHECK(role IN ('volunteer','ngo','admin')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);"""

_CREATE_VOLUNTEER_PROFILES = """CREATE TABLE IF NOT EXISTS VolunteerProfiles (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id              INTEGER NOT NULL UNIQUE REFERENCES Users(id) ON DELETE CASCADE,
    full_name            TEXT NOT NULL DEFAULT '',
    gender               TEXT DEFAULT '',
    age                  INTEGER,
    address              TEXT DEFAULT '',
    city                 TEXT NOT NULL DEFAULT '',
    education            TEXT DEFAULT '',
    languages            TEXT DEFAULT '',
    occupation           TEXT DEFAULT '',
    skills               TEXT NOT NULL DEFAULT '',
    interests            TEXT NOT NULL DEFAULT '',
    availability         TEXT NOT NULL DEFAULT '',
    experience_level     TEXT NOT NULL DEFAULT '',
    preferred_mode       TEXT NOT NULL DEFAULT '',
    bio                  TEXT,
    profile_completeness INTEGER NOT NULL DEFAULT 0,
    verification_status  TEXT NOT NULL DEFAULT 'unverified'
                              CHECK(verification_status IN ('unverified','pending','verified','rejected')),
    verification_notes   TEXT,
    profile_photo_path   TEXT,
    created_at           TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at           TEXT NOT NULL DEFAULT (datetime('now'))
);"""

_CREATE_NGO_PROFILES = """CREATE TABLE IF NOT EXISTS NGOProfiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL UNIQUE REFERENCES Users(id) ON DELETE CASCADE,
    organization_name   TEXT NOT NULL,
    registration_number TEXT,
    contact_person      TEXT NOT NULL,
    phone               TEXT,
    city                TEXT NOT NULL,
    address             TEXT DEFAULT '',
    aim                 TEXT DEFAULT '',
    objectives          TEXT DEFAULT '',
    services            TEXT DEFAULT '',
    cause_areas         TEXT NOT NULL,
    description         TEXT,
    website             TEXT,
    legal_document_path TEXT,
    profile_photo_path  TEXT,
    verification_status TEXT NOT NULL DEFAULT 'pending'
                             CHECK(verification_status IN ('pending','approved','rejected')),
    rejection_reason    TEXT,
    submitted_at        TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at         TEXT,
    reviewed_by         INTEGER REFERENCES Users(id),
    updated_at          TEXT NOT NULL DEFAULT (datetime('now'))
);"""

_CREATE_EVENTS = """CREATE TABLE IF NOT EXISTS Events (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ngo_profile_id   INTEGER NOT NULL REFERENCES NGOProfiles(id) ON DELETE CASCADE,
    title            TEXT NOT NULL,
    description      TEXT NOT NULL,
    required_skills  TEXT NOT NULL,
    city             TEXT NOT NULL,
    detailed_location TEXT DEFAULT '',
    event_date       TEXT NOT NULL,
    event_time       TEXT NOT NULL,
    duration_hours   REAL,
    capacity         INTEGER NOT NULL,
    cause_area       TEXT NOT NULL,
    experience_level TEXT NOT NULL,
    mode             TEXT NOT NULL,
    required_gender  TEXT DEFAULT 'Anyone',
    minimum_age      INTEGER DEFAULT 0,
    maximum_age      INTEGER DEFAULT 100,
    required_education TEXT DEFAULT 'Anyone',
    status           TEXT NOT NULL DEFAULT 'pending'
                          CHECK(status IN ('pending','approved','rejected','closed','completed')),
    rejection_reason TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at       TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at      TEXT,
    reviewed_by      INTEGER REFERENCES Users(id)
);"""

_CREATE_MATCH_SCORES = """CREATE TABLE IF NOT EXISTS MatchScores (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    volunteer_profile_id INTEGER NOT NULL REFERENCES VolunteerProfiles(id) ON DELETE CASCADE,
    event_id             INTEGER NOT NULL REFERENCES Events(id) ON DELETE CASCADE,
    final_score          REAL NOT NULL,
    skill_score          REAL NOT NULL,
    availability_score   REAL NOT NULL,
    location_score       REAL NOT NULL,
    interest_score       REAL NOT NULL,
    experience_score     REAL NOT NULL,
    mode_score           REAL NOT NULL,
    explanation          TEXT,
    calculated_at        TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(volunteer_profile_id, event_id)
);"""

_CREATE_APPLICATIONS = """CREATE TABLE IF NOT EXISTS Applications (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    volunteer_profile_id INTEGER NOT NULL REFERENCES VolunteerProfiles(id) ON DELETE CASCADE,
    event_id             INTEGER NOT NULL REFERENCES Events(id) ON DELETE CASCADE,
    match_score          REAL,
    status               TEXT NOT NULL DEFAULT 'pending'
                              CHECK(status IN ('pending','accepted','rejected','cancelled')),
    volunteer_note       TEXT,
    ngo_response         TEXT,
    applied_at           TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at          TEXT,
    UNIQUE(volunteer_profile_id, event_id)
);"""

_CREATE_FEEDBACK = """CREATE TABLE IF NOT EXISTS Feedback (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id   INTEGER NOT NULL REFERENCES Applications(id) ON DELETE CASCADE,
    feedback_from    TEXT NOT NULL CHECK(feedback_from IN ('volunteer','ngo')),
    rating           INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    secondary_rating INTEGER CHECK(secondary_rating BETWEEN 1 AND 5),
    attended         INTEGER NOT NULL DEFAULT 0 CHECK(attended IN (0,1)),
    match_relevance  TEXT,
    comments         TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(application_id, feedback_from)
);"""

# Phase 8.5 — VolunteerDocuments
_CREATE_VOLUNTEER_DOCUMENTS = """CREATE TABLE IF NOT EXISTS VolunteerDocuments (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    volunteer_profile_id INTEGER NOT NULL REFERENCES VolunteerProfiles(id) ON DELETE CASCADE,
    document_type        TEXT NOT NULL
                              CHECK(document_type IN ('CNIC','Resume','Student Card','Certificate','Other')),
    file_path            TEXT NOT NULL,
    original_filename    TEXT NOT NULL DEFAULT '',
    verification_status  TEXT NOT NULL DEFAULT 'pending'
                              CHECK(verification_status IN ('pending','verified','rejected')),
    admin_notes          TEXT,
    uploaded_at          TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at          TEXT,
    extracted_text       TEXT,
    ocr_status           TEXT NOT NULL DEFAULT 'not_processed'
                              CHECK(ocr_status IN ('not_processed','processed','failed')),
    ocr_error            TEXT,
    ai_summary           TEXT,
    analyzed_at          TEXT
);"""




_CREATE_NGO_DOCUMENTS = """CREATE TABLE IF NOT EXISTS NGODocuments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ngo_profile_id      INTEGER NOT NULL REFERENCES NGOProfiles(id) ON DELETE CASCADE,
    document_type       TEXT NOT NULL
                            CHECK(document_type IN ('Registration Certificate','Tax Certificate','Authorization Letter','NGO License','Address Proof','Bank Letter','Other')),
    file_path           TEXT NOT NULL,
    original_filename   TEXT NOT NULL DEFAULT '',
    verification_status TEXT NOT NULL DEFAULT 'pending'
                            CHECK(verification_status IN ('pending','verified','rejected')),
    admin_notes         TEXT,
    uploaded_at         TEXT NOT NULL DEFAULT (datetime('now')),
    reviewed_at         TEXT,
    reviewed_by         INTEGER REFERENCES Users(id),
    extracted_text      TEXT,
    ocr_status          TEXT NOT NULL DEFAULT 'not_processed'
                            CHECK(ocr_status IN ('not_processed','processed','failed')),
    ocr_error           TEXT,
    ai_summary          TEXT,
    analyzed_at         TEXT
);"""


_CREATE_SESSIONS = """CREATE TABLE IF NOT EXISTS Sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    session_token TEXT NOT NULL UNIQUE,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at    TEXT,
    is_active     INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1))
);"""

_CREATE_SESSIONS_INDEX = """CREATE INDEX IF NOT EXISTS idx_sessions_token_active ON Sessions(session_token, is_active);"""

_CREATE_NOTIFICATIONS = """CREATE TABLE IF NOT EXISTS Notifications (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    title               TEXT NOT NULL,
    message             TEXT NOT NULL,
    notification_type   TEXT NOT NULL,
    related_entity_type TEXT,
    related_entity_id   INTEGER,
    is_read             INTEGER NOT NULL DEFAULT 0 CHECK(is_read IN (0,1)),
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);"""

def _trig(name, table):
    return f"""CREATE TRIGGER IF NOT EXISTS {name}
AFTER UPDATE ON {table} BEGIN
    UPDATE {table} SET updated_at = datetime('now') WHERE id = NEW.id;
END;"""

_ALL = [
    ("Users",               _CREATE_USERS),
    ("VolunteerProfiles",   _CREATE_VOLUNTEER_PROFILES),
    ("NGOProfiles",         _CREATE_NGO_PROFILES),
    ("Events",              _CREATE_EVENTS),
    ("MatchScores",         _CREATE_MATCH_SCORES),
    ("Applications",        _CREATE_APPLICATIONS),
    ("Feedback",            _CREATE_FEEDBACK),
    ("VolunteerDocuments",  _CREATE_VOLUNTEER_DOCUMENTS),
    ("NGODocuments",       _CREATE_NGO_DOCUMENTS),
    ("Notifications",       _CREATE_NOTIFICATIONS),
    ("Sessions",            _CREATE_SESSIONS),
    ("idx_sessions",       _CREATE_SESSIONS_INDEX),
    ("trg_users",   _trig("trg_users_upd",   "Users")),
    ("trg_vol",     _trig("trg_vol_upd",     "VolunteerProfiles")),
    ("trg_ngo",     _trig("trg_ngo_upd",     "NGOProfiles")),
    ("trg_events",  _trig("trg_events_upd",  "Events")),
]

_MIGRATIONS = [
    ("Users","updated_at","TEXT NOT NULL DEFAULT (datetime('now'))"),

    # Persistent login sessions
    ("Sessions","user_id","INTEGER NOT NULL DEFAULT 0"),
    ("Sessions","session_token","TEXT NOT NULL DEFAULT ''"),
    ("Sessions","created_at","TEXT NOT NULL DEFAULT (datetime('now'))"),
    ("Sessions","expires_at","TEXT"),
    ("Sessions","is_active","INTEGER NOT NULL DEFAULT 1"),

    # Notifications table cols
    ("Notifications","user_id","INTEGER NOT NULL DEFAULT 0"),
    ("Notifications","title","TEXT NOT NULL DEFAULT ''"),
    ("Notifications","message","TEXT NOT NULL DEFAULT ''"),
    ("Notifications","notification_type","TEXT NOT NULL DEFAULT 'system'"),
    ("Notifications","related_entity_type","TEXT"),
    ("Notifications","related_entity_id","INTEGER"),
    ("Notifications","is_read","INTEGER NOT NULL DEFAULT 0"),
    ("Notifications","created_at","TEXT NOT NULL DEFAULT (datetime('now'))"),
    # VolunteerProfiles new cols
    ("VolunteerProfiles","gender","TEXT DEFAULT ''"),
    ("VolunteerProfiles","address","TEXT DEFAULT ''"),
    ("VolunteerProfiles","education","TEXT DEFAULT ''"),
    ("VolunteerProfiles","languages","TEXT DEFAULT ''"),
    ("VolunteerProfiles","occupation","TEXT DEFAULT ''"),
    ("VolunteerProfiles","verification_status","TEXT NOT NULL DEFAULT 'unverified'"),
    ("VolunteerProfiles","verification_notes","TEXT"),
    ("VolunteerProfiles","profile_photo_path","TEXT"),
    ("VolunteerProfiles","full_name","TEXT NOT NULL DEFAULT ''"),
    ("VolunteerProfiles","age","INTEGER"),
    ("VolunteerProfiles","city","TEXT NOT NULL DEFAULT ''"),
    ("VolunteerProfiles","skills","TEXT NOT NULL DEFAULT ''"),
    ("VolunteerProfiles","interests","TEXT NOT NULL DEFAULT ''"),
    ("VolunteerProfiles","availability","TEXT NOT NULL DEFAULT ''"),
    ("VolunteerProfiles","experience_level","TEXT NOT NULL DEFAULT ''"),
    ("VolunteerProfiles","preferred_mode","TEXT NOT NULL DEFAULT ''"),
    ("VolunteerProfiles","bio","TEXT"),
    ("VolunteerProfiles","profile_completeness","INTEGER NOT NULL DEFAULT 0"),
    ("VolunteerProfiles","updated_at","TEXT NOT NULL DEFAULT (datetime('now'))"),

    # VolunteerDocuments OCR/content intelligence cols
    ("VolunteerDocuments","extracted_text","TEXT"),
    ("VolunteerDocuments","ocr_status","TEXT NOT NULL DEFAULT 'not_processed'"),
    ("VolunteerDocuments","ocr_error","TEXT"),
    ("VolunteerDocuments","ai_summary","TEXT"),
    ("VolunteerDocuments","analyzed_at","TEXT"),

    # NGODocuments migration-safe cols
    ("NGODocuments","ngo_profile_id","INTEGER NOT NULL DEFAULT 0"),
    ("NGODocuments","document_type","TEXT NOT NULL DEFAULT 'Other'"),
    ("NGODocuments","file_path","TEXT NOT NULL DEFAULT ''"),
    ("NGODocuments","original_filename","TEXT NOT NULL DEFAULT ''"),
    ("NGODocuments","verification_status","TEXT NOT NULL DEFAULT 'pending'"),
    ("NGODocuments","admin_notes","TEXT"),
    ("NGODocuments","uploaded_at","TEXT NOT NULL DEFAULT (datetime('now'))"),
    ("NGODocuments","reviewed_at","TEXT"),
    ("NGODocuments","reviewed_by","INTEGER"),
    ("NGODocuments","extracted_text","TEXT"),
    ("NGODocuments","ocr_status","TEXT NOT NULL DEFAULT 'not_processed'"),
    ("NGODocuments","ocr_error","TEXT"),
    ("NGODocuments","ai_summary","TEXT"),
    ("NGODocuments","analyzed_at","TEXT"),
    # NGOProfiles new cols
    ("NGOProfiles","address","TEXT DEFAULT ''"),
    ("NGOProfiles","aim","TEXT DEFAULT ''"),
    ("NGOProfiles","objectives","TEXT DEFAULT ''"),
    ("NGOProfiles","services","TEXT DEFAULT ''"),
    ("NGOProfiles","legal_document_path","TEXT"),
    ("NGOProfiles","profile_photo_path","TEXT"),
    ("NGOProfiles","registration_number","TEXT"),
    ("NGOProfiles","contact_person","TEXT NOT NULL DEFAULT ''"),
    ("NGOProfiles","phone","TEXT"),
    ("NGOProfiles","city","TEXT NOT NULL DEFAULT ''"),
    ("NGOProfiles","cause_areas","TEXT NOT NULL DEFAULT ''"),
    ("NGOProfiles","verification_status","TEXT NOT NULL DEFAULT 'pending'"),
    ("NGOProfiles","rejection_reason","TEXT"),
    ("NGOProfiles","submitted_at","TEXT NOT NULL DEFAULT (datetime('now'))"),
    ("NGOProfiles","reviewed_at","TEXT"),
    ("NGOProfiles","reviewed_by","INTEGER"),
    ("NGOProfiles","updated_at","TEXT NOT NULL DEFAULT (datetime('now'))"),
    # Events new cols
    ("Events","ngo_profile_id","INTEGER NOT NULL DEFAULT 0"),
    ("Events","description","TEXT NOT NULL DEFAULT ''"),
    ("Events","required_skills","TEXT NOT NULL DEFAULT ''"),
    ("Events","city","TEXT NOT NULL DEFAULT ''"),
    ("Events","detailed_location","TEXT DEFAULT ''"),
    ("Events","event_date","TEXT NOT NULL DEFAULT ''"),
    ("Events","event_time","TEXT NOT NULL DEFAULT ''"),
    ("Events","duration_hours","REAL"),
    ("Events","capacity","INTEGER NOT NULL DEFAULT 1"),
    ("Events","cause_area","TEXT NOT NULL DEFAULT ''"),
    ("Events","experience_level","TEXT NOT NULL DEFAULT ''"),
    ("Events","mode","TEXT NOT NULL DEFAULT ''"),
    ("Events","required_gender","TEXT DEFAULT 'Anyone'"),
    ("Events","minimum_age","INTEGER DEFAULT 0"),
    ("Events","maximum_age","INTEGER DEFAULT 100"),
    ("Events","required_education","TEXT DEFAULT 'Anyone'"),
    ("Events","rejection_reason","TEXT"),
    ("Events","reviewed_at","TEXT"),
    ("Events","reviewed_by","INTEGER"),
    ("Events","updated_at","TEXT NOT NULL DEFAULT (datetime('now'))"),
]

_DEMO_ACCOUNTS = [
    ("admin@volmatch.local", "Admin@123", "admin"),
    ("volunteer@volmatch.local", "Volunteer@123", "volunteer"),
    ("ngo@volmatch.local", "Ngo@123", "ngo"),
]
_ADMIN_EMAIL    = "admin@volmatch.local"
_ADMIN_PASSWORD = "Admin@123"

def _cols(conn, table):
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}

def _tbl(conn, table):
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None

def _run_migrations(conn):
    for table, col, defn in _MIGRATIONS:
        if not _tbl(conn, table): continue
        if col not in _cols(conn, table):
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
                conn.commit()
                logger.info("Migration: added %s.%s", table, col)
            except sqlite3.Error as exc:
                logger.warning("Migration skipped %s.%s: %s", table, col, exc)

def initialize_schema(conn):
    cur = conn.cursor()
    try:
        for _, stmt in _ALL:
            cur.execute(stmt)
        conn.commit()
    except sqlite3.Error as exc:
        conn.rollback(); raise
    finally:
        cur.close()

def _seed_demo_accounts(conn):
    """Ensure demo accounts exist and repair their passwords/roles if needed."""
    from auth.auth_service import hash_password, verify_password

    for email, password, role in _DEMO_ACCOUNTS:
        row = conn.execute(
            "SELECT id, password_hash, role FROM Users WHERE email=?",
            (email,),
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO Users (email, password_hash, role) VALUES (?,?,?)",
                (email, hash_password(password), role),
            )
            continue

        needs_update = row["role"] != role or not verify_password(password, row["password_hash"])
        if needs_update:
            conn.execute(
                "UPDATE Users SET password_hash=?, role=?, updated_at=datetime('now') WHERE id=?",
                (hash_password(password), role, row["id"]),
            )
    conn.commit()


def _seed_admin(conn):
    # Backward-compatible wrapper retained for older imports.
    _seed_demo_accounts(conn)

def initialize_database():
    conn = get_connection()
    try:
        initialize_schema(conn)
        _run_migrations(conn)
        _seed_demo_accounts(conn)
    finally:
        conn.close()

def get_table_names(conn):
    return [r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()]
