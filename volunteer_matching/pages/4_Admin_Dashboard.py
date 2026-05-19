"""
pages/4_Admin_Dashboard.py — Bugfix
Fixes: Raw HTML/code rendered in Volunteer Profiles and Document Review sections.
All cards now use native Streamlit components (st.container, st.columns, st.caption).
"""

import streamlit as st
from ui.styles import apply_global_styles
from ui.components import status_badge
import pandas as pd
from utils.session import init_session, current_user, logout_user, require_auth
from utils.config import settings
from admin.admin_service import get_ngos_by_status, approve_ngo, reject_ngo
from events.event_service import get_events_by_status, approve_event, reject_event, delete_event
from volunteer.volunteer_service import get_all_volunteers_for_admin, update_verification_status
from volunteer.document_service import get_all_documents_for_admin, verify_document, reject_document
from ngo.document_service import (
    get_all_ngo_documents, verify_ngo_document, reject_ngo_document,
    process_ngo_document_ocr, generate_ngo_document_ai_summary,
)
from documents.document_analysis_service import process_document_ocr, generate_document_ai_summary
from documents.document_utils import safe_text_preview
from db.database import get_connection, get_db_path
from db.schema import get_table_names
from notifications.notification_service import get_system_alerts
from analytics.analytics_service import get_application_conversion_metrics, get_match_quality_metrics, get_system_health_summary
from ai.ai_service import (
    generate_profile_summary,
    generate_document_metadata_summary,
    generate_system_insights,
)

st.set_page_config(page_title="Admin Dashboard · VolunteerAI", page_icon="🔐", layout="wide")
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
    .vm-divider { border:none; border-top:1px solid #30363d; margin:1.5rem 0; }
    .stButton > button { background:#238636!important; color:#fff!important;
        border:1px solid #2ea043!important; border-radius:6px!important; font-weight:500!important; }
    .stButton > button:hover { background:#2ea043!important; }
    .stTextInput > div > input, .stTextArea textarea {
        background:#0d1117!important; border:1px solid #30363d!important;
        color:#e6edf3!important; border-radius:6px!important; }
    .stTextInput > div > input:focus, .stTextArea textarea:focus {
        border-color:#58a6ff!important; box-shadow:none!important; }
    [data-baseweb="select"] > div { background:#0d1117!important; border-color:#30363d!important; color:#e6edf3!important; }
    .stTabs [data-baseweb="tab-list"] { background:transparent; border-bottom:1px solid #30363d; }
    .stTabs [data-baseweb="tab"]      { color:#8b949e!important; }
    .stTabs [aria-selected="true"]    { color:#58a6ff!important; border-bottom:2px solid #58a6ff!important; }
    [data-testid="stMetricValue"] { font-family:'Syne',sans-serif!important; color:#58a6ff!important; font-size:1.6rem!important; }
    [data-testid="stMetricLabel"] { color:#8b949e!important; font-size:0.75rem!important; text-transform:uppercase; }
    label { color:#c9d1d9!important; }
    div[data-testid="stCheckbox"] label { color:#c9d1d9!important; }
</style>
""", unsafe_allow_html=True)

init_session()
require_auth(allowed_roles=["admin"])
user = current_user()

with st.sidebar:
    st.markdown("**🤝 VolunteerAI**")
    st.caption(f"Admin: {user['email']}")
    st.markdown("")
    if st.button("🚪 Logout", key="admin_logout"):
        logout_user(); st.rerun()
    st.page_link("app.py",                   label="🏠 Home")
    st.page_link("pages/7_Evaluation.py",     label="📊 Evaluation")
    st.page_link("pages/8_ML_Evaluation.py",  label="🤖 ML Evaluation")
    st.page_link("pages/9_Advanced_Analytics.py", label="📈 Advanced Analytics")

st.markdown(
    f"<h1 style='font-size:2.2rem;margin-bottom:0.1rem'>🔐 Admin Dashboard</h1>"
    f"<p style='color:#8b949e;margin-top:0'>Welcome, "
    f"<strong style='color:#f85149'>{user['email']}</strong></p>",
    unsafe_allow_html=True,
)
st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
pending_ngos   = get_ngos_by_status("pending")
approved_ngos  = get_ngos_by_status("approved")
rejected_ngos  = get_ngos_by_status("rejected")
pending_evts   = get_events_by_status("pending")
approved_evts  = get_events_by_status("approved")
rejected_evts  = get_events_by_status("rejected")
all_volunteers = get_all_volunteers_for_admin()
all_docs       = get_all_documents_for_admin()
pending_docs   = [d for d in all_docs if d["verification_status"] == "pending"]
all_ngo_docs   = get_all_ngo_documents()
pending_ngo_docs = [d for d in all_ngo_docs if d["verification_status"] == "pending"]


# ── AI summary cache helpers ─────────────────────────────────────────────────
st.session_state.setdefault("admin_ai_summaries", {})
st.session_state.setdefault("admin_ai_insights", {})


def _entity_cache_key(prefix, entity_id):
    """Create a per-session, entity-specific AI cache key."""
    return f"{prefix}_{entity_id or 'unknown'}"


def _show_ai_payload(payload, unavailable_message="AI summary temporarily unavailable."):
    """Render a standardized AI service response safely."""
    if not payload or not payload.get("success"):
        st.warning(unavailable_message)
        return
    st.info(payload.get("response", ""))


def _render_profile_summary_button(profile, profile_type, entity_id, label, cache_prefix):
    """Manual-only AI profile summary button with session cache."""
    cache = st.session_state["admin_ai_summaries"]
    cache_key = _entity_cache_key(cache_prefix, entity_id)

    with st.expander("🤖 AI Summary", expanded=False):
        st.caption("Assistive summary only — it does not approve, reject, or verify this profile.")
        if cache_key in cache:
            _show_ai_payload(cache[cache_key])
        elif st.button(label, key=f"btn_{cache_key}", use_container_width=True):
            with st.spinner("Generating AI summary..."):
                cache[cache_key] = generate_profile_summary(profile, profile_type)
            _show_ai_payload(cache[cache_key])


def _render_document_metadata_summary_button(document, document_id):
    """Manual-only AI document metadata summary button with session cache."""
    cache = st.session_state["admin_ai_summaries"]
    cache_key = _entity_cache_key("document_metadata", document_id)

    with st.expander("🤖 AI Metadata Summary", expanded=False):
        st.caption("OCR-based document content analysis will be implemented in a future phase.")
        st.caption("This summary uses metadata only and does not read or verify document contents.")
        if cache_key in cache:
            _show_ai_payload(cache[cache_key], "AI metadata summary temporarily unavailable.")
        elif st.button("Generate Metadata Summary", key=f"btn_{cache_key}", use_container_width=True):
            with st.spinner("Generating metadata summary..."):
                cache[cache_key] = generate_document_metadata_summary(document)
            _show_ai_payload(cache[cache_key], "AI metadata summary temporarily unavailable.")

conn = get_connection()
try:
    total_users = conn.execute("SELECT COUNT(*) FROM Users").fetchone()[0]
    total_vols  = conn.execute("SELECT COUNT(*) FROM Users WHERE role='volunteer'").fetchone()[0]
    total_ngou  = conn.execute("SELECT COUNT(*) FROM Users WHERE role='ngo'").fetchone()[0]
    tables      = get_table_names(conn)
finally:
    conn.close()

# ── Metrics ───────────────────────────────────────────────────────────────────
m1, m2, m3, m4, m5, m6, m7, m8 = st.columns(8)
with m1: st.metric("Total Users",    total_users)
with m2: st.metric("Volunteers",     total_vols)
with m3: st.metric("NGO Users",      total_ngou)
with m4: st.metric("NGOs Pending",   len(pending_ngos))
with m5: st.metric("Events Pending", len(pending_evts))
with m6: st.metric("Volunteer Docs", len(pending_docs))
with m7: st.metric("NGO Docs",       len(pending_ngo_docs))
with m8: st.metric("Approved NGOs",  len(approved_ngos))

# ── Evaluation / Analytics links ─────────────────────────────────────────────
with st.container(border=True):
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        st.markdown("**📊 Reporting & Analytics**")
        st.caption("Evaluation metrics plus advanced admin intelligence for FYP reporting.")
    with c2:
        st.page_link("pages/7_Evaluation.py", label="Evaluation →")
    with c3:
        st.page_link("pages/9_Advanced_Analytics.py", label="Analytics →")

# ── Compact analytics preview ────────────────────────────────────────────────
try:
    _app_metrics = get_application_conversion_metrics()
    _match_metrics = get_match_quality_metrics()
    _health_metrics = get_system_health_summary()
    with st.container(border=True):
        st.markdown("### 📈 Analytics Preview")
        ap1, ap2, ap3 = st.columns(3)
        with ap1:
            st.metric("Pending Tasks", _health_metrics.get("pending_admin_tasks", 0))
        with ap2:
            st.metric("Acceptance Rate", f"{_app_metrics.get('acceptance_rate', 0)}%")
        with ap3:
            st.metric("Avg Match Score", _match_metrics.get("average_deterministic_score") or "—")
        st.caption("Open Advanced Analytics for full reporting, trends, and rule-based insights.")
except Exception:
    st.info("Analytics preview is temporarily unavailable, but the admin dashboard remains usable.")

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)


# ── System Alerts ─────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("### 🔔 System Alerts")
    alerts = get_system_alerts(limit=10)
    if not alerts:
        st.success("No current system alerts.")
    for alert in alerts:
        st.warning(f"**{alert.get('title')}** — {alert.get('message')}")

st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

# ── Six tabs ──────────────────────────────────────────────────────────────────
t_vol, t_ngo, t_docs, t_ngo_docs, t_events, t_users, t_sys = st.tabs([
    "🙋 Volunteer Verification",
    "🏢 NGO Verification",
    "📄 Volunteer Document Review",
    "🏢 NGO Document Review",
    "📣 Event Management",
    "👥 User Management",
    "🔧 System",
])


# ════════════════════════════════════════════════════════════════════════
# TAB 1 — VOLUNTEER VERIFICATION  (all native Streamlit, no raw HTML)
# ════════════════════════════════════════════════════════════════════════
with t_vol:
    st.markdown("### 🙋 Volunteer Profiles")

    _vstatus_icon = {
        "unverified": "⬜", "pending": "⏳",
        "verified": "✅", "rejected": "❌",
    }

    if not all_volunteers:
        st.info("No volunteer profiles yet.")
    else:
        for vol in all_volunteers:
            vs  = vol.get("verification_status", "unverified")
            vid = vol.get("user_id") or vol.get("id")
            icon = _vstatus_icon.get(vs, "•")

            with st.container(border=True):
                col_info, col_badge = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**{vol.get('full_name','—')}**  ·  `{vol.get('email','')}`")
                    st.caption(
                        f"📍 {vol.get('city','—')}  ·  "
                        f"🎓 {vol.get('experience_level','—')}  ·  "
                        f"✅ {vol.get('profile_completeness', 0)}% complete"
                    )
                    skills_preview = (vol.get("skills","") or "")[:80]
                    if skills_preview:
                        st.caption(f"🛠️ {skills_preview}{'…' if len(vol.get('skills',''))>80 else ''}")
                    if vol.get("verification_notes"):
                        st.caption(f"📝 Notes: {vol['verification_notes']}")
                with col_badge:
                    st.markdown(f"**{icon} {vs.capitalize()}**")

                _render_profile_summary_button(
                    vol,
                    "volunteer",
                    vid,
                    "Generate AI Profile Summary",
                    "volunteer_profile",
                )

                if vs in ("unverified", "pending", "rejected"):
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button("✅ Verify", key=f"vverify_{vid}", use_container_width=True):
                            ok, m = update_verification_status(vid, "verified", "")
                            if ok:
                                st.success(f"✅ {m}")
                                st.rerun()
                            else:
                                st.error(f"❌ {m}")
                    with btn_c2:
                        with st.expander("❌ Reject"):
                            vrej_r = st.text_area(
                                "Rejection reason *",
                                key=f"vrej_{vid}", height=65,
                                placeholder="Reason for rejection…",
                            )
                            if st.button("Confirm", key=f"vrejbtn_{vid}", use_container_width=True):
                                if not vrej_r.strip():
                                    st.warning("Enter a reason.")
                                else:
                                    ok, m = update_verification_status(vid, "rejected", vrej_r.strip())
                                    if ok:
                                        st.success(f"✅ {m}")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {m}")


# ════════════════════════════════════════════════════════════════════════
# TAB 2 — NGO VERIFICATION
# ════════════════════════════════════════════════════════════════════════
with t_ngo:
    ngo_t1, ngo_t2, ngo_t3 = st.tabs([
        f"⏳ Pending ({len(pending_ngos)})",
        f"✅ Approved ({len(approved_ngos)})",
        f"❌ Rejected ({len(rejected_ngos)})",
    ])

    def _render_ngo_card(ngo):
        with st.container(border=True):
            st.markdown(f"**{ngo.get('organization_name','—')}**")
            st.caption(f"📧 {ngo.get('ngo_email','—')}")
            st.caption(
                f"👤 {ngo.get('contact_person','—')}  ·  "
                f"📞 {ngo.get('phone') or '—'}  ·  "
                f"📍 {ngo.get('city','—')}"
            )
            st.caption(f"🎯 {ngo.get('cause_areas','—')}")
            st.caption(f"📅 Submitted: {str(ngo.get('submitted_at',''))[:10]}")
            if ngo.get("description"):
                with st.expander("📄 Description"):
                    st.write(ngo["description"])
            _render_profile_summary_button(
                ngo,
                "ngo",
                ngo.get("id") or ngo.get("user_id"),
                "Generate AI NGO Summary",
                "ngo_profile",
            )

    with ngo_t1:
        if not pending_ngos:
            st.info("No pending NGOs — all caught up!")
        for ngo in pending_ngos:
            pid = ngo["id"]
            ci, ca = st.columns([3, 2])
            with ci:
                _render_ngo_card(ngo)
            with ca:
                st.markdown("")
                if st.button("✅ Approve", key=f"ngo_app_{pid}", use_container_width=True):
                    ok, m = approve_ngo(pid, user["id"])
                    if ok:
                        st.success(m); st.rerun()
                    else:
                        st.error(m)
                reason = st.text_area(
                    "Rejection reason", key=f"ngo_rea_{pid}",
                    height=80, label_visibility="collapsed",
                    placeholder="Enter rejection reason…",
                )
                if st.button("❌ Reject", key=f"ngo_rej_{pid}", use_container_width=True):
                    if not reason.strip():
                        st.warning("Enter a reason first.")
                    else:
                        ok, m = reject_ngo(pid, user["id"], reason.strip())
                        if ok:
                            st.error("NGO rejected."); st.rerun()
                        else:
                            st.error(m)
            st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

    with ngo_t2:
        if not approved_ngos:
            st.info("No approved NGOs yet.")
        for ngo in approved_ngos:
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{ngo.get('organization_name','—')}**")
                    st.caption(f"📧 {ngo.get('ngo_email','—')}  ·  📍 {ngo.get('city','—')}")
                    st.caption(f"🎯 {ngo.get('cause_areas','—')}")
                    rev = ngo.get('reviewer_email','—')
                    rev_at = str(ngo.get('reviewed_at',''))[:10]
                    st.caption(f"Reviewed by: {rev}  ·  {rev_at}")
                with c2:
                    st.markdown("**✅ Approved**")

    with ngo_t3:
        if not rejected_ngos:
            st.info("No rejected NGOs.")
        for ngo in rejected_ngos:
            with st.container(border=True):
                st.markdown(f"**{ngo.get('organization_name','—')}**")
                st.caption(f"📧 {ngo.get('ngo_email','—')}  ·  📍 {ngo.get('city','—')}")
                st.error(f"Rejection reason: {ngo.get('rejection_reason','—')}")


# ════════════════════════════════════════════════════════════════════════
# TAB 3 — DOCUMENT REVIEW + OCR / AI ASSISTANCE
# ════════════════════════════════════════════════════════════════════════
with t_docs:
    st.markdown("### 📄 Volunteer Documents")
    st.warning(
        "OCR and AI summaries are assistive and may contain errors. "
        "Admin verification remains manual."
    )

    doc_filter = st.selectbox(
        "Filter by status", ["All", "Pending", "Verified", "Rejected"],
        key="doc_filter",
    )
    filtered_docs = (
        all_docs if doc_filter == "All"
        else [d for d in all_docs if d["verification_status"].capitalize() == doc_filter]
    )

    _doc_status_icon = {"pending": "⏳", "verified": "✅", "rejected": "❌"}
    _ocr_status_icon = {
        "not_processed": "⬜ OCR pending",
        "processed": "✅ OCR processed",
        "failed": "❌ OCR failed",
    }

    if not filtered_docs:
        st.info(f"No {doc_filter.lower()} documents.")
    else:
        for doc in filtered_docs:
            ds = doc.get("verification_status", "pending")
            icon = _doc_status_icon.get(ds, "•")
            did = doc["id"]
            ocr_status = doc.get("ocr_status") or "not_processed"

            with st.container(border=True):
                col_info, col_status = st.columns([4, 1])
                with col_info:
                    st.markdown(
                        f"**📄 {doc.get('document_type','—')}**  ·  "
                        f"`{doc.get('original_filename','')}`"
                    )
                    st.caption(
                        f"👤 {doc.get('volunteer_name','—')}  ·  "
                        f"📧 {doc.get('volunteer_email','—')}"
                    )
                    st.caption(f"Uploaded: {str(doc.get('uploaded_at',''))[:10]}")
                    st.caption(_ocr_status_icon.get(ocr_status, f"OCR: {ocr_status}"))
                    if doc.get("reviewed_at"):
                        st.caption(f"Reviewed: {str(doc['reviewed_at'])[:10]}")
                    if doc.get("admin_notes"):
                        st.caption(f"📝 Admin notes: {doc['admin_notes']}")
                    if doc.get("ocr_error"):
                        st.error(f"OCR error: {doc['ocr_error']}")
                with col_status:
                    status_badge(ds)

                action_cols = st.columns(2)
                with action_cols[0]:
                    if st.button("🔍 Run OCR", key=f"run_ocr_{did}", use_container_width=True):
                        with st.spinner("Running OCR safely..."):
                            ok, msg = process_document_ocr(did)
                        if ok:
                            st.success(f"✅ {msg}")
                        else:
                            st.warning(f"⚠️ {msg}")
                        st.rerun()
                with action_cols[1]:
                    if st.button("🤖 Generate AI Summary", key=f"doc_ai_summary_{did}", use_container_width=True):
                        with st.spinner("Generating assistive AI summary..."):
                            ok, msg = generate_document_ai_summary(did)
                        if ok:
                            st.success("✅ AI summary generated.")
                        else:
                            st.warning(f"⚠️ {msg}")
                        st.rerun()

                if doc.get("extracted_text"):
                    with st.expander("📖 Extracted OCR Text Preview", expanded=False):
                        st.caption("OCR text may contain errors. Use it only as an admin review aid.")
                        st.text_area(
                            "OCR preview",
                            value=safe_text_preview(doc.get("extracted_text"), 2200),
                            height=220,
                            disabled=True,
                            key=f"ocr_preview_{did}",
                        )

                if doc.get("ai_summary"):
                    with st.expander("🤖 AI Document Summary", expanded=False):
                        st.caption("Assistive only — this does not verify authenticity or approve/reject the document.")
                        st.info(doc.get("ai_summary"))

                _render_document_metadata_summary_button(doc, did)

                if ds == "pending":
                    decision_c1, decision_c2 = st.columns(2)
                    with decision_c1:
                        if st.button("✅ Verify Document", key=f"dverify_{did}", use_container_width=True):
                            ok, m = verify_document(did, "Verified by admin after manual review.")
                            if ok:
                                st.success(f"✅ {m}"); st.rerun()
                            else:
                                st.error(f"❌ {m}")
                    with decision_c2:
                        with st.expander("❌ Reject Document"):
                            drej_r = st.text_area(
                                "Reason *", key=f"drej_{did}",
                                height=60, placeholder="Why is this being rejected?",
                            )
                            if st.button(
                                "Confirm Rejection",
                                key=f"drejbtn_{did}", use_container_width=True,
                            ):
                                if not drej_r.strip():
                                    st.warning("Enter a reason.")
                                else:
                                    ok, m = reject_document(did, drej_r.strip())
                                    if ok:
                                        st.success(f"✅ {m}"); st.rerun()
                                    else:
                                        st.error(f"❌ {m}")
                elif ds == "verified":
                    st.success("✅ This document is already verified. Verification actions are hidden.")
                elif ds == "rejected":
                    st.error("❌ This document has been rejected. Review the admin notes above.")



# ════════════════════════════════════════════════════════════════════════
# TAB 4 — NGO DOCUMENT REVIEW + OCR / AI ASSISTANCE
# ════════════════════════════════════════════════════════════════════════
with t_ngo_docs:
    st.markdown("### 🏢 NGO Documents")
    st.warning("OCR and AI summaries are assistive and may contain errors. Admin verification remains manual.")

    ngo_doc_filter = st.selectbox(
        "Filter NGO documents by status", ["All", "Pending", "Verified", "Rejected"],
        key="ngo_doc_filter",
    )
    filtered_ngo_docs = (
        all_ngo_docs if ngo_doc_filter == "All"
        else [d for d in all_ngo_docs if d["verification_status"].capitalize() == ngo_doc_filter]
    )

    _doc_status_icon = {"pending": "⏳", "verified": "✅", "rejected": "❌"}
    _ocr_status_icon = {
        "not_processed": "⬜ OCR pending",
        "processed": "✅ OCR processed",
        "failed": "❌ OCR failed",
    }

    if not filtered_ngo_docs:
        st.info(f"No {ngo_doc_filter.lower()} NGO documents.")
    else:
        for doc in filtered_ngo_docs:
            ds = doc.get("verification_status", "pending")
            did = doc["id"]
            ocr_status = doc.get("ocr_status") or "not_processed"
            with st.container(border=True):
                col_info, col_status = st.columns([4, 1])
                with col_info:
                    st.markdown(
                        f"**🏢 {doc.get('document_type','—')}** · "
                        f"`{doc.get('original_filename') or doc.get('file_path','').split('/')[-1]}`"
                    )
                    st.caption(f"NGO: {doc.get('organization_name','—')} · {doc.get('ngo_email','—')}")
                    st.caption(f"Uploaded: {str(doc.get('uploaded_at',''))[:10]}")
                    st.caption(_ocr_status_icon.get(ocr_status, f"OCR: {ocr_status}"))
                    if doc.get("admin_notes"):
                        st.caption(f"📝 Admin notes: {doc['admin_notes']}")
                    if doc.get("ocr_error"):
                        st.error(f"OCR error: {doc['ocr_error']}")
                with col_status:
                    status_badge(ds)

                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🔍 Run OCR", key=f"ngo_run_ocr_{did}", use_container_width=True):
                        with st.spinner("Running OCR safely..."):
                            ok, msg = process_ngo_document_ocr(did)
                        (st.success if ok else st.warning)(f"{'✅' if ok else '⚠️'} {msg}")
                        st.rerun()
                with c2:
                    if st.button("🤖 Generate AI Summary", key=f"ngo_doc_ai_{did}", use_container_width=True):
                        with st.spinner("Generating assistive AI summary..."):
                            ok, msg = generate_ngo_document_ai_summary(did)
                        (st.success if ok else st.warning)("✅ AI summary generated." if ok else f"⚠️ {msg}")
                        st.rerun()

                if doc.get("extracted_text"):
                    with st.expander("📖 Extracted OCR Text Preview", expanded=False):
                        st.caption("OCR text may contain errors. Use it only as an admin review aid.")
                        st.text_area(
                            "NGO OCR preview",
                            value=safe_text_preview(doc.get("extracted_text"), 2200),
                            height=220, disabled=True, key=f"ngo_ocr_preview_{did}",
                        )
                if doc.get("ai_summary"):
                    with st.expander("🤖 AI Document Summary", expanded=False):
                        st.caption("Assistive only — this does not verify authenticity or approve/reject the document.")
                        st.info(doc.get("ai_summary"))

                _render_document_metadata_summary_button(doc, f"ngo_{did}")

                if ds == "pending":
                    d1, d2 = st.columns(2)
                    with d1:
                        if st.button("✅ Verify NGO Document", key=f"ngo_doc_verify_{did}", use_container_width=True):
                            ok, m = verify_ngo_document(did, user["id"], "Verified by admin after manual review.")
                            (st.success if ok else st.error)(f"{'✅' if ok else '❌'} {m}")
                            if ok: st.rerun()
                    with d2:
                        with st.expander("❌ Reject NGO Document"):
                            reason = st.text_area("Reason *", key=f"ngo_doc_rej_reason_{did}", height=60)
                            if st.button("Confirm Rejection", key=f"ngo_doc_rej_{did}", use_container_width=True):
                                if not reason.strip():
                                    st.warning("Enter a reason.")
                                else:
                                    ok, m = reject_ngo_document(did, user["id"], reason.strip())
                                    (st.success if ok else st.error)(f"{'✅' if ok else '❌'} {m}")
                                    if ok: st.rerun()
                elif ds == "verified":
                    st.success("✅ This NGO document is already verified. Verification actions are hidden.")
                elif ds == "rejected":
                    st.error("❌ This NGO document has been rejected. Review the admin notes above.")


# ════════════════════════════════════════════════════════════════════════
# TAB 4 — EVENT MANAGEMENT
# ════════════════════════════════════════════════════════════════════════
with t_events:
    ev_t1, ev_t2, ev_t3 = st.tabs([
        f"⏳ Pending ({len(pending_evts)})",
        f"✅ Approved ({len(approved_evts)})",
        f"❌ Rejected ({len(rejected_evts)})",
    ])

    def _render_event_card(ev):
        with st.container(border=True):
            st.markdown(f"**{ev.get('title','—')}**")
            st.caption(f"🏢 {ev.get('organization_name','—')}")
            st.caption(
                f"📍 {ev.get('city','—')}  ·  "
                f"📅 {ev.get('event_date','—')} {ev.get('event_time','')}  ·  "
                f"👥 Cap: {ev.get('capacity','—')}"
            )
            st.caption(
                f"🎯 {ev.get('cause_area','—')}  ·  "
                f"💻 {ev.get('mode','—')}  ·  "
                f"🎓 {ev.get('experience_level','—')}"
            )
            st.caption(
                f"👫 Gender: {ev.get('required_gender','Anyone')}  ·  "
                f"🎂 Age: {ev.get('minimum_age',0)}–{ev.get('maximum_age',100)}"
            )
            if ev.get("description"):
                with st.expander("📄 Description"):
                    st.write(ev["description"])

    with ev_t1:
        if not pending_evts:
            st.info("No pending events — all caught up!")
        for ev in pending_evts:
            eid = ev["id"]
            ec1, ec2 = st.columns([3, 2])
            with ec1:
                _render_event_card(ev)
            with ec2:
                st.markdown("")
                if st.button("✅ Approve", key=f"ev_app_{eid}", use_container_width=True):
                    ok, m = approve_event(eid, user["id"])
                    if ok:
                        st.success(m); st.rerun()
                    else:
                        st.error(m)
                ev_reason = st.text_area(
                    "Rejection reason", key=f"ev_rea_{eid}",
                    height=80, label_visibility="collapsed",
                    placeholder="Enter rejection reason…",
                )
                if st.button("❌ Reject", key=f"ev_rej_{eid}", use_container_width=True):
                    if not ev_reason.strip():
                        st.warning("Enter a reason first.")
                    else:
                        ok, m = reject_event(eid, user["id"], ev_reason.strip())
                        if ok:
                            st.error("Event rejected."); st.rerun()
                        else:
                            st.error(m)
            st.markdown("<div class='vm-divider'></div>", unsafe_allow_html=True)

    with ev_t2:
        if not approved_evts:
            st.info("No approved events yet.")
        for ev in approved_evts:
            eid = ev["id"]
            _render_event_card(ev)
            st.caption("✅ Approved")
            if st.button("🗑️ Delete Event", key=f"del_ev_{eid}"):
                ok, m = delete_event(eid)
                if ok:
                    st.success(f"✅ {m}"); st.rerun()
                else:
                    st.error(f"❌ {m}")

    with ev_t3:
        if not rejected_evts:
            st.info("No rejected events.")
        for ev in rejected_evts:
            _render_event_card(ev)
            st.error(f"Rejection reason: {ev.get('rejection_reason','—')}")


# ════════════════════════════════════════════════════════════════════════
# TAB 5 — USER MANAGEMENT
# ════════════════════════════════════════════════════════════════════════
with t_users:
    st.markdown("### 👥 All Users")
    conn2 = get_connection()
    try:
        rows = conn2.execute(
            "SELECT id, email, role, created_at FROM Users ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn2.close()

    if rows:
        df = pd.DataFrame([dict(r) for r in rows])
        df.columns = ["ID", "Email", "Role", "Registered At"]
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.warning(
        "⚠️ User deletion is irreversible and cascades to all profiles, "
        "applications, and feedback. Use direct DB access for destructive operations."
    )


# ════════════════════════════════════════════════════════════════════════
# TAB 6 — SYSTEM
# ════════════════════════════════════════════════════════════════════════
with t_sys:
    st.markdown("### 🤖 AI System Insights")
    with st.container(border=True):
        st.caption("Assistive aggregate insights only — AI does not approve, reject, verify, or moderate records.")
        insight_key = "system_insights_main"
        metrics_data = {
            "total_users": total_users,
            "total_volunteers": total_vols,
            "total_ngo_users": total_ngou,
            "pending_ngos": len(pending_ngos),
            "approved_ngos": len(approved_ngos),
            "rejected_ngos": len(rejected_ngos),
            "pending_events": len(pending_evts),
            "approved_events": len(approved_evts),
            "rejected_events": len(rejected_evts),
            "pending_documents": len(pending_docs),
            "total_documents": len(all_docs),
            "database_tables": tables,
        }
        if insight_key in st.session_state["admin_ai_insights"]:
            _show_ai_payload(st.session_state["admin_ai_insights"][insight_key], "AI insights temporarily unavailable.")
        elif st.button("Generate AI Insights", key="btn_admin_ai_system_insights", use_container_width=True):
            with st.spinner("Generating AI insights..."):
                st.session_state["admin_ai_insights"][insight_key] = generate_system_insights(metrics_data)
            _show_ai_payload(st.session_state["admin_ai_insights"][insight_key], "AI insights temporarily unavailable.")

    st.markdown("### 🔧 System Information")
    sc1, sc2 = st.columns(2)
    with sc1:
        with st.container(border=True):
            st.markdown("**🗄️ Database**")
            st.caption(f"Status: ✅ Connected")
            st.caption(f"Tables: {', '.join(tables)}")
            st.caption(f"Path: `{get_db_path()}`")
    with sc2:
        with st.container(border=True):
            st.markdown("**⚙️ Config**")
            groq_status = "Configured ✅" if settings["groq_configured"] else "Not configured"
            st.caption(f"Groq API: {groq_status}")
            st.caption("Phase: 8.5 · System Cleanup")
