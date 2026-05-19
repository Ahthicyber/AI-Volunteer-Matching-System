"""
documents/document_analysis_service.py
──────────────────────────────────────
Database-backed OCR and optional AI document content summary service.

Admin verification remains manual. OCR and AI summaries are assistive only and
must never approve/reject documents.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from db.database import get_connection
from documents.ocr_service import extract_text_from_document
from documents.document_utils import clean_extracted_text, safe_text_preview, truncate_text
from ai.ai_service import generate_document_content_summary
from notifications.notification_service import create_notification


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def get_document_analysis(document_id: int) -> dict[str, Any] | None:
    """Return one document record with OCR/AI analysis fields."""
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT d.*, vp.full_name AS volunteer_name, vp.user_id AS user_id, u.email AS volunteer_email
               FROM VolunteerDocuments d
               JOIN VolunteerProfiles vp ON vp.id = d.volunteer_profile_id
               JOIN Users u ON u.id = vp.user_id
               WHERE d.id=?""",
            (document_id,),
        ).fetchone()
        return _row_to_dict(row)
    except sqlite3.Error:
        return None
    finally:
        conn.close()


def process_document_ocr(document_id: int) -> tuple[bool, str]:
    """Run OCR for one document and persist extracted text/status safely."""
    document = get_document_analysis(document_id)
    if not document:
        return False, "Document not found."

    file_path = document.get("file_path") or ""
    ok, text_or_error = extract_text_from_document(file_path)

    conn = get_connection()
    try:
        if ok:
            extracted_text = clean_extracted_text(text_or_error)
            conn.execute(
                """UPDATE VolunteerDocuments
                   SET extracted_text=?, ocr_status='processed', ocr_error=NULL,
                       analyzed_at=datetime('now')
                   WHERE id=?""",
                (extracted_text, document_id),
            )
            conn.commit()
            create_notification(
                user_id=document.get("user_id"),
                title="OCR processing completed",
                message=f"OCR processing completed for your {document.get('document_type') or 'document'} document.",
                notification_type="ocr_completed",
                related_entity_type="volunteer_document",
                related_entity_id=document_id,
            )
            return True, "OCR completed successfully."

        conn.execute(
            """UPDATE VolunteerDocuments
               SET ocr_status='failed', ocr_error=?, analyzed_at=datetime('now')
               WHERE id=?""",
            (truncate_text(text_or_error, 500), document_id),
        )
        conn.commit()
        return False, text_or_error
    except sqlite3.Error:
        return False, "Database error while saving OCR results."
    finally:
        conn.close()


def generate_document_ai_summary(document_id: int) -> tuple[bool, str]:
    """Generate and persist an optional AI summary from OCR extracted text."""
    document = get_document_analysis(document_id)
    if not document:
        return False, "Document not found."

    extracted_text = (document.get("extracted_text") or "").strip()
    if not extracted_text:
        return False, "Run OCR before generating an AI summary."

    payload = generate_document_content_summary(
        extracted_text=extracted_text,
        document_type=document.get("document_type") or "Document",
    )
    if not payload.get("success"):
        return False, payload.get("response") or "AI summary temporarily unavailable."

    summary = payload.get("response", "").strip()
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE VolunteerDocuments
               SET ai_summary=?, analyzed_at=datetime('now')
               WHERE id=?""",
            (summary, document_id),
        )
        conn.commit()
        create_notification(
            user_id=document.get("user_id"),
            title="AI document summary ready",
            message=f"An assistive AI summary is ready for the {document.get('document_type') or 'document'} document.",
            notification_type="ai_summary_ready",
            related_entity_type="volunteer_document",
            related_entity_id=document_id,
        )
        return True, summary
    except sqlite3.Error:
        return False, "Database error while saving AI summary."
    finally:
        conn.close()


def get_safe_extracted_preview(document_id: int, limit: int = 1800) -> str:
    """Convenience helper for admin UI previews."""
    document = get_document_analysis(document_id)
    if not document:
        return ""
    return safe_text_preview(document.get("extracted_text"), limit=limit)
