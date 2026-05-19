"""Seed demo accounts and realistic sample data for the VolunteerAI demo.

Safe to run multiple times. Existing demo accounts/data are reused instead of
being duplicated where practical.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from auth.auth_service import hash_password, verify_password  # noqa: E402
from db.database import get_connection  # noqa: E402
from db.schema import initialize_database  # noqa: E402

ADMIN_EMAIL = "admin@volmatch.local"
ADMIN_PASSWORD = "Admin@123"
VOLUNTEER_EMAIL = "volunteer@volmatch.local"
VOLUNTEER_PASSWORD = "Volunteer@123"
NGO_EMAIL = "ngo@volmatch.local"
NGO_PASSWORD = "Ngo@123"


def _get_user_id(conn, email: str) -> int | None:
    row = conn.execute("SELECT id FROM Users WHERE email=?", (email,)).fetchone()
    return int(row["id"]) if row else None


def _ensure_user(conn, email: str, password: str, role: str) -> int:
    """Create or repair a demo user without duplicating accounts."""
    row = conn.execute(
        "SELECT id, password_hash, role FROM Users WHERE email=?",
        (email,),
    ).fetchone()
    if row:
        if row["role"] != role or not verify_password(password, row["password_hash"]):
            conn.execute(
                "UPDATE Users SET password_hash=?, role=?, updated_at=datetime('now') WHERE id=?",
                (hash_password(password), role, row["id"]),
            )
            conn.commit()
        return int(row["id"])

    conn.execute(
        "INSERT INTO Users (email, password_hash, role) VALUES (?, ?, ?)",
        (email, hash_password(password), role),
    )
    conn.commit()
    return int(_get_user_id(conn, email))


def seed_demo_data() -> None:
    initialize_database()
    (ROOT / "uploads").mkdir(exist_ok=True)
    (ROOT / "data" / "models").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "dataset").mkdir(parents=True, exist_ok=True)

    sample_doc = ROOT / "uploads" / "demo_certificate.txt"
    if not sample_doc.exists():
        sample_doc.write_text("Demo certificate placeholder for final-year project testing.\n", encoding="utf-8")

    conn = get_connection()
    try:
        admin_id = _ensure_user(conn, ADMIN_EMAIL, ADMIN_PASSWORD, "admin")
        volunteer_user_id = _ensure_user(conn, VOLUNTEER_EMAIL, VOLUNTEER_PASSWORD, "volunteer")
        ngo_user_id = _ensure_user(conn, NGO_EMAIL, NGO_PASSWORD, "ngo")

        conn.execute(
            """
            INSERT INTO VolunteerProfiles
                (user_id, full_name, gender, age, address, city, education,
                 languages, occupation, skills, interests, availability,
                 experience_level, preferred_mode, bio, profile_completeness,
                 verification_status, verification_notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                 full_name=excluded.full_name,
                 gender=excluded.gender,
                 age=excluded.age,
                 address=excluded.address,
                 city=excluded.city,
                 education=excluded.education,
                 languages=excluded.languages,
                 occupation=excluded.occupation,
                 skills=excluded.skills,
                 interests=excluded.interests,
                 availability=excluded.availability,
                 experience_level=excluded.experience_level,
                 preferred_mode=excluded.preferred_mode,
                 bio=excluded.bio,
                 profile_completeness=excluded.profile_completeness,
                 verification_status=excluded.verification_status,
                 verification_notes=excluded.verification_notes,
                 updated_at=datetime('now')
            """,
            (
                volunteer_user_id,
                "Demo Volunteer",
                "Prefer Not To Say",
                22,
                "Gulshan-e-Iqbal",
                "Karachi",
                "Undergraduate",
                "English, Urdu",
                "Computer Science Student",
                "Teaching, Communication, Event Management, Data Entry",
                "Education, Community Service, Youth Development",
                "Weekend",
                "Intermediate",
                "Hybrid",
                "Motivated student interested in education and community volunteering.",
                95,
                "verified",
                "Demo profile verified for presentation.",
            ),
        )
        volunteer_profile_id = conn.execute(
            "SELECT id FROM VolunteerProfiles WHERE user_id=?", (volunteer_user_id,)
        ).fetchone()["id"]

        conn.execute(
            """
            INSERT INTO NGOProfiles
                (user_id, organization_name, registration_number, contact_person,
                 phone, city, address, aim, objectives, services, cause_areas,
                 description, website, verification_status, submitted_at,
                 reviewed_at, reviewed_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', datetime('now'), datetime('now'), ?, datetime('now'))
            ON CONFLICT(user_id) DO UPDATE SET
                 organization_name=excluded.organization_name,
                 registration_number=excluded.registration_number,
                 contact_person=excluded.contact_person,
                 phone=excluded.phone,
                 city=excluded.city,
                 address=excluded.address,
                 aim=excluded.aim,
                 objectives=excluded.objectives,
                 services=excluded.services,
                 cause_areas=excluded.cause_areas,
                 description=excluded.description,
                 website=excluded.website,
                 verification_status='approved',
                 reviewed_at=datetime('now'),
                 reviewed_by=excluded.reviewed_by,
                 updated_at=datetime('now')
            """,
            (
                ngo_user_id,
                "Demo Community NGO",
                "REG-DEMO-2026",
                "Ayesha Khan",
                "+92-300-0000000",
                "Karachi",
                "Shahrah-e-Faisal, Karachi",
                "Support youth education and community welfare.",
                "Improve access to learning, mentorship, and civic engagement.",
                "Education drives, mentoring sessions, awareness campaigns",
                "Education, Community Service, Youth Development",
                "A demo NGO profile used to showcase the volunteer matching platform.",
                "https://example.org",
                admin_id,
            ),
        )
        ngo_profile_id = conn.execute(
            "SELECT id FROM NGOProfiles WHERE user_id=?", (ngo_user_id,)
        ).fetchone()["id"]

        demo_events = [
            (
                "Weekend Digital Literacy Workshop",
                "Help young learners build basic computer and internet skills.",
                "Teaching, Communication, Computer Skills",
                "Karachi",
                "Community Learning Center",
                "2026-05-20",
                "10:00",
                3.0,
                25,
                "Education",
                "Beginner",
                "On-site",
            ),
            (
                "Online Youth Mentorship Session",
                "Guide students about academic planning and career confidence.",
                "Communication, Mentoring, Presentation",
                "Karachi",
                "Online",
                "2026-05-25",
                "18:00",
                2.0,
                15,
                "Youth Development",
                "Intermediate",
                "Online",
            ),
        ]
        event_ids: list[int] = []
        for event in demo_events:
            existing = conn.execute(
                "SELECT id FROM Events WHERE ngo_profile_id=? AND title=?",
                (ngo_profile_id, event[0]),
            ).fetchone()
            if existing:
                event_ids.append(int(existing["id"]))
                continue
            conn.execute(
                """
                INSERT INTO Events
                    (ngo_profile_id, title, description, required_skills, city,
                     detailed_location, event_date, event_time, duration_hours,
                     capacity, cause_area, experience_level, mode, status,
                     reviewed_at, reviewed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', datetime('now'), ?)
                """,
                (ngo_profile_id, *event, admin_id),
            )
            event_ids.append(int(conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]))

        if event_ids:
            first_event = event_ids[0]
            conn.execute(
                """
                INSERT OR IGNORE INTO Applications
                    (volunteer_profile_id, event_id, match_score, status,
                     volunteer_note, ngo_response, applied_at, reviewed_at)
                VALUES (?, ?, 86.5, 'accepted', ?, ?, datetime('now'), datetime('now'))
                """,
                (
                    volunteer_profile_id,
                    first_event,
                    "I am available on weekends and interested in teaching.",
                    "Accepted for the demo workshop.",
                ),
            )
            app_row = conn.execute(
                "SELECT id FROM Applications WHERE volunteer_profile_id=? AND event_id=?",
                (volunteer_profile_id, first_event),
            ).fetchone()
            if app_row:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO Feedback
                        (application_id, feedback_from, rating, secondary_rating,
                         attended, match_relevance, comments)
                    VALUES (?, 'volunteer', 5, 5, 1, 'High', 'Great match for my skills and availability.')
                    """,
                    (app_row["id"],),
                )

        for event_id in event_ids:
            conn.execute(
                """
                INSERT OR REPLACE INTO MatchScores
                    (volunteer_profile_id, event_id, final_score, skill_score,
                     availability_score, location_score, interest_score,
                     experience_score, mode_score, explanation, calculated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    volunteer_profile_id,
                    event_id,
                    86.5 if event_id == event_ids[0] else 74.0,
                    90.0,
                    80.0,
                    100.0,
                    85.0,
                    70.0,
                    80.0,
                    "Demo deterministic score based on skills, city, availability, interests, experience, and mode.",
                ),
            )

        existing_doc = conn.execute(
            "SELECT id FROM VolunteerDocuments WHERE volunteer_profile_id=? AND original_filename=?",
            (volunteer_profile_id, "demo_certificate.txt"),
        ).fetchone()
        if not existing_doc:
            conn.execute(
                """
                INSERT INTO VolunteerDocuments
                    (volunteer_profile_id, document_type, file_path, original_filename,
                     verification_status, admin_notes, ocr_status)
                VALUES (?, 'Certificate', ?, 'demo_certificate.txt', 'verified', 'Demo document verified.', 'not_processed')
                """,
                (volunteer_profile_id, str(sample_doc.relative_to(ROOT))),
            )

        notifications = [
            (volunteer_user_id, "Welcome to VolunteerAI", "Your demo volunteer account is ready.", "system", "user", volunteer_user_id),
            (volunteer_user_id, "Application accepted", "Your demo application has been accepted.", "application_accepted", "application", 1),
            (ngo_user_id, "NGO approved", "Your demo NGO profile has been approved.", "ngo_approved", "ngo_profile", ngo_profile_id),
            (admin_id, "Demo data seeded", "Demo accounts and sample records are ready for presentation.", "system", "system", None),
        ]
        for note in notifications:
            duplicate = conn.execute(
                """
                SELECT id FROM Notifications
                WHERE user_id=? AND title=? AND message=? AND notification_type=?
                  AND COALESCE(related_entity_type,'') = COALESCE(?, '')
                  AND COALESCE(related_entity_id,-1) = COALESCE(?, -1)
                LIMIT 1
                """,
                note,
            ).fetchone()
            if not duplicate:
                conn.execute(
                    """
                    INSERT INTO Notifications
                        (user_id, title, message, notification_type,
                         related_entity_type, related_entity_id, is_read, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 0, datetime('now'))
                    """,
                    note,
                )

        conn.commit()
        print("Demo data seeded successfully.")
        print("Admin:     admin@volmatch.local / Admin@123")
        print("Volunteer: volunteer@volmatch.local / Volunteer@123")
        print("NGO:       ngo@volmatch.local / Ngo@123")
    finally:
        conn.close()


if __name__ == "__main__":
    seed_demo_data()
