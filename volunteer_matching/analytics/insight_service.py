"""
analytics/insight_service.py
────────────────────────────
Rule-based admin insights for Phase 13. These do not require Groq and never
make automated decisions.
"""
from __future__ import annotations


def generate_rule_based_insights(metrics: dict) -> list[str]:
    insights: list[str] = []
    apps = metrics.get("application_conversion", {})
    match = metrics.get("match_quality", {})
    docs = metrics.get("document_verification", {})
    ngo = metrics.get("ngo_activity", {})
    vol = metrics.get("volunteer_engagement", {})
    feedback = metrics.get("feedback_satisfaction", {})
    events = metrics.get("event_performance", {})

    if apps.get("pending_rate", 0) >= 50 and apps.get("total_applications", 0) > 0:
        insights.append("Most applications are still pending; NGO response time may need improvement.")
    if apps.get("acceptance_rate", 0) > apps.get("rejection_rate", 0) and apps.get("total_applications", 0) > 0:
        insights.append("Accepted applications currently outnumber rejected applications, which suggests healthy volunteer-event alignment.")

    accepted_avg = match.get("accepted_average_match_score")
    rejected_avg = match.get("rejected_average_match_score")
    if accepted_avg is not None and rejected_avg is not None and accepted_avg > rejected_avg:
        insights.append("Accepted applications have a higher average deterministic match score than rejected applications.")
    if match.get("low_quality_matches", 0) > match.get("high_quality_matches", 0):
        insights.append("Low-quality matches are higher than high-quality matches; profiles or event requirements may need clearer data.")

    if docs.get("ocr_failed_count", 0) > 0:
        insights.append("Some OCR jobs failed; admins should review file quality or unsupported document formats.")
    if docs.get("pending_documents", 0) > 0:
        insights.append("There are pending document reviews that may affect volunteer verification readiness.")

    if ngo.get("ngos_with_events", 0) < ngo.get("approved_ngos", 0):
        insights.append("Some approved NGOs have not posted events yet; admin follow-up may increase platform activity.")
    if vol.get("completed_profiles", 0) < vol.get("active_volunteers", 0):
        insights.append("Some volunteers have incomplete profiles, which may reduce recommendation quality.")

    if feedback.get("overall_average_rating") is not None and feedback.get("overall_average_rating") >= 4:
        insights.append("Feedback ratings are strong overall, supporting positive satisfaction evidence for the FYP evaluation.")

    cats = events.get("events_by_cause_area", [])
    if cats:
        top = cats[0]
        insights.append(f"{top.get('category', 'A category')} is currently the most common event category.")

    return insights or ["No major issues detected yet. More activity data will produce stronger insights."]


def generate_admin_recommendations(metrics: dict) -> list[str]:
    recommendations: list[str] = []
    apps = metrics.get("application_conversion", {})
    docs = metrics.get("document_verification", {})
    match = metrics.get("match_quality", {})
    health = metrics.get("system_health", {})

    if apps.get("pending_applications", 0) > 0:
        recommendations.append("Encourage NGOs to review pending applications regularly.")
    if docs.get("pending_documents", 0) > 0:
        recommendations.append("Prioritize pending document reviews to improve user trust and verification flow.")
    if docs.get("ocr_failed_count", 0) > 0:
        recommendations.append("Review OCR-failed files and guide users to upload clearer PDF/JPG/PNG documents.")
    if match.get("average_deterministic_score") is not None and match.get("average_deterministic_score") < 60:
        recommendations.append("Encourage users and NGOs to provide clearer skills, interests, availability, and location data.")
    if health.get("groq_status") != "available":
        recommendations.append("Configure GROQ_API_KEY when AI summaries/explanations are needed for demos.")
    if health.get("ml_model_status") != "available":
        recommendations.append("Train or restore the ML model before demonstrating ML comparison features.")

    return recommendations or ["Continue monitoring applications, profile completeness, and document reviews."]
