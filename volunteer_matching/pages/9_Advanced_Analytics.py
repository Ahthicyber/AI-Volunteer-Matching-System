"""
pages/9_Advanced_Analytics.py
──────────────────────────────
Phase 13 — Advanced Analytics + Admin Intelligence.

Admin-only, Streamlit-native dashboard using SQLite-safe analytics services.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
from ui.styles import apply_global_styles

from utils.session import init_session, require_auth, current_user, logout_user
from analytics.analytics_service import get_all_analytics
from analytics.insight_service import generate_rule_based_insights, generate_admin_recommendations
from analytics.chart_utils import dataframe_from_metrics, empty_chart_message, status_badge

st.set_page_config(page_title="Advanced Analytics · VolunteerAI", page_icon="📈", layout="wide")
apply_global_styles()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
    html,body,[class*="css"] { font-family:'DM Sans',sans-serif; }
    #MainMenu,footer,header  { visibility:hidden; }
    .stApp { background:#0d1117; color:#e6edf3; }
    [data-testid="stSidebar"] { background:#161b22!important; border-right:1px solid #30363d; }
    [data-testid="stSidebar"] * { color:#e6edf3!important; }
    h1,h2,h3 { font-family:'Syne',sans-serif!important; font-weight:800!important; color:#e6edf3!important; }
    .main .block-container { padding:2rem 3rem; max-width:1250px; }
    .vm-divider { border:none; border-top:1px solid #30363d; margin:1.5rem 0; }
    [data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important; color:#58a6ff!important; font-size:1.7rem!important; }
    [data-testid="stMetricLabel"] { color:#8b949e!important; font-size:0.75rem!important; text-transform:uppercase; }
    .stTabs [data-baseweb="tab-list"] { background:transparent; border-bottom:1px solid #30363d; }
    .stTabs [data-baseweb="tab"] { color:#8b949e!important; }
    .stTabs [aria-selected="true"] { color:#58a6ff!important; border-bottom:2px solid #58a6ff!important; }
</style>
""", unsafe_allow_html=True)

init_session()
require_auth(allowed_roles=["admin"])
user = current_user()

with st.sidebar:
    st.markdown("**🤝 VolunteerAI**")
    st.caption(f"Admin: {user['email']}")
    st.page_link("app.py", label="🏠 Home")
    st.page_link("pages/4_Admin_Dashboard.py", label="🔐 Admin Dashboard")
    st.page_link("pages/7_Evaluation.py", label="📊 Evaluation")
    st.page_link("pages/9_Advanced_Analytics.py", label="📈 Advanced Analytics")
    if st.button("🚪 Logout", key="analytics_logout"):
        logout_user(); st.rerun()

st.markdown("# 📈 Advanced Analytics")
st.caption("Admin-only intelligence dashboard for reporting, viva/demo evidence, and platform monitoring.")
st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

metrics = get_all_analytics()
users = metrics.get("user_growth", {})
vol = metrics.get("volunteer_engagement", {})
ngo = metrics.get("ngo_activity", {})
events = metrics.get("event_performance", {})
apps = metrics.get("application_conversion", {})
match = metrics.get("match_quality", {})
feedback = metrics.get("feedback_satisfaction", {})
docs = metrics.get("document_verification", {})
ml = metrics.get("ml_comparison", {})
health = metrics.get("system_health", {})

# Executive Summary
st.markdown("## Executive Summary")
s1, s2, s3, s4 = st.columns(4)
s5, s6, s7, s8 = st.columns(4)
with s1: st.metric("Total Users", users.get("total_users", 0))
with s2: st.metric("Approved NGOs", ngo.get("approved_ngos", 0))
with s3: st.metric("Approved Events", events.get("approved_events", 0))
with s4: st.metric("Applications", apps.get("total_applications", 0))
with s5: st.metric("Acceptance Rate", f"{apps.get('acceptance_rate', 0)}%")
with s6: st.metric("Avg Match Score", match.get("average_deterministic_score") or "—")
with s7: st.metric("Avg Feedback", feedback.get("overall_average_rating") or "—")
with s8: st.metric("Pending Tasks", health.get("pending_admin_tasks", 0))

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

tabs = st.tabs([
    "👥 Users",
    "🏢 NGOs",
    "📣 Events",
    "📋 Applications",
    "🎯 Match Quality",
    "⭐ Feedback",
    "📄 Documents",
    "🤖 ML & AI Status",
    "🧠 Insights",
])


def _bar_chart(rows, index_col, value_col, label="No data available yet."):
    df = dataframe_from_metrics(rows)
    if df.empty or index_col not in df.columns or value_col not in df.columns:
        st.info(empty_chart_message(label))
        return
    st.bar_chart(df.set_index(index_col)[value_col])
    st.dataframe(df, use_container_width=True, hide_index=True)


def _line_chart(rows, index_col, value_col, label="No trend data available yet."):
    df = dataframe_from_metrics(rows)
    if df.empty or index_col not in df.columns or value_col not in df.columns:
        st.info(empty_chart_message(label))
        return
    st.line_chart(df.set_index(index_col)[value_col])
    st.dataframe(df, use_container_width=True, hide_index=True)


with tabs[0]:
    st.markdown("### User Analytics")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Volunteers", users.get("volunteer_count", 0))
    with c2: st.metric("NGO Users", users.get("ngo_count", 0))
    with c3: st.metric("Admins", users.get("admin_count", 0))

    left, right = st.columns(2)
    with left:
        st.markdown("#### Role Distribution")
        _bar_chart(users.get("users_by_role", []), "role", "count", "No users found.")
    with right:
        st.markdown("#### Registrations Over Time")
        _line_chart(users.get("registrations_over_time", []), "date", "count", "No registration trend yet.")

    st.markdown("#### Volunteer Verification")
    _bar_chart(vol.get("verification_status", []), "status", "count", "No volunteer profiles yet.")


with tabs[1]:
    st.markdown("### NGO Analytics")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total NGOs", ngo.get("total_ngos", 0))
    with c2: st.metric("Approved NGOs", ngo.get("approved_ngos", 0))
    with c3: st.metric("NGOs With Events", ngo.get("ngos_with_events", 0))
    with c4: st.metric("Avg Events / NGO", ngo.get("average_events_per_ngo", 0))

    left, right = st.columns(2)
    with left:
        st.markdown("#### NGO Approval Status")
        _bar_chart(ngo.get("approval_status", []), "status", "count", "No NGO profiles yet.")
    with right:
        st.markdown("#### Most Active NGOs")
        _bar_chart(ngo.get("most_active_ngos", []), "organization_name", "event_count", "No NGO event activity yet.")


with tabs[2]:
    st.markdown("### Event Analytics")
    st.metric("Average Applications per Event", events.get("average_applications_per_event", 0))
    e1, e2 = st.columns(2)
    with e1:
        st.markdown("#### Events by Category")
        _bar_chart(events.get("events_by_cause_area", []), "category", "count", "No events by category yet.")
    with e2:
        st.markdown("#### Events by Mode")
        _bar_chart(events.get("events_by_mode", []), "mode", "count", "No events by mode yet.")
    e3, e4 = st.columns(2)
    with e3:
        st.markdown("#### Events by City")
        _bar_chart(events.get("events_by_city", []), "city", "count", "No city distribution yet.")
    with e4:
        st.markdown("#### Event Application Counts")
        _bar_chart(events.get("event_application_counts", []), "title", "applications", "No application counts yet.")


with tabs[3]:
    st.markdown("### Application Analytics")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total", apps.get("total_applications", 0))
    with c2: st.metric("Accepted", apps.get("accepted_applications", 0))
    with c3: st.metric("Rejected", apps.get("rejected_applications", 0))
    with c4: st.metric("Pending", apps.get("pending_applications", 0))
    r1, r2, r3 = st.columns(3)
    with r1: st.metric("Acceptance Rate", f"{apps.get('acceptance_rate', 0)}%")
    with r2: st.metric("Rejection Rate", f"{apps.get('rejection_rate', 0)}%")
    with r3: st.metric("Pending Rate", f"{apps.get('pending_rate', 0)}%")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Status Distribution")
        _bar_chart(apps.get("status_distribution", []), "status", "count", "No applications yet.")
    with right:
        st.markdown("#### Applications Over Time")
        _line_chart(apps.get("application_trends", []), "date", "count", "No application trend yet.")


with tabs[4]:
    st.markdown("### Match Quality Analytics")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Average Score", match.get("average_deterministic_score") or "—")
    with c2: st.metric("High Quality", match.get("high_quality_matches", 0))
    with c3: st.metric("Medium Quality", match.get("medium_quality_matches", 0))
    with c4: st.metric("Low Quality", match.get("low_quality_matches", 0))
    a1, a2 = st.columns(2)
    with a1: st.metric("Accepted Avg Score", match.get("accepted_average_match_score") or "—")
    with a2: st.metric("Rejected Avg Score", match.get("rejected_average_match_score") or "—")
    _bar_chart(match.get("score_distribution", []), "quality", "count", "No match scores calculated yet.")


with tabs[5]:
    st.markdown("### Feedback Analytics")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Feedback", feedback.get("total_feedback", 0))
    with c2: st.metric("Volunteer Avg", feedback.get("average_volunteer_rating") or "—")
    with c3: st.metric("NGO Avg", feedback.get("average_ngo_rating") or "—")
    with c4: st.metric("Overall Avg", feedback.get("overall_average_rating") or "—")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Rating Distribution")
        _bar_chart(feedback.get("rating_distribution", []), "rating", "count", "No feedback ratings yet.")
    with right:
        st.markdown("#### Satisfaction Trend")
        _line_chart(feedback.get("satisfaction_trend", []), "date", "average_rating", "No satisfaction trend yet.")


with tabs[6]:
    st.markdown("### Document Analytics")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Docs", docs.get("total_documents", 0))
    with c2: st.metric("Pending", docs.get("pending_documents", 0))
    with c3: st.metric("Verified", docs.get("verified_documents", 0))
    with c4: st.metric("Rejected", docs.get("rejected_documents", 0))
    o1, o2 = st.columns(2)
    with o1: st.metric("OCR Processed", docs.get("ocr_processed_count", 0))
    with o2: st.metric("OCR Failed", docs.get("ocr_failed_count", 0))
    left, right = st.columns(2)
    with left:
        st.markdown("#### Verification Status")
        _bar_chart(docs.get("verification_status", []), "status", "count", "No documents uploaded yet.")
    with right:
        st.markdown("#### OCR Status")
        _bar_chart(docs.get("ocr_status", []), "status", "count", "No OCR data yet.")


with tabs[7]:
    st.markdown("### ML & AI System Status")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Database", str(health.get("database_status", "unknown")).replace("_", " ").title())
    with c2: st.metric("ML Model", str(health.get("ml_model_status", "unknown")).replace("_", " ").title())
    with c3: st.metric("Groq", str(health.get("groq_status", "unknown")).replace("_", " ").title())
    with c4: st.metric("Notifications", str(health.get("notifications_status", "unknown")).replace("_", " ").title())
    c5, c6, c7 = st.columns(3)
    with c5: st.metric("Failed OCR", health.get("failed_ocr_count", 0))
    with c6: st.metric("Unread System Alerts", health.get("unread_system_notifications", 0))
    with c7: st.metric("Pending Admin Tasks", health.get("pending_admin_tasks", 0))

    st.markdown("#### ML Comparison")
    st.info(ml.get("comparison_explanation", "Deterministic scoring remains authoritative."))
    m1, m2 = st.columns(2)
    with m1: st.metric("Deterministic Avg", ml.get("deterministic_average_score") or "—")
    with m2: st.metric("ML Avg", ml.get("ml_average_score") or "Not stored")
    if ml.get("model_metadata"):
        st.dataframe(pd.DataFrame([ml.get("model_metadata")]), use_container_width=True, hide_index=True)


with tabs[8]:
    st.markdown("### Rule-Based Admin Insights")
    st.caption("These insights are generated using deterministic rules, not Groq, and are assistive only.")
    insights = generate_rule_based_insights(metrics)
    recommendations = generate_admin_recommendations(metrics)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Observations")
        for item in insights:
            st.info(item)
    with right:
        st.markdown("#### Recommendations")
        for item in recommendations:
            st.success(item)
