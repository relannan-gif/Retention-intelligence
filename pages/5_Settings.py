# pages/5_Settings.py  —  Threshold configuration and impact preview

import streamlit as st

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")

from utils.helpers import (
    apply_theme, load_data, rescore, page_header, fmt_currency,
    DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS, DEFAULT_PROF_WEIGHTS,
    DEFAULT_REACT_WEIGHTS, DEFAULT_UPSIDE_WEIGHTS, DEFAULT_THRESHOLDS,
    GOLD, RED, GREEN, AMBER, BLUE,
)
from utils.session_init import init_session_state

apply_theme()
init_session_state()
page_header("⚙️ Settings", "Configure scoring thresholds · save changes · preview impact")

t = st.session_state.get("thresholds", DEFAULT_THRESHOLDS.copy()).copy()

# ── Appearance ─────────────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Appearance</h4>", unsafe_allow_html=True)
_theme_options = {"OneRoyal Dark": "dark", "OneRoyal Light": "light"}
_current_theme_name = {v: k for k, v in _theme_options.items()}.get(
    st.session_state.get("theme", "dark"), "OneRoyal Dark"
)
_selected_name = st.radio(
    "Select Theme",
    list(_theme_options.keys()),
    index=list(_theme_options.keys()).index(_current_theme_name),
    horizontal=True,
    key="theme_selector",
)
_new_theme = _theme_options[_selected_name]
if _new_theme != st.session_state.get("theme", "dark"):
    st.session_state["theme"] = _new_theme
    st.rerun()

st.caption("Theme changes apply immediately across all pages.")

st.divider()

# ── Scoring thresholds ────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Scoring Thresholds</h4>", unsafe_allow_html=True)
st.caption(
    "Thresholds convert continuous 0–100 scores into actionable labels. "
    "All scores are min-max normalised across the current client portfolio — "
    "a score of 60 means the client is in the top 40% of the portfolio for that dimension. "
    "Raise a threshold to focus only on the most extreme cases; lower it to cast a wider net."
)

tc1, tc2, tc3, tc4 = st.columns(4)
with tc1:
    t["high_risk"] = st.slider(
        "High Risk threshold", 10, 95, int(t["high_risk"]),
        help=(
            "Clients above this threshold are labelled 'High Risk' and appear in the Action Center. "
            "Default: 60. At this level, roughly the top 40% of the portfolio by risk score are flagged. "
            "Raise to 70–75 if the action queue is too large for your team to handle."
        ))
with tc2:
    t["high_value"] = st.slider(
        "High Value threshold", 10, 95, int(t["high_value"]),
        help=(
            "Clients above this threshold are labelled 'High Value' and receive priority actions. "
            "Default: 60. Commercial value is based on lifetime deposits, equity, volume, and tenure. "
            "Lowering this threshold expands the protected portfolio; raising it tightens focus on top clients."
        ))
with tc3:
    t["high_profitability"] = st.slider(
        "High Profitability threshold", 10, 95, int(t.get("high_profitability", 60)),
        help=(
            "Clients above this threshold are treated as high-profitability for action prioritisation. "
            "Profitability is book-type aware: A-Book uses fees only; B/M-Book uses captured losses + fees. "
            "Default: 60. These clients are sorted to the top of the Action Center."
        ))
with tc4:
    t["critical_priority"] = st.slider(
        "Critical Priority threshold", 10, 95, int(t["critical_priority"]),
        help=(
            "Clients above this Priority Score threshold are labelled 'Critical Priority'. "
            "Priority = Risk×35% + Value×25% + Profitability×35% + Upside×5%. "
            "Default: 65. These clients should receive same-day intervention."
        ))

st.divider()

# ── Activity thresholds ────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Activity Thresholds</h4>", unsafe_allow_html=True)
st.caption(
    "Activity thresholds define the boundary conditions used in the risk scoring bands and action rules. "
    "These complement the scoring weights — the bands in the Business Rules Engine use absolute thresholds, "
    "while these settings drive the action logic and labelling."
)

ac1, ac2, ac3 = st.columns(3)
with ac1:
    t["login_inactivity_days"] = st.slider(
        "Login inactivity (days)", 7, 180, int(t["login_inactivity_days"]),
        help=(
            "Clients who haven't logged in for this many days or more are flagged as inactive in action rules. "
            "Default: 30 days. This also controls the Reactivation Score — "
            "the sweet spot for reactivation is clients inactive 30–180 days."
        ))
with ac2:
    t["large_withdrawal_pct"] = st.slider(
        "Large withdrawal % of equity", 0.05, 0.80,
        float(t["large_withdrawal_pct"]), step=0.05, format="%.0f%%",
        help=(
            "A withdrawal exceeding this percentage of current equity triggers a 'Withdrawal Alert' action. "
            "Default: 30%. Set lower (e.g. 20%) for high-value clients where smaller withdrawals matter. "
            "The scoring engine always measures withdrawal pressure as a continuous % — this threshold "
            "is used only in the action rule tree."
        ))
with ac3:
    t["dormant_days"] = st.slider(
        "Dormant client threshold (days)", 7, 90, int(t.get("dormant_days", 30)),
        help=(
            "Clients with no login for this many days are classified as 'Dormant' in the account_status field. "
            "Default: 30 days. Dormant clients with a high Reactivation Score are escalated to the "
            "'Reactivation Call' action in the Action Center."
        ))

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
            ("thresholds",     DEFAULT_THRESHOLDS),
            ("risk_weights",   DEFAULT_RISK_WEIGHTS),
            ("value_weights",  DEFAULT_VALUE_WEIGHTS),
            ("prof_weights",   DEFAULT_PROF_WEIGHTS),
            ("react_weights",  DEFAULT_REACT_WEIGHTS),
            ("upside_weights", DEFAULT_UPSIDE_WEIGHTS),
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

st.divider()

# ── Business Rules Engine ──────────────────────────────────────────────────────
import copy
from utils.rules_engine import load_rules, save_rules

st.markdown(f"<h4 style='color:{GOLD}'>Business Rules Engine — Scoring Bands</h4>",
            unsafe_allow_html=True)
st.caption(
    "Each factor is scored by matching the client's value against tiered bands. "
    "Edit the **Points** column (0–100) to change how much weight each band carries. "
    "Higher points = stronger signal. Click **Save Rules & Rescore** to apply."
)

if "scoring_rules" not in st.session_state:
    st.session_state["scoring_rules"] = load_rules()

_current_rules = st.session_state["scoring_rules"]
_edited = copy.deepcopy(_current_rules)


def _band_editor(section: str, factor_key: str, bands: list) -> list:
    hc1, hc2 = st.columns([4, 1])
    hc1.markdown("<small style='color:#94A3B8'>Band Condition</small>",
                 unsafe_allow_html=True)
    hc2.markdown("<small style='color:#94A3B8'>Points</small>",
                 unsafe_allow_html=True)
    updated = []
    for i, band in enumerate(bands):
        c1, c2 = st.columns([4, 1])
        c1.markdown(
            f"<span style='color:#E8E8E8'>&nbsp;&nbsp;{band['label']}</span>",
            unsafe_allow_html=True,
        )
        pts = c2.number_input(
            "Points",
            min_value=0,
            max_value=100,
            value=int(band["points"]),
            key=f"band_{section}_{factor_key}_{i}",
            label_visibility="collapsed",
        )
        b = dict(band)
        b["points"] = int(pts)
        updated.append(b)
    return updated


tab_rr, tab_cv, tab_prof = st.tabs([
    "Retention Risk Factors",
    "Commercial Value Factors",
    "Profitability Bands",
])

with tab_rr:
    st.caption("These bands drive the **Retention Risk Score**. "
               "Higher points = client is flagged as more at risk of leaving.")
    for fkey, fdata in _edited["retention_risk"].items():
        with st.expander(
            f"**{fdata['label']}** · _{fdata['description']}_",
            expanded=False,
        ):
            _edited["retention_risk"][fkey]["bands"] = _band_editor(
                "rr", fkey, fdata["bands"]
            )

with tab_cv:
    st.caption("These bands drive the **Commercial Value Score**. "
               "Higher points = client is considered more commercially important.")
    for fkey, fdata in _edited["commercial_value"].items():
        with st.expander(
            f"**{fdata['label']}** · _{fdata['description']}_",
            expanded=False,
        ):
            _edited["commercial_value"][fkey]["bands"] = _band_editor(
                "cv", fkey, fdata["bands"]
            )

with tab_prof:
    st.caption(
        "These bands drive the **Profitability Score**, separated by book type. "
        "Each book type has its own dollar thresholds because A-Book profits are "
        "purely revenue-based while B-Book profits include captured client losses."
    )
    st.markdown(f"<h5 style='color:{GOLD}'>M-Book Configuration</h5>",
                unsafe_allow_html=True)
    _edited["profitability"]["m_book"]["internal_ratio"] = st.slider(
        "M-Book internal ratio — fraction of client losses held internally (B-Book style)",
        min_value=0.10,
        max_value=1.00,
        value=float(_current_rules["profitability"]["m_book"].get("internal_ratio", 0.6)),
        step=0.05,
        key="m_book_ratio",
        help="1.0 = fully B-Book (all losses held); 0.0 = fully A-Book (all hedged externally)",
    )
    st.divider()
    for bkey in ["a_book", "b_book", "m_book"]:
        bdata = _edited["profitability"][bkey]
        formula = bdata.get("formula_label", "")
        with st.expander(
            f"**{bdata['label']}** · `{formula}`",
            expanded=False,
        ):
            _edited["profitability"][bkey]["bands"] = _band_editor(
                "prof", bkey, bdata["bands"]
            )

st.divider()
sr1, sr2 = st.columns([2, 1])
with sr1:
    if st.button("Save Scoring Rules & Rescore All Clients",
                 type="primary", key="save_scoring_rules"):
        st.session_state["scoring_rules"] = _edited
        save_rules(_edited)
        rescore()
        st.success(
            "Scoring rules saved to `config/scoring_rules.json`. "
            "All 300 clients have been rescored using the new bands."
        )
        st.rerun()
with sr2:
    if st.button("Reload Rules from File", key="reset_rules"):
        st.session_state["scoring_rules"] = load_rules()
        rescore()
        st.success("Scoring rules reloaded from `config/scoring_rules.json`.")
        st.rerun()
