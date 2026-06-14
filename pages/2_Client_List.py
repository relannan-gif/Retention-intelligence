# pages/2_Client_List.py  —  Full searchable/filterable client table with all 6 scores

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Client List", page_icon="👥", layout="wide")

from utils.helpers import (
    apply_theme, load_data, fmt_currency, page_header,
    GOLD, RED, GREEN, AMBER, BLUE, MUTED, PLOTLY_LAYOUT,
    get_plotly_layout,
)
from utils.session_init import init_session_state

apply_theme()
init_session_state()
page_header("👥 Client List", "All 300 clients · 6 scores · searchable and filterable")

df = load_data()
t  = st.session_state["thresholds"]

# ── Filters ───────────────────────────────────────────────────────────────────
with st.expander("Filters", expanded=True):
    fc1, fc2, fc3 = st.columns(3)
    fc4, fc5, fc6 = st.columns(3)
    fc7, fc8      = st.columns(2)

    with fc1:
        search = st.text_input("Search name or client ID", "")
    with fc2:
        sel_country = st.selectbox("Country", ["All"] + sorted(df["country"].unique()))
    with fc3:
        sel_am = st.selectbox("Account Manager", ["All"] + sorted(df["account_manager"].unique()))
    with fc4:
        sel_ib = st.selectbox("IB Name", ["All"] + sorted(df["ib_name"].unique()))
    with fc5:
        sel_book = st.selectbox("Book Type", ["All", "A-Book", "B-Book", "M-Book"])
    with fc6:
        sel_acct = st.selectbox("Account Type", ["All"] + sorted(df["account_type"].unique()))
    with fc7:
        sel_risk = st.selectbox("Risk Level", ["All", "Low", "Medium", "High"])
    with fc8:
        sel_health = st.selectbox("Health", ["All", "Excellent", "Healthy", "Watchlist", "At Risk", "Critical"])

filtered = df.copy()

if search:
    m = (filtered["client_name"].str.contains(search, case=False, na=False) |
         filtered["client_id"].str.contains(search, case=False, na=False))
    filtered = filtered[m]
if sel_country != "All":   filtered = filtered[filtered["country"] == sel_country]
if sel_am      != "All":   filtered = filtered[filtered["account_manager"] == sel_am]
if sel_ib      != "All":   filtered = filtered[filtered["ib_name"] == sel_ib]
if sel_book    != "All":   filtered = filtered[filtered["book_type"] == sel_book]
if sel_acct    != "All":   filtered = filtered[filtered["account_type"] == sel_acct]
if sel_risk    != "All":   filtered = filtered[filtered["risk_level"] == sel_risk]
if sel_health  != "All":   filtered = filtered[filtered["health_label"] == sel_health]

sort_col = st.selectbox("Sort by", [
    "priority_score", "retention_risk_score", "commercial_value_score",
    "profitability_score", "reactivation_score", "vip_upside_score",
    "client_health_score", "current_equity", "lifetime_deposits",
])
sort_asc = st.checkbox("Sort ascending", False)
filtered = filtered.sort_values(sort_col, ascending=sort_asc)

st.markdown(f"**{len(filtered)} clients** match your filters.")

# ── Summary KPIs for filtered set ─────────────────────────────────────────────
if len(filtered) > 0:
    sm1, sm2, sm3, sm4 = st.columns(4)
    sm1.metric("Avg Risk Score",         f"{filtered['retention_risk_score'].mean():.1f}")
    sm2.metric("Avg Profitability Score", f"{filtered['profitability_score'].mean():.1f}")
    sm3.metric("Total Equity",            fmt_currency(filtered["current_equity"].sum()))
    sm4.metric("Annual Revenue (est.)",
               fmt_currency((filtered["spread_commission_revenue"] +
                              filtered["commission_revenue"] +
                              filtered["swap_revenue"]).sum() * 12))

# ── Table ─────────────────────────────────────────────────────────────────────
display_cols = [
    "client_id", "client_name", "country", "account_manager",
    "book_type", "account_type", "vip_status", "health_label",
    "retention_risk_score", "commercial_value_score", "profitability_score",
    "reactivation_score", "vip_upside_score", "client_health_score", "priority_score",
    "segment", "recommended_action", "recommended_owner",
    "current_equity", "net_company_pnl",
]

st.dataframe(
    filtered[display_cols].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
    column_config={
        "retention_risk_score": st.column_config.ProgressColumn(
            "Risk", min_value=0, max_value=100, format="%.0f"),
        "commercial_value_score": st.column_config.ProgressColumn(
            "Value", min_value=0, max_value=100, format="%.0f"),
        "profitability_score": st.column_config.ProgressColumn(
            "Profitability", min_value=0, max_value=100, format="%.0f"),
        "reactivation_score": st.column_config.ProgressColumn(
            "Reactivation", min_value=0, max_value=100, format="%.0f"),
        "vip_upside_score": st.column_config.ProgressColumn(
            "VIP Upside", min_value=0, max_value=100, format="%.0f"),
        "client_health_score": st.column_config.ProgressColumn(
            "Health", min_value=0, max_value=100, format="%.0f"),
        "priority_score": st.column_config.ProgressColumn(
            "Priority", min_value=0, max_value=100, format="%.0f"),
        "current_equity": st.column_config.NumberColumn("Equity ($)", format="$%.0f"),
        "net_company_pnl": st.column_config.NumberColumn("Monthly PnL ($)", format="$%.0f"),
        "vip_status": st.column_config.CheckboxColumn("VIP"),
    },
)

# ── Client detail ─────────────────────────────────────────────────────────────
st.divider()
st.markdown(f"<h4 style='color:{GOLD}'>Client Detail</h4>", unsafe_allow_html=True)

if len(filtered) == 0:
    st.info("No clients match the current filters.")
else:
    sel_id = st.selectbox("Select a client", filtered["client_id"].tolist())
    row = df[df["client_id"] == sel_id].iloc[0]

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Risk Score",         f"{row['retention_risk_score']:.0f}/100")
    c2.metric("Value Score",        f"{row['commercial_value_score']:.0f}/100")
    c3.metric("Profitability",      f"{row['profitability_score']:.0f}/100")
    c4.metric("Reactivation",       f"{row['reactivation_score']:.0f}/100")
    c5.metric("VIP Upside",         f"{row['vip_upside_score']:.0f}/100")
    c6.metric("Health Score",       f"{row['client_health_score']:.0f}/100")

    st.markdown(
        f"**Segment:** `{row['segment']}`  ·  "
        f"**Action:** `{row['recommended_action']}`  ·  "
        f"**Owner:** `{row['recommended_owner']}`"
    )
    st.caption(f"Reason: {row['action_reason']}")

    d1, d2 = st.columns(2)
    with d1:
        st.markdown("**Financial summary**")
        st.write({
            "Book Type":        row["book_type"],
            "Current Equity":   fmt_currency(row["current_equity"]),
            "Lifetime Deposits": fmt_currency(row["lifetime_deposits"]),
            "Net Deposits":     fmt_currency(row["net_deposits"]),
            "Monthly PnL":      fmt_currency(row["net_company_pnl"]),
            "Account Status":   row["account_status"],
            "VIP Status":       "Yes" if row["vip_status"] else "No",
            "Tenure (days)":    int(row["client_tenure_days"]),
        })
    with d2:
        st.markdown("**Activity summary**")
        st.write({
            "Last Login":       f"{row['login_days_ago']}d ago",
            "Last Deposit":     f"{row['last_deposit_days_ago']}d ago",
            "Last Withdrawal":  f"{row['last_withdrawal_days_ago']}d ago",
            "Volume (30d)":     fmt_currency(row["trading_volume_last_30d"]),
            "Volume (90d)":     fmt_currency(row["volume_90d_ago"]),
            "Redeposits":       int(row["number_of_redeposits"]),
            "Complaints (30d)": int(row["complaints_last_30d"]),
            "Open Tickets":     int(row["open_tickets"]),
        })

    # ── Score Contribution Breakdown ─────────────────────────────────────────
    import plotly.graph_objects as go
    from utils.rules_engine import get_factor_breakdown, load_rules

    st.divider()
    st.markdown(f"<h5 style='color:{GOLD}'>Score Contribution Analysis — why did this client score this way?</h5>",
                unsafe_allow_html=True)
    st.caption("Each bar shows the raw band score (0–100) for that factor. "
               "The final score is a weighted combination of these signals.")

    rules   = st.session_state.get("scoring_rules") or load_rules()
    breakdown = get_factor_breakdown(row, rules)
    rf = breakdown["risk_factors"]
    vf = breakdown["value_factors"]

    bc1, bc2 = st.columns(2)
    with bc1:
        fig_rf = go.Figure(go.Bar(
            x=list(rf.values()), y=list(rf.keys()),
            orientation="h", marker_color=RED, opacity=0.80,
            text=[f"{v:.0f}" for v in rf.values()], textposition="outside",
        ))
        fig_rf.update_layout(
            **get_plotly_layout(), height=260,
            title=dict(text=f"Risk Factors  (score = {row['retention_risk_score']:.0f})",
                       font=dict(color=RED, size=12)),
            xaxis=dict(range=[0,105], title="Band Score (0–100)"),
            showlegend=False,
        )
        st.plotly_chart(fig_rf, use_container_width=True)

    with bc2:
        fig_vf = go.Figure(go.Bar(
            x=list(vf.values()), y=list(vf.keys()),
            orientation="h", marker_color=BLUE, opacity=0.80,
            text=[f"{v:.0f}" for v in vf.values()], textposition="outside",
        ))
        fig_vf.update_layout(
            **get_plotly_layout(), height=260,
            title=dict(text=f"Value Factors  (score = {row['commercial_value_score']:.0f})",
                       font=dict(color=BLUE, size=12)),
            xaxis=dict(range=[0,105], title="Band Score (0–100)"),
            showlegend=False,
        )
        st.plotly_chart(fig_vf, use_container_width=True)
