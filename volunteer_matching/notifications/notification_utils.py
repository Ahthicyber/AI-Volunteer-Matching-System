"""Utility helpers for notification rendering and formatting."""

from __future__ import annotations

from datetime import datetime


def truncate_notification(text: str | None, limit: int = 120) -> str:
    """Return a compact, UI-safe notification string."""
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def get_notification_icon(notification_type: str | None) -> str:
    """Return a small icon for a notification type."""
    icons = {
        "ngo_approved": "✅",
        "ngo_rejected": "❌",
        "volunteer_verified": "✅",
        "volunteer_rejected": "❌",
        "document_verified": "📄✅",
        "document_rejected": "📄❌",
        "event_approved": "📣✅",
        "event_rejected": "📣❌",
        "application_accepted": "🎉",
        "application_rejected": "📋❌",
        "feedback_received": "⭐",
        "ocr_completed": "🔍",
        "ai_summary_ready": "🤖",
        "system": "ℹ️",
    }
    return icons.get(notification_type or "system", "🔔")


def format_notification_time(value: str | None) -> str:
    """Format SQLite timestamp values for compact display."""
    if not value:
        return ""
    raw = str(value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(raw[:19], fmt)
            return dt.strftime("%b %d, %Y · %H:%M")
        except ValueError:
            continue
    return raw[:16]
