"""
analytics/analytics_service.py
──────────────────────────────
SQLite-compatible analytics service for Phase 13.

All functions are defensive: they return dictionaries/lists suitable for
Streamlit rendering and never raise raw SQL errors to pages.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from db.database import get_connection, get_db_path

logger = logging.getLogger(__name__)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _fetchall(sql: str, params: tuple = ()) -> list[dict]:
    conn = get_connection()
    try:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]
    except Exception as exc:
        logger.warning("Analytics query failed: %s", exc)
        return []
    finally:
        conn.close()


def _fetchone(sql: str, params: tuple = ()) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else {}
    except Exception as exc:
        logger.warning("Analytics query failed: %s", exc)
        return {}
    finally:
        conn.close()


def _scalar(sql: str, params: tuple = (), default: Any = 0) -> Any:
    row = _fetchone(sql, params)
    if not row:
        return default
    try:
        return next(iter(row.values()))
    except Exception:
        return default


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 2)
    except Exception:
        return None


def _pct(num: Any, den: Any) -> float:
    den = _float(den) or 0
    if den <= 0:
        return 0.0
    return round((_float(num) or 0) / den * 100, 1)


def _table_exists(table: str) -> bool:
    return bool(_scalar("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table,), 0))


def _column_exists(table: str, column: str) -> bool:
    conn = get_connection()
    try:
        return any(dict(r).get("name") == column for r in conn.execute(f"PRAGMA table_info({table})").fetchall())
    except Exception:
        return False
    finally:
        conn.close()


def get_user_growth_metrics() -> dict:
    role_rows = _fetchall("SELECT role, COUNT(*) AS count FROM Users GROUP BY role ORDER BY count DESC")
    registrations = _fetchall(
        """
        SELECT date(created_at) AS date, COUNT(*) AS count
        FROM Users
        GROUP BY date(created_at)
        ORDER BY date(created_at)
        """
    )
    by_role = {r.get("role", "unknown"): _int(r.get("count")) for r in role_rows}
    return {
        "users_by_role": role_rows,
        "registrations_over_time": registrations,
        "volunteer_count": by_role.get("volunteer", 0),
        "ngo_count": by_role.get("ngo", 0),
        "admin_count": by_role.get("admin", 0),
        "total_users": sum(by_role.values()),
    }


def get_volunteer_engagement_metrics() -> dict:
    total = _int(_scalar("SELECT COUNT(*) FROM VolunteerProfiles"))
    completed = _int(_scalar("SELECT COUNT(*) FROM VolunteerProfiles WHERE profile_completeness >= 70"))
    with_apps = _int(_scalar("SELECT COUNT(DISTINCT volunteer_profile_id) FROM Applications"))
    total_apps = _int(_scalar("SELECT COUNT(*) FROM Applications"))
    status_rows = _fetchall("SELECT verification_status AS status, COUNT(*) AS count FROM VolunteerProfiles GROUP BY verification_status")
    return {
        "active_volunteers": total,
        "completed_profiles": completed,
        "volunteers_with_applications": with_apps,
        "average_applications_per_volunteer": round(total_apps / total, 2) if total else 0.0,
        "verified_volunteers": _int(_scalar("SELECT COUNT(*) FROM VolunteerProfiles WHERE verification_status='verified'")),
        "unverified_volunteers": _int(_scalar("SELECT COUNT(*) FROM VolunteerProfiles WHERE verification_status!='verified'")),
        "verification_status": status_rows,
    }


def get_ngo_activity_metrics() -> dict:
    approved = _int(_scalar("SELECT COUNT(*) FROM NGOProfiles WHERE verification_status='approved'"))
    total_ngos = _int(_scalar("SELECT COUNT(*) FROM NGOProfiles"))
    with_events = _int(_scalar("SELECT COUNT(DISTINCT ngo_profile_id) FROM Events"))
    total_events = _int(_scalar("SELECT COUNT(*) FROM Events"))
    most_active = _fetchall(
        """
        SELECT COALESCE(n.organization_name, 'Unknown NGO') AS organization_name, COUNT(e.id) AS event_count
        FROM NGOProfiles n
        LEFT JOIN Events e ON e.ngo_profile_id = n.id
        GROUP BY n.id
        ORDER BY event_count DESC, organization_name ASC
        LIMIT 10
        """
    )
    approval_status = _fetchall("SELECT verification_status AS status, COUNT(*) AS count FROM NGOProfiles GROUP BY verification_status")
    return {
        "total_ngos": total_ngos,
        "approved_ngos": approved,
        "ngos_with_events": with_events,
        "average_events_per_ngo": round(total_events / total_ngos, 2) if total_ngos else 0.0,
        "most_active_ngos": most_active,
        "approval_status": approval_status,
    }


def get_event_performance_metrics() -> dict:
    events_by_status = _fetchall("SELECT status, COUNT(*) AS count FROM Events GROUP BY status ORDER BY count DESC")
    events_by_category = _fetchall("SELECT cause_area AS category, COUNT(*) AS count FROM Events GROUP BY cause_area ORDER BY count DESC")
    events_by_mode = _fetchall("SELECT mode, COUNT(*) AS count FROM Events GROUP BY mode ORDER BY count DESC")
    events_by_city = _fetchall("SELECT city, COUNT(*) AS count FROM Events GROUP BY city ORDER BY count DESC LIMIT 15")
    total_events = _int(_scalar("SELECT COUNT(*) FROM Events"))
    total_apps = _int(_scalar("SELECT COUNT(*) FROM Applications"))
    app_counts = _fetchall(
        """
        SELECT e.title, COUNT(a.id) AS applications
        FROM Events e
        LEFT JOIN Applications a ON a.event_id = e.id
        GROUP BY e.id
        ORDER BY applications DESC, e.created_at DESC
        LIMIT 15
        """
    )
    return {
        "events_by_status": events_by_status,
        "events_by_cause_area": events_by_category,
        "events_by_mode": events_by_mode,
        "events_by_city": events_by_city,
        "average_applications_per_event": round(total_apps / total_events, 2) if total_events else 0.0,
        "event_application_counts": app_counts,
        "approved_events": _int(_scalar("SELECT COUNT(*) FROM Events WHERE status='approved'")),
    }


def get_application_conversion_metrics() -> dict:
    rows = _fetchall("SELECT status, COUNT(*) AS count FROM Applications GROUP BY status")
    counts = {r.get("status"): _int(r.get("count")) for r in rows}
    total = sum(counts.values())
    trends = _fetchall(
        """
        SELECT date(applied_at) AS date, status, COUNT(*) AS count
        FROM Applications
        GROUP BY date(applied_at), status
        ORDER BY date(applied_at)
        """
    )
    return {
        "status_distribution": rows,
        "total_applications": total,
        "accepted_applications": counts.get("accepted", 0),
        "rejected_applications": counts.get("rejected", 0),
        "cancelled_applications": counts.get("cancelled", 0),
        "pending_applications": counts.get("pending", 0),
        "acceptance_rate": _pct(counts.get("accepted", 0), total),
        "rejection_rate": _pct(counts.get("rejected", 0), total),
        "pending_rate": _pct(counts.get("pending", 0), total),
        "application_trends": trends,
    }


def get_match_quality_metrics() -> dict:
    row = _fetchone(
        """
        SELECT ROUND(AVG(final_score),2) AS avg_score,
               SUM(CASE WHEN final_score >= 75 THEN 1 ELSE 0 END) AS high_count,
               SUM(CASE WHEN final_score >= 50 AND final_score < 75 THEN 1 ELSE 0 END) AS medium_count,
               SUM(CASE WHEN final_score < 50 THEN 1 ELSE 0 END) AS low_count,
               COUNT(*) AS total_matches
        FROM MatchScores
        """
    )
    accepted = _scalar(
        """
        SELECT ROUND(AVG(ms.final_score),2)
        FROM Applications a
        JOIN MatchScores ms ON ms.volunteer_profile_id=a.volunteer_profile_id AND ms.event_id=a.event_id
        WHERE a.status='accepted'
        """, default=None)
    rejected = _scalar(
        """
        SELECT ROUND(AVG(ms.final_score),2)
        FROM Applications a
        JOIN MatchScores ms ON ms.volunteer_profile_id=a.volunteer_profile_id AND ms.event_id=a.event_id
        WHERE a.status='rejected'
        """, default=None)
    distribution = [
        {"quality": "High (≥75)", "count": _int(row.get("high_count"))},
        {"quality": "Medium (50–74)", "count": _int(row.get("medium_count"))},
        {"quality": "Low (<50)", "count": _int(row.get("low_count"))},
    ]
    return {
        "average_deterministic_score": _float(row.get("avg_score")),
        "high_quality_matches": _int(row.get("high_count")),
        "medium_quality_matches": _int(row.get("medium_count")),
        "low_quality_matches": _int(row.get("low_count")),
        "total_matches": _int(row.get("total_matches")),
        "accepted_average_match_score": _float(accepted),
        "rejected_average_match_score": _float(rejected),
        "score_distribution": distribution,
    }


def get_feedback_satisfaction_metrics() -> dict:
    total = _int(_scalar("SELECT COUNT(*) FROM Feedback"))
    avg_volunteer = _scalar("SELECT ROUND(AVG(rating),2) FROM Feedback WHERE feedback_from='volunteer'", default=None)
    avg_ngo = _scalar("SELECT ROUND(AVG(rating),2) FROM Feedback WHERE feedback_from='ngo'", default=None)
    distribution = _fetchall("SELECT rating, COUNT(*) AS count FROM Feedback GROUP BY rating ORDER BY rating")
    trend = _fetchall(
        """
        SELECT date(created_at) AS date, ROUND(AVG(rating),2) AS average_rating, COUNT(*) AS feedback_count
        FROM Feedback
        GROUP BY date(created_at)
        ORDER BY date(created_at)
        """
    )
    return {
        "average_volunteer_rating": _float(avg_volunteer),
        "average_ngo_rating": _float(avg_ngo),
        "overall_average_rating": _float(_scalar("SELECT ROUND(AVG(rating),2) FROM Feedback", default=None)),
        "total_feedback": total,
        "rating_distribution": distribution,
        "satisfaction_trend": trend,
    }


def get_document_verification_metrics() -> dict:
    total = _int(_scalar("SELECT COUNT(*) FROM VolunteerDocuments"))
    verification = _fetchall("SELECT verification_status AS status, COUNT(*) AS count FROM VolunteerDocuments GROUP BY verification_status")
    ocr = _fetchall("SELECT ocr_status AS status, COUNT(*) AS count FROM VolunteerDocuments GROUP BY ocr_status") if _column_exists("VolunteerDocuments", "ocr_status") else []
    counts = {r.get("status"): _int(r.get("count")) for r in verification}
    ocr_counts = {r.get("status"): _int(r.get("count")) for r in ocr}
    return {
        "total_documents": total,
        "pending_documents": counts.get("pending", 0),
        "verified_documents": counts.get("verified", 0),
        "rejected_documents": counts.get("rejected", 0),
        "ocr_processed_count": ocr_counts.get("processed", 0),
        "ocr_failed_count": ocr_counts.get("failed", 0),
        "verification_status": verification,
        "ocr_status": ocr,
    }


def get_ml_comparison_metrics() -> dict:
    det_avg = _float(_scalar("SELECT ROUND(AVG(final_score),2) FROM MatchScores", default=None))
    model_path = _PROJECT_ROOT / "data" / "models" / "match_model.pkl"
    meta_path = _PROJECT_ROOT / "data" / "models" / "model_meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    ml_avg = None
    if _column_exists("MatchScores", "ml_score"):
        ml_avg = _float(_scalar("SELECT ROUND(AVG(ml_score),2) FROM MatchScores", default=None))
    return {
        "deterministic_average_score": det_avg,
        "ml_average_score": ml_avg,
        "model_available": model_path.exists(),
        "model_metadata": meta,
        "comparison_explanation": "Deterministic scores remain authoritative. ML is used only as a secondary enhancement when available.",
    }


def get_system_health_summary() -> dict:
    db_path = get_db_path()
    db_ok = db_path.exists()
    failed_ocr = _int(_scalar("SELECT COUNT(*) FROM VolunteerDocuments WHERE ocr_status='failed'")) if _column_exists("VolunteerDocuments", "ocr_status") else 0
    pending_tasks = (
        _int(_scalar("SELECT COUNT(*) FROM NGOProfiles WHERE verification_status='pending'"))
        + _int(_scalar("SELECT COUNT(*) FROM Events WHERE status='pending'"))
        + _int(_scalar("SELECT COUNT(*) FROM VolunteerDocuments WHERE verification_status='pending'"))
        + _int(_scalar("SELECT COUNT(*) FROM VolunteerProfiles WHERE verification_status='pending'"))
    )
    unread_system = _int(_scalar("SELECT COUNT(*) FROM Notifications WHERE is_read=0 AND notification_type='system'")) if _table_exists("Notifications") else 0
    try:
        from ai.groq_client import is_groq_available
        groq_available = bool(is_groq_available())
    except Exception:
        groq_available = False
    model_path = _PROJECT_ROOT / "data" / "models" / "match_model.pkl"
    return {
        "database_status": "available" if db_ok else "unavailable",
        "database_path": str(db_path),
        "total_users": _int(_scalar("SELECT COUNT(*) FROM Users")),
        "pending_admin_tasks": pending_tasks,
        "failed_ocr_count": failed_ocr,
        "unread_system_notifications": unread_system,
        "ml_model_status": "available" if model_path.exists() else "unavailable",
        "groq_status": "available" if groq_available else "unavailable",
        "notifications_status": "available" if _table_exists("Notifications") else "unavailable",
    }


def get_all_analytics() -> dict:
    return {
        "user_growth": get_user_growth_metrics(),
        "volunteer_engagement": get_volunteer_engagement_metrics(),
        "ngo_activity": get_ngo_activity_metrics(),
        "event_performance": get_event_performance_metrics(),
        "application_conversion": get_application_conversion_metrics(),
        "match_quality": get_match_quality_metrics(),
        "feedback_satisfaction": get_feedback_satisfaction_metrics(),
        "document_verification": get_document_verification_metrics(),
        "ml_comparison": get_ml_comparison_metrics(),
        "system_health": get_system_health_summary(),
    }
