# pages/8_User_Management.py
# Level-1 only: create, edit, deactivate, reset password, audit log.

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from typing import Optional

st.set_page_config(
    page_title="User Management",
    page_icon="👥",
    layout="wide",
)

from utils.helpers import apply_theme, page_header, GOLD, RED, GREEN, AMBER, MUTED
from utils.session_init import init_session_state
from utils.auth import require_login
from utils.permissions import require_page_access, ALL_ROLES, get_user_level
from utils.user_db import (
    get_all_users, get_user_by_id, create_user, update_user,
    reset_password, log_audit, get_audit_log, verify_password,
)
from data.sample_data import (
    COUNTRIES, ACCOUNT_MANAGERS, BUSINESS_DEVELOPERS, REGIONS,
)

apply_theme()
init_session_state()
user = require_login()
require_page_access(user, "User Management")

page_header("👥 User Management",
            "Create · Edit · Deactivate · Reset Password · Audit Log")

# ---------------------------------------------------------------------------
# Reference data for scope pickers
# ---------------------------------------------------------------------------
ALL_REGIONS = list(REGIONS)
ALL_TEAM_MEMBERS = sorted(set(ACCOUNT_MANAGERS) | set(BUSINESS_DEVELOPERS))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_date(iso: Optional[str]) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%d %b %Y %H:%M")
    except Exception:
        return iso


def _level_badge(role: str) -> str:
    lv = get_user_level(role)
    return {1: "🟡 L1 Full", 2: "🔵 L2 Regional", 3: "🟢 L3 Own"}.get(lv, "—")


def _status_badge(status: str) -> str:
    return "🟢 Active" if status == "active" else "🔴 Inactive"


def _validate_password_strength(pwd: str, confirm: str) -> Optional[str]:
    if len(pwd) < 8:
        return "Password must be at least 8 characters."
    if pwd != confirm:
        return "Passwords do not match."
    return None


# ---------------------------------------------------------------------------
# Scope assignment form widget (reused in create + edit)
# ---------------------------------------------------------------------------

def _scope_widgets(prefix: str, defaults: dict) -> dict:
    """Render scope assignment widgets. Returns dict of values."""
    c1, c2 = st.columns(2)
    with c1:
        regions = st.multiselect(
            "Assigned Regions",
            ALL_REGIONS,
            default=defaults.get("assigned_regions", []),
            key=f"{prefix}_regions",
        )
        countries = st.multiselect(
            "Assigned Countries",
            sorted(COUNTRIES),
            default=defaults.get("assigned_countries", []),
            key=f"{prefix}_countries",
        )
    with c2:
        managers = st.multiselect(
            "Reporting Managers",
            ALL_TEAM_MEMBERS,
            default=defaults.get("assigned_managers", []),
            key=f"{prefix}_managers",
            help="Managers this user reports to.",
        )
        team = st.multiselect(
            "Assigned Team Members",
            ALL_TEAM_MEMBERS,
            default=defaults.get("assigned_team_members", []),
            key=f"{prefix}_team",
            help="AMs / BDs whose clients this user can see.",
        )
    return {
        "assigned_regions": regions,
        "assigned_countries": countries,
        "assigned_managers": managers,
        "assigned_team_members": team,
    }


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_users, tab_create, tab_audit = st.tabs(["👥 Users", "➕ Create User", "📋 Audit Log"])


# ===========================================================================
# Tab 1 — User list
# ===========================================================================
with tab_users:
    all_users = get_all_users()

    # ── Search & filters ──────────────────────────────────────────────────────
    st.markdown(f"<h5 style='color:{GOLD}'>User Directory</h5>", unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns([2, 1, 1, 1])
    with f1:
        search = st.text_input("🔍 Search", placeholder="Name or email…",
                               label_visibility="collapsed", key="um_search")
    with f2:
        role_f = st.selectbox("Role", ["All Roles"] + ALL_ROLES,
                              label_visibility="collapsed", key="um_role_f")
    with f3:
        status_f = st.selectbox("Status", ["All", "active", "inactive"],
                                label_visibility="collapsed", key="um_status_f")
    with f4:
        region_f = st.selectbox("Region", ["All Regions"] + ALL_REGIONS,
                                label_visibility="collapsed", key="um_region_f")

    visible = all_users
    if search:
        s = search.lower()
        visible = [u for u in visible
                   if s in u["full_name"].lower() or s in u["email"].lower()]
    if role_f != "All Roles":
        visible = [u for u in visible if u["role"] == role_f]
    if status_f != "All":
        visible = [u for u in visible if u["status"] == status_f]
    if region_f != "All Regions":
        visible = [u for u in visible
                   if region_f in (u.get("assigned_regions") or [])]

    # ── Directory table ───────────────────────────────────────────────────────
    if not visible:
        st.info("No users match the current filters.")
    else:
        rows = []
        for u in visible:
            rows.append({
                "Name":       u["full_name"],
                "Email":      u["email"],
                "Role":       u["role"],
                "Access":     _level_badge(u["role"]),
                "Status":     _status_badge(u["status"]),
                "Regions":    ", ".join(u.get("assigned_regions") or []) or "—",
                "Last Login": _fmt_date(u.get("last_login")),
            })
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.divider()

    # ── Select user to manage ─────────────────────────────────────────────────
    st.markdown(f"<h5 style='color:{GOLD}'>Manage a User</h5>", unsafe_allow_html=True)

    if not visible:
        st.caption("No users to manage (adjust filters above).")
    else:
        options = {f"{u['full_name']}  ·  {u['email']}": u["id"] for u in visible}
        selected_label = st.selectbox("Select user", list(options.keys()),
                                      label_visibility="collapsed", key="um_select")
        sel_id   = options[selected_label]
        sel_user = next(u for u in visible if u["id"] == sel_id)

        # ── User detail card ──────────────────────────────────────────────────
        with st.expander("📋 User Details", expanded=False):
            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown(f"**Full Name:** {sel_user['full_name']}")
                st.markdown(f"**Email:** {sel_user['email']}")
                st.markdown(f"**Role:** {sel_user['role']}")
                st.markdown(f"**Access Level:** {_level_badge(sel_user['role'])}")
            with d2:
                st.markdown(f"**Status:** {_status_badge(sel_user['status'])}")
                st.markdown(f"**Created:** {_fmt_date(sel_user.get('created_at'))}")
                st.markdown(f"**Last Login:** {_fmt_date(sel_user.get('last_login'))}")
                st.markdown(f"**Last Pwd Reset:** {_fmt_date(sel_user.get('last_password_reset'))}")
            with d3:
                st.markdown(f"**Created By:** {sel_user.get('created_by') or '—'}")
                st.markdown(f"**Last Modified By:** {sel_user.get('last_modified_by') or '—'}")
                st.markdown(f"**Regions:** {', '.join(sel_user.get('assigned_regions') or []) or '—'}")
                st.markdown(f"**Team:** {', '.join(sel_user.get('assigned_team_members') or []) or '—'}")

        # ── Action buttons ────────────────────────────────────────────────────
        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button("✏️ Edit User", key="um_btn_edit", use_container_width=True):
                st.session_state["um_edit_id"]  = sel_id
                st.session_state["um_reset_id"] = None
        with a2:
            deact_label = "✅ Activate" if sel_user["status"] == "inactive" else "🚫 Deactivate"
            if st.button(deact_label, key="um_btn_deact", use_container_width=True):
                if sel_id == user["id"]:
                    st.error("You cannot deactivate your own account.")
                else:
                    new_status   = "active" if sel_user["status"] == "inactive" else "inactive"
                    action_label = "activated" if new_status == "active" else "deactivated"
                    update_user(sel_id, status=new_status, modified_by=user["email"])
                    log_audit(user["email"], f"user_{action_label}",
                              sel_user["email"],
                              f"{sel_user['full_name']} {action_label} by {user['full_name']}")
                    st.success(f"{sel_user['full_name']} has been {action_label}.")
                    st.rerun()
        with a3:
            if st.button("🔑 Reset Password", key="um_btn_reset", use_container_width=True):
                st.session_state["um_reset_id"] = sel_id
                st.session_state["um_edit_id"]  = None

        # ── Edit form ─────────────────────────────────────────────────────────
        if st.session_state.get("um_edit_id") == sel_id:
            st.divider()
            st.markdown(f"<h5 style='color:{GOLD}'>✏️ Edit: {sel_user['full_name']}</h5>",
                        unsafe_allow_html=True)

            with st.form(f"edit_form_{sel_id}"):
                ef1, ef2 = st.columns(2)
                with ef1:
                    new_name = st.text_input("Full Name", value=sel_user["full_name"])
                with ef2:
                    # Prevent self-role-escalation: editing own role is disabled
                    role_disabled = (sel_id == user["id"])
                    role_help = "You cannot change your own role." if role_disabled else None
                    new_role = st.selectbox(
                        "Role", ALL_ROLES,
                        index=ALL_ROLES.index(sel_user["role"]) if sel_user["role"] in ALL_ROLES else 0,
                        disabled=role_disabled, help=role_help,
                    )

                ef3, ef4 = st.columns(2)
                with ef3:
                    new_status = st.selectbox("Status", ["active", "inactive"],
                                              index=0 if sel_user["status"] == "active" else 1)
                with ef4:
                    force_pwd = st.checkbox("Force password change on next login",
                                            value=sel_user.get("force_password_change", False))

                st.caption("Scope Assignment")
                scope = _scope_widgets(f"edit_{sel_id}", sel_user)

                submitted = st.form_submit_button("Save Changes", type="primary")

            if submitted:
                changes = []
                if new_name != sel_user["full_name"]:
                    changes.append(f"name: {sel_user['full_name']} → {new_name}")
                if new_role != sel_user["role"] and not role_disabled:
                    changes.append(f"role: {sel_user['role']} → {new_role}")
                if new_status != sel_user["status"]:
                    changes.append(f"status: {sel_user['status']} → {new_status}")

                update_user(
                    sel_id,
                    full_name=new_name,
                    role=None if role_disabled else new_role,
                    status=new_status,
                    assigned_regions=scope["assigned_regions"],
                    assigned_countries=scope["assigned_countries"],
                    assigned_managers=scope["assigned_managers"],
                    assigned_team_members=scope["assigned_team_members"],
                    force_password_change=force_pwd,
                    modified_by=user["email"],
                )
                log_audit(user["email"], "user_edited", sel_user["email"],
                          "; ".join(changes) if changes else "Scope updated")

                # If editing self, refresh session user
                if sel_id == user["id"]:
                    refreshed = get_user_by_id(sel_id)
                    if refreshed:
                        from utils.permissions import get_user_level
                        refreshed.pop("password_hash", None)
                        refreshed["level"] = get_user_level(refreshed["role"])
                        st.session_state["user"] = refreshed

                st.success(f"User {new_name} updated successfully.")
                st.session_state["um_edit_id"] = None
                st.rerun()

        # ── Password reset form ───────────────────────────────────────────────
        if st.session_state.get("um_reset_id") == sel_id:
            st.divider()
            st.markdown(f"<h5 style='color:{GOLD}'>🔑 Reset Password: {sel_user['full_name']}</h5>",
                        unsafe_allow_html=True)

            with st.form(f"reset_form_{sel_id}"):
                new_pwd  = st.text_input("New password",     type="password")
                confirm  = st.text_input("Confirm password", type="password")
                force    = st.checkbox("Require user to change password on next login",
                                       value=True)
                submitted = st.form_submit_button("Set New Password", type="primary")

            if submitted:
                err = _validate_password_strength(new_pwd, confirm)
                if err:
                    st.error(err)
                else:
                    reset_password(sel_id, new_pwd, modified_by=user["email"])
                    if force:
                        update_user(sel_id, force_password_change=True,
                                    modified_by=user["email"])
                    log_audit(user["email"], "password_reset", sel_user["email"],
                              f"Password reset by {user['full_name']}")
                    st.success(f"Password for {sel_user['full_name']} has been reset.")
                    st.session_state["um_reset_id"] = None
                    st.rerun()


# ===========================================================================
# Tab 2 — Create user
# ===========================================================================
with tab_create:
    st.markdown(f"<h5 style='color:{GOLD}'>Create New User</h5>", unsafe_allow_html=True)
    st.caption("All fields marked ✱ are required. Passwords are hashed before storage.")

    with st.form("create_user_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_full_name = st.text_input("✱ Full Name", placeholder="Jane Smith")
            new_email     = st.text_input("✱ Email / Username",
                                          placeholder="jane.smith@oneroyal.com")
        with c2:
            new_role   = st.selectbox("✱ Role", ALL_ROLES)
            new_status = st.selectbox("Status", ["active", "inactive"])

        p1, p2 = st.columns(2)
        with p1:
            new_pwd = st.text_input("✱ Password", type="password")
        with p2:
            new_pwd_confirm = st.text_input("✱ Confirm Password", type="password")

        new_force_pwd = st.checkbox("Force password change on next login", value=True)

        st.caption("Scope Assignment")
        scope = _scope_widgets("create", {})

        submitted = st.form_submit_button("Create User", type="primary",
                                          use_container_width=True)

    if submitted:
        err = None
        if not new_full_name.strip():
            err = "Full name is required."
        elif not new_email.strip():
            err = "Email is required."
        elif "@" not in new_email:
            err = "Enter a valid email address."
        elif not new_pwd:
            err = "Password is required."
        else:
            err = _validate_password_strength(new_pwd, new_pwd_confirm)

        if err:
            st.error(err)
        else:
            # Check email uniqueness
            existing = [u for u in get_all_users()
                        if u["email"] == new_email.strip().lower()]
            if existing:
                st.error(f"A user with email '{new_email.strip().lower()}' already exists.")
            else:
                new_id = create_user(
                    full_name=new_full_name.strip(),
                    email=new_email.strip().lower(),
                    password=new_pwd,
                    role=new_role,
                    status=new_status,
                    assigned_regions=scope["assigned_regions"],
                    assigned_countries=scope["assigned_countries"],
                    assigned_managers=scope["assigned_managers"],
                    assigned_team_members=scope["assigned_team_members"],
                    force_password_change=new_force_pwd,
                    created_by=user["email"],
                )
                log_audit(
                    user["email"], "user_created",
                    new_email.strip().lower(),
                    f"Created {new_full_name.strip()} as {new_role} by {user['full_name']}",
                )
                st.success(
                    f"✅ User **{new_full_name.strip()}** ({new_email.strip().lower()}) "
                    f"created with role **{new_role}** (ID: {new_id})."
                )


# ===========================================================================
# Tab 3 — Audit Log
# ===========================================================================
with tab_audit:
    st.markdown(f"<h5 style='color:{GOLD}'>Audit Log</h5>", unsafe_allow_html=True)
    st.caption("All user management actions and login events are recorded here.")

    al1, al2 = st.columns(2)
    with al1:
        action_f = st.selectbox("Filter by action", [
            "All",
            "login_success", "login_failed", "logout",
            "user_created", "user_edited", "user_activated", "user_deactivated",
            "password_reset", "password_changed", "role_changed",
        ], key="al_action")
    with al2:
        actor_f = st.text_input("Filter by actor email", placeholder="actor@oneroyal.com",
                                key="al_actor")

    logs = get_audit_log(limit=500)

    if action_f != "All":
        logs = [l for l in logs if l["action"] == action_f]
    if actor_f.strip():
        logs = [l for l in logs if actor_f.strip().lower() in l["actor_email"].lower()]

    if not logs:
        st.info("No audit events match the current filters.")
    else:
        st.caption(f"Showing {len(logs)} event(s) — most recent first.")
        log_rows = []
        for l in logs:
            log_rows.append({
                "Timestamp":    _fmt_date(l["timestamp"]),
                "Actor":        l["actor_email"],
                "Action":       l["action"],
                "Target":       l.get("target_email") or "—",
                "Details":      l.get("details") or "—",
            })
        st.dataframe(pd.DataFrame(log_rows), hide_index=True, use_container_width=True)
