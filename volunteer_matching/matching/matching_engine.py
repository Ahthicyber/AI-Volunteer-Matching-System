"""
matching/matching_engine.py
────────────────────────────
Deterministic, rule-based volunteer-to-event matching engine — Phase 6.

Weights
-------
    Skills       40%
    Availability 20%
    Location     15%
    Interests    15%
    Experience    5%
    Mode          5%
    ─────────────────
    Total       100%

All functions are pure (no DB calls) except save_match_score and
get_recommendations_for_volunteer.
"""

import sqlite3
import logging
from datetime import datetime

from db.database import get_connection

logger = logging.getLogger(__name__)

# ── Weights ───────────────────────────────────────────────────────────────────
_W = {
    "skill":        0.40,
    "availability": 0.20,
    "location":     0.15,
    "interest":     0.15,
    "experience":   0.05,
    "mode":         0.05,
}

_EXP_RANK = {"Beginner": 1, "Intermediate": 2, "Experienced": 3}


# ── 1. normalize_list ─────────────────────────────────────────────────────────

def normalize_list(text: str) -> list[str]:
    """Convert comma-separated text to a lowercase, stripped list (no empties)."""
    if not text:
        return []
    return [item.strip().lower() for item in text.split(",") if item.strip()]


# ── 2. calculate_overlap_score ────────────────────────────────────────────────

def calculate_overlap_score(
    user_items: list[str], required_items: list[str]
) -> float:
    """
    Return 0–100 based on how many required items are covered by user items.

    If required_items is empty → 0 (no basis for comparison).
    """
    if not required_items:
        return 0.0
    user_set = set(user_items)
    matched  = sum(1 for item in required_items if item in user_set)
    return round((matched / len(required_items)) * 100, 2)


# ── 3. calculate_location_score ───────────────────────────────────────────────

def calculate_location_score(volunteer_city: str, event_city: str) -> float:
    """
    Exact city match  → 100
    Either missing    →   0
    Different cities  →  30
    """
    vc = (volunteer_city or "").strip().lower()
    ec = (event_city     or "").strip().lower()
    if not vc or not ec:
        return 0.0
    return 100.0 if vc == ec else 30.0


# ── 4. calculate_availability_score ──────────────────────────────────────────

def calculate_availability_score(
    volunteer_availability: str, event_date: str, event_time: str
) -> float:
    """
    Flexible in availability          → 100
    Weekend event + Weekend slot      → 100
    Weekday event + Weekday slot      → 100
    Time-of-day slot match (Morning/Afternoon/Evening) → bonus
    Otherwise                         →  40
    """
    avail_lower = (volunteer_availability or "").lower()

    if "flexible" in avail_lower:
        return 100.0

    # Determine weekday/weekend from event_date
    is_weekend = None
    if event_date:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(event_date.strip(), fmt)
                is_weekend = dt.weekday() >= 5  # 5=Sat, 6=Sun
                break
            except ValueError:
                continue

    if is_weekend is True and "weekend" in avail_lower:
        return 100.0
    if is_weekend is False and "weekday" in avail_lower:
        return 100.0

    # Time-of-day match (partial credit)
    time_lower = (event_time or "").lower()
    if ("morning" in avail_lower and
            any(t in time_lower for t in ["am", "morning", "06:", "07:", "08:", "09:", "10:", "11:"])):
        return 70.0
    if ("afternoon" in avail_lower and
            any(t in time_lower for t in ["pm", "12:", "13:", "14:", "15:", "16:"])):
        return 70.0
    if ("evening" in avail_lower and
            any(t in time_lower for t in ["17:", "18:", "19:", "20:", "21:", "pm"])):
        return 70.0

    return 40.0


# ── 5. calculate_experience_score ─────────────────────────────────────────────

def calculate_experience_score(
    volunteer_experience: str, required_experience: str
) -> float:
    """
    Same level                                      → 100
    Experienced volunteer for Beginner/Intermediate → 100
    Intermediate volunteer for Beginner             → 100
    Under-qualified (Beginner for Intermediate/Experienced) → 50
    Either missing / unrecognised                   →  60
    """
    ve = (volunteer_experience or "").strip()
    re = (required_experience  or "").strip()

    if not ve or not re:
        return 60.0
    if ve == re:
        return 100.0

    v_rank = _EXP_RANK.get(ve)
    r_rank = _EXP_RANK.get(re)
    if v_rank is None or r_rank is None:
        return 60.0

    # Over-qualified: always OK
    if v_rank > r_rank:
        return 100.0
    # Under-qualified: partial score
    return 50.0


# ── 6. calculate_mode_score ───────────────────────────────────────────────────

def calculate_mode_score(volunteer_mode: str, event_mode: str) -> float:
    """
    Exact match                  → 100
    Volunteer Hybrid             → 100 (can do anything)
    Event is Hybrid              →  80 (open to all modes)
    Otherwise                    →  40
    """
    vm = (volunteer_mode or "").strip().lower()
    em = (event_mode     or "").strip().lower()

    if not vm or not em:
        return 40.0
    if vm == em:
        return 100.0
    if vm == "hybrid":
        return 100.0
    if em == "hybrid":
        return 80.0
    return 40.0


# ── 7. calculate_match ────────────────────────────────────────────────────────

def calculate_match(volunteer_profile: dict, event: dict) -> dict:
    """
    Compute all component scores and the weighted final score.

    Returns a dict with keys:
        final_score, skill_score, availability_score, location_score,
        interest_score, experience_score, mode_score, explanation
    """
    vol_skills   = normalize_list(volunteer_profile.get("skills", ""))
    ev_skills    = normalize_list(event.get("required_skills", ""))
    vol_interests= normalize_list(volunteer_profile.get("interests", ""))
    ev_cause     = normalize_list(event.get("cause_area", ""))

    skill_score        = calculate_overlap_score(vol_skills, ev_skills)
    availability_score = calculate_availability_score(
        volunteer_profile.get("availability", ""),
        event.get("event_date", ""),
        event.get("event_time", ""),
    )
    location_score     = calculate_location_score(
        volunteer_profile.get("city", ""), event.get("city", "")
    )
    interest_score     = calculate_overlap_score(vol_interests, ev_cause)
    experience_score   = calculate_experience_score(
        volunteer_profile.get("experience_level", ""),
        event.get("experience_level", ""),
    )
    mode_score         = calculate_mode_score(
        volunteer_profile.get("preferred_mode", ""),
        event.get("mode", ""),
    )

    final_score = round(
        skill_score        * _W["skill"]        +
        availability_score * _W["availability"] +
        location_score     * _W["location"]     +
        interest_score     * _W["interest"]     +
        experience_score   * _W["experience"]   +
        mode_score         * _W["mode"],
        2,
    )

    explanation = _build_explanation(
        vol_skills, ev_skills, skill_score,
        location_score,
        availability_score,
        interest_score, vol_interests, ev_cause,
        experience_score,
        volunteer_profile.get("experience_level", ""),
        event.get("experience_level", ""),
        mode_score,
        volunteer_profile.get("preferred_mode", ""),
        event.get("mode", ""),
        final_score,
    )

    return {
        "final_score":        final_score,
        "skill_score":        skill_score,
        "availability_score": availability_score,
        "location_score":     location_score,
        "interest_score":     interest_score,
        "experience_score":   experience_score,
        "mode_score":         mode_score,
        "explanation":        explanation,
    }


def _build_explanation(
    vol_skills, ev_skills, skill_score,
    location_score, availability_score,
    interest_score, vol_interests, ev_cause,
    experience_score, vol_exp, ev_exp,
    mode_score, vol_mode, ev_mode,
    final_score,
) -> str:
    parts = []

    # Skills
    matched_skills = [s for s in ev_skills if s in set(vol_skills)]
    if matched_skills:
        parts.append(
            f"{len(matched_skills)} of {len(ev_skills)} required skill(s) match "
            f"({', '.join(s.title() for s in matched_skills)})"
        )
    elif ev_skills:
        parts.append("none of the required skills match your profile")

    # Location
    if location_score == 100:
        parts.append("the event is in your city")
    elif location_score == 30:
        parts.append("the event is in a different city")
    else:
        parts.append("location data is incomplete")

    # Availability
    if availability_score == 100:
        parts.append("your availability fits the event schedule")
    elif availability_score >= 70:
        parts.append("your availability partially overlaps with the event schedule")
    else:
        parts.append("your availability may not align with the event schedule")

    # Interests
    matched_int = [i for i in ev_cause if i in set(vol_interests)]
    if matched_int:
        parts.append(f"the cause area aligns with your interests ({', '.join(i.title() for i in matched_int)})")
    elif ev_cause:
        parts.append("the cause area does not match your listed interests")

    # Experience
    if experience_score == 100:
        parts.append(f"your experience level ({vol_exp}) meets the requirement ({ev_exp})")
    else:
        parts.append(f"your experience level ({vol_exp}) is below the requirement ({ev_exp})")

    # Mode
    if mode_score == 100:
        parts.append(f"your preferred mode ({vol_mode}) matches the event ({ev_mode})")
    elif mode_score == 80:
        parts.append(f"the event is hybrid which suits your preference ({vol_mode})")
    else:
        parts.append(f"preferred mode ({vol_mode}) differs from event mode ({ev_mode})")

    if not parts:
        return "Match calculated based on your profile and event requirements."

    joined = "; ".join(parts[:-1])
    if len(parts) > 1:
        summary = f"{joined}; and {parts[-1]}."
    else:
        summary = f"{parts[0]}."

    quality = (
        "Strong match" if final_score >= 75
        else "Moderate match" if final_score >= 50
        else "Low match"
    )
    return f"{quality}: {summary}"


# ── 8. save_match_score ───────────────────────────────────────────────────────

def save_match_score(
    volunteer_profile_id: int, event_id: int, scores: dict
) -> None:
    """
    Insert or update the MatchScores row (UPSERT via INSERT OR REPLACE).
    The UNIQUE constraint on (volunteer_profile_id, event_id) ensures no
    duplicates — SQLite replaces the old row on conflict.
    """
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO MatchScores (
                volunteer_profile_id, event_id,
                final_score, skill_score, availability_score,
                location_score, interest_score, experience_score,
                mode_score, explanation, calculated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))
            ON CONFLICT(volunteer_profile_id, event_id) DO UPDATE SET
                final_score          = excluded.final_score,
                skill_score          = excluded.skill_score,
                availability_score   = excluded.availability_score,
                location_score       = excluded.location_score,
                interest_score       = excluded.interest_score,
                experience_score     = excluded.experience_score,
                mode_score           = excluded.mode_score,
                explanation          = excluded.explanation,
                calculated_at        = datetime('now')
            """,
            (
                volunteer_profile_id, event_id,
                scores["final_score"], scores["skill_score"],
                scores["availability_score"], scores["location_score"],
                scores["interest_score"], scores["experience_score"],
                scores["mode_score"], scores["explanation"],
            ),
        )
        conn.commit()
    except sqlite3.Error as exc:
        logger.error("save_match_score error: %s", exc)
    finally:
        conn.close()


# ── 9. get_recommendations_for_volunteer ─────────────────────────────────────

def get_recommendations_for_volunteer(user_id: int) -> list[dict]:
    """
    1. Fetch volunteer profile (return [] if missing).
    2. Fetch all approved events.
    3. Calculate + save match scores.
    4. Return events sorted by final_score DESC, enriched with scores & explanation.
    """
    from volunteer.volunteer_service import get_volunteer_profile
    from events.event_service import get_approved_events

    profile = get_volunteer_profile(user_id)
    if not profile:
        logger.info("get_recommendations: no profile for user_id=%s", user_id)
        return []

    events = get_approved_events()
    if not events:
        return []

    vol_profile_id = profile["id"]
    results = []

    for event in events:
        scores = calculate_match(profile, event)
        save_match_score(vol_profile_id, event["id"], scores)

        results.append({
            **event,
            **scores,
        })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    return results
