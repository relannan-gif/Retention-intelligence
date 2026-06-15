# Retention Intelligence Platform

**Current Release:** v1.0-test
**Status:** Ready for UAT testing

## Overview

A rules-based client retention intelligence platform for forex brokerages. Scores each client across six dimensions — Retention Risk, Commercial Value, Profitability, Reactivation Potential, Upside Potential, and Client Health — and recommends targeted retention actions.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Pages

| Page | Description |
|------|-------------|
| Executive Dashboard | KPI summary, segment matrix, top-risk clients |
| Client List | Full scored client table with filtering and export |
| Scoring Engine | Weight tuning and score distributions |
| Action Center | Prioritised action queue for retention teams |
| Settings | Thresholds, activity parameters, and display options |
| Data Management | Upload, CRM API, Holistics feed, data quality monitoring |
| Model Validation | Backtesting and segment simulation |

## Data Input

Upload a single Excel / CSV file using the BI export spec columns (see Data Management page). Required fields: `client_id`, `client_name`, `country`, `book_type`, `lifetime_deposits`, `current_equity`.

## Scoring Model (v2.0)

- **Priority Score** = Risk × 35% + Value × 25% + Profitability × 35% + Upside × 5%
- **Book-type-aware profitability:** A-Book (commission + swap + spread), B-Book / M-Book (captured losses + commission + swap)
- **9-segment matrix** based on Risk × Value quadrants
