# pages/2_Client_List.py
# Full searchable and filterable client table.

import streamlit as st
import pandas as pd
from utils.helpers import load_data, fmt_currency, page_header

st.set_page_config(page_title="Client List", page_icon="👥", layout="wide")

page_header("👥 Client List", "Search and filter all 300 clients")

df = load_data()

# ── Filters ───────────────────────────────────────────────────────────────────
with st.expander("🔍 Filters", expanded=True):
    f1, f2, f3 = st.columns(3)
    f4, f5, f6, f7 = st.columns(4)

    with f1:
        search_name = st.text_input("Search by name or ID", "")

    with f2:
        countries = ["All"] + sorted(df["country"].unique().tolist())
        sel_country = st.selectbox("Country", countries)

    with f3:
        ams = ["All"] + sorted(df["account_manager"].unique().tolist())
        sel_am = st.selectbox("Account Manager", ams)

    with f4:
        ibs = ["All"] + sorted(df["ib_name"].unique().tolist())
        sel_ib = st.selectbox("IB Name", ibs)

    with f5:
        book_types = ["All"] + sorted(df["book_type"].unique().tolist())
        sel_book = st.selectbox("Book Type", book_types)

    with f6:
        acct_types = ["All"] + sorted(df["account_type"].unique().tolist())
        sel_acct = st.selectbox("Account Type", acct_types)

    with f7:
        risk_levels   = ["All", "Low", "Medium", "High"]
        sel_risk_lvl  = st.selectbox("Risk Level", risk_levels)

    priority_levels = ["All", "Normal", "Elevated", "Critical"]
    sel_prio_lvl    = st.selectbox("Priority Level", priority_levels)

# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = df.copy()

if search_name:
    mask = (
        filtered["client_name"].str.contains(search_name, case=False, na=False) |
        filtered["client_id"].str.contains(search_name, case=False, na=False)
    )
    filtered = filtered[mask]

if sel_country != "All":
    filtered = filtered[filtered["country"] == sel_country]

if sel_am != "All":
    filtered = filtered[filtered["account_manager"] == sel_am]

if sel_ib != "All":
    filtered = filtered[filtered["ib_name"] == sel_ib]

if sel_book != "All":
    filtered = filtered[filtered["book_type"] == sel_book]

if sel_acct != "All":
    filtered = filtered[filtered["account_type"] == sel_acct]

if sel_risk_lvl != "All":
    filtered = filtered[filtered["risk_level"] == sel_risk_lvl]

if sel_prio_lvl != "All":
    filtered = filtered[filtered["priority_level"] == sel_prio_lvl]

# ── Sort control ──────────────────────────────────────────────────────────────
sort_col = st.selectbox(
    "Sort by",
    ["priority_score", "retention_risk_score", "client_value_score",
     "current_equity", "lifetime_deposits", "last_deposit_days_ago"],
    index=0,
)
sort_asc = st.checkbox("Sort ascending", value=False)
filtered = filtered.sort_values(sort_col, ascending=sort_asc)

st.markdown(f"**{len(filtered)} clients** match your filters.")

# ── Display table ─────────────────────────────────────────────────────────────
display_cols = [
    "client_id", "client_name", "country", "account_manager",
    "book_type", "account_type",
    "retention_risk_score", "client_value_score", "priority_score",
    "risk_level", "priority_level",
    "current_equity", "lifetime_deposits", "last_deposit_days_ago",
    "withdrawal_amount_last_30d", "trading_volume_last_30d",
    "login_days_ago", "recommended_action",
]

st.dataframe(
    filtered[display_cols].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
    column_config={
        "retention_risk_score": st.column_config.ProgressColumn(
            "Risk Score", min_value=0, max_value=100, format="%.0f"
        ),
        "client_value_score": st.column_config.ProgressColumn(
            "Value Score", min_value=0, max_value=100, format="%.0f"
        ),
        "priority_score": st.column_config.ProgressColumn(
            "Priority", min_value=0, max_value=100, format="%.0f"
        ),
        "current_equity": st.column_config.NumberColumn(
            "Equity ($)", format="$%.0f"
        ),
        "lifetime_deposits": st.column_config.NumberColumn(
            "Lifetime Dep ($)", format="$%.0f"
        ),
        "withdrawal_amount_last_30d": st.column_config.NumberColumn(
            "Withdrawal 30d ($)", format="$%.0f"
        ),
        "trading_volume_last_30d": st.column_config.NumberColumn(
            "Volume 30d ($)", format="$%.0f"
        ),
    },
)

# ── Client detail expander ────────────────────────────────────────────────────
st.divider()
st.markdown("### Client Detail")
selected_id = st.selectbox(
    "Select a client to see full details",
    options=filtered["client_id"].tolist()
)

if selected_id:
    row = df[df["client_id"] == selected_id].iloc[0]

    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Risk Score",     f"{row['retention_risk_score']:.0f}/100")
    d2.metric("Value Score",    f"{row['client_value_score']:.0f}/100")
    d3.metric("Priority Score", f"{row['priority_score']:.0f}/100")
    d4.metric("Current Equity", fmt_currency(row["current_equity"]))

    st.markdown(f"**Recommended Action:** `{row['recommended_action']}`")
    st.markdown(f"**Reason:** {row['action_reason']}")

    with st.expander("Full client record"):
        st.json(row.to_dict())
