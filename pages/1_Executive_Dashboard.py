# pages/1_Executive_Dashboard.py
# Executive Dashboard — high-level KPIs and charts for leadership.

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.helpers import load_data, fmt_currency, page_header

st.set_page_config(page_title="Executive Dashboard", page_icon="📈", layout="wide")

page_header("📈 Executive Dashboard", "Real-time overview of client retention health")

df = load_data()
thresholds       = st.session_state["thresholds"]
high_risk_t      = thresholds["high_risk"]
high_value_t     = thresholds["high_value"]
critical_prio_t  = thresholds["critical_priority"]

# ── KPI Row 1 ────────────────────────────────────────────────────────────────
st.markdown("### Key Performance Indicators")
k1, k2, k3, k4, k5, k6 = st.columns(6)

total_clients       = len(df)
high_risk_clients   = int((df["retention_risk_score"] >= high_risk_t).sum())
high_val_at_risk    = int(
    ((df["retention_risk_score"] >= high_risk_t) &
     (df["client_value_score"]   >= high_value_t)).sum()
)
total_equity_at_risk = df.loc[df["retention_risk_score"] >= high_risk_t, "current_equity"].sum()
total_withdrawals_30d = df["withdrawal_amount_last_30d"].sum()
revenue_at_risk = df.loc[
    df["retention_risk_score"] >= high_risk_t,
    "spread_commission_revenue"
].sum()

k1.metric("Total Clients",         total_clients)
k2.metric("High Risk Clients",     high_risk_clients,
          delta=f"{high_risk_clients/total_clients:.0%} of total",
          delta_color="inverse")
k3.metric("High-Value at Risk",    high_val_at_risk,
          delta="Needs immediate action", delta_color="inverse")
k4.metric("Equity at Risk",        fmt_currency(total_equity_at_risk),
          delta_color="inverse")
k5.metric("Withdrawals Last 30d",  fmt_currency(total_withdrawals_30d),
          delta_color="inverse")
k6.metric("Revenue at Risk",       fmt_currency(revenue_at_risk),
          delta_color="inverse")

st.divider()

# ── Charts Row 1 ─────────────────────────────────────────────────────────────
st.markdown("### Risk & Value Distribution")
ch1, ch2 = st.columns(2)

with ch1:
    # Retention risk histogram
    fig_risk = px.histogram(
        df, x="retention_risk_score", nbins=20,
        color_discrete_sequence=["#E74C3C"],
        title="Retention Risk Distribution",
        labels={"retention_risk_score": "Risk Score (0–100)"},
    )
    fig_risk.update_layout(showlegend=False, height=300)
    st.plotly_chart(fig_risk, use_container_width=True)

with ch2:
    # Client value histogram
    fig_value = px.histogram(
        df, x="client_value_score", nbins=20,
        color_discrete_sequence=["#2ECC71"],
        title="Client Value Distribution",
        labels={"client_value_score": "Value Score (0–100)"},
    )
    fig_value.update_layout(showlegend=False, height=300)
    st.plotly_chart(fig_value, use_container_width=True)

# ── Charts Row 2 ─────────────────────────────────────────────────────────────
st.markdown("### Priority Analysis")
ch3, ch4 = st.columns(2)

with ch3:
    # Priority score by country (top 10)
    country_priority = (
        df.groupby("country")["priority_score"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    fig_country = px.bar(
        country_priority, x="priority_score", y="country",
        orientation="h",
        color="priority_score",
        color_continuous_scale="RdYlGn_r",
        title="Avg Priority Score by Country (Top 10)",
        labels={"priority_score": "Avg Priority", "country": "Country"},
    )
    fig_country.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_country, use_container_width=True)

with ch4:
    # Priority by account manager
    am_priority = (
        df.groupby("account_manager")["priority_score"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig_am = px.bar(
        am_priority, x="priority_score", y="account_manager",
        orientation="h",
        color="priority_score",
        color_continuous_scale="RdYlGn_r",
        title="Avg Priority Score by Account Manager",
        labels={"priority_score": "Avg Priority", "account_manager": "Account Manager"},
    )
    fig_am.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig_am, use_container_width=True)

# ── Charts Row 3 ─────────────────────────────────────────────────────────────
ch5, ch6 = st.columns(2)

with ch5:
    # Book type breakdown
    book_counts = df["book_type"].value_counts().reset_index()
    book_counts.columns = ["book_type", "count"]
    fig_book = px.pie(
        book_counts, names="book_type", values="count",
        title="Client Distribution by Book Type",
        color_discrete_map={
            "A-Book": "#3498DB",
            "B-Book": "#E67E22",
            "M-Book": "#9B59B6"
        }
    )
    fig_book.update_layout(height=320)
    st.plotly_chart(fig_book, use_container_width=True)

with ch6:
    # Risk level distribution (pie)
    risk_level_counts = df["risk_level"].value_counts().reset_index()
    risk_level_counts.columns = ["risk_level", "count"]
    fig_risk_pie = px.pie(
        risk_level_counts, names="risk_level", values="count",
        title="Clients by Risk Level",
        color_discrete_map={
            "Low": "#27AE60",
            "Medium": "#F39C12",
            "High": "#E74C3C"
        }
    )
    fig_risk_pie.update_layout(height=320)
    st.plotly_chart(fig_risk_pie, use_container_width=True)

st.divider()

# ── Top 5 Tables ─────────────────────────────────────────────────────────────
st.markdown("### Top Retention Opportunities")
t1, t2 = st.columns(2)

with t1:
    st.markdown("**Top 5 Countries by Avg Risk**")
    top_countries = (
        df.groupby("country")
        .agg(
            avg_risk=("retention_risk_score", "mean"),
            clients=("client_id", "count"),
            equity_at_risk=("current_equity", "sum"),
        )
        .sort_values("avg_risk", ascending=False)
        .head(5)
        .reset_index()
    )
    top_countries["avg_risk"] = top_countries["avg_risk"].round(1)
    top_countries["equity_at_risk"] = top_countries["equity_at_risk"].apply(fmt_currency)
    st.dataframe(top_countries, use_container_width=True, hide_index=True)

with t2:
    st.markdown("**Top 5 Account Managers by Retention Opportunity**")
    top_ams = (
        df.groupby("account_manager")
        .agg(
            high_risk_clients=("retention_risk_score", lambda x: (x >= high_risk_t).sum()),
            avg_priority=("priority_score", "mean"),
            equity_managed=("current_equity", "sum"),
        )
        .sort_values("high_risk_clients", ascending=False)
        .head(5)
        .reset_index()
    )
    top_ams["avg_priority"] = top_ams["avg_priority"].round(1)
    top_ams["equity_managed"] = top_ams["equity_managed"].apply(fmt_currency)
    st.dataframe(top_ams, use_container_width=True, hide_index=True)
