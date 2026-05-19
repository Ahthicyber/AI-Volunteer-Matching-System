"""
pages/3_NGO_Dashboard.py — Phase 8.5
Improved NGO profile with summary card, extended fields, and fixed approval flow.
"""

import streamlit as st
from datetime import date, datetime
from ui.styles import apply_global_styles
from ui.components import status_badge
from utils.session import init_session, current_user, logout_user, require_auth
from ngo.ngo_service import get_ngo_profile, upsert_ngo_profile, get_ngo_verification_status
from ngo.document_service import upload_ngo_document, get_documents_for_ngo
from events.event_service import create_event, update_event, get_events_by_ngo
from applications.application_service import (
    get_applications_for_ngo, update_application_status, get_application_counts_for_ngo,
)
from feedback.feedback_service import submit_feedback, has_feedback, get_feedback_for_application
from ai.ai_service import improve_event_description
from notifications.notification_service import get_notifications_for_user, mark_notification_read
from notifications.notification_utils import format_notification_time, get_notification_icon, truncate_notification

st.set_page_config(page_title="NGO Dashboard · VolunteerAI", page_icon="🏢", layout="wide")
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
    .vm-card  { background:#161b22; border:1px solid #30363d; border-radius:12px; padding:1.5rem 2rem; margin-bottom:1rem; }
    .ev-card  { background:#161b22; border:1px solid #30363d; border-radius:10px; padding:1.2rem 1.6rem; margin-bottom:0.8rem; }
    .app-card { background:#161b22; border:1px solid #30363d; border-radius:10px; padding:1.2rem 1.5rem; margin-bottom:0.8rem; }
    .fb-card  { background:#0c2d6b; border:1px solid #1f6feb; border-radius:8px; padding:0.9rem 1.2rem; margin-top:0.6rem; }
    .stat-pill    { display:inline-block; background:#1f2937; border:1px solid #374151;
                    border-radius:999px; padding:0.25rem 0.85rem; font-size:0.78rem; color:#9ca3af; margin:0.15rem; }
    .badge-green  { background:#0d4429; border-color:#1a7f37; color:#3fb950; }
    .badge-orange { background:#3d1f00; border-color:#9e4a00; color:#f0883e; }
    .badge-red    { background:#3d0e0e; border-color:#9e1515; color:#f85149; }
    .badge-blue   { background:#0c2d6b; border-color:#1f6feb; color:#58a6ff; }
    .badge-grey   { background:#21262d; border-color:#484f58; color:#8b949e; }
    .vm-divider   { border:none; border-top:1px solid #30363d; margin:1.5rem 0; }
    .stButton > button { background:#238636!important; color:#fff!important;
        border:1px solid #2ea043!important; border-radius:6px!important; font-weight:500!important; }
    .stButton > button:hover { background:#2ea043!important; }
    .stTextInput > div > input, .stTextArea textarea, .stNumberInput input {
        background:#0d1117!important; border:1px solid #30363d!important;
        color:#e6edf3!important; border-radius:6px!important; }
    .stTextInput > div > input:focus, .stTextArea textarea:focus {
        border-color:#58a6ff!important; box-shadow:none!important; }
    [data-baseweb="select"] > div { background:#0d1117!important; border-color:#30363d!important; color:#e6edf3!important; }
    .stMultiSelect [data-baseweb="tag"] { background:#1f6feb!important; color:#fff!important; }
    .stTabs [data-baseweb="tab-list"] { background:transparent; border-bottom:1px solid #30363d; }
    .stTabs [data-baseweb="tab"]      { color:#8b949e!important; }
    .stTabs [aria-selected="true"]    { color:#58a6ff!important; border-bottom:2px solid #58a6ff!important; }
    [data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important; color:#58a6ff!important; font-size:1.6rem!important; }
    [data-testid="stMetricLabel"] { color:#8b949e!important; font-size:0.75rem!important; text-transform:uppercase; }
    label { color:#c9d1d9!important; font-size:0.88rem!important; }
    div[data-testid="stCheckbox"] label { color:#c9d1d9!important; }
</style>
""", unsafe_allow_html=True)

init_session()
require_auth(allowed_roles=["ngo"])
user = current_user()

with st.sidebar:
    st.markdown(f"""
        <div style='padding:1rem 0'>
            <div style='font-family:Syne,sans-serif;font-size:1.1rem;font-weight:800;color:#58a6ff'>🤝 VolunteerAI</div>
        </div>
        <hr style='border-color:#30363d;margin:0 0 0.75rem'>
        <div style='background:#161b22;border:1px solid #30363d;border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.75rem'>
            <div style='font-size:0.7rem;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em'>Logged in as</div>
            <div style='font-size:0.85rem;color:#e6edf3;margin-top:0.2rem;word-break:break-all'>{user['email']}</div>
            <span class='vm-badge vm-badge-info'>🏢 NGO</span>
        </div>
    """, unsafe_allow_html=True)
    if st.button("🚪 Logout", key="ngo_logout"):
        logout_user(); st.rerun()
    st.page_link("app.py", label="🏠 Home")

st.markdown(f"<h1 style='font-size:2.2rem;margin-bottom:0.1rem'>🏢 NGO Dashboard</h1>"
            f"<p style='color:#8b949e;margin-top:0'>Welcome, <strong style='color:#3fb950'>{user['email']}</strong></p>",
            unsafe_allow_html=True)
st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

# ── NGO Landing Metrics ──────────────────────────────────────────────────────
try:
    _profile_metrics = get_ngo_profile(user["id"])
    _docs_metrics = get_documents_for_ngo(user["id"]) if _profile_metrics else []
    _events_metrics = get_events_by_ngo(_profile_metrics["id"]) if _profile_metrics else []
    _apps_counts = get_application_counts_for_ngo(user["id"]) if _profile_metrics else {"total": 0, "accepted": 0}
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Verification", (_profile_metrics or {}).get("verification_status", "not submitted").capitalize())
    with c2: st.metric("Documents", len(_docs_metrics))
    with c3: st.metric("Approved Events", len([e for e in _events_metrics if e.get("status") == "approved"]))
    with c4: st.metric("Pending Events", len([e for e in _events_metrics if e.get("status") == "pending"]))
    with c5: st.metric("Applicants", _apps_counts.get("total", 0))
except Exception:
    st.info("Dashboard summary is temporarily unavailable.")

# ── Recent Notifications ─────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("### 🔔 Recent Notifications")
    notes = get_notifications_for_user(user["id"], limit=5)
    if not notes:
        st.caption("No recent notifications yet.")
    for note in notes:
        icon = get_notification_icon(note.get("notification_type"))
        state = "Unread" if not note.get("is_read") else "Read"
        st.markdown(f"**{icon} {note.get('title','Notification')}** · {state}")
        st.caption(f"{format_notification_time(note.get('created_at'))} — {truncate_notification(note.get('message'), 180)}")
        if not note.get("is_read"):
            if st.button("Mark read", key=f"ngo_note_read_{note['id']}"):
                mark_notification_read(note["id"], user["id"])
                st.rerun()

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)


tab_profile, tab_documents, tab_events, tab_applicants = st.tabs([
    "🏛️  NGO Profile", "📄  NGO Documents", "📣  Events", "👥  Applicants"
])

CAUSE_OPTIONS = ["Education","Environment","Health","Poverty Alleviation","Disaster Relief",
                 "Women Empowerment","Youth Development","Animal Welfare","Arts & Culture","Human Rights","Other"]
SKILLS_OPT = ["Teaching","Mentoring","Fundraising","Event Management","First Aid","Graphic Design",
              "Social Media","Content Writing","Data Entry","Public Speaking","Photography",
              "Community Outreach","Translation","IT Support","Research"]
CAUSE_OPT  = ["Education","Health","Environment","Poverty Relief","Animal Welfare","Women Empowerment",
              "Youth Development","Disaster Relief","Mental Health","Elderly Care"]
EXP_OPT    = ["Anyone","Beginner","Intermediate","Experienced"]
MODE_OPT   = ["On-site","Online","Hybrid"]
GENDER_OPT = ["Anyone","Male","Female"]
EDU_OPT    = ["Anyone","High School","Intermediate","Undergraduate","Graduate","Postgraduate"]
TIME_OPTIONS = [
    "08:00 AM", "09:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
    "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM", "05:00 PM",
    "06:00 PM", "07:00 PM", "08:00 PM", "09:00 PM",
]


def _reset_event_form_state() -> None:
    """Clear create-event widget values after a successful submit."""
    for key in (
        "event_title", "event_description", "event_required_skills", "event_city",
        "event_date", "event_time", "event_duration", "event_capacity",
        "event_cause_area", "event_experience", "event_mode", "event_gender",
        "event_min_age", "event_max_age", "event_education", "event_location",
    ):
        st.session_state.pop(key, None)


def _date_from_string(value: str):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except Exception:
        return date.today()


def _time_index(value: str) -> int:
    try:
        return TIME_OPTIONS.index(str(value))
    except Exception:
        return 0

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — NGO PROFILE
# ══════════════════════════════════════════════════════════════════════════════
with tab_profile:
    vstatus = get_ngo_verification_status(user["id"])
    status  = vstatus["status"]
    profile = get_ngo_profile(user["id"])

    # Status banner
    _sc = {
        "not_submitted": ("#111827","#374151","#9ca3af","⬜","Profile Not Submitted","Submit your NGO profile for verification."),
        "pending":       ("#261d0d","#9e6a03","#f0883e","⏳","Pending Admin Review","Your profile is awaiting review."),
        "approved":      ("#0d2a1a","#1a7f37","#3fb950","✅","Verified NGO","Your NGO is verified and active."),
        "rejected":      ("#2a0d0d","#9e1515","#f85149","❌","Verification Rejected","Update and resubmit your profile."),
    }
    bg,border,color,icon,lbl,msg2 = _sc.get(status, _sc["not_submitted"])
    st.markdown(f"""
        <div style='background:{bg};border:1px solid {border};border-radius:10px;
                    padding:1.2rem 1.5rem;margin-bottom:1rem'>
            <div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.3rem'>
                <span style='font-size:1.3rem'>{icon}</span>
                <span style='font-family:Syne,sans-serif;font-weight:700;color:{color}'>{lbl}</span>
            </div>
            <div style='font-size:0.88rem;color:#c9d1d9'>{msg2}</div>
            {'<div style="margin-top:0.5rem;background:#1a0000;border:1px solid #9e1515;border-radius:5px;padding:0.4rem 0.8rem;font-size:0.82rem;color:#f85149"><strong>Reason:</strong> ' + str(vstatus.get("rejection_reason","")) + '</div>' if status=="rejected" and vstatus.get("rejection_reason") else ""}
        </div>
    """, unsafe_allow_html=True)

    # If approved and profile exists — show summary card first
    if status == "approved" and profile:
        st.markdown(f"""
            <div class='vm-card' style='border-color:#1a7f37'>
                <div style='display:flex;align-items:flex-start;gap:1.2rem;flex-wrap:wrap'>
                    <div style='font-size:3rem'>🏢</div>
                    <div style='flex:1'>
                        <div style='font-family:Syne,sans-serif;font-weight:800;font-size:1.3rem;color:#e6edf3'>
                            {profile.get("organization_name","—")}
                        </div>
                        <div style='font-size:0.85rem;color:#8b949e;line-height:1.9;margin-top:0.3rem'>
                            <span>👤 {profile.get("contact_person","—")}</span> &nbsp;·&nbsp;
                            <span>📞 {profile.get("phone") or "—"}</span> &nbsp;·&nbsp;
                            <span>📍 {profile.get("city","—")}</span>
                        </div>
                        <div style='font-size:0.85rem;color:#8b949e;line-height:1.9'>
                            <span>🏷️ Reg#: {profile.get("registration_number") or "—"}</span> &nbsp;·&nbsp;
                            <span>🌐 {profile.get("website") or "—"}</span>
                        </div>
                        <div style='margin-top:0.5rem;font-size:0.82rem;color:#8b949e'>
                            🎯 {profile.get("cause_areas","—")}
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Profile form — always show for not_submitted/rejected, expandable otherwise
    show_form = status in ("not_submitted", "rejected") or not profile
    if not show_form:
        show_form = st.checkbox("✏️ Edit NGO Profile", key="edit_ngo_profile")
        if not show_form:
            st.info("ℹ️ Click 'Edit NGO Profile' above to update your details. "
                    "Changing critical fields will reset your verification status.")

    if show_form:
        if profile and status == "approved":
            st.markdown("<div style='font-size:0.83rem;color:#f0883e;margin-bottom:0.8rem'>"
                        "⚠️ Changing organisation name, registration number, address, or legal document "
                        "will reset verification to <strong>Pending</strong>.</div>",
                        unsafe_allow_html=True)

        def _pre(k, d=""): return profile[k] if profile and profile.get(k) not in (None,"") else d
        def _causes():
            if not profile or not profile.get("cause_areas"): return []
            return [c.strip() for c in profile["cause_areas"].split(",") if c.strip() in CAUSE_OPTIONS]

        with st.form("ngo_profile_form"):
            st.markdown("**Organisation Details**")
            fc1, fc2 = st.columns(2)
            with fc1:
                org     = st.text_input("Organisation Name *",  value=_pre("organization_name"))
                contact = st.text_input("Contact Person Name *", value=_pre("contact_person"))
                city_f  = st.text_input("City *",               value=_pre("city"))
                address = st.text_input("Address",              value=_pre("address"), placeholder="Street address")
            with fc2:
                reg     = st.text_input("Registration Number (numeric only)", value=_pre("registration_number"))
                phone   = st.text_input("Phone",   value=_pre("phone"))
                web     = st.text_input("Website", value=_pre("website"))

            st.markdown("**About Your NGO**")
            causes = st.multiselect("Cause Areas *", CAUSE_OPTIONS, default=_causes())
            aim    = st.text_area("Aim",        value=_pre("aim"),        placeholder="What does your NGO aim to achieve?", height=70)
            objs   = st.text_area("Objectives", value=_pre("objectives"), placeholder="List your key objectives…", height=70)
            svcs   = st.text_area("Services",   value=_pre("services"),   placeholder="Describe the services you provide…", height=70)
            desc   = st.text_area("Description",value=_pre("description"),height=80)
            psub   = st.form_submit_button("📤 Submit Profile" if not profile else "💾 Update & Resubmit",
                                           use_container_width=True)

        if psub:
            # Numeric-only registration number validation
            reg_clean = (reg or "").strip()
            if reg_clean and not reg_clean.isdigit():
                st.error("❌ Registration number must contain numbers only.")
            else:
                ok, m = upsert_ngo_profile(
                    user["id"], org, reg_clean, contact, phone, city_f,
                    ", ".join(causes), desc, web,
                    address=address, aim=aim, objectives=objs, services=svcs,
                )
                if ok:
                    st.success(f"✅ {m}"); st.rerun()
                else:
                    st.error(f"❌ {m}")



# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — NGO DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════
with tab_documents:
    st.markdown("### 📄 NGO Documents")
    st.info("Upload legal documents to help admin verify your NGO. Admin verification remains manual.")

    profile_for_docs = get_ngo_profile(user["id"])
    if not profile_for_docs:
        st.warning("Create your NGO profile before uploading verification documents.")
    else:
        doc_types = [
            "Registration Certificate", "Tax Certificate", "Authorization Letter",
            "NGO License", "Address Proof", "Bank Letter", "Other",
        ]
        with st.container(border=True):
            st.markdown("#### Upload NGO Document")
            with st.form("ngo_document_upload_form", clear_on_submit=True):
                dtype = st.selectbox("Document Type", doc_types)
                up_file = st.file_uploader("Choose PDF/JPG/PNG", type=["pdf", "jpg", "jpeg", "png"])
                submitted = st.form_submit_button("📤 Upload Document", use_container_width=True)
            if submitted:
                ok, msg = upload_ngo_document(user["id"], dtype, up_file)
                if ok:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

        st.markdown("#### Uploaded Documents")
        docs = get_documents_for_ngo(user["id"])
        if not docs:
            st.info("No NGO documents uploaded yet.")
        else:
            _status_icon = {"pending": "⏳", "verified": "✅", "rejected": "❌"}
            _ocr_label = {"not_processed": "OCR pending", "processed": "OCR processed", "failed": "OCR failed"}
            for doc in docs:
                status = doc.get("verification_status", "pending")
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{doc.get('document_type','Document')}** · `{doc.get('original_filename') or doc.get('file_path','').split('/')[-1]}`")
                        st.caption(f"Uploaded: {str(doc.get('uploaded_at',''))[:10]} · {_ocr_label.get(doc.get('ocr_status','not_processed'), doc.get('ocr_status',''))}")
                        if doc.get("admin_notes"):
                            st.caption(f"📝 Admin notes: {doc.get('admin_notes')}")
                    with c2:
                        st.markdown(f"**{_status_icon.get(status,'•')} {status.capitalize()}**")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — EVENT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab_events:
    ngo_profile = get_ngo_profile(user["id"])
    if not ngo_profile:
        st.warning("⚠️ Create your NGO profile first."); st.stop()
    if ngo_profile.get("verification_status") != "approved":
        st.markdown("""
            <div style='background:#261d0d;border:1px solid #9e6a03;border-radius:10px;
                        padding:1.5rem;text-align:center'>
                <div style='font-size:2rem'>⏳</div>
                <div style='font-family:Syne,sans-serif;font-weight:700;color:#f0883e;font-size:1.1rem;margin:0.4rem 0'>
                    NGO must be verified before posting events.</div>
            </div>""", unsafe_allow_html=True)
        st.stop()

    ngo_pid = ngo_profile["id"]
    st.markdown("### ➕ Post New Event")
    if st.session_state.pop("event_created_success", False):
        st.success("✅ Event submitted for admin approval. The form has been reset.")

    with st.form("create_event_form", clear_on_submit=True):
        et = st.text_input("Event Title *", key="event_title")
        ed = st.text_area("Description *", height=80, key="event_description")
        fc1, fc2 = st.columns(2)
        with fc1:
            esk  = st.multiselect("Required Skills *", SKILLS_OPT, key="event_required_skills")
            eca  = st.selectbox("Cause Area *", CAUSE_OPT, key="event_cause_area")
            eex  = st.selectbox("Experience Level *", EXP_OPT, key="event_experience")
            ege  = st.selectbox("Required Gender", GENDER_OPT, key="event_gender")
            eedu = st.selectbox("Required Education", EDU_OPT, key="event_education")
        with fc2:
            eci  = st.text_input("City *", key="event_city")
            eloc = st.text_input("Detailed Location", placeholder="e.g. Clifton Block 5, Community Hall", key="event_location")
            emo  = st.selectbox("Mode *", MODE_OPT, key="event_mode")
            ecp  = st.number_input("Capacity *", min_value=1, value=10, key="event_capacity")
            emna = st.number_input("Min Age", min_value=0, max_value=100, value=0, key="event_min_age")
            emxa = st.number_input("Max Age", min_value=0, max_value=100, value=100, key="event_max_age")
        r3c1, r3c2, r3c3 = st.columns(3)
        with r3c1:
            edt = st.date_input("Event Date *", value=date.today(), key="event_date")
        with r3c2:
            etm = st.selectbox("Event Time *", TIME_OPTIONS, key="event_time")
        with r3c3:
            edu_h = st.number_input("Duration (hrs)", min_value=0.0, value=2.0, step=0.5, key="event_duration")
        esub = st.form_submit_button("📤 Submit for Approval", use_container_width=True)

    if esub:
        if emna > emxa:
            st.error("❌ Minimum age cannot be greater than maximum age.")
        else:
            event_date_str = edt.strftime("%Y-%m-%d") if hasattr(edt, "strftime") else str(edt)
            ok, m = create_event(
                ngo_pid, et, ed, ", ".join(esk), eci, event_date_str, etm,
                edu_h if edu_h > 0 else None, int(ecp), eca, eex, emo,
                required_gender=ege, minimum_age=int(emna), maximum_age=int(emxa),
                required_education=eedu, detailed_location=eloc,
            )
            if ok:
                st.session_state["event_created_success"] = True
                _reset_event_form_state()
                st.rerun()
            else:
                st.error(f"❌ {m}")

    st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)
    st.markdown("### 📋 My Events")
    events = get_events_by_ngo(ngo_pid)
    if not events:
        st.info("No events posted yet.")
    else:
        _sb = {"pending":"badge-orange","approved":"badge-green","rejected":"badge-red","closed":"badge-grey","completed":"badge-blue"}
        _si = {"pending":"⏳","approved":"✅","rejected":"❌","closed":"🔒","completed":"🎉"}
        for ev in events:
            eid = ev["id"]; es = ev.get("status","pending")
            ev_badge = _sb.get(es, "")
            with st.container(border=True):
                top_left, top_right = st.columns([4, 1])
                with top_left:
                    st.markdown(f"**{ev.get('title','—')}**")
                    st.caption(
                        f"📍 {ev.get('city','—')} · 📅 {ev.get('event_date','—')} "
                        f"{ev.get('event_time','')} · 👥 {ev.get('capacity','—')}"
                    )
                    if ev.get("description"):
                        st.caption(str(ev.get("description", ""))[:180] + ("..." if len(str(ev.get("description", ""))) > 180 else ""))
                    if es == "rejected" and ev.get("rejection_reason"):
                        st.error(f"Rejection reason: {ev.get('rejection_reason')}")
                with top_right:
                    status_badge(es)

            with st.expander(f"🤖 AI Event Description Assistant #{eid}"):
                st.caption(
                    "Optional wording guidance only. AI will not auto-save, approve, reject, "
                    "or change this event. Copy any useful wording manually."
                )
                if "event_ai_improvements" not in st.session_state:
                    st.session_state["event_ai_improvements"] = {}

                event_cache_key = f"event_improvement_{user['id']}_{eid}_{hash(str(ev.get('description','')))}"
                if st.button(
                    "Improve Event Description with AI",
                    key=f"improve_event_ai_{eid}",
                    use_container_width=True,
                ):
                    event_payload = dict(ev) if hasattr(ev, "keys") else ev
                    with st.spinner("Improving event description..."):
                        st.session_state["event_ai_improvements"][event_cache_key] = improve_event_description(event_payload)

                cached_event_ai = st.session_state["event_ai_improvements"].get(event_cache_key)
                if cached_event_ai:
                    if cached_event_ai.get("success"):
                        original_col, improved_col = st.columns(2)
                        with original_col:
                            st.markdown("**Original Description**")
                            st.text_area(
                                "Original",
                                value=ev.get("description", ""),
                                height=180,
                                key=f"original_desc_{eid}",
                                disabled=True,
                                label_visibility="collapsed",
                            )
                        with improved_col:
                            st.markdown("**AI Improved Description**")
                            st.text_area(
                                "AI Improved",
                                value=cached_event_ai.get("response", ""),
                                height=180,
                                key=f"improved_desc_{eid}",
                                disabled=True,
                                label_visibility="collapsed",
                            )
                        st.info("No changes were saved automatically. Copy the improved text manually if you want to use it.")
                    else:
                        st.warning("AI event improvement temporarily unavailable.")

            if es in ("pending","rejected"):
                with st.expander(f"✏️ Edit Event #{eid}"):
                    def _parse(v, opts): return [x.strip() for x in (v or "").split(",") if x.strip() in opts]
                    with st.form(f"edit_{eid}"):
                        ut  = st.text_input("Title *",  value=ev.get("title",""), key=f"ut_{eid}")
                        ud  = st.text_area("Desc *",    value=ev.get("description",""), key=f"ud_{eid}", height=60)
                        uc1, uc2 = st.columns(2)
                        with uc1:
                            us   = st.multiselect("Skills *", SKILLS_OPT, default=_parse(ev.get("required_skills"), SKILLS_OPT), key=f"us_{eid}")
                            uca  = st.selectbox("Cause *", CAUSE_OPT, index=CAUSE_OPT.index(ev["cause_area"]) if ev.get("cause_area") in CAUSE_OPT else 0, key=f"uca_{eid}")
                            uex  = st.selectbox("Exp *",   EXP_OPT,   index=EXP_OPT.index(ev["experience_level"]) if ev.get("experience_level") in EXP_OPT else 0, key=f"uex_{eid}")
                            uge  = st.selectbox("Gender",  GENDER_OPT, index=GENDER_OPT.index(ev.get("required_gender","Anyone")) if ev.get("required_gender") in GENDER_OPT else 0, key=f"uge_{eid}")
                        with uc2:
                            uci  = st.text_input("City *", value=ev.get("city",""), key=f"uci_{eid}")
                            uloc = st.text_input("Location", value=ev.get("detailed_location",""), key=f"uloc_{eid}")
                            umo  = st.selectbox("Mode *",  MODE_OPT, index=MODE_OPT.index(ev["mode"]) if ev.get("mode") in MODE_OPT else 0, key=f"umo_{eid}")
                            ucp  = st.number_input("Cap *", min_value=1, value=int(ev.get("capacity",1)), key=f"ucp_{eid}")
                        uc3, uc4, uc5 = st.columns(3)
                        with uc3: udt = st.date_input("Date *", value=_date_from_string(ev.get("event_date","")), key=f"udt_{eid}")
                        with uc4: utm = st.selectbox("Time *", TIME_OPTIONS, index=_time_index(ev.get("event_time","")), key=f"utm_{eid}")
                        with uc5: udu = st.number_input("Dur", min_value=0.0, value=float(ev.get("duration_hours") or 0), step=0.5, key=f"udu_{eid}")
                        usb = st.form_submit_button("🔄 Update & Resubmit", use_container_width=True)
                    if usb:
                        udt_str = udt.strftime("%Y-%m-%d") if hasattr(udt, "strftime") else str(udt)
                        ok2, m2 = update_event(eid, ngo_pid, ut, ud, ", ".join(us), uci, udt_str, utm, udu if udu>0 else None, int(ucp), uca, uex, umo)
                        (st.success if ok2 else st.error)(f"{'✅' if ok2 else '❌'} {m2}")
                        if ok2: st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — APPLICANT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab_applicants:
    ngo_p2 = get_ngo_profile(user["id"])
    if not ngo_p2 or ngo_p2.get("verification_status") != "approved":
        st.markdown("""<div style='background:#261d0d;border:1px solid #9e6a03;border-radius:10px;
                        padding:1.5rem;text-align:center'>
            <div style='font-size:2rem'>⏳</div>
            <div style='font-family:Syne,sans-serif;font-weight:700;color:#f0883e;margin:0.4rem 0'>
                Applicant management unlocks after NGO approval.</div></div>""", unsafe_allow_html=True)
        st.stop()

    counts = get_application_counts_for_ngo(user["id"])
    mc1,mc2,mc3,mc4,mc5 = st.columns(5)
    with mc1: st.metric("Total",     counts["total"])
    with mc2: st.metric("Pending",   counts["pending"])
    with mc3: st.metric("Accepted",  counts["accepted"])
    with mc4: st.metric("Rejected",  counts["rejected"])
    with mc5: st.metric("Cancelled", counts["cancelled"])
    st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

    all_apps = get_applications_for_ngo(user["id"])
    if not all_apps:
        st.markdown("""<div style='text-align:center;padding:2.5rem;color:#484f58'>
            <div style='font-size:2.5rem'>📭</div><div>No applications received yet.</div></div>""",
            unsafe_allow_html=True); st.stop()

    sel = st.selectbox("Filter by status", ["All","Pending","Accepted","Rejected","Cancelled"], key="app_filter")
    filtered = all_apps if sel=="All" else [a for a in all_apps if a["status"].capitalize()==sel]
    if not filtered: st.info(f"No {sel.lower()} applications.")

    _badge = {"pending":"badge-orange","accepted":"badge-green","rejected":"badge-red","cancelled":"badge-grey"}
    _blbl  = {"pending":"⏳ Pending","accepted":"✅ Accepted","rejected":"❌ Rejected","cancelled":"🚫 Cancelled"}
    _bdr   = {"pending":"#9e6a03","accepted":"#1a7f37","rejected":"#9e1515","cancelled":"#374151"}
    SUIT_OPT = ["Very Suitable","Suitable","Somewhat Suitable","Not Suitable"]

    for app in filtered:
        aid = app["id"]; astatus = app["status"]
        score_s = f"{app['match_score']:.1f}%" if app.get("match_score") is not None else "—"
        with st.container(border=True):
            row_info, row_status = st.columns([4, 1])
            with row_info:
                st.markdown(f"**{app.get('volunteer_name','—')}**")
                if app.get("volunteer_email"):
                    st.caption(f"📧 {app.get('volunteer_email')}")
                st.caption(
                    f"📋 {app.get('event_title','—')} · "
                    f"📍 {app.get('volunteer_city','—')} · "
                    f"🤖 Match: {score_s}"
                )
                st.caption(
                    f"🛠️ {app.get('volunteer_skills','—')} · "
                    f"🎓 {app.get('experience_level','—')}"
                )
                if app.get("volunteer_note"):
                    st.info(f"📝 Volunteer note: {app.get('volunteer_note')}")
            with row_status:
                status_badge(astatus)

        if astatus == "pending":
            col_acc, col_rej = st.columns(2)
            with col_acc:
                if st.button("✅ Accept", key=f"acc_{aid}", use_container_width=True):
                    ok, m = update_application_status(aid, user["id"], "accepted", "")
                    (st.success if ok else st.error)(f"{'✅' if ok else '❌'} {m}")
                    if ok: st.rerun()
            with col_rej:
                with st.expander("❌ Reject with reason"):
                    rr = st.text_area("Rejection reason *", key=f"rr_{aid}", placeholder="Explain why…", height=65)
                    if st.button("Confirm Rejection", key=f"rej_{aid}", use_container_width=True):
                        if not rr.strip(): st.warning("Enter a reason.")
                        else:
                            ok, m = update_application_status(aid, user["id"], "rejected", rr.strip())
                            (st.success if ok else st.error)(f"{'✅' if ok else '❌'} {m}")
                            if ok: st.rerun()

        elif astatus == "accepted":
            already_ngo = has_feedback(aid, "ngo")
            if already_ngo:
                fb_list = get_feedback_for_application(aid)
                ngo_fb  = next((f for f in fb_list if f["feedback_from"]=="ngo"), None)
                if ngo_fb:
                    stars = "⭐" * ngo_fb["rating"]
                    st.markdown(f"""<div class='fb-card'>
                        <div style='font-size:0.75rem;color:#58a6ff;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.3rem'>✅ NGO Feedback Submitted</div>
                        <div style='font-size:0.85rem;color:#c9d1d9'>{stars} Perf: {ngo_fb["rating"]}/5 · Skills: {ngo_fb.get("secondary_rating","—")}/5 · Attended: {"Yes" if ngo_fb.get("attended") else "No"}</div>
                        <div style='font-size:0.8rem;color:#8b949e'>Suitability: {ngo_fb.get("match_relevance","—")}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                with st.expander(f"⭐ Give Feedback for {app.get('volunteer_name','this volunteer')}"):
                    with st.form(f"ngo_fb_{aid}"):
                        nc1, nc2 = st.columns(2)
                        with nc1: perf_r  = st.selectbox("Performance *", [1,2,3,4,5], index=4, format_func=lambda x:f"{'⭐'*x} ({x}/5)", key=f"pfr_{aid}")
                        with nc2: skill_r = st.selectbox("Skills *",      [1,2,3,4,5], index=4, format_func=lambda x:f"{'⭐'*x} ({x}/5)", key=f"skr_{aid}")
                        att  = st.checkbox("Volunteer attended", value=True, key=f"att_{aid}")
                        suit = st.selectbox("Match suitability", SUIT_OPT, key=f"suit_{aid}")
                        ngo_cmt = st.text_area("Comments", placeholder="Describe volunteer's contribution…", key=f"ncmt_{aid}", height=65)
                        nfb_sub = st.form_submit_button("📤 Submit Feedback", use_container_width=True)
                    if nfb_sub:
                        ok, m = submit_feedback(aid, user["id"], "ngo", perf_r, skill_r, att, suit, ngo_cmt)
                        (st.success if ok else st.error)(f"{'✅' if ok else '❌'} {m}")
                        if ok: st.rerun()

        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
