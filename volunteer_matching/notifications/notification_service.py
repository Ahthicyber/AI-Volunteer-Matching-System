"""Database-backed in-app notification service.

Notifications are informational only. They do not replace approvals,
verification, recommendation ranking, or any core workflow decision.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any

from db.database import get_connection

logger = logging.getLogger(__name__)

_VALID_TYPES = {
    "ngo_approved", "ngo_rejected", "volunteer_verified", "volunteer_rejected",
    "document_verified", "document_rejected", "event_approved", "event_rejected",
    "application_accepted", "application_rejected", "feedback_received",
    "ocr_completed", "ai_summary_ready", "system",
}


def create_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str,
    related_entity_type: str | None = None,
    related_entity_id: int | None = None,
) -> tuple[bool, str]:
    """Create one notification safely, with lightweight duplicate protection."""
    try:
        uid = int(user_id)
    except Exception:
        return False, "Invalid notification user."
    title = " ".join(str(title or "").split())[:160]
    message = " ".join(str(message or "").split())[:1000]
    ntype = (notification_type or "system").strip()
    if ntype not in _VALID_TYPES:
        ntype = "system"
    if not title or not message:
        return False, "Notification title/message required."

    conn = get_connection()
    try:
        # Prevent duplicate notifications caused by accidental double-clicks/reruns.
        duplicate = conn.execute(
            """
            SELECT id FROM Notifications
            WHERE user_id=? AND notification_type=?
              AND COALESCE(related_entity_type,'') = COALESCE(?, '')
              AND COALESCE(related_entity_id,-1) = COALESCE(?, -1)
              AND title=? AND message=?
            LIMIT 1
            """,
            (uid, ntype, related_entity_type, related_entity_id, title, message),
        ).fetchone()
        if duplicate:
            return True, "Notification already exists."

        conn.execute(
            """
            INSERT INTO Notifications
                (user_id, title, message, notification_type,
                 related_entity_type, related_entity_id, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, datetime('now'))
            """,
            (uid, title, message, ntype, related_entity_type, related_entity_id),
        )
        conn.commit()
        return True, "Notification created."
    except sqlite3.Error as exc:
        logger.error("create_notification: %s", exc)
        return False, "Could not create notification."
    finally:
        conn.close()


def get_notifications_for_user(user_id: int, unread_only: bool = False, limit: int = 20) -> list[dict[str, Any]]:
    """Return latest notifications for one user."""
    conn = get_connection()
    try:
        query = "SELECT * FROM Notifications WHERE user_id=?"
        params: list[Any] = [int(user_id)]
        if unread_only:
            query += " AND is_read=0"
        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 100)))
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    except Exception as exc:
        logger.error("get_notifications_for_user: %s", exc)
        return []
    finally:
        conn.close()


def mark_notification_read(notification_id: int, user_id: int) -> tuple[bool, str]:
    """Mark one notification as read, scoped to the logged-in user."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE Notifications SET is_read=1 WHERE id=? AND user_id=?",
            (int(notification_id), int(user_id)),
        )
        conn.commit()
        return True, "Notification marked as read."
    except Exception as exc:
        logger.error("mark_notification_read: %s", exc)
        return False, "Could not update notification."
    finally:
        conn.close()


def mark_all_notifications_read(user_id: int) -> tuple[bool, str]:
    """Mark all notifications as read for one user."""
    conn = get_connection()
    try:
        conn.execute("UPDATE Notifications SET is_read=1 WHERE user_id=?", (int(user_id),))
        conn.commit()
        return True, "All notifications marked as read."
    except Exception as exc:
        logger.error("mark_all_notifications_read: %s", exc)
        return False, "Could not update notifications."
    finally:
        conn.close()


def get_unread_count(user_id: int) -> int:
    """Return unread notification count for one user."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM Notifications WHERE user_id=? AND is_read=0",
            (int(user_id),),
        ).fetchone()
        return int(row["c"] if row else 0)
    except Exception as exc:
        logger.error("get_unread_count: %s", exc)
        return 0
    finally:
        conn.close()


def get_system_alerts(limit: int = 20) -> list[dict[str, Any]]:
    """Return simple admin-facing system alerts from existing review queues."""
    conn = get_connection()
    alerts: list[dict[str, Any]] = []
    try:
        checks = [
            ("Pending NGO reviews", "SELECT COUNT(*) AS c FROM NGOProfiles WHERE verification_status='pending'"),
            ("Pending volunteer documents", "SELECT COUNT(*) AS c FROM VolunteerDocuments WHERE verification_status='pending'"),
            ("Pending NGO documents", "SELECT COUNT(*) AS c FROM NGODocuments WHERE verification_status='pending'"),
            ("Pending events", "SELECT COUNT(*) AS c FROM Events WHERE status='pending'"),
            ("OCR failures", "SELECT (SELECT COUNT(*) FROM VolunteerDocuments WHERE ocr_status='failed') + (SELECT COUNT(*) FROM NGODocuments WHERE ocr_status='failed') AS c"),
        ]
        for title, sql in checks:
            row = conn.execute(sql).fetchone()
            count = int(row["c"] if row else 0)
            if count > 0:
                alerts.append({"title": title, "message": f"{count} item(s) need attention.", "count": count})
        return alerts[: max(1, int(limit))]
    except sqlite3.Error as exc:
        logger.error("get_system_alerts: %s", exc)
        return []
    finally:
        conn.close()
