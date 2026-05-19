"""
events/event_service.py — Phase 8.5
Extended with new event fields: required_gender, min/max age, education, detailed_location.
"""

import sqlite3, logging
from db.database import get_connection
from notifications.notification_service import create_notification

logger = logging.getLogger(__name__)
_EDITABLE = {"pending","rejected"}


def _validate(**kw) -> tuple[bool, str]:
    required = ["title","description","required_skills","city","event_date","event_time",
                "cause_area","experience_level","mode"]
    labels   = {"title":"Event title","description":"Description","required_skills":"Required skills",
                "city":"City","event_date":"Event date","event_time":"Event time",
                "cause_area":"Cause area","experience_level":"Experience level","mode":"Mode"}
    for f in required:
        if not (kw.get(f) or "").strip():
            return False, f"{labels.get(f,f)} is required."
    try:
        cap = int(kw.get("capacity",0))
        if cap < 1: return False, "Capacity must be at least 1."
    except (TypeError, ValueError):
        return False, "Capacity must be a valid number."
    mn = int(kw.get("minimum_age",0) or 0)
    mx = int(kw.get("maximum_age",100) or 100)
    if mn > mx: return False, "Minimum age cannot exceed maximum age."
    return True, ""


def create_event(
    ngo_profile_id: int, title: str, description: str,
    required_skills: str, city: str, event_date: str, event_time: str,
    duration_hours, capacity: int, cause_area: str,
    experience_level: str, mode: str,
    required_gender: str = "Anyone", minimum_age: int = 0,
    maximum_age: int = 100, required_education: str = "Anyone",
    detailed_location: str = "",
) -> tuple[bool, str]:
    ok, msg = _validate(title=title, description=description, required_skills=required_skills,
                        city=city, event_date=event_date, event_time=event_time,
                        cause_area=cause_area, experience_level=experience_level,
                        mode=mode, capacity=capacity,
                        minimum_age=minimum_age, maximum_age=maximum_age)
    if not ok: return False, msg
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO Events
               (ngo_profile_id, title, description, required_skills, city,
                detailed_location, event_date, event_time, duration_hours,
                capacity, cause_area, experience_level, mode,
                required_gender, minimum_age, maximum_age, required_education,
                status, rejection_reason, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending',NULL,
                       datetime('now'),datetime('now'))""",
            (
                ngo_profile_id,
                title.strip(), description.strip(), required_skills.strip(),
                city.strip(), (detailed_location or "").strip(),
                event_date.strip(), event_time.strip(),
                duration_hours, int(capacity),
                cause_area.strip(), experience_level.strip(), mode.strip(),
                required_gender or "Anyone",
                int(minimum_age or 0), int(maximum_age or 100),
                required_education or "Anyone",
            ),
        )
        conn.commit()
        logger.info("Event created: '%s' by ngo_profile_id=%s", title, ngo_profile_id)
        return True, "Event submitted for admin approval."
    except sqlite3.Error as exc:
        logger.error("create_event: %s", exc); return False, "A database error occurred."
    finally:
        conn.close()


def update_event(
    event_id: int, ngo_profile_id: int, title: str, description: str,
    required_skills: str, city: str, event_date: str, event_time: str,
    duration_hours, capacity: int, cause_area: str,
    experience_level: str, mode: str,
    required_gender: str = "Anyone", minimum_age: int = 0,
    maximum_age: int = 100, required_education: str = "Anyone",
    detailed_location: str = "",
) -> tuple[bool, str]:
    ok, msg = _validate(title=title, description=description, required_skills=required_skills,
                        city=city, event_date=event_date, event_time=event_time,
                        cause_area=cause_area, experience_level=experience_level,
                        mode=mode, capacity=capacity,
                        minimum_age=minimum_age, maximum_age=maximum_age)
    if not ok: return False, msg
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id,ngo_profile_id,status FROM Events WHERE id=?", (event_id,)
        ).fetchone()
        if not row: return False, "Event not found."
        if row["ngo_profile_id"] != ngo_profile_id: return False, "Permission denied."
        if row["status"] not in _EDITABLE: return False, f"Events with status '{row['status']}' cannot be edited."
        conn.execute(
            """UPDATE Events SET
               title=?,description=?,required_skills=?,city=?,
               detailed_location=?,event_date=?,event_time=?,duration_hours=?,
               capacity=?,cause_area=?,experience_level=?,mode=?,
               required_gender=?,minimum_age=?,maximum_age=?,required_education=?,
               status='pending',rejection_reason=NULL,updated_at=datetime('now')
               WHERE id=?""",
            (title.strip(), description.strip(), required_skills.strip(), city.strip(),
             (detailed_location or "").strip(), event_date.strip(), event_time.strip(),
             duration_hours, int(capacity), cause_area.strip(), experience_level.strip(),
             mode.strip(), required_gender or "Anyone", int(minimum_age or 0),
             int(maximum_age or 100), required_education or "Anyone", event_id),
        )
        conn.commit()
        return True, "Event updated and resubmitted for review."
    except sqlite3.Error as exc:
        logger.error("update_event: %s", exc); return False, "A database error occurred."
    finally:
        conn.close()


def get_events_by_ngo(ngo_profile_id: int) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM Events WHERE ngo_profile_id=? ORDER BY created_at DESC",
            (ngo_profile_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_events_by_ngo: %s", exc); return []
    finally:
        conn.close()


def get_event_by_id(event_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT e.*, n.organization_name, u.email AS admin_email
               FROM Events e JOIN NGOProfiles n ON n.id=e.ngo_profile_id
               LEFT JOIN Users u ON u.id=e.reviewed_by WHERE e.id=?""",
            (event_id,)
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        logger.error("get_event_by_id: %s", exc); return None
    finally:
        conn.close()


def get_events_by_status(status: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT e.*, n.organization_name, u.email AS admin_email
               FROM Events e JOIN NGOProfiles n ON n.id=e.ngo_profile_id
               LEFT JOIN Users u ON u.id=e.reviewed_by
               WHERE e.status=? ORDER BY e.created_at DESC""",
            (status,)
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_events_by_status: %s", exc); return []
    finally:
        conn.close()


def get_approved_events() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT e.*, n.organization_name, n.city AS ngo_city
               FROM Events e JOIN NGOProfiles n ON n.id=e.ngo_profile_id
               WHERE e.status='approved' ORDER BY e.created_at DESC""",
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_approved_events: %s", exc); return []
    finally:
        conn.close()


def approve_event(event_id: int, admin_user_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        event_row = conn.execute("""SELECT e.id, e.title, n.user_id FROM Events e JOIN NGOProfiles n ON n.id=e.ngo_profile_id WHERE e.id=?""", (event_id,)).fetchone()
        if not event_row:
            return False, "Event not found."
        conn.execute(
            "UPDATE Events SET status='approved',rejection_reason=NULL,"
            "reviewed_at=datetime('now'),reviewed_by=? WHERE id=?",
            (admin_user_id, event_id),
        )
        conn.commit()
        create_notification(
            user_id=event_row["user_id"],
            title="Event approved",
            message=f"Your event {event_row['title']} has been approved and is visible to volunteers.",
            notification_type="event_approved",
            related_entity_type="event",
            related_entity_id=event_id,
        )
        return True, "Event approved."
    except sqlite3.Error as exc:
        logger.error("approve_event: %s", exc); return False, "Database error."
    finally:
        conn.close()


def reject_event(event_id: int, admin_user_id: int, reason: str) -> tuple[bool, str]:
    reason = (reason or "").strip()
    if not reason: return False, "A rejection reason is required."
    conn = get_connection()
    try:
        event_row = conn.execute("""SELECT e.id, e.title, n.user_id FROM Events e JOIN NGOProfiles n ON n.id=e.ngo_profile_id WHERE e.id=?""", (event_id,)).fetchone()
        if not event_row:
            return False, "Event not found."
        conn.execute(
            "UPDATE Events SET status='rejected',rejection_reason=?,"
            "reviewed_at=datetime('now'),reviewed_by=? WHERE id=?",
            (reason, admin_user_id, event_id),
        )
        conn.commit()
        create_notification(
            user_id=event_row["user_id"],
            title="Event rejected",
            message=f"Your event {event_row['title']} was rejected. Reason: {reason}",
            notification_type="event_rejected",
            related_entity_type="event",
            related_entity_id=event_id,
        )
        return True, "Event rejected."
    except sqlite3.Error as exc:
        logger.error("reject_event: %s", exc); return False, "Database error."
    finally:
        conn.close()


def delete_event(event_id: int) -> tuple[bool, str]:
    conn = get_connection()
    try:
        if not conn.execute("SELECT id FROM Events WHERE id=?", (event_id,)).fetchone():
            return False, "Event not found."
        conn.execute("DELETE FROM Events WHERE id=?", (event_id,))
        conn.commit()
        return True, "Event deleted."
    except sqlite3.Error as exc:
        logger.error("delete_event: %s", exc); return False, "Database error."
    finally:
        conn.close()
