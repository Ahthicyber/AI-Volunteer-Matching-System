"""
applications/application_service.py
─────────────────────────────────────
Volunteer application management — Phase 7.

Public API
----------
    apply_to_event(volunteer_user_id, event_id, volunteer_note)   → (bool, str)
    get_applications_for_volunteer(volunteer_user_id)             → list[dict]
    cancel_application(application_id, volunteer_user_id)        → (bool, str)
    get_applications_for_ngo(ngo_user_id)                        → list[dict]
    update_application_status(application_id, ngo_user_id, ...)  → (bool, str)
    get_application_counts_for_ngo(ngo_user_id)                  → dict
"""

import sqlite3
import logging
from db.database import get_connection
from notifications.notification_service import create_notification

logger = logging.getLogger(__name__)

_VALID_NGO_STATUSES = {"accepted", "rejected"}


# ── 1. apply_to_event ─────────────────────────────────────────────────────────

def apply_to_event(
    volunteer_user_id: int,
    event_id: int,
    volunteer_note: str = "",
) -> tuple[bool, str]:
    """
    Submit a volunteer application.

    Guards:
    - Volunteer must have a profile.
    - Event must exist and be approved.
    - No duplicate applications.
    - Saves the current match_score from MatchScores if available.
    """
    conn = get_connection()
    try:
        # Get volunteer profile
        vol_profile = conn.execute(
            "SELECT id FROM VolunteerProfiles WHERE user_id = ?",
            (volunteer_user_id,),
        ).fetchone()
        if not vol_profile:
            return False, "You must complete your volunteer profile before applying."
        vol_profile_id = vol_profile["id"]

        # Verify event exists and is approved
        event = conn.execute(
            "SELECT id, status, title FROM Events WHERE id = ?", (event_id,)
        ).fetchone()
        if not event:
            return False, "Event not found."
        if event["status"] != "approved":
            return False, "You can only apply to approved events."

        # Duplicate check
        existing = conn.execute(
            "SELECT id, status FROM Applications WHERE volunteer_profile_id=? AND event_id=?",
            (vol_profile_id, event_id),
        ).fetchone()
        if existing:
            status = existing["status"]
            if status == "cancelled":
                return False, "You previously cancelled this application. Please contact the NGO directly."
            return False, f"You have already applied to this event (status: {status})."

        # Fetch match score if already calculated
        score_row = conn.execute(
            "SELECT final_score FROM MatchScores WHERE volunteer_profile_id=? AND event_id=?",
            (vol_profile_id, event_id),
        ).fetchone()
        match_score = score_row["final_score"] if score_row else None

        conn.execute(
            """
            INSERT INTO Applications
                (volunteer_profile_id, event_id, match_score, status,
                 volunteer_note, applied_at)
            VALUES (?, ?, ?, 'pending', ?, datetime('now'))
            """,
            (vol_profile_id, event_id, match_score, (volunteer_note or "").strip()),
        )
        conn.commit()
        logger.info("Application: user_id=%s → event_id=%s", volunteer_user_id, event_id)
        return True, f"Successfully applied to \"{event['title']}\"!"

    except sqlite3.IntegrityError:
        return False, "You have already applied to this event."
    except sqlite3.Error as exc:
        logger.error("apply_to_event error: %s", exc)
        return False, "A database error occurred. Please try again."
    finally:
        conn.close()


# ── 2. get_applications_for_volunteer ─────────────────────────────────────────

def get_applications_for_volunteer(volunteer_user_id: int) -> list[dict]:
    """Return all applications by this volunteer with event + NGO details."""
    conn = get_connection()
    try:
        vol = conn.execute(
            "SELECT id FROM VolunteerProfiles WHERE user_id=?", (volunteer_user_id,)
        ).fetchone()
        if not vol:
            return []

        rows = conn.execute(
            """
            SELECT  a.id,
                    a.status,
                    a.match_score,
                    a.volunteer_note,
                    a.ngo_response,
                    a.applied_at,
                    a.reviewed_at,
                    e.id         AS event_id,
                    e.title      AS event_title,
                    e.city       AS event_city,
                    e.event_date,
                    e.event_time,
                    e.mode,
                    e.cause_area,
                    e.experience_level,
                    n.organization_name
            FROM    Applications a
            JOIN    Events       e ON e.id = a.event_id
            JOIN    NGOProfiles  n ON n.id = e.ngo_profile_id
            WHERE   a.volunteer_profile_id = ?
            ORDER BY a.applied_at DESC
            """,
            (vol["id"],),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_applications_for_volunteer error: %s", exc)
        return []
    finally:
        conn.close()


# ── 3. cancel_application ─────────────────────────────────────────────────────

def cancel_application(
    application_id: int, volunteer_user_id: int
) -> tuple[bool, str]:
    """Cancel a pending application. Only the owner can cancel; only pending allowed."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT a.id, a.status, a.volunteer_profile_id
            FROM   Applications a
            JOIN   VolunteerProfiles vp ON vp.id = a.volunteer_profile_id
            WHERE  a.id = ? AND vp.user_id = ?
            """,
            (application_id, volunteer_user_id),
        ).fetchone()

        if not row:
            return False, "Application not found or you do not own it."
        if row["status"] != "pending":
            return False, f"Only pending applications can be cancelled (current: {row['status']})."

        conn.execute(
            "UPDATE Applications SET status='cancelled' WHERE id=?",
            (application_id,),
        )
        conn.commit()
        logger.info("Application %s cancelled by user_id=%s", application_id, volunteer_user_id)
        return True, "Application cancelled successfully."
    except sqlite3.Error as exc:
        logger.error("cancel_application error: %s", exc)
        return False, "A database error occurred."
    finally:
        conn.close()


# ── 4. get_applications_for_ngo ───────────────────────────────────────────────

def get_applications_for_ngo(ngo_user_id: int) -> list[dict]:
    """Return applications for events owned by this NGO's profile."""
    conn = get_connection()
    try:
        ngo = conn.execute(
            "SELECT id FROM NGOProfiles WHERE user_id=?", (ngo_user_id,)
        ).fetchone()
        if not ngo:
            return []

        rows = conn.execute(
            """
            SELECT  a.id,
                    a.status,
                    a.match_score,
                    a.volunteer_note,
                    a.ngo_response,
                    a.applied_at,
                    a.reviewed_at,
                    e.id    AS event_id,
                    e.title AS event_title,
                    e.city  AS event_city,
                    e.event_date,
                    e.event_time,
                    vp.full_name     AS volunteer_name,
                    vp.city          AS volunteer_city,
                    vp.skills        AS volunteer_skills,
                    vp.experience_level,
                    vp.preferred_mode,
                    u.email          AS volunteer_email
            FROM    Applications   a
            JOIN    Events         e  ON e.id  = a.event_id
            JOIN    VolunteerProfiles vp ON vp.id = a.volunteer_profile_id
            JOIN    Users          u  ON u.id  = vp.user_id
            WHERE   e.ngo_profile_id = ?
            ORDER BY a.applied_at DESC
            """,
            (ngo["id"],),
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_applications_for_ngo error: %s", exc)
        return []
    finally:
        conn.close()


# ── 5. update_application_status ─────────────────────────────────────────────

def update_application_status(
    application_id: int,
    ngo_user_id: int,
    status: str,
    ngo_response: str = "",
) -> tuple[bool, str]:
    """
    Accept or reject an application.

    Guards:
    - NGO can only update applications for its own events.
    - Allowed transitions: pending → accepted | rejected.
    - Rejection requires ngo_response.
    """
    status = status.strip().lower()
    if status not in _VALID_NGO_STATUSES:
        return False, f"Invalid status '{status}'. Use 'accepted' or 'rejected'."

    if status == "rejected" and not (ngo_response or "").strip():
        return False, "A response/reason is required when rejecting an application."

    conn = get_connection()
    try:
        # Verify ownership: app → event → ngo_profile → ngo user
        row = conn.execute(
            """
            SELECT  a.id, a.status, e.title AS event_title, vp.user_id AS volunteer_user_id
            FROM    Applications  a
            JOIN    Events        e  ON e.id = a.event_id
            JOIN    NGOProfiles   n  ON n.id = e.ngo_profile_id
            JOIN    VolunteerProfiles vp ON vp.id = a.volunteer_profile_id
            WHERE   a.id = ? AND n.user_id = ?
            """,
            (application_id, ngo_user_id),
        ).fetchone()

        if not row:
            return False, "Application not found or you do not have permission."
        if row["status"] not in ("pending",):
            return False, f"Cannot update application with status '{row['status']}'."

        conn.execute(
            """
            UPDATE Applications SET
                status       = ?,
                ngo_response = ?,
                reviewed_at  = datetime('now')
            WHERE id = ?
            """,
            (status, (ngo_response or "").strip(), application_id),
        )
        conn.commit()
        verb = "accepted" if status == "accepted" else "rejected"
        logger.info("Application %s %s by ngo_user_id=%s", application_id, verb, ngo_user_id)
        create_notification(
            user_id=row["volunteer_user_id"],
            title=f"Application {verb}",
            message=f"Your application for {row['event_title']} has been {verb}." + ((f" NGO response: {(ngo_response or '').strip()}") if (ngo_response or "").strip() else ""),
            notification_type=("application_accepted" if status == "accepted" else "application_rejected"),
            related_entity_type="application",
            related_entity_id=application_id,
        )
        return True, f"Application {verb} successfully."
    except sqlite3.Error as exc:
        logger.error("update_application_status error: %s", exc)
        return False, "A database error occurred."
    finally:
        conn.close()


# ── 6. get_application_counts_for_ngo ────────────────────────────────────────

def get_application_counts_for_ngo(ngo_user_id: int) -> dict:
    """Return application status counts across all events owned by this NGO."""
    conn = get_connection()
    try:
        ngo = conn.execute(
            "SELECT id FROM NGOProfiles WHERE user_id=?", (ngo_user_id,)
        ).fetchone()
        if not ngo:
            return {"total": 0, "pending": 0, "accepted": 0, "rejected": 0, "cancelled": 0}

        rows = conn.execute(
            """
            SELECT a.status, COUNT(*) as cnt
            FROM   Applications a
            JOIN   Events e ON e.id = a.event_id
            WHERE  e.ngo_profile_id = ?
            GROUP BY a.status
            """,
            (ngo["id"],),
        ).fetchall()

        counts = {"total": 0, "pending": 0, "accepted": 0, "rejected": 0, "cancelled": 0}
        for r in rows:
            s = r["status"]
            if s in counts:
                counts[s] = r["cnt"]
                counts["total"] += r["cnt"]
        return counts
    except sqlite3.Error as exc:
        logger.error("get_application_counts_for_ngo error: %s", exc)
        return {"total": 0, "pending": 0, "accepted": 0, "rejected": 0, "cancelled": 0}
    finally:
        conn.close()


# ── Helper: get application status for a specific volunteer + event ───────────

def get_application_status(volunteer_user_id: int, event_id: int) -> dict | None:
    """
    Return the application row (id, status, ngo_response) for this
    volunteer/event pair, or None if no application exists.
    """
    conn = get_connection()
    try:
        vol = conn.execute(
            "SELECT id FROM VolunteerProfiles WHERE user_id=?", (volunteer_user_id,)
        ).fetchone()
        if not vol:
            return None
        row = conn.execute(
            "SELECT id, status, ngo_response, applied_at FROM Applications "
            "WHERE volunteer_profile_id=? AND event_id=?",
            (vol["id"], event_id),
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        logger.error("get_application_status error: %s", exc)
        return None
    finally:
        conn.close()
