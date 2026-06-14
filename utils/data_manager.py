# utils/data_manager.py
# Central data source manager for the Retention Intelligence platform.
# Manages switching between sample data, manual uploads, CRM, and Holistics feeds.

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_SOURCE_LABELS: Dict[str, str] = {
    "sample":    "Sample Data (Built-in 300 clients)",
    "upload":    "Manual Excel / CSV Upload",
    "crm":       "CRM API Integration",
    "holistics": "Holistics Automated Feed",
}

REFRESH_INTERVALS: Dict[str, Optional[int]] = {
    "manual":  None,
    "hourly":  60,
    "6h":      360,
    "daily":   1440,
}


# ---------------------------------------------------------------------------
# Source / state accessors
# ---------------------------------------------------------------------------

def get_data_source() -> str:
    """Return the active data source key (defaults to 'sample')."""
    import streamlit as st
    return st.session_state.get("data_source", "sample")


def get_data_source_label() -> str:
    """Return the human-readable label for the active data source."""
    return DATA_SOURCE_LABELS.get(get_data_source(), "Unknown")


def get_last_refresh() -> Optional[datetime]:
    """Return the timestamp of the last data refresh, or None."""
    import streamlit as st
    return st.session_state.get("last_refresh_time")


def get_records_count() -> int:
    """Return the number of records in the current scored DataFrame."""
    import streamlit as st
    df = st.session_state.get("scored_df")
    if df is None:
        return 0
    return int(len(df))


def get_quality_score() -> int:
    """Return the data quality score (0-100) for the current dataset."""
    import streamlit as st
    return st.session_state.get("data_quality_score", 100)


def get_quality_report() -> Dict[str, Any]:
    """Return the full quality report dict for the current dataset."""
    import streamlit as st
    return st.session_state.get("data_quality_report", {})


# ---------------------------------------------------------------------------
# Activation helpers
# ---------------------------------------------------------------------------

def activate_sample_data():
    """Generate 300 built-in sample clients and activate them."""
    from data.sample_data import generate_clients
    raw = generate_clients(300)
    _activate_dataframe(raw, source="sample", filename=None)


def activate_upload(df: pd.DataFrame, filename: str = None):
    """Activate a user-uploaded DataFrame (already mapped to internal schema)."""
    _activate_dataframe(df, source="upload", filename=filename)


def activate_crm_sample():
    """Load the CRM connector's mock sample data and activate it."""
    from integrations.crm_connector import CRMConnector
    from integrations.data_mapper import map_upload

    raw = CRMConnector().get_sample_response()
    mapped = map_upload(raw)
    _activate_dataframe(mapped, source="crm", filename=None)


def activate_holistics_sample():
    """Load the Holistics connector's mock sample data and activate it."""
    from integrations.holistics_connector import HolisticsConnector
    from integrations.data_mapper import map_upload

    raw = HolisticsConnector().get_sample_response()
    mapped = map_upload(raw)
    _activate_dataframe(mapped, source="holistics", filename=None)


# ---------------------------------------------------------------------------
# Refresh scheduling
# ---------------------------------------------------------------------------

def schedule_refresh(interval: str):
    """
    Set the auto-refresh interval for the active data source.

    Parameters
    ----------
    interval : str
        One of the keys in REFRESH_INTERVALS ('manual', 'hourly', '6h', 'daily').
    """
    import streamlit as st

    minutes = REFRESH_INTERVALS.get(interval)
    st.session_state["refresh_interval"] = interval

    if minutes is not None:
        next_refresh = datetime.now() + timedelta(minutes=minutes)
        st.session_state["next_refresh_time"] = next_refresh
    else:
        # Manual mode — clear any scheduled refresh
        st.session_state.pop("next_refresh_time", None)


def check_and_refresh():
    """
    If a scheduled refresh is due, re-run the active source's activate function
    and reschedule the next refresh.
    """
    import streamlit as st

    next_refresh: Optional[datetime] = st.session_state.get("next_refresh_time")
    if next_refresh is None:
        return

    if datetime.now() >= next_refresh:
        source = get_data_source()
        if source == "sample":
            activate_sample_data()
        elif source == "crm":
            activate_crm_sample()
        elif source == "holistics":
            activate_holistics_sample()
        # For 'upload' source, we cannot re-pull from a file automatically;
        # skip silently and wait for user to re-upload.

        # Reschedule
        interval = st.session_state.get("refresh_interval", "manual")
        schedule_refresh(interval)


# ---------------------------------------------------------------------------
# Internal activation core
# ---------------------------------------------------------------------------

def _activate_dataframe(
    raw: pd.DataFrame,
    source: str,
    filename: Optional[str] = None,
):
    """
    Store raw data in session state, run quality validation, and trigger rescoring.

    Parameters
    ----------
    raw      : already-mapped internal-schema DataFrame
    source   : one of 'sample', 'upload', 'crm', 'holistics'
    filename : original upload filename (or None for non-upload sources)
    """
    import streamlit as st
    from integrations.data_validator import validate_internal

    # Persist raw data and metadata
    st.session_state["raw_df"] = raw
    st.session_state["data_source"] = source
    st.session_state["upload_filename"] = filename
    st.session_state["last_refresh_time"] = datetime.now()

    # Run quality validation and store results
    quality_report = validate_internal(raw)
    st.session_state["data_quality_score"] = quality_report.get("quality_score", 100)
    st.session_state["data_quality_report"] = quality_report

    # Trigger rescoring (lazy import to avoid circular dependency)
    from utils.helpers import rescore
    rescore()
