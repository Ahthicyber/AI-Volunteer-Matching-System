"""Role-based navigation helpers for the Volunteer Matching System.

These helpers keep the visible navigation focused on the logged-in user's role.
Every page must still call require_auth(...); sidebar hiding is UX, not security.
"""
from __future__ import annotations

from typing import Any
import streamlit as st

from utils.session import current_user, is_logged_in, logout_user


def get_navigation_items(role: str) -> list[dict[str, str]]:
    """Return sidebar navigation items allowed for a role."""
    role = (role or "").lower().strip()
    common = [{"label": "🏠 Home", "page": "app.py"}]
    role_items: dict[str, list[dict[str, str]]] = {
        "volunteer": [
            {"label": "🙋 Volunteer Dashboard", "page": "pages/2_Volunteer_Dashboard.py"},
            {"label": "🎯 Recommended Events", "page": "pages/5_Recommendations.py"},
            {"label": "📋 My Applications", "page": "pages/6_My_Applications.py"},
        ],
        "ngo": [
            {"label": "🏢 NGO Dashboard", "page": "pages/3_NGO_Dashboard.py"},
            {"label": "📣 Event Management", "page": "pages/3_NGO_Dashboard.py"},
            {"label": "👥 Applicant Management", "page": "pages/3_NGO_Dashboard.py"},
        ],
        "admin": [
            {"label": "🔐 Admin Dashboard", "page": "pages/4_Admin_Dashboard.py"},
            {"label": "✅ Volunteer/NGO Review", "page": "pages/4_Admin_Dashboard.py"},
            {"label": "📄 Document Review", "page": "pages/4_Admin_Dashboard.py"},
            {"label": "📣 Event Approval", "page": "pages/4_Admin_Dashboard.py"},
            {"label": "📊 Evaluation", "page": "pages/7_Evaluation.py"},
            {"label": "🤖 ML Evaluation", "page": "pages/8_ML_Evaluation.py"},
            {"label": "📈 Advanced Analytics", "page": "pages/9_Advanced_Analytics.py"},
        ],
    }
    return common + role_items.get(role, [])


def redirect_after_login(role: str) -> str:
    """Return the landing page path for a role after login."""
    role = (role or "").lower().strip()
    return {
        "volunteer": "pages/2_Volunteer_Dashboard.py",
        "ngo": "pages/3_NGO_Dashboard.py",
        "admin": "pages/4_Admin_Dashboard.py",
    }.get(role, "app.py")


def render_role_based_sidebar() -> None:
    """Render a clean role-aware sidebar with user info, nav links, and logout."""
    with st.sidebar:
        st.markdown("### 🤝 VolunteerAI")
        st.caption("Role-based platform navigation")
        st.divider()

        if not is_logged_in():
            st.page_link("pages/1_Login.py", label="🔐 Login / Register")
            return

        user = current_user() or {}
        role = user.get("role", "")
        email = user.get("email", "")
        role_label = {"volunteer": "🙋 Volunteer", "ngo": "🏢 NGO", "admin": "🔐 Admin"}.get(role, role.title())

        st.markdown(f"**{email}**")
        st.caption(role_label)

        try:
            from notifications.notification_service import get_unread_count
            unread = get_unread_count(user.get("id"))
            st.caption(f"🔔 {unread} unread notification(s)")
        except Exception:
            pass

        st.divider()
        for item in get_navigation_items(role):
            st.page_link(item["page"], label=item["label"])

        st.divider()
        if st.button("🚪 Logout", key=f"logout_{role}_{user.get('id')}", use_container_width=True):
            logout_user()
            st.rerun()
