"""
AI Volunteer Matching System — Main Entry Point
Home screen, role-aware navigation, and startup bootstrap.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from db.schema import initialize_database
from ui.styles import apply_global_styles
from ui.components import hero_section, role_card, feature_card, section_header
from ui.layout import render_footer
from utils.session import init_session, restore_session_from_token, is_logged_in, current_user
from utils.navigation import render_role_based_sidebar, redirect_after_login

PROJECT_ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = PROJECT_ROOT / "uploads"
MODEL_DIR = PROJECT_ROOT / "data" / "models"
DATASET_DIR = PROJECT_ROOT / "data" / "dataset"

st.set_page_config(
    page_title="AI Volunteer Matching System",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_global_styles()


@st.cache_resource(show_spinner=False)
def _boot() -> bool:
    """Initialize runtime folders and database safely for local/Cloud runs."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    initialize_database()
    return True


try:
    _boot()
except Exception:
    st.error("Critical startup setup failed. Please check database/write permissions and deployment configuration.")
    st.stop()

init_session()
restore_session_from_token()
render_role_based_sidebar()


def _open_auth(mode: str, role: str | None = None) -> None:
    """Set auth navigation state and open the Login/Register page."""
    st.session_state["auth_mode"] = mode
    st.session_state["selected_role"] = role
    st.session_state["current_page"] = "Login"
    if role in {"volunteer", "ngo"}:
        st.session_state["reg_role"] = role
    try:
        st.switch_page("pages/1_Login.py")
    except Exception:
        st.rerun()


# Logged-in users get a focused landing card and dashboard shortcut.
if is_logged_in():
    user = current_user() or {}
    role = user.get("role", "")
    dest_page = redirect_after_login(role)
    role_label = {"volunteer": "Volunteer", "ngo": "NGO", "admin": "Admin"}.get(role, role.title())

    hero_section(
        "Welcome back to VolunteerAI",
        "Continue from your role-specific dashboard. Navigation is filtered so you only see the tools relevant to your account.",
        kicker=f"Signed in as {role_label}",
    )

    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.subheader(f"👋 {user.get('email', 'User')}")
            st.caption(f"Role: {role_label}")
        with c2:
            st.page_link(dest_page, label=f"Open {role_label} Dashboard", icon="➡️")

    render_footer()
    st.stop()


# Public home screen.
hero_section(
    "AI Volunteer Matching System",
    "A role-based platform that connects volunteers with verified NGOs using explainable matching, ML-assisted scoring, AI explanations, OCR document checks, notifications, and analytics.",
    kicker="Final Year Project · Streamlit + SQLite + AI",
)

cta1, cta2, cta3 = st.columns(3)
with cta1:
    if st.button("🙋 Register as Volunteer", key="home_register_volunteer", use_container_width=True):
        _open_auth("register", "volunteer")
with cta2:
    if st.button("🏢 Register as NGO", key="home_register_ngo", use_container_width=True):
        _open_auth("register", "ngo")
with cta3:
    if st.button("🔑 Login / Admin Login", key="home_login_admin", use_container_width=True):
        _open_auth("login", None)

section_header("Choose Your Role", "Each user type has a focused journey and protected dashboard.", icon="👥")
r1, r2, r3 = st.columns(3)
with r1:
    role_card("🙋", "Volunteer", "Create your profile, upload documents, receive recommended events, apply for opportunities, and submit feedback.")
with r2:
    role_card("🏢", "NGO", "Complete NGO verification, upload legal documents, post approved events, and manage volunteer applicants.")
with r3:
    role_card("🔐", "Admin", "Verify users and NGOs, review documents, approve events, monitor analytics, and manage system quality.")

section_header("Platform Features", "Built as a production-style final year project with explainable and assistive AI.", icon="✨")
f1, f2, f3 = st.columns(3)
with f1:
    feature_card("🎯", "Smart Matching", "Deterministic scoring remains primary and explainable for academic transparency.")
with f2:
    feature_card("🤖", "ML + Groq AI", "ML scores and AI explanations enhance recommendations without replacing decision logic.")
with f3:
    feature_card("📄", "OCR Verification", "Admins can review extracted document text and AI summaries while retaining manual authority.")
f4, f5, f6 = st.columns(3)
with f4:
    feature_card("🔔", "Notifications", "Users receive in-app updates for approvals, applications, documents, and system actions.")
with f5:
    feature_card("📊", "Analytics", "Admin dashboards provide engagement, conversion, match quality, and system health insights.")
with f6:
    feature_card("🛡️", "Role-Based Access", "Volunteer, NGO, and admin views are separated for clean and secure workflows.")

render_footer()
