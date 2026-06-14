# app.py
# Main entry point for the OneRoyal Client Intelligence Platform.
# Run with: streamlit run app.py

import streamlit as st

# --- Page config must be the FIRST Streamlit call ---
st.set_page_config(
    page_title="OneRoyal Client Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Load data into session state on first run ---
from utils.helpers import load_data, DEFAULT_RISK_WEIGHTS, DEFAULT_VALUE_WEIGHTS, DEFAULT_THRESHOLDS

if "risk_weights"  not in st.session_state:
    st.session_state["risk_weights"]  = DEFAULT_RISK_WEIGHTS.copy()
if "value_weights" not in st.session_state:
    st.session_state["value_weights"] = DEFAULT_VALUE_WEIGHTS.copy()
if "thresholds"    not in st.session_state:
    st.session_state["thresholds"]    = DEFAULT_THRESHOLDS.copy()
if "risk_blend"    not in st.session_state:
    st.session_state["risk_blend"]    = 0.6

# Trigger first data load
load_data()

# --- Sidebar branding ---
st.sidebar.markdown("## 📊 OneRoyal")
st.sidebar.markdown("**Client Intelligence Platform**")
st.sidebar.divider()
st.sidebar.markdown("Navigate using the pages in the sidebar.")
st.sidebar.divider()

df = st.session_state["scored_df"]
high_risk_threshold = st.session_state["thresholds"]["high_risk"]
critical_priority   = st.session_state["thresholds"]["critical_priority"]

st.sidebar.metric("Total Clients",   len(df))
st.sidebar.metric("High Risk",       int((df["retention_risk_score"] >= high_risk_threshold).sum()))
st.sidebar.metric("Critical Priority", int((df["priority_score"] >= critical_priority).sum()))

# --- Home page content ---
st.title("📊 OneRoyal Client Intelligence Platform")
st.markdown("""
Welcome to the **OneRoyal Client Intelligence Platform** — your central hub for
identifying at-risk clients, prioritising retention actions, and protecting revenue.

---

### How to navigate
Use the **sidebar** on the left to move between pages:

| Page | What it does |
|------|-------------|
| **Executive Dashboard** | High-level KPIs and charts for leadership |
| **Client List** | Full searchable/filterable client table |
| **Scoring Engine** | Adjust scoring weights and see how scores change |
| **Action Center** | Clients needing action right now |
| **Settings** | Change risk/value/priority thresholds |

---

### Quick summary
""")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Clients", len(df))
col2.metric("High Risk Clients",
            int((df["retention_risk_score"] >= high_risk_threshold).sum()))
col3.metric("Critical Priority",
            int((df["priority_score"] >= critical_priority).sum()))
col4.metric("Avg Priority Score",
            f"{df['priority_score'].mean():.1f}")

st.info("💡 Start with the **Executive Dashboard** page to see the full overview.")
