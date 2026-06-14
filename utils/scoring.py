# utils/scoring.py
# This module contains all scoring logic for retention risk, client value,
# and priority score. Weights can be passed in from the UI sliders.

import pandas as pd
import numpy as np


def _normalize(series: pd.Series) -> pd.Series:
    """Scale any numeric series to 0–100 using min-max normalization."""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - min_val) / (max_val - min_val)) * 100


def compute_retention_risk(df: pd.DataFrame, weights: dict) -> pd.Series:
    """
    Retention risk goes UP when a client is showing signs of leaving:
    - Recent large withdrawals
    - Dropped trading volume
    - Not logging in
    - No recent deposits
    - Complaints or open tickets
    - Equity is falling vs deposits

    Each factor is scored 0–100, then weighted and averaged.
    Final score is 0–100 where 100 = highest risk.
    """
    # Factor 1: Withdrawal pressure — bigger withdrawals = higher risk
    withdrawal_ratio = df["withdrawal_amount_last_30d"] / (df["current_equity"].clip(lower=1))
    f_withdrawal = _normalize(withdrawal_ratio)

    # Factor 2: Volume drop — did trading drop from last period?
    volume_drop = df["trading_volume_previous_30d"] - df["trading_volume_last_30d"]
    volume_drop_pct = volume_drop / (df["trading_volume_previous_30d"].clip(lower=1))
    f_volume_drop = _normalize(volume_drop_pct.clip(lower=0))  # only score drops

    # Factor 3: Login inactivity — longer ago = higher risk
    f_login = _normalize(df["login_days_ago"])

    # Factor 4: Deposit inactivity — longer since last deposit = higher risk
    f_deposit_stale = _normalize(df["last_deposit_days_ago"])

    # Factor 5: Complaints/tickets — more = higher risk
    f_complaints = _normalize(df["complaints_last_30d"] + df["open_tickets"])

    # Factor 6: Equity erosion — equity much lower than net deposits = higher risk
    equity_vs_deposits = 1 - (df["current_equity"] / df["net_deposits"].clip(lower=1))
    f_equity_erosion = _normalize(equity_vs_deposits.clip(lower=0))

    # Combine with weights (weights are 0–10 from sliders, we normalise them)
    total_weight = (
        weights["w_withdrawal"] + weights["w_volume_drop"] +
        weights["w_login"] + weights["w_deposit_stale"] +
        weights["w_complaints"] + weights["w_equity_erosion"]
    )
    if total_weight == 0:
        total_weight = 1  # avoid division by zero

    score = (
        f_withdrawal       * weights["w_withdrawal"] +
        f_volume_drop      * weights["w_volume_drop"] +
        f_login            * weights["w_login"] +
        f_deposit_stale    * weights["w_deposit_stale"] +
        f_complaints       * weights["w_complaints"] +
        f_equity_erosion   * weights["w_equity_erosion"]
    ) / total_weight

    # Final normalization so scores genuinely span 0–100
    return _normalize(score).round(1)


def compute_client_value(df: pd.DataFrame, weights: dict) -> pd.Series:
    """
    Client value goes UP when the client is financially important:
    - High lifetime deposits
    - High net deposits
    - High trading volume
    - Frequent redeposits (loyal depositor)
    - High company PnL from client
    - High spread/commission revenue

    Final score is 0–100 where 100 = most valuable.
    """
    f_lifetime_dep  = _normalize(df["lifetime_deposits"])
    f_net_dep       = _normalize(df["net_deposits"])
    f_volume        = _normalize(df["trading_volume_last_30d"])
    f_redeposits    = _normalize(df["number_of_redeposits"])
    f_pnl           = _normalize(df["company_pnl_from_client"])
    f_spread_rev    = _normalize(df["spread_commission_revenue"])

    total_weight = (
        weights["v_lifetime_dep"] + weights["v_net_dep"] +
        weights["v_volume"] + weights["v_redeposits"] +
        weights["v_pnl"] + weights["v_spread_rev"]
    )
    if total_weight == 0:
        total_weight = 1

    score = (
        f_lifetime_dep  * weights["v_lifetime_dep"] +
        f_net_dep       * weights["v_net_dep"] +
        f_volume        * weights["v_volume"] +
        f_redeposits    * weights["v_redeposits"] +
        f_pnl           * weights["v_pnl"] +
        f_spread_rev    * weights["v_spread_rev"]
    ) / total_weight

    # Final normalization: stretch the combined score to the full 0–100 range
    return _normalize(score).round(1)


def compute_priority(risk: pd.Series, value: pd.Series,
                     risk_weight: float = 0.6, value_weight: float = 0.4) -> pd.Series:
    """
    Priority = blend of high risk + high value.
    A client who is valuable AND at risk gets the highest priority.
    """
    raw = (risk * risk_weight) + (value * value_weight)
    return _normalize(raw).round(1)


def assign_recommended_action(row: pd.Series, thresholds: dict) -> tuple:
    """
    Rule-based engine: returns (action_label, reason_string).
    Rules are checked top-to-bottom; first match wins.
    """
    risk   = row["retention_risk_score"]
    value  = row["client_value_score"]
    priority = row["priority_score"]

    complaints = row["complaints_last_30d"] + row["open_tickets"]
    withdrawal_pct = row["withdrawal_amount_last_30d"] / max(row["current_equity"], 1)
    volume_dropped = row["trading_volume_last_30d"] < row["trading_volume_previous_30d"] * 0.5

    high_risk_threshold   = thresholds.get("high_risk", 65)
    high_value_threshold  = thresholds.get("high_value", 60)
    critical_priority     = thresholds.get("critical_priority", 70)
    large_withdrawal_pct  = thresholds.get("large_withdrawal_pct", 0.30)

    # Rule 1: Complaints must be resolved before commercial offers
    if complaints >= 2 and risk >= high_risk_threshold:
        return (
            "Investigate complaints before commercial offer",
            f"{complaints} complaints/tickets + risk {risk:.0f}"
        )

    # Rule 2: High-value, high-risk — senior intervention needed
    if risk >= high_risk_threshold and value >= high_value_threshold:
        return (
            "Senior retention call today",
            f"Risk {risk:.0f} | Value {value:.0f} — top priority"
        )

    # Rule 3: Large withdrawal in last 30 days
    if withdrawal_pct >= large_withdrawal_pct and risk >= high_risk_threshold:
        return (
            "Senior retention call today",
            f"Withdrew {withdrawal_pct:.0%} of equity in 30 days"
        )

    # Rule 4: High risk but moderate value — AM follow-up
    if risk >= high_risk_threshold:
        return (
            "Account manager follow-up",
            f"Elevated risk {risk:.0f} — check in needed"
        )

    # Rule 5: High-value, moderate risk — reward loyalty
    if value >= high_value_threshold and risk < high_risk_threshold:
        return (
            "VIP upsell opportunity",
            f"High-value client {value:.0f} with manageable risk"
        )

    # Rule 6: Volume dropped significantly
    if volume_dropped and risk >= 40:
        return (
            "Cashback/bonus review",
            "Trading volume dropped >50% — incentive may help"
        )

    # Rule 7: Complaints present but not critical
    if complaints >= 1:
        return (
            "Investigate complaints before commercial offer",
            f"{complaints} open complaint(s)/ticket(s)"
        )

    # Rule 8: Client is fine — low activity monitoring
    if risk < 30 and value < 30:
        return (
            "Watch only",
            "Low risk, low value — no immediate action"
        )

    # Rule 9: Medium engagement — keep warm
    if risk < 50:
        return (
            "Nurture campaign",
            "Moderate engagement — add to drip campaign"
        )

    # Rule 10: Do not push bonuses to high-withdrawal clients
    if withdrawal_pct >= 0.15:
        return (
            "Do not offer bonus",
            "Client withdrawing funds — bonus may accelerate exit"
        )

    # Default
    return (
        "Account manager follow-up",
        "General check-in recommended"
    )


def score_dataframe(df: pd.DataFrame,
                    risk_weights: dict,
                    value_weights: dict,
                    thresholds: dict,
                    risk_blend: float = 0.6) -> pd.DataFrame:
    """
    Main entry point: takes raw client data and returns it enriched
    with all scores and recommended actions.
    """
    df = df.copy()

    df["retention_risk_score"] = compute_retention_risk(df, risk_weights)
    df["client_value_score"]   = compute_client_value(df, value_weights)
    df["priority_score"]       = compute_priority(
        df["retention_risk_score"],
        df["client_value_score"],
        risk_weight=risk_blend,
        value_weight=1 - risk_blend,
    )

    # Apply action rules row by row
    actions = df.apply(
        lambda row: assign_recommended_action(row, thresholds), axis=1
    )
    df["recommended_action"] = actions.apply(lambda x: x[0])
    df["action_reason"]      = actions.apply(lambda x: x[1])

    # Risk tier labels
    # We use the user-defined threshold as the High boundary.
    # The Low/Medium split is always half of the threshold (or 33, whichever is smaller)
    # so bins are always strictly increasing regardless of threshold value.
    high_risk_threshold  = thresholds.get("high_risk", 60)
    high_value_threshold = thresholds.get("high_value", 20)
    critical_priority    = thresholds.get("critical_priority", 50)

    risk_mid  = max(1, min(high_risk_threshold - 1,  int(high_risk_threshold  * 0.5)))
    value_mid = max(1, min(high_value_threshold - 1, int(high_value_threshold * 0.5)))
    prio_mid  = max(1, min(critical_priority - 1,    int(critical_priority    * 0.5)))

    df["risk_level"] = pd.cut(
        df["retention_risk_score"],
        bins=[-1, risk_mid, high_risk_threshold, 101],
        labels=["Low", "Medium", "High"]
    )
    df["value_level"] = pd.cut(
        df["client_value_score"],
        bins=[-1, value_mid, high_value_threshold, 101],
        labels=["Low", "Medium", "High"]
    )
    df["priority_level"] = pd.cut(
        df["priority_score"],
        bins=[-1, prio_mid, critical_priority, 101],
        labels=["Normal", "Elevated", "Critical"]
    )

    return df
