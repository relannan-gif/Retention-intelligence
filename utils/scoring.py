# utils/scoring.py — OneRoyal Client Intelligence Platform v2.0
# VIP concept removed. Upside Potential replaces VIP Upside.
# Priority Score recalibrated: Risk 35% / Value 25% / Profitability 35% / Upside 5%.

import pandas as pd
import numpy as np
from utils import rules_engine as _re


def _normalize(series: pd.Series) -> pd.Series:
    """Stretch any numeric series to exactly 0–100 using min-max normalization."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - mn) / (mx - mn)) * 100


# ─────────────────────────────────────────────────────────────────────────────
# 1. RETENTION RISK SCORE
# ─────────────────────────────────────────────────────────────────────────────

def compute_retention_risk(df: pd.DataFrame, weights: dict) -> pd.Series:
    """
    Probability of churn. Higher = more likely to leave.
    Seven weighted signals, all normalized 0-100, then combined and re-normalized.
    """
    wr = df["withdrawal_amount_last_30d"] / df["current_equity"].clip(lower=1)
    f_withdrawal = _normalize(wr)

    vdrop = (df["trading_volume_previous_30d"] - df["trading_volume_last_30d"]) \
            / df["trading_volume_previous_30d"].clip(lower=1)
    f_vol_drop = _normalize(vdrop.clip(lower=0))

    f_login    = _normalize(df["login_days_ago"])
    f_deposit  = _normalize(df["last_deposit_days_ago"])
    f_complaints = _normalize(df["complaints_last_30d"] + df["open_tickets"])

    erosion = 1 - df["current_equity"] / df["net_deposits"].clip(lower=1)
    f_equity_erosion = _normalize(erosion.clip(lower=0))

    trend_drop = (df["equity_30d_ago"] - df["current_equity"]) \
                 / df["equity_30d_ago"].clip(lower=1)
    f_equity_trend = _normalize(trend_drop.clip(lower=0))

    w = weights
    total = (w["w_withdrawal"] + w["w_volume_drop"] + w["w_login"] +
             w["w_deposit_stale"] + w["w_complaints"] +
             w["w_equity_erosion"] + w["w_equity_trend"]) or 1

    raw = (
        f_withdrawal      * w["w_withdrawal"] +
        f_vol_drop        * w["w_volume_drop"] +
        f_login           * w["w_login"] +
        f_deposit         * w["w_deposit_stale"] +
        f_complaints      * w["w_complaints"] +
        f_equity_erosion  * w["w_equity_erosion"] +
        f_equity_trend    * w["w_equity_trend"]
    ) / total

    return _normalize(raw).round(1)


# ─────────────────────────────────────────────────────────────────────────────
# 2. COMMERCIAL VALUE SCORE
# ─────────────────────────────────────────────────────────────────────────────

def compute_commercial_value(df: pd.DataFrame, weights: dict) -> pd.Series:
    """
    Commercial importance of the client to OneRoyal.
    Answers: "How much does it cost us if this client leaves?"
    No VIP status factor — commercial value is based solely on financial behaviour.
    """
    f_lifetime   = _normalize(df["lifetime_deposits"])
    f_net_dep    = _normalize(df["net_deposits"])
    f_equity     = _normalize(df["current_equity"])
    f_volume     = _normalize(df["trading_volume_last_30d"])
    f_redeposits = _normalize(df["number_of_redeposits"])
    f_tenure     = _normalize(df["client_tenure_days"])

    w = weights
    total = (w["v_lifetime_dep"] + w["v_net_dep"] + w["v_current_equity"] +
             w["v_volume"] + w["v_redeposits"] + w["v_tenure"]) or 1

    raw = (
        f_lifetime   * w["v_lifetime_dep"] +
        f_net_dep    * w["v_net_dep"] +
        f_equity     * w["v_current_equity"] +
        f_volume     * w["v_volume"] +
        f_redeposits * w["v_redeposits"] +
        f_tenure     * w["v_tenure"]
    ) / total

    return _normalize(raw).round(1)


# ─────────────────────────────────────────────────────────────────────────────
# 3. PROFITABILITY SCORE  (book-type aware)
# ─────────────────────────────────────────────────────────────────────────────

def compute_profitability(df: pd.DataFrame) -> pd.Series:
    """
    Actual profitability to OneRoyal, calculated per book type.

    A-Book:  commission + swap + spread_commission_revenue
             (hedged exposure; earns fees only)
    B-Book:  captured_client_losses + commission + swap
             (positions held internally; losses ARE the profit; NO spread)
    M-Book:  internal_ratio × captured_client_losses + commission + swap
             (partial internal holding; NO spread in P&L)

    A single 'profitability_amount' series is computed and then normalized
    to 0-100 across all clients regardless of book type.
    """
    amounts = pd.Series(0.0, index=df.index)

    a_mask = df["book_type"] == "A-Book"
    b_mask = df["book_type"] == "B-Book"
    m_mask = df["book_type"] == "M-Book"

    amounts[a_mask] = (
        df.loc[a_mask, "commission_revenue"] +
        df.loc[a_mask, "swap_revenue"] +
        df.loc[a_mask, "spread_commission_revenue"]
    )
    amounts[b_mask] = (
        df.loc[b_mask, "captured_client_losses"] +
        df.loc[b_mask, "commission_revenue"] +
        df.loc[b_mask, "swap_revenue"]
    )
    amounts[m_mask] = (
        0.6 * df.loc[m_mask, "captured_client_losses"] +
        df.loc[m_mask, "commission_revenue"] +
        df.loc[m_mask, "swap_revenue"]
    )

    return _normalize(amounts).round(1)


# ─────────────────────────────────────────────────────────────────────────────
# 4. REACTIVATION SCORE
# ─────────────────────────────────────────────────────────────────────────────

def compute_reactivation(df: pd.DataFrame, weights: dict) -> pd.Series:
    """
    Likelihood of successful reactivation for dormant clients.
    High score = was a good client who went quiet → worth calling.
    The 'login window' factor peaks for clients who logged in 30-180 days ago.
    """
    login = df["login_days_ago"].clip(0, 365)
    window_score = np.where(
        (login >= 30) & (login <= 180),
        100 - ((login - 105).abs() / 75) * 100,
        np.where(login < 30, login / 30 * 50, np.maximum(0, 100 - (login - 180) / 1.85))
    )
    f_login_window = pd.Series(window_score, index=df.index).clip(0, 100)

    f_lifetime   = _normalize(df["lifetime_deposits"])
    f_redeposits = _normalize(df["number_of_redeposits"])
    f_vol_hist   = _normalize(df["volume_90d_ago"])
    f_tenure     = _normalize(df["client_tenure_days"])

    w = weights
    total = (w["r_login_window"] + w["r_lifetime_dep"] + w["r_redeposits"] +
             w["r_volume_hist"] + w["r_tenure"]) or 1

    raw = (
        f_login_window * w["r_login_window"] +
        f_lifetime     * w["r_lifetime_dep"] +
        f_redeposits   * w["r_redeposits"] +
        f_vol_hist     * w["r_volume_hist"] +
        f_tenure       * w["r_tenure"]
    ) / total

    return _normalize(raw).round(1)


# ─────────────────────────────────────────────────────────────────────────────
# 5. UPSIDE POTENTIAL SCORE  (formerly VIP Upside — VIP concept removed)
# ─────────────────────────────────────────────────────────────────────────────

def compute_upside_potential(df: pd.DataFrame, weights: dict) -> pd.Series:
    """
    Growth and commercial expansion potential.
    High score = client showing strong financial growth trajectory.
    Identifies clients most likely to grow in value — equity growth,
    deposit growth, volume growth, loyalty, and long tenure.
    No VIP status dependency — based solely on financial behaviour.
    """
    f_equity   = _normalize(df["current_equity"])
    f_net_dep  = _normalize(df["net_deposits"])

    vol_trend  = (df["trading_volume_last_30d"] - df["volume_90d_ago"]) \
                 / df["volume_90d_ago"].clip(lower=1)
    f_vol_trend = _normalize(vol_trend.clip(lower=-1, upper=5))

    f_redeposits = _normalize(df["number_of_redeposits"])
    f_tenure     = _normalize(df["client_tenure_days"])

    w = weights
    total = (w["u_equity"] + w["u_net_dep"] + w["u_volume_trend"] +
             w["u_redeposits"] + w["u_tenure"]) or 1

    raw = (
        f_equity      * w["u_equity"] +
        f_net_dep     * w["u_net_dep"] +
        f_vol_trend   * w["u_volume_trend"] +
        f_redeposits  * w["u_redeposits"] +
        f_tenure      * w["u_tenure"]
    ) / total

    return _normalize(raw).round(1)


# ─────────────────────────────────────────────────────────────────────────────
# 6. CLIENT HEALTH SCORE
# ─────────────────────────────────────────────────────────────────────────────

def compute_client_health(risk: pd.Series, value: pd.Series,
                          profitability: pd.Series) -> pd.Series:
    """
    Positive management metric. 100 = excellent, 0 = critical.
    High risk always degrades health. Value and profitability contribute positively.
    Formula: (100 − risk) × 50% + value × 30% + profitability × 20%
    """
    raw = (100 - risk) * 0.5 + value * 0.3 + profitability * 0.2
    return _normalize(raw).round(1)


def health_label(score: float) -> str:
    if score >= 80:  return "Excellent"
    if score >= 60:  return "Healthy"
    if score >= 40:  return "Watchlist"
    if score >= 20:  return "At Risk"
    return "Critical"


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY SCORE
# ─────────────────────────────────────────────────────────────────────────────

def compute_priority(risk: pd.Series, value: pd.Series,
                     profitability: pd.Series, upside: pd.Series) -> pd.Series:
    """
    "If this client leaves tomorrow, how much economic damage does OneRoyal suffer?"
    Risk 35% + Profitability 35% + Value 25% + Upside Potential 5%.
    Risk and profitability are equally dominant — a client must be BOTH at risk
    AND profitable to reach the top of the Action Center queue.
    """
    raw = (risk * 0.35 + value * 0.25 + profitability * 0.35 + upside * 0.05)
    return _normalize(raw).round(1)


# ─────────────────────────────────────────────────────────────────────────────
# SEGMENTATION MATRIX  (3 × 3)
# ─────────────────────────────────────────────────────────────────────────────

SEGMENT_MATRIX = {
    ("High",   "High"):   "Save Immediately",
    ("High",   "Medium"): "Senior Retention Review",
    ("High",   "Low"):    "Automated Retention",
    ("Medium", "High"):   "Proactive Nurture",
    ("Medium", "Medium"): "Standard Nurture",
    ("Medium", "Low"):    "Light Touch",
    ("Low",    "High"):   "High Value Growth",
    ("Low",    "Medium"): "Growth Program",
    ("Low",    "Low"):    "Monitor",
}


def _tier(score: float, high_t: float, low_t: float) -> str:
    if score >= high_t: return "High"
    if score >= low_t:  return "Medium"
    return "Low"


def assign_segment(row: pd.Series, thresholds: dict) -> str:
    risk_tier  = _tier(row["retention_risk_score"],
                       thresholds["high_risk"], thresholds["high_risk"] * 0.5)
    value_tier = _tier(row["commercial_value_score"],
                       thresholds["high_value"], thresholds["high_value"] * 0.5)
    return SEGMENT_MATRIX.get((risk_tier, value_tier), "Monitor")


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDED ACTION  (9-rule decision tree — VIP rules removed)
# ─────────────────────────────────────────────────────────────────────────────

def assign_recommended_action(row: pd.Series, thresholds: dict) -> tuple:
    """Returns (action_label, reason_string). First matching rule wins."""
    risk   = row["retention_risk_score"]
    value  = row["commercial_value_score"]
    prof   = row["profitability_score"]
    react  = row["reactivation_score"]
    upside = row["upside_potential_score"]

    hr = thresholds["high_risk"]
    hv = thresholds["high_value"]
    hp = thresholds.get("high_profitability", 60)

    complaints   = row["complaints_last_30d"] + row["open_tickets"]
    wd_pct       = row["withdrawal_amount_last_30d"] / max(row["current_equity"], 1)
    vol_dropped  = row["trading_volume_last_30d"] < row["trading_volume_previous_30d"] * 0.5
    status       = row["account_status"]
    large_wd_pct = thresholds.get("large_withdrawal_pct", 0.30)

    # Rule 1: High risk + high value + high profitability → immediate call
    if risk >= hr and value >= hv and prof >= hp:
        return ("Immediate Retention Call",
                f"Risk {risk:.0f} · Value {value:.0f} · Profit {prof:.0f} — protect revenue now")

    # Rule 2: Complaints with high risk
    if complaints >= 2 and risk >= hr:
        return ("Resolve Complaints + Retention Review",
                f"{complaints} complaints/tickets · Risk {risk:.0f} — service failure")

    # Rule 3: Large withdrawal + high risk
    if wd_pct >= large_wd_pct and risk >= hr:
        return ("Retention Call: Withdrawal Alert",
                f"Withdrew {wd_pct:.0%} of equity · Risk {risk:.0f}")

    # Rule 4: High risk (general)
    if risk >= hr:
        return ("Retention Follow-Up",
                f"Elevated risk {risk:.0f} — proactive check-in required")

    # Rule 5: High upside potential
    if upside >= 65 and value >= hv * 0.7:
        return ("Growth Opportunity: Upgrade Offer",
                f"Upside potential {upside:.0f} · Value {value:.0f} — commercial growth candidate")

    # Rule 6: Dormant/inactive with high reactivation score
    if react >= 65 and status in ("Dormant", "Inactive"):
        return ("Reactivation Campaign",
                f"Reactivation score {react:.0f} · Status: {status}")

    # Rule 7: Volume dropped >50%
    if vol_dropped and risk >= 35:
        return ("Re-engagement: Trading Incentive",
                "Trading volume dropped >50% — bonus or cashback may re-engage")

    # Rule 8: Complaints present
    if complaints >= 1:
        return ("Complaint Resolution",
                f"{complaints} open complaint(s)/ticket(s)")

    # Rule 9: Low risk, low value
    if risk < 30 and value < 30:
        return ("Monitor Only",
                "Low risk, low value — no immediate action needed")

    # Default
    return ("Account Manager Follow-Up",
            "Routine check-in recommended")


# ─────────────────────────────────────────────────────────────────────────────
# RECOMMENDED OWNER
# ─────────────────────────────────────────────────────────────────────────────

def assign_recommended_owner(row: pd.Series, thresholds: dict) -> str:
    hr = thresholds["high_risk"]
    hv = thresholds["high_value"]

    if row["priority_score"] > 80 and row["commercial_value_score"] >= hv:
        return "Management Review"
    if row["priority_score"] > 80:
        return "Retention Team"
    if row["retention_risk_score"] >= hr and row["commercial_value_score"] >= hv:
        return "Retention Team"
    if row["retention_risk_score"] >= hr:
        return "Account Manager"
    if row["reactivation_score"] > 65 and row["account_status"] in ("Dormant", "Inactive"):
        return "Sales Team"
    return "Account Manager"


# ─────────────────────────────────────────────────────────────────────────────
# TREND DATA
# ─────────────────────────────────────────────────────────────────────────────

def generate_trend_snapshots(scored_df: pd.DataFrame) -> pd.DataFrame:
    """
    Simulate 6 monthly platform-level snapshots so we can draw trend charts.
    Values drift slightly backwards from the current state to simulate history.
    """
    import datetime
    today = datetime.date.today()

    current_risk   = scored_df["retention_risk_score"].mean()
    current_health = scored_df["client_health_score"].mean()
    current_equity = scored_df["current_equity"].sum()
    # Revenue uses net_company_pnl (book-type-aware profit)
    current_rev    = scored_df["net_company_pnl"].sum() * 12

    rows = []
    for i in range(5, -1, -1):
        factor = 1 - i * 0.025
        rows.append({
            "date": today - datetime.timedelta(days=30 * i),
            "avg_risk_score":     round(current_risk * factor, 1),
            "avg_health_score":   round(current_health / factor, 1),
            "total_equity":       round(current_equity * factor, 0),
            "annual_revenue":     round(current_rev * factor, 0),
            "annual_profitability": round(current_rev * factor, 0),
            "pct_high_risk":      round(
                (scored_df["retention_risk_score"] >= 60).mean() * factor, 3),
        })

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

def score_dataframe(df: pd.DataFrame,
                    risk_weights: dict,
                    value_weights: dict,
                    prof_weights: dict,
                    react_weights: dict,
                    upside_weights: dict,
                    thresholds: dict,
                    rules: dict = None) -> pd.DataFrame:
    """
    Enrich the raw client DataFrame with all 6 scores plus labels,
    segmentation, recommended action, and recommended owner.
    Risk, Value, and Profitability are driven by the Business Rules Engine.
    """
    if rules is None:
        rules = _re.load_rules()

    df = df.copy()

    df["retention_risk_score"]    = _re.score_retention_risk(df, rules, risk_weights)
    df["commercial_value_score"]  = _re.score_commercial_value(df, rules, value_weights)
    df["profitability_score"]     = _re.score_profitability(df, rules)
    df["reactivation_score"]      = compute_reactivation(df, react_weights)
    df["upside_potential_score"]  = compute_upside_potential(df, upside_weights)
    df["client_health_score"]     = compute_client_health(
        df["retention_risk_score"],
        df["commercial_value_score"],
        df["profitability_score"],
    )
    df["priority_score"] = compute_priority(
        df["retention_risk_score"],
        df["commercial_value_score"],
        df["profitability_score"],
        df["upside_potential_score"],
    )

    df["health_label"] = df["client_health_score"].apply(health_label)
    df["segment"]      = df.apply(lambda r: assign_segment(r, thresholds), axis=1)

    actions = df.apply(lambda r: assign_recommended_action(r, thresholds), axis=1)
    df["recommended_action"] = actions.apply(lambda x: x[0])
    df["action_reason"]      = actions.apply(lambda x: x[1])
    df["recommended_owner"]  = df.apply(
        lambda r: assign_recommended_owner(r, thresholds), axis=1)

    hr = thresholds["high_risk"]
    hv = thresholds["high_value"]
    hp = thresholds.get("high_profitability", 60)
    cp = thresholds.get("critical_priority", 65)

    risk_mid  = max(1, int(hr * 0.5))
    value_mid = max(1, int(hv * 0.5))
    prio_mid  = max(1, int(cp * 0.5))

    df["risk_level"] = pd.cut(
        df["retention_risk_score"],
        bins=[-1, risk_mid, hr, 101],
        labels=["Low", "Medium", "High"]
    )
    df["value_level"] = pd.cut(
        df["commercial_value_score"],
        bins=[-1, value_mid, hv, 101],
        labels=["Low", "Medium", "High"]
    )
    df["priority_level"] = pd.cut(
        df["priority_score"],
        bins=[-1, prio_mid, cp, 101],
        labels=["Normal", "Elevated", "Critical"]
    )

    return df
