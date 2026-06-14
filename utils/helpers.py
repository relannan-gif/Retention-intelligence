# utils/helpers.py — v2.0
# Shared utilities, default weights/thresholds, theme CSS, and data loader.
# Changes v2.0: VIP removed from value weights. DEFAULT_VIP_WEIGHTS renamed to
# DEFAULT_UPSIDE_WEIGHTS with updated keys. Risk weights recalibrated per spec.
# B-Book/M-Book profitability formulas corrected (no spread). Priority 35/25/35/5.

import streamlit as st
import pandas as pd
from data.sample_data import generate_clients
from utils.scoring import score_dataframe
from config.theme import THEMES, GOLD, RED, GREEN, AMBER, BLUE, PURPLE

# ── Default weights ───────────────────────────────────────────────────────────

DEFAULT_RISK_WEIGHTS = {
    "w_withdrawal":    12,   # Withdrawal pressure — strongest churn signal
    "w_volume_drop":   10,   # Volume decline — earliest warning sign
    "w_login":          6,   # Login inactivity
    "w_deposit_stale":  5,   # Deposit inactivity
    "w_complaints":     5,   # Complaints — important but should not dominate
    "w_equity_erosion": 5,   # Long-term equity erosion vs net deposits
    "w_equity_trend":   6,   # Short-term 30-day equity decline
}

DEFAULT_VALUE_WEIGHTS = {
    "v_lifetime_dep":   10,  # Lifetime deposits — highest weight
    "v_net_dep":         8,  # Net deposits (committed capital)
    "v_current_equity": 10,  # Current equity — equally highest weight
    "v_volume":          6,  # Trading volume
    "v_redeposits":      6,  # Redeposit loyalty
    "v_tenure":          5,  # Client tenure
    # No VIP weight — account type has no scoring impact
}

DEFAULT_PROF_WEIGHTS = {
    "a_commission": 8, "a_swap": 7, "a_spread": 5,
    "b_captured_losses": 10, "b_commission": 5, "b_swap": 4,
    "m_captured_losses": 7, "m_commission": 5, "m_swap": 4,
}

DEFAULT_REACT_WEIGHTS = {
    "r_login_window": 8, "r_lifetime_dep": 7,
    "r_redeposits": 6, "r_volume_hist": 7, "r_tenure": 5,
}

DEFAULT_UPSIDE_WEIGHTS = {
    "u_equity":       8,   # Current equity size
    "u_net_dep":      6,   # Net deposits (committed capital)
    "u_volume_trend": 7,   # Positive trading volume trend
    "u_redeposits":   5,   # Redeposit loyalty
    "u_tenure":       4,   # Long-term client relationship
    # No VIP factor — upside is based on financial behaviour only
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

# ── Dark-theme backward-compat constants ──────────────────────────────────────
_DARK  = THEMES["dark"]
BG     = _DARK["bg"]
CARD   = _DARK["card"]
BORDER = _DARK["border"]
TEXT   = _DARK["text"]
MUTED  = _DARK["muted"]

PLOTLY_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=_DARK["plot_bg"],
    font=dict(color=TEXT, family="Inter, sans-serif"),
    margin=dict(l=10, r=10, t=40, b=10),
    coloraxis_colorbar=dict(tickfont=dict(color=TEXT)),
)


# ── Theme-aware helpers ───────────────────────────────────────────────────────

def get_colors() -> dict:
    """Return the current theme's color palette. Call at render time, not import time."""
    theme_key = st.session_state.get("theme", "dark")
    t = THEMES.get(theme_key, THEMES["dark"])
    return {
        **t,
        "gold": GOLD, "red": RED, "green": GREEN,
        "amber": AMBER, "blue": BLUE, "purple": PURPLE,
    }


def get_plotly_layout(**overrides) -> dict:
    """Return a theme-aware Plotly layout dict. Keyword overrides replace defaults."""
    c = get_colors()
    base = dict(
        paper_bgcolor=c["bg"],
        plot_bgcolor=c["plot_bg"],
        font=dict(color=c["text"], family="Inter, sans-serif"),
        margin=dict(l=10, r=10, t=40, b=10),
        coloraxis_colorbar=dict(tickfont=dict(color=c["text"])),
    )
    base.update(overrides)
    return base


# ── Theme CSS ─────────────────────────────────────────────────────────────────

def apply_theme():
    """Inject CSS for the currently selected theme (dark or light)."""
    theme_key = st.session_state.get("theme", "dark")
    t = THEMES.get(theme_key, THEMES["dark"])

    bg       = t["bg"]
    card     = t["card"]
    sidebar  = t["sidebar_bg"]
    border   = t["border"]
    text     = t["text"]
    muted    = t["muted"]
    sec      = t["secondary_bg"]
    input_bg = t["input_bg"]

    st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg}; color: {text}; }}
    .stApp > header {{ background-color: {bg}; }}

    [data-testid="stSidebar"] {{ background-color: {sidebar}; border-right: 1px solid {border}; }}
    [data-testid="stSidebar"] * {{ color: {text} !important; }}

    [data-testid="stMetric"] {{
        background-color: {card};
        border: 1px solid {border};
        border-radius: 8px;
        padding: 12px 16px;
    }}
    [data-testid="stMetricLabel"] {{ color: {muted} !important; font-size: 12px; }}
    [data-testid="stMetricValue"] {{ color: {GOLD} !important; font-size: 22px; font-weight: 700; }}
    [data-testid="stMetricDelta"] {{ color: {muted} !important; }}

    [data-testid="stExpander"] {{
        background-color: {sec};
        border: 1px solid {border};
        border-radius: 8px;
    }}

    [data-testid="stSelectbox"] > div > div {{ background-color: {input_bg}; color: {text}; }}
    .stTextInput input {{ background-color: {input_bg}; color: {text}; border-color: {border}; }}
    .stMultiSelect > div {{ background-color: {input_bg}; }}

    .stTabs [data-baseweb="tab-list"] {{ background-color: {sec}; border-bottom: 1px solid {border}; }}
    .stTabs [data-baseweb="tab"] {{ color: {muted}; }}
    .stTabs [aria-selected="true"] {{ color: {GOLD} !important; border-bottom: 2px solid {GOLD}; }}

    .stButton > button {{
        background-color: {card};
        color: {GOLD};
        border: 1px solid {GOLD};
        border-radius: 6px;
        font-weight: 600;
    }}
    .stButton > button:hover {{ background-color: {GOLD}; color: {bg}; }}
    .stButton > button[kind="primary"] {{ background-color: {GOLD}; color: {bg}; }}

    [data-testid="stSlider"] > div > div > div {{ background-color: {GOLD} !important; }}

    [data-testid="stDataFrame"] {{ background-color: {card}; }}
    iframe {{ background-color: {card} !important; }}

    hr {{ border-color: {border}; }}

    [data-testid="stAlert"] {{ background-color: {card}; border-color: {border}; }}

    .stMarkdown p, .stMarkdown li {{ color: {text}; }}
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{ color: {GOLD}; }}
    </style>
    """, unsafe_allow_html=True)


# ── Data loader ───────────────────────────────────────────────────────────────

def load_data() -> pd.DataFrame:
    """Return scored DataFrame from session state, generating if first run."""
    if "scored_df" not in st.session_state:
        refresh_data()
    return st.session_state["scored_df"]


def refresh_data():
    """Regenerate sample data and recompute all scores."""
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
        st.session_state.get("risk_weights",    DEFAULT_RISK_WEIGHTS),
        st.session_state.get("value_weights",   DEFAULT_VALUE_WEIGHTS),
        st.session_state.get("prof_weights",    DEFAULT_PROF_WEIGHTS),
        st.session_state.get("react_weights",   DEFAULT_REACT_WEIGHTS),
        st.session_state.get("upside_weights",  DEFAULT_UPSIDE_WEIGHTS),
        st.session_state.get("thresholds",      DEFAULT_THRESHOLDS),
        rules=st.session_state["scoring_rules"],
    )
    st.session_state["scored_df"] = scored
    try:
        init_db()
        source = st.session_state.get("data_source", "sample")
        save_snapshot(scored, source=source)
        log_refresh(source, len(scored), "success", round(time.time() - t0, 2))
    except Exception:
        pass


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
        f"<h2 style='color:{GOLD};margin-bottom:2px'>{title}</h2>",
        unsafe_allow_html=True
    )
    if subtitle:
        st.markdown(
            f"<p style='color:#94A3B8;margin-top:0;margin-bottom:8px'>{subtitle}</p>",
            unsafe_allow_html=True
        )
    st.divider()
