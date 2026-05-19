"""NGO document upload and admin verification service.

NGO documents are used to assist manual admin verification. OCR/AI may support
review, but documents are never auto-approved.
"""
from __future__ import annotations

import logging
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

from db.database import get_connection
from documents.ocr_service import extract_text_from_document
from documents.document_utils import clean_extracted_text, truncate_text
from ai.ai_service import generate_document_content_summary
from notifications.notification_service import create_notification

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_UPLOAD_DIR = _PROJECT_ROOT / "uploads" / "ngo_documents"
_MAX_SIZE_MB = 5
_ALLOWED_EXTS = {".pdf", ".jpg", ".jpeg", ".png"}
_DOC_TYPES = {
    "Registration Certificate", "Tax Certificate", "Authorization Letter",
    "NGO License", "Address Proof", "Bank Letter", "Other",
}


def _safe_filename(filename: str) -> str:
    name = os.path.basename(filename or "document")
    safe = "".join(c for c in name if c.isalnum() or c in "._- ").strip()
    return safe or "document"


def _ensure_upload_dir() -> None:
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _row_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def upload_ngo_document(ngo_user_id: int, document_type: str, uploaded_file) -> tuple[bool, str]:
    """Save an NGO verification document from a Streamlit UploadedFile."""
    document_type = (document_type or "").strip()
    if document_type not in _DOC_TYPES:
        return False, "Invalid document type."
    if uploaded_file is None:
        return False, "Please choose a PDF, JPG, or PNG file."

    original_filename = getattr(uploaded_file, "name", "document")
    ext = Path(original_filename).suffix.lower()
    if ext not in _ALLOWED_EXTS:
        return False, "Only PDF, JPG, and PNG files are allowed."

    try:
        file_bytes = uploaded_file.getvalue()
    except Exception:
        return False, "Could not read uploaded file."

    if not file_bytes:
        return False, "Uploaded file is empty."
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > _MAX_SIZE_MB:
        return False, f"File too large ({size_mb:.1f} MB). Maximum is {_MAX_SIZE_MB} MB."

    conn = get_connection()
    try:
        profile = conn.execute("SELECT id FROM NGOProfiles WHERE user_id=?", (ngo_user_id,)).fetchone()
        if not profile:
            return False, "Create your NGO profile before uploading documents."

        _ensure_upload_dir()
        safe_name = _safe_filename(original_filename)
        stored_name = f"ngo_{profile['id']}_{document_type.replace(' ', '_')}_{int(time.time())}{ext}"
        file_path = _UPLOAD_DIR / stored_name
        file_path.write_bytes(file_bytes)

        conn.execute(
            """INSERT INTO NGODocuments
               (ngo_profile_id, document_type, file_path, original_filename,
                verification_status, uploaded_at)
               VALUES (?, ?, ?, ?, 'pending', datetime('now'))""",
            (profile["id"], document_type, str(file_path), safe_name),
        )
        conn.commit()
        return True, "NGO document uploaded successfully and is pending admin review."
    except sqlite3.Error as exc:
        logger.error("upload_ngo_document: %s", exc)
        return False, "Database error while uploading NGO document."
    finally:
        conn.close()


def get_documents_for_ngo(ngo_user_id: int) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT d.* FROM NGODocuments d
               JOIN NGOProfiles n ON n.id=d.ngo_profile_id
               WHERE n.user_id=? ORDER BY d.uploaded_at DESC""",
            (ngo_user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_documents_for_ngo: %s", exc)
        return []
    finally:
        conn.close()


def get_all_ngo_documents(status: str | None = None) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        sql = """SELECT d.*, n.organization_name, n.user_id AS ngo_user_id, u.email AS ngo_email
                 FROM NGODocuments d
                 JOIN NGOProfiles n ON n.id=d.ngo_profile_id
                 JOIN Users u ON u.id=n.user_id"""
        params: list[Any] = []
        if status:
            sql += " WHERE d.verification_status=?"
            params.append(status)
        sql += " ORDER BY d.uploaded_at DESC"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_all_ngo_documents: %s", exc)
        return []
    finally:
        conn.close()


def verify_ngo_document(document_id: int, admin_user_id: int, notes: str = "") -> tuple[bool, str]:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT d.id, d.document_type, n.user_id FROM NGODocuments d
               JOIN NGOProfiles n ON n.id=d.ngo_profile_id WHERE d.id=?""",
            (document_id,),
        ).fetchone()
        if not row:
            return False, "NGO document not found."
        conn.execute(
            """UPDATE NGODocuments
               SET verification_status='verified', admin_notes=?, reviewed_at=datetime('now'), reviewed_by=?
               WHERE id=?""",
            ((notes or "").strip(), admin_user_id, document_id),
        )
        conn.commit()
        create_notification(
            user_id=row["user_id"], title="NGO document verified",
            message=f"Your NGO {row['document_type']} document has been verified by admin.",
            notification_type="document_verified", related_entity_type="ngo_document",
            related_entity_id=document_id,
        )
        return True, "NGO document verified."
    except sqlite3.Error as exc:
        logger.error("verify_ngo_document: %s", exc)
        return False, "Database error while verifying NGO document."
    finally:
        conn.close()


def reject_ngo_document(document_id: int, admin_user_id: int, notes: str) -> tuple[bool, str]:
    notes = (notes or "").strip()
    if not notes:
        return False, "Rejection notes are required."
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT d.id, d.document_type, n.user_id FROM NGODocuments d
               JOIN NGOProfiles n ON n.id=d.ngo_profile_id WHERE d.id=?""",
            (document_id,),
        ).fetchone()
        if not row:
            return False, "NGO document not found."
        conn.execute(
            """UPDATE NGODocuments
               SET verification_status='rejected', admin_notes=?, reviewed_at=datetime('now'), reviewed_by=?
               WHERE id=?""",
            (notes, admin_user_id, document_id),
        )
        conn.commit()
        create_notification(
            user_id=row["user_id"], title="NGO document rejected",
            message=f"Your NGO {row['document_type']} document was rejected. Notes: {notes}",
            notification_type="document_rejected", related_entity_type="ngo_document",
            related_entity_id=document_id,
        )
        return True, "NGO document rejected."
    except sqlite3.Error as exc:
        logger.error("reject_ngo_document: %s", exc)
        return False, "Database error while rejecting NGO document."
    finally:
        conn.close()


def get_ngo_document(document_id: int) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT d.*, n.organization_name, n.user_id AS ngo_user_id, u.email AS ngo_email
               FROM NGODocuments d
               JOIN NGOProfiles n ON n.id=d.ngo_profile_id
               JOIN Users u ON u.id=n.user_id WHERE d.id=?""",
            (document_id,),
        ).fetchone()
        return _row_dict(row)
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def process_ngo_document_ocr(document_id: int) -> tuple[bool, str]:
    doc = get_ngo_document(document_id)
    if not doc:
        return False, "NGO document not found."
    ok, text_or_error = extract_text_from_document(doc.get("file_path") or "")
    conn = get_connection()
    try:
        if ok:
            extracted = clean_extracted_text(text_or_error)
            conn.execute(
                """UPDATE NGODocuments SET extracted_text=?, ocr_status='processed',
                   ocr_error=NULL, analyzed_at=datetime('now') WHERE id=?""",
                (extracted, document_id),
            )
            conn.commit()
            create_notification(
                user_id=doc.get("ngo_user_id"), title="NGO document OCR completed",
                message=f"OCR processing completed for your {doc.get('document_type') or 'NGO'} document.",
                notification_type="ocr_completed", related_entity_type="ngo_document",
                related_entity_id=document_id,
            )
            return True, "OCR completed successfully."
        conn.execute(
            """UPDATE NGODocuments SET ocr_status='failed', ocr_error=?, analyzed_at=datetime('now')
               WHERE id=?""",
            (truncate_text(text_or_error, 500), document_id),
        )
        conn.commit()
        return False, text_or_error
    except sqlite3.Error:
        return False, "Database error while saving OCR result."
    finally:
        conn.close()


def generate_ngo_document_ai_summary(document_id: int) -> tuple[bool, str]:
    doc = get_ngo_document(document_id)
    if not doc:
        return False, "NGO document not found."
    extracted = (doc.get("extracted_text") or "").strip()
    if not extracted:
        return False, "Run OCR before generating AI summary."
    payload = generate_document_content_summary(extracted, doc.get("document_type") or "NGO Document")
    if not payload.get("success"):
        return False, payload.get("response") or "AI summary temporarily unavailable."
    summary = (payload.get("response") or "").strip()
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE NGODocuments SET ai_summary=?, analyzed_at=datetime('now') WHERE id=?",
            (summary, document_id),
        )
        conn.commit()
        create_notification(
            user_id=doc.get("ngo_user_id"), title="NGO document AI summary ready",
            message=f"An assistive AI summary is ready for your {doc.get('document_type') or 'NGO'} document.",
            notification_type="ai_summary_ready", related_entity_type="ngo_document",
            related_entity_id=document_id,
        )
        return True, summary
    except sqlite3.Error:
        return False, "Database error while saving AI summary."
    finally:
        conn.close()
