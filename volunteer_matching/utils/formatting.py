"""
utils/formatting.py
───────────────────
Small formatting helpers used by Phase 14 UI components.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def safe_display(value: Any, default: str = "—") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def truncate_text(text: Any, max_chars: int = 160) -> str:
    value = safe_display(text, "")
    if len(value) <= max_chars:
        return value
    return value[: max(0, max_chars - 1)].rstrip() + "…"


def format_datetime(value: Any) -> str:
    if not value:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y, %I:%M %p")
    text = str(value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19] if "T" in fmt else text[:19], fmt).strftime("%d %b %Y, %I:%M %p")
        except Exception:
            continue
    return text


def format_percentage(value: Any, decimals: int = 1) -> str:
    try:
        return f"{float(value):.{decimals}f}%"
    except Exception:
        return "0%"


def format_status(status: Any) -> str:
    text = safe_display(status, "Unknown").replace("_", " ").strip()
    return text.title()


def format_role(role: Any) -> str:
    return format_status(role)
