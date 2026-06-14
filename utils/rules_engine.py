# utils/rules_engine.py — v2.0
# Business Rules Engine — loads tiered scoring rules from config/scoring_rules.json,
# applies them to compute factor scores, and exposes the config for UI editing.
# Changes v2.0: VIP removed from commercial value. Both equity_erosion and equity_trend
# signals now in retention risk. Corrected B-Book/M-Book profitability (no spread).

import json, os
import pandas as pd
import numpy as np

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "scoring_rules.json")


# ─────────────────────────────────────────────────────────────────────────────
# Config I/O
# ─────────────────────────────────────────────────────────────────────────────

def load_rules() -> dict:
    """Load scoring rules from the JSON config file."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_rules(rules: dict):
    """Persist updated rules back to the JSON config file."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Band evaluation
# ─────────────────────────────────────────────────────────────────────────────

def apply_band(value: float, bands: list) -> float:
    """
    Evaluate a single scalar value against a list of band rules.
    Returns the points for the first matching band.

    Supported operators:
      lt       value < threshold
      lte      value <= threshold
      gt       value > threshold
      gte      value >= threshold
      eq       value == threshold   (integer equality)
      between  low <= value < high
    """
    for band in bands:
        op = band["op"]
        if op == "lt"  and value < band["threshold"]:
            return float(band["points"])
        if op == "lte" and value <= band["threshold"]:
            return float(band["points"])
        if op == "gt"  and value > band["threshold"]:
            return float(band["points"])
        if op == "gte" and value >= band["threshold"]:
            return float(band["points"])
        if op == "eq"  and int(value) == int(band["threshold"]):
            return float(band["points"])
        if op == "between" and band["low"] <= value < band["high"]:
            return float(band["points"])
    return float(bands[-1]["points"]) if bands else 50.0


def apply_band_series(series: pd.Series, bands: list) -> pd.Series:
    """Vectorised band evaluation over a pandas Series."""
    return series.apply(lambda v: apply_band(v, bands))


# ─────────────────────────────────────────────────────────────────────────────
# Retention Risk — rules-based  (7 signals)
# ─────────────────────────────────────────────────────────────────────────────

def score_retention_risk(df: pd.DataFrame, rules: dict, weights: dict) -> pd.Series:
    """
    Apply configured retention-risk rules to every client.
    Seven signals: withdrawal pressure, volume drop, login inactivity,
    deposit inactivity, complaints, equity erosion (vs deposits), equity trend (30d).
    Each factor scored 0-100 via band rules, combined with weights, then re-normalized.
    """
    rr = rules["retention_risk"]

    # Derived metrics
    withdrawal_pct = (
        df["withdrawal_amount_last_30d"] / df["current_equity"].clip(lower=1) * 100
    )
    vol_drop_pct = (
        (df["trading_volume_previous_30d"] - df["trading_volume_last_30d"])
        / df["trading_volume_previous_30d"].clip(lower=1) * 100
    ).clip(lower=0)
    complaints_total = df["complaints_last_30d"] + df["open_tickets"]

    # Equity erosion vs net deposits (long-term capital destruction signal)
    equity_erosion_pct = (
        (1 - df["current_equity"] / df["net_deposits"].clip(lower=1)) * 100
    ).clip(lower=0)

    # Equity trend: short-term 30-day balance decline
    equity_trend_pct = (
        (df["equity_30d_ago"] - df["current_equity"])
        / df["equity_30d_ago"].clip(lower=1) * 100
    ).clip(lower=0)

    # Apply bands
    f_withdrawal = apply_band_series(withdrawal_pct,             rr["withdrawal_risk"]["bands"])
    f_vol_drop   = apply_band_series(vol_drop_pct,               rr["volume_drop"]["bands"])
    f_login      = apply_band_series(df["login_days_ago"],       rr["login_inactivity"]["bands"])
    f_deposit    = apply_band_series(df["last_deposit_days_ago"],rr["deposit_inactivity"]["bands"])
    f_complaints = apply_band_series(complaints_total,           rr["complaints"]["bands"])
    f_erosion    = apply_band_series(equity_erosion_pct,         rr["equity_erosion"]["bands"])
    f_trend      = apply_band_series(equity_trend_pct,           rr["equity_trend"]["bands"])

    w = weights
    total_w = (
        w["w_withdrawal"] + w["w_volume_drop"] + w["w_login"] +
        w["w_deposit_stale"] + w["w_complaints"] +
        w["w_equity_erosion"] + w["w_equity_trend"]
    ) or 1

    raw = (
        f_withdrawal * w["w_withdrawal"] +
        f_vol_drop   * w["w_volume_drop"] +
        f_login      * w["w_login"] +
        f_deposit    * w["w_deposit_stale"] +
        f_complaints * w["w_complaints"] +
        f_erosion    * w["w_equity_erosion"] +
        f_trend      * w["w_equity_trend"]
    ) / total_w

    return _normalize(raw).round(1)


# ─────────────────────────────────────────────────────────────────────────────
# Commercial Value — rules-based  (6 signals, no VIP)
# ─────────────────────────────────────────────────────────────────────────────

def score_commercial_value(df: pd.DataFrame, rules: dict, weights: dict) -> pd.Series:
    """
    Apply configured commercial-value rules to every client.
    Six financial signals. No VIP status — value is measured by financial behaviour only.
    """
    cv = rules["commercial_value"]

    f_lifetime   = apply_band_series(df["lifetime_deposits"],        cv["lifetime_deposits"]["bands"])
    f_net_dep    = apply_band_series(df["net_deposits"],             cv["net_deposits"]["bands"])
    f_equity     = apply_band_series(df["current_equity"],           cv["current_equity"]["bands"])
    f_volume     = apply_band_series(df["trading_volume_last_30d"],  cv["trading_volume"]["bands"])
    f_redeposits = apply_band_series(df["number_of_redeposits"],     cv["redeposit_count"]["bands"])
    f_tenure     = apply_band_series(df["client_tenure_days"],       cv["client_tenure"]["bands"])

    w = weights
    total_w = (
        w["v_lifetime_dep"] + w["v_net_dep"] + w["v_current_equity"] +
        w["v_volume"] + w["v_redeposits"] + w["v_tenure"]
    ) or 1

    raw = (
        f_lifetime   * w["v_lifetime_dep"] +
        f_net_dep    * w["v_net_dep"] +
        f_equity     * w["v_current_equity"] +
        f_volume     * w["v_volume"] +
        f_redeposits * w["v_redeposits"] +
        f_tenure     * w["v_tenure"]
    ) / total_w

    return _normalize(raw).round(1)


# ─────────────────────────────────────────────────────────────────────────────
# Profitability — book-type aware rules  (corrected B-Book/M-Book formulas)
# ─────────────────────────────────────────────────────────────────────────────

def score_profitability(df: pd.DataFrame, rules: dict) -> pd.Series:
    """
    Compute profitability amount per book type, apply book-specific bands,
    then normalize across all clients to produce a 0-100 score.

    A-Book: commission + swap + spread_commission_revenue
            (all revenue is fee-based; spread IS a client-facing charge)
    B-Book: captured_client_losses + commission + swap
            (position P&L model; spread NOT included — B-Book earns from losses)
    M-Book: internal_ratio × captured_client_losses + commission + swap
            (partial position model; spread NOT included in internal P&L)
    """
    pr = rules["profitability"]
    amounts    = pd.Series(0.0, index=df.index)
    raw_scores = pd.Series(0.0, index=df.index)

    a_mask = df["book_type"] == "A-Book"
    b_mask = df["book_type"] == "B-Book"
    m_mask = df["book_type"] == "M-Book"

    # A-Book: fees only
    amounts[a_mask] = (
        df.loc[a_mask, "commission_revenue"] +
        df.loc[a_mask, "swap_revenue"] +
        df.loc[a_mask, "spread_commission_revenue"]
    )

    # B-Book: position P&L + fees, no spread
    amounts[b_mask] = (
        df.loc[b_mask, "captured_client_losses"] +
        df.loc[b_mask, "commission_revenue"] +
        df.loc[b_mask, "swap_revenue"]
    )

    # M-Book: partial position P&L + fees, no spread
    internal_ratio = pr["m_book"].get("internal_ratio", 0.6)
    amounts[m_mask] = (
        internal_ratio * df.loc[m_mask, "captured_client_losses"] +
        df.loc[m_mask, "commission_revenue"] +
        df.loc[m_mask, "swap_revenue"]
    )

    # Apply book-specific bands to raw dollar amounts
    raw_scores[a_mask] = apply_band_series(amounts[a_mask], pr["a_book"]["bands"])
    raw_scores[b_mask] = apply_band_series(amounts[b_mask], pr["b_book"]["bands"])
    raw_scores[m_mask] = apply_band_series(amounts[m_mask], pr["m_book"]["bands"])

    return _normalize(raw_scores).round(1)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - mn) / (mx - mn)) * 100


def get_factor_breakdown(row: pd.Series, rules: dict) -> dict:
    """
    Return a dict of {factor_label: points_scored} for a single client.
    Used in the Client Detail view to show WHY a client scored a certain way.
    """
    rr = rules["retention_risk"]
    cv = rules["commercial_value"]

    withdrawal_pct   = (row["withdrawal_amount_last_30d"] / max(row["current_equity"], 1)) * 100
    vol_drop_pct     = max(0, (row["trading_volume_previous_30d"] - row["trading_volume_last_30d"])
                          / max(row["trading_volume_previous_30d"], 1) * 100)
    equity_erosion   = max(0, (1 - row["current_equity"] / max(row["net_deposits"], 1)) * 100)
    equity_trend     = max(0, (row["equity_30d_ago"] - row["current_equity"])
                          / max(row["equity_30d_ago"], 1) * 100)
    complaints_total = row["complaints_last_30d"] + row["open_tickets"]

    return {
        "risk_factors": {
            rr["withdrawal_risk"]["label"]:    apply_band(withdrawal_pct, rr["withdrawal_risk"]["bands"]),
            rr["volume_drop"]["label"]:        apply_band(vol_drop_pct,   rr["volume_drop"]["bands"]),
            rr["login_inactivity"]["label"]:   apply_band(row["login_days_ago"], rr["login_inactivity"]["bands"]),
            rr["deposit_inactivity"]["label"]: apply_band(row["last_deposit_days_ago"], rr["deposit_inactivity"]["bands"]),
            rr["complaints"]["label"]:         apply_band(complaints_total, rr["complaints"]["bands"]),
            rr["equity_erosion"]["label"]:     apply_band(equity_erosion, rr["equity_erosion"]["bands"]),
            rr["equity_trend"]["label"]:       apply_band(equity_trend, rr["equity_trend"]["bands"]),
        },
        "value_factors": {
            cv["lifetime_deposits"]["label"]:  apply_band(row["lifetime_deposits"],       cv["lifetime_deposits"]["bands"]),
            cv["net_deposits"]["label"]:       apply_band(row["net_deposits"],             cv["net_deposits"]["bands"]),
            cv["current_equity"]["label"]:     apply_band(row["current_equity"],           cv["current_equity"]["bands"]),
            cv["trading_volume"]["label"]:     apply_band(row["trading_volume_last_30d"],  cv["trading_volume"]["bands"]),
            cv["redeposit_count"]["label"]:    apply_band(row["number_of_redeposits"],     cv["redeposit_count"]["bands"]),
            cv["client_tenure"]["label"]:      apply_band(row["client_tenure_days"],       cv["client_tenure"]["bands"]),
        },
    }
