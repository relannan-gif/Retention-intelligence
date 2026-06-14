# pages/4_Action_Center.py
# Action Center — shows only clients that require an action right now.

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helpers import load_data, fmt_currency, page_header

st.set_page_config(page_title="Action Center", page_icon="🚨", layout="wide")

page_header("🚨 Action Center", "Clients requiring immediate commercial or retention action")

df = load_data()
thresholds = st.session_state["thresholds"]

# ── Filter to clients who need action ─────────────────────────────────────────
# We exclude "Watch only" — those don't need active intervention.
action_df = df[df["recommended_action"] != "Watch only"].copy()
action_df = action_df.sort_values("priority_score", ascending=False)

# ── Summary KPIs ──────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Clients Needing Action", len(action_df))
k2.metric("Avg Priority Score",     f"{action_df['priority_score'].mean():.1f}")
k3.metric("Equity at Stake",        fmt_currency(action_df["current_equity"].sum()))
k4.metric("Revenue at Stake",       fmt_currency(action_df["spread_commission_revenue"].sum()))

st.divider()

# ── Filter by action type ──────────────────────────────────────────────────────
all_actions   = sorted(action_df["recommended_action"].unique().tolist())
action_filter = st.multiselect(
    "Filter by recommended action (leave blank to show all)",
    options=all_actions,
    default=[],
)

if action_filter:
    action_df = action_df[action_df["recommended_action"].isin(action_filter)]

# ── Priority level filter ──────────────────────────────────────────────────────
prio_filter = st.selectbox(
    "Filter by priority level",
    ["All", "Critical", "Elevated", "Normal"],
)
if prio_filter != "All":
    action_df = action_df[action_df["priority_level"] == prio_filter]

st.markdown(f"**{len(action_df)} clients** match the current filters.")

st.divider()

# ── Action breakdown chart ─────────────────────────────────────────────────────
action_counts = (
    action_df["recommended_action"]
    .value_counts()
    .reset_index()
)
action_counts.columns = ["action", "count"]

fig_actions = px.bar(
    action_counts,
    x="count", y="action",
    orientation="h",
    color="count",
    color_continuous_scale="Reds",
    title="Clients by Recommended Action",
    labels={"count": "Number of Clients", "action": "Action"},
)
fig_actions.update_layout(height=350, showlegend=False)
st.plotly_chart(fig_actions, use_container_width=True)

st.divider()

# ── Action table ───────────────────────────────────────────────────────────────
st.markdown("### Action List")

display_cols = [
    "client_id",
    "client_name",
    "country",
    "account_manager",
    "priority_score",
    "retention_risk_score",
    "client_value_score",
    "priority_level",
    "recommended_action",
    "action_reason",
    "current_equity",
    "withdrawal_amount_last_30d",
    "last_deposit_days_ago",
    "login_days_ago",
    "complaints_last_30d",
    "open_tickets",
]

st.dataframe(
    action_df[display_cols].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
    column_config={
        "priority_score": st.column_config.ProgressColumn(
            "Priority", min_value=0, max_value=100, format="%.0f"
        ),
        "retention_risk_score": st.column_config.ProgressColumn(
            "Risk Score", min_value=0, max_value=100, format="%.0f"
        ),
        "client_value_score": st.column_config.ProgressColumn(
            "Value Score", min_value=0, max_value=100, format="%.0f"
        ),
        "current_equity": st.column_config.NumberColumn(
            "Equity ($)", format="$%.0f"
        ),
        "withdrawal_amount_last_30d": st.column_config.NumberColumn(
            "Withdrawal 30d ($)", format="$%.0f"
        ),
    },
)

# ── Per-action deep dives ──────────────────────────────────────────────────────
st.divider()
st.markdown("### Deep-Dive by Action Type")
selected_action = st.selectbox("Pick an action type to analyse", all_actions)

subset = action_df[action_df["recommended_action"] == selected_action]

if len(subset) == 0:
    st.info("No clients with this action in the current filters.")
else:
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Clients", len(subset))
        st.metric("Avg Risk",     f"{subset['retention_risk_score'].mean():.1f}")
        st.metric("Avg Value",    f"{subset['client_value_score'].mean():.1f}")
    with col2:
        st.metric("Total Equity", fmt_currency(subset["current_equity"].sum()))
        st.metric("Avg Equity",   fmt_currency(subset["current_equity"].mean()))
        st.metric("Total Withdrawals 30d", fmt_currency(subset["withdrawal_amount_last_30d"].sum()))

    # Country breakdown for this action
    country_counts = subset["country"].value_counts().head(8).reset_index()
    country_counts.columns = ["country", "count"]
    fig_c = px.bar(
        country_counts, x="country", y="count",
        title=f"Country breakdown — '{selected_action}'",
        color_discrete_sequence=["#3498DB"],
    )
    fig_c.update_layout(height=280)
    st.plotly_chart(fig_c, use_container_width=True)
