# integrations/holistics_connector.py
# Holistics API placeholder connector.
# Real API integration requires HOLISTICS_BASE_URL, HOLISTICS_API_KEY,
# and HOLISTICS_DATASET_ID environment variables.

import os
import pandas as pd
from datetime import date, timedelta
from typing import Dict, Any


class HolisticsConnector:
    """
    Placeholder connector for the Holistics automated reporting API.
    All data-fetch methods raise NotImplementedError until real credentials
    are configured via environment variables.
    """

    def __init__(
        self,
        base_url: str = None,
        api_key: str = None,
        dataset_id: str = None,
    ):
        self.base_url = base_url or os.environ.get("HOLISTICS_BASE_URL", "")
        self.api_key = api_key or os.environ.get("HOLISTICS_API_KEY", "")
        self.dataset_id = dataset_id or os.environ.get("HOLISTICS_DATASET_ID", "")

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def test_connection(self) -> Dict[str, Any]:
        """
        Test whether Holistics credentials are configured.
        Always returns False (not connected) in this placeholder version.
        """
        if not self.api_key:
            return {
                "connected": False,
                "message": "Configure HOLISTICS_API_KEY environment variable",
            }
        return {
            "connected": False,
            "message": (
                "Holistics API key is set but live connectivity is not "
                "implemented in this version. Use get_sample_response() "
                "to load mock data instead."
            ),
        }

    # ------------------------------------------------------------------
    # Data-fetch endpoints (not yet implemented)
    # ------------------------------------------------------------------

    def fetch_dataset(self) -> pd.DataFrame:
        """
        Fetch the configured Holistics dataset.
        Raises NotImplementedError until real credentials are provided.
        """
        raise NotImplementedError(
            "Configure HOLISTICS_BASE_URL and HOLISTICS_API_KEY, "
            "then set HOLISTICS_DATASET_ID"
        )

    def fetch_all(self) -> pd.DataFrame:
        """
        Fetch all data from the configured Holistics dataset.
        Delegates to fetch_dataset(); raises NotImplementedError if unconfigured.
        """
        return self.fetch_dataset()

    # ------------------------------------------------------------------
    # Mock / sample data
    # ------------------------------------------------------------------

    def get_sample_response(self) -> pd.DataFrame:
        """
        Return a DataFrame of 20 mock clients in upload-style column format
        (the format a user would upload, NOT the internal schema).

        Internal columns are renamed to upload-style names so that the
        result can be fed directly into map_upload().
        """
        from data.sample_data import generate_clients

        df = generate_clients(20)
        today = date.today()

        # Add date string columns derived from days-ago integers
        df["last_login_date"] = df["login_days_ago"].apply(
            lambda d: str(today - timedelta(days=int(d)))
        )
        df["last_deposit_date"] = df["last_deposit_days_ago"].apply(
            lambda d: str(today - timedelta(days=int(d)))
        )
        df["last_withdrawal_date"] = df["last_withdrawal_days_ago"].apply(
            lambda d: str(today - timedelta(days=int(d)))
        )

        # Rename internal column names to upload-style names
        df.rename(
            columns={
                "trading_volume_last_30d":    "trading_volume_30d",
                "spread_commission_revenue":  "spread_revenue",
                "company_pnl_from_client":    "company_pnl",
                "complaints_last_30d":        "complaints",
                "withdrawal_amount_last_30d": "withdrawals_30d",
            },
            inplace=True,
        )

        # Drop raw internal columns that were replaced by date strings
        drop_cols = [
            c for c in ["login_days_ago", "last_deposit_days_ago", "last_withdrawal_days_ago"]
            if c in df.columns
        ]
        df.drop(columns=drop_cols, inplace=True)

        df["_source"] = "Holistics mock data"
        return df
