# integrations/data_validator.py
# Validates DataFrames for data quality before and after column mapping.

import pandas as pd
from typing import Dict, List, Any

# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

UPLOAD_REQUIRED_COLUMNS: List[str] = [
    "client_id",
    "client_name",
    "country",
    "book_type",
    "lifetime_deposits",
    "current_equity",
]

INTERNAL_REQUIRED_COLUMNS: List[str] = [
    "client_id",
    "client_name",
    "country",
    "account_manager",
    "ib_name",
    "account_type",
    "book_type",
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
    "account_status",
]

VALID_BOOK_TYPES = {"A-Book", "B-Book", "M-Book"}

# Columns where nulls or negatives matter for scoring
_IMPORTANT_COLS = [
    "lifetime_deposits",
    "current_equity",
    "login_days_ago",
    "last_deposit_days_ago",
    "trading_volume_last_30d",
]

_EQUITY_COLS_UPLOAD = ["current_equity"]
_EQUITY_COLS_INTERNAL = ["current_equity", "net_deposits"]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _null_counts(df: pd.DataFrame, columns: List[str]) -> Dict[str, int]:
    """Return a dict of column -> null count for columns that have at least one null."""
    result: Dict[str, int] = {}
    for col in columns:
        if col in df.columns:
            n = int(df[col].isna().sum())
            if n > 0:
                result[col] = n
    return result


def _negative_counts(df: pd.DataFrame, columns: List[str]) -> Dict[str, int]:
    """Return a dict of column -> count of strictly negative numeric values."""
    result: Dict[str, int] = {}
    for col in columns:
        if col in df.columns:
            numeric = pd.to_numeric(df[col], errors="coerce")
            n = int((numeric < 0).sum())
            if n > 0:
                result[col] = n
    return result


def _compute_quality_score(
    df: pd.DataFrame,
    required_columns: List[str],
    missing_columns: List[str],
    invalid_book_types: int,
    duplicate_clients: int,
    null_counts: Dict[str, int],
    negative_values: Dict[str, int],
) -> int:
    """
    Scoring rubric (starts at 100):
      - -10 per missing required column
      - -min(15, duplicates*2) for duplicate client_ids
      - -min(20, invalid_book_types*2) for invalid book types
      - -min(5, null_pct_in_important_col) per important column with nulls
      - -min(5, negative_equity_count) for negative equity records
    Clamped to [0, 100].
    """
    score = 100
    total = max(len(df), 1)

    # Missing required columns
    score -= len(missing_columns) * 10

    # Duplicate client IDs
    score -= min(15, duplicate_clients * 2)

    # Invalid book types
    score -= min(20, invalid_book_types * 2)

    # Nulls in important columns (as percentage, capped at 5 per col)
    for col in _IMPORTANT_COLS:
        if col in null_counts:
            pct = int((null_counts[col] / total) * 100)
            score -= min(5, pct)

    # Negative equity
    for col, neg in negative_values.items():
        score -= min(5, neg)

    return max(0, min(100, score))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_upload(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate an uploaded DataFrame using upload-style column names.

    Returns a dict with:
        total_records      : int
        missing_columns    : list[str]
        invalid_book_types : int
        duplicate_clients  : int
        null_counts        : dict[str, int]
        negative_values    : dict[str, int]
        quality_score      : int  (0-100)
        errors             : list[str]
        warnings           : list[str]
    """
    errors: List[str] = []
    warnings: List[str] = []

    total_records = int(len(df))

    # Missing required upload columns
    missing_columns: List[str] = [
        col for col in UPLOAD_REQUIRED_COLUMNS if col not in df.columns
    ]
    for col in missing_columns:
        errors.append(f"Required column missing: '{col}'")

    # Duplicate client_ids
    duplicate_clients = 0
    if "client_id" in df.columns:
        duplicate_clients = int(df["client_id"].duplicated().sum())
        if duplicate_clients > 0:
            warnings.append(
                f"{duplicate_clients} duplicate client_id value(s) found — "
                "only the first occurrence will be used."
            )

    # Invalid book types
    invalid_book_types = 0
    if "book_type" in df.columns:
        mask = ~df["book_type"].isin(VALID_BOOK_TYPES) & df["book_type"].notna()
        invalid_book_types = int(mask.sum())
        if invalid_book_types > 0:
            bad = df.loc[mask, "book_type"].unique().tolist()[:5]
            errors.append(
                f"{invalid_book_types} row(s) have invalid book_type values: "
                f"{bad}. Expected one of {sorted(VALID_BOOK_TYPES)}."
            )

    # Null counts across all present required cols + important cols
    check_null_cols = [c for c in UPLOAD_REQUIRED_COLUMNS if c in df.columns]
    null_counts = _null_counts(df, check_null_cols)
    for col, cnt in null_counts.items():
        pct = round(cnt / max(total_records, 1) * 100, 1)
        if pct > 20:
            errors.append(f"Column '{col}' has {cnt} null values ({pct}%).")
        else:
            warnings.append(f"Column '{col}' has {cnt} null values ({pct}%).")

    # Negative equity values
    negative_values = _negative_counts(df, _EQUITY_COLS_UPLOAD)
    for col, cnt in negative_values.items():
        warnings.append(f"Column '{col}' has {cnt} negative value(s).")

    # Quality score
    quality_score = _compute_quality_score(
        df,
        UPLOAD_REQUIRED_COLUMNS,
        missing_columns,
        invalid_book_types,
        duplicate_clients,
        null_counts,
        negative_values,
    )

    return {
        "total_records": total_records,
        "missing_columns": missing_columns,
        "invalid_book_types": invalid_book_types,
        "duplicate_clients": duplicate_clients,
        "null_counts": null_counts,
        "negative_values": negative_values,
        "quality_score": quality_score,
        "errors": errors,
        "warnings": warnings,
    }


def validate_internal(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate an already-mapped internal DataFrame.

    Returns the same structure as validate_upload but checks
    INTERNAL_REQUIRED_COLUMNS.
    """
    errors: List[str] = []
    warnings: List[str] = []

    total_records = int(len(df))

    # Missing required internal columns
    missing_columns: List[str] = [
        col for col in INTERNAL_REQUIRED_COLUMNS if col not in df.columns
    ]
    for col in missing_columns:
        errors.append(f"Required internal column missing: '{col}'")

    # Duplicate client_ids
    duplicate_clients = 0
    if "client_id" in df.columns:
        duplicate_clients = int(df["client_id"].duplicated().sum())
        if duplicate_clients > 0:
            warnings.append(
                f"{duplicate_clients} duplicate client_id value(s) found."
            )

    # Invalid book types
    invalid_book_types = 0
    if "book_type" in df.columns:
        mask = ~df["book_type"].isin(VALID_BOOK_TYPES) & df["book_type"].notna()
        invalid_book_types = int(mask.sum())
        if invalid_book_types > 0:
            bad = df.loc[mask, "book_type"].unique().tolist()[:5]
            errors.append(
                f"{invalid_book_types} row(s) have invalid book_type values: "
                f"{bad}."
            )

    # Null counts across all internal required cols
    check_null_cols = [c for c in INTERNAL_REQUIRED_COLUMNS if c in df.columns]
    null_counts = _null_counts(df, check_null_cols)
    for col, cnt in null_counts.items():
        pct = round(cnt / max(total_records, 1) * 100, 1)
        if pct > 20:
            errors.append(f"Column '{col}' has {cnt} null values ({pct}%).")
        else:
            warnings.append(f"Column '{col}' has {cnt} null values ({pct}%).")

    # Negative values for equity columns
    negative_values = _negative_counts(df, _EQUITY_COLS_INTERNAL)
    for col, cnt in negative_values.items():
        warnings.append(f"Column '{col}' has {cnt} negative value(s).")

    # Quality score
    quality_score = _compute_quality_score(
        df,
        INTERNAL_REQUIRED_COLUMNS,
        missing_columns,
        invalid_book_types,
        duplicate_clients,
        null_counts,
        negative_values,
    )

    return {
        "total_records": total_records,
        "missing_columns": missing_columns,
        "invalid_book_types": invalid_book_types,
        "duplicate_clients": duplicate_clients,
        "null_counts": null_counts,
        "negative_values": negative_values,
        "quality_score": quality_score,
        "errors": errors,
        "warnings": warnings,
    }
