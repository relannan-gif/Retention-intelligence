# utils/helpers.py
# Shared helper functions used across multiple pages.

import streamlit as st
import pandas as pd
from data.sample_data import generate_clients
from utils.scoring import score_dataframe


# --- Default scoring weights ---
DEFAULT_RISK_WEIGHTS = {
    "w_withdrawal":     8,
    "w_volume_drop":    7,
    "w_login":          6,
    "w_deposit_stale":  5,
    "w_complaints":     9,
    "w_equity_erosion": 5,
}

DEFAULT_VALUE_WEIGHTS = {
    "v_lifetime_dep":  8,
    "v_net_dep":       7,
    "v_volume":        6,
    "v_redeposits":    5,
    "v_pnl":           9,
    "v_spread_rev":    5,
}

DEFAULT_THRESHOLDS = {
    "high_risk":            60,   # top ~25% of risk scores
    "high_value":           20,   # value scores are right-skewed; 20 catches top tier
    "critical_priority":    50,   # top ~10% of priority scores
    "login_inactivity_days": 30,
    "large_withdrawal_pct": 0.30,
}


def load_data() -> pd.DataFrame:
    """
    Load and score the dataset. Uses Streamlit session state so we don't
    regenerate data on every page interaction.
    """
    if "scored_df" not in st.session_state:
        refresh_data()
    return st.session_state["scored_df"]


def refresh_data():
    """Regenerate the fake data and recompute all scores."""
    raw_df = generate_clients(300)
    risk_weights  = st.session_state.get("risk_weights", DEFAULT_RISK_WEIGHTS)
    value_weights = st.session_state.get("value_weights", DEFAULT_VALUE_WEIGHTS)
    thresholds    = st.session_state.get("thresholds", DEFAULT_THRESHOLDS)
    risk_blend    = st.session_state.get("risk_blend", 0.6)

    st.session_state["raw_df"]    = raw_df
    st.session_state["scored_df"] = score_dataframe(
        raw_df, risk_weights, value_weights, thresholds, risk_blend
    )


def rescore():
    """Recompute scores using current session state weights/thresholds."""
    raw_df        = st.session_state.get("raw_df")
    risk_weights  = st.session_state.get("risk_weights", DEFAULT_RISK_WEIGHTS)
    value_weights = st.session_state.get("value_weights", DEFAULT_VALUE_WEIGHTS)
    thresholds    = st.session_state.get("thresholds", DEFAULT_THRESHOLDS)
    risk_blend    = st.session_state.get("risk_blend", 0.6)

    if raw_df is None:
        refresh_data()
        return

    st.session_state["scored_df"] = score_dataframe(
        raw_df, risk_weights, value_weights, thresholds, risk_blend
    )


def fmt_currency(val: float) -> str:
    """Format a number as USD currency string."""
    if val >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val/1_000:.1f}K"
    return f"${val:.0f}"


def risk_color(score: float) -> str:
    """Return a hex colour for a risk/priority score."""
    if score >= 65:
        return "#E74C3C"   # red
    if score >= 35:
        return "#F39C12"   # amber
    return "#27AE60"       # green


def page_header(title: str, subtitle: str = ""):
    """Render a consistent page header."""
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<p style='color:#888;margin-top:-10px'>{subtitle}</p>",
                    unsafe_allow_html=True)
    st.divider()
