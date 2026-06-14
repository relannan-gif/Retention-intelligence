# pages/3_Scoring_Engine.py  —  6-score explainer with live weight sliders

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Scoring Engine", page_icon="⚙️", layout="wide")

from utils.helpers import (
    apply_theme, load_data, rescore, page_header,
    DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS,
    DEFAULT_REACT_WEIGHTS, DEFAULT_UPSIDE_WEIGHTS,
    GOLD, RED, GREEN, AMBER, BLUE, PURPLE, PLOTLY_LAYOUT,
    get_plotly_layout,
)
from utils.session_init import init_session_state

apply_theme()
init_session_state()
page_header("⚙️ Scoring Engine",
            "Six book-aware scores · adjust weights · live scatter analysis")

df = load_data()
t  = st.session_state["thresholds"]

# ── Score explainer ───────────────────────────────────────────────────────────
with st.expander("How all 6 scores work (click to read)", expanded=False):
    st.markdown(f"""
<div style='color:#E8E8E8'>

### The 6 Scores — all on a 0–100 scale

---

#### 1. Retention Risk Score
> **Higher = more likely to leave**

7 signals: withdrawal pressure · volume drop · login inactivity · deposit staleness ·
complaints + tickets · equity erosion vs deposits · equity declining vs 30 days ago

---

#### 2. Commercial Value Score
> **Higher = more commercially important**

6 financial signals: lifetime deposits · net deposits · current equity · trading volume ·
redeposit count · client tenure. Value is measured by financial behaviour only — no account type classification.

---

#### 3. Profitability Score ← **Book-type aware**
> **Higher = more profit for OneRoyal**

| Book Type | How Profitability is Calculated |
|-----------|--------------------------------|
| **A-Book** | Spread revenue + Commission + Swap income (all fee-based) |
| **B-Book** | Captured client losses + Commission + Swap (no spread — position P&L model) |
| **M-Book** | (internal_ratio × captured losses) + Commission + Swap (no spread) |

B-Book clients who are winning (costing the company money) will score LOW here.
B-Book clients who are losing (profitable for OneRoyal) will score HIGH.

---

#### 4. Reactivation Score
> **Higher = best candidate to call and win back**

Scores highest for clients who were active 30–180 days ago (not too recent,
not completely gone), had high historical deposits, showed loyalty via redeposits,
and had strong trading volume in the past.

---

#### 5. Upside Potential Score
> **Higher = untapped growth potential**

Scores highest for clients with growing equity + growing volume trend + redeposit
loyalty + long tenure. Based purely on financial behaviour — no account classification used.
Factors: current equity size · net deposits · positive volume trend · redeposit count · tenure.

---

#### 6. Client Health Score
> **Composite positive metric. 100 = excellent business relationship.**

Formula: `(100 − Risk) × 50% + Value × 30% + Profitability × 20%`

Labels: **Excellent** (80+) · **Healthy** (60–79) · **Watchlist** (40–59) ·
**At Risk** (20–39) · **Critical** (0–19)

---

#### Priority Score (used to rank the Action Center)
Formula: `Risk×35% + Value×25% + Profitability×35% + Upside×5%`

</div>
""", unsafe_allow_html=True)

# ── Tabs for each score group ─────────────────────────────────────────────────
tab_rules, tab_risk, tab_val, tab_react, tab_upside, tab_dist = st.tabs([
    "Active Scoring Rules", "Risk Weights", "Value Weights", "Reactivation Weights",
    "Upside Potential Weights", "Score Distributions",
])

# ── Active Scoring Rules (read-only summary) ──────────────────────────────────
with tab_rules:
    from utils.rules_engine import load_rules
    import pandas as _pd

    if "scoring_rules" not in st.session_state:
        st.session_state["scoring_rules"] = load_rules()
    _rules = st.session_state["scoring_rules"]

    st.markdown(
        f"<h4 style='color:{GOLD}'>Active Business Rules — current scoring configuration</h4>",
        unsafe_allow_html=True,
    )
    st.caption("These are the rules currently in use. Edit them in the ⚙️ Settings page → Business Rules Engine section.")

    def _rules_table(factor_dict: dict):
        rows = []
        for fkey, fdata in factor_dict.items():
            for band in fdata["bands"]:
                rows.append({
                    "Factor":    fdata["label"],
                    "Band":      band["label"],
                    "Points":    band["points"],
                })
        return _pd.DataFrame(rows)

    col_rr, col_cv = st.columns(2)
    with col_rr:
        st.markdown(f"<h5 style='color:{GOLD}'>Retention Risk Factors</h5>",
                    unsafe_allow_html=True)
        rr_df = _rules_table(_rules["retention_risk"])
        st.dataframe(rr_df, hide_index=True, use_container_width=True)

    with col_cv:
        st.markdown(f"<h5 style='color:{GOLD}'>Commercial Value Factors</h5>",
                    unsafe_allow_html=True)
        cv_df = _rules_table(_rules["commercial_value"])
        st.dataframe(cv_df, hide_index=True, use_container_width=True)

    st.divider()
    st.markdown(f"<h5 style='color:{GOLD}'>Profitability Bands (by Book Type)</h5>",
                unsafe_allow_html=True)
    pr = _rules["profitability"]
    m_ratio = pr["m_book"].get("internal_ratio", 0.6)
    st.caption(f"M-Book internal ratio: **{m_ratio:.0%}** of client losses held internally")
    pc1, pc2, pc3 = st.columns(3)
    for col, bkey, clr in [
        (pc1, "a_book", BLUE),
        (pc2, "b_book", RED),
        (pc3, "m_book", PURPLE),
    ]:
        bdata = pr[bkey]
        col.markdown(
            f"<b style='color:{clr}'>{bdata['label']}</b><br>"
            f"<small style='color:#94A3B8'>{bdata.get('formula_label','')}</small>",
            unsafe_allow_html=True,
        )
        brows = [{"Band": b["label"], "Points": b["points"]} for b in bdata["bands"]]
        col.dataframe(_pd.DataFrame(brows), hide_index=True, use_container_width=True)


# ── Risk weights ──────────────────────────────────────────────────────────────
with tab_risk:
    st.markdown(f"<h4 style='color:{GOLD}'>Retention Risk Weights</h4>",
                unsafe_allow_html=True)
    st.caption(
        "Each weight controls the relative importance of a risk signal. "
        "Higher weight = that signal has more influence on the final Retention Risk Score. "
        "Weights are proportional — only the ratio between them matters, not the absolute values."
    )
    rw = st.session_state["risk_weights"].copy()
    c1, c2 = st.columns(2)
    with c1:
        rw["w_withdrawal"]     = st.slider("Withdrawal pressure (strongest churn signal)",    0, 15, rw["w_withdrawal"])
        rw["w_volume_drop"]    = st.slider("Volume drop (early warning — precedes withdrawal)",0, 15, rw["w_volume_drop"])
        rw["w_login"]          = st.slider("Login inactivity (platform disengagement)",       0, 15, rw["w_login"])
        rw["w_equity_trend"]   = st.slider("Equity declining 30-day (short-term capital flight)", 0, 15, rw["w_equity_trend"])
    with c2:
        rw["w_deposit_stale"]  = st.slider("Deposit inactivity (no top-up signal)",          0, 15, rw["w_deposit_stale"])
        rw["w_complaints"]     = st.slider("Complaints + tickets (service dissatisfaction)", 0, 15, rw["w_complaints"])
        rw["w_equity_erosion"] = st.slider("Equity erosion vs net deposits (long-term P&L destruction)", 0, 15, rw["w_equity_erosion"])

    if st.button("Apply Risk Weights", type="primary", key="apply_risk"):
        st.session_state["risk_weights"] = rw
        rescore()
        st.success("Risk weights updated — all scores recalculated.")

# ── Value weights ─────────────────────────────────────────────────────────────
with tab_val:
    st.markdown(f"<h4 style='color:{GOLD}'>Commercial Value Weights</h4>",
                unsafe_allow_html=True)
    st.caption(
        "Controls what makes a client commercially important. "
        "Value is based entirely on financial behaviour — not account type. "
        "A higher weight means that factor contributes more to the Commercial Value Score."
    )
    vw = st.session_state["value_weights"].copy()
    c1, c2 = st.columns(2)
    with c1:
        vw["v_lifetime_dep"]   = st.slider("Lifetime deposits (total relationship size)",  0, 15, vw["v_lifetime_dep"])
        vw["v_net_dep"]        = st.slider("Net deposits (committed capital)",             0, 15, vw["v_net_dep"])
        vw["v_current_equity"] = st.slider("Current equity (capital at risk if churns)",  0, 15, vw["v_current_equity"])
    with c2:
        vw["v_volume"]         = st.slider("Trading volume 30d (active revenue generator)", 0, 15, vw["v_volume"])
        vw["v_redeposits"]     = st.slider("Redeposit count (loyalty indicator)",          0, 15, vw["v_redeposits"])
        vw["v_tenure"]         = st.slider("Client tenure (long-term commitment)",         0, 15, vw["v_tenure"])

    if st.button("Apply Value Weights", type="primary", key="apply_val"):
        st.session_state["value_weights"] = vw
        rescore()
        st.success("Value weights updated.")

# ── Reactivation weights ──────────────────────────────────────────────────────
with tab_react:
    st.markdown(f"<h4 style='color:{GOLD}'>Reactivation Weights</h4>",
                unsafe_allow_html=True)
    st.caption(
        "Controls which dormant or inactive clients rank highest for win-back campaigns. "
        "The sweet spot is clients who were previously engaged (not brand new, not permanently lost) "
        "and had strong enough financials to be worth re-engaging."
    )
    rw2 = st.session_state["react_weights"].copy()
    c1, c2 = st.columns(2)
    with c1:
        rw2["r_login_window"]  = st.slider("Login recency window (30–180d)", 0, 10, rw2["r_login_window"])
        rw2["r_lifetime_dep"]  = st.slider("Historical deposits",            0, 10, rw2["r_lifetime_dep"])
        rw2["r_volume_hist"]   = st.slider("Historical volume (90d)",        0, 10, rw2["r_volume_hist"])
    with c2:
        rw2["r_redeposits"]    = st.slider("Past redeposit loyalty",         0, 10, rw2["r_redeposits"])
        rw2["r_tenure"]        = st.slider("Client tenure",                  0, 10, rw2["r_tenure"])

    if st.button("Apply Reactivation Weights", type="primary", key="apply_react"):
        st.session_state["react_weights"] = rw2
        rescore()
        st.success("Reactivation weights updated.")

# ── Upside Potential weights ──────────────────────────────────────────────────
with tab_upside:
    st.markdown(f"<h4 style='color:{GOLD}'>Upside Potential Weights</h4>",
                unsafe_allow_html=True)
    st.caption(
        "Controls which clients rank highest for growth and upsell opportunities. "
        "Upside is based entirely on financial behaviour — equity size, deposit commitment, "
        "volume growth, loyalty, and tenure. No account type classification is used."
    )
    uw = st.session_state["upside_weights"].copy()
    c1, c2 = st.columns(2)
    with c1:
        uw["u_equity"]       = st.slider("Current equity size (capital base)", 0, 15, uw["u_equity"])
        uw["u_net_dep"]      = st.slider("Net deposits (committed capital)",   0, 15, uw["u_net_dep"])
        uw["u_volume_trend"] = st.slider("Positive volume trend (growing trader)", 0, 15, uw["u_volume_trend"])
    with c2:
        uw["u_redeposits"]   = st.slider("Redeposit loyalty (repeat depositor)", 0, 15, uw["u_redeposits"])
        uw["u_tenure"]       = st.slider("Client tenure (long-term relationship)", 0, 15, uw["u_tenure"])

    if st.button("Apply Upside Potential Weights", type="primary", key="apply_upside"):
        st.session_state["upside_weights"] = uw
        rescore()
        st.success("Upside Potential weights updated.")

# ── Score distributions ───────────────────────────────────────────────────────
with tab_dist:
    st.markdown(f"<h4 style='color:{GOLD}'>All 6 Score Distributions</h4>",
                unsafe_allow_html=True)

    scores = [
        ("retention_risk_score",   "Retention Risk",     RED),
        ("commercial_value_score", "Commercial Value",   BLUE),
        ("profitability_score",    "Profitability",      GREEN),
        ("reactivation_score",     "Reactivation",       AMBER),
        ("upside_potential_score", "Upside Potential",   PURPLE),
        ("client_health_score",    "Client Health",      GOLD),
    ]

    for i in range(0, 6, 2):
        c1, c2 = st.columns(2)
        for col, (col_name, label, color) in zip([c1, c2], scores[i:i+2]):
            fig = px.histogram(df, x=col_name, nbins=20,
                               color_discrete_sequence=[color],
                               title=f"{label} Distribution",
                               labels={col_name: label})
            fig.update_layout(**get_plotly_layout(), height=240, showlegend=False)
            col.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.markdown(f"<h4 style='color:{GOLD}'>Risk vs Profitability (by Book Type)</h4>",
                unsafe_allow_html=True)

    sample = df.sample(min(200, len(df)), random_state=1)
    book_colors = {"A-Book": BLUE, "B-Book": RED, "M-Book": PURPLE}
    fig_sc = px.scatter(
        sample,
        x="profitability_score",
        y="retention_risk_score",
        color="book_type",
        color_discrete_map=book_colors,
        size="current_equity",
        hover_data=["client_name", "country", "recommended_action"],
        labels={
            "profitability_score":  "Profitability Score →",
            "retention_risk_score": "↑ Retention Risk Score",
            "book_type": "Book Type",
        },
        title="Top-right = high-risk but profitable clients (protect immediately)",
        height=500,
    )
    fig_sc.add_hline(y=t["high_risk"], line_dash="dash", line_color=GOLD,
                     annotation_text=f"High Risk ({t['high_risk']})",
                     annotation_font_color=GOLD)
    fig_sc.add_vline(x=t["high_profitability"], line_dash="dash", line_color=GREEN,
                     annotation_text=f"High Profit ({t['high_profitability']})",
                     annotation_font_color=GREEN)
    fig_sc.update_layout(**get_plotly_layout())
    st.plotly_chart(fig_sc, use_container_width=True)
