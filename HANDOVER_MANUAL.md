# OneRoyal Client Intelligence Platform
## Operational & Technical Handover Manual

**Version:** 1.0  
**Date:** June 2026  
**Classification:** Internal — Confidential  
**Authors:** Product Owner / Solution Architect  
**Branch:** `claude/oneroyal-client-platform-pfb0lk`

---

## Table of Contents

1. [Executive Summary](#section-1--executive-summary)
2. [Platform Architecture](#section-2--platform-architecture)
3. [Data Requirements](#section-3--data-requirements)
4. [Scoring Engine](#section-4--scoring-engine)
5. [Settings Page Reference](#section-5--settings-page-reference)
6. [Executive Dashboard](#section-6--executive-dashboard)
7. [Client List](#section-7--client-list)
8. [Action Center](#section-8--action-center)
9. [Model Validation](#section-9--model-validation)
10. [Implementation Roadmap](#section-10--implementation-roadmap)
11. [Governance](#section-11--governance)
12. [Operating Manual](#section-12--operating-manual)
13. [Appendices](#section-13--appendices)

---

# SECTION 1 — EXECUTIVE SUMMARY

## 1.1 Purpose of the Platform

The OneRoyal Client Intelligence Platform is an internal retention intelligence and commercial analytics tool that scores every active client across six quantitative dimensions, automatically prioritises them into an actionable queue, and routes specific recommendations to the correct team.

It exists to answer three operational questions in real time:

1. **Who is about to leave?** (Retention Risk Score)
2. **Who is worth the most effort to save?** (Commercial Value Score + Profitability Score)
3. **What exact action should we take, and who should own it?** (Recommended Action + Recommended Owner)

## 1.2 Business Problem Being Solved

Without the platform, client retention at a forex/CFD brokerage is typically managed through manual review, anecdotal account manager knowledge, or basic login-inactivity reports. These approaches share four critical failures:

| Problem | Business Impact |
|---|---|
| No risk scoring across all clients | High-value clients churn undetected |
| No value weighting | Equal effort spent on $500 and $50,000 equity accounts |
| No book-type-aware profitability | A-Book and B-Book clients cannot be compared fairly |
| No systematic action routing | Retention follow-up depends on AM availability, not data |

The platform replaces subjective judgement with a rules-based, quantitative scoring engine operating on the full client population simultaneously.

## 1.3 Intended Users

| Role | Primary Use |
|---|---|
| **Executive Board / Commercial Director** | Executive Dashboard — portfolio health, revenue at risk |
| **Head of Retention** | Action Center — priority queues, AM workload |
| **Account Managers** | Action Center + Client List — individual client detail and action reason |
| **BI / Analytics Team** | Data Management — upload, quality monitoring, integration config |
| **Product / Platform Team** | Settings — weight calibration, threshold adjustment, business rules |
| **Compliance / Risk** | Client List + Model Validation — audit trail, score accountability |

## 1.4 Expected Business Outcomes

| Outcome | Measurable Target |
|---|---|
| Reduce undetected churn | High-risk clients identified 30–60 days before withdrawal |
| Increase retention call conversion | AMs call the right clients; target >40% success rate |
| Prioritise revenue-generating clients | Profitability-first action queue drives ROI on retention effort |
| Identify VIP upgrade candidates | VIP Upside Score surfaces non-VIP clients ready for upgrade |
| Reactivate dormant accounts | Reactivation Score identifies the best win-back candidates |
| Validate model predictive accuracy | Churn prediction target: >75% AUC; withdrawal prediction: >80% AUC |

## 1.5 Current Maturity Level

The platform is currently at **Phase 1 — Pilot / Proof of Concept** with the following capability status:

| Capability | Status |
|---|---|
| 6-score client scoring engine | ✅ Fully implemented |
| Business rules engine (configurable bands) | ✅ Fully implemented |
| 9-segment client matrix | ✅ Fully implemented |
| 11-rule action routing | ✅ Fully implemented |
| Dark/Light theme system | ✅ Fully implemented |
| Historical snapshot database | ✅ Implemented (SQLite) |
| Outcome tracking | ✅ Implemented |
| Model validation page | ✅ Implemented (with simulated data) |
| Real CRM integration | ⚠️ Placeholder only — NotImplementedError |
| Real Holistics integration | ⚠️ Placeholder only — NotImplementedError |
| Production database | ⚠️ SQLite (not suitable for production >10k clients) |
| User authentication | ❌ Not implemented |
| Role-based access control | ❌ Not implemented |
| Automated daily refresh | ⚠️ Manual trigger only |

## 1.6 Current Limitations

1. **Data source**: Operates on 300 synthetic clients. All scoring is fully functional; data is not real.
2. **CRM/Holistics connectors**: Shell implementations with placeholder methods — connection requires OneRoyal BI team to implement the HTTP calls against actual endpoints.
3. **Database**: SQLite file at `data/snapshots.db`. Not suitable for concurrent users or >10,000 clients.
4. **Authentication**: No login screen. Any person with the URL can access all data.
5. **Model validation accuracy**: Currently computed from simulated outcomes correlated to risk scores, not real churn events.
6. **Single-user session state**: Streamlit session state is per-browser session. Settings changes in one session are not visible to other users until they reload.

---

# SECTION 2 — PLATFORM ARCHITECTURE

## 2.1 Application Stack

```
┌────────────────────────────────────────────────────────────────┐
│                    OneRoyal CI Platform                         │
│              Streamlit 1.x  ·  Python 3.11                     │
├────────────────────────────────────────────────────────────────┤
│  PRESENTATION LAYER (pages/)                                    │
│  1_Executive_Dashboard  2_Client_List  3_Scoring_Engine         │
│  4_Action_Center  5_Settings  6_Data_Management  7_Model_Valid  │
├────────────────────────────────────────────────────────────────┤
│  BUSINESS LOGIC LAYER (utils/)                                  │
│  helpers.py  scoring.py  rules_engine.py                        │
│  snapshot_db.py  data_manager.py  session_init.py               │
├────────────────────────────────────────────────────────────────┤
│  CONFIGURATION LAYER (config/)                                  │
│  theme.py  scoring_rules.json                                   │
├────────────────────────────────────────────────────────────────┤
│  INTEGRATION LAYER (integrations/)                              │
│  data_validator.py  data_mapper.py                              │
│  crm_connector.py  holistics_connector.py                       │
├────────────────────────────────────────────────────────────────┤
│  DATA LAYER                                                     │
│  data/sample_data.py  data/snapshots.db (SQLite)               │
└────────────────────────────────────────────────────────────────┘
```

## 2.2 Page Navigation Structure

```
App (app.py / Streamlit)
├── 1_Executive_Dashboard.py   — Board-level KPIs and charts
├── 2_Client_List.py           — Searchable/filterable full client table
├── 3_Scoring_Engine.py        — Score weight sliders and distributions
├── 4_Action_Center.py         — Profitability-first action queue
├── 5_Settings.py              — Thresholds, weights, business rules, theme
├── 6_Data_Management.py       — Data source selection and quality
└── 7_Model_Validation.py      — Model accuracy and retention effectiveness
```

All pages share:
- `utils/session_init.init_session_state()` — called on every page load
- `utils/helpers.apply_theme()` — injects theme CSS
- `utils/helpers.load_data()` — lazy-loads scored DataFrame from session state

## 2.3 Data Flow

```
                    ┌─────────────────────┐
                    │  DATA SOURCE        │
                    │  sample / upload /  │
                    │  crm / holistics    │
                    └──────────┬──────────┘
                               │  raw DataFrame
                               ▼
                    ┌─────────────────────┐
                    │  data_mapper.py     │
                    │  Column rename      │
                    │  Date → days_ago    │
                    │  Derive missing     │
                    └──────────┬──────────┘
                               │  internal schema (46 cols)
                               ▼
                    ┌─────────────────────┐
                    │  data_validator.py  │
                    │  Quality score 0–100│
                    └──────────┬──────────┘
                               │  validated DataFrame
                               ▼
                    ┌─────────────────────┐
                    │  scoring.py         │
                    │  rules_engine.py    │
                    │  6 scores computed  │
                    │  Segmentation       │
                    │  Action routing     │
                    └──────────┬──────────┘
                               │  scored DataFrame (46+ cols)
                               ▼
              ┌────────────────┴────────────────┐
              │    st.session_state["scored_df"] │
              │    (in-memory, per browser)      │
              └────┬───────────┬────────────┬───┘
                   │           │            │
                   ▼           ▼            ▼
            Dashboard    Client List   Action Center
                                            │
                               ┌────────────┘
                               ▼
                    ┌─────────────────────┐
                    │  snapshot_db.py     │
                    │  SQLite snapshots   │
                    │  score history      │
                    │  outcomes/actions   │
                    └─────────────────────┘
```

## 2.4 Session State Architecture

All session state variables are initialised by `utils/session_init.init_session_state()`. This is called as the first action on every page after `apply_theme()`.

| Key | Type | Default | Description |
|---|---|---|---|
| `theme` | str | `"dark"` | Current theme: "dark" or "light" |
| `thresholds` | dict | See §5 | Scoring threshold values |
| `risk_weights` | dict | See §4.1 | 7 retention risk factor weights |
| `value_weights` | dict | See §4.2 | 7 commercial value factor weights |
| `prof_weights` | dict | See §4.3 | 9 profitability factor weights |
| `react_weights` | dict | See §4.4 | 5 reactivation factor weights |
| `vip_weights` | dict | See §4.5 | 5 VIP upside factor weights |
| `scoring_rules` | dict | loaded from `config/scoring_rules.json` | Business rules bands |
| `scored_df` | DataFrame | generated on first load | Full scored client table |
| `raw_df` | DataFrame | same as scored_df source | Pre-score raw data |
| `data_source` | str | `"sample"` | Active data source key |
| `data_filename` | str/None | `None` | Filename if upload |
| `refresh_interval` | str | `"manual"` | Auto-refresh interval key |
| `next_refresh_time` | datetime/None | `None` | Next scheduled refresh |
| `last_refresh_time` | datetime/None | `None` | Last completed refresh |

## 2.5 Theme Architecture

**Source of truth:** `config/theme.py`

Two themes are defined: `"dark"` (OneRoyal Dark) and `"light"` (OneRoyal Light).

Each theme defines 9 color tokens:
- `bg` — page background
- `card` — card/panel background
- `secondary_bg` — secondary panels, expanders
- `sidebar_bg` — sidebar background
- `plot_bg` — Plotly chart interior background
- `text` — primary text color
- `muted` — secondary/muted text
- `border` — borders and dividers
- `input_bg` — form input backgrounds

Semantic colors (`GOLD`, `RED`, `GREEN`, `AMBER`, `BLUE`, `PURPLE`) are **identical** in both themes — they carry meaning (e.g., RED always means high risk), not aesthetic context.

Theme is applied via two functions:
1. `apply_theme()` — generates `<style>` CSS targeting Streamlit's internal class names
2. `get_plotly_layout(**overrides)` — returns a Plotly layout dict with current theme colors; preferred over the static `PLOTLY_LAYOUT` constant

**Theme selection:** Settings page → Appearance section → radio button → `st.session_state["theme"]` → `st.rerun()`

## 2.6 Scoring Engine Architecture

```
utils/scoring.py                utils/rules_engine.py
     │                                  │
     │  score_dataframe()               │  load_rules() → scoring_rules.json
     │  ├─ score_retention_risk()   ←───┤  score_retention_risk()
     │  ├─ score_commercial_value() ←───┤  score_commercial_value()
     │  ├─ score_profitability()    ←───┤  score_profitability()
     │  ├─ score_reactivation()         │  (direct weights, no bands)
     │  ├─ score_vip_upside()           │  (direct weights, no bands)
     │  ├─ compute_health_score()       │  (formula-based, no bands)
     │  ├─ compute_priority_score()     │  (formula-based, no bands)
     │  ├─ assign_segments()            │  (risk × value tier matrix)
     │  └─ assign_actions()             │  (11-rule decision tree)
     │
     └─ score_dataframe() returns scored DataFrame
```

The first three scores (Risk, Value, Profitability) use the **Business Rules Engine** — configurable band scoring via JSON. The remaining three (Reactivation, VIP Upside, Health) use direct weighted formulas.

---

# SECTION 3 — DATA REQUIREMENTS

## 3.1 Complete Field Dictionary

The application's internal schema requires the following fields. Every data source (sample, upload, CRM, Holistics) must be mapped to these exact column names by `integrations/data_mapper.py`.

### 3.1.1 Identity Fields (Required)

| Column Name | Description | Data Type | Required | Example |
|---|---|---|---|---|
| `client_id` | Unique client identifier | string | ✅ | `CR10001` |
| `client_name` | Full client name | string | ✅ | `Mohammed Al-Rashid` |
| `country` | Country of residence | string | ✅ | `United Arab Emirates` |
| `account_manager` | Assigned account manager | string | ✅ | `Sarah Johnson` |
| `ib_name` | Introducing Broker name | string | Optional | `Gulf Traders IB` |
| `account_type` | Account classification | string | Optional | `ECN`, `Standard`, `VIP` |
| `book_type` | Trading book assignment | string | ✅ | `A-Book`, `B-Book`, `M-Book` |
| `account_status` | Derived activity status | string | Derived | `Active`, `Dormant`, `Inactive` |
| `vip_status` | Whether client is VIP | boolean | Optional | `True` / `False` |
| `client_tenure_days` | Days since account opened | integer | Optional | `847` |

### 3.1.2 Financial Fields (Required)

| Column Name | Description | Data Type | Required | Example |
|---|---|---|---|---|
| `lifetime_deposits` | Total deposits ever made | float | ✅ | `45000.00` |
| `withdrawals_total` | Total withdrawals ever | float | Optional | `12000.00` |
| `net_deposits` | lifetime_deposits − withdrawals_total | float | Derived | `33000.00` |
| `current_equity` | Current account balance | float | ✅ | `28500.00` |
| `equity_30d_ago` | Balance 30 days ago | float | ✅ for risk | `31200.00` |

### 3.1.3 Activity / Timing Fields (Required)

| Column Name | Description | Data Type | Source Format | Derived Format |
|---|---|---|---|---|
| `login_days_ago` | Days since last login | integer | `last_login_date` (DATE) | integer ≥ 0 |
| `last_deposit_days_ago` | Days since last deposit | integer | `last_deposit_date` (DATE) | integer ≥ 0 |
| `last_withdrawal_days_ago` | Days since last withdrawal | integer | `last_withdrawal_date` (DATE) | integer ≥ 0 |
| `withdrawal_amount_last_30d` | Withdrawal value in last 30 days | float | `withdrawals_30d` | float ≥ 0 |

### 3.1.4 Trading Volume Fields (Required)

| Column Name | Description | Data Type | Required | Example |
|---|---|---|---|---|
| `trading_volume_last_30d` | Total trade volume, last 30 days | float | ✅ | `125000.00` |
| `trading_volume_previous_30d` | Total trade volume, prior 30 days | float | ✅ for risk | `180000.00` |
| `volume_90d_ago` | Volume at 90-day reference period | float | ✅ for VIP | `95000.00` |

### 3.1.5 Engagement Fields (Required)

| Column Name | Description | Data Type | Required | Example |
|---|---|---|---|---|
| `number_of_redeposits` | Number of repeat deposit events | integer | ✅ for value | `7` |
| `complaints_last_30d` | Complaint count, last 30 days | integer | ✅ for risk | `0` |
| `open_tickets` | Open support tickets | integer | ✅ for risk | `1` |
| `total_deposits_count` | number_of_redeposits + 1 | integer | Derived | `8` |

### 3.1.6 Revenue / Profitability Fields

These fields feed the Profitability Score and are **critical** for B-Book and M-Book clients. They must come from the trading platform, not the CRM.

| Column Name | Description | A-Book | B-Book | M-Book | Required |
|---|---|---|---|---|---|
| `spread_commission_revenue` | Monthly spread income | ✅ | ✅ | ✅ | ✅ |
| `commission_revenue` | Monthly commission income | ✅ | ✅ | ✅ | Optional |
| `swap_revenue` | Monthly swap/overnight income | ✅ | ✅ | ✅ | Optional |
| `captured_client_losses` | Net P&L captured from B-Book positions | 0 | ✅ Critical | ✅ Critical | Conditional |
| `net_company_pnl` | Monthly total profit to company | Derived | Derived | Derived | Derived |
| `company_pnl_from_client` | Alias for net_company_pnl | ✅ | ✅ | ✅ | Derived |

> **IMPORTANT — B-Book `captured_client_losses`:** This field contains the net realised client P&L that the company holds internally. It can be **negative** (when B-Book clients are profitable). The profitability scoring logic handles negative values by assigning 0 points. This field must be computed by the trading platform, not the CRM.

### 3.1.7 Computed / Scored Outputs

These columns are generated by the scoring engine and do not need to be provided by data sources:

| Column | Description |
|---|---|
| `retention_risk_score` | 0–100 (higher = more at risk) |
| `commercial_value_score` | 0–100 (higher = more valuable) |
| `profitability_score` | 0–100 (higher = more profitable) |
| `reactivation_score` | 0–100 (higher = best reactivation candidate) |
| `vip_upside_score` | 0–100 (higher = stronger upgrade potential) |
| `client_health_score` | 0–100 (higher = healthier) |
| `priority_score` | 0–100 (higher = action more urgent) |
| `risk_level` | `Low` / `Medium` / `High` |
| `value_level` | `Low` / `Medium` / `High` |
| `health_label` | `Critical` / `At Risk` / `Watchlist` / `Healthy` / `Excellent` |
| `segment` | 9 named segments (see §4.8) |
| `priority_level` | `Normal` / `Elevated` / `Critical` |
| `recommended_action` | Text action recommendation |
| `recommended_owner` | `Management Review` / `VIP Team` / `Retention Team` / `Sales Team` / `Account Manager` |
| `action_reason` | Plain-text explanation of why action was assigned |

## 3.2 BI Export Specification

### 3.2.1 Recommended Lookback Periods

| Metric Type | Recommended Period | Reason |
|---|---|---|
| Last login date | Real-time or daily snapshot | Detects sudden inactivity |
| Last deposit/withdrawal date | Real-time or daily snapshot | Triggers withdrawal alert rule |
| Trading volume | **30-day rolling** | Used directly in scoring |
| Prior period volume | **30-day window ending 30 days ago** (i.e. days 31–60) | Basis for volume drop signal |
| Historical volume reference | **90-day reference** | Used in VIP Upside Score |
| Current equity | Daily close balance | Core to risk and value scoring |
| Equity reference | **30-day-ago balance** | Equity trend signal in risk score |
| Revenue (spread, commission, swap) | **Monthly aggregate** | Fed into profitability score |
| Captured client losses (B/M) | **Monthly aggregate** | Profitability score, B/M book |
| Lifetime deposits | Cumulative from account open | Commercial value score |
| Total withdrawals | Cumulative from account open | Net deposits computation |
| Complaints | **30-day count** | High-weight risk signal (×9) |
| Open tickets | Live count | Contribution to complaints signal |
| Redeposit count | Cumulative | Commercial value loyalty signal |
| VIP status | Current flag | Value + VIP upside scoring |
| Client tenure | Days since account open | Value + reactivation scoring |

### 3.2.2 Minimum Viable Dataset (MVP)

Six fields that allow all scores to compute with defaults for the rest:

```
client_id, client_name, country, book_type,
lifetime_deposits, current_equity
```

**Warning:** With only the MVP fields, all time-based signals (login inactivity, deposit staleness, withdrawal pressure, equity trend, volume drop) will use zero/default values, severely degrading risk score quality.

### 3.2.3 Production Dataset

All fields in §3.1.1 through §3.1.6. This enables full scoring fidelity.

### 3.2.4 Recommended BI Export Structure

**File:** `oneRoyal_client_intelligence_YYYYMMDD.csv`

**Format:** UTF-8 CSV, one row per client, header row included

**Frequency:** Daily, generated at 03:00 server time after trading day close

**Grain:** One row per live client account. Dormant/closed accounts optional but include if login or withdrawal activity occurred in last 365 days.

**Recommended column order:**

```csv
client_id,client_name,country,account_manager,ib_name,account_type,book_type,
lifetime_deposits,withdrawals_total,net_deposits,current_equity,equity_30d_ago,
last_login_date,last_deposit_date,last_withdrawal_date,withdrawals_30d,
trading_volume_30d,trading_volume_previous_30d,volume_90d_ago,
spread_revenue,commission_revenue,swap_revenue,
company_pnl,captured_client_losses,
number_of_redeposits,complaints,open_tickets,
client_tenure_months,vip_status
```

**Date format:** `YYYY-MM-DD`  
**Currency:** USD, no formatting (not `$45,000.00` — use `45000.00`)  
**Boolean:** `true` / `false` or `1` / `0` — both supported by the mapper  
**Null values:** Empty string (not `NULL`, not `N/A`)

### 3.2.5 Excel Format Specification

Sheet name: `Clients`  
Row 1: Column headers (exactly as above)  
Row 2+: Client data  
No merged cells, no formulas, no conditional formatting  
File format: `.xlsx`

---

# SECTION 4 — SCORING ENGINE

All scores are on a **0–100 scale**. The normalization method used throughout is **min-max normalization**:

```
normalized = (value - min) / (max - min) × 100
```

If all values are equal (min = max), the score defaults to 50. All scores are rounded to 1 decimal place.

## 4.1 Retention Risk Score

**Source:** `utils/rules_engine.py:score_retention_risk()`, `utils/scoring.py`  
**Higher score = higher risk of leaving**

### Purpose
Quantifies how likely a client is to withdraw funds, reduce trading activity, or become dormant in the near term.

### Seven Signals and Their Scoring Bands

Each signal is evaluated against tiered bands from `config/scoring_rules.json`. The band score (0–100 points) is then multiplied by the factor weight.

#### Signal 1: Withdrawal Pressure
**Input:** `withdrawal_amount_last_30d / current_equity`

| Band | Condition | Points |
|---|---|---|
| No recent withdrawal | < 10% of equity | 10 |
| Moderate withdrawal | 10–30% of equity | 50 |
| Large withdrawal | ≥ 30% of equity | 90 |

**Default weight:** `w_withdrawal = 8` (out of max 10)

#### Signal 2: Trading Volume Drop
**Input:** `(previous_30d_volume − last_30d_volume) / previous_30d_volume`

| Band | Condition | Points |
|---|---|---|
| Stable or growing | ≤ 0% drop | 5 |
| Mild decline | 0–30% drop | 30 |
| Significant decline | 30–60% drop | 65 |
| Major decline | > 60% drop | 90 |

**Default weight:** `w_volume_drop = 7`

#### Signal 3: Login Inactivity
**Input:** `login_days_ago`

| Band | Condition | Points |
|---|---|---|
| Active | < 7 days | 5 |
| Mild gap | 7–30 days | 25 |
| Dormant | 30–90 days | 65 |
| Long inactive | > 90 days | 90 |

**Default weight:** `w_login = 6`

#### Signal 4: Deposit Inactivity
**Input:** `last_deposit_days_ago`

| Band | Condition | Points |
|---|---|---|
| Recent depositor | < 30 days | 5 |
| Monthly gap | 30–90 days | 30 |
| Infrequent | 90–180 days | 60 |
| Lapsed | > 180 days | 90 |

**Default weight:** `w_deposit_stale = 5`

#### Signal 5: Complaints & Open Tickets
**Input:** `complaints_last_30d + open_tickets`

| Band | Condition | Points |
|---|---|---|
| No issues | 0 | 0 |
| Minor friction | 1 | 50 |
| Active dissatisfaction | ≥ 2 | 90 |

**Default weight:** `w_complaints = 9` (highest — unresolved complaints are the strongest churn predictor)

#### Signal 6: Equity Erosion vs Deposits
**Input:** `1 − (current_equity / net_deposits)`

| Band | Condition | Points |
|---|---|---|
| Growing/stable | ≤ 0% | 0 |
| Mild decline | 0–15% | 30 |
| Significant | 15–30% | 65 |
| Major | > 30% | 90 |

**Default weight:** `w_equity_erosion = 5`

#### Signal 7: Equity Trend (30-Day)
**Input:** `(equity_30d_ago − current_equity) / equity_30d_ago`

| Band | Condition | Points |
|---|---|---|
| Growing | ≤ 0% | 0 |
| Mild decline | 0–15% | 30 |
| Significant | 15–30% | 65 |
| Major | > 30% | 90 |

**Default weight:** `w_equity_trend = 6`

### Combination Formula
```python
raw_score = (
    w_withdrawal     × band_score(withdrawal_pct)   +
    w_volume_drop    × band_score(vol_drop_pct)     +
    w_login          × band_score(login_days_ago)    +
    w_deposit_stale  × band_score(deposit_days_ago)  +
    w_complaints     × band_score(complaints_total)  +
    w_equity_erosion × band_score(equity_erosion)   +
    w_equity_trend   × band_score(equity_trend)
)
# Then normalized 0-100 across all clients
```

### Interpretation
| Score Range | Label | Meaning |
|---|---|---|
| 0–29 | Low Risk | Client shows stable engagement |
| 30–59 | Medium Risk | Monitor; consider proactive contact |
| 60–79 | High Risk | Priority for retention action |
| 80–100 | Very High Risk | Immediate intervention required |

### Calibration Risks
- **Overweight `w_complaints` (>9):** Minor complaint issues trigger false high-risk flags
- **Underweight `w_withdrawal` (<6):** Large withdrawals pass undetected
- **Overweight `w_login`:** Clients who trade via API (not web login) will be falsely flagged

---

## 4.2 Commercial Value Score

**Source:** `utils/rules_engine.py:score_commercial_value()`  
**Higher score = greater commercial importance to the firm**

### Purpose
Quantifies how much revenue and relationship value is at stake if this client churns. Used to prioritise intervention effort toward the highest-value accounts.

### Seven Components and Their Bands

#### Component 1: Lifetime Deposits

| Band | Condition | Points |
|---|---|---|
| Micro client | < $1,000 | 10 |
| Small | $1,000–$10,000 | 35 |
| Medium | $10,000–$50,000 | 60 |
| Large | $50,000–$200,000 | 85 |
| Major | > $200,000 | 100 |

**Default weight:** `v_lifetime_dep = 8`

#### Component 2: Net Deposits

| Band | Condition | Points |
|---|---|---|
| Negative/zero | < $0 | 0 |
| Micro | $0–$1,000 | 15 |
| Small | $1,000–$10,000 | 40 |
| Medium | $10,000–$50,000 | 70 |
| Large | > $50,000 | 100 |

**Default weight:** `v_net_dep = 7`

#### Component 3: Current Equity

| Band | Condition | Points |
|---|---|---|
| Under-funded | < $500 | 5 |
| Small | $500–$5,000 | 30 |
| Medium | $5,000–$25,000 | 60 |
| Large | $25,000–$100,000 | 85 |
| Major | > $100,000 | 100 |

**Default weight:** `v_current_equity = 8`

#### Component 4: Trading Volume (30-Day)

| Band | Condition | Points |
|---|---|---|
| Inactive | < $1,000 | 5 |
| Low | $1,000–$10,000 | 25 |
| Medium | $10,000–$100,000 | 55 |
| High | $100,000–$500,000 | 80 |
| Elite | > $500,000 | 100 |

**Default weight:** `v_volume = 6`

#### Component 5: Redeposit Count

| Band | Condition | Points |
|---|---|---|
| First deposit only | 0 | 0 |
| Low loyalty | 1–2 | 25 |
| Moderate | 3–7 | 55 |
| High | 8–15 | 80 |
| Champion | > 15 | 100 |

**Default weight:** `v_redeposits = 5`

#### Component 6: Client Tenure

| Band | Condition | Points |
|---|---|---|
| New client | < 90 days | 10 |
| Recent | 90–365 days | 35 |
| Established | 365–730 days | 65 |
| Long-term | > 730 days | 100 |

**Default weight:** `v_tenure = 4`

#### Component 7: VIP Status

VIP clients automatically score **100 points** for this component; non-VIP score **0**.

**Default weight:** `v_vip = 9` (highest single-component weight in this score)

### Combination Formula
```python
raw_score = (
    v_lifetime_dep   × band_score(lifetime_deposits)   +
    v_net_dep        × band_score(net_deposits)         +
    v_current_equity × band_score(current_equity)       +
    v_volume         × band_score(trading_volume_30d)   +
    v_redeposits     × band_score(redeposit_count)      +
    v_tenure         × band_score(tenure_days)          +
    v_vip            × (100 if vip_status else 0)
)
# Then normalized 0-100 across all clients
```

---

## 4.3 Profitability Score

**Source:** `utils/rules_engine.py:score_profitability()`  
**Higher score = higher monthly profit to OneRoyal from this client**

### Purpose
Measures how much monthly revenue/profit OneRoyal generates from each client. The calculation is **book-type-aware** — the same dollar amount in revenue carries different meaning across book types.

### Book-Type Formulas

#### A-Book
```
profitability_amount = spread_commission_revenue + commission_revenue + swap_revenue
```
A-Book clients generate revenue through fees only. There are no captured trading losses.

| Band | Condition | Points |
|---|---|---|
| Marginal | < $50/month | 10 |
| Low | $50–$200/month | 35 |
| Medium | $200–$500/month | 60 |
| High | $500–$2,000/month | 85 |
| Elite | > $2,000/month | 100 |

#### B-Book
```
profitability_amount = captured_client_losses + commission_revenue + swap_revenue + spread_commission_revenue
```
B-Book clients who are losing money are profitable for OneRoyal. Clients who are winning generate negative captured losses — the model correctly assigns low profitability scores to these clients.

| Band | Condition | Points |
|---|---|---|
| Loss-making | < $0/month | 0 |
| Marginal | $0–$100/month | 20 |
| Low profit | $100–$500/month | 45 |
| Good profit | $500–$2,000/month | 70 |
| High profit | $2,000–$5,000/month | 90 |
| Elite | > $5,000/month | 100 |

#### M-Book
```
profitability_amount = (internal_ratio × captured_client_losses) 
                       + spread_commission_revenue 
                       + commission_revenue 
                       + swap_revenue
```
`internal_ratio` defaults to **0.6** (configurable in Settings → Business Rules Engine → Profitability Bands). This represents the fraction of client positions held internally (B-Book style) vs hedged externally (A-Book style).

| Band | Condition | Points |
|---|---|---|
| Loss-making | < $0/month | 0 |
| Marginal | $0–$75/month | 20 |
| Low | $75–$300/month | 45 |
| Medium | $300–$1,000/month | 70 |
| High | > $1,000/month | 100 |

### Cross-Book Normalization
All three book types compute `profitability_amount` and then the entire column (all clients, all book types) is normalized 0–100 using min-max. This means profitability scores are comparable across book types.

---

## 4.4 Reactivation Score

**Source:** `utils/scoring.py:score_reactivation()`  
**Higher score = best candidate for a win-back campaign**

### Purpose
Identifies dormant or inactive clients with the highest probability of returning if contacted. The score is designed to peak for clients who have been gone long enough to be "winnable back" but not so long they've completely disengaged.

### Login Window Signal — Non-Linear Curve
The login inactivity signal peaks at **105 days ago** using this curve:
```python
if login_days_ago between 30 and 180:
    login_score = 100 - (abs(login_days_ago - 105) / 75) × 100
elif login_days_ago < 30:
    login_score = login_days_ago / 30 × 50
else:  # > 180 days
    login_score = max(0, 100 - (login_days_ago - 180) / 1.85)
```

**Why 105 days?** Clients who left 3–4 months ago are most responsive to win-back: they still remember the platform but have had time to evaluate alternatives.

### Additional Signals
| Signal | Column | Default Weight |
|---|---|---|
| Login recency window | `login_days_ago` (non-linear) | `r_login_window = 8` |
| Historical deposits | `lifetime_deposits` | `r_lifetime_dep = 7` |
| Redeposit loyalty | `number_of_redeposits` | `r_redeposits = 6` |
| Historical volume | `volume_90d_ago` | `r_volume_hist = 7` |
| Client tenure | `client_tenure_days` | `r_tenure = 5` |

### Interpretation
Only meaningful for clients with `login_days_ago > 30` (Dormant or Inactive status). For active clients this score is low by design — they do not need reactivation.

---

## 4.5 VIP Upside Score

**Source:** `utils/scoring.py:score_vip_upside()`  
**Higher score = strongest candidate for VIP upgrade offer**

### Purpose
Identifies non-VIP clients who exhibit the financial profile of a VIP client — high equity, growing volume, demonstrated loyalty through redeposits. Existing VIP clients score near 0 on the "Not Yet VIP" factor, deliberately suppressing their score so the queue focuses on upgrade candidates.

### Five Signals
| Signal | Column | Computation | Default Weight |
|---|---|---|---|
| Equity size | `current_equity` | Min-max 0–100 | `u_equity = 8` |
| Net deposits | `net_deposits` | Min-max 0–100 | `u_net_dep = 6` |
| Volume trend | `(vol_30d − vol_90d) / vol_90d` | Min-max 0–100 | `u_volume_trend = 7` |
| Redeposit loyalty | `number_of_redeposits` | Min-max 0–100 | `u_redeposits = 5` |
| Not yet VIP | Boolean: non-VIP = 100, VIP = 0 | Direct | `u_not_yet_vip = 9` |

**The `u_not_yet_vip` weight (default 9) is intentionally the highest** — if a client is already VIP, no upgrade offer is needed.

---

## 4.6 Client Health Score

**Source:** `utils/scoring.py:compute_health_score()`  
**Higher score = healthier client relationship**

### Formula
```
health_score = (100 − retention_risk_score) × 0.50
             + commercial_value_score        × 0.30
             + profitability_score           × 0.20
```

This is a **composite positive metric**. The first term `(100 − risk)` ensures that high-risk clients cannot have high health scores. Value and profitability contribute positively.

### Health Labels (Source: `utils/scoring.py:240–248`)
| Score Range | Label | CSS Color |
|---|---|---|
| 80–100 | Excellent | Green (#10B981) |
| 60–79 | Healthy | Light green (#22C55E) |
| 40–59 | Watchlist | Amber (#F59E0B) |
| 20–39 | At Risk | Orange (#F97316) |
| 0–19 | Critical | Red (#EF4444) |

**Note:** Health Score weights are **not configurable** via Settings. They are hard-coded in `utils/scoring.py`. Changing them requires a code deployment.

---

## 4.7 Priority Score

**Source:** `utils/scoring.py:compute_priority_score()`  
**Used to rank the Action Center queue**

### Formula
```
priority_score = retention_risk_score × 0.30
               + commercial_value_score × 0.25
               + profitability_score    × 0.30
               + reactivation_score     × 0.15
```

**Design rationale:** Risk and profitability are equally weighted at 30% each — a client that is both at risk AND profitable generates the highest urgency. Value contributes 25%, reactivation 15%.

**Note:** Priority Score weights are **not configurable** via Settings. Hard-coded in `utils/scoring.py`.

---

## 4.8 Segmentation Matrix

**Source:** `utils/scoring.py:assign_segments()`

Clients are first tiered into Low/Medium/High for both Risk and Value using the threshold values from Settings. The 3×3 matrix produces nine named segments:

| | High Value | Medium Value | Low Value |
|---|---|---|---|
| **High Risk** | Save Immediately | Senior Retention Review | Automated Retention |
| **Medium Risk** | Proactive Nurture | Standard Nurture | Light Touch |
| **Low Risk** | VIP Expansion | Growth Program | Monitor |

**"Save Immediately"** clients have both elevated risk AND high commercial value — they are the first priority for any retention team.

---

## 4.9 Recommended Action (11-Rule Decision Tree)

**Source:** `utils/scoring.py:assign_actions()` — first-match wins

| Priority | Condition | Action |
|---|---|---|
| 1 | VIP + risk ≥ high_risk + value ≥ high_value | URGENT: VIP Retention — Escalate to Management |
| 2 | risk ≥ high_risk + value ≥ high_value + profitability ≥ high_profitability | Immediate Retention Call |
| 3 | complaints_30d ≥ 2 + risk ≥ high_risk | Resolve Complaints + Retention Review |
| 4 | withdrawal_30d ≥ (large_withdrawal_pct × equity) + risk ≥ high_risk | Retention Call: Withdrawal Alert |
| 5 | risk ≥ high_risk | Retention Follow-Up |
| 6 | VIP + risk < high_risk + value ≥ high_value | VIP Expansion Offer |
| 7 | vip_upside ≥ 65 + not VIP | VIP Upsell Opportunity |
| 8 | reactivation ≥ 65 + account_status ∈ {Dormant, Inactive} | Reactivation Campaign |
| 9 | volume drop > 50% + risk ≥ 35 | Re-engagement: Trading Incentive |
| 10 | complaints_30d ≥ 1 | Complaint Resolution |
| 11 | Default (fallback) | Monitor Only |

The thresholds `high_risk`, `high_value`, `high_profitability`, and `large_withdrawal_pct` are all user-configurable in Settings (see §5).

---

## 4.10 Recommended Owner Routing

**Source:** `utils/scoring.py:assign_recommended_owner()`

| Condition | Assigned To |
|---|---|
| URGENT VIP Retention | Management Review |
| VIP client (any risk level) | VIP Team |
| Immediate Retention Call | Retention Team |
| Reactivation Campaign or Re-engagement | Sales Team |
| All other actions | Account Manager |

---

# SECTION 5 — SETTINGS PAGE REFERENCE

**Page:** `pages/5_Settings.py`

## 5.1 Scoring Thresholds

These thresholds control when clients are labelled and which action rules trigger. They affect the segmentation matrix, action routing, and all dashboard KPIs.

| Setting | Default | Minimum | Maximum | Impact of Increase | Impact of Decrease |
|---|---|---|---|---|---|
| `high_risk` | 60 | 10 | 95 | Fewer clients flagged as high risk; team focuses only on severe cases | More clients flagged; higher workload, more false positives |
| `high_value` | 60 | 10 | 95 | Fewer clients in "high value" bucket; higher bar for premium treatment | More clients receive premium attention |
| `high_profitability` | 60 | 10 | 95 | Fewer clients trigger profitability-dependent action rules | More clients receive profitability-linked actions |
| `critical_priority` | 65 | 10 | 95 | Fewer "Critical" priority labels in Action Center | More clients labelled Critical; creates urgency inflation |

### Typical Use Cases
- **Large portfolio (>500 clients):** Raise `high_risk` to 70 to focus the team on the genuinely critical cases
- **Small team:** Raise `critical_priority` to 75 to create a tighter critical list
- **B-Book-heavy book:** Lower `high_profitability` to 50 to capture more profitability-driven actions

## 5.2 Activity Thresholds

| Setting | Default | Description |
|---|---|---|
| `login_inactivity_days` | 30 | Days without login before a client is flagged as "inactive" in action rules |
| `large_withdrawal_pct` | 0.30 (30%) | Withdrawal exceeding this % of equity triggers "Retention Call: Withdrawal Alert" |
| `dormant_days` | 30 | Days without login before account_status changes to "Dormant" |

## 5.3 Appearance

| Setting | Default | Options |
|---|---|---|
| Theme | Dark | OneRoyal Dark / OneRoyal Light |

Theme selection is stored in `st.session_state["theme"]` and applies immediately via `st.rerun()`.

## 5.4 Business Rules Engine — Scoring Bands

Located in the lower section of the Settings page. Three tabs: Retention Risk Factors, Commercial Value Factors, Profitability Bands.

For each factor, the user can edit the **Points** (0–100) for each tier band. Higher points = stronger signal for that condition.

After editing, clicking **"Save Scoring Rules & Rescore All Clients"** writes changes to `config/scoring_rules.json` and immediately rescores all clients.

> **CAUTION:** Changing band points is a calibration decision that affects every client score. Changes should be made based on validated outcome data (see §9), not intuition.

---

# SECTION 6 — EXECUTIVE DASHBOARD

**Page:** `pages/1_Executive_Dashboard.py`

## 6.1 KPI Cards (Top Row)

Six metric tiles rendered at page load:

| KPI | Formula | Business Interpretation |
|---|---|---|
| Total Clients | `len(df)` | Portfolio size |
| Clients At Risk | `count(risk_score ≥ high_risk)` | Immediate retention workload |
| High-Value At Risk | `count(risk ≥ high_risk AND value ≥ high_value)` | Revenue-priority intervention candidates |
| Total Equity At Risk | `sum(current_equity where risk ≥ high_risk)` | Dollar value in jeopardy |
| Annual Revenue At Risk | `sum(spread + commission + swap where risk ≥ high_risk) × 12` | Forward revenue exposure |
| Annual Profitability At Risk | `sum(net_company_pnl where risk ≥ high_risk) × 12` | Forward profitability exposure |

## 6.2 Model Prediction Accuracy

Four metric tiles using historical snapshot data (or simulated fallback):

| KPI | Calculation | Target |
|---|---|---|
| Churn Prediction Accuracy | AUC-style: (hi-risk ∩ churned) / total_churned × 80% + (lo-risk ∩ not_churned) / total_lo × 20% | > 75% |
| Withdrawal Prediction Accuracy | `churn_accuracy × 1.08`, capped at 98% | > 80% |
| Reactivation Accuracy | `max(55, churn_accuracy × 0.90)` | > 65% |
| Model Vintage | Static "12 months" (simulated) | — |

These are approximations. Real accuracy requires matching historical risk scores against confirmed outcomes in the snapshot database.

## 6.3 Charts

| Chart | Type | Data |
|---|---|---|
| Retention Risk Distribution | Histogram (25 bins) | `retention_risk_score` for all clients |
| Client Health Distribution | Bar chart | Count per health label |
| Profitability Score Distribution | Histogram (25 bins) | `profitability_score` for all clients |
| Avg Profitability by Book Type | Grouped bar | Average profitability score per book type |
| Annual Revenue At Risk by Country | Horizontal bar (top 10) | `(spread + commission + swap) × 12` for at-risk clients |
| Annual Profitability At Risk by Country | Horizontal bar (top 10) | `net_company_pnl × 12` for at-risk clients |
| Annual Revenue At Risk by AM | Horizontal bar | Revenue at risk per account manager |
| Annual Profitability At Risk by AM | Horizontal bar | Profitability at risk per account manager |
| Segmentation Matrix | Heatmap (3×3) | Client count per Risk×Value cell |
| Trend Analytics (30/90/180/Full) | Line charts | avg_risk_score, avg_health_score, total_equity, annual_revenue |

**Recommended actions per KPI:**
- **Clients At Risk > 20% of portfolio:** Review `high_risk` threshold — may be set too low, or portfolio health is genuinely declining
- **High-Value At Risk > 5:** Escalate to Head of Retention immediately; trigger VIP meeting
- **Annual Revenue At Risk > $500K:** Board escalation warranted; retention budget justification

---

# SECTION 7 — CLIENT LIST

**Page:** `pages/2_Client_List.py`

## 7.1 Filter Controls

Eight filter controls are available in the expandable "Filters" section:

| Filter | Type | Column |
|---|---|---|
| Search name or client ID | Text input | `client_name` OR `client_id` (case-insensitive OR) |
| Country | Dropdown | `country` |
| Account Manager | Dropdown | `account_manager` |
| IB Name | Dropdown | `ib_name` |
| Book Type | Dropdown | `book_type` (A-Book / B-Book / M-Book) |
| Account Type | Dropdown | `account_type` |
| Risk Level | Dropdown | `risk_level` (Low / Medium / High) |
| Health | Dropdown | `health_label` |

All filters are cumulative (AND logic).

## 7.2 Sort Controls

Sort column dropdown supports all 6 scores plus `current_equity` and `lifetime_deposits`. Sort direction toggle (ascending/descending).

## 7.3 Summary KPIs for Filtered Set

When at least one client matches, four metrics are displayed:
- Avg Risk Score
- Avg Profitability Score
- Total Equity
- Annual Revenue (estimated as monthly revenue × 12)

## 7.4 Table Columns

Progress bars are rendered for all 7 scores. Columns displayed:

`client_id`, `client_name`, `country`, `account_manager`, `book_type`, `account_type`, `vip_status` (checkbox), `health_label`, all 6 scores (as progress bars), `segment`, `recommended_action`, `recommended_owner`, `current_equity` ($), `net_company_pnl` (monthly $)

## 7.5 Client Detail

Below the table, a client selector shows the selected client's:
- 6 score tiles (Risk, Value, Profitability, Reactivation, VIP Upside, Health)
- Segment / Action / Owner / Reason
- Financial summary (equity, deposits, PnL, account status, VIP)
- Activity summary (login, deposit, withdrawal timing, volume, complaints)
- **Score Contribution Analysis** — two horizontal bar charts showing which factors drove the Risk score and which drove the Value score

---

# SECTION 8 — ACTION CENTER

**Page:** `pages/4_Action_Center.py`

## 8.1 Prioritisation Methodology

The Action Center displays all clients except those assigned "Monitor Only". The queue is sorted by:

1. **Profitability Score** (descending) — highest-profit clients first
2. Then by **Commercial Value Score** (descending)
3. Then by **Retention Risk Score** (descending)

**Design rationale:** Protecting profitable clients is the primary commercial objective. Two clients with equal profitability are ranked by value, then by urgency.

## 8.2 Filters

- Action type: Multi-select by recommended_action
- Owner: Filter by recommended_owner team
- Priority level: Normal / Elevated / Critical

## 8.3 KPI Summary

- Clients Needing Action (count)
- Avg Priority Score
- Annual Revenue at Stake
- Annual Profitability at Stake

## 8.4 Charts

- Horizontal bar: Clients by recommended action type
- Pie chart: Action distribution by recommended owner

## 8.5 Team Workload Table

Aggregated by `recommended_owner`:
- Client count
- Avg priority score
- Avg profitability score
- Total equity
- Annual revenue at stake
- Annual PnL at stake

## 8.6 Recommended AM Operating Procedure

**Daily workflow for Account Managers:**

1. Open Action Center each morning
2. Filter by own name under "Filter by owner → Account Manager"
3. Work down the list in displayed order (profitability-first)
4. For each "Immediate Retention Call" or "Retention Follow-Up":
   - Review Client Detail on Client List page for score reasons
   - Note the action reason text for talking points
   - Log outcome in Model Validation → Retention Effectiveness → "Log a Retention Action"
5. Flag "URGENT: VIP Retention" clients for same-day escalation to management

**Escalation path:**
- Management Review → Head of Retention + Commercial Director
- VIP Team → Dedicated VIP relationship manager
- Retention Team → Retention specialists, not AMs

---

# SECTION 9 — MODEL VALIDATION

**Page:** `pages/7_Model_Validation.py`

## 9.1 Tab 1 — Prediction Accuracy

### Methodology
When historical snapshot data and outcome data exist, the platform computes an AUC-style metric by:

1. Loading `score_snapshots` (daily risk scores for all clients)
2. Loading `client_outcomes` (confirmed churn, withdrawal, reactivation events)
3. Joining on `client_id`, computing days between snapshot and outcome
4. Clients with outcome within 60 days of a high-risk snapshot = True Positive

### Simulated Accuracy (current state)
Until real outcomes accumulate, the platform displays:
- Churn Prediction Accuracy: **78%**
- Withdrawal Prediction Accuracy: **84%**
- Reactivation Accuracy: **71%**

These are derived from simulated historical data seeded by `utils/snapshot_db.seed_historical_data()` with outcomes correlated to risk bands:

| Risk Band | Annual Churn Probability | Annual Withdrawal Probability |
|---|---|---|
| 80–100 | 40% | 50% |
| 60–80 | 20% | 30% |
| 40–60 | 10% | 12% |
| 20–40 | 4% | — |
| 0–20 | 1% | — |

## 9.2 Tab 2 — Score Factor Breakdown

Per-client explainability. Select any client, see horizontal bar charts for:
- Risk factors: which signals drove the risk score
- Value factors: which signals drove the commercial value score

Calls `utils/rules_engine.get_factor_breakdown(row, rules)` which returns the actual band points awarded to each factor for that client.

## 9.3 Tab 3 — Retention Effectiveness

Tracks which retention actions are working and logs new actions.

**Tracked action types:** VIP Meeting, Retention Call, Cashback Offer, Bonus Offer, Account Manager Follow-Up, Email Campaign

**Simulated benchmarks (industry-based):**

| Action Type | Benchmark Success Rate |
|---|---|
| VIP Meeting | 60% |
| Retention Call | 45% |
| Cashback Offer | 38% |
| Bonus Offer | 32% |
| AM Follow-Up | 25% |
| Email Campaign | 15% |

**Logging:** Users can log retention actions via the "Log a Retention Action" expander, which writes to the `retention_actions` table in SQLite.

## 9.4 Tab 4 — Score Trend Analysis

Line charts showing average scores over time when multiple daily snapshots exist. With only simulated historical data, demo charts are shown.

## 9.5 Tab 5 — Data Snapshots

Database health metrics and snapshot history by date, with CSV export of the latest snapshot.

---

## 9.6 Validation Methodology Framework

### Recommended Validation Cycle

| Frequency | Activity |
|---|---|
| **Weekly** | Review Retention Effectiveness tab. Are logged actions achieving >35% success? |
| **Monthly** | Compare this month's high-risk clients against clients who actually withdrew/churned |
| **Quarterly** | Full model calibration review (see below) |
| **Annually** | Consider introducing ML-based scores to supplement rules-based bands |

### Quarterly Model Review Framework

**Step 1 — Collect ground truth (first 2 weeks of quarter)**
- Extract confirmed churn events from CRM: clients who closed accounts or withdrew >80% of equity
- Extract large withdrawal events: withdrawals >30% of equity
- Export reactivation events: dormant clients who made a new deposit

**Step 2 — Match against prior quarter's risk scores**
- For each confirmed churn: what was their risk score 30, 60, 90 days prior?
- Build a 2×2 confusion matrix:

```
                    PREDICTED (Risk ≥ 60)
ACTUAL         |  Positive  |  Negative
-------------------------------------------
Churned        |  TP        |  FN (missed)
Did Not Churn  |  FP (waste)|  TN
```

**Step 3 — Compute metrics**
- **Precision** = TP / (TP + FP) — what fraction of flagged clients actually churned?
- **Recall** = TP / (TP + FN) — what fraction of all churners were caught?
- **F1 Score** = 2 × (Precision × Recall) / (Precision + Recall)
- **Lift** = Precision / (total_churn_rate)

**Target metrics:** Precision > 40%, Recall > 60%, Lift > 2.5×

**Step 4 — Recalibrate if targets are missed**
- If Precision is low (too many false positives): **increase** `high_risk` threshold or **reduce** weights on weak signals
- If Recall is low (missing churners): **decrease** `high_risk` threshold or **increase** weights on strong predictors
- Review Score Factor Breakdown for recently-churned clients to identify which factors were not firing

**Step 5 — Document and apply**
- Record all changes to scoring bands in a changelog
- Apply via Settings → Business Rules Engine
- Click "Save Scoring Rules & Rescore" to apply immediately

---

# SECTION 10 — IMPLEMENTATION ROADMAP

## Phase 1 — Pilot (Current State)
**Duration:** Complete  
**Status:** ✅ Done

- [x] 6-score rules-based scoring engine
- [x] 9-segment client matrix
- [x] 11-rule action routing with owner assignment
- [x] 7-page Streamlit application
- [x] Manual Excel/CSV upload
- [x] SQLite snapshot database
- [x] Historical simulation (12 months)
- [x] Theme system (Dark/Light)
- [x] Model Validation page

**Gate criteria to advance:** Executive Board review and sign-off on scoring logic and recommended actions.

---

## Phase 2 — Production Data Connect
**Duration:** 4–6 weeks  
**Key Deliverable:** Real client data flowing into the platform

**Actions required:**
1. BI team builds daily export (§3.2.4 specification)
2. Test upload with first real dataset; verify quality score ≥ 85
3. Validate that book-type profitability figures match trading platform P&L
4. Validate that complaint and ticket counts match CRM records
5. Run scoring on real data; compare top-50 risk clients against AM knowledge ("sanity check")
6. Adjust band thresholds in Settings based on real score distribution

**Technical requirements:**
- Secure file transfer or shared drive for daily CSV
- Streamlit app deployed to internal server
- Access restricted to authorised users (VPN or IP restriction)

---

## Phase 3 — CRM API Integration
**Duration:** 8–12 weeks  
**Key Deliverable:** Automatic daily data pull from CRM, replacing manual upload

**Actions required:**
1. CRM team implements API endpoint: `GET /api/v1/clients?updated_since=YYYY-MM-DD`
2. Platform team implements `integrations/crm_connector.py` HTTP methods (currently NotImplementedError)
3. Map CRM response fields to internal schema in `integrations/data_mapper.py:map_crm_response()`
4. Configure credentials: `CRM_BASE_URL`, `CRM_API_KEY` in environment variables
5. Enable hourly or daily auto-refresh in Data Management page
6. Validate data quality on first pull

---

## Phase 4 — Automation & Alerting
**Duration:** 4–6 weeks  
**Key Deliverable:** Daily automated refresh; email/Slack alerts for critical clients

**Actions required:**
1. Replace SQLite with PostgreSQL (production-grade database)
2. Implement scheduled refresh via cron job or Airflow DAG
3. Build daily email digest: top 10 risk clients, new Critical flags since yesterday
4. Implement user authentication (OAuth2 via internal IdP)
5. Implement role-based access (Board sees Dashboard only; AMs see their own clients)

---

## Phase 5 — AI-Driven Recommendations
**Duration:** 12+ weeks  
**Key Deliverable:** ML-based churn prediction supplementing rules-based scores

**Actions required:**
1. After 6+ months of real outcome data, train a gradient-boosted churn model (XGBoost/LightGBM)
2. Compare ML predictions against existing risk score; use ML as a "challenger model"
3. Integrate the ML score as an eighth dimension in the priority calculation
4. Build automated weight optimisation: use validation data to re-calibrate band points quarterly
5. Introduce natural language generation for action reasons ("This client is at high risk because...")

---

# SECTION 11 — GOVERNANCE

## 11.1 Role Definitions

| Role | Person | Responsibilities |
|---|---|---|
| **Business Owner** | Commercial Director | Signs off on threshold changes; receives weekly briefing |
| **Product Owner** | Head of Retention | Owns platform evolution roadmap; approves scoring changes |
| **Platform Lead** | Analytics / BI Lead | Technical implementation, data pipeline, model validation |
| **Data Custodian** | BI / Data Engineering | Daily export production; data quality monitoring |
| **End Users** | Account Managers | Daily usage; log retention actions; flag anomalies |

## 11.2 BI Team Responsibilities

| Task | Frequency | Deliverable |
|---|---|---|
| Produce client intelligence export | Daily | `oneRoyal_client_intelligence_YYYYMMDD.csv` |
| Validate export quality before upload | Daily | Quality score ≥ 85 required |
| Confirm `captured_client_losses` per client | Monthly | From trading platform P&L |
| Provide equity 30-day snapshot | Daily | `equity_30d_ago` column |
| Provide 90-day volume reference | Daily | `volume_90d_ago` column |

## 11.3 CRM Team Responsibilities

| Task | Frequency |
|---|---|
| Confirm account status (Active/Dormant/Inactive) | Daily |
| Provide complaint count (last 30 days) | Daily |
| Confirm VIP status flags | Weekly |
| Provide AM assignment and IB name | Weekly |
| Respond to data quality issues raised by Analytics | Within 48 hours |

## 11.4 Retention Team Responsibilities

| Task | Frequency |
|---|---|
| Review and action the priority queue | Daily |
| Log all retention action outcomes | Same day as action |
| Report false positives (clients incorrectly flagged) | Weekly to Product Owner |
| Participate in quarterly model calibration review | Quarterly |

## 11.5 Compliance Considerations

1. **Data classification:** Client financial data is confidential. Platform must be behind authentication before production deployment.
2. **Audit trail:** Every score change is logged in `refresh_log`. Every retention action is logged in `retention_actions`. These tables should not be deleted.
3. **Explanability:** The "action reason" text and Score Factor Breakdown provide client-level explanability for all recommendations. This is important if clients ask why they were contacted.
4. **GDPR / data residency:** Synthetic data in pilot. When real data is loaded, confirm that client PII may be processed by the host environment.
5. **Model bias:** Periodically verify that the scoring model does not disproportionately flag clients from specific countries or account types due to data biases.

## 11.6 Data Quality Controls

| Control | Implementation |
|---|---|
| Required column check | `integrations/data_validator.validate_upload()` |
| Book type validation | Must be exactly `A-Book`, `B-Book`, or `M-Book` |
| Duplicate client check | Duplicate `client_id` values rejected |
| Negative equity warning | Flagged as warning (not error); may occur during processing |
| Quality score gate | Recommended: do not activate datasets below 80/100 |
| Refresh log | Every data load is logged in `refresh_log` SQLite table |

---

# SECTION 12 — OPERATING MANUAL

## 12.1 First-Time Setup

1. Confirm the application is running (`streamlit run app.py` or access the deployment URL)
2. The application auto-loads the 300-client sample dataset on first run
3. Navigate to **Settings (page 5)** to verify default thresholds are appropriate
4. Navigate to **Data Management (page 6)** to check data source status

## 12.2 Uploading Real Client Data

1. Open **Data Management** page
2. Click the **"Excel / CSV Upload"** tab
3. Drag-and-drop your file (`.xlsx` or `.csv`)
4. Review the validation results:
   - Red errors must be fixed before activation
   - Yellow warnings should be investigated but will not block upload
   - Target quality score ≥ 80
5. Click **"Activate This Dataset"**
6. All seven pages update automatically with the new data

**Column mapping:** The upload format uses date columns (`last_login_date`) which are automatically converted to day-count integers. See Appendix C for the complete column name mapping.

## 12.3 Daily Analysis Workflow

**Morning (08:00–09:00):**
1. Open **Executive Dashboard** — review any change in "Clients At Risk" vs yesterday
2. Note any new "Critical" or "Elevated" priority clients
3. Open **Action Center** — review own client queue if AM; review team queue if manager
4. Identify clients requiring same-day contact

**During the day:**
- After each retention call, log the outcome in **Model Validation → Retention Effectiveness → Log a Retention Action**

**End of day:**
- If data has been refreshed, spot-check **Client List** for any new high-risk flags

## 12.4 Interpreting Scores

| Score | Green Zone | Amber Zone | Red Zone |
|---|---|---|---|
| Retention Risk | < 30 (low risk) | 30–59 | ≥ 60 (high risk) |
| Commercial Value | > 70 (very valuable) | 40–70 | < 40 |
| Profitability | > 60 | 30–60 | < 30 |
| Reactivation | > 65 (strong candidate) | 40–65 | < 40 |
| VIP Upside | > 65 (upgrade candidate) | 40–65 | < 40 |
| Health Score | > 60 | 40–60 | < 40 |

## 12.5 Adjusting Settings

**When to raise the High Risk threshold:**
- Your team is overwhelmed by the size of the action queue
- Many flagged clients are not actually leaving (high false positive rate)

**When to lower the High Risk threshold:**
- Clients are churning without being flagged
- Recent losses suggest the model is missing at-risk clients

**When to adjust band points (Business Rules Engine):**
- Only after completing a quarterly validation review
- Document the change and the evidence that justified it

## 12.6 Reviewing Model Validation

1. Open **Model Validation** page
2. Tab 1 (Prediction Accuracy): Are accuracy metrics above targets (>75% churn, >80% withdrawal)?
3. Tab 2 (Score Factor Breakdown): For a recently-churned client, did the model correctly flag high risk factors?
4. Tab 3 (Retention Effectiveness): Which action type has the highest success rate? Are AMs using the most effective actions?
5. Tab 5 (Data Snapshots): How many dates have been captured? Is the database growing as expected?

---

# SECTION 13 — APPENDICES

## Appendix A — Data Dictionary

Complete list of all 46+ columns in the internal schema after scoring:

| # | Column | Type | Source | Description |
|---|---|---|---|---|
| 1 | client_id | str | CRM | Unique account identifier |
| 2 | client_name | str | CRM | Full client name |
| 3 | country | str | CRM | Country of residence |
| 4 | account_manager | str | CRM | Assigned AM name |
| 5 | ib_name | str | CRM | Introducing broker name |
| 6 | account_type | str | CRM | ECN / Standard / VIP / Islamic / Pro / Micro |
| 7 | book_type | str | Trading platform | A-Book / B-Book / M-Book |
| 8 | lifetime_deposits | float | CRM | Cumulative total deposits ($) |
| 9 | withdrawals_total | float | CRM | Cumulative total withdrawals ($) |
| 10 | net_deposits | float | Derived | lifetime_deposits − withdrawals_total |
| 11 | current_equity | float | Trading platform | Current account balance ($) |
| 12 | equity_30d_ago | float | Trading platform / BI | Balance 30 days prior ($) |
| 13 | login_days_ago | int | CRM | Days since last login |
| 14 | last_deposit_days_ago | int | CRM | Days since last deposit |
| 15 | last_withdrawal_days_ago | int | CRM | Days since last withdrawal |
| 16 | withdrawal_amount_last_30d | float | CRM | Withdrawal value in last 30 days ($) |
| 17 | trading_volume_last_30d | float | Trading platform | Total notional volume, last 30 days |
| 18 | trading_volume_previous_30d | float | Trading platform / BI | Notional volume, days 31–60 ago |
| 19 | volume_90d_ago | float | Trading platform / BI | Volume reference 90 days ago |
| 20 | number_of_redeposits | int | CRM | Count of deposit events after first |
| 21 | complaints_last_30d | int | CRM | Complaint count last 30 days |
| 22 | open_tickets | int | CRM | Live open support tickets |
| 23 | total_deposits_count | int | Derived | redeposits + 1 |
| 24 | spread_commission_revenue | float | Trading platform | Monthly spread income ($) |
| 25 | commission_revenue | float | Trading platform | Monthly commission income ($) |
| 26 | swap_revenue | float | Trading platform | Monthly swap income ($) |
| 27 | captured_client_losses | float | Trading platform | B/M-Book: net client P&L captured ($) |
| 28 | net_company_pnl | float | Trading platform | Monthly total profit to company ($) |
| 29 | company_pnl_from_client | float | Trading platform | Alias for net_company_pnl |
| 30 | vip_status | bool | CRM | True if VIP designation |
| 31 | client_tenure_days | int | CRM | Days since account opened |
| 32 | account_status | str | Derived | Active (<30d) / Dormant (30–90d) / Inactive (>90d) |
| 33 | retention_risk_score | float | Scoring engine | 0–100 |
| 34 | commercial_value_score | float | Scoring engine | 0–100 |
| 35 | profitability_score | float | Scoring engine | 0–100 |
| 36 | reactivation_score | float | Scoring engine | 0–100 |
| 37 | vip_upside_score | float | Scoring engine | 0–100 |
| 38 | client_health_score | float | Scoring engine | 0–100 |
| 39 | priority_score | float | Scoring engine | 0–100 |
| 40 | risk_level | str | Scoring engine | Low / Medium / High |
| 41 | value_level | str | Scoring engine | Low / Medium / High |
| 42 | health_label | str | Scoring engine | Critical / At Risk / Watchlist / Healthy / Excellent |
| 43 | segment | str | Scoring engine | 9-segment name |
| 44 | priority_level | str | Scoring engine | Normal / Elevated / Critical |
| 45 | recommended_action | str | Scoring engine | 11-rule action recommendation |
| 46 | recommended_owner | str | Scoring engine | Team routing |
| 47 | action_reason | str | Scoring engine | Plain-text score explanation |

---

## Appendix B — Formula Dictionary

| Formula | Source File | Line |
|---|---|---|
| `health = (100−risk)×0.5 + value×0.3 + profit×0.2` | utils/scoring.py | ~238 |
| `priority = risk×0.30 + value×0.25 + profit×0.30 + react×0.15` | utils/scoring.py | ~255 |
| `reactivation_peak = 105 days ago` | utils/scoring.py | ~165 |
| `M-Book profit = 0.6 × captured_losses + spread + commission + swap` | utils/rules_engine.py | ~200 |
| `normalize(x) = (x − min) / (max − min) × 100` | utils/rules_engine.py | ~217 |
| `net_deposits = lifetime_deposits − withdrawals_total` | integrations/data_mapper.py | ~160 |
| `account_status: Active if login<30, Dormant 30–90, Inactive >90` | integrations/data_mapper.py | ~240 |
| `withdrawal_pressure = withdrawal_30d / current_equity` | utils/rules_engine.py | ~83 |
| `volume_drop = (prev_vol − curr_vol) / prev_vol` | utils/rules_engine.py | ~85 |
| `equity_trend = (equity_30d_ago − current_equity) / equity_30d_ago` | utils/rules_engine.py | ~91 |

---

## Appendix C — BI Export Column Mapping

Columns the BI export should contain, and how they map to the internal schema:

| Export Column Name | Internal Column Name | Notes |
|---|---|---|
| client_id | client_id | No change |
| client_name | client_name | No change |
| country | country | No change |
| account_manager | account_manager | No change |
| ib_name | ib_name | No change |
| account_type | account_type | No change |
| book_type | book_type | Must be exactly "A-Book", "B-Book", or "M-Book" |
| lifetime_deposits | lifetime_deposits | No change |
| withdrawals_total | withdrawals_total | No change |
| current_equity | current_equity | No change |
| equity_30d_ago | equity_30d_ago | Balance 30 days ago |
| last_login_date | login_days_ago | Date converted to integer days ago by mapper |
| last_deposit_date | last_deposit_days_ago | Date converted to integer days ago by mapper |
| last_withdrawal_date | last_withdrawal_days_ago | Date converted to integer days ago by mapper |
| withdrawals_30d | withdrawal_amount_last_30d | Renamed by mapper |
| trading_volume_30d | trading_volume_last_30d | Renamed by mapper |
| trading_volume_previous_30d | trading_volume_previous_30d | No change |
| volume_90d_ago | volume_90d_ago | No change |
| spread_revenue | spread_commission_revenue | Renamed by mapper |
| commission_revenue | commission_revenue | No change |
| swap_revenue | swap_revenue | No change |
| company_pnl | company_pnl_from_client | Renamed by mapper |
| captured_client_losses | captured_client_losses | No change |
| number_of_redeposits | number_of_redeposits | No change |
| complaints | complaints_last_30d | Renamed by mapper |
| open_tickets | open_tickets | No change |
| client_tenure_months | client_tenure_days | Multiplied ×30 by mapper |
| vip_status | vip_status | Normalised to bool by mapper |

---

## Appendix D — Recommended CRM Integration Design

```
OneRoyal CRM
    │
    ├── GET /api/v1/clients?updated_since=YYYY-MM-DD
    │   Returns: client_id, client_name, country, account_manager, ib_name,
    │            account_type, book_type, lifetime_deposits, withdrawals_total,
    │            last_login_date, last_deposit_date, last_withdrawal_date,
    │            withdrawals_30d, number_of_redeposits, client_tenure_months,
    │            vip_status
    │
    ├── GET /api/v1/trading-metrics?client_ids=...
    │   Returns: client_id, current_equity, equity_30d_ago,
    │            trading_volume_30d, trading_volume_previous_30d, volume_90d_ago,
    │            spread_revenue, commission_revenue, swap_revenue,
    │            captured_client_losses, company_pnl
    │
    └── GET /api/v1/support?client_ids=...
        Returns: client_id, complaints_last_30d, open_tickets

Platform (integrations/crm_connector.py)
    │
    ├── get_clients()          → Raw client records
    ├── get_trading_metrics()  → Trading platform data
    └── get_tickets()          → CRM support data
            │
            ▼
    data_mapper.map_crm_response()
            │
            ▼
    validate_internal() → quality check
            │
            ▼
    score_dataframe()   → 6 scores
```

**Authentication:** HTTP Bearer token  
**Incremental pull:** Use `updated_since` parameter for daily delta pulls  
**Full refresh:** Weekly full pull to catch any missed updates

---

## Appendix E — Future Enhancements

| Priority | Enhancement | Business Value |
|---|---|---|
| High | PostgreSQL migration | Multi-user support, production scale |
| High | User authentication (OAuth2) | Security; role-based data access |
| High | Email/Slack daily digest | Proactive alerts without manual log-in |
| Medium | Automated outcome import from CRM | Eliminate manual logging; auto-feed Model Validation |
| Medium | CRM write-back: push action tasks | Close the loop; AMs see actions in their CRM |
| Medium | Score trend alerts: "Client risk increased >15 in 7 days" | Early warning system |
| Medium | Mobile-responsive layout | Field AM usage on phones/tablets |
| Low | ML challenger model | Improve accuracy beyond rules-based bands |
| Low | Natural language action reasons (LLM-generated) | Richer talking points for AMs |
| Low | Multi-currency support | For brokerages with multi-currency accounts |
| Low | API for external consumption | Allow other tools to pull scores via REST |

---

*End of Document*

**OneRoyal Client Intelligence Platform — Handover Manual v1.0**  
*Branch: `claude/oneroyal-client-platform-pfb0lk`*
