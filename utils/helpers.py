# utils/helpers.py
# Shared utilities, default weights/thresholds, theme CSS, and data loader.

import streamlit as st
import pandas as pd
from data.sample_data import generate_clients
from utils.scoring import score_dataframe

# ── Default weights ───────────────────────────────────────────────────────────

DEFAULT_RISK_WEIGHTS = {
    "w_withdrawal": 8, "w_volume_drop": 7, "w_login": 6,
    "w_deposit_stale": 5, "w_complaints": 9,
    "w_equity_erosion": 5, "w_equity_trend": 6,
}

DEFAULT_VALUE_WEIGHTS = {
    "v_lifetime_dep": 8, "v_net_dep": 7, "v_current_equity": 8,
    "v_volume": 6, "v_redeposits": 5, "v_tenure": 4, "v_vip": 9,
}

DEFAULT_PROF_WEIGHTS = {
    "a_spread": 8, "a_commission": 7, "a_swap": 5,
    "b_captured_losses": 10, "b_spread": 4,
    "m_captured_losses": 7, "m_spread": 5, "m_commission": 5, "m_swap": 4,
}

DEFAULT_REACT_WEIGHTS = {
    "r_login_window": 8, "r_lifetime_dep": 7,
    "r_redeposits": 6, "r_volume_hist": 7, "r_tenure": 5,
}

DEFAULT_VIP_WEIGHTS = {
    "u_equity": 8, "u_net_dep": 6,
    "u_volume_trend": 7, "u_redeposits": 5, "u_not_yet_vip": 9,
}

DEFAULT_THRESHOLDS = {
    "high_risk":             60,
    "high_value":            60,
    "high_profitability":    60,
    "critical_priority":     65,
    "login_inactivity_days": 30,
    "large_withdrawal_pct":  0.30,
    "dormant_days":          30,
}

# ── Theme colors (used in charts and helpers) ─────────────────────────────────

GOLD   = "#F0B429"
RED    = "#EF4444"
GREEN  = "#10B981"
AMBER  = "#F59E0B"
BLUE   = "#3B82F6"
PURPLE = "#8B5CF6"
BG     = "#0A0E1A"
CARD   = "#141B2D"
BORDER = "#1E2D4A"
TEXT   = "#E8E8E8"
MUTED  = "#94A3B8"

PLOTLY_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor="#0F1629",
    font=dict(color=TEXT, family="Inter, sans-serif"),
    margin=dict(l=10, r=10, t=40, b=10),
    coloraxis_colorbar=dict(tickfont=dict(color=TEXT)),
)


def apply_theme():
    """Inject CSS for the dark gold executive theme."""
    st.markdown("""
    <style>
    /* Main background */
    .stApp { background-color: #0A0E1A; color: #E8E8E8; }
    .stApp > header { background-color: #0A0E1A; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0F1629; border-right: 1px solid #1E2D4A; }
    [data-testid="stSidebar"] * { color: #E8E8E8 !important; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #141B2D;
        border: 1px solid #1E2D4A;
        border-radius: 8px;
        padding: 12px 16px;
    }
    [data-testid="stMetricLabel"] { color: #94A3B8 !important; font-size: 12px; }
    [data-testid="stMetricValue"] { color: #F0B429 !important; font-size: 22px; font-weight: 700; }
    [data-testid="stMetricDelta"] { color: #94A3B8 !important; }

    /* Expander */
    [data-testid="stExpander"] {
        background-color: #0F1629;
        border: 1px solid #1E2D4A;
        border-radius: 8px;
    }

    /* Selectbox / inputs */
    [data-testid="stSelectbox"] > div > div { background-color: #141B2D; color: #E8E8E8; }
    .stTextInput input { background-color: #141B2D; color: #E8E8E8; border-color: #1E2D4A; }
    .stMultiSelect > div { background-color: #141B2D; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: #0F1629; border-bottom: 1px solid #1E2D4A; }
    .stTabs [data-baseweb="tab"] { color: #94A3B8; }
    .stTabs [aria-selected="true"] { color: #F0B429 !important; border-bottom: 2px solid #F0B429; }

    /* Buttons */
    .stButton > button {
        background-color: #1E2D4A;
        color: #F0B429;
        border: 1px solid #F0B429;
        border-radius: 6px;
        font-weight: 600;
    }
    .stButton > button:hover { background-color: #F0B429; color: #0A0E1A; }

    /* Primary button */
    .stButton > button[kind="primary"] { background-color: #F0B429; color: #0A0E1A; }

    /* Sliders */
    [data-testid="stSlider"] > div > div > div { background-color: #F0B429 !important; }

    /* Dataframe / tables */
    [data-testid="stDataFrame"] { background-color: #141B2D; }
    iframe { background-color: #141B2D !important; }

    /* Divider */
    hr { border-color: #1E2D4A; }

    /* Info / success boxes */
    [data-testid="stAlert"] { background-color: #141B2D; border-color: #1E2D4A; }

    /* Markdown text */
    .stMarkdown p, .stMarkdown li { color: #E8E8E8; }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: #F0B429; }
    </style>
    """, unsafe_allow_html=True)


# ── Data loader ───────────────────────────────────────────────────────────────

def load_data() -> pd.DataFrame:
    """Return scored DataFrame from session state, generating if first run."""
    if "scored_df" not in st.session_state:
        refresh_data()
    return st.session_state["scored_df"]


def refresh_data():
    """Regenerate fake data and recompute all scores."""
    raw = generate_clients(300)
    st.session_state["raw_df"] = raw
    _rescore_from_raw(raw)


def rescore():
    """Recompute scores using current weights/thresholds without regenerating data."""
    raw = st.session_state.get("raw_df")
    if raw is None:
        refresh_data()
        return
    _rescore_from_raw(raw)


def _rescore_from_raw(raw: pd.DataFrame):
    import time
    t0 = time.time()
    from utils.rules_engine import load_rules
    from utils.snapshot_db import init_db, save_snapshot, log_refresh
    if "scoring_rules" not in st.session_state:
        st.session_state["scoring_rules"] = load_rules()
    scored = score_dataframe(
        raw,
        st.session_state.get("risk_weights",  DEFAULT_RISK_WEIGHTS),
        st.session_state.get("value_weights", DEFAULT_VALUE_WEIGHTS),
        st.session_state.get("prof_weights",  DEFAULT_PROF_WEIGHTS),
        st.session_state.get("react_weights", DEFAULT_REACT_WEIGHTS),
        st.session_state.get("vip_weights",   DEFAULT_VIP_WEIGHTS),
        st.session_state.get("thresholds",    DEFAULT_THRESHOLDS),
        rules=st.session_state["scoring_rules"],
    )
    st.session_state["scored_df"] = scored
    # Persist snapshot + refresh log
    try:
        init_db()
        source = st.session_state.get("data_source", "sample")
        save_snapshot(scored, source=source)
        log_refresh(source, len(scored), "success", round(time.time() - t0, 2))
    except Exception:
        pass  # never let DB errors break the UI


# ── Formatting helpers ────────────────────────────────────────────────────────

def fmt_currency(val: float) -> str:
    if val >= 1_000_000:  return f"${val/1_000_000:.1f}M"
    if val >= 1_000:      return f"${val/1_000:.1f}K"
    return f"${val:.0f}"


def get_health_color(label: str) -> str:
    return {
        "Excellent": GREEN,
        "Healthy":   "#22C55E",
        "Watchlist": AMBER,
        "At Risk":   "#F97316",
        "Critical":  RED,
    }.get(label, MUTED)


def get_risk_color(score: float) -> str:
    if score >= 60:  return RED
    if score >= 30:  return AMBER
    return GREEN


def page_header(title: str, subtitle: str = ""):
    st.markdown(
        f"<h2 style='color:#F0B429;margin-bottom:2px'>{title}</h2>",
        unsafe_allow_html=True
    )
    if subtitle:
        st.markdown(
            f"<p style='color:#94A3B8;margin-top:0;margin-bottom:8px'>{subtitle}</p>",
            unsafe_allow_html=True
        )
    st.divider()
