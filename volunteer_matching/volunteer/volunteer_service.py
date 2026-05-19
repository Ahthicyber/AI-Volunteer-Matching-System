"""
volunteer/volunteer_service.py — Bugfix
Fix: experience_level options for volunteer profile must NOT include 'Anyone'.
     'Anyone' is reserved for NGO event requirements only.
"""

import sqlite3, logging
from db.database import get_connection
from notifications.notification_service import create_notification

logger = logging.getLogger(__name__)

# Volunteer profile valid values — NO 'Anyone'
VALID_EXPERIENCE = {"Beginner", "Intermediate", "Experienced"}
VALID_MODE       = {"On-site", "Online", "Hybrid"}
VALID_AVAIL      = {"Weekdays", "Weekend", "Flexible"}
VALID_EDU        = {"High School", "Intermediate", "Undergraduate",
                    "Graduate", "Postgraduate", "Other"}
VALID_GENDER     = {"Male", "Female", "Prefer Not To Say"}

_COMPLETENESS_FIELDS = [
    "full_name", "gender", "age", "city", "address", "education",
    "languages", "occupation", "skills", "interests",
    "availability", "experience_level", "preferred_mode", "bio",
]


def get_volunteer_profile(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT v.*, u.email AS volunteer_email "
            "FROM VolunteerProfiles v "
            "JOIN Users u ON u.id = v.user_id "
            "WHERE v.user_id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        logger.error("get_volunteer_profile: %s", exc)
        return None
    finally:
        conn.close()


def calculate_profile_completeness(data: dict) -> int:
    if not data:
        return 0
    filled = 0
    for f in _COMPLETENESS_FIELDS:
        v = data.get(f)
        if v is None:
            continue
        if isinstance(v, str) and v.strip():
            filled += 1
        elif isinstance(v, int) and v > 0:
            filled += 1
    return round(filled / len(_COMPLETENESS_FIELDS) * 100)


def upsert_volunteer_profile(
    user_id: int,
    full_name: str,
    gender: str,
    age,
    address: str,
    city: str,
    education: str,
    languages: str,
    occupation: str,
    skills: str,
    interests: str,
    availability: str,
    experience_level: str,
    preferred_mode: str,
    bio: str,
) -> tuple[bool, str]:

    full_name        = (full_name        or "").strip()
    gender           = (gender           or "").strip()
    address          = (address          or "").strip()
    city             = (city             or "").strip()
    education        = (education        or "").strip()
    languages        = (languages        or "").strip()
    occupation       = (occupation       or "").strip()
    skills           = (skills           or "").strip()
    interests        = (interests        or "").strip()
    availability     = (availability     or "").strip()
    experience_level = (experience_level or "").strip()
    preferred_mode   = (preferred_mode   or "").strip()
    bio              = (bio              or "").strip()

    if not full_name:        return False, "Full name is required."
    if not city:             return False, "City is required."
    if not skills:           return False, "Please select at least one skill."
    if not interests:        return False, "Please select at least one interest."
    if not availability:     return False, "Please select availability."
    if not experience_level: return False, "Experience level is required."
    if not preferred_mode:   return False, "Preferred mode is required."

    # Enforce no 'Anyone' in volunteer profiles
    if experience_level == "Anyone":
        return False, "Please select a specific experience level (Beginner, Intermediate, or Experienced)."

    age_val = None
    if age:
        try:
            age_val = int(age)
            if not (13 <= age_val <= 100):
                return False, "Age must be between 13 and 100."
        except (ValueError, TypeError):
            return False, "Age must be a valid number."

    completeness = calculate_profile_completeness({
        "full_name": full_name, "gender": gender, "age": age_val,
        "address": address, "city": city, "education": education,
        "languages": languages, "occupation": occupation,
        "skills": skills, "interests": interests,
        "availability": availability, "experience_level": experience_level,
        "preferred_mode": preferred_mode, "bio": bio,
    })

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM VolunteerProfiles WHERE user_id=?", (user_id,)
        ).fetchone()

        if not existing:
            conn.execute(
                """INSERT INTO VolunteerProfiles
                   (user_id, full_name, gender, age, address, city, education,
                    languages, occupation, skills, interests, availability,
                    experience_level, preferred_mode, bio,
                    profile_completeness, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))""",
                (user_id, full_name, gender, age_val, address, city, education,
                 languages, occupation, skills, interests, availability,
                 experience_level, preferred_mode, bio, completeness),
            )
            conn.commit()
            return True, f"Profile saved! Completeness: {completeness}%"

        conn.execute(
            """UPDATE VolunteerProfiles SET
               full_name=?, gender=?, age=?, address=?, city=?, education=?,
               languages=?, occupation=?, skills=?, interests=?, availability=?,
               experience_level=?, preferred_mode=?, bio=?,
               profile_completeness=?, updated_at=datetime('now')
               WHERE user_id=?""",
            (full_name, gender, age_val, address, city, education,
             languages, occupation, skills, interests, availability,
             experience_level, preferred_mode, bio, completeness, user_id),
        )
        conn.commit()
        return True, f"Profile updated! Completeness: {completeness}%"

    except sqlite3.Error as exc:
        logger.error("upsert_volunteer_profile: %s", exc)
        return False, "A database error occurred."
    finally:
        conn.close()


def update_verification_status(
    volunteer_user_id: int, status: str, notes: str = ""
) -> tuple[bool, str]:
    valid = {"unverified", "pending", "verified", "rejected"}
    if status not in valid:
        return False, f"Invalid status '{status}'."
    conn = get_connection()
    try:
        vp = conn.execute(
            "SELECT id, full_name FROM VolunteerProfiles WHERE user_id=?", (volunteer_user_id,)
        ).fetchone()
        if not vp:
            return False, "Volunteer profile not found."
        conn.execute(
            "UPDATE VolunteerProfiles SET verification_status=?, "
            "verification_notes=? WHERE user_id=?",
            (status, (notes or "").strip(), volunteer_user_id),
        )
        conn.commit()
        if status in ("verified", "rejected"):
            create_notification(
                user_id=volunteer_user_id,
                title="Volunteer verification updated",
                message=("Your volunteer profile has been verified." if status == "verified" else f"Your volunteer profile was rejected. Notes: {(notes or 'No notes provided.')}") ,
                notification_type=("volunteer_verified" if status == "verified" else "volunteer_rejected"),
                related_entity_type="volunteer_profile",
                related_entity_id=vp["id"],
            )
        return True, f"Verification updated to '{status}'."
    except sqlite3.Error as exc:
        logger.error("update_verification_status: %s", exc)
        return False, "Database error."
    finally:
        conn.close()


def get_all_volunteers_for_admin() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT vp.*, u.email, u.created_at AS registered_at
               FROM VolunteerProfiles vp
               JOIN Users u ON u.id = vp.user_id
               ORDER BY vp.updated_at DESC""",
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_all_volunteers_for_admin: %s", exc)
        return []
    finally:
        conn.close()
