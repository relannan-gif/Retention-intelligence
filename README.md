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
| **User Management** | Create, edit, deactivate users · RBAC · Audit Log |

## Data Input

Upload a single Excel / CSV file using the BI export spec columns (see Data Management page). Required fields: `client_id`, `client_name`, `country`, `book_type`, `lifetime_deposits`, `current_equity`.

## User Management & Permissions

### Roles

| Level | Roles | Data Visibility |
|-------|-------|----------------|
| **L1 — Full Access** | Chairman, CCO, Head of Sales, Head of Retention, Head of Marketing, Admin | All clients, all countries, all regions |
| **L2 — Regional / Team** | Sales Director, Regional Manager | Assigned regions/countries/team members only |
| **L3 — Own Clients** | Business Developer, Account Manager, Sales | Own clients only (where they are AM, BD, or sales_owner) |

### Page Access

| Page | L1 | L2 | L3 |
|------|----|----|----|
| Executive Dashboard | ✅ | ✅ | ✅ |
| Client List | ✅ | ✅ | ✅ |
| Scoring Engine | ✅ (edit) | ✅ (read-only) | ✅ (read-only) |
| Action Center | ✅ | ✅ | ✅ |
| Settings | ✅ | ❌ | ❌ |
| Data Management | ✅ | ❌ | ❌ |
| Model Validation | ✅ | ❌ | ❌ |
| User Management | ✅ | ❌ | ❌ |

### Default Users (development)

| Email | Password | Role | Notes |
|-------|----------|------|-------|
| `admin@oneroyal.com` | `ChangeMe123!` | Admin | Force password change on first login |
| `cco@oneroyal.com` | `TestUser123!` | Chief Commercial Officer | Full access, sees all 300 clients |
| `rm.gcc@oneroyal.com` | `TestUser123!` | Regional Manager | GCC region only (~53 clients) |
| `am.sarah@oneroyal.com` | `TestUser123!` | Account Manager | Sarah Johnson's own clients (~45 clients) |

### How Data Filtering Works

All client data is filtered by `filter_data_for_user(df, user)` in `utils/permissions.py` **before rendering**, on every page. UI hiding is not relied on — the DataFrame itself is filtered.

L2 users match on: `region`, `country`, `regional_manager`, `sales_director`, `account_manager` (team), `business_developer` (team).

L3 users match on: `account_manager`, `business_developer`, `sales_owner`.

### How to Create Users

1. Log in as Admin or any Level-1 role.
2. Navigate to **User Management** → **Create User** tab.
3. Fill in name, email, role, scope, and password.
4. Click **Create User**. The user can log in immediately.

### How to Reset a Password

1. In **User Management** → **Users** tab, select the user.
2. Click **Reset Password**, enter the new password twice, and submit.
3. Optionally check "Force password change on next login".

### How to Deactivate a User

1. In **User Management** → **Users** tab, select the user.
2. Click **Deactivate**. The account is immediately blocked from logging in.
3. Deactivated users are retained in the DB (not deleted).

### Audit Log

Every login, logout, user creation, edit, deactivation, and password reset is recorded in the `audit_log` table (SQLite). View it in **User Management** → **Audit Log** tab.

---

## Scoring Model (v2.0)

- **Priority Score** = Risk × 35% + Value × 25% + Profitability × 35% + Upside × 5%
- **Book-type-aware profitability:** A-Book (commission + swap + spread), B-Book / M-Book (captured losses + commission + swap)
- **9-segment matrix** based on Risk × Value quadrants
