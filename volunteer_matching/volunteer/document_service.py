"""
volunteer/document_service.py — Phase 8.5
Volunteer document upload and admin verification.
"""

import os, sqlite3, logging
from pathlib import Path
from db.database import get_connection
from notifications.notification_service import create_notification

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_UPLOAD_DIR   = _PROJECT_ROOT / "uploads"
_MAX_SIZE_MB  = 5
_ALLOWED_EXTS = {".pdf", ".jpg", ".jpeg", ".png"}
_DOC_TYPES    = {"CNIC","Resume","Student Card","Certificate","Other"}
_DOC_STATUSES = {"pending","verified","rejected"}


def _ensure_upload_dir():
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(filename: str) -> str:
    """Strip path components and dangerous characters."""
    name = os.path.basename(filename)
    safe = "".join(c for c in name if c.isalnum() or c in "._- ")
    return safe.strip() or "document"


def upload_volunteer_document(
    volunteer_user_id: int,
    document_type: str,
    file_bytes: bytes,
    original_filename: str,
) -> tuple[bool, str]:
    """
    Save a document for a volunteer.
    Returns (True, doc_id_str) on success, (False, error_msg) on failure.
    """
    document_type = (document_type or "").strip()
    if document_type not in _DOC_TYPES:
        return False, f"Invalid document type. Choose: {', '.join(sorted(_DOC_TYPES))}"

    if not file_bytes:
        return False, "No file data received."

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > _MAX_SIZE_MB:
        return False, f"File too large ({size_mb:.1f} MB). Maximum is {_MAX_SIZE_MB} MB."

    ext = Path(original_filename).suffix.lower()
    if ext not in _ALLOWED_EXTS:
        return False, f"File type '{ext}' not allowed. Use PDF, JPG, or PNG."

    conn = get_connection()
    try:
        vp = conn.execute(
            "SELECT id FROM VolunteerProfiles WHERE user_id=?", (volunteer_user_id,)
        ).fetchone()
        if not vp:
            return False, "Volunteer profile not found. Please complete your profile first."
        vp_id = vp["id"]

        _ensure_upload_dir()
        safe_name = _safe_filename(original_filename)
        import time
        ts = int(time.time())
        stored_name = f"vol_{vp_id}_{document_type.replace(' ','_')}_{ts}{ext}"
        file_path   = _UPLOAD_DIR / stored_name
        file_path.write_bytes(file_bytes)

        conn.execute(
            """INSERT INTO VolunteerDocuments
               (volunteer_profile_id, document_type, file_path,
                original_filename, verification_status, uploaded_at)
               VALUES (?,?,?,?,'pending',datetime('now'))""",
            (vp_id, document_type, str(file_path), safe_name),
        )
        conn.commit()
        logger.info("Document uploaded: user_id=%s type=%s", volunteer_user_id, document_type)
        return True, "Document uploaded successfully and is pending admin review."

    except sqlite3.Error as exc:
        logger.error("upload_volunteer_document: %s", exc)
        return False, "A database error occurred."
    finally:
        conn.close()


def get_documents_for_volunteer(volunteer_user_id: int) -> list[dict]:
    conn = get_connection()
    try:
        vp = conn.execute(
            "SELECT id FROM VolunteerProfiles WHERE user_id=?", (volunteer_user_id,)
        ).fetchone()
        if not vp: return []
        rows = conn.execute(
            "SELECT * FROM VolunteerDocuments WHERE volunteer_profile_id=? ORDER BY uploaded_at DESC",
            (vp["id"],),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_documents_for_volunteer: %s", exc)
        return []
    finally:
        conn.close()


def get_all_documents_for_admin() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT d.*, vp.full_name AS volunteer_name, u.email AS volunteer_email
               FROM VolunteerDocuments d
               JOIN VolunteerProfiles vp ON vp.id = d.volunteer_profile_id
               JOIN Users u ON u.id = vp.user_id
               ORDER BY d.uploaded_at DESC""",
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_all_documents_for_admin: %s", exc)
        return []
    finally:
        conn.close()


def verify_document(doc_id: int, admin_notes: str = "") -> tuple[bool, str]:
    conn = get_connection()
    try:
        doc_row = conn.execute("""SELECT d.id, d.document_type, vp.user_id FROM VolunteerDocuments d JOIN VolunteerProfiles vp ON vp.id=d.volunteer_profile_id WHERE d.id=?""", (doc_id,)).fetchone()
        if not doc_row:
            return False, "Document not found."
        conn.execute(
            "UPDATE VolunteerDocuments SET verification_status='verified', "
            "admin_notes=?, reviewed_at=datetime('now') WHERE id=?",
            ((admin_notes or "").strip(), doc_id),
        )
        conn.commit()
        create_notification(
            user_id=doc_row["user_id"],
            title="Document verified",
            message=f"Your {doc_row['document_type']} document has been verified by admin.",
            notification_type="document_verified",
            related_entity_type="volunteer_document",
            related_entity_id=doc_id,
        )
        return True, "Document verified."
    except sqlite3.Error as exc:
        logger.error("verify_document: %s", exc); return False, "Database error."
    finally:
        conn.close()


def reject_document(doc_id: int, admin_notes: str) -> tuple[bool, str]:
    admin_notes = (admin_notes or "").strip()
    if not admin_notes:
        return False, "Please provide a reason for rejection."
    conn = get_connection()
    try:
        doc_row = conn.execute("""SELECT d.id, d.document_type, vp.user_id FROM VolunteerDocuments d JOIN VolunteerProfiles vp ON vp.id=d.volunteer_profile_id WHERE d.id=?""", (doc_id,)).fetchone()
        if not doc_row:
            return False, "Document not found."
        conn.execute(
            "UPDATE VolunteerDocuments SET verification_status='rejected', "
            "admin_notes=?, reviewed_at=datetime('now') WHERE id=?",
            (admin_notes, doc_id),
        )
        conn.commit()
        create_notification(
            user_id=doc_row["user_id"],
            title="Document rejected",
            message=f"Your {doc_row['document_type']} document was rejected. Notes: {admin_notes}",
            notification_type="document_rejected",
            related_entity_type="volunteer_document",
            related_entity_id=doc_id,
        )
        return True, "Document rejected."
    except sqlite3.Error as exc:
        logger.error("reject_document: %s", exc); return False, "Database error."
    finally:
        conn.close()
