# pages/5_Settings.py  —  Threshold configuration and impact preview

import streamlit as st

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

from utils.helpers import (
    apply_theme, load_data, rescore, page_header, fmt_currency,
    DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS, DEFAULT_PROF_WEIGHTS,
    DEFAULT_REACT_WEIGHTS, DEFAULT_VIP_WEIGHTS, DEFAULT_THRESHOLDS,
    GOLD, RED, GREEN, AMBER, BLUE,
)

apply_theme()
page_header("⚙️ Settings", "Configure scoring thresholds · save changes · preview impact")

t = st.session_state.get("thresholds", DEFAULT_THRESHOLDS.copy()).copy()

# ── Scoring thresholds ────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Scoring Thresholds</h4>", unsafe_allow_html=True)
st.caption("These determine when a client is labelled High Risk, High Value, High Profitability, or Critical Priority.")

tc1, tc2, tc3, tc4 = st.columns(4)
with tc1:
    t["high_risk"] = st.slider(
        "High Risk threshold", 10, 95, int(t["high_risk"]),
        help="Clients with risk score above this are labelled 'High Risk'.")
with tc2:
    t["high_value"] = st.slider(
        "High Value threshold", 10, 95, int(t["high_value"]),
        help="Clients with value score above this are labelled 'High Value'.")
with tc3:
    t["high_profitability"] = st.slider(
        "High Profitability threshold", 10, 95, int(t.get("high_profitability", 60)),
        help="Clients with profitability score above this trigger higher-priority actions.")
with tc4:
    t["critical_priority"] = st.slider(
        "Critical Priority threshold", 10, 95, int(t["critical_priority"]),
        help="Clients with priority score above this are labelled 'Critical'.")

st.divider()

# ── Activity thresholds ────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Activity Thresholds</h4>", unsafe_allow_html=True)

ac1, ac2, ac3 = st.columns(3)
with ac1:
    t["login_inactivity_days"] = st.slider(
        "Login inactivity (days)", 7, 180, int(t["login_inactivity_days"]),
        help="Client is considered inactive if no login for this many days.")
with ac2:
    t["large_withdrawal_pct"] = st.slider(
        "Large withdrawal % of equity", 0.05, 0.80,
        float(t["large_withdrawal_pct"]), step=0.05, format="%.0f%%",
        help="A withdrawal exceeding this % of equity triggers a withdrawal alert action.")
with ac3:
    t["dormant_days"] = st.slider(
        "Dormant client threshold (days)", 7, 90, int(t.get("dormant_days", 30)),
        help="Clients who haven't logged in for longer than this are marked Dormant.")

st.divider()

# ── Save / Reset ──────────────────────────────────────────────────────────────
sc1, sc2 = st.columns([1, 1])
with sc1:
    if st.button("Save Settings & Rescore All Clients", type="primary"):
        st.session_state["thresholds"] = t
        rescore()
        st.success("Settings saved. All 300 clients have been rescored.")
with sc2:
    if st.button("Reset All Settings to Defaults"):
        for key, val in [
            ("thresholds",    DEFAULT_THRESHOLDS),
            ("risk_weights",  DEFAULT_RISK_WEIGHTS),
            ("value_weights", DEFAULT_VALUE_WEIGHTS),
            ("prof_weights",  DEFAULT_PROF_WEIGHTS),
            ("react_weights", DEFAULT_REACT_WEIGHTS),
            ("vip_weights",   DEFAULT_VIP_WEIGHTS),
        ]:
            st.session_state[key] = val.copy()
        rescore()
        st.success("All settings and weights reset to defaults.")
        st.rerun()

st.divider()

# ── Impact preview ─────────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Impact of Current Thresholds</h4>",
            unsafe_allow_html=True)
df = load_data()

hr = st.session_state["thresholds"]["high_risk"]
hv = st.session_state["thresholds"]["high_value"]
hp = st.session_state["thresholds"].get("high_profitability", 60)
cp = st.session_state["thresholds"]["critical_priority"]

i1, i2, i3, i4, i5 = st.columns(5)
i1.metric("High Risk Clients",
          int((df["retention_risk_score"] >= hr).sum()),
          f"{(df['retention_risk_score'] >= hr).mean():.0%} of portfolio")
i2.metric("High Value Clients",
          int((df["commercial_value_score"] >= hv).sum()),
          f"{(df['commercial_value_score'] >= hv).mean():.0%} of portfolio")
i3.metric("High Profitability",
          int((df["profitability_score"] >= hp).sum()),
          f"{(df['profitability_score'] >= hp).mean():.0%} of portfolio")
i4.metric("Critical Priority",
          int((df["priority_score"] >= cp).sum()),
          f"{(df['priority_score'] >= cp).mean():.0%} of portfolio")
i5.metric("High-Value At Risk",
          int(((df["retention_risk_score"] >= hr) &
               (df["commercial_value_score"] >= hv)).sum()))

st.info(
    "Tip: if too many clients are 'High Risk', raise the threshold. "
    "The goal is to focus your retention team on the clients where intervention matters most."
)

st.divider()

# ── Current config summary ─────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Current Configuration</h4>", unsafe_allow_html=True)

col_t, col_rw, col_vw = st.columns(3)
with col_t:
    st.markdown("**Thresholds**")
    cfg = st.session_state.get("thresholds", DEFAULT_THRESHOLDS)
    st.write({
        "High Risk":          cfg["high_risk"],
        "High Value":         cfg["high_value"],
        "High Profitability": cfg.get("high_profitability", 60),
        "Critical Priority":  cfg["critical_priority"],
        "Login Inactivity":   f"{cfg['login_inactivity_days']}d",
        "Large Withdrawal":   f"{int(cfg['large_withdrawal_pct']*100)}% of equity",
        "Dormant Threshold":  f"{cfg.get('dormant_days',30)}d",
    })
with col_rw:
    st.markdown("**Risk Weights**")
    st.write(st.session_state.get("risk_weights", DEFAULT_RISK_WEIGHTS))
with col_vw:
    st.markdown("**Value Weights**")
    st.write(st.session_state.get("value_weights", DEFAULT_VALUE_WEIGHTS))
