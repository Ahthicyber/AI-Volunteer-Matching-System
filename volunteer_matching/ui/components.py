"""
ui/components.py
────────────────
Reusable Streamlit UI components for Phase 14 polish.
"""
from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from utils.formatting import format_datetime, format_percentage, format_status, truncate_text, safe_display


def _html(text: Any) -> str:
    return escape(safe_display(text))


def page_title(title: str, subtitle: str | None = None, icon: str | None = None) -> None:
    prefix = f"{icon} " if icon else ""
    st.markdown(
        f"""
        <div class='vm-page-title'>
            <h1>{_html(prefix + title)}</h1>
            {f"<p class='vm-page-subtitle'>{_html(subtitle)}</p>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str | None = None, icon: str | None = None, level: int = 2) -> None:
    level = 3 if level == 3 else 2
    prefix = f"{icon} " if icon else ""
    st.markdown(
        f"""
        <div class='vm-section-header'>
            <h{level}>{_html(prefix + title)}</h{level}>
            {f"<p>{_html(subtitle)}</p>" if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _badge_meta(status: Any, label: str | None = None) -> tuple[str, str, str]:
    """Return icon, label and semantic level for a status value."""
    raw = safe_display(status).lower().strip()
    text = label or format_status(raw)
    if raw in {"approved", "verified", "accepted", "processed", "completed", "active", "success"}:
        return "✅", text, "success"
    if raw in {"pending", "not_processed", "under_review", "submitted", "waiting", "unverified"}:
        return "⏳", text, "warning"
    if raw in {"rejected", "failed", "cancelled", "inactive", "error", "closed"}:
        return "❌", text, "error"
    return "ℹ️", text, "info"


def _badge_html(status: Any, label: str | None = None) -> str:
    """HTML badge for internal component cards only; callers should prefer status_badge()."""
    icon, text, level = _badge_meta(status, label)
    cls = {
        "success": "vm-badge-success",
        "warning": "vm-badge-warning",
        "error": "vm-badge-danger",
        "info": "vm-badge-info",
    }.get(level, "vm-badge-muted")
    return f"<span class='vm-badge {cls}'>{_html(icon + ' ' + text)}</span>"


def status_badge(status: Any, label: str | None = None) -> None:
    """
    Render a safe Streamlit-native status badge.

    This function intentionally does not return raw HTML. Use it as:
        status_badge(status)
    not st.write(status_badge(status)).
    """
    icon, text, level = _badge_meta(status, label)
    message = f"{icon} {text}"
    if level == "success":
        st.success(message)
    elif level == "warning":
        st.warning(message)
    elif level == "error":
        st.error(message)
    else:
        st.info(message)


def metric_card(label: str, value: Any, delta: Any | None = None, help_text: str | None = None) -> None:
    st.metric(label, value if value not in (None, "") else "—", delta=delta, help=help_text)


def info_card(title: str, body: str, icon: str = "ℹ️") -> None:
    st.markdown(f"<div class='vm-info-card'><strong>{_html(icon + ' ' + title)}</strong><br>{_html(body)}</div>", unsafe_allow_html=True)


def warning_card(title: str, body: str, icon: str = "⚠️") -> None:
    st.markdown(f"<div class='vm-warning-card'><strong>{_html(icon + ' ' + title)}</strong><br>{_html(body)}</div>", unsafe_allow_html=True)


def success_card(title: str, body: str, icon: str = "✅") -> None:
    st.markdown(f"<div class='vm-success-card'><strong>{_html(icon + ' ' + title)}</strong><br>{_html(body)}</div>", unsafe_allow_html=True)


def empty_state(title: str, message: str = "There is nothing to show yet.", icon: str = "📭") -> None:
    st.markdown(
        f"<div class='vm-empty-state'><div style='font-size:1.8rem'>{_html(icon)}</div>"
        f"<strong>{_html(title)}</strong><br><span>{_html(message)}</span></div>",
        unsafe_allow_html=True,
    )


def action_button_label(icon: str, label: str) -> str:
    return f"{icon} {label}"


def notification_card(notification: dict[str, Any]) -> None:
    title = notification.get("title", "Notification")
    message = truncate_text(notification.get("message", ""), 160)
    created = format_datetime(notification.get("created_at"))
    read_badge = _badge_html("processed", "Read") if notification.get("is_read") else _badge_html("pending", "Unread")
    st.markdown(
        f"""
        <div class='vm-notification-card'>
            <div style='display:flex;justify-content:space-between;gap:0.5rem;align-items:flex-start'>
                <strong>{_html(title)}</strong>{read_badge}
            </div>
            <div style='color:#8b949e;font-size:0.84rem;margin:0.25rem 0'>{_html(created)}</div>
            <div>{_html(message)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def profile_summary_card(title: str, fields: dict[str, Any], status: Any | None = None) -> None:
    rows = "".join(
        f"<div style='margin:0.25rem 0'><span style='color:#8b949e'>{_html(k)}:</span> <strong>{_html(v)}</strong></div>"
        for k, v in fields.items()
    )
    badge = _badge_html(status) if status else ""
    st.markdown(f"<div class='vm-profile-card'><div style='display:flex;justify-content:space-between'><strong>{_html(title)}</strong>{badge}</div>{rows}</div>", unsafe_allow_html=True)


def event_card(title: str, description: str, status: Any | None = None, meta: dict[str, Any] | None = None) -> None:
    meta_html = "".join(f"<span class='vm-badge vm-badge-muted'>{_html(k)}: {_html(v)}</span>" for k, v in (meta or {}).items())
    badge = _badge_html(status) if status else ""
    st.markdown(
        f"<div class='vm-event-card'><div style='display:flex;justify-content:space-between;gap:0.5rem'><strong>{_html(title)}</strong>{badge}</div>"
        f"<p style='color:#8b949e;line-height:1.55'>{_html(truncate_text(description, 220))}</p>{meta_html}</div>",
        unsafe_allow_html=True,
    )


def application_card(title: str, status: Any, body: str = "", meta: dict[str, Any] | None = None) -> None:
    meta_html = "".join(f"<span class='vm-badge vm-badge-muted'>{_html(k)}: {_html(v)}</span>" for k, v in (meta or {}).items())
    st.markdown(
        f"<div class='vm-application-card'><div style='display:flex;justify-content:space-between;gap:0.5rem'><strong>{_html(title)}</strong>{_badge_html(status)}</div>"
        f"<p style='color:#8b949e;line-height:1.55'>{_html(truncate_text(body, 220))}</p>{meta_html}</div>",
        unsafe_allow_html=True,
    )



def hero_section(title: str, subtitle: str, kicker: str = "Final Year Project") -> None:
    """Render a polished home-page hero section."""
    st.markdown(
        f"""
        <div class='vm-hero vm-fade-in'>
            <div class='vm-kicker'>{_html(kicker)}</div>
            <h1>{_html(title)}</h1>
            <p>{_html(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def role_card(icon: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class='vm-role-card vm-fade-in'>
            <div class='vm-role-icon'>{_html(icon)}</div>
            <div class='vm-role-title'>{_html(title)}</div>
            <div class='vm-role-text'>{_html(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feature_card(icon: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class='vm-feature-card vm-fade-in'>
            <div style='font-size:1.55rem;margin-bottom:0.45rem'>{_html(icon)}</div>
            <div class='vm-feature-title'>{_html(title)}</div>
            <div class='vm-feature-text'>{_html(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def action_card(title: str, body: str, icon: str = "✨") -> None:
    st.markdown(
        f"""
        <div class='vm-action-card vm-fade-in'>
            <div style='font-size:1.5rem;margin-bottom:0.4rem'>{_html(icon)}</div>
            <strong>{_html(title)}</strong>
            <div style='color:#8b949e;font-size:0.88rem;line-height:1.6;margin-top:0.35rem'>{_html(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
