# integrations/data_mapper.py
# Transforms raw input DataFrames (upload-style column names) into the
# internal schema expected by the scoring engine.

import pandas as pd
import numpy as np
from datetime import date
from typing import Dict, List, Any

# ---------------------------------------------------------------------------
# Column rename map: upload name -> internal name
# ---------------------------------------------------------------------------

UPLOAD_COLUMN_MAP: Dict[str, str] = {
    "trading_volume_30d":   "trading_volume_last_30d",
    "spread_revenue":       "spread_commission_revenue",
    "company_pnl":          "company_pnl_from_client",
    "complaints":           "complaints_last_30d",
    "withdrawals_30d":      "withdrawal_amount_last_30d",
    # Date columns are handled separately (conversion, not simple rename)
    # client_tenure_months -> client_tenure_days is handled separately
}

# Date columns: upload name -> internal name (days-ago integer)
_DATE_COLUMN_MAP: Dict[str, str] = {
    "last_login_date":      "login_days_ago",
    "last_deposit_date":    "last_deposit_days_ago",
    "last_withdrawal_date": "last_withdrawal_days_ago",
}

# Numeric columns that should be coerced to numeric types
_NUMERIC_COLS: List[str] = [
    "lifetime_deposits",
    "net_deposits",
    "current_equity",
    "equity_30d_ago",
    "login_days_ago",
    "last_deposit_days_ago",
    "last_withdrawal_days_ago",
    "withdrawal_amount_last_30d",
    "trading_volume_last_30d",
    "trading_volume_previous_30d",
    "volume_90d_ago",
    "number_of_redeposits",
    "complaints_last_30d",
    "open_tickets",
    "spread_commission_revenue",
    "commission_revenue",
    "swap_revenue",
    "captured_client_losses",
    "net_company_pnl",
    "company_pnl_from_client",
    "client_tenure_days",
    "total_deposits_count",
]

# Default fill values for optional columns
_DEFAULTS: Dict[str, Any] = {
    "ib_name":                    "No IB",
    "account_type":               "Standard",
    "number_of_redeposits":       0,
    "open_tickets":               0,
    "complaints_last_30d":        0,
    "withdrawal_amount_last_30d": 0.0,
    "spread_commission_revenue":  0.0,
    "commission_revenue":         0.0,
    "swap_revenue":               0.0,
    "captured_client_losses":     0.0,
    "last_withdrawal_days_ago":   365,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dates_to_days_ago(df: pd.DataFrame) -> pd.DataFrame:
    """Convert date string columns to integer days-ago columns."""
    today = pd.Timestamp(date.today())
    for date_col, days_col in _DATE_COLUMN_MAP.items():
        if date_col in df.columns:
            parsed = pd.to_datetime(df[date_col], errors="coerce")
            df[days_col] = (today - parsed).dt.days.clip(lower=0)
            df.drop(columns=[date_col], inplace=True)
    return df


def _derive_account_status(login_days: pd.Series) -> pd.Series:
    """Categorise clients as Active / Dormant / Inactive based on login recency."""
    conditions = [
        login_days < 30,
        (login_days >= 30) & (login_days <= 90),
        login_days > 90,
    ]
    choices = ["Active", "Dormant", "Inactive"]
    return np.select(conditions, choices, default="Inactive")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def map_upload(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform an upload-style DataFrame to the internal schema.

    Steps (in order):
      1. Deep copy
      2. Track original columns
      3. Rename upload columns to internal names
      4. Convert date columns to days-ago integers
      5. Convert client_tenure_months -> client_tenure_days (×30)
      6. Fill missing columns with defaults
      7. Coerce numeric columns
      8. Derive missing derived columns
      9. Return mapped DataFrame
    """
    # 1. Deep copy
    df = df.copy(deep=True)

    # 2. Track original columns (before any renames)
    original_cols = set(df.columns)

    # 3. Apply column renames
    df.rename(columns=UPLOAD_COLUMN_MAP, inplace=True)

    # 4. Convert date strings -> days-ago integers
    df = _dates_to_days_ago(df)

    # 5. client_tenure_months -> client_tenure_days
    if "client_tenure_months" in df.columns and "client_tenure_days" not in df.columns:
        df["client_tenure_days"] = pd.to_numeric(
            df["client_tenure_months"], errors="coerce"
        ).fillna(0) * 30
        df.drop(columns=["client_tenure_months"], inplace=True)

    # 6. Fill missing optional columns with defaults
    for col, default_val in _DEFAULTS.items():
        if col not in df.columns:
            df[col] = default_val

    # 8. Coerce numeric columns
    for col in _NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 9. Derive missing computed columns
    # net_deposits: if not in original upload, estimate as 70% of lifetime_deposits
    if "net_deposits" not in original_cols and "net_deposits" not in df.columns:
        df["net_deposits"] = df.get("lifetime_deposits", pd.Series(0.0, index=df.index)) * 0.7

    # equity_30d_ago: random variation around current_equity
    if "equity_30d_ago" not in df.columns and "current_equity" in df.columns:
        rng = np.random.default_rng(seed=42)
        factors = rng.uniform(0.9, 1.1, size=len(df))
        df["equity_30d_ago"] = df["current_equity"] * factors

    # trading_volume_previous_30d
    if "trading_volume_previous_30d" not in df.columns and "trading_volume_last_30d" in df.columns:
        df["trading_volume_previous_30d"] = df["trading_volume_last_30d"].copy()

    # volume_90d_ago
    if "volume_90d_ago" not in df.columns and "trading_volume_last_30d" in df.columns:
        df["volume_90d_ago"] = df["trading_volume_last_30d"].copy()

    # net_company_pnl
    if "net_company_pnl" not in df.columns and "company_pnl_from_client" in df.columns:
        df["net_company_pnl"] = df["company_pnl_from_client"].copy()

    # total_deposits_count
    if "total_deposits_count" not in df.columns:
        redeposits = df.get(
            "number_of_redeposits", pd.Series(0, index=df.index)
        ).fillna(0)
        df["total_deposits_count"] = redeposits + 1

    # account_status from login_days_ago
    if "account_status" not in df.columns and "login_days_ago" in df.columns:
        df["account_status"] = _derive_account_status(
            df["login_days_ago"].fillna(999)
        )

    # Ensure client_tenure_days exists
    if "client_tenure_days" not in df.columns:
        df["client_tenure_days"] = 0

    return df


def map_crm_response(crm_data: dict) -> pd.DataFrame:
    """
    Merge CRM response tables (clients + sub-tables joined on client_id)
    into a single DataFrame, then apply map_upload.

    crm_data expected keys: "clients" (list/dict), optionally others.
    """
    clients = crm_data.get("clients", [])
    if isinstance(clients, dict):
        clients = list(clients.values())

    df = pd.DataFrame(clients) if clients else pd.DataFrame()

    # Merge any additional tables on client_id
    for key, records in crm_data.items():
        if key == "clients":
            continue
        if isinstance(records, list) and records:
            sub_df = pd.DataFrame(records)
            if "client_id" in sub_df.columns and "client_id" in df.columns:
                # Avoid duplicating columns already in df
                overlap = [
                    c for c in sub_df.columns
                    if c != "client_id" and c in df.columns
                ]
                sub_df = sub_df.drop(columns=overlap)
                df = df.merge(sub_df, on="client_id", how="left")

    return map_upload(df)


def map_holistics_response(records: list) -> pd.DataFrame:
    """
    Convert a flat list of Holistics record dicts to the internal schema.
    """
    df = pd.DataFrame(records) if records else pd.DataFrame()
    return map_upload(df)
