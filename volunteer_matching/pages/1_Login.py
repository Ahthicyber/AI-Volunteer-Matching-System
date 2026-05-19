"""
pages/1_Login.py
Stable login/register page with home-screen preselection support.
"""
from __future__ import annotations

import streamlit as st

from auth.auth_service import authenticate_user, create_user, ensure_demo_accounts
from ui.styles import apply_global_styles
from utils.navigation import redirect_after_login
from utils.session import (
    clear_registration_state,
    current_user,
    init_session,
    restore_session_from_token,
    is_logged_in,
    login_user,
    logout_user,
)

st.set_page_config(page_title="Login · VolunteerAI", page_icon="🔑", layout="centered")
apply_global_styles()
init_session()
restore_session_from_token()
ensure_demo_accounts()

ROLE_OPTIONS = ["volunteer", "ngo"]
ROLE_LABELS = {"volunteer": "🙋 Volunteer", "ngo": "🏢 NGO / Organisation"}

# Defaults used by home-screen CTA buttons.
st.session_state.setdefault("auth_mode", "login")
st.session_state.setdefault("selected_role", None)
st.session_state.setdefault("pending_login_email", "")

selected_role = st.session_state.get("selected_role")
if selected_role in ROLE_OPTIONS:
    st.session_state["reg_role"] = selected_role


if is_logged_in():
    user = current_user() or {}
    dest_page = redirect_after_login(user.get("role", ""))
    st.markdown(
        """
        <div class='vm-hero vm-fade-in' style='text-align:center'>
            <div class='vm-kicker'>Authenticated</div>
            <h1>Already Logged In</h1>
            <p style='margin:auto'>You are already signed in. Open your dashboard or log out to switch accounts.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.subheader(user.get("email", "Signed in user"))
        st.caption(f"Role: {str(user.get('role', '')).capitalize()}")
        st.page_link(dest_page, label="Open My Dashboard", icon="➡️")
        if st.button("🚪 Logout", key="login_page_logout", use_container_width=True):
            logout_user()
    st.stop()

st.markdown(
    """
    <div class='vm-hero vm-fade-in' style='text-align:center'>
        <div class='vm-kicker'>Welcome</div>
        <h1>VolunteerAI</h1>
        <p style='margin:auto'>Sign in or create a volunteer/NGO account. Admin accounts are created only through seeded/admin credentials.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

mode_from_state = st.session_state.get("auth_mode", "login")
default_index = 1 if mode_from_state == "register" else 0
mode_label = st.radio(
    "Choose an option",
    options=["🔑 Sign In", "📝 Create Account"],
    horizontal=True,
    index=default_index,
    key="auth_mode_radio",
    label_visibility="collapsed",
)
st.session_state["auth_mode"] = "register" if "Create" in mode_label else "login"

if st.session_state["auth_mode"] == "login":
    with st.container(border=True):
        st.subheader("🔑 Sign in to your account")
        with st.form("login_form", clear_on_submit=False):
            login_email = st.text_input(
                "Email address",
                value=st.session_state.get("pending_login_email", ""),
                placeholder="you@example.com",
                key="li_email",
            )
            login_password = st.text_input("Password", type="password", placeholder="••••••••", key="li_pw")
            login_submitted = st.form_submit_button("Sign In", use_container_width=True)

        if login_submitted:
            if not login_email or not login_password:
                st.warning("Please enter your email and password.")
            else:
                ok, result = authenticate_user(login_email.strip(), login_password)
                if ok:
                    login_user(result)
                    st.session_state["auth_mode"] = "login"
                    st.session_state["selected_role"] = None
                    st.session_state["pending_login_email"] = ""
                    st.success(f"✅ Welcome back, **{result['email']}**!")
                    try:
                        st.switch_page(redirect_after_login(result["role"]))
                    except Exception:
                        st.rerun()
                else:
                    st.error(f"❌ {result}")

    with st.expander("Demo login credentials", expanded=False):
        st.code(
            "Admin: admin@volmatch.local / Admin@123\n"
            "Volunteer: volunteer@volmatch.local / Volunteer@123\n"
            "NGO: ngo@volmatch.local / Ngo@123",
            language="text",
        )
        st.caption("Admin registration is intentionally disabled from the public UI.")

else:
    # Ensure home-screen selected role is honored before the selectbox is created.
    reg_role_default = st.session_state.get("reg_role")
    if reg_role_default not in ROLE_OPTIONS:
        reg_role_default = selected_role if selected_role in ROLE_OPTIONS else "volunteer"
        st.session_state["reg_role"] = reg_role_default

    with st.container(border=True):
        st.subheader("📝 Create a new account")
        if selected_role == "volunteer":
            st.info("Volunteer registration selected from the home page.")
        elif selected_role == "ngo":
            st.info("NGO registration selected from the home page.")

        with st.form("register_form", clear_on_submit=False):
            reg_role = st.selectbox(
                "I am registering as",
                options=ROLE_OPTIONS,
                format_func=lambda r: ROLE_LABELS[r],
                key="reg_role",
            )
            reg_email = st.text_input("Email address", placeholder="you@example.com", key="reg_email")
            rc1, rc2 = st.columns(2)
            with rc1:
                reg_pw1 = st.text_input("Password", type="password", placeholder="Min. 6 characters", key="reg_pw1")
            with rc2:
                reg_pw2 = st.text_input("Confirm password", type="password", placeholder="Repeat password", key="reg_pw2")
            agree = st.checkbox("I agree to the Terms of Service", key="agree")
            reg_submitted = st.form_submit_button("Create Account", use_container_width=True)

        if reg_submitted:
            if not reg_email or not reg_pw1 or not reg_pw2:
                st.warning("Please fill in all fields.")
            elif reg_pw1 != reg_pw2:
                st.error("❌ Passwords do not match.")
            elif len(reg_pw1) < 6:
                st.error("❌ Password must be at least 6 characters.")
            elif not agree:
                st.warning("You must agree to the Terms of Service.")
            else:
                ok, msg = create_user(reg_email.strip(), reg_pw1, reg_role)
                if ok:
                    clear_registration_state()
                    st.session_state["auth_mode"] = "login"
                    st.session_state["selected_role"] = None
                    st.session_state["pending_login_email"] = reg_email.strip()
                    st.success(f"✅ Account created successfully as **{ROLE_LABELS[reg_role]}**. Please sign in now.")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    st.caption("Admin registration is not available. Admin users must log in with existing admin credentials.")
