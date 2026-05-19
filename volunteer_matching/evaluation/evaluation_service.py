"""
evaluation/evaluation_service.py
──────────────────────────────────
System-wide evaluation metrics for the admin dashboard — Phase 8.

Public API
----------
    get_system_metrics()            → dict
    get_match_quality_metrics()     → dict
    get_event_category_metrics()    → list[dict]
    get_application_status_metrics() → list[dict]
"""

import sqlite3
import logging
from db.database import get_connection

logger = logging.getLogger(__name__)


def _safe_float(val) -> float | None:
    if val is None:
        return None
    try:
        return round(float(val), 2)
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> int:
    try:
        return int(val or 0)
    except (TypeError, ValueError):
        return 0


# ── 1. get_system_metrics ─────────────────────────────────────────────────────

def get_system_metrics() -> dict:
    conn = get_connection()
    try:
        def _q(sql, *args):
            return conn.execute(sql, args).fetchone()

        total_users    = _safe_int(_q("SELECT COUNT(*) FROM Users")[0])
        total_vol      = _safe_int(_q("SELECT COUNT(*) FROM Users WHERE role='volunteer'")[0])
        total_ngo      = _safe_int(_q("SELECT COUNT(*) FROM Users WHERE role='ngo'")[0])
        approved_ngos  = _safe_int(_q("SELECT COUNT(*) FROM NGOProfiles WHERE verification_status='approved'")[0])
        pending_ngos   = _safe_int(_q("SELECT COUNT(*) FROM NGOProfiles WHERE verification_status='pending'")[0])
        rejected_ngos  = _safe_int(_q("SELECT COUNT(*) FROM NGOProfiles WHERE verification_status='rejected'")[0])

        total_events   = _safe_int(_q("SELECT COUNT(*) FROM Events")[0])
        approved_evts  = _safe_int(_q("SELECT COUNT(*) FROM Events WHERE status='approved'")[0])
        pending_evts   = _safe_int(_q("SELECT COUNT(*) FROM Events WHERE status='pending'")[0])
        rejected_evts  = _safe_int(_q("SELECT COUNT(*) FROM Events WHERE status='rejected'")[0])

        total_apps     = _safe_int(_q("SELECT COUNT(*) FROM Applications")[0])
        pending_apps   = _safe_int(_q("SELECT COUNT(*) FROM Applications WHERE status='pending'")[0])
        accepted_apps  = _safe_int(_q("SELECT COUNT(*) FROM Applications WHERE status='accepted'")[0])
        rejected_apps  = _safe_int(_q("SELECT COUNT(*) FROM Applications WHERE status='rejected'")[0])
        cancelled_apps = _safe_int(_q("SELECT COUNT(*) FROM Applications WHERE status='cancelled'")[0])

        total_feedback = _safe_int(_q("SELECT COUNT(*) FROM Feedback")[0])

        avg_match_row  = _q("SELECT ROUND(AVG(final_score),2) FROM MatchScores")
        avg_match      = _safe_float(avg_match_row[0]) if avg_match_row else None

        avg_fb_row     = _q("SELECT ROUND(AVG(rating),2) FROM Feedback")
        avg_feedback   = _safe_float(avg_fb_row[0]) if avg_fb_row else None

        reviewed_apps  = accepted_apps + rejected_apps
        accept_rate    = round(accepted_apps / reviewed_apps * 100, 1) if reviewed_apps else 0.0
        reject_rate    = round(rejected_apps / reviewed_apps * 100, 1) if reviewed_apps else 0.0

        return {
            "total_users":             total_users,
            "total_volunteers":        total_vol,
            "total_ngos":              total_ngo,
            "approved_ngos":           approved_ngos,
            "pending_ngos":            pending_ngos,
            "rejected_ngos":           rejected_ngos,
            "total_events":            total_events,
            "approved_events":         approved_evts,
            "pending_events":          pending_evts,
            "rejected_events":         rejected_evts,
            "total_applications":      total_apps,
            "pending_applications":    pending_apps,
            "accepted_applications":   accepted_apps,
            "rejected_applications":   rejected_apps,
            "cancelled_applications":  cancelled_apps,
            "total_feedback":          total_feedback,
            "average_match_score":     avg_match,
            "average_feedback_rating": avg_feedback,
            "acceptance_rate":         accept_rate,
            "rejection_rate":          reject_rate,
        }
    except sqlite3.Error as exc:
        logger.error("get_system_metrics error: %s", exc)
        return {}
    finally:
        conn.close()


# ── 2. get_match_quality_metrics ──────────────────────────────────────────────

def get_match_quality_metrics() -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT
                ROUND(AVG(final_score), 2)                                   AS avg_score,
                SUM(CASE WHEN final_score >= 75 THEN 1 ELSE 0 END)           AS high_count,
                SUM(CASE WHEN final_score >= 50 AND final_score < 75 THEN 1 ELSE 0 END) AS mid_count,
                SUM(CASE WHEN final_score < 50  THEN 1 ELSE 0 END)           AS low_count
            FROM MatchScores
            """
        ).fetchone()

        acc_row = conn.execute(
            """
            SELECT ROUND(AVG(ms.final_score),2)
            FROM   Applications a
            JOIN   MatchScores ms ON ms.volunteer_profile_id = a.volunteer_profile_id
                                  AND ms.event_id = a.event_id
            WHERE  a.status = 'accepted'
            """
        ).fetchone()

        rej_row = conn.execute(
            """
            SELECT ROUND(AVG(ms.final_score),2)
            FROM   Applications a
            JOIN   MatchScores ms ON ms.volunteer_profile_id = a.volunteer_profile_id
                                  AND ms.event_id = a.event_id
            WHERE  a.status = 'rejected'
            """
        ).fetchone()

        return {
            "average_match_score":          _safe_float(row["avg_score"]) if row else None,
            "high_quality_matches_count":   _safe_int(row["high_count"]) if row else 0,
            "medium_quality_matches_count": _safe_int(row["mid_count"]) if row else 0,
            "low_quality_matches_count":    _safe_int(row["low_count"]) if row else 0,
            "accepted_average_match_score": _safe_float(acc_row[0]) if acc_row else None,
            "rejected_average_match_score": _safe_float(rej_row[0]) if rej_row else None,
        }
    except sqlite3.Error as exc:
        logger.error("get_match_quality_metrics error: %s", exc)
        return {}
    finally:
        conn.close()


# ── 3. get_event_category_metrics ─────────────────────────────────────────────

def get_event_category_metrics() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT cause_area, COUNT(*) AS event_count
            FROM   Events
            WHERE  status = 'approved'
            GROUP BY cause_area
            ORDER BY event_count DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_event_category_metrics error: %s", exc)
        return []
    finally:
        conn.close()


# ── 4. get_application_status_metrics ────────────────────────────────────────

def get_application_status_metrics() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM   Applications
            GROUP BY status
            ORDER BY count DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.Error as exc:
        logger.error("get_application_status_metrics error: %s", exc)
        return []
    finally:
        conn.close()
