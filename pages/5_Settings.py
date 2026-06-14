# pages/5_Settings.py
# Settings page — adjust thresholds that drive risk/value tier labels
# and the recommended action rules.

import streamlit as st
from utils.helpers import (
    load_data, rescore, page_header,
    DEFAULT_THRESHOLDS, DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS,
)

st.set_page_config(page_title="Settings", page_icon="🔧", layout="wide")

page_header("🔧 Settings", "Configure thresholds and platform behaviour")

thresholds = st.session_state.get("thresholds", DEFAULT_THRESHOLDS.copy()).copy()

# ── Risk / Value / Priority thresholds ────────────────────────────────────────
st.markdown("### Scoring Thresholds")
st.caption("These thresholds determine when a client is labelled High Risk, High Value, or Critical Priority.")

t1, t2, t3 = st.columns(3)

with t1:
    thresholds["high_risk"] = st.slider(
        "High Risk threshold",
        min_value=10, max_value=95,
        value=int(thresholds["high_risk"]),
        help="Clients with a risk score above this are labelled 'High Risk'."
    )

with t2:
    thresholds["high_value"] = st.slider(
        "High Value threshold",
        min_value=10, max_value=95,
        value=int(thresholds["high_value"]),
        help="Clients with a value score above this are labelled 'High Value'."
    )

with t3:
    thresholds["critical_priority"] = st.slider(
        "Critical Priority threshold",
        min_value=10, max_value=95,
        value=int(thresholds["critical_priority"]),
        help="Clients with a priority score above this are 'Critical'."
    )

st.divider()

# ── Activity thresholds ────────────────────────────────────────────────────────
st.markdown("### Activity Thresholds")
st.caption("These affect how the platform interprets login and deposit inactivity.")

a1, a2 = st.columns(2)

with a1:
    thresholds["login_inactivity_days"] = st.slider(
        "Login inactivity threshold (days)",
        min_value=7, max_value=180,
        value=int(thresholds["login_inactivity_days"]),
        help="A client is considered inactive if they haven't logged in for this many days."
    )

with a2:
    thresholds["large_withdrawal_pct"] = st.slider(
        "Large withdrawal % of equity",
        min_value=0.05, max_value=0.80,
        value=float(thresholds["large_withdrawal_pct"]),
        step=0.05,
        format="%.0f%%",
        help="A withdrawal is 'large' when it exceeds this % of current equity."
    )

st.divider()

# ── Apply / Reset ──────────────────────────────────────────────────────────────
col_apply, col_reset = st.columns([1, 1])

with col_apply:
    if st.button("✅ Save settings and rescore", type="primary"):
        st.session_state["thresholds"] = thresholds
        rescore()
        st.success("Settings saved and all scores recalculated.")

with col_reset:
    if st.button("🔄 Reset to defaults"):
        st.session_state["thresholds"]    = DEFAULT_THRESHOLDS.copy()
        st.session_state["risk_weights"]  = DEFAULT_RISK_WEIGHTS.copy()
        st.session_state["value_weights"] = DEFAULT_VALUE_WEIGHTS.copy()
        st.session_state["risk_blend"]    = 0.6
        rescore()
        st.success("All settings reset to defaults.")
        st.rerun()

st.divider()

# ── Current settings summary ───────────────────────────────────────────────────
st.markdown("### Current Configuration Summary")

with st.expander("View all current settings"):
    st.markdown("#### Thresholds")
    st.json(st.session_state.get("thresholds", DEFAULT_THRESHOLDS))

    st.markdown("#### Retention Risk Weights")
    st.json(st.session_state.get("risk_weights", DEFAULT_RISK_WEIGHTS))

    st.markdown("#### Client Value Weights")
    st.json(st.session_state.get("value_weights", DEFAULT_VALUE_WEIGHTS))

    st.markdown("#### Priority Score Blend")
    blend = st.session_state.get("risk_blend", 0.6)
    st.write(f"Risk weight: **{blend:.0%}** | Value weight: **{1-blend:.0%}**")

# ── Impact preview ─────────────────────────────────────────────────────────────
st.divider()
st.markdown("### Impact of Current Thresholds")
df = load_data()

high_risk_t = st.session_state["thresholds"]["high_risk"]
high_val_t  = st.session_state["thresholds"]["high_value"]
crit_prio_t = st.session_state["thresholds"]["critical_priority"]

i1, i2, i3, i4 = st.columns(4)
i1.metric("High Risk Clients",
          int((df["retention_risk_score"] >= high_risk_t).sum()),
          f"{(df['retention_risk_score'] >= high_risk_t).mean():.0%} of total")
i2.metric("High Value Clients",
          int((df["client_value_score"] >= high_val_t).sum()),
          f"{(df['client_value_score'] >= high_val_t).mean():.0%} of total")
i3.metric("Critical Priority",
          int((df["priority_score"] >= crit_prio_t).sum()),
          f"{(df['priority_score'] >= crit_prio_t).mean():.0%} of total")
i4.metric("High-Value at Risk",
          int(((df["retention_risk_score"] >= high_risk_t) &
               (df["client_value_score"]   >= high_val_t)).sum()))

st.info(
    "Tip: if High Risk count is too high, raise the threshold. "
    "If too low, lower it. The goal is to focus your team on the most important clients."
)
