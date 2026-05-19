"""
pages/5_Recommendations.py — Phase 9
Adds ML score alongside deterministic score.
Deterministic score remains PRIMARY for sorting.
"""

import streamlit as st
from ui.styles import apply_global_styles
from utils.session import init_session, current_user, logout_user, require_auth
from matching.matching_engine import get_recommendations_for_volunteer
from volunteer.volunteer_service import get_volunteer_profile
from applications.application_service import apply_to_event, get_application_status
from ml.ml_matcher import predict_ml_match
from ml.model_utils import model_exists
from ai.ai_service import test_groq_connection, generate_match_explanation

st.set_page_config(
    page_title="Recommendations · VolunteerAI",
    page_icon="🎯",
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
    .main .block-container { padding:2rem 3rem; max-width:1100px; }
    .vm-divider { border:none; border-top:1px solid #30363d; margin:1.5rem 0; }
    .score-bar-wrap { background:#21262d; border-radius:999px; height:8px; overflow:hidden; margin:0.3rem 0 0.1rem; }
    .score-bar-fill { height:8px; border-radius:999px; }
    .stButton > button { background:#238636!important; color:#fff!important;
        border:1px solid #2ea043!important; border-radius:6px!important; font-weight:500!important; }
    .stButton > button:hover { background:#2ea043!important; }
    .stTextArea textarea { background:#0d1117!important; border:1px solid #30363d!important;
        color:#e6edf3!important; border-radius:6px!important; }
    .stTextArea textarea:focus { border-color:#58a6ff!important; box-shadow:none!important; }
    [data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important; color:#58a6ff!important; font-size:1.4rem!important; }
    [data-testid="stMetricLabel"] { color:#8b949e!important; font-size:0.72rem!important; text-transform:uppercase; }
    label { color:#c9d1d9!important; }
</style>
""", unsafe_allow_html=True)

init_session()
require_auth(allowed_roles=["volunteer"])
user = current_user()

with st.sidebar:
    st.markdown("**🤝 VolunteerAI**")
    st.caption(user["email"])
    st.markdown("")
    if st.button("🚪 Logout", key="rec_logout"):
        logout_user(); st.rerun()
    st.page_link("app.py",                        label="🏠 Home")
    st.page_link("pages/2_Volunteer_Dashboard.py", label="🙋 My Profile")
    st.page_link("pages/6_My_Applications.py",     label="📋 My Applications")

st.markdown(
    "<h1 style='font-size:2.2rem;margin-bottom:0.2rem'>🎯 Recommended Volunteer Opportunities</h1>"
    "<p style='color:#8b949e;margin-top:0'>Personalised matches ranked by compatibility. Apply directly from this page.</p>",
    unsafe_allow_html=True,
)
st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

profile = get_volunteer_profile(user["id"])
if not profile:
    st.warning("👤 Complete your volunteer profile first to see recommendations.")
    st.page_link("pages/2_Volunteer_Dashboard.py", label="✏️ Complete My Profile →")
    st.stop()

# ML model badge
ml_available = model_exists()
if ml_available:
    st.success("🤖 **ML Enhancement Active** — Each event shows both Deterministic & ML match scores.")
else:
    st.info("ℹ️ ML model not trained yet. Showing deterministic scores only. "
            "Train the model via Admin → ML Evaluation page.")

# Phase 10.1: Manual AI infrastructure test only.
# This does not generate recommendations, alter rankings, or call Groq on rerun.
with st.expander("🧪 AI Infrastructure Test", expanded=False):
    st.caption(
        "Optional Groq connectivity check. This is explanation infrastructure only; "
        "deterministic recommendations remain authoritative and unchanged."
    )
    if "groq_test_result" not in st.session_state:
        st.session_state["groq_test_result"] = None

    if st.button("Test Groq Connection", key="test_groq_connection_btn"):
        with st.spinner("Testing optional Groq connection…"):
            ok, message = test_groq_connection()
            st.session_state["groq_test_result"] = {"ok": ok, "message": message}

    result = st.session_state.get("groq_test_result")
    if result:
        if result.get("ok"):
            st.success(result.get("message", "Groq connection successful."))
        else:
            st.warning(result.get("message", "Groq is not configured yet."))


# Phase 10.2: Session cache for manually generated AI match explanations.
# Keyed by event_id to avoid duplicate Groq calls during Streamlit reruns.
if "ai_match_explanations" not in st.session_state:
    st.session_state["ai_match_explanations"] = {}

with st.spinner("Calculating your matches…"):
    recommendations = get_recommendations_for_volunteer(user["id"])

if not recommendations:
    st.markdown("""
        <div style='background:#111827;border:1px dashed #374151;border-radius:12px;
                    padding:2.5rem;text-align:center'>
            <div style='font-size:3rem'>📭</div>
            <div style='font-size:1rem;color:#8b949e;margin-top:0.5rem'>No approved events yet. Check back soon.</div>
        </div>""", unsafe_allow_html=True)
    st.stop()

# Summary bar
top_score = recommendations[0]["final_score"]
c1, c2, c3 = st.columns(3)
with c1: st.metric("Events Found",   len(recommendations))
with c2: st.metric("Best Match",     f"{top_score:.1f}%")
with c3: st.metric("ML Model",       "Active ✅" if ml_available else "Not trained")
st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

_app_status_label = {
    "pending":   "⏳ Applied — Pending",
    "accepted":  "✅ Accepted",
    "rejected":  "❌ Rejected",
    "cancelled": "🚫 Cancelled",
}

def _score_color(s):
    return "#3fb950" if s >= 75 else ("#f0883e" if s >= 50 else "#f85149")

def _score_badge(s):
    if s >= 75: return "Strong Match"
    if s >= 50: return "Moderate Match"
    return "Low Match"

def _mini_bar(score: float, color: str) -> str:
    pct = min(max(score, 0), 100)
    return (f"<div class='score-bar-wrap'>"
            f"<div class='score-bar-fill' style='width:{pct}%;background:{color}'></div>"
            f"</div>")

for rank, rec in enumerate(recommendations, 1):
    det_score  = rec["final_score"]
    sc         = _score_color(det_score)
    event_id   = rec["id"]

    # ML prediction (secondary, graceful)
    ml_result = predict_ml_match(profile, rec) if ml_available else {"model_available": False}
    ml_score  = ml_result.get("ml_score_percentage")

    req_skills = [s.strip().title() for s in (rec.get("required_skills","") or "").split(",") if s.strip()]

    app = get_application_status(user["id"], event_id)

    with st.container(border=True):
        # Header row
        hc1, hc2 = st.columns([4, 1])
        with hc1:
            st.markdown(f"**#{rank}  {rec.get('title','—')}**")
            st.caption(
                f"🏢 {rec.get('organization_name','—')}  ·  "
                f"📍 {rec.get('city','—')}  ·  "
                f"📅 {rec.get('event_date','—')} {rec.get('event_time','')}  ·  "
                f"💻 {rec.get('mode','—')}  ·  "
                f"🎯 {rec.get('cause_area','—')}"
            )
            if req_skills:
                st.caption("🛠️ Skills: " + "  ".join(f"`{s}`" for s in req_skills))
        with hc2:
            st.metric("Deterministic", f"{det_score:.1f}%",
                      help="Primary score — used for sorting")

        # Score comparison row
        if ml_available and ml_score is not None:
            sc1, sc2, sc3 = st.columns([2, 2, 3])
            with sc1:
                st.markdown(
                    f"**🔢 Deterministic:** "
                    f"<span style='color:{sc};font-weight:700'>{det_score:.1f}%</span>  "
                    f"<span style='color:#484f58;font-size:0.75rem'>(Primary · sorts ranking)</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(_mini_bar(det_score, sc), unsafe_allow_html=True)
            with sc2:
                ml_color = _score_color(ml_score)
                st.markdown(
                    f"**🤖 ML Score:** "
                    f"<span style='color:{ml_color};font-weight:700'>{ml_score:.1f}%</span>  "
                    f"<span style='color:#484f58;font-size:0.75rem'>(Secondary · for reference)</span>",
                    unsafe_allow_html=True,
                )
                st.markdown(_mini_bar(ml_score, ml_color), unsafe_allow_html=True)
            with sc3:
                diff = det_score - ml_score
                diff_color = "#3fb950" if abs(diff) <= 10 else "#f0883e"
                agreement = "Models agree ✅" if abs(diff) <= 10 else f"Δ {abs(diff):.1f}% difference"
                st.caption(f"{agreement}")
                st.caption(f"💡 {rec.get('explanation','—')}")
        else:
            st.caption(f"💡 {rec.get('explanation','—')}")

        # Score breakdown expander
        with st.expander(f"📊 Score Breakdown — {rec.get('title','Event')}"):
            breakdown = [
                ("🛠️ Skills Match",    rec["skill_score"],        "40%", "#58a6ff"),
                ("🕐 Availability",     rec["availability_score"], "20%", "#a371f7"),
                ("📍 Location",         rec["location_score"],     "15%", "#3fb950"),
                ("🎯 Interests",        rec["interest_score"],     "15%", "#f0883e"),
                ("🎓 Experience",       rec["experience_score"],    "5%", "#ffa657"),
                ("💻 Mode",             rec["mode_score"],          "5%", "#79c0ff"),
            ]
            for label, raw_s, weight, color in breakdown:
                bc1, bc2 = st.columns([3, 1])
                with bc1:
                    st.markdown(
                        f"<div style='font-size:0.85rem;color:#c9d1d9;margin-bottom:0.1rem'>"
                        f"{label} <span style='color:#484f58;font-size:0.75rem'>(weight {weight})</span></div>"
                        f"{_mini_bar(raw_s, color)}"
                        f"<div style='font-size:0.75rem;color:#8b949e'>{raw_s:.1f} / 100</div>",
                        unsafe_allow_html=True,
                    )
                with bc2:
                    weighted = round(raw_s * float(weight.strip("%")) / 100, 1)
                    st.markdown(
                        f"<div style='text-align:right;font-family:Syne,sans-serif;"
                        f"font-weight:700;font-size:1.1rem;color:{color};padding-top:0.2rem'>"
                        f"+{weighted:.1f}</div><div style='text-align:right;font-size:0.72rem;color:#484f58'>pts</div>",
                        unsafe_allow_html=True,
                    )

        # Phase 10.2: Manual, cached AI match explanation.
        # This is explanation-only and never changes deterministic ranking, ML score, or applications.
        deterministic_breakdown = {
            "skills_score": rec.get("skill_score"),
            "availability_score": rec.get("availability_score"),
            "location_score": rec.get("location_score"),
            "interests_score": rec.get("interest_score"),
            "experience_score": rec.get("experience_score"),
            "mode_score": rec.get("mode_score"),
            "deterministic_explanation": rec.get("explanation"),
            "primary_score_note": "Deterministic score is authoritative and used for ranking.",
        }
        event_data_for_ai = {
            "event_id": event_id,
            "title": rec.get("title"),
            "organization_name": rec.get("organization_name"),
            "city": rec.get("city"),
            "event_date": rec.get("event_date"),
            "event_time": rec.get("event_time"),
            "mode": rec.get("mode"),
            "cause_area": rec.get("cause_area"),
            "required_skills": rec.get("required_skills"),
            "description": rec.get("description"),
        }

        with st.expander("✨ AI Match Explanation", expanded=False):
            st.caption(
                "Optional Groq explanation only. Deterministic score remains authoritative; "
                "AI does not change ranking or application decisions."
            )
            cache_key = str(event_id)
            cached_explanation = st.session_state["ai_match_explanations"].get(cache_key)

            if cached_explanation:
                if cached_explanation.get("success"):
                    st.markdown(cached_explanation.get("response", ""))
                else:
                    st.warning("AI explanation temporarily unavailable.")
            else:
                if st.button("Generate AI Match Explanation", key=f"ai_explain_{event_id}"):
                    with st.spinner("Generating AI explanation…"):
                        ai_result = generate_match_explanation(
                            volunteer_profile=profile,
                            event_data=event_data_for_ai,
                            deterministic_score=det_score,
                            deterministic_breakdown=deterministic_breakdown,
                            ml_score=ml_score,
                        )
                        st.session_state["ai_match_explanations"][cache_key] = ai_result
                        cached_explanation = ai_result

                if cached_explanation:
                    if cached_explanation.get("success"):
                        st.markdown(cached_explanation.get("response", ""))
                    else:
                        st.warning("AI explanation temporarily unavailable.")
                else:
                    st.info("Click the button to generate an optional AI explanation for this match.")

        # Application section
        if app:
            lbl = _app_status_label.get(app["status"], app["status"])
            st.info(f"{lbl}  ·  Applied: {str(app.get('applied_at',''))[:10]}")
            if app.get("ngo_response") and app["status"] == "rejected":
                st.error(f"NGO: {app['ngo_response']}")
        else:
            with st.expander(f"📝 Apply to: {rec.get('title','this event')}"):
                note = st.text_area(
                    "Optional message to the NGO",
                    placeholder="Tell the NGO why you're a great fit…",
                    key=f"note_{event_id}", height=70,
                )
                if st.button("🚀 Submit Application", key=f"apply_{event_id}"):
                    ok, msg = apply_to_event(user["id"], event_id, note)
                    if ok:
                        st.success(f"✅ {msg}"); st.rerun()
                    else:
                        st.error(f"❌ {msg}")

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)
st.page_link("pages/6_My_Applications.py", label="📋 View My Applications →")
