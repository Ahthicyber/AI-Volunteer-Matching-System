"""
ai/ai_service.py
────────────────
Public service layer for optional AI features.

Pages and business services should call this file only, not groq_client.py
directly. This keeps future AI features centralized and safe.
"""

from __future__ import annotations

from typing import Any

from ai.ai_utils import compact_dict, fallback_response, sanitize_ai_response, truncate_text
from ai.groq_client import generate_completion, is_groq_available
from ai.prompts import (
    ADMIN_SUMMARY_PROMPT,
    ADMIN_PROFILE_SUMMARY_PROMPT,
    DOCUMENT_METADATA_SUMMARY_PROMPT,
    DOCUMENT_OCR_SUMMARY_PROMPT,
    SYSTEM_INSIGHTS_PROMPT,
    AI_SYSTEM_GUARDRAILS,
    EVENT_IMPROVEMENT_PROMPT,
    MATCH_EXPLANATION_PROMPT,
    PROFILE_IMPROVEMENT_PROMPT,
)


def _safe_format(template: str, **kwargs: Any) -> str:
    """Format prompt templates without exposing formatting errors to pages."""
    safe_kwargs = {key: truncate_text(value, 1800) for key, value in kwargs.items()}
    try:
        return template.format(**safe_kwargs)
    except Exception:
        return "AI prompt could not be prepared safely."


def _result(success: bool, response: str, fallback: bool = False) -> dict[str, Any]:
    """Consistent response payload for Streamlit pages."""
    return {
        "success": bool(success),
        "response": sanitize_ai_response(response, max_words=230, max_chars=1400),
        "fallback": bool(fallback),
    }


def generate_match_explanation(
    volunteer_profile: dict[str, Any] | None = None,
    event_data: dict[str, Any] | None = None,
    deterministic_score: float | int | None = None,
    deterministic_breakdown: dict[str, Any] | None = None,
    ml_score: float | int | None = None,
    # Backward-compatible aliases from Phase 10.1/internal tests.
    event_details: dict[str, Any] | None = None,
    score_breakdown: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate an optional AI explanation for an existing deterministic match.

    This function never changes recommendation ranking, deterministic scoring,
    ML scoring, application outcomes, or approval decisions. It returns a safe
    dictionary that pages can display directly.
    """
    try:
        if not is_groq_available():
            return _result(False, fallback_response("AI explanation temporarily unavailable."), True)

        safe_event_data = event_data or event_details or {}
        safe_breakdown = deterministic_breakdown or score_breakdown or {}

        prompt = _safe_format(
            MATCH_EXPLANATION_PROMPT,
            volunteer_profile=compact_dict(volunteer_profile),
            event_details=compact_dict(safe_event_data),
            deterministic_score="Not provided" if deterministic_score is None else f"{float(deterministic_score):.1f}%",
            score_breakdown=compact_dict(safe_breakdown),
            ml_score="Not available" if ml_score is None else f"{float(ml_score):.1f}%",
        )
        response = generate_completion(
            prompt=prompt,
            system_prompt=AI_SYSTEM_GUARDRAILS,
            temperature=0.35,
            max_tokens=320,
        )
        cleaned = sanitize_ai_response(response, max_words=230, max_chars=1400)
        if not cleaned or "unavailable" in cleaned.lower() or "not configured" in cleaned.lower():
            return _result(False, fallback_response("AI explanation temporarily unavailable."), True)
        return _result(True, cleaned, False)
    except Exception:
        return _result(False, fallback_response("AI explanation temporarily unavailable."), True)


def generate_profile_suggestions(profile_data: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Generate optional volunteer profile improvement suggestions.

    This is guidance-only. It never edits stored profile data and never
    guarantees better matches or application outcomes.
    """
    try:
        volunteer_profile = profile_data or kwargs.get("volunteer_profile") or {}
        if not is_groq_available():
            return _result(False, fallback_response("AI suggestions temporarily unavailable."), True)

        prompt = _safe_format(
            PROFILE_IMPROVEMENT_PROMPT,
            volunteer_profile=compact_dict(volunteer_profile),
        )
        response = generate_completion(
            prompt=prompt,
            system_prompt=AI_SYSTEM_GUARDRAILS,
            temperature=0.35,
            max_tokens=380,
        )
        cleaned = sanitize_ai_response(response, max_words=260, max_chars=1700)
        if not cleaned or "unavailable" in cleaned.lower() or "not configured" in cleaned.lower():
            return _result(False, fallback_response("AI suggestions temporarily unavailable."), True)
        return _result(True, cleaned, False)
    except Exception:
        return _result(False, fallback_response("AI suggestions temporarily unavailable."), True)


def improve_event_description(event_data: dict[str, Any] | str | None = None, **kwargs: Any) -> dict[str, Any]:
    """Improve NGO event wording without auto-saving or changing event records."""
    try:
        safe_event_data = event_data if event_data is not None else kwargs.get("event_description", {})
        if not is_groq_available():
            return _result(False, fallback_response("AI event improvement temporarily unavailable."), True)

        prompt = _safe_format(
            EVENT_IMPROVEMENT_PROMPT,
            event_data=compact_dict(safe_event_data) if isinstance(safe_event_data, dict) else safe_event_data,
        )
        response = generate_completion(
            prompt=prompt,
            system_prompt=AI_SYSTEM_GUARDRAILS,
            temperature=0.35,
            max_tokens=420,
        )
        cleaned = sanitize_ai_response(response, max_words=280, max_chars=1800)
        if not cleaned or "unavailable" in cleaned.lower() or "not configured" in cleaned.lower():
            return _result(False, fallback_response("AI event improvement temporarily unavailable."), True)
        return _result(True, cleaned, False)
    except Exception:
        return _result(False, fallback_response("AI event improvement temporarily unavailable."), True)


def generate_admin_summary(platform_data: dict[str, Any] | str | None = None) -> dict[str, Any]:
    """Generate an optional admin dashboard summary from provided platform data."""
    try:
        if not is_groq_available():
            return _result(False, fallback_response(), True)
        prompt = _safe_format(
            ADMIN_SUMMARY_PROMPT,
            platform_data=compact_dict(platform_data) if isinstance(platform_data, dict) else platform_data,
        )
        response = generate_completion(prompt, AI_SYSTEM_GUARDRAILS, max_tokens=300)
        return _result(True, response, False)
    except Exception:
        return _result(False, fallback_response(), True)


def generate_profile_summary(profile_data: dict[str, Any] | None = None, profile_type: str = "volunteer") -> dict[str, Any]:
    """Generate an optional admin-facing summary for a volunteer or NGO profile.

    The summary is assistive only. It never approves, rejects, verifies,
    moderates, or changes any database record.
    """
    try:
        normalized_type = "ngo" if str(profile_type).lower() == "ngo" else "volunteer"
        if not is_groq_available():
            return _result(False, fallback_response("AI summary temporarily unavailable."), True)

        prompt = _safe_format(
            ADMIN_PROFILE_SUMMARY_PROMPT,
            profile_type=normalized_type,
            profile_data=compact_dict(profile_data),
        )
        response = generate_completion(
            prompt=prompt,
            system_prompt=AI_SYSTEM_GUARDRAILS,
            temperature=0.30,
            max_tokens=340,
        )
        cleaned = sanitize_ai_response(response, max_words=240, max_chars=1500)
        if not cleaned or "unavailable" in cleaned.lower() or "not configured" in cleaned.lower():
            return _result(False, fallback_response("AI summary temporarily unavailable."), True)
        return _result(True, cleaned, False)
    except Exception:
        return _result(False, fallback_response("AI summary temporarily unavailable."), True)


def generate_document_metadata_summary(document_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generate an optional summary of document metadata only.

    This function intentionally does not inspect document content or perform OCR.
    """
    try:
        if not is_groq_available():
            return _result(False, fallback_response("AI metadata summary temporarily unavailable."), True)

        prompt = _safe_format(
            DOCUMENT_METADATA_SUMMARY_PROMPT,
            document_data=compact_dict(document_data),
        )
        response = generate_completion(
            prompt=prompt,
            system_prompt=AI_SYSTEM_GUARDRAILS,
            temperature=0.25,
            max_tokens=260,
        )
        cleaned = sanitize_ai_response(response, max_words=180, max_chars=1200)
        if not cleaned or "unavailable" in cleaned.lower() or "not configured" in cleaned.lower():
            return _result(False, fallback_response("AI metadata summary temporarily unavailable."), True)
        return _result(True, cleaned, False)
    except Exception:
        return _result(False, fallback_response("AI metadata summary temporarily unavailable."), True)


def generate_system_insights(metrics_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generate optional lightweight admin insights from aggregate metrics only."""
    try:
        if not is_groq_available():
            return _result(False, fallback_response("AI insights temporarily unavailable."), True)

        prompt = _safe_format(
            SYSTEM_INSIGHTS_PROMPT,
            metrics_data=compact_dict(metrics_data),
        )
        response = generate_completion(
            prompt=prompt,
            system_prompt=AI_SYSTEM_GUARDRAILS,
            temperature=0.30,
            max_tokens=340,
        )
        cleaned = sanitize_ai_response(response, max_words=240, max_chars=1500)
        if not cleaned or "unavailable" in cleaned.lower() or "not configured" in cleaned.lower():
            return _result(False, fallback_response("AI insights temporarily unavailable."), True)
        return _result(True, cleaned, False)
    except Exception:
        return _result(False, fallback_response("AI insights temporarily unavailable."), True)


def generate_document_content_summary(extracted_text: str, document_type: str = "Document") -> dict[str, Any]:
    """Generate an optional AI summary from OCR-extracted document text.

    The summary is assistive only. It never verifies authenticity and never
    approves/rejects the document.
    """
    try:
        safe_text = truncate_text(extracted_text or "", 5000)
        if not safe_text.strip():
            return _result(False, fallback_response("No OCR text is available for AI summary."), True)
        if not is_groq_available():
            return _result(False, fallback_response("AI document summary temporarily unavailable."), True)

        prompt = _safe_format(
            DOCUMENT_OCR_SUMMARY_PROMPT,
            document_type=document_type or "Document",
            extracted_text=safe_text,
        )
        response = generate_completion(
            prompt=prompt,
            system_prompt=AI_SYSTEM_GUARDRAILS,
            temperature=0.25,
            max_tokens=360,
        )
        cleaned = sanitize_ai_response(response, max_words=230, max_chars=1500)
        if not cleaned or "unavailable" in cleaned.lower() or "not configured" in cleaned.lower():
            return _result(False, fallback_response("AI document summary temporarily unavailable."), True)
        return _result(True, cleaned, False)
    except Exception:
        return _result(False, fallback_response("AI document summary temporarily unavailable."), True)


def test_groq_connection() -> tuple[bool, str]:
    """Run a small manual Groq connectivity test for Streamlit UI."""
    if not is_groq_available():
        return False, fallback_response(
            "Groq AI is not configured. Add GROQ_API_KEY to .env or Streamlit secrets, then restart the app."
        )

    prompt = (
        "Reply in one short sentence confirming that the optional Groq "
        "explanation infrastructure is connected. Do not mention approvals, "
        "rankings, or decisions."
    )
    response = sanitize_ai_response(generate_completion(prompt, AI_SYSTEM_GUARDRAILS, max_tokens=80))
    ok = "unavailable" not in response.lower() and "not configured" not in response.lower()
    return ok, response
