"""
ngo/ngo_service.py — Phase 8.5
Extended with new profile fields; critical-field change detection for re-verification.
"""

import sqlite3, logging
from db.database import get_connection

logger = logging.getLogger(__name__)

_CRITICAL_FIELDS = {"organization_name","registration_number","address"}


def get_ngo_profile(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT n.*, u.email AS ngo_email FROM NGOProfiles n "
            "JOIN Users u ON u.id = n.user_id WHERE n.user_id=?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.Error as exc:
        logger.error("get_ngo_profile: %s", exc); return None
    finally:
        conn.close()


def get_ngo_verification_status(user_id: int) -> dict:
    profile = get_ngo_profile(user_id)
    if not profile:
        return {"status":"not_submitted","rejection_reason":None,
                "submitted_at":None,"reviewed_at":None}
    return {
        "status":           profile.get("verification_status","pending"),
        "rejection_reason": profile.get("rejection_reason"),
        "submitted_at":     profile.get("submitted_at"),
        "reviewed_at":      profile.get("reviewed_at"),
    }


def upsert_ngo_profile(
    user_id: int,
    organization_name: str,
    registration_number: str,
    contact_person: str,
    phone: str,
    city: str,
    cause_areas: str,
    description: str,
    website: str,
    address: str = "",
    aim: str = "",
    objectives: str = "",
    services: str = "",
) -> tuple[bool, str]:
    organization_name   = (organization_name  or "").strip()
    registration_number = (registration_number or "").strip()
    contact_person      = (contact_person     or "").strip()
    city                = (city               or "").strip()
    cause_areas         = (cause_areas        or "").strip()
    address             = (address            or "").strip()

    if not organization_name: return False, "Organisation name is required."
    if not contact_person:    return False, "Contact person name is required."
    if not city:              return False, "City is required."
    if not cause_areas:       return False, "Please select at least one cause area."

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id, organization_name, registration_number, address, verification_status "
            "FROM NGOProfiles WHERE user_id=?", (user_id,)
        ).fetchone()

        if not existing:
            conn.execute(
                """INSERT INTO NGOProfiles
                   (user_id, organization_name, registration_number, contact_person,
                    phone, city, address, cause_areas, description, website,
                    aim, objectives, services,
                    verification_status, submitted_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'pending',datetime('now'))""",
                (user_id, organization_name, registration_number, contact_person,
                 phone, city, address, cause_areas, description, website,
                 aim, objectives, services),
            )
            conn.commit()
            return True, "NGO profile submitted for verification."

        # Check if any critical field changed
        ex = dict(existing)
        critical_changed = (
            ex.get("organization_name","")   != organization_name or
            ex.get("registration_number","") != registration_number or
            ex.get("address","")             != address
        )
        new_status = "pending" if critical_changed or ex.get("verification_status") in ("rejected",) else ex.get("verification_status","pending")
        # Always reset to pending on any edit (simpler and safer for review)
        new_status = "pending"

        conn.execute(
            """UPDATE NGOProfiles SET
               organization_name=?, registration_number=?, contact_person=?,
               phone=?, city=?, address=?, cause_areas=?, description=?, website=?,
               aim=?, objectives=?, services=?,
               verification_status=?, rejection_reason=NULL,
               submitted_at=datetime('now'), reviewed_at=NULL, reviewed_by=NULL
               WHERE user_id=?""",
            (organization_name, registration_number, contact_person,
             phone, city, address, cause_areas, description, website,
             aim, objectives, services, new_status, user_id),
        )
        conn.commit()
        return True, "Profile updated and resubmitted for review."
    except sqlite3.Error as exc:
        logger.error("upsert_ngo_profile: %s", exc)
        return False, "A database error occurred."
    finally:
        conn.close()
