# utils/auth.py
# Authentication: session management, login form, forced password change.
# Every page must call require_login() before rendering any content.

import streamlit as st
from typing import Any, Dict, Optional

from utils.user_db import (
    get_user_by_email, verify_password,
    update_last_login, log_audit, reset_password, init_db,
)
from utils.permissions import get_user_level
from config.theme import GOLD


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------

def get_current_user() -> Optional[Dict[str, Any]]:
    """Return the authenticated user dict from session state, or None."""
    return st.session_state.get("user")


def logout() -> None:
    """Clear the session and log the logout event."""
    user = get_current_user()
    if user:
        try:
            log_audit(user["email"], "logout", user["email"], "User logged out")
        except Exception:
            pass
    for key in ("user",):
        st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# Credential check
# ---------------------------------------------------------------------------

def _attempt_login(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Validate credentials against the DB.
    Returns a sanitised user dict (no password_hash) on success, None on failure.
    Logs both outcomes to the audit log.
    """
    db_user = get_user_by_email(email)
    if not db_user:
        log_audit("unknown", "login_failed", email, "Email not found")
        return None
    if db_user["status"] != "active":
        log_audit(email, "login_failed", email, "Account inactive")
        return None
    if not verify_password(password, db_user["password_hash"]):
        log_audit(email, "login_failed", email, "Incorrect password")
        return None

    update_last_login(db_user["id"])
    log_audit(email, "login_success", email, f"Signed in as {db_user['role']}")

    # Build session user: omit password_hash, add computed level
    user = {k: v for k, v in db_user.items() if k != "password_hash"}
    user["level"] = get_user_level(db_user["role"])
    return user


# ---------------------------------------------------------------------------
# UI — login form
# ---------------------------------------------------------------------------

def _render_login_form() -> None:
    """Render the centred sign-in form. Sets session_state.user + reruns on success."""
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] .main > div { padding-top: 4rem; }
    </style>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown(
            f"<h1 style='color:{GOLD};text-align:center;letter-spacing:2px'>"
            f"OneRoyal</h1>"
            "<p style='color:#94A3B8;text-align:center;margin-top:-8px;margin-bottom:28px'>"
            "Client Intelligence Platform</p>",
            unsafe_allow_html=True,
        )

        with st.form("login_form", clear_on_submit=False):
            email    = st.text_input("Email address", placeholder="you@oneroyal.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button(
                "Sign In", use_container_width=True, type="primary"
            )

        if submitted:
            if not email.strip() or not password:
                st.error("Please enter your email and password.")
            else:
                user = _attempt_login(email.strip().lower(), password)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Invalid email or password, or account is inactive.")

        st.markdown(
            "<p style='color:#475569;text-align:center;font-size:12px;margin-top:20px'>"
            "Contact your administrator if you cannot log in.</p>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# UI — forced password change
# ---------------------------------------------------------------------------

def _render_change_password_form(user: Dict[str, Any]) -> None:
    """Block all access until the user sets a new password."""
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown(
            f"<h2 style='color:{GOLD};text-align:center'>Set Your Password</h2>",
            unsafe_allow_html=True,
        )
        st.info(
            "Your account requires a password change before you can continue. "
            "Please choose a strong password of at least 8 characters."
        )

        with st.form("change_pwd_form"):
            new_pwd = st.text_input("New password", type="password")
            confirm = st.text_input("Confirm new password", type="password")
            submitted = st.form_submit_button(
                "Set Password", type="primary", use_container_width=True
            )

        if submitted:
            err = _validate_new_password(new_pwd, confirm)
            if err:
                st.error(err)
            else:
                reset_password(user["id"], new_pwd, modified_by=user["email"])
                log_audit(
                    user["email"], "password_changed", user["email"],
                    "Mandatory password change on first login"
                )
                user["force_password_change"] = False
                st.session_state["user"] = user
                st.success("Password updated. Loading platform…")
                st.rerun()

        st.divider()
        if st.button("Log out instead", key="_logout_after_force",
                     use_container_width=True):
            logout()
            st.rerun()


def _validate_new_password(pwd: str, confirm: str) -> Optional[str]:
    if len(pwd) < 8:
        return "Password must be at least 8 characters."
    if pwd != confirm:
        return "Passwords do not match."
    return None


# ---------------------------------------------------------------------------
# UI — sidebar user info
# ---------------------------------------------------------------------------

def _render_user_sidebar(user: Dict[str, Any]) -> None:
    """Add user info and logout button to the top of the sidebar."""
    with st.sidebar:
        st.markdown(
            f"<div style='padding:6px 0 10px 0'>"
            f"<p style='color:#64748B;font-size:10px;margin:0;letter-spacing:1px'>"
            f"SIGNED IN AS</p>"
            f"<p style='color:#F8FAFC;font-weight:700;font-size:14px;margin:3px 0 1px 0'>"
            f"{user['full_name']}</p>"
            f"<p style='color:{GOLD};font-size:12px;margin:0'>{user['role']}</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("🚪 Logout", key="_global_logout_btn", use_container_width=True):
            logout()
            st.rerun()
        st.divider()


# ---------------------------------------------------------------------------
# Public gate — call at top of every page
# ---------------------------------------------------------------------------

def require_login() -> Dict[str, Any]:
    """
    Must be called at the top of every page (after st.set_page_config).

    Flow:
      1. Ensure DB is initialised (idempotent).
      2. If no user in session → show login form → st.stop().
      3. If force_password_change → show change-password form → st.stop().
      4. Add user info + logout button to sidebar.
      5. Return the user dict.
    """
    if not st.session_state.get("_db_initialized"):
        init_db()
        st.session_state["_db_initialized"] = True

    user = get_current_user()
    if not user:
        _render_login_form()
        st.stop()

    if user.get("force_password_change"):
        _render_user_sidebar(user)
        _render_change_password_form(user)
        st.stop()

    _render_user_sidebar(user)
    return user
