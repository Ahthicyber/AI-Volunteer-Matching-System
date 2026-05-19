"""
analytics/chart_utils.py
────────────────────────
Small, Streamlit-friendly helpers for safe dashboard rendering.
"""
from __future__ import annotations

from typing import Any, Iterable
import pandas as pd


def safe_percentage(numerator: Any, denominator: Any, decimals: int = 1) -> float:
    try:
        num = float(numerator or 0)
        den = float(denominator or 0)
        if den <= 0:
            return 0.0
        return round((num / den) * 100, decimals)
    except Exception:
        return 0.0


def safe_average(values: Iterable[Any], decimals: int = 2) -> float | None:
    vals = []
    for value in values or []:
        try:
            if value is not None:
                vals.append(float(value))
        except Exception:
            continue
    if not vals:
        return None
    return round(sum(vals) / len(vals), decimals)


def dataframe_from_metrics(data: Any) -> pd.DataFrame:
    if data is None:
        return pd.DataFrame()
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, dict):
        return pd.DataFrame([data])
    return pd.DataFrame()


def format_metric_card(value: Any, suffix: str = "") -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.2f}{suffix}"
    return f"{value}{suffix}"


def status_badge(status: str | None) -> str:
    status = (status or "unknown").lower()
    icons = {
        "approved": "✅", "verified": "✅", "accepted": "✅", "processed": "✅",
        "pending": "⏳", "not_processed": "⏳", "unverified": "⬜",
        "rejected": "❌", "failed": "⚠️", "cancelled": "🚫",
        "available": "✅", "unavailable": "⚠️",
    }
    return f"{icons.get(status, '•')} {status.replace('_', ' ').title()}"


def empty_chart_message(label: str = "No data available yet.") -> str:
    return f"ℹ️ {label}"
