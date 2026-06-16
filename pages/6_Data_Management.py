# pages/6_Data_Management.py  —  Data source configuration, upload, quality monitoring

import streamlit as st
import pandas as pd
import datetime
import io

st.set_page_config(
    page_title="Data Management",
    page_icon="📂",
    layout="wide",
)

from utils.helpers import (
    apply_theme, load_data, page_header, fmt_currency,
    GOLD, RED, GREEN, AMBER, BLUE, PURPLE, MUTED,
    get_colors,
)
from utils.session_init import init_session_state
from utils.auth import require_login
from utils.permissions import require_page_access

apply_theme()
init_session_state()
user = require_login()
require_page_access(user, "Data Management")
C = get_colors()
page_header(
    "📂 Data Management",
    "Configure data sources · upload client data · monitor refresh schedule · data quality",
)

import utils.data_manager as dm

# Check if a scheduled refresh is due on this page load
dm.check_and_refresh()

# ── Status Overview ───────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Data Source Status</h4>", unsafe_allow_html=True)

last_refresh = dm.get_last_refresh()
quality      = dm.get_quality_score()
src_label    = dm.get_data_source_label()
rec_count    = dm.get_records_count()
interval     = st.session_state.get("refresh_interval", "manual")
next_rt      = st.session_state.get("next_refresh_time")

quality_color = GREEN if quality >= 80 else (AMBER if quality >= 60 else RED)

s1, s2, s3, s4, s5 = st.columns(5)
s1.metric("Current Source",    src_label)
s2.metric("Last Refresh",      last_refresh.strftime("%d %b %H:%M") if last_refresh else "Never")
s3.metric("Records Loaded",    f"{rec_count:,}")
s4.metric("Data Quality",      f"{quality}/100")
s5.metric(
    "Next Refresh",
    next_rt.strftime("%d %b %H:%M") if next_rt else "Manual only",
)

st.divider()

# ── Data Source Tabs ──────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Select Data Source</h4>", unsafe_allow_html=True)
st.caption("Switch between built-in sample data, a manual upload, or an automated CRM / Holistics feed.")

tab_sample, tab_upload, tab_crm, tab_holistics = st.tabs([
    "📊 Sample Data",
    "📁 Excel / CSV Upload",
    "🔌 CRM API",
    "🤖 Holistics Feed",
])

# ── Sample Data ───────────────────────────────────────────────────────────────
with tab_sample:
    st.markdown(f"<h5 style='color:{GOLD}'>Built-in Sample Dataset</h5>", unsafe_allow_html=True)
    st.info(
        "300 realistic fake brokerage clients generated using the Faker library. "
        "All scores and rules are fully functional. Use this source to explore the "
        "platform before connecting real data."
    )
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown("""
| Field | Details |
|-------|---------|
| Clients | 300 fake accounts |
| Book types | A-Book (30%), B-Book (50%), M-Book (20%) |
| Countries | 30 countries across MENA, Africa, Europe, Asia |
| Account Managers | 10 named managers |
| Scoring | All 6 scores computed from rules engine |
        """)
    with c2:
        if st.button("🔄 Reload Sample Data", type="primary", key="reload_sample"):
            with st.spinner("Generating 300 clients and scoring…"):
                dm.activate_sample_data()
            st.success("Sample data reloaded. All scores recalculated.")
            st.rerun()

        if dm.get_data_source() == "sample":
            st.markdown(
                f"<div style='background:{C['card']};border:1px solid #F0B429;border-radius:8px;"
                f"padding:12px;margin-top:8px;text-align:center'>"
                f"<b style='color:{GOLD}'>✓ Currently Active</b></div>",
                unsafe_allow_html=True,
            )

# ── Excel / CSV Upload ────────────────────────────────────────────────────────
with tab_upload:
    st.markdown(f"<h5 style='color:{GOLD}'>Manual Excel / CSV Upload</h5>", unsafe_allow_html=True)
    st.caption(
        "Upload a single unified client intelligence file. "
        "The file should contain one row per client with the columns listed below."
    )

    from integrations.data_validator import validate_upload
    from integrations.data_mapper import map_upload

    uploaded_file = st.file_uploader(
        "Drag and drop your client data file here",
        type=["xlsx", "csv"],
        accept_multiple_files=False,
        help="Single .xlsx or .csv file. Max recommended size: 10,000 rows.",
    )

    if uploaded_file is not None:
        # ── Read file ──────────────────────────────────────────────────────────
        try:
            if uploaded_file.name.endswith(".csv"):
                raw_df = pd.read_csv(uploaded_file)
            else:
                raw_df = pd.read_excel(uploaded_file, engine="openpyxl")
        except Exception as e:
            st.error(f"Could not read file: {e}")
            raw_df = None

        if raw_df is not None:
            st.divider()
            st.markdown(f"<h5 style='color:{GOLD}'>Validation Results — {uploaded_file.name}</h5>",
                        unsafe_allow_html=True)

            # ── Validate ──────────────────────────────────────────────────────
            report = validate_upload(raw_df)
            qscore = report["quality_score"]
            qcolor = GREEN if qscore >= 80 else (AMBER if qscore >= 60 else RED)

            v1, v2, v3, v4 = st.columns(4)
            v1.metric("Records Found",      f"{report['total_records']:,}")
            v2.metric("Missing Columns",    len(report["missing_columns"]))
            v3.metric("Duplicate Clients",  report["duplicate_clients"])
            v4.metric("Quality Score",      f"{qscore}/100")

            # Errors (fatal)
            if report["errors"]:
                for err in report["errors"]:
                    st.error(f"❌ {err}")

            # Warnings
            if report["warnings"]:
                with st.expander(f"⚠️ {len(report['warnings'])} warning(s) found", expanded=True):
                    for w in report["warnings"]:
                        st.warning(w)
            else:
                st.success("✅ No issues found — file structure looks good.")

            # Missing columns detail
            if report["missing_columns"]:
                st.markdown(
                    f"<b style='color:{RED}'>Missing required columns:</b> "
                    + ", ".join(f"`{c}`" for c in report["missing_columns"]),
                    unsafe_allow_html=True,
                )

            st.divider()

            # ── Data Preview ──────────────────────────────────────────────────
            st.markdown(f"<h5 style='color:{GOLD}'>Data Preview (first 100 rows)</h5>",
                        unsafe_allow_html=True)
            st.dataframe(raw_df.head(100), use_container_width=True)

            st.divider()

            # ── Activate Button ───────────────────────────────────────────────
            can_activate = len(report["errors"]) == 0

            if can_activate:
                col_act, col_msg = st.columns([1, 2])
                with col_act:
                    if st.button(
                        "✅ Activate This Dataset",
                        type="primary",
                        key="activate_upload",
                        help="Map columns, score all clients, and make this the active data source.",
                    ):
                        with st.spinner("Mapping columns, computing derived fields, scoring…"):
                            try:
                                mapped_df = map_upload(raw_df)
                                dm.activate_upload(mapped_df, uploaded_file.name)
                                st.success(
                                    f"Dataset activated! {len(mapped_df):,} clients loaded "
                                    f"and scored. All dashboards updated."
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Activation failed: {e}")
                with col_msg:
                    st.info(
                        "Activating will: map upload columns → internal schema, "
                        "compute all 6 scores, and refresh every page."
                    )
            else:
                st.error(
                    "Fix the errors above before activating. "
                    "Ensure all required columns are present."
                )

    else:
        # Column guide — BI Export Specification (v2.0)
        st.markdown(
            f"<h5 style='color:{GOLD}'>Upload Column Reference — BI Export Specification</h5>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Your upload file should include the columns below, organised by BI export section. "
            "**Required** (✅) columns must be present; **Recommended** (Rec) columns "
            "significantly improve scoring accuracy; optional (—) columns add filtering context."
        )

        def _col_table(data: dict) -> None:
            st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)

        # 1. Identity
        st.markdown(f"<h6 style='color:{GOLD}'>1. Identity Fields</h6>", unsafe_allow_html=True)
        _col_table({
            "Column Name": [
                "client_id", "client_name", "country", "book_type",
                "account_manager", "ib_name", "account_type",
            ],
            "Required": ["✅", "✅", "✅", "✅", "—", "—", "—"],
            "Description": [
                "Unique client identifier (string, e.g. CR10001)",
                "Full client name",
                "Country of residence",
                "Book type: A-Book / B-Book / M-Book (controls profitability formula)",
                "Assigned account manager name (filtering and reporting only)",
                "Introducing broker name (filtering and reporting only)",
                "Account type: Classic / Prime / Islamic (informational only — not used in scoring)",
            ],
        })

        # 2. Snapshot
        st.markdown(f"<h6 style='color:{GOLD}'>2. Snapshot Fields</h6>", unsafe_allow_html=True)
        _col_table({
            "Column Name": ["lifetime_deposits", "current_equity", "equity_30d_ago", "net_deposits"],
            "Required": ["✅", "✅", "Rec", "Rec"],
            "Description": [
                "Total deposits since account opened ($) — core value signal",
                "Current account balance ($) — core value and risk signal",
                "Equity 30 days ago ($) — enables equity trend signal",
                "Lifetime deposits minus total withdrawals ($) — equity erosion signal",
            ],
        })

        # 3. 30-day behavioural
        st.markdown(
            f"<h6 style='color:{GOLD}'>3. 30-Day Behavioural Fields</h6>",
            unsafe_allow_html=True,
        )
        _col_table({
            "Column Name": [
                "last_login_date", "last_deposit_date", "trading_volume_30d",
                "last_withdrawal_date", "withdrawals_30d", "complaints", "open_tickets",
            ],
            "Required": ["✅", "✅", "✅", "Rec", "Rec", "Rec", "Rec"],
            "Description": [
                "Date of last login (YYYY-MM-DD) — converted to login_days_ago internally",
                "Date of last deposit (YYYY-MM-DD) — converted to last_deposit_days_ago internally",
                "Trading volume in last 30 days ($) — primary activity signal",
                "Date of last withdrawal (YYYY-MM-DD) — enables withdrawal timing signal",
                "Withdrawal amount in last 30 days ($) — strongest churn signal (weight 12)",
                "Number of complaints in last 30 days — risk signal (weight 5)",
                "Number of open support tickets — risk signal",
            ],
        })

        # 4. Previous 30-day comparison
        st.markdown(
            f"<h6 style='color:{GOLD}'>4. Previous 30-Day Comparison</h6>",
            unsafe_allow_html=True,
        )
        _col_table({
            "Column Name": ["trading_volume_previous_30d"],
            "Required": ["Rec"],
            "Description": [
                "Trading volume in the prior 30-day period ($) — enables volume drop signal (weight 10)",
            ],
        })

        # 5. 90-day trend
        st.markdown(f"<h6 style='color:{GOLD}'>5. 90-Day Trend Fields</h6>", unsafe_allow_html=True)
        _col_table({
            "Column Name": ["volume_90d_ago"],
            "Required": ["Rec"],
            "Description": [
                "Trading volume 90 days ago ($) — used in upside potential scoring",
            ],
        })

        # 6. Lifetime fields
        st.markdown(f"<h6 style='color:{GOLD}'>6. Lifetime Fields</h6>", unsafe_allow_html=True)
        _col_table({
            "Column Name": ["number_of_redeposits", "client_tenure_months"],
            "Required": ["Rec", "Rec"],
            "Description": [
                "Total number of redeposits made (count) — value and reactivation signal",
                "Client tenure in months — converted to client_tenure_days (×30) internally",
            ],
        })

        # 7. Profitability fields
        st.markdown(
            f"<h6 style='color:{GOLD}'>7. Profitability Fields</h6>", unsafe_allow_html=True
        )
        _col_table({
            "Column Name": [
                "commission_revenue", "spread_revenue", "swap_revenue",
                "captured_client_losses", "company_pnl",
            ],
            "Required": ["Rec", "Rec", "Rec", "Rec", "—"],
            "Description": [
                "Commission revenue from client ($/month) — all book types",
                "Spread revenue from client ($/month) — A-Book profitability only",
                "Swap revenue from client ($/month) — all book types",
                "Captured client losses ($/month) — B-Book and M-Book profitability",
                "Total company P&L from client ($) — alternative to individual revenue fields",
            ],
        })

        # ── Download Template ──────────────────────────────────────────────────
        # 27 columns matching the 7 BI export spec sections above
        all_cols = [
            # 1. Identity (7)
            "client_id", "client_name", "country", "book_type",
            "account_manager", "ib_name", "account_type",
            # 2. Snapshot (4)
            "lifetime_deposits", "current_equity", "equity_30d_ago", "net_deposits",
            # 3. 30-day behavioural (7)
            "last_login_date", "last_deposit_date", "trading_volume_30d",
            "last_withdrawal_date", "withdrawals_30d", "complaints", "open_tickets",
            # 4. Previous 30-day (1)
            "trading_volume_previous_30d",
            # 5. 90-day trend (1)
            "volume_90d_ago",
            # 6. Lifetime (2)
            "number_of_redeposits", "client_tenure_months",
            # 7. Profitability (5)
            "commission_revenue", "spread_revenue", "swap_revenue",
            "captured_client_losses", "company_pnl",
        ]
        template_df = pd.DataFrame(columns=all_cols)
        template_df.loc[0] = [
            # 1. Identity (7)
            "CR10001", "John Smith", "UAE", "B-Book",
            "Sarah Johnson", "Gulf Traders IB", "Prime",
            # 2. Snapshot (4)
            "25000", "16500", "17200", "18000",
            # 3. 30-day behavioural (7)
            "2026-06-01", "2026-05-15", "120000",
            "2026-04-20", "2000", "1", "0",
            # 4. Previous 30-day (1)
            "95000",
            # 5. 90-day trend (1)
            "85000",
            # 6. Lifetime (2)
            "5", "18",
            # 7. Profitability (5)
            "24", "80", "35", "500", "1200",
        ]
        buf = io.BytesIO()
        template_df.to_excel(buf, index=False, engine="openpyxl")
        st.download_button(
            "⬇️ Download Excel Template",
            data=buf.getvalue(),
            file_name="client_intelligence_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ── CRM API ───────────────────────────────────────────────────────────────────
with tab_crm:
    st.markdown(f"<h5 style='color:{GOLD}'>CRM REST API Integration</h5>", unsafe_allow_html=True)
    st.caption(
        "Connect directly to your CRM system. The application will fetch client profiles, "
        "trading metrics, deposit history, and support tickets automatically."
    )

    from integrations.crm_connector import CRMConnector

    c1, c2 = st.columns(2)
    with c1:
        crm_url  = st.text_input("CRM Base URL",  value=st.session_state.get("crm_url", ""),
                                  placeholder="https://crm.example.com/api/v1",
                                  key="crm_url_input")
        crm_key  = st.text_input("API Key",       value="",
                                  type="password", placeholder="sk-xxxx…",
                                  key="crm_key_input")
    with c2:
        crm_user = st.text_input("Username (OAuth)", value="",
                                  placeholder="admin@company.com", key="crm_user_input")
        crm_pass = st.text_input("Password (OAuth)", value="",
                                  type="password", placeholder="••••••••", key="crm_pass_input")

    st.caption("⚠️ Credentials are stored in session only — never persisted to disk.")

    btn1, btn2, btn3 = st.columns(3)
    with btn1:
        if st.button("🔍 Test Connection", key="test_crm"):
            conn = CRMConnector(base_url=crm_url or None, api_key=crm_key or None)
            result = conn.test_connection()
            if result["connected"]:
                st.success(f"✅ Connected: {result['message']}")
            else:
                st.warning(f"⚠️ {result['message']}")

    with btn2:
        if st.button("🧪 Load CRM Sample (20 clients)", key="crm_sample"):
            with st.spinner("Generating CRM mock response and scoring…"):
                dm.activate_crm_sample()
            st.success("CRM sample loaded! 20 mock clients activated.")
            st.rerun()

    with btn3:
        if st.button("⬇️ Fetch from CRM", type="primary", key="fetch_crm", disabled=True):
            st.info("Configure CRM credentials to enable live fetch.")

    st.divider()
    st.markdown(f"<h5 style='color:{GOLD}'>Integration Architecture</h5>", unsafe_allow_html=True)
    st.markdown("""
**File:** `integrations/crm_connector.py`

The connector fetches data from these CRM endpoints and merges them into a single client dataset:

| Method | Endpoint | Data Returned |
|--------|----------|---------------|
| `get_clients()` | `/clients` | Profile, country, account manager |
| `get_trading_metrics()` | `/trading/summary` | Volume 30d, volume prev 30d |
| `get_deposits()` | `/deposits/summary` | Lifetime deposits, last deposit date |
| `get_withdrawals()` | `/withdrawals/summary` | Total withdrawals, last withdrawal |
| `get_activity_metrics()` | `/activity` | Last login date, account status |
| `get_profitability_metrics()` | `/profitability` | Spread, commission, swap, PnL |
| `get_tickets()` | `/support/tickets` | Open tickets, complaint count |

All responses are merged on `client_id` and passed through `data_mapper.map_crm_response()`.
    """)

# ── Holistics Feed ────────────────────────────────────────────────────────────
with tab_holistics:
    st.markdown(f"<h5 style='color:{GOLD}'>Holistics Automated Data Feed</h5>", unsafe_allow_html=True)
    st.caption(
        "Holistics exports a unified client intelligence dataset via its REST API. "
        "Configure once — the application pulls automatically on your chosen schedule."
    )

    from integrations.holistics_connector import HolisticsConnector

    h1, h2 = st.columns(2)
    with h1:
        h_url = st.text_input(
            "Holistics Base URL",
            value=st.session_state.get("holistics_url", ""),
            placeholder="https://app.holistics.io/api/v2",
            key="h_url_input",
        )
        h_key = st.text_input(
            "API Key",
            value="",
            type="password",
            placeholder="holistics-api-key…",
            key="h_key_input",
        )
    with h2:
        h_ds_id = st.text_input(
            "Dataset ID",
            value=st.session_state.get("holistics_dataset_id", ""),
            placeholder="12345",
            key="h_dsid_input",
        )
        st.caption(
            "Find the Dataset ID in Holistics → Datasets → your client "
            "intelligence dataset → Settings → API."
        )

    hb1, hb2, hb3 = st.columns(3)
    with hb1:
        if st.button("🔍 Test Connection", key="test_holistics"):
            conn = HolisticsConnector(
                base_url=h_url or None,
                api_key=h_key or None,
                dataset_id=h_ds_id or None,
            )
            result = conn.test_connection()
            if result["connected"]:
                st.success(f"✅ Connected: {result['message']}")
            else:
                st.warning(f"⚠️ {result['message']}")

    with hb2:
        if st.button("🧪 Load Holistics Sample (20 clients)", key="holistics_sample"):
            with st.spinner("Generating Holistics mock response and scoring…"):
                dm.activate_holistics_sample()
            st.success("Holistics sample loaded! 20 mock clients activated.")
            st.rerun()

    with hb3:
        if st.button("⬇️ Fetch from Holistics", type="primary", key="fetch_holistics", disabled=True):
            st.info("Configure Holistics credentials to enable live fetch.")

    st.divider()
    st.markdown(f"<h5 style='color:{GOLD}'>How the Holistics Integration Works</h5>",
                unsafe_allow_html=True)
    st.markdown("""
**File:** `integrations/holistics_connector.py`

**Long-term setup (your target architecture):**

```
Holistics dataset (scheduled export)
    ↓  Daily at 06:00
    GET /api/v2/datasets/{id}/export
    ↓
data_mapper.map_holistics_response()
    ↓  Maps columns, converts dates to days-ago, derives missing fields
Unified Internal Schema
    ↓
rules_engine.score_*()
    ↓  Applies JSON band rules
All 6 Scores + Labels + Actions
    ↓
Dashboard refreshes automatically
```

**Steps to activate:**
1. Create a Holistics dataset that exports all client fields in the upload format
2. Enter your API key and Dataset ID above
3. Set refresh schedule to "Daily"
4. The application fetches and scores automatically — no manual uploads required
    """)

st.divider()

# ── Refresh Schedule ──────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Refresh Schedule</h4>", unsafe_allow_html=True)
st.caption(
    "Choose how often the application re-fetches data from the active source. "
    "For Sample Data and Upload, 'Manual' is recommended. "
    "For CRM and Holistics, set 'Daily' for the automated feed."
)

rc1, rc2 = st.columns([2, 1])
with rc1:
    schedule_choice = st.radio(
        "Refresh Frequency",
        options=["manual", "hourly", "6h", "daily"],
        format_func=lambda x: {
            "manual": "Manual Only (refresh on demand)",
            "hourly": "Every Hour",
            "6h":     "Every 6 Hours",
            "daily":  "Daily (recommended for CRM / Holistics)",
        }[x],
        index=["manual", "hourly", "6h", "daily"].index(
            st.session_state.get("refresh_interval", "manual")
        ),
        key="schedule_radio",
        horizontal=False,
    )
    if st.button("Apply Refresh Schedule", key="apply_schedule"):
        dm.schedule_refresh(schedule_choice)
        st.success(f"Schedule set to: {schedule_choice}")
        st.rerun()

with rc2:
    last_r   = dm.get_last_refresh()
    next_r   = st.session_state.get("next_refresh_time")
    q_report = dm.get_quality_report()
    duration = st.session_state.get("last_refresh_duration_s", "—")

    st.markdown(f"<div style='background:{C['card']};border:1px solid {C['border']};border-radius:8px;padding:16px'>", unsafe_allow_html=True)
    st.markdown(f"**Last Successful Refresh**  \n{last_r.strftime('%d %b %Y · %H:%M') if last_r else 'Never'}")
    st.markdown(f"**Next Scheduled Refresh**  \n{next_r.strftime('%d %b %Y · %H:%M') if next_r else 'Not scheduled'}")
    st.markdown(f"**Records Loaded**  \n{dm.get_records_count():,}")
    st.markdown("</div>", unsafe_allow_html=True)

    if dm.get_data_source() in ("crm", "holistics"):
        st.button("🔄 Refresh Now", type="primary", key="manual_refresh_now",
                  on_click=lambda: dm.activate_crm_sample()
                  if dm.get_data_source() == "crm"
                  else dm.activate_holistics_sample())

st.divider()

# ── Data Quality Dashboard ────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Data Quality Dashboard</h4>", unsafe_allow_html=True)

q_report = dm.get_quality_report()
qscore   = dm.get_quality_score()
qcolor   = GREEN if qscore >= 80 else (AMBER if qscore >= 60 else RED)

# Quality score big display
qs_col, qd_col = st.columns([1, 3])
with qs_col:
    st.markdown(
        f"<div style='background:{C['card']};border:2px solid {qcolor};border-radius:12px;"
        f"padding:24px;text-align:center'>"
        f"<div style='font-size:48px;font-weight:700;color:{qcolor}'>{qscore}</div>"
        f"<div style='color:{C['muted']};font-size:14px'>Quality Score / 100</div>"
        f"<div style='color:{qcolor};font-size:12px;margin-top:4px'>"
        f"{'Excellent' if qscore >= 80 else 'Needs Attention' if qscore >= 60 else 'Poor — fix issues'}"
        f"</div></div>",
        unsafe_allow_html=True,
    )

with qd_col:
    if q_report:
        qm1, qm2, qm3, qm4 = st.columns(4)
        qm1.metric("Missing Columns",   len(q_report.get("missing_columns", [])))
        qm2.metric("Duplicate Clients", q_report.get("duplicate_clients", 0))
        qm3.metric("Invalid Book Types",q_report.get("invalid_book_types", 0))
        qm4.metric("Total Records",     f"{q_report.get('total_records', 0):,}")

        # Null counts table
        null_c = q_report.get("null_counts", {})
        neg_c  = q_report.get("negative_values", {})
        if null_c or neg_c:
            issues_rows = []
            for col, cnt in null_c.items():
                issues_rows.append({"Issue Type": "Null Value", "Column": col, "Count": cnt})
            for col, cnt in neg_c.items():
                issues_rows.append({"Issue Type": "Negative Value", "Column": col, "Count": cnt})
            miss = q_report.get("missing_columns", [])
            for col in miss:
                issues_rows.append({"Issue Type": "Missing Column", "Column": col, "Count": "—"})
            if issues_rows:
                st.dataframe(pd.DataFrame(issues_rows), hide_index=True, use_container_width=True)
        else:
            st.success("✅ No data quality issues detected in the current dataset.")

        # Errors and warnings from last validation
        errors   = q_report.get("errors", [])
        warnings = q_report.get("warnings", [])
        if errors:
            with st.expander(f"❌ {len(errors)} error(s)", expanded=True):
                for e in errors:
                    st.error(e)
        if warnings:
            with st.expander(f"⚠️ {len(warnings)} warning(s)"):
                for w in warnings:
                    st.warning(w)
    else:
        st.info("Load a dataset to see the quality report.")

st.divider()

# ── Integration Configuration (Persistent) ────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Integration Configuration</h4>",
            unsafe_allow_html=True)
st.caption("Save your CRM and Holistics credentials. Stored in the local SQLite database — never sent anywhere.")

from utils.snapshot_db import init_db, save_config, get_config, get_refresh_log, snapshot_summary
init_db()

cfg_tab_crm, cfg_tab_hol = st.tabs(["CRM API Settings", "Holistics Settings"])

with cfg_tab_crm:
    ic1, ic2 = st.columns(2)
    with ic1:
        saved_crm_url = get_config("crm_base_url")
        saved_crm_key = get_config("crm_api_key")
        new_crm_url = st.text_input("CRM Base URL", value=saved_crm_url,
                                     placeholder="https://crm.example.com/api/v1",
                                     key="cfg_crm_url")
        new_crm_key = st.text_input("CRM API Key", value=saved_crm_key,
                                     type="password", placeholder="sk-xxxx…",
                                     key="cfg_crm_key")
    with ic2:
        saved_crm_user = get_config("crm_username")
        new_crm_user   = st.text_input("CRM Username (OAuth)", value=saved_crm_user,
                                        placeholder="admin@company.com", key="cfg_crm_user")
        crm_auth_method = st.selectbox("Auth Method", ["API Key", "OAuth 2.0"],
                                        key="cfg_crm_auth")
        crm_status = "🟢 Connected" if get_config("crm_last_sync") else "🔴 Not Connected"
        st.caption(f"**Status:** {crm_status}")
        if get_config("crm_last_sync"):
            st.caption(f"**Last Sync:** {get_config('crm_last_sync')}")

    if st.button("Save CRM Configuration", key="save_crm_cfg"):
        if new_crm_url:  save_config("crm_base_url",  new_crm_url)
        if new_crm_key:  save_config("crm_api_key",   new_crm_key)
        if new_crm_user: save_config("crm_username",  new_crm_user)
        save_config("crm_auth_method", crm_auth_method)
        st.success("CRM configuration saved to local database.")

with cfg_tab_hol:
    ih1, ih2 = st.columns(2)
    with ih1:
        saved_h_url = get_config("holistics_base_url")
        saved_h_key = get_config("holistics_api_key")
        new_h_url = st.text_input("Holistics Base URL", value=saved_h_url,
                                   placeholder="https://app.holistics.io/api/v2",
                                   key="cfg_h_url")
        new_h_key = st.text_input("Holistics API Key", value=saved_h_key,
                                   type="password", placeholder="holistics-key…",
                                   key="cfg_h_key")
    with ih2:
        saved_h_ds  = get_config("holistics_dataset_id")
        new_h_ds    = st.text_input("Dataset ID", value=saved_h_ds,
                                     placeholder="12345", key="cfg_h_ds")
        hol_status  = "🟢 Connected" if get_config("holistics_last_sync") else "🔴 Not Connected"
        st.caption(f"**Status:** {hol_status}")
        if get_config("holistics_last_sync"):
            st.caption(f"**Last Sync:** {get_config('holistics_last_sync')}")

    if st.button("Save Holistics Configuration", key="save_hol_cfg"):
        if new_h_url: save_config("holistics_base_url",   new_h_url)
        if new_h_key: save_config("holistics_api_key",    new_h_key)
        if new_h_ds:  save_config("holistics_dataset_id", new_h_ds)
        st.success("Holistics configuration saved to local database.")

st.divider()

# ── Refresh Log ───────────────────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Refresh History</h4>", unsafe_allow_html=True)
refresh_log = get_refresh_log(limit=10)
if not refresh_log.empty:
    refresh_log["status_icon"] = refresh_log["status"].map(
        {"success": "✅", "failed": "❌"}).fillna("⚠️")
    display_log = refresh_log[["refresh_time","status_icon","data_source",
                               "records_processed","duration_seconds"]].copy()
    display_log.columns = ["Refresh Time","Status","Source","Records","Duration (s)"]
    st.dataframe(display_log, hide_index=True, use_container_width=True)
else:
    st.info("No refresh history yet. Activate a data source to record the first refresh.")

st.divider()

# ── Snapshot Database Status ──────────────────────────────────────────────────
st.markdown(f"<h4 style='color:{GOLD}'>Snapshot Database Status</h4>", unsafe_allow_html=True)
snap_summary = snapshot_summary()
sn1, sn2, sn3, sn4 = st.columns(4)
sn1.metric("Total Snapshots",  f"{snap_summary['total_snapshots']:,}")
sn2.metric("Unique Dates",     snap_summary['unique_dates'])
sn3.metric("Oldest Snapshot",  snap_summary['oldest_date'] or "None")
sn4.metric("Latest Snapshot",  snap_summary['latest_date'] or "None")

st.caption("Location: `data/snapshots.db`  ·  Format: SQLite  ·  Never overwrites — complete audit trail.")

st.divider()

# ── Integration Architecture Summary ──────────────────────────────────────────
with st.expander("Integration Architecture & File Structure", expanded=False):
    st.markdown("""
**Pipeline:**
```
Holistics/CRM/Upload/Sample
    → data_mapper.map_upload()        (column rename + date conversion)
    → integrations.data_validator     (quality score)
    → utils.data_manager              (session state activation)
    → utils.helpers.rescore()         (scoring engine)
    → utils.rules_engine              (band rules → 6 scores)
    → utils.snapshot_db.save_snapshot (SQLite snapshot)
    → session_state["scored_df"]      (all dashboards read from here)
```

| File | Purpose |
|------|---------|
| `integrations/crm_connector.py` | REST API connector |
| `integrations/holistics_connector.py` | Holistics dataset export |
| `integrations/data_mapper.py` | Column mapping + derived fields |
| `integrations/data_validator.py` | Quality checks |
| `utils/data_manager.py` | Source switching + scheduling |
| `utils/snapshot_db.py` | SQLite snapshot + outcome storage |
    """)
