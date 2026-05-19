"""
feedback/feedback_service.py
─────────────────────────────
Post-application feedback management — Phase 8.

Public API
----------
    submit_feedback(application_id, user_id, feedback_from, ...)  → (bool, str)
    get_feedback_for_application(application_id)                  → list[dict]
    has_feedback(application_id, feedback_from)                   → bool
    get_feedback_summary()                                        → dict
"""

import sqlite3
import logging
from db.database import get_connection
from notifications.notification_service import create_notification

logger = logging.getLogger(__name__)

_VALID_FROM    = {"volunteer", "ngo"}
_RELEVANCE_VOL = {"Very Relevant", "Relevant", "Somewhat Relevant", "Not Relevant"}
_RELEVANCE_NGO = {"Very Suitable", "Suitable", "Somewhat Suitable", "Not Suitable"}


# ── 1. submit_feedback ────────────────────────────────────────────────────────

def submit_feedback(
    application_id: int,
    user_id: int,
    feedback_from: str,
    rating: int,
    secondary_rating: int | None,
    attended: bool,
    match_relevance: str,
    comments: str,
) -> tuple[bool, str]:
    """
    Submit feedback for an accepted application.

    Guards
    ------
    - feedback_from must be 'volunteer' or 'ngo'.
    - rating must be 1–5.
    - Only accepted applications can receive feedback.
    - Volunteer may only submit for their own application.
    - NGO may only submit for applications linked to their events.
    - Duplicate feedback from the same side is blocked.
    """
    feedback_from = (feedback_from or "").strip().lower()
    if feedback_from not in _VALID_FROM:
        return False, "feedback_from must be 'volunteer' or 'ngo'."

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return False, "Rating must be a number."
    if not (1 <= rating <= 5):
        return False, "Rating must be between 1 and 5."

    sec = None
    if secondary_rating is not None:
        try:
            sec = int(secondary_rating)
            if not (1 <= sec <= 5):
                return False, "Secondary rating must be between 1 and 5."
        except (TypeError, ValueError):
            return False, "Secondary rating must be a number."

    conn = get_connection()
    try:
        # Load application + ownership info in one query
        app = conn.execute(
            """
            SELECT  a.id, a.status,
                    vp.user_id          AS vol_user_id,
                    e.title             AS event_title,
                    e.ngo_profile_id,
                    n.user_id           AS ngo_user_id
            FROM    Applications  a
            JOIN    VolunteerProfiles vp ON vp.id = a.volunteer_profile_id
            JOIN    Events        e  ON e.id  = a.event_id
            JOIN    NGOProfiles   n  ON n.id  = e.ngo_profile_id
            WHERE   a.id = ?
            """,
            (application_id,),
        ).fetchone()

        if not app:
            return False, "Application not found."
        if app["status"] != "accepted":
            return False, "Feedback is only allowed for accepted applications."

        # Ownership check
        if feedback_from == "volunteer" and app["vol_user_id"] != user_id:
            return False, "You can only submit feedback for your own application."
        if feedback_from == "ngo" and app["ngo_user_id"] != user_id:
            return False, "You can only submit feedback for your own NGO's applications."

        # Duplicate check
        if has_feedback(application_id, feedback_from, conn=conn):
            return False, f"You have already submitted {feedback_from} feedback for this application."

        conn.execute(
            """
            INSERT INTO Feedback
                (application_id, feedback_from, rating, secondary_rating,
                 attended, match_relevance, comments, created_at)
            VALUES (?,?,?,?,?,?,?,datetime('now'))
            """,
            (
                application_id, feedback_from, rating, sec,
                1 if attended else 0,
                (match_relevance or "").strip(),
                (comments or "").strip(),
            ),
        )
        conn.commit()
        logger.info("Feedback submitted: app_id=%s from=%s", application_id, feedback_from)
        target_user_id = app["ngo_user_id"] if feedback_from == "volunteer" else app["vol_user_id"]
        create_notification(
            user_id=target_user_id,
            title="Feedback received",
            message=f"New {feedback_from} feedback was submitted for {app['event_title']}.",
            notification_type="feedback_received",
            related_entity_type="application",
            related_entity_id=application_id,
        )
        return True, "Feedback submitted successfully. Thank you!"

    except sqlite3.IntegrityError:
        return False, "Feedback already submitted for this application."
    except sqlite3.Error as exc:
        logger.error("submit_feedback error: %s", exc)
        return False, "A database error occurred. Please try again."
    finally:
        conn.close()


# ── 2. get_feedback_for_application ───────────────────────────────────────────

def get_feedback_for_application(application_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM Feedback WHERE application_id=? ORDER BY created_at",
            (application_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_feedback_for_application error: %s", exc)
        return []
    finally:
        conn.close()


# ── 3. has_feedback ───────────────────────────────────────────────────────────

def has_feedback(
    application_id: int, feedback_from: str, *, conn=None
) -> bool:
    """Return True if feedback from *feedback_from* already exists."""
    _close = conn is None
    if _close:
        conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM Feedback WHERE application_id=? AND feedback_from=?",
            (application_id, feedback_from),
        ).fetchone()
        return row is not None
    except sqlite3.Error:
        return False
    finally:
        if _close:
            conn.close()


# ── 4. get_feedback_summary ───────────────────────────────────────────────────

def get_feedback_summary() -> dict:
    """Aggregate stats across all feedback rows."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                COUNT(*)                                            AS total_feedback,
                ROUND(AVG(rating), 2)                              AS average_rating,
                ROUND(AVG(secondary_rating), 2)                    AS average_secondary_rating,
                SUM(CASE WHEN feedback_from='volunteer' THEN 1 ELSE 0 END)  AS total_volunteer_feedback,
                SUM(CASE WHEN feedback_from='ngo'       THEN 1 ELSE 0 END)  AS total_ngo_feedback,
                ROUND(AVG(CASE WHEN feedback_from='volunteer' THEN rating END), 2) AS average_volunteer_rating,
                ROUND(AVG(CASE WHEN feedback_from='ngo'       THEN rating END), 2) AS average_ngo_rating
            FROM Feedback
            """
        ).fetchone()
        return dict(rows) if rows else {
            "total_feedback": 0, "average_rating": None,
            "average_secondary_rating": None,
            "total_volunteer_feedback": 0, "total_ngo_feedback": 0,
            "average_volunteer_rating": None, "average_ngo_rating": None,
        }
    except sqlite3.Error as exc:
        logger.error("get_feedback_summary error: %s", exc)
        return {}
    finally:
        conn.close()
