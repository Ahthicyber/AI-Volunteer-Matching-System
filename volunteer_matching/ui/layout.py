"""
ui/layout.py
────────────
Shared layout helpers for polished Streamlit pages.
"""
from __future__ import annotations

from html import escape
from typing import Any, Iterable

import streamlit as st

from ui.styles import apply_global_styles
from utils.formatting import safe_display


def render_sidebar_user_card(user: dict[str, Any] | None) -> None:
    if not user:
        st.markdown("<div class='vm-card'><strong>Guest</strong><br><span style='color:#8b949e'>Please login to continue.</span></div>", unsafe_allow_html=True)
        return
    email = escape(safe_display(user.get("email", "User")))
    role = safe_display(user.get("role", "user"))
    st.markdown(
        f"""
        <div class='vm-card'>
            <div style='font-size:0.72rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em'>Logged in as</div>
            <div style='font-weight:700;word-break:break-all;margin:0.25rem 0'>{email}</div>
            <span class="vm-badge vm-badge-info">{escape(role.title())}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard_grid(items: Iterable[tuple[str, Any]], columns: int = 4) -> None:
    cols = st.columns(max(1, min(columns, 4)))
    for idx, (label, value) in enumerate(items):
        with cols[idx % len(cols)]:
            st.metric(label, value if value not in (None, "") else "—")


def render_page_container() -> None:
    st.markdown("<div class='vm-page-container'>", unsafe_allow_html=True)


def render_footer(text: str = "AI-Based Volunteer Matching System · Final Year Project") -> None:
    st.markdown(f"<div class='vm-footer'>{escape(text)}</div>", unsafe_allow_html=True)


def render_breadcrumb(*items: str) -> None:
    if items:
        st.caption(" / ".join(items))
