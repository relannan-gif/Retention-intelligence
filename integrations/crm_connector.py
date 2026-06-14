# integrations/crm_connector.py
# CRM REST API placeholder connector.
# Real API integration requires CRM_BASE_URL and CRM_API_KEY environment variables.

import os
import pandas as pd
from datetime import date, timedelta
from typing import Dict, Any


class CRMConnector:
    """
    Placeholder connector for a CRM REST API.
    All data-fetch methods raise NotImplementedError until real credentials
    are configured via environment variables.
    """

    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.environ.get("CRM_BASE_URL", "")
        self.api_key = api_key or os.environ.get("CRM_API_KEY", "")
        self.username = os.environ.get("CRM_USERNAME", "")
        self.password = os.environ.get("CRM_PASSWORD", "")

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def test_connection(self) -> Dict[str, Any]:
        """
        Test whether CRM credentials are configured.
        Always returns False (not connected) in this placeholder version.
        """
        if not self.base_url or not self.api_key:
            return {
                "connected": False,
                "message": (
                    "CRM integration not configured. "
                    "Set CRM_BASE_URL and CRM_API_KEY environment variables."
                ),
            }
        return {
            "connected": False,
            "message": (
                "CRM credentials are set but live connectivity is not "
                "implemented in this version. Use get_sample_response() "
                "to load mock data instead."
            ),
        }

    # ------------------------------------------------------------------
    # Auth header
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        """Return HTTP headers with Bearer token authentication."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Data-fetch endpoints (not yet implemented)
    # ------------------------------------------------------------------

    def get_clients(self):
        raise NotImplementedError(
            "Configure CRM_BASE_URL and CRM_API_KEY environment variables"
        )

    def get_trading_metrics(self):
        raise NotImplementedError(
            "Configure CRM_BASE_URL and CRM_API_KEY environment variables"
        )

    def get_deposits(self):
        raise NotImplementedError(
            "Configure CRM_BASE_URL and CRM_API_KEY environment variables"
        )

    def get_withdrawals(self):
        raise NotImplementedError(
            "Configure CRM_BASE_URL and CRM_API_KEY environment variables"
        )

    def get_activity_metrics(self):
        raise NotImplementedError(
            "Configure CRM_BASE_URL and CRM_API_KEY environment variables"
        )

    def get_profitability_metrics(self):
        raise NotImplementedError(
            "Configure CRM_BASE_URL and CRM_API_KEY environment variables"
        )

    def get_tickets(self):
        raise NotImplementedError(
            "Configure CRM_BASE_URL and CRM_API_KEY environment variables"
        )

    def fetch_all(self) -> Dict[str, Any]:
        """
        Attempt to call all data-fetch endpoints and return a combined dict.
        Since all endpoints raise NotImplementedError, this will raise as well.
        """
        return {
            "clients":             self.get_clients(),
            "trading_metrics":     self.get_trading_metrics(),
            "deposits":            self.get_deposits(),
            "withdrawals":         self.get_withdrawals(),
            "activity_metrics":    self.get_activity_metrics(),
            "profitability":       self.get_profitability_metrics(),
            "tickets":             self.get_tickets(),
        }

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

        df["_source"] = "CRM mock data"
        return df
