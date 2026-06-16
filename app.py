# app.py  —  OneRoyal Client Intelligence Platform  (Phase 2)
# Run with:  streamlit run app.py

import streamlit as st

st.set_page_config(
    page_title="OneRoyal Client Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.helpers import (
    apply_theme, load_data, refresh_data,
    DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS, DEFAULT_PROF_WEIGHTS,
    DEFAULT_REACT_WEIGHTS, DEFAULT_UPSIDE_WEIGHTS, DEFAULT_THRESHOLDS,
    fmt_currency, GOLD, RED, AMBER, GREEN,
)
from utils.session_init import init_session_state
from utils.auth import require_login
from utils.permissions import filter_data_for_user

apply_theme()
init_session_state()

# ── Authentication gate ───────────────────────────────────────────────────────
user = require_login()

load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
full_df = st.session_state["scored_df"]
df = filter_data_for_user(full_df, user)
t  = st.session_state["thresholds"]

st.sidebar.markdown(
    f"<h2 style='color:{GOLD}'>OneRoyal</h2>"
    "<p style='color:#94A3B8;margin-top:-10px;font-size:13px'>"
    "Client Intelligence Platform</p>",
    unsafe_allow_html=True
)
st.sidebar.divider()

high_risk        = int((df["retention_risk_score"] >= t["high_risk"]).sum())
critical         = int((df["priority_score"] >= t["critical_priority"]).sum())
high_val_at_risk = int(
    ((df["retention_risk_score"] >= t["high_risk"]) &
     (df["commercial_value_score"] >= t["high_value"])).sum()
)

st.sidebar.metric("Your Clients",       len(df))
st.sidebar.metric("Clients At Risk",    high_risk)
st.sidebar.metric("Critical Priority",  critical)
st.sidebar.metric("High-Value At Risk", high_val_at_risk)
st.sidebar.divider()
st.sidebar.caption("Navigate using the pages above.")

# ── Home page ─────────────────────────────────────────────────────────────────
st.markdown(
    f"<h1 style='color:{GOLD};font-size:2rem'>📊 OneRoyal Client Intelligence Platform</h1>",
    unsafe_allow_html=True
)
st.markdown(
    f"<p style='color:#94A3B8'>Welcome, <b>{user['full_name']}</b> · "
    f"{user['role']} · A-Book · B-Book · M-Book · Phase 2</p>",
    unsafe_allow_html=True
)
st.divider()

# Six KPI cards (scoped to user's visible clients)
k1, k2, k3, k4, k5, k6 = st.columns(6)

equity_at_risk = df.loc[df["retention_risk_score"] >= t["high_risk"], "current_equity"].sum()

annual_revenue_at_risk = (
    df.loc[df["retention_risk_score"] >= t["high_risk"],
           ["spread_commission_revenue", "commission_revenue", "swap_revenue"]]
    .sum().sum() * 12
)
annual_profit_at_risk = (
    df.loc[df["retention_risk_score"] >= t["high_risk"], "net_company_pnl"].sum() * 12
)

k1.metric("Your Clients",                len(df))
k2.metric("Clients At Risk",             high_risk)
k3.metric("High-Value At Risk",          high_val_at_risk)
k4.metric("Equity At Risk",              fmt_currency(equity_at_risk))
k5.metric("Annual Revenue At Risk",      fmt_currency(annual_revenue_at_risk))
k6.metric("Annual Profitability At Risk", fmt_currency(annual_profit_at_risk))

st.divider()
st.markdown("""
| Page | Purpose |
|------|---------|
| **Executive Dashboard** | Board-level KPIs, geographic & AM analysis, segmentation matrix, trend analytics |
| **Client List** | Full filterable client table with all 6 scores |
| **Scoring Engine** | Adjust scoring weights · Understand book-type logic · Scatter analysis |
| **Action Center** | Prioritised action queue — profitability-first · Team owner assignment |
| **Settings** | Configure risk / value / profitability thresholds |
""")
st.info("💡 Start with **Executive Dashboard** or go directly to **Action Center** to see today's call list.")
