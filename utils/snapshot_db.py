# utils/snapshot_db.py
# Historical scoring snapshot database — SQLite-based, append-only.
# Every data refresh creates a new dated snapshot row per client.

import sqlite3
import os
import datetime
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "snapshots.db"

OUTCOME_TYPES   = ["churn", "large_withdrawal", "full_withdrawal",
                   "dormancy", "redeposit", "reactivation", "vip_upgrade"]
ACTION_TYPES    = ["Retention Call", "Cashback Offer", "Bonus Offer",
                   "VIP Meeting", "Account Manager Follow-Up", "Email Campaign"]
ACTION_OUTCOMES = ["success", "failure", "pending"]


# ─────────────────────────────────────────────────────────────────────────────
# Connection + Init
# ─────────────────────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    os.makedirs(DB_PATH.parent, exist_ok=True)
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c


def init_db():
    """Create all tables and indexes if they don't exist."""
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS score_snapshots (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date         DATE    NOT NULL,
            client_id             TEXT    NOT NULL,
            retention_risk_score  REAL,
            commercial_value_score REAL,
            profitability_score   REAL,
            reactivation_score    REAL,
            vip_upside_score      REAL,
            client_health_score   REAL,
            priority_score        REAL,
            recommended_action    TEXT,
            recommended_owner     TEXT,
            data_source           TEXT DEFAULT 'sample',
            created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(snapshot_date, client_id)
        );

        CREATE TABLE IF NOT EXISTS client_outcomes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            outcome_date  DATE    NOT NULL,
            client_id     TEXT    NOT NULL,
            outcome_type  TEXT    NOT NULL,
            outcome_value REAL,
            notes         TEXT,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS retention_actions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            action_date DATE    NOT NULL,
            client_id   TEXT    NOT NULL,
            action_type TEXT    NOT NULL,
            assigned_to TEXT,
            outcome     TEXT DEFAULT 'pending',
            notes       TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS refresh_log (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            refresh_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_source        TEXT NOT NULL,
            records_processed  INTEGER,
            status             TEXT NOT NULL,
            duration_seconds   REAL,
            error_message      TEXT
        );

        CREATE TABLE IF NOT EXISTS integration_config (
            key        TEXT PRIMARY KEY,
            value      TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_snap_date   ON score_snapshots(snapshot_date);
        CREATE INDEX IF NOT EXISTS idx_snap_client ON score_snapshots(client_id);
        CREATE INDEX IF NOT EXISTS idx_out_client  ON client_outcomes(client_id);
        CREATE INDEX IF NOT EXISTS idx_out_type    ON client_outcomes(outcome_type);
        CREATE INDEX IF NOT EXISTS idx_act_client  ON retention_actions(client_id);
        """)


# ─────────────────────────────────────────────────────────────────────────────
# Snapshots
# ─────────────────────────────────────────────────────────────────────────────

def save_snapshot(scored_df: pd.DataFrame, source: str = "sample"):
    """Upsert today's scores for every client. Never overwrites a different date."""
    today = str(datetime.date.today())
    snap_cols = [
        "client_id", "retention_risk_score", "commercial_value_score",
        "profitability_score", "reactivation_score", "vip_upside_score",
        "client_health_score", "priority_score",
        "recommended_action", "recommended_owner",
    ]
    present = [c for c in snap_cols if c in scored_df.columns]

    with _conn() as c:
        for _, row in scored_df.iterrows():
            r = {"snapshot_date": today, "data_source": source}
            for col in present:
                r[col] = row[col]
            keys   = ", ".join(r.keys())
            ph     = ", ".join("?" * len(r))
            c.execute(
                f"INSERT OR REPLACE INTO score_snapshots ({keys}) VALUES ({ph})",
                list(r.values()),
            )


def get_snapshots(start_date=None, end_date=None) -> pd.DataFrame:
    where, params = "WHERE 1=1", []
    if start_date:
        where += " AND snapshot_date >= ?"; params.append(str(start_date))
    if end_date:
        where += " AND snapshot_date <= ?"; params.append(str(end_date))
    with _conn() as c:
        return pd.read_sql_query(
            f"SELECT * FROM score_snapshots {where} ORDER BY snapshot_date", c, params=params
        )


def get_snapshot_dates() -> list:
    with _conn() as c:
        rows = c.execute(
            "SELECT DISTINCT snapshot_date FROM score_snapshots ORDER BY snapshot_date"
        ).fetchall()
    return [r["snapshot_date"] for r in rows]


def get_latest_snapshot() -> pd.DataFrame:
    with _conn() as c:
        latest = c.execute(
            "SELECT MAX(snapshot_date) AS d FROM score_snapshots"
        ).fetchone()["d"]
        if not latest:
            return pd.DataFrame()
        return pd.read_sql_query(
            "SELECT * FROM score_snapshots WHERE snapshot_date = ?", c, params=[latest]
        )


def count_snapshots() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM score_snapshots").fetchone()[0]


# ─────────────────────────────────────────────────────────────────────────────
# Outcomes
# ─────────────────────────────────────────────────────────────────────────────

def save_outcome(client_id: str, outcome_type: str,
                 outcome_date=None, outcome_value=None, notes: str = ""):
    if outcome_date is None:
        outcome_date = str(datetime.date.today())
    with _conn() as c:
        c.execute(
            """INSERT INTO client_outcomes
               (outcome_date, client_id, outcome_type, outcome_value, notes)
               VALUES (?, ?, ?, ?, ?)""",
            (str(outcome_date), client_id, outcome_type, outcome_value, notes),
        )


def get_outcomes(outcome_type=None, start_date=None) -> pd.DataFrame:
    where, params = "WHERE 1=1", []
    if outcome_type:
        where += " AND outcome_type = ?"; params.append(outcome_type)
    if start_date:
        where += " AND outcome_date >= ?"; params.append(str(start_date))
    with _conn() as c:
        return pd.read_sql_query(
            f"SELECT * FROM client_outcomes {where} ORDER BY outcome_date DESC",
            c, params=params
        )


def count_outcomes() -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM client_outcomes").fetchone()[0]


# ─────────────────────────────────────────────────────────────────────────────
# Retention Actions
# ─────────────────────────────────────────────────────────────────────────────

def save_retention_action(client_id: str, action_type: str,
                          assigned_to: str = "", outcome: str = "pending",
                          notes: str = "", action_date=None):
    if action_date is None:
        action_date = str(datetime.date.today())
    with _conn() as c:
        c.execute(
            """INSERT INTO retention_actions
               (action_date, client_id, action_type, assigned_to, outcome, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (str(action_date), client_id, action_type, assigned_to, outcome, notes),
        )


def get_retention_actions() -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query(
            "SELECT * FROM retention_actions ORDER BY action_date DESC", c
        )


# ─────────────────────────────────────────────────────────────────────────────
# Refresh Log
# ─────────────────────────────────────────────────────────────────────────────

def log_refresh(data_source: str, records: int, status: str,
                duration: float = 0.0, error: str = ""):
    with _conn() as c:
        c.execute(
            """INSERT INTO refresh_log
               (data_source, records_processed, status, duration_seconds, error_message)
               VALUES (?, ?, ?, ?, ?)""",
            (data_source, records, status, duration, error),
        )


def get_refresh_log(limit: int = 20) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query(
            f"SELECT * FROM refresh_log ORDER BY refresh_time DESC LIMIT {limit}", c
        )


# ─────────────────────────────────────────────────────────────────────────────
# Integration Config
# ─────────────────────────────────────────────────────────────────────────────

def save_config(key: str, value: str):
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO integration_config (key, value) VALUES (?, ?)",
            (key, value),
        )


def get_config(key: str, default: str = "") -> str:
    with _conn() as c:
        row = c.execute(
            "SELECT value FROM integration_config WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row else default


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def has_historical_data() -> bool:
    return len(get_snapshot_dates()) > 1


def snapshot_summary() -> dict:
    dates = get_snapshot_dates()
    return {
        "total_snapshots": count_snapshots(),
        "unique_dates":    len(dates),
        "oldest_date":     dates[0]  if dates else None,
        "latest_date":     dates[-1] if dates else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Historical Seed (called once on first run)
# ─────────────────────────────────────────────────────────────────────────────

def seed_historical_data(scored_df: pd.DataFrame, months: int = 12):
    """
    Populate 12 months of simulated historical snapshots + outcomes.
    Outcomes are correlated with scores so validation charts are meaningful.
    Only inserts rows that don't already exist (safe to call repeatedly).
    """
    import numpy as np
    rng   = np.random.default_rng(42)
    today = datetime.date.today()

    score_cols = [
        "retention_risk_score", "commercial_value_score", "profitability_score",
        "reactivation_score",   "vip_upside_score",       "client_health_score",
        "priority_score",
    ]

    # Churn probability per risk band (annualised → per-month fraction)
    CHURN_PROB = {(80,101):0.40, (60,80):0.20, (40,60):0.10, (20,40):0.04, (0,20):0.01}
    WD_PROB    = {(80,101):0.50, (60,80):0.30, (40,60):0.12, (0, 60):0.03}
    REACT_PROB = 0.15  # probability dormant client reactivates per month (if react score >= 50)

    with _conn() as c:
        for mo in range(months, 0, -1):
            snap_date = today - datetime.timedelta(days=30 * mo)
            snap_str  = str(snap_date)
            age_factor = mo / months  # older snapshots have more noise

            for _, row in scored_df.iterrows():
                cid = row["client_id"]

                # Score snapshot with slight historical drift
                r = {
                    "snapshot_date":    snap_str,
                    "client_id":        cid,
                    "data_source":      "historical_seed",
                    "recommended_action": row.get("recommended_action", ""),
                    "recommended_owner":  row.get("recommended_owner",  ""),
                }
                for col in score_cols:
                    if col in row.index:
                        noise   = rng.uniform(-6, 6) * age_factor
                        r[col]  = float(np.clip(float(row[col]) + noise, 0, 100))

                keys = ", ".join(r.keys())
                ph   = ", ".join("?" * len(r))
                c.execute(
                    f"INSERT OR IGNORE INTO score_snapshots ({keys}) VALUES ({ph})",
                    list(r.values()),
                )

                risk  = float(row.get("retention_risk_score", 50))
                react = float(row.get("reactivation_score",   50))
                login = int(row.get("login_days_ago", 0))

                # Simulated churn outcomes
                for (lo, hi), annual_prob in CHURN_PROB.items():
                    if lo <= risk < hi and rng.random() < annual_prob / months:
                        c.execute(
                            """INSERT OR IGNORE INTO client_outcomes
                               (outcome_date,client_id,outcome_type,notes)
                               VALUES (?,?,'churn','simulated')""",
                            (snap_str, cid),
                        )

                # Simulated large withdrawal outcomes
                for (lo, hi), annual_prob in WD_PROB.items():
                    if lo <= risk < hi and rng.random() < annual_prob / months:
                        wd_val = float(row.get("current_equity", 5000)) * rng.uniform(0.30, 0.70)
                        c.execute(
                            """INSERT OR IGNORE INTO client_outcomes
                               (outcome_date,client_id,outcome_type,outcome_value,notes)
                               VALUES (?,?,'large_withdrawal',?,'simulated')""",
                            (snap_str, cid, round(wd_val, 2)),
                        )

                # Simulated reactivation
                if login >= 30 and react >= 50 and rng.random() < REACT_PROB / months:
                    c.execute(
                        """INSERT OR IGNORE INTO client_outcomes
                           (outcome_date,client_id,outcome_type,notes)
                           VALUES (?,?,'reactivation','simulated')""",
                        (snap_str, cid),
                    )

                # Simulated redeposit (healthy clients)
                if risk < 40 and rng.random() < 0.08 / months:
                    dep_val = float(row.get("lifetime_deposits", 5000)) * rng.uniform(0.05, 0.25)
                    c.execute(
                        """INSERT OR IGNORE INTO client_outcomes
                           (outcome_date,client_id,outcome_type,outcome_value,notes)
                           VALUES (?,?,'redeposit',?,'simulated')""",
                        (snap_str, cid, round(dep_val, 2)),
                    )

        # Seed retention actions (last 6 months, high-risk clients only)
        SUCCESS = {
            "Retention Call": 0.45, "Cashback Offer": 0.38,
            "Bonus Offer": 0.32,    "VIP Meeting": 0.60,
            "Account Manager Follow-Up": 0.25, "Email Campaign": 0.15,
        }
        high_risk = scored_df[scored_df["retention_risk_score"] >= 60].head(80)
        for _, row in high_risk.iterrows():
            for mo in range(6, 0, -1):
                if rng.random() < 0.45:
                    atype    = rng.choice(list(SUCCESS.keys()))
                    act_date = str(today - datetime.timedelta(days=30 * mo))
                    outcome  = "success" if rng.random() < SUCCESS[atype] else "failure"
                    c.execute(
                        """INSERT INTO retention_actions
                           (action_date,client_id,action_type,assigned_to,outcome,notes)
                           VALUES (?,?,?,?,?,'simulated')""",
                        (act_date, row["client_id"], atype,
                         row.get("account_manager", "Team"), outcome),
                    )
