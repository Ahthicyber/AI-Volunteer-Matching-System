"""
pages/6_My_Applications.py — Bugfix
Fixes: status badges not showing, raw code/dicts in detail boxes,
       event details rendered as code instead of text.
All content uses native Streamlit components only.
"""

import streamlit as st
from ui.styles import apply_global_styles
from collections import Counter
from utils.session import init_session, current_user, logout_user, require_auth
from applications.application_service import (
    get_applications_for_volunteer, cancel_application,
)
from notifications.notification_service import get_notifications_for_user
from notifications.notification_utils import format_notification_time
from feedback.feedback_service import (
    submit_feedback, has_feedback, get_feedback_for_application,
)

st.set_page_config(
    page_title="My Applications · VolunteerAI",
    page_icon="📋",
    layout="wide",
)
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
    .main .block-container { padding:2rem 3rem; max-width:1000px; }
    .vm-divider { border:none; border-top:1px solid #30363d; margin:1.5rem 0; }
    .stButton > button { background:#238636!important; color:#fff!important;
        border:1px solid #2ea043!important; border-radius:6px!important; font-weight:500!important; }
    .stButton > button:hover { background:#2ea043!important; }
    .stTextArea textarea { background:#0d1117!important; border:1px solid #30363d!important;
        color:#e6edf3!important; border-radius:6px!important; }
    .stTextArea textarea:focus { border-color:#58a6ff!important; box-shadow:none!important; }
    [data-baseweb="select"] > div { background:#0d1117!important; border-color:#30363d!important; color:#e6edf3!important; }
    [data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important; color:#58a6ff!important; font-size:1.6rem!important; }
    [data-testid="stMetricLabel"] { color:#8b949e!important; font-size:0.75rem!important; text-transform:uppercase; }
    label { color:#c9d1d9!important; font-size:0.85rem!important; }
</style>
""", unsafe_allow_html=True)

init_session()
require_auth(allowed_roles=["volunteer"])
user = current_user()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("**🤝 VolunteerAI**")
    st.caption(user["email"])
    st.markdown("")
    if st.button("🚪 Logout", key="myapp_logout"):
        logout_user(); st.rerun()
    st.page_link("app.py",                        label="🏠 Home")
    st.page_link("pages/2_Volunteer_Dashboard.py", label="🙋 My Profile")
    st.page_link("pages/5_Recommendations.py",     label="🎯 Recommendations")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='font-size:2.2rem;margin-bottom:0.2rem'>📋 My Applications</h1>"
    "<p style='color:#8b949e;margin-top:0'>Track your applications and share your experience.</p>",
    unsafe_allow_html=True,
)
st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

applications = get_applications_for_volunteer(user["id"])
application_notifications = get_notifications_for_user(user["id"], limit=50)

if not applications:
    st.info("No applications yet — browse recommended events and apply to get started.")
    st.page_link("pages/5_Recommendations.py", label="🎯 Browse Events →")
    st.stop()

# ── Summary metrics ───────────────────────────────────────────────────────────
sc = Counter(a["status"] for a in applications)
m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.metric("Total",     len(applications))
with m2: st.metric("Pending",   sc.get("pending",   0))
with m3: st.metric("Accepted",  sc.get("accepted",  0))
with m4: st.metric("Rejected",  sc.get("rejected",  0))
with m5: st.metric("Cancelled", sc.get("cancelled", 0))

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

# ── Status helpers — NO raw HTML, all native ───────────────────────────────────
_status_label = {
    "pending":   "⏳ Pending",
    "accepted":  "✅ Accepted",
    "rejected":  "❌ Rejected",
    "cancelled": "🚫 Cancelled",
}

RELEVANCE_OPT = ["Very Relevant", "Relevant", "Somewhat Relevant", "Not Relevant"]

for app in applications:
    status  = app.get("status", "pending")
    aid     = app["id"]
    label   = _status_label.get(status, status.capitalize())
    score_s = f"{app['match_score']:.1f}%" if app.get("match_score") is not None else "—"

    with st.container(border=True):
        # ── Top row: event title + status badge ──────────────────────────────
        row1, row2 = st.columns([4, 1])
        with row1:
            st.markdown(f"**{app.get('event_title','—')}**")
        with row2:
            st.markdown(f"**{label}**")

        # ── Event details — plain text via st.caption ─────────────────────────
        st.caption(
            f"🏢 {app.get('organization_name','—')}  ·  "
            f"📍 {app.get('event_city','—')}  ·  "
            f"📅 {app.get('event_date','—')} {app.get('event_time','')}"
        )
        st.caption(
            f"💻 {app.get('mode','—')}  ·  "
            f"🎯 {app.get('cause_area','—')}  ·  "
            f"🤖 Match: {score_s}"
        )
        st.caption(f"Applied: {str(app.get('applied_at',''))[:10]}")
        if status in ("accepted", "rejected"):
            ntype = "application_accepted" if status == "accepted" else "application_rejected"
            related_note = next(
                (n for n in application_notifications
                 if n.get("notification_type") == ntype and n.get("related_entity_id") == app.get("id")),
                None,
            )
            if related_note:
                st.caption(f"🔔 Application {status} — notified on {format_notification_time(related_note.get('created_at'))}")

        # ── Volunteer note ────────────────────────────────────────────────────
        if app.get("volunteer_note"):
            st.caption(f"📝 Your note: {app['volunteer_note']}")

        # ── NGO response ──────────────────────────────────────────────────────
        if app.get("ngo_response"):
            if status == "accepted":
                st.success(f"💬 NGO response: {app['ngo_response']}")
            elif status == "rejected":
                st.error(f"💬 NGO response: {app['ngo_response']}")
            else:
                st.info(f"💬 NGO response: {app['ngo_response']}")

        # ── Actions by status ─────────────────────────────────────────────────
        if status == "pending":
            if st.button("🚫 Cancel Application", key=f"cancel_{aid}"):
                ok, msg = cancel_application(aid, user["id"])
                if ok:
                    st.success(f"✅ {msg}"); st.rerun()
                else:
                    st.error(f"❌ {msg}")

        elif status == "accepted":
            already = has_feedback(aid, "volunteer")
            if already:
                fb_list = get_feedback_for_application(aid)
                vol_fb  = next(
                    (f for f in fb_list if f["feedback_from"] == "volunteer"), None
                )
                if vol_fb:
                    stars = "⭐" * vol_fb["rating"]
                    st.success(
                        f"✅ Feedback submitted  ·  "
                        f"{stars} Event: {vol_fb['rating']}/5  ·  "
                        f"NGO professionalism: {vol_fb.get('secondary_rating','—')}/5  ·  "
                        f"Match relevance: {vol_fb.get('match_relevance','—')}"
                    )
                    if vol_fb.get("comments"):
                        st.caption(f"Comments: {vol_fb['comments']}")
            else:
                with st.expander(f"⭐ Leave Feedback for: {app.get('event_title','this event')}"):
                    with st.form(f"fb_form_{aid}"):
                        fc1, fc2 = st.columns(2)
                        with fc1:
                            ev_rating = st.selectbox(
                                "Event Experience Rating *",
                                [1, 2, 3, 4, 5], index=4,
                                format_func=lambda x: f"{'⭐'*x} ({x}/5)",
                                key=f"evr_{aid}",
                            )
                        with fc2:
                            ngo_rating = st.selectbox(
                                "NGO Professionalism Rating *",
                                [1, 2, 3, 4, 5], index=4,
                                format_func=lambda x: f"{'⭐'*x} ({x}/5)",
                                key=f"ngor_{aid}",
                            )
                        rel = st.selectbox(
                            "How relevant was this event?",
                            RELEVANCE_OPT, key=f"rel_{aid}",
                        )
                        comments = st.text_area(
                            "Comments (optional)",
                            placeholder="Describe your experience…",
                            key=f"cmt_{aid}", height=80,
                        )
                        fb_sub = st.form_submit_button(
                            "📤 Submit Feedback", use_container_width=True
                        )

                    if fb_sub:
                        ok, msg = submit_feedback(
                            application_id   = aid,
                            user_id          = user["id"],
                            feedback_from    = "volunteer",
                            rating           = ev_rating,
                            secondary_rating = ngo_rating,
                            attended         = True,
                            match_relevance  = rel,
                            comments         = comments,
                        )
                        if ok:
                            st.success(f"✅ {msg}"); st.rerun()
                        else:
                            st.error(f"❌ {msg}")

    st.markdown("")   # spacing between cards
