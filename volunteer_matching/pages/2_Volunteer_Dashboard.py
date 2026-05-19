"""
pages/2_Volunteer_Dashboard.py — Bugfix
Fix: experience_level options for volunteer profile = Beginner/Intermediate/Experienced only.
"""

import streamlit as st
from ui.styles import apply_global_styles
from utils.session import init_session, current_user, logout_user, require_auth
from volunteer.volunteer_service import (
    get_volunteer_profile, upsert_volunteer_profile, calculate_profile_completeness,
)
from volunteer.document_service import (
    upload_volunteer_document, get_documents_for_volunteer,
)
from matching.matching_engine import get_recommendations_for_volunteer
from ai.ai_service import generate_profile_suggestions
from notifications.notification_service import get_notifications_for_user, mark_notification_read
from notifications.notification_utils import format_notification_time, get_notification_icon, truncate_notification

st.set_page_config(
    page_title="Volunteer Dashboard · VolunteerAI",
    page_icon="🙋",
    layout="wide",
)
apply_global_styles()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');
    html,body,[class*="css"] { font-family:'DM Sans',sans-serif; }
    #MainMenu,footer,header   { visibility:hidden; }
    .stApp { background:#0d1117; color:#e6edf3; }
    [data-testid="stSidebar"] { background:#161b22!important; border-right:1px solid #30363d; }
    [data-testid="stSidebar"] * { color:#e6edf3!important; }
    h1,h2,h3 { font-family:'Syne',sans-serif!important; font-weight:800!important; color:#e6edf3!important; }
    .main .block-container { padding:2rem 3rem; max-width:1100px; }
    .vm-card { background:#161b22; border:1px solid #30363d; border-radius:12px;
               padding:1.5rem 2rem; margin-bottom:1rem; }
    .dash-card { background:#161b22; border:1px solid #30363d; border-radius:12px;
                 padding:1.4rem 1.6rem; margin-bottom:0.8rem; }
    .vm-divider { border:none; border-top:1px solid #30363d; margin:1.5rem 0; }
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
    .stProgress > div > div { background:#238636!important; border-radius:999px; }
    label { color:#c9d1d9!important; font-size:0.85rem!important; }
    div[data-testid="stCheckbox"] label { color:#c9d1d9!important; }
</style>
""", unsafe_allow_html=True)

init_session()
require_auth(allowed_roles=["volunteer"])
user    = current_user()
profile = get_volunteer_profile(user["id"])
score   = profile["profile_completeness"] if profile else 0
vstatus = profile.get("verification_status", "unverified") if profile else "unverified"

# ── Sidebar ───────────────────────────────────────────────────────────────────
_vbadge = {"unverified":"🔘","pending":"⏳","verified":"✅","rejected":"❌"}
with st.sidebar:
    st.markdown(f"""
        <div style='padding:1rem 0'>
            <div style='font-family:Syne,sans-serif;font-size:1.1rem;font-weight:800;color:#58a6ff'>🤝 VolunteerAI</div>
        </div>
        <hr style='border-color:#30363d;margin:0 0 0.75rem'>
    """, unsafe_allow_html=True)
    st.markdown(f"**{user['email']}**")
    st.caption(f"Role: Volunteer | Verification: {_vbadge.get(vstatus,'')} {vstatus.capitalize()}")
    st.progress(score / 100, text=f"Profile: {score}%")
    st.markdown("")
    if st.button("🚪 Logout", key="vol_logout"):
        logout_user(); st.rerun()
    st.page_link("app.py",                        label="🏠 Home")
    st.page_link("pages/5_Recommendations.py",     label="🎯 Recommendations")
    st.page_link("pages/6_My_Applications.py",     label="📋 My Applications")

st.markdown(
    f"<h1 style='font-size:2.2rem;margin-bottom:0.1rem'>🙋 Volunteer Dashboard</h1>"
    f"<p style='color:#8b949e;margin-top:0'>Welcome, "
    f"<strong style='color:#58a6ff'>{user['email']}</strong></p>",
    unsafe_allow_html=True,
)
st.progress(score / 100)
st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

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
            if st.button("Mark read", key=f"vol_note_read_{note['id']}"):
                mark_notification_read(note["id"], user["id"])
                st.rerun()

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)


tab_overview, tab_profile, tab_docs, tab_recs = st.tabs([
    "🏠 Overview", "✏️ My Profile", "📄 Documents", "🎯 Recommendations"
])


# ═══ TAB 1 — OVERVIEW ════════════════════════════════════════════════════════
with tab_overview:
    if not profile:
        st.info("👋 Welcome! Complete your profile to get started.")

    docs = get_documents_for_volunteer(user["id"])
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Profile", f"{score}%")
    with m2: st.metric("Documents", len(docs))
    with m3: st.metric("Verification", vstatus.capitalize())
    with m4:
        try:
            from events.event_service import get_approved_events
            ev_count = len(get_approved_events())
        except Exception:
            ev_count = 0
        st.metric("Available Events", ev_count)

    st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)
    st.markdown("### 🚀 Quick Actions")

    # Use Streamlit columns + containers — no raw HTML in card content
    dc1, dc2, dc3 = st.columns(3)
    with dc1:
        with st.container(border=True):
            st.markdown("✏️ **Update Profile**")
            st.caption("Fill your skills, availability, and preferences.")
            score_color = "green" if score == 100 else "orange"
            st.caption(f"Completeness: {score}%")
    with dc2:
        with st.container(border=True):
            st.markdown("🛡️ **Verification Status**")
            st.caption("Get verified by admin to boost credibility.")
            st.caption(f"Status: {_vbadge.get(vstatus,'')} {vstatus.capitalize()}")
    with dc3:
        with st.container(border=True):
            st.markdown("📄 **Documents**")
            st.caption("Upload CNIC, Resume, or Certificates.")
            st.caption(f"{len(docs)} document(s) uploaded")

    dc4, dc5, dc6 = st.columns(3)
    with dc4:
        with st.container(border=True):
            st.markdown("🎯 **Recommendations**")
            st.caption("AI-matched events based on your profile.")
        st.page_link("pages/5_Recommendations.py", label="View Events →")
    with dc5:
        with st.container(border=True):
            st.markdown("📋 **My Applications**")
            st.caption("Track your event applications.")
        st.page_link("pages/6_My_Applications.py", label="View Applications →")
    with dc6:
        with st.container(border=True):
            st.markdown("⭐ **Feedback History**")
            st.caption("View feedback for completed events.")
        st.page_link("pages/6_My_Applications.py", label="View Feedback →")

    # Profile summary
    if profile:
        st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)
        st.markdown("### 👤 Profile Summary")
        ps1, ps2 = st.columns([1, 2])
        with ps1:
            with st.container(border=True):
                st.markdown(f"**{profile.get('full_name','—')}**")
                st.caption(
                    f"{profile.get('gender','') or '—'}  ·  "
                    f"Age {profile.get('age') or '—'}  ·  "
                    f"📍 {profile.get('city','—')}"
                )
                st.caption(
                    f"Experience: {profile.get('experience_level','—')}  ·  "
                    f"Mode: {profile.get('preferred_mode','—')}"
                )
        with ps2:
            with st.container(border=True):
                st.markdown("**Skills**")
                skills_list = [s.strip() for s in (profile.get("skills","") or "").split(",") if s.strip()]
                if skills_list:
                    st.write("  ".join(f"`{s}`" for s in skills_list))
                else:
                    st.caption("None added yet")

                st.markdown("**Interests**")
                int_list = [i.strip() for i in (profile.get("interests","") or "").split(",") if i.strip()]
                if int_list:
                    st.write("  ".join(f"`{i}`" for i in int_list))
                else:
                    st.caption("None added yet")

                st.markdown("**Availability**")
                av_list = [a.strip() for a in (profile.get("availability","") or "").split(",") if a.strip()]
                st.write("  ".join(f"`{a}`" for a in av_list) if av_list else "Not set")

                st.caption(f"Last updated: {str(profile.get('updated_at',''))[:16]}")


    if profile:
        st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)
        st.markdown("### 🤖 AI Profile Assistant")
        with st.container(border=True):
            st.caption(
                "Optional guidance only. AI suggestions never edit your profile, "
                "guarantee acceptance, or change recommendation scores."
            )

            profile_cache_key = f"profile_suggestions_{user['id']}_{profile.get('updated_at','')}_{profile.get('id','')}"
            if "profile_ai_suggestions" not in st.session_state:
                st.session_state["profile_ai_suggestions"] = {}

            if st.button(
                "Generate Profile Improvement Suggestions",
                key=f"generate_profile_ai_{user['id']}",
                use_container_width=True,
            ):
                with st.spinner("Generating profile suggestions..."):
                    profile_payload = dict(profile) if hasattr(profile, "keys") else profile
                    st.session_state["profile_ai_suggestions"][profile_cache_key] = generate_profile_suggestions(profile_payload)

            cached_profile_ai = st.session_state["profile_ai_suggestions"].get(profile_cache_key)
            if cached_profile_ai:
                if cached_profile_ai.get("success"):
                    with st.expander("View AI profile suggestions", expanded=True):
                        st.write(cached_profile_ai.get("response", ""))
                else:
                    st.warning("AI suggestions temporarily unavailable.")


# ═══ TAB 2 — PROFILE FORM ════════════════════════════════════════════════════
with tab_profile:
    st.markdown("### ✏️ Edit Volunteer Profile")

    SKILLS_OPT   = ["Teaching","Mentoring","Fundraising","Event Management","First Aid",
                    "Graphic Design","Social Media","Content Writing","Data Entry",
                    "Public Speaking","Photography","Community Outreach",
                    "Translation","IT Support","Research"]
    INTEREST_OPT = ["Education","Health","Environment","Poverty Relief","Animal Welfare",
                    "Women Empowerment","Youth Development","Disaster Relief",
                    "Mental Health","Elderly Care"]
    AVAIL_OPT    = ["Weekdays","Weekend","Flexible"]
    # Volunteer experience — NO 'Anyone'
    EXP_OPT      = ["Beginner","Intermediate","Experienced"]
    MODE_OPT     = ["On-site","Online","Hybrid"]
    EDU_OPT      = ["High School","Intermediate","Undergraduate","Graduate","Postgraduate","Other"]
    GENDER_OPT   = ["Male","Female","Prefer Not To Say"]
    LANG_OPT     = ["English","Urdu","Punjabi","Sindhi","Pashto","Balochi","Other"]

    def _pre(k, d=""):
        if profile and profile.get(k) not in (None, ""):
            return profile[k]
        return d

    def _parse(v, opts):
        return [x.strip() for x in (v or "").split(",") if x.strip() in opts]

    with st.form("vol_profile_form", clear_on_submit=False):
        st.markdown("**Personal Information**")
        r1, r2, r3 = st.columns(3)
        with r1:
            full_name = st.text_input("Full Name *", value=_pre("full_name"),
                                      placeholder="Your full name")
        with r2:
            gender_idx = GENDER_OPT.index(_pre("gender")) if _pre("gender") in GENDER_OPT else 0
            gender = st.selectbox("Gender *", GENDER_OPT, index=gender_idx)
        with r3:
            age_val = st.number_input(
                "Age", min_value=0, max_value=120,
                value=int(_pre("age", 0)) if _pre("age") else 0,
                help="Enter 0 to leave blank",
            )

        r4, r5 = st.columns(2)
        with r4:
            address = st.text_input("Address", value=_pre("address"),
                                    placeholder="Street address")
        with r5:
            city = st.text_input("City *", value=_pre("city"), placeholder="Karachi")

        r6, r7, r8 = st.columns(3)
        with r6:
            edu_idx = EDU_OPT.index(_pre("education")) if _pre("education") in EDU_OPT else 0
            education = st.selectbox("Education", EDU_OPT, index=edu_idx)
        with r7:
            occupation = st.text_input("Occupation", value=_pre("occupation"),
                                       placeholder="Student / Engineer etc.")
        with r8:
            langs_sel = st.multiselect("Languages", LANG_OPT,
                                       default=_parse(_pre("languages"), LANG_OPT))

        st.markdown("**Volunteering Preferences**")
        r9, r10 = st.columns(2)
        with r9:
            skills_sel = st.multiselect("Skills *", SKILLS_OPT,
                                        default=_parse(_pre("skills"), SKILLS_OPT))
        with r10:
            interests_sel = st.multiselect("Interests / Cause Areas *", INTEREST_OPT,
                                           default=_parse(_pre("interests"), INTEREST_OPT))

        r11, r12, r13 = st.columns(3)
        with r11:
            avail_sel = st.multiselect("Availability *", AVAIL_OPT,
                                       default=_parse(_pre("availability"), AVAIL_OPT))
        with r12:
            # Volunteer experience — Beginner / Intermediate / Experienced only
            cur_exp = _pre("experience_level")
            # If DB has a legacy 'Anyone' value, default to Beginner
            if cur_exp not in EXP_OPT:
                cur_exp = EXP_OPT[0]
            exp_idx = EXP_OPT.index(cur_exp)
            experience = st.selectbox("Experience Level *", EXP_OPT, index=exp_idx)
        with r13:
            cur_mode = _pre("preferred_mode")
            if cur_mode not in MODE_OPT:
                cur_mode = MODE_OPT[0]
            mode_idx = MODE_OPT.index(cur_mode)
            pref_mode = st.selectbox("Preferred Mode *", MODE_OPT, index=mode_idx)

        bio = st.text_area("Bio / About Me", value=_pre("bio"),
                           placeholder="Tell NGOs about yourself…", height=100)

        submitted = st.form_submit_button(
            "💾 Save Profile" if not profile else "🔄 Update Profile",
            use_container_width=True,
        )

    if submitted:
        age_in = int(age_val) if age_val and age_val > 0 else None
        ok, msg = upsert_volunteer_profile(
            user_id=user["id"],
            full_name=full_name, gender=gender, age=age_in,
            address=address, city=city, education=education,
            languages=", ".join(langs_sel), occupation=occupation,
            skills=", ".join(skills_sel), interests=", ".join(interests_sel),
            availability=", ".join(avail_sel),
            experience_level=experience, preferred_mode=pref_mode, bio=bio,
        )
        if ok:
            st.success(f"✅ {msg}")
            st.rerun()
        else:
            st.error(f"❌ {msg}")


# ═══ TAB 3 — DOCUMENTS ═══════════════════════════════════════════════════════
with tab_docs:
    st.markdown("### 📄 Volunteer Documents")

    if not profile:
        st.warning("⚠️ Complete your profile before uploading documents.")
        st.stop()

    st.info(
        "📌 **Allowed:** PDF, JPG, PNG  ·  **Max size:** 5 MB  \n"
        "🔍 Admins may run OCR after upload. OCR is assistive only and manual verification remains required."
    )

    DOC_TYPES = ["CNIC", "Resume", "Student Card", "Certificate", "Other"]

    with st.form("doc_upload_form", clear_on_submit=True):
        doc_type   = st.selectbox("Document Type", DOC_TYPES, key="doc_type_sel")
        uploaded_f = st.file_uploader(
            "Choose file", type=["pdf","jpg","jpeg","png"], key="doc_file"
        )
        doc_sub = st.form_submit_button("📤 Upload Document", use_container_width=True)

    if doc_sub:
        if not uploaded_f:
            st.warning("Please select a file first.")
        else:
            ok, msg = upload_volunteer_document(
                volunteer_user_id=user["id"],
                document_type=doc_type,
                file_bytes=uploaded_f.read(),
                original_filename=uploaded_f.name,
            )
            if ok:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")

    st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)
    docs = get_documents_for_volunteer(user["id"])

    if not docs:
        st.info("No documents uploaded yet.")
    else:
        _status_colors = {
            "pending":  ("🟡", "Pending Review"),
            "verified": ("✅", "Verified"),
            "rejected": ("❌", "Rejected"),
        }
        for doc in docs:
            ds = doc.get("verification_status", "pending")
            icon, label = _status_colors.get(ds, ("🔘", ds.capitalize()))
            with st.container(border=True):
                col_info, col_status = st.columns([3, 1])
                with col_info:
                    st.markdown(f"**📄 {doc.get('document_type','—')}**  ·  "
                                f"`{doc.get('original_filename','—')}`")
                    st.caption(f"Uploaded: {str(doc.get('uploaded_at',''))[:10]}")
                    ocr_status = doc.get("ocr_status") or "not_processed"
                    ocr_label = {
                        "not_processed": "OCR pending",
                        "processed": "OCR processed",
                        "failed": "OCR failed",
                    }.get(ocr_status, ocr_status)
                    st.caption(f"🔍 {ocr_label}")
                    if doc.get("admin_notes"):
                        st.caption(f"📝 Admin note: {doc['admin_notes']}")
                with col_status:
                    st.markdown(f"**{icon} {label}**")


# ═══ TAB 4 — RECOMMENDATIONS PREVIEW ════════════════════════════════════════
with tab_recs:
    st.markdown("### 🎯 Your Top Matches")
    if not profile:
        st.warning("Complete your profile to see recommendations.")
    else:
        with st.spinner("Calculating matches…"):
            top_recs = get_recommendations_for_volunteer(user["id"])
        if not top_recs:
            st.info("No approved events available yet.")
        else:
            for rec in top_recs[:5]:
                s = rec["final_score"]
                score_color = "green" if s >= 75 else ("orange" if s >= 50 else "red")
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{rec.get('title','—')}**")
                        st.caption(
                            f"🏢 {rec.get('organization_name','—')}  ·  "
                            f"📍 {rec.get('city','—')}  ·  "
                            f"📅 {rec.get('event_date','—')}"
                        )
                    with c2:
                        st.metric("Match", f"{s:.0f}%")
        st.page_link("pages/5_Recommendations.py", label="🎯 View All Recommendations →")
