# utils/session_init.py — Centralized session state initialization

import streamlit as st


def init_session_state():
    """
    Initialize all required session state variables with safe defaults.
    Safe to call on every page load — only sets keys that are missing.
    """
    from utils.helpers import (
        DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS, DEFAULT_PROF_WEIGHTS,
        DEFAULT_REACT_WEIGHTS, DEFAULT_UPSIDE_WEIGHTS, DEFAULT_THRESHOLDS,
    )

    defaults = {
        "theme":            "dark",
        "thresholds":       DEFAULT_THRESHOLDS.copy(),
        "risk_weights":     DEFAULT_RISK_WEIGHTS.copy(),
        "value_weights":    DEFAULT_VALUE_WEIGHTS.copy(),
        "prof_weights":     DEFAULT_PROF_WEIGHTS.copy(),
        "react_weights":    DEFAULT_REACT_WEIGHTS.copy(),
        "upside_weights":   DEFAULT_UPSIDE_WEIGHTS.copy(),
        "data_source":      "sample",
        "data_filename":    None,
        "refresh_interval": "manual",
        "next_refresh_time": None,
        "last_refresh_time": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    if "scoring_rules" not in st.session_state:
        try:
            from utils.rules_engine import load_rules
            st.session_state["scoring_rules"] = load_rules()
        except Exception:
            pass
