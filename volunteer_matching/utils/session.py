"""
utils/session.py
────────────────
Streamlit session helpers with persistent token restore.

Normal Streamlit reruns must never reset authentication state. Browser hard
refreshes can reset st.session_state, so this module restores a valid login
from a random session token stored in the URL query params and validated in
SQLite. Passwords and password hashes are never stored in session/query params.
"""
from __future__ import annotations

from typing import Any
import streamlit as st

_KEY_LOGGED_IN = "logged_in"
_KEY_USER_ID = "user_id"
_KEY_EMAIL = "email"
_KEY_ROLE = "role"
_KEY_SESSION_TOKEN = "session_token"

AUTH_KEYS = (
    _KEY_LOGGED_IN,
    _KEY_USER_ID,
    _KEY_EMAIL,
    _KEY_ROLE,
    _KEY_SESSION_TOKEN,
)


def init_session() -> None:
    """Initialize missing session keys only; never overwrite an active login."""
    defaults: dict[str, Any] = {
        _KEY_LOGGED_IN: False,
        _KEY_USER_ID: None,
        _KEY_EMAIL: None,
        _KEY_ROLE: None,
        _KEY_SESSION_TOKEN: None,
        "current_page": "Home",
        "auth_mode": "login",
        "selected_role": None,
        "pending_login_email": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _get_query_token() -> str | None:
    """Return session_token from query params, compatible with Streamlit APIs."""
    try:
        value = st.query_params.get("session_token")
        if isinstance(value, list):
            value = value[0] if value else None
        token = str(value).strip() if value else ""
        return token or None
    except Exception:
        try:
            params = st.experimental_get_query_params()
            value = params.get("session_token", [None])
            if isinstance(value, list):
                value = value[0] if value else None
            token = str(value).strip() if value else ""
            return token or None
        except Exception:
            return None


def _set_query_token(token: str) -> None:
    """Store token in URL query params without exposing credentials."""
    try:
        st.query_params["session_token"] = token
    except Exception:
        try:
            st.experimental_set_query_params(session_token=token)
        except Exception:
            pass


def _clear_query_params() -> None:
    """Clear query params on logout so refresh cannot restore old sessions."""
    try:
        st.query_params.clear()
        return
    except Exception:
        pass
    try:
        st.experimental_set_query_params()
    except Exception:
        pass


def restore_session_from_token() -> bool:
    """
    Restore login from a valid query-param session token.

    If st.session_state already contains a complete login, nothing is changed.
    This avoids logging users out on normal Streamlit reruns.
    """
    init_session()

    if (
        st.session_state.get(_KEY_LOGGED_IN) is True
        and st.session_state.get(_KEY_USER_ID)
        and st.session_state.get(_KEY_EMAIL)
        and st.session_state.get(_KEY_ROLE)
    ):
        return True

    token = st.session_state.get(_KEY_SESSION_TOKEN) or _get_query_token()
    if not token:
        return False

    try:
        from auth.auth_service import validate_login_session
        user = validate_login_session(token)
    except Exception:
        user = None

    if not user:
        # Invalid/expired token should not keep being retried after refresh.
        st.session_state[_KEY_SESSION_TOKEN] = None
        _clear_query_params()
        return False

    st.session_state[_KEY_LOGGED_IN] = True
    st.session_state[_KEY_USER_ID] = user["id"]
    st.session_state[_KEY_EMAIL] = user["email"]
    st.session_state[_KEY_ROLE] = user["role"]
    st.session_state[_KEY_SESSION_TOKEN] = token
    _set_query_token(token)
    return True


def login_user(user: dict) -> None:
    """Persist an authenticated user and create a persistent demo session token."""
    init_session()
    st.session_state[_KEY_LOGGED_IN] = True
    st.session_state[_KEY_USER_ID] = user["id"]
    st.session_state[_KEY_EMAIL] = user["email"]
    st.session_state[_KEY_ROLE] = user["role"]

    try:
        from auth.auth_service import create_login_session
        token = create_login_session(int(user["id"]))
    except Exception:
        token = None

    if token:
        st.session_state[_KEY_SESSION_TOKEN] = token
        _set_query_token(token)


def logout_user() -> None:
    """Log out only when explicitly requested, then invalidate persisted token."""
    token = st.session_state.get(_KEY_SESSION_TOKEN) or _get_query_token()
    try:
        from auth.auth_service import deactivate_login_session
        deactivate_login_session(token)
    except Exception:
        pass

    _clear_query_params()

    # Clear auth/navigation keys. Leave unrelated widgets alone where possible.
    for key in (
        _KEY_LOGGED_IN,
        _KEY_USER_ID,
        _KEY_EMAIL,
        _KEY_ROLE,
        _KEY_SESSION_TOKEN,
        "current_page",
        "auth_mode",
        "selected_role",
        "reg_role",
        "pending_login_email",
    ):
        if key in st.session_state:
            del st.session_state[key]

    init_session()
    st.session_state[_KEY_LOGGED_IN] = False
    st.session_state["current_page"] = "Home"
    st.session_state["auth_mode"] = "login"
    st.session_state["selected_role"] = None

    try:
        st.switch_page("app.py")
    except Exception:
        st.rerun()


def clear_registration_state() -> None:
    """Registration must not log a user in or preserve a previous auth token."""
    st.session_state[_KEY_LOGGED_IN] = False
    st.session_state[_KEY_USER_ID] = None
    st.session_state[_KEY_EMAIL] = None
    st.session_state[_KEY_ROLE] = None
    st.session_state[_KEY_SESSION_TOKEN] = None


def is_logged_in() -> bool:
    """Return True when the session contains a complete authenticated user."""
    restore_session_from_token()
    if not st.session_state.get(_KEY_LOGGED_IN, False):
        return False

    if not (
        st.session_state.get(_KEY_USER_ID)
        and st.session_state.get(_KEY_EMAIL)
        and st.session_state.get(_KEY_ROLE)
    ):
        st.session_state[_KEY_LOGGED_IN] = False
        return False

    return True


def current_user() -> dict | None:
    """Return current safe user data, or None when not authenticated."""
    if not is_logged_in():
        return None
    return {
        "id": st.session_state.get(_KEY_USER_ID),
        "email": st.session_state.get(_KEY_EMAIL),
        "role": st.session_state.get(_KEY_ROLE),
    }


def require_auth(allowed_roles: list[str] | None = None) -> None:
    """Guard a page and attempt token restore before denying access."""
    init_session()
    restore_session_from_token()

    if not is_logged_in():
        st.warning("🔒 Please log in to access this page.")
        st.page_link("pages/1_Login.py", label="Go to Login →")
        st.stop()

    if allowed_roles is not None:
        user = current_user()
        if not user or user["role"] not in allowed_roles:
            st.error(f"⛔ Access denied. This page requires role: {', '.join(allowed_roles)}.")
            if user:
                st.info(f"You are logged in as **{user['email']}** with role **{user['role']}**.")
            st.stop()
