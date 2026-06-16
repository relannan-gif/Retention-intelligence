# pages/4_Action_Center.py  —  Profitability-first action queue with team owner assignment

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Action Center", page_icon="🚨", layout="wide")

from utils.helpers import (
    apply_theme, load_data, fmt_currency, page_header,
    GOLD, RED, GREEN, AMBER, BLUE, PURPLE, MUTED, PLOTLY_LAYOUT,
    get_plotly_layout,
)
from utils.session_init import init_session_state
from utils.auth import require_login
from utils.permissions import filter_data_for_user, no_data_warning

apply_theme()
init_session_state()
user = require_login()
page_header("🚨 Action Center",
            "Profitability-first · protect the most revenue today")

df = filter_data_for_user(load_data(), user)
if df.empty:
    no_data_warning(user)
    st.stop()
t  = st.session_state["thresholds"]

# Sort: profitability DESC, then value DESC, then risk DESC
action_df = df[df["recommended_action"] != "Monitor Only"].copy()
action_df = action_df.sort_values(
    ["profitability_score", "commercial_value_score", "retention_risk_score"],
    ascending=[False, False, False]
)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Clients Needing Action",    len(action_df))
k2.metric("Avg Priority Score",        f"{action_df['priority_score'].mean():.1f}")
k3.metric("Annual Revenue at Stake",
          fmt_currency((action_df["spread_commission_revenue"] +
                         action_df["commission_revenue"] +
                         action_df["swap_revenue"]).sum() * 12))
k4.metric("Annual Profitability at Stake",
          fmt_currency(action_df["net_company_pnl"].sum() * 12))

st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────
fc1, fc2, fc3 = st.columns(3)
with fc1:
    all_actions = sorted(action_df["recommended_action"].unique())
    sel_actions = st.multiselect("Filter by action", all_actions)
with fc2:
    all_owners = sorted(action_df["recommended_owner"].unique())
    sel_owner  = st.selectbox("Filter by owner", ["All"] + all_owners)
with fc3:
    sel_prio   = st.selectbox("Priority level", ["All", "Critical", "Elevated", "Normal"])

if sel_actions:
    action_df = action_df[action_df["recommended_action"].isin(sel_actions)]
if sel_owner != "All":
    action_df = action_df[action_df["recommended_owner"] == sel_owner]
if sel_prio != "All":
    action_df = action_df[action_df["priority_level"] == sel_prio]

st.markdown(f"**{len(action_df)} clients** match the current filters.")

st.divider()

# ── Action breakdown chart ─────────────────────────────────────────────────────
ac1, ac2 = st.columns(2)

with ac1:
    action_counts = action_df["recommended_action"].value_counts().reset_index()
    action_counts.columns = ["action", "count"]
    fig1 = px.bar(action_counts, x="count", y="action", orientation="h",
                  color="count", color_continuous_scale="Reds",
                  title="Clients by Recommended Action",
                  labels={"count": "Clients", "action": ""})
    fig1.update_layout(**get_plotly_layout(), height=320, showlegend=False,
                       coloraxis_showscale=False)
    st.plotly_chart(fig1, use_container_width=True)

with ac2:
    owner_counts = action_df["recommended_owner"].value_counts().reset_index()
    owner_counts.columns = ["owner", "count"]
    fig2 = px.pie(owner_counts, names="owner", values="count",
                  title="Action Distribution by Recommended Owner",
                  color_discrete_sequence=[GOLD, RED, GREEN, BLUE, PURPLE])
    fig2.update_layout(**get_plotly_layout(), height=320)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Action table ───────────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Action List — Sorted by Profitability → Value → Risk</h4>",
            unsafe_allow_html=True)

display_cols = [
    "client_id", "client_name", "country", "account_manager", "book_type",
    "priority_score", "profitability_score", "retention_risk_score",
    "commercial_value_score", "client_health_score",
    "priority_level", "health_label", "segment",
    "recommended_action", "recommended_owner", "action_reason",
    "current_equity", "net_company_pnl",
]

st.dataframe(
    action_df[display_cols].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
    column_config={
        "priority_score": st.column_config.ProgressColumn(
            "Priority", min_value=0, max_value=100, format="%.0f"),
        "profitability_score": st.column_config.ProgressColumn(
            "Profit Score", min_value=0, max_value=100, format="%.0f"),
        "retention_risk_score": st.column_config.ProgressColumn(
            "Risk Score", min_value=0, max_value=100, format="%.0f"),
        "commercial_value_score": st.column_config.ProgressColumn(
            "Value Score", min_value=0, max_value=100, format="%.0f"),
        "client_health_score": st.column_config.ProgressColumn(
            "Health", min_value=0, max_value=100, format="%.0f"),
        "current_equity": st.column_config.NumberColumn("Equity ($)", format="$%.0f"),
        "net_company_pnl": st.column_config.NumberColumn("Monthly PnL ($)", format="$%.0f"),
    },
)

st.divider()

# ── Team-level view ────────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Team Workload Summary</h4>",
            unsafe_allow_html=True)

team_summary = (
    action_df.groupby("recommended_owner")
    .agg(
        clients=("client_id", "count"),
        avg_priority=("priority_score", "mean"),
        avg_profitability=("profitability_score", "mean"),
        total_equity=("current_equity", "sum"),
        annual_rev=("spread_commission_revenue", lambda x: x.sum() * 12),
        annual_pnl=("net_company_pnl", lambda x: x.sum() * 12),
    )
    .sort_values("avg_priority", ascending=False)
    .reset_index()
)
team_summary["avg_priority"]      = team_summary["avg_priority"].round(1)
team_summary["avg_profitability"] = team_summary["avg_profitability"].round(1)
team_summary["total_equity"]      = team_summary["total_equity"].apply(fmt_currency)
team_summary["annual_rev"]        = team_summary["annual_rev"].apply(fmt_currency)
team_summary["annual_pnl"]        = team_summary["annual_pnl"].apply(fmt_currency)
team_summary.columns = [
    "Owner Team", "Clients", "Avg Priority", "Avg Profitability",
    "Total Equity", "Annual Revenue", "Annual PnL"
]
st.dataframe(team_summary, use_container_width=True, hide_index=True)

st.divider()

# ── Deep-dive by action ────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Deep-Dive by Action Type</h4>",
            unsafe_allow_html=True)
sel_action = st.selectbox("Select action to analyse", sorted(df["recommended_action"].unique()))
subset = action_df[action_df["recommended_action"] == sel_action]

if len(subset) == 0:
    st.info("No clients with this action in the current filters.")
else:
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Clients",          len(subset))
    d2.metric("Avg Risk",         f"{subset['retention_risk_score'].mean():.1f}")
    d3.metric("Avg Profitability",f"{subset['profitability_score'].mean():.1f}")
    d4.metric("Total Equity",     fmt_currency(subset["current_equity"].sum()))

    country_counts = subset["country"].value_counts().head(8).reset_index()
    country_counts.columns = ["country", "count"]
    fig3 = px.bar(country_counts, x="country", y="count",
                  title=f"Country breakdown — '{sel_action}'",
                  color_discrete_sequence=[GOLD])
    fig3.update_layout(**get_plotly_layout(), height=260)
    st.plotly_chart(fig3, use_container_width=True)
