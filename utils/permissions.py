# utils/permissions.py
# Role hierarchy, page-level access control, and the centralised data filter.

from __future__ import annotations

import streamlit as st
import pandas as pd
from typing import Any, Dict, List, Set

# ---------------------------------------------------------------------------
# Role definitions
# ---------------------------------------------------------------------------

LEVEL_1_ROLES: Set[str] = {
    "Chairman",
    "Chief Commercial Officer",
    "Head of Sales",
    "Head of Retention",
    "Head of Marketing",
    "Admin",
}

LEVEL_2_ROLES: Set[str] = {
    "Sales Director",
    "Regional Manager",
}

LEVEL_3_ROLES: Set[str] = {
    "Business Developer",
    "Account Manager",
    "Sales",
}

ALL_ROLES: List[str] = sorted(LEVEL_1_ROLES | LEVEL_2_ROLES | LEVEL_3_ROLES)


def get_user_level(role: str) -> int:
    """Return 1 (full), 2 (regional/team), or 3 (own clients)."""
    if role in LEVEL_1_ROLES:
        return 1
    if role in LEVEL_2_ROLES:
        return 2
    return 3


# ---------------------------------------------------------------------------
# Page access
# ---------------------------------------------------------------------------

# Minimum level required per page (lower number = more access)
_PAGE_MIN_LEVEL: Dict[str, int] = {
    "home":                1,  # set to 1 = all levels (1, 2, 3) can access
    "Executive Dashboard": 3,
    "Client List":         3,
    "Scoring Engine":      3,
    "Action Center":       3,
    "Settings":            1,
    "Data Management":     1,
    "Model Validation":    1,
    "User Management":     1,
}


def can_access_page(user: Dict[str, Any], page_name: str) -> bool:
    """True if user's level is allowed to view this page."""
    level = user.get("level", 3)
    min_required = _PAGE_MIN_LEVEL.get(page_name, 1)
    # A lower level number means higher privilege.
    # Level 1 can access pages requiring level 1.
    # Level 3 can access pages requiring level 3.
    # So access is granted when user_level <= min_required  ... wait, that's wrong.
    # Pages requiring level 1 = only level 1 can access.
    # Pages requiring level 3 = levels 1, 2, and 3 can access.
    # So: access when user_level <= min_required  --> but "3" means open to all.
    # Correct: access when user_level >= required_level  --> but that's inverted.
    # Let me re-think: min_required is the "most restrictive level that can access".
    # If min_required == 1: only level 1 can access.
    # If min_required == 3: all levels can access.
    # So: access granted when level >= min_required (since higher number = less access... hmm)
    # Actually: level 1 = most privileged. level 3 = least privileged.
    # Page "requires level 1" = only admins. Page "open to level 3" = everyone.
    # Correct logic: access when user_level <= min_required
    #   e.g. Settings requires min_level=1 → only level 1 (user_level <= 1)
    #        Dashboard requires min_level=3 → levels 1, 2, 3 (user_level <= 3) = all
    return level <= min_required


def require_page_access(user: Dict[str, Any], page_name: str) -> None:
    """
    Call near the top of restricted pages (after require_login).
    Shows an access-denied message and stops if the user lacks permission.
    """
    if not can_access_page(user, page_name):
        st.error(
            "🔒 **Access denied.** You do not have permission to view this page. "
            "Contact your administrator if you believe this is incorrect."
        )
        st.stop()


# ---------------------------------------------------------------------------
# Data filter — applied on every page before rendering any client data
# ---------------------------------------------------------------------------

def filter_data_for_user(df: pd.DataFrame, user: Dict[str, Any]) -> pd.DataFrame:
    """
    Return only the rows the logged-in user is permitted to see.

    Level 1 (Full Access):
        All rows returned as-is.

    Level 2 (Regional / Team Access):
        Rows where ANY of the following match:
          - region in assigned_regions
          - country in assigned_countries
          - regional_manager == user.full_name
          - sales_director   == user.full_name
          - account_manager  in assigned_team_members
          - business_developer in assigned_team_members

    Level 3 (Own Client Access):
        Rows where ANY of the following match:
          - account_manager  == user.full_name
          - business_developer == user.full_name
          - sales_owner      == user.full_name

    If a lower-level user has no scope configured, returns an empty DataFrame
    with the same columns (not an error — the caller should show a warning).
    """
    if df is None or df.empty:
        return df

    level = user.get("level", 3)

    if level == 1:
        return df

    name     = user.get("full_name", "").strip()
    regions  = user.get("assigned_regions", []) or []
    countries= user.get("assigned_countries", []) or []
    team     = user.get("assigned_team_members", []) or []

    mask = pd.Series(False, index=df.index)

    if level == 2:
        if regions and "region" in df.columns:
            mask |= df["region"].isin(regions)
        if countries and "country" in df.columns:
            mask |= df["country"].isin(countries)
        if name:
            if "regional_manager" in df.columns:
                mask |= (df["regional_manager"] == name)
            if "sales_director" in df.columns:
                mask |= (df["sales_director"] == name)
        if team:
            if "account_manager" in df.columns:
                mask |= df["account_manager"].isin(team)
            if "business_developer" in df.columns:
                mask |= df["business_developer"].isin(team)
    else:
        # Level 3
        if name:
            if "account_manager" in df.columns:
                mask |= (df["account_manager"] == name)
            if "business_developer" in df.columns:
                mask |= (df["business_developer"] == name)
            if "sales_owner" in df.columns:
                mask |= (df["sales_owner"] == name)

    if not mask.any():
        return df.iloc[0:0].copy()
    return df[mask].copy()


def no_data_warning(user: Dict[str, Any]) -> None:
    """Show a clear warning when filter_data_for_user returns empty."""
    name = user.get("full_name", "your account")
    st.warning(
        f"⚠️ No clients are currently assigned to **{name}**. "
        "Contact your administrator to assign regions, countries, or team members to your account."
    )
