# utils/scoring.py
# Phase 3 — Rules-engine-driven scoring for Risk, Value, and Profitability.
# Reactivation, VIP Upside, and Health remain weight-based.

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
    # Withdrawal pressure: large recent withdrawal relative to equity
    wr = df["withdrawal_amount_last_30d"] / df["current_equity"].clip(lower=1)
    f_withdrawal = _normalize(wr)

    # Volume drop: did trading fall vs previous period?
    vdrop = (df["trading_volume_previous_30d"] - df["trading_volume_last_30d"]) \
            / df["trading_volume_previous_30d"].clip(lower=1)
    f_vol_drop = _normalize(vdrop.clip(lower=0))

    # Login inactivity
    f_login = _normalize(df["login_days_ago"])

    # Deposit staleness
    f_deposit = _normalize(df["last_deposit_days_ago"])

    # Complaints and open tickets
    f_complaints = _normalize(df["complaints_last_30d"] + df["open_tickets"])

    # Equity erosion vs net deposits
    erosion = 1 - df["current_equity"] / df["net_deposits"].clip(lower=1)
    f_equity_erosion = _normalize(erosion.clip(lower=0))

    # Equity declining in last 30 days
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
    Future business potential. Higher = more commercially important.
    """
    f_lifetime   = _normalize(df["lifetime_deposits"])
    f_net_dep    = _normalize(df["net_deposits"])
    f_equity     = _normalize(df["current_equity"])
    f_volume     = _normalize(df["trading_volume_last_30d"])
    f_redeposits = _normalize(df["number_of_redeposits"])
    f_tenure     = _normalize(df["client_tenure_days"])
    # VIP flag converted to 0 or 100
    f_vip        = df["vip_status"].astype(float) * 100

    w = weights
    total = (w["v_lifetime_dep"] + w["v_net_dep"] + w["v_current_equity"] +
             w["v_volume"] + w["v_redeposits"] + w["v_tenure"] + w["v_vip"]) or 1

    raw = (
        f_lifetime   * w["v_lifetime_dep"] +
        f_net_dep    * w["v_net_dep"] +
        f_equity     * w["v_current_equity"] +
        f_volume     * w["v_volume"] +
        f_redeposits * w["v_redeposits"] +
        f_tenure     * w["v_tenure"] +
        f_vip        * w["v_vip"]
    ) / total

    return _normalize(raw).round(1)


# ─────────────────────────────────────────────────────────────────────────────
# 3. PROFITABILITY SCORE  (book-type aware)
# ─────────────────────────────────────────────────────────────────────────────

def compute_profitability(df: pd.DataFrame) -> pd.Series:
    """
    Actual profitability to OneRoyal, calculated per book type.

    A-Book:  spread + commission + swap  (exposure is hedged, PnL irrelevant)
    B-Book:  captured client losses + spread  (losses ARE the product)
    M-Book:  0.6 × captured losses + spread + commission + swap

    A single 'profitability_amount' series is computed and then normalized
    to 0-100 across all clients regardless of book type.
    """
    amounts = pd.Series(0.0, index=df.index)

    a_mask = df["book_type"] == "A-Book"
    b_mask = df["book_type"] == "B-Book"
    m_mask = df["book_type"] == "M-Book"

    amounts[a_mask] = (
        df.loc[a_mask, "spread_commission_revenue"] +
        df.loc[a_mask, "commission_revenue"] +
        df.loc[a_mask, "swap_revenue"]
    )
    amounts[b_mask] = (
        df.loc[b_mask, "captured_client_losses"] +
        df.loc[b_mask, "spread_commission_revenue"]
    )
    amounts[m_mask] = (
        0.6 * df.loc[m_mask, "captured_client_losses"] +
        df.loc[m_mask, "spread_commission_revenue"] +
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

    The 'login window' factor scores highest for clients who logged in
    30-180 days ago (not too recent, not completely gone).
    """
    # Score highest when login was 30-180 days ago
    login = df["login_days_ago"].clip(0, 365)
    window_score = np.where(
        (login >= 30) & (login <= 180),
        100 - ((login - 105).abs() / 75) * 100,   # peaks at 105 days
        np.where(login < 30, login / 30 * 50, np.maximum(0, 100 - (login - 180) / 1.85))
    )
    f_login_window = pd.Series(window_score, index=df.index).clip(0, 100)

    f_lifetime  = _normalize(df["lifetime_deposits"])
    f_redeposits = _normalize(df["number_of_redeposits"])
    f_vol_hist  = _normalize(df["volume_90d_ago"])
    f_tenure    = _normalize(df["client_tenure_days"])

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
# 5. VIP UPSIDE SCORE
# ─────────────────────────────────────────────────────────────────────────────

def compute_vip_upside(df: pd.DataFrame, weights: dict) -> pd.Series:
    """
    Growth and upsell potential. High score = untapped commercial opportunity.
    Clients already VIP score lower on the 'not yet VIP' factor.
    """
    f_equity    = _normalize(df["current_equity"])
    f_net_dep   = _normalize(df["net_deposits"])

    # Positive volume trend vs 90 days ago
    vol_trend = (df["trading_volume_last_30d"] - df["volume_90d_ago"]) \
                / df["volume_90d_ago"].clip(lower=1)
    f_vol_trend = _normalize(vol_trend.clip(lower=-1, upper=5))

    f_redeposits = _normalize(df["number_of_redeposits"])

    # Non-VIP clients score 100, VIPs score 0 on this factor
    f_not_vip = (~df["vip_status"]).astype(float) * 100

    w = weights
    total = (w["u_equity"] + w["u_net_dep"] + w["u_volume_trend"] +
             w["u_redeposits"] + w["u_not_yet_vip"]) or 1

    raw = (
        f_equity      * w["u_equity"] +
        f_net_dep     * w["u_net_dep"] +
        f_vol_trend   * w["u_volume_trend"] +
        f_redeposits  * w["u_redeposits"] +
        f_not_vip     * w["u_not_yet_vip"]
    ) / total

    return _normalize(raw).round(1)


# ─────────────────────────────────────────────────────────────────────────────
# 6. CLIENT HEALTH SCORE
# ─────────────────────────────────────────────────────────────────────────────

def compute_client_health(risk: pd.Series, value: pd.Series,
                          profitability: pd.Series) -> pd.Series:
    """
    Positive management metric. 100 = excellent, 0 = critical.
    Decreases sharply when retention risk rises.
    High commercial value or profitability partially offsets risk.
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
                     profitability: pd.Series, reactivation: pd.Series) -> pd.Series:
    """
    Answers: "who should we call today to protect the most revenue?"
    Profitability and risk are the dominant signals.
    """
    raw = (risk * 0.30 + value * 0.25 + profitability * 0.30 + reactivation * 0.15)
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
    ("Low",    "High"):   "VIP Expansion",
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
# RECOMMENDED ACTION
# ─────────────────────────────────────────────────────────────────────────────

def assign_recommended_action(row: pd.Series, thresholds: dict) -> tuple:
    """Returns (action_label, reason_string). First matching rule wins."""
    risk  = row["retention_risk_score"]
    value = row["commercial_value_score"]
    prof  = row["profitability_score"]
    react = row["reactivation_score"]
    upside = row["vip_upside_score"]

    hr = thresholds["high_risk"]
    hv = thresholds["high_value"]
    hp = thresholds.get("high_profitability", 60)

    complaints   = row["complaints_last_30d"] + row["open_tickets"]
    wd_pct       = row["withdrawal_amount_last_30d"] / max(row["current_equity"], 1)
    vol_dropped  = row["trading_volume_last_30d"] < row["trading_volume_previous_30d"] * 0.5
    is_vip       = row["vip_status"]
    status       = row["account_status"]
    large_wd_pct = thresholds.get("large_withdrawal_pct", 0.30)

    # Rule 1: VIP + high risk + high value → board-level escalation
    if is_vip and risk >= hr and value >= hv:
        return ("URGENT: VIP Retention — Escalate to Management",
                f"VIP client · Risk {risk:.0f} · Value {value:.0f}")

    # Rule 2: High risk + high value + high profitability → immediate call
    if risk >= hr and value >= hv and prof >= hp:
        return ("Immediate Retention Call",
                f"Risk {risk:.0f} · Value {value:.0f} · Profit {prof:.0f}")

    # Rule 3: Complaints with high risk
    if complaints >= 2 and risk >= hr:
        return ("Resolve Complaints + Retention Review",
                f"{complaints} complaints/tickets · Risk {risk:.0f}")

    # Rule 4: Large withdrawal + high risk
    if wd_pct >= large_wd_pct and risk >= hr:
        return ("Retention Call: Withdrawal Alert",
                f"Withdrew {wd_pct:.0%} of equity · Risk {risk:.0f}")

    # Rule 5: High risk (general)
    if risk >= hr:
        return ("Retention Follow-Up",
                f"Elevated risk {risk:.0f} — check-in required")

    # Rule 6: VIP + low risk + high value → expand
    if is_vip and risk < hr * 0.5 and value >= hv:
        return ("VIP Expansion Offer",
                f"Healthy VIP · Value {value:.0f} — upsell opportunity")

    # Rule 7: High VIP upside potential, not yet VIP
    if upside >= 65 and not is_vip:
        return ("VIP Upsell Opportunity",
                f"VIP upside score {upside:.0f} — commercial growth potential")

    # Rule 8: Dormant/inactive with high reactivation score
    if react >= 65 and status in ("Dormant", "Inactive"):
        return ("Reactivation Campaign",
                f"Reactivation score {react:.0f} · Status: {status}")

    # Rule 9: Volume dropped >50%
    if vol_dropped and risk >= 35:
        return ("Re-engagement: Trading Incentive",
                "Trading volume dropped >50% — bonus or cashback may help")

    # Rule 10: Complaints present
    if complaints >= 1:
        return ("Complaint Resolution",
                f"{complaints} open complaint(s)/ticket(s)")

    # Rule 11: Low risk, low value
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

    if row["vip_status"] or row["commercial_value_score"] > 75:
        if row["priority_score"] > 80:
            return "Management Review"
        return "VIP Team"
    if row["priority_score"] > 80:
        return "Management Review"
    if row["retention_risk_score"] >= hr:
        return "Retention Team"
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
    current_rev    = (scored_df["spread_commission_revenue"] +
                      scored_df["commission_revenue"] +
                      scored_df["swap_revenue"]).sum() * 12
    current_prof   = scored_df["net_company_pnl"].sum() * 12

    rows = []
    for i in range(5, -1, -1):
        # Older months: slightly better metrics (risk lower, health higher)
        factor = 1 - i * 0.025     # each month back is 2.5% "better"
        rows.append({
            "date": today - datetime.timedelta(days=30 * i),
            "avg_risk_score":     round(current_risk * factor, 1),
            "avg_health_score":   round(current_health / factor, 1),
            "total_equity":       round(current_equity * factor, 0),
            "annual_revenue":     round(current_rev * factor, 0),
            "annual_profitability": round(current_prof * factor, 0),
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
                    vip_weights: dict,
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

    df["retention_risk_score"]   = _re.score_retention_risk(df, rules, risk_weights)
    df["commercial_value_score"] = _re.score_commercial_value(df, rules, value_weights)
    df["profitability_score"]    = _re.score_profitability(df, rules)
    df["reactivation_score"]     = compute_reactivation(df, react_weights)
    df["vip_upside_score"]       = compute_vip_upside(df, vip_weights)
    df["client_health_score"]    = compute_client_health(
        df["retention_risk_score"],
        df["commercial_value_score"],
        df["profitability_score"],
    )
    df["priority_score"] = compute_priority(
        df["retention_risk_score"],
        df["commercial_value_score"],
        df["profitability_score"],
        df["reactivation_score"],
    )

    # Health label
    df["health_label"] = df["client_health_score"].apply(health_label)

    # Segment
    df["segment"] = df.apply(lambda r: assign_segment(r, thresholds), axis=1)

    # Action and owner
    actions = df.apply(lambda r: assign_recommended_action(r, thresholds), axis=1)
    df["recommended_action"] = actions.apply(lambda x: x[0])
    df["action_reason"]      = actions.apply(lambda x: x[1])
    df["recommended_owner"]  = df.apply(
        lambda r: assign_recommended_owner(r, thresholds), axis=1)

    # Tier labels for filtering
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
