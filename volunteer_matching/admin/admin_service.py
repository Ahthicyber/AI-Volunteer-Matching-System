"""
admin/admin_service.py
───────────────────────
Admin-side NGO verification + event approval service — Phase 5.

Public API
----------
    get_ngos_by_status(status)                    → list[dict]
    approve_ngo(profile_id, admin_user_id)        → (bool, str)
    reject_ngo(profile_id, admin_user_id, reason) → (bool, str)

Event functions now live in events/event_service.py.
"""

import sqlite3
import logging
from db.database import get_connection
from notifications.notification_service import create_notification

logger = logging.getLogger(__name__)

_VALID_STATUSES = {"pending", "approved", "rejected"}


def get_ngos_by_status(status: str) -> list[dict]:
    if status not in _VALID_STATUSES:
        return []
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT  n.*, u.email AS ngo_email, a.email AS reviewer_email
            FROM    NGOProfiles n
            JOIN    Users u ON u.id = n.user_id
            LEFT JOIN Users a ON a.id = n.reviewed_by
            WHERE   n.verification_status = ?
            ORDER BY n.submitted_at DESC
            """,
            (status,),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_ngos_by_status error: %s", exc)
        return []
    finally:
        conn.close()


def approve_ngo(profile_id: int, admin_user_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        ngo_row = conn.execute("SELECT id, user_id, organization_name FROM NGOProfiles WHERE id=?", (profile_id,)).fetchone()
        if not ngo_row:
            return False, "NGO profile not found."
        conn.execute(
            """
            UPDATE NGOProfiles SET
                verification_status = 'approved',
                rejection_reason    = NULL,
                reviewed_at         = datetime('now'),
                reviewed_by         = ?
            WHERE id = ?
            """,
            (admin_user_id, profile_id),
        )
        conn.commit()
        create_notification(
            user_id=ngo_row["user_id"],
            title="NGO profile approved",
            message=f"Your NGO profile {ngo_row['organization_name'] or ''} has been approved. You can now manage events.",
            notification_type="ngo_approved",
            related_entity_type="ngo_profile",
            related_entity_id=profile_id,
        )
        return True, "NGO approved successfully."
    except sqlite3.Error as exc:
        logger.error("approve_ngo error: %s", exc)
        return False, "A database error occurred."
    finally:
        conn.close()


def reject_ngo(profile_id: int, admin_user_id: int, reason: str) -> tuple[bool, str]:
    reason = (reason or "").strip()
    if not reason:
        return False, "A rejection reason is required."
    conn = get_connection()
    try:
        ngo_row = conn.execute("SELECT id, user_id, organization_name FROM NGOProfiles WHERE id=?", (profile_id,)).fetchone()
        if not ngo_row:
            return False, "NGO profile not found."
        conn.execute(
            """
            UPDATE NGOProfiles SET
                verification_status = 'rejected',
                rejection_reason    = ?,
                reviewed_at         = datetime('now'),
                reviewed_by         = ?
            WHERE id = ?
            """,
            (reason, admin_user_id, profile_id),
        )
        conn.commit()
        create_notification(
            user_id=ngo_row["user_id"],
            title="NGO profile rejected",
            message=f"Your NGO profile {ngo_row['organization_name'] or ''} was rejected. Reason: {reason}",
            notification_type="ngo_rejected",
            related_entity_type="ngo_profile",
            related_entity_id=profile_id,
        )
        return True, "NGO rejected."
    except sqlite3.Error as exc:
        logger.error("reject_ngo error: %s", exc)
        return False, "A database error occurred."
    finally:
        conn.close()
