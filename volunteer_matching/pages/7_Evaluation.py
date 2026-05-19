"""
pages/7_Evaluation.py — Phase 8: Admin-only system evaluation dashboard.
"""

import streamlit as st
from ui.styles import apply_global_styles
import pandas as pd
from utils.session import init_session, current_user, logout_user, require_auth
from evaluation.evaluation_service import (
    get_system_metrics, get_match_quality_metrics,
    get_event_category_metrics, get_application_status_metrics,
)
from feedback.feedback_service import get_feedback_summary

st.set_page_config(page_title="Evaluation · VolunteerAI", page_icon="📊", layout="wide")
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
    .main .block-container { padding:2rem 3rem; max-width:1200px; }
    .metric-card { background:#161b22; border:1px solid #30363d; border-radius:12px;
                   padding:1.2rem 1.6rem; margin-bottom:0.8rem; text-align:center; }
    .metric-card:hover { border-color:#58a6ff; }
    .section-card { background:#161b22; border:1px solid #30363d; border-radius:12px;
                    padding:1.5rem 2rem; margin-bottom:1.2rem; }
    .stat-pill    { display:inline-block; background:#1f2937; border:1px solid #374151;
                    border-radius:999px; padding:0.25rem 0.85rem; font-size:0.78rem; color:#9ca3af; margin:0.15rem; }
    .badge-green  { background:#0d4429; border-color:#1a7f37; color:#3fb950; }
    .badge-blue   { background:#0c2d6b; border-color:#1f6feb; color:#58a6ff; }
    .badge-red    { background:#3d0e0e; border-color:#9e1515; color:#f85149; }
    .vm-divider   { border:none; border-top:1px solid #30363d; margin:1.5rem 0; }
    [data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important;
        color:#58a6ff!important; font-size:1.8rem!important; }
    [data-testid="stMetricLabel"] { color:#8b949e!important; font-size:0.75rem!important;
        text-transform:uppercase; letter-spacing:0.05em; }
    .stDataFrame { border-radius:8px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

init_session()
require_auth(allowed_roles=["admin"])
user = current_user()

with st.sidebar:
    st.markdown(f"""
        <div style='padding:1rem 0'>
            <div style='font-family:Syne,sans-serif;font-size:1.1rem;font-weight:800;color:#58a6ff'>🤝 VolunteerAI</div>
        </div>
        <hr style='border-color:#30363d;margin:0 0 0.75rem'>
        <div style='background:#161b22;border:1px solid #30363d;border-radius:8px;
                    padding:0.75rem 1rem;margin-bottom:0.75rem'>
            <div style='font-size:0.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em'>Logged in as</div>
            <div style='font-size:0.85rem;color:#e6edf3;margin-top:0.2rem;word-break:break-all'>{user['email']}</div>
            <span class='stat-pill badge-red'>🔐 Admin</span>
        </div>
    """, unsafe_allow_html=True)
    if st.button("🚪 Logout", key="eval_logout"):
        logout_user(); st.rerun()
    st.page_link("app.py",                     label="🏠 Home")
    st.page_link("pages/4_Admin_Dashboard.py",  label="🔐 Admin Dashboard")
    st.page_link("pages/9_Advanced_Analytics.py", label="📈 Advanced Analytics")

st.markdown("""
    <h1 style='font-size:2.2rem;margin-bottom:0.2rem'>📊 System Evaluation Dashboard</h1>
    <p style='color:#8b949e;margin-top:0'>
        Academic reporting metrics for the AI-Based Volunteer Matching System.
    </p>
""", unsafe_allow_html=True)
st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### 📈 Advanced Analytics")
    st.caption("A deeper admin-only analytics dashboard is available for user growth, engagement, match quality, document/OCR metrics, ML/Groq status, and rule-based insights.")
    st.page_link("pages/9_Advanced_Analytics.py", label="Open Advanced Analytics →")

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

# ── Load all data ─────────────────────────────────────────────────────────────
metrics   = get_system_metrics()
mq        = get_match_quality_metrics()
fb_sum    = get_feedback_summary()
cat_data  = get_event_category_metrics()
app_data  = get_application_status_metrics()


# ── Section 1: Core platform metrics ─────────────────────────────────────────
st.markdown("### 👥 Platform Overview")
c1,c2,c3,c4 = st.columns(4)
with c1: st.metric("Total Users",       metrics.get("total_users",0))
with c2: st.metric("Volunteers",         metrics.get("total_volunteers",0))
with c3: st.metric("NGO Users",          metrics.get("total_ngos",0))
with c4: st.metric("Approved NGOs",      metrics.get("approved_ngos",0))

c5,c6,c7,c8 = st.columns(4)
with c5: st.metric("Total Events",       metrics.get("total_events",0))
with c6: st.metric("Approved Events",    metrics.get("approved_events",0))
with c7: st.metric("Total Applications", metrics.get("total_applications",0))
with c8: st.metric("Accepted",           metrics.get("accepted_applications",0))

c9,c10,c11,c12 = st.columns(4)
avg_ms = metrics.get("average_match_score")
avg_fb = metrics.get("average_feedback_rating")
acc_rt = metrics.get("acceptance_rate",0)
with c9:  st.metric("Avg Match Score",   f"{avg_ms:.1f}%" if avg_ms else "—")
with c10: st.metric("Avg Feedback",      f"{avg_fb:.1f}/5" if avg_fb else "—")
with c11: st.metric("Acceptance Rate",   f"{acc_rt:.1f}%")
with c12: st.metric("Total Feedback",    metrics.get("total_feedback",0))

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)


# ── Section 2: Application status distribution ────────────────────────────────
st.markdown("### 📋 Application Status Distribution")
if app_data:
    col_t, col_c = st.columns([1, 2])
    with col_t:
        df_app = pd.DataFrame(app_data)
        df_app.columns = ["Status", "Count"]
        df_app["Status"] = df_app["Status"].str.capitalize()
        total_apps = df_app["Count"].sum()
        df_app["Percentage"] = (df_app["Count"] / total_apps * 100).round(1).astype(str) + "%"
        st.dataframe(df_app, use_container_width=True, hide_index=True)
    with col_c:
        st.bar_chart(
            df_app.set_index("Status")["Count"],
            color="#58a6ff",
            height=220,
        )
else:
    st.info("No application data yet.")

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)


# ── Section 3: Event category distribution ────────────────────────────────────
st.markdown("### 🎯 Approved Events by Cause Area")
if cat_data:
    col_t2, col_c2 = st.columns([1, 2])
    with col_t2:
        df_cat = pd.DataFrame(cat_data)
        df_cat.columns = ["Cause Area", "Count"]
        total_cat = df_cat["Count"].sum()
        df_cat["Share"] = (df_cat["Count"] / total_cat * 100).round(1).astype(str) + "%"
        st.dataframe(df_cat, use_container_width=True, hide_index=True)
    with col_c2:
        st.bar_chart(
            df_cat.set_index("Cause Area")["Count"],
            color="#3fb950",
            height=220,
        )
else:
    st.info("No approved events yet.")

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)


# ── Section 4: Match quality breakdown ───────────────────────────────────────
st.markdown("### 🤖 Match Quality Breakdown")
mq_c1, mq_c2, mq_c3 = st.columns(3)
with mq_c1:
    st.markdown(f"""
        <div class='metric-card' style='border-color:#1a7f37'>
            <div style='font-size:0.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>High Quality (≥75%)</div>
            <div style='font-family:Syne,sans-serif;font-size:2rem;font-weight:800;color:#3fb950'>{mq.get("high_quality_matches_count",0)}</div>
        </div>""", unsafe_allow_html=True)
with mq_c2:
    st.markdown(f"""
        <div class='metric-card' style='border-color:#9e6a03'>
            <div style='font-size:0.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>Medium Quality (50–75%)</div>
            <div style='font-family:Syne,sans-serif;font-size:2rem;font-weight:800;color:#f0883e'>{mq.get("medium_quality_matches_count",0)}</div>
        </div>""", unsafe_allow_html=True)
with mq_c3:
    st.markdown(f"""
        <div class='metric-card' style='border-color:#9e1515'>
            <div style='font-size:0.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>Low Quality (&lt;50%)</div>
            <div style='font-family:Syne,sans-serif;font-size:2rem;font-weight:800;color:#f85149'>{mq.get("low_quality_matches_count",0)}</div>
        </div>""", unsafe_allow_html=True)

mq_avg_score = mq.get("average_match_score")
mq_acc_avg   = mq.get("accepted_average_match_score")
mq_rej_avg   = mq.get("rejected_average_match_score")

qa1, qa2, qa3 = st.columns(3)
with qa1: st.metric("Overall Avg Match Score", f"{mq_avg_score:.1f}%" if mq_avg_score else "—")
with qa2: st.metric("Avg Score (Accepted)",     f"{mq_acc_avg:.1f}%" if mq_acc_avg else "—")
with qa3: st.metric("Avg Score (Rejected)",     f"{mq_rej_avg:.1f}%" if mq_rej_avg else "—")

# Match quality bar chart
mq_chart_data = {
    "High (≥75%)":    mq.get("high_quality_matches_count",0),
    "Medium (50-75%)":mq.get("medium_quality_matches_count",0),
    "Low (<50%)":     mq.get("low_quality_matches_count",0),
}
mq_df = pd.DataFrame({"Quality Band": list(mq_chart_data.keys()), "Count": list(mq_chart_data.values())})
if mq_df["Count"].sum() > 0:
    st.bar_chart(mq_df.set_index("Quality Band")["Count"], color="#a371f7", height=200)

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)


# ── Section 5: Feedback summary ───────────────────────────────────────────────
st.markdown("### ⭐ Feedback Summary")
fb1,fb2,fb3,fb4 = st.columns(4)
avg_r  = fb_sum.get("average_rating")
avg_vr = fb_sum.get("average_volunteer_rating")
avg_nr = fb_sum.get("average_ngo_rating")
avg_sr = fb_sum.get("average_secondary_rating")
with fb1: st.metric("Total Feedback",           fb_sum.get("total_feedback",0))
with fb2: st.metric("Avg Rating (Overall)",     f"{avg_r:.2f}/5"  if avg_r  else "—")
with fb3: st.metric("Avg Volunteer Rating",     f"{avg_vr:.2f}/5" if avg_vr else "—")
with fb4: st.metric("Avg NGO Rating",           f"{avg_nr:.2f}/5" if avg_nr else "—")

fb5,fb6 = st.columns(2)
with fb5: st.metric("Volunteer Feedback Count", fb_sum.get("total_volunteer_feedback",0))
with fb6: st.metric("NGO Feedback Count",       fb_sum.get("total_ngo_feedback",0))

if fb_sum.get("total_feedback",0) > 0:
    fb_chart_data = {
        "Volunteer Feedback": fb_sum.get("total_volunteer_feedback",0),
        "NGO Feedback":       fb_sum.get("total_ngo_feedback",0),
    }
    fb_df = pd.DataFrame({"Source": list(fb_chart_data.keys()), "Count": list(fb_chart_data.values())})
    st.bar_chart(fb_df.set_index("Source")["Count"], color="#ffa657", height=180)

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)


# ── Section 6: NGO metrics breakdown ─────────────────────────────────────────
st.markdown("### 🏢 NGO & Event Status")
ng1, ng2, ng3, ng4, ng5 = st.columns(5)
with ng1: st.metric("Approved NGOs",  metrics.get("approved_ngos",0))
with ng2: st.metric("Pending NGOs",   metrics.get("pending_ngos",0))
with ng3: st.metric("Rejected NGOs",  metrics.get("rejected_ngos",0))
with ng4: st.metric("Pending Events", metrics.get("pending_events",0))
with ng5: st.metric("Rejected Events",metrics.get("rejected_events",0))

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)
st.markdown("""
    <div style='background:#161b22;border:1px solid #1f6feb;border-radius:8px;
                padding:0.85rem 1.2rem;font-size:0.85rem;color:#58a6ff'>
        📌 <strong>Phase 8 complete.</strong>
        Groq AI integration, ML-based matching, OCR, notifications, and analytics are available in the latest build.
        This dashboard can be used for academic FYP reporting.
    </div>
""", unsafe_allow_html=True)
