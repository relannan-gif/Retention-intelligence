# pages/3_Scoring_Engine.py
# Explains the scoring logic and lets users adjust weights with sliders.

import streamlit as st
import plotly.express as px
from utils.helpers import load_data, rescore, page_header

st.set_page_config(page_title="Scoring Engine", page_icon="⚙️", layout="wide")

page_header("⚙️ Scoring Engine", "Understand and adjust how clients are scored")

# ── Explainer ─────────────────────────────────────────────────────────────────
with st.expander("📖 How scoring works", expanded=False):
    st.markdown("""
    ### Scoring overview

    Every client gets **three scores** — all on a 0–100 scale:

    ---

    #### 1. Retention Risk Score (0–100)
    > Higher score = client is more likely to leave

    Built from 6 signals:

    | Signal | Meaning |
    |--------|---------|
    | **Withdrawal pressure** | Large recent withdrawals relative to equity |
    | **Volume drop** | Trading dropped significantly vs previous period |
    | **Login inactivity** | Client hasn't logged in recently |
    | **Deposit staleness** | No new deposits in a long time |
    | **Complaints / tickets** | Open issues signal dissatisfaction |
    | **Equity erosion** | Current equity is much lower than net deposits |

    ---

    #### 2. Client Value Score (0–100)
    > Higher score = client is more commercially important

    Built from 6 signals:

    | Signal | Meaning |
    |--------|---------|
    | **Lifetime deposits** | Total money ever deposited |
    | **Net deposits** | Deposits minus withdrawals |
    | **Trading volume** | Recent activity level |
    | **Redeposits** | Number of times client topped up — loyalty signal |
    | **Company PnL** | Profit the company makes from this client |
    | **Spread/commission revenue** | Revenue from client's trades |

    ---

    #### 3. Priority Score (0–100)
    > Combines risk + value. High risk AND high value = top priority.

    Formula: `Priority = (Risk × risk_blend) + (Value × (1 − risk_blend))`

    Default blend: **60% risk, 40% value**. You can adjust this below.

    ---

    #### How weights work
    Each signal has a weight from 0 to 10.
    Weight 0 = ignore that signal completely.
    Weight 10 = that signal has maximum influence.
    The weights are automatically normalised so they always add up to 100%.
    """)

df = load_data()

# ── Retention Risk Weights ────────────────────────────────────────────────────
st.markdown("### Retention Risk Weights")
st.caption("Drag sliders to change how much each factor influences the risk score.")

risk_weights = st.session_state["risk_weights"].copy()

rw1, rw2 = st.columns(2)
with rw1:
    risk_weights["w_withdrawal"]     = st.slider("💸 Withdrawal pressure",      0, 10, risk_weights["w_withdrawal"])
    risk_weights["w_volume_drop"]    = st.slider("📉 Volume drop",              0, 10, risk_weights["w_volume_drop"])
    risk_weights["w_login"]          = st.slider("🔒 Login inactivity",         0, 10, risk_weights["w_login"])
with rw2:
    risk_weights["w_deposit_stale"]  = st.slider("🏦 Deposit staleness",        0, 10, risk_weights["w_deposit_stale"])
    risk_weights["w_complaints"]     = st.slider("⚠️ Complaints / tickets",     0, 10, risk_weights["w_complaints"])
    risk_weights["w_equity_erosion"] = st.slider("📊 Equity erosion",           0, 10, risk_weights["w_equity_erosion"])

st.divider()

# ── Client Value Weights ───────────────────────────────────────────────────────
st.markdown("### Client Value Weights")
st.caption("Drag sliders to change how much each factor influences the value score.")

value_weights = st.session_state["value_weights"].copy()

vw1, vw2 = st.columns(2)
with vw1:
    value_weights["v_lifetime_dep"]  = st.slider("💰 Lifetime deposits",        0, 10, value_weights["v_lifetime_dep"])
    value_weights["v_net_dep"]       = st.slider("🏧 Net deposits",             0, 10, value_weights["v_net_dep"])
    value_weights["v_volume"]        = st.slider("📈 Trading volume",            0, 10, value_weights["v_volume"])
with vw2:
    value_weights["v_redeposits"]    = st.slider("🔄 Number of redeposits",     0, 10, value_weights["v_redeposits"])
    value_weights["v_pnl"]           = st.slider("🏢 Company PnL",              0, 10, value_weights["v_pnl"])
    value_weights["v_spread_rev"]    = st.slider("💹 Spread/commission revenue", 0, 10, value_weights["v_spread_rev"])

st.divider()

# ── Priority Blend ────────────────────────────────────────────────────────────
st.markdown("### Priority Score Blend")
risk_blend = st.slider(
    "Risk weight in Priority Score",
    min_value=0.0, max_value=1.0,
    value=float(st.session_state.get("risk_blend", 0.6)),
    step=0.05,
    help="0.6 means 60% risk + 40% value. Raise this to prioritise at-risk clients more."
)
st.caption(f"Priority = Risk × {risk_blend:.0%} + Value × {1-risk_blend:.0%}")

st.divider()

# ── Apply button ──────────────────────────────────────────────────────────────
if st.button("✅ Apply new weights and rescore all clients", type="primary"):
    st.session_state["risk_weights"]  = risk_weights
    st.session_state["value_weights"] = value_weights
    st.session_state["risk_blend"]    = risk_blend
    rescore()
    st.success("Scores updated! All pages now reflect the new weights.")
    st.balloons()

# ── Preview effect of weights ─────────────────────────────────────────────────
st.divider()
st.markdown("### Current Score Distribution")
st.caption("These charts show the current scores (before or after you apply changes).")

df = load_data()
ch1, ch2, ch3 = st.columns(3)

with ch1:
    fig1 = px.histogram(
        df, x="retention_risk_score", nbins=15,
        title="Risk Score Distribution",
        color_discrete_sequence=["#E74C3C"],
    )
    fig1.update_layout(height=280, showlegend=False)
    st.plotly_chart(fig1, use_container_width=True)

with ch2:
    fig2 = px.histogram(
        df, x="client_value_score", nbins=15,
        title="Value Score Distribution",
        color_discrete_sequence=["#2ECC71"],
    )
    fig2.update_layout(height=280, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

with ch3:
    fig3 = px.histogram(
        df, x="priority_score", nbins=15,
        title="Priority Score Distribution",
        color_discrete_sequence=["#3498DB"],
    )
    fig3.update_layout(height=280, showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

# ── Scatter: risk vs value ────────────────────────────────────────────────────
st.markdown("### Risk vs Value Scatter (bubble = equity)")
fig_scatter = px.scatter(
    df.sample(min(150, len(df))),  # sample to keep chart readable
    x="client_value_score",
    y="retention_risk_score",
    size="current_equity",
    color="priority_score",
    color_continuous_scale="RdYlGn_r",
    hover_data=["client_name", "country", "account_manager", "recommended_action"],
    labels={
        "client_value_score": "Client Value Score →",
        "retention_risk_score": "↑ Retention Risk Score",
        "priority_score": "Priority",
    },
    title="Top-right quadrant = highest priority (high value + high risk)",
    height=500,
)
# Add quadrant lines
thresholds = st.session_state["thresholds"]
fig_scatter.add_hline(y=thresholds["high_risk"],  line_dash="dash", line_color="red",    annotation_text="High Risk")
fig_scatter.add_vline(x=thresholds["high_value"], line_dash="dash", line_color="green",  annotation_text="High Value")
st.plotly_chart(fig_scatter, use_container_width=True)
