# utils/user_db.py
# SQLite-backed user store: schema, CRUD, password hashing, audit log.
# All list fields (regions, countries, etc.) stored as JSON strings.

import hashlib
import hmac
import os
import base64
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "users.db")
_PBKDF2_ITERS = 260_000  # NIST SP 800-132 recommended minimum (2023)


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """PBKDF2-SHA256 hash with a random 16-byte salt, base64-encoded."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERS)
    return base64.b64encode(salt + dk).decode("utf-8")


def verify_password(password: str, stored_hash: str) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    try:
        raw = base64.b64decode(stored_hash.encode("utf-8"))
        salt, stored_dk = raw[:16], raw[16:]
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERS)
        return hmac.compare_digest(dk, stored_dk)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    for field in ("assigned_regions", "assigned_countries",
                  "assigned_managers", "assigned_team_members"):
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                d[field] = []
    d["force_password_change"] = bool(d.get("force_password_change", 0))
    return d


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Schema & seeding
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create tables if they don't exist and seed default users on first run."""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name             TEXT    NOT NULL,
                email                 TEXT    NOT NULL UNIQUE,
                password_hash         TEXT    NOT NULL,
                role                  TEXT    NOT NULL,
                status                TEXT    NOT NULL DEFAULT 'active',
                assigned_regions      TEXT    NOT NULL DEFAULT '[]',
                assigned_countries    TEXT    NOT NULL DEFAULT '[]',
                assigned_managers     TEXT    NOT NULL DEFAULT '[]',
                assigned_team_members TEXT    NOT NULL DEFAULT '[]',
                force_password_change INTEGER NOT NULL DEFAULT 0,
                created_at            TEXT    NOT NULL,
                updated_at            TEXT    NOT NULL,
                last_login            TEXT,
                last_password_reset   TEXT,
                created_by            TEXT,
                last_modified_by      TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    TEXT NOT NULL,
                actor_email  TEXT NOT NULL,
                action       TEXT NOT NULL,
                target_email TEXT,
                details      TEXT
            );
        """)
        count = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            _seed_defaults(c)


def _seed_defaults(c: sqlite3.Connection) -> None:
    """Insert the four default users on a fresh database."""
    now = _now()
    # (full_name, email, password, role, force_pwd, regions, countries, managers, team)
    seeds = [
        ("System Admin",     "admin@oneroyal.com",    "ChangeMe123!",
         "Admin",                    1, [], [], [], []),
        ("James Williams",   "cco@oneroyal.com",      "TestUser123!",
         "Chief Commercial Officer", 0, [], [], [], []),
        ("Omar Al-Mansouri", "rm.gcc@oneroyal.com",   "TestUser123!",
         "Regional Manager",         0, ["GCC"], [], [],
         ["Sarah Johnson", "Mohammed Al-Rashid", "David Chen"]),
        ("Sarah Johnson",    "am.sarah@oneroyal.com", "TestUser123!",
         "Account Manager",          0, [], [], [], []),
    ]
    for full_name, email, pwd, role, force_pwd, regions, countries, managers, team in seeds:
        c.execute("""
            INSERT INTO users
                (full_name, email, password_hash, role, status,
                 assigned_regions, assigned_countries, assigned_managers,
                 assigned_team_members, force_password_change,
                 created_at, updated_at, created_by)
            VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, 'system')
        """, (
            full_name, email, hash_password(pwd), role,
            json.dumps(regions), json.dumps(countries),
            json.dumps(managers), json.dumps(team),
            force_pwd, now, now,
        ))


# ---------------------------------------------------------------------------
# User reads
# ---------------------------------------------------------------------------

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
    return _row_to_dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_dict(row) if row else None


def get_all_users() -> List[Dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM users ORDER BY role, full_name"
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# User writes
# ---------------------------------------------------------------------------

def create_user(
    full_name: str,
    email: str,
    password: str,
    role: str,
    status: str = "active",
    assigned_regions: Optional[List[str]] = None,
    assigned_countries: Optional[List[str]] = None,
    assigned_managers: Optional[List[str]] = None,
    assigned_team_members: Optional[List[str]] = None,
    force_password_change: bool = True,
    created_by: str = "system",
) -> int:
    """Insert a new user. Returns the new row id."""
    now = _now()
    with _conn() as c:
        cur = c.execute("""
            INSERT INTO users
                (full_name, email, password_hash, role, status,
                 assigned_regions, assigned_countries, assigned_managers,
                 assigned_team_members, force_password_change,
                 created_at, updated_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            full_name.strip(), email.strip().lower(),
            hash_password(password), role, status,
            json.dumps(assigned_regions or []),
            json.dumps(assigned_countries or []),
            json.dumps(assigned_managers or []),
            json.dumps(assigned_team_members or []),
            int(force_password_change), now, now, created_by,
        ))
        return cur.lastrowid


def update_user(
    user_id: int,
    full_name: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    assigned_regions: Optional[List[str]] = None,
    assigned_countries: Optional[List[str]] = None,
    assigned_managers: Optional[List[str]] = None,
    assigned_team_members: Optional[List[str]] = None,
    force_password_change: Optional[bool] = None,
    modified_by: str = "system",
) -> None:
    """Partial update: only supplied fields are changed."""
    fields: List[str] = []
    values: List[Any] = []
    if full_name is not None:
        fields.append("full_name = ?"); values.append(full_name.strip())
    if role is not None:
        fields.append("role = ?"); values.append(role)
    if status is not None:
        fields.append("status = ?"); values.append(status)
    if assigned_regions is not None:
        fields.append("assigned_regions = ?"); values.append(json.dumps(assigned_regions))
    if assigned_countries is not None:
        fields.append("assigned_countries = ?"); values.append(json.dumps(assigned_countries))
    if assigned_managers is not None:
        fields.append("assigned_managers = ?"); values.append(json.dumps(assigned_managers))
    if assigned_team_members is not None:
        fields.append("assigned_team_members = ?"); values.append(json.dumps(assigned_team_members))
    if force_password_change is not None:
        fields.append("force_password_change = ?"); values.append(int(force_password_change))
    if not fields:
        return
    fields += ["updated_at = ?", "last_modified_by = ?"]
    values += [_now(), modified_by, user_id]
    with _conn() as c:
        c.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)


def reset_password(user_id: int, new_password: str, modified_by: str = "system") -> None:
    now = _now()
    with _conn() as c:
        c.execute("""
            UPDATE users
            SET password_hash = ?, last_password_reset = ?, updated_at = ?, last_modified_by = ?
            WHERE id = ?
        """, (hash_password(new_password), now, now, modified_by, user_id))


def update_last_login(user_id: int) -> None:
    with _conn() as c:
        c.execute("UPDATE users SET last_login = ? WHERE id = ?", (_now(), user_id))


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

def log_audit(
    actor_email: str,
    action: str,
    target_email: Optional[str] = None,
    details: Optional[str] = None,
) -> None:
    with _conn() as c:
        c.execute("""
            INSERT INTO audit_log (timestamp, actor_email, action, target_email, details)
            VALUES (?, ?, ?, ?, ?)
        """, (_now(), actor_email, action, target_email, details))


def get_audit_log(limit: int = 200, offset: int = 0) -> List[Dict[str, Any]]:
    with _conn() as c:
        rows = c.execute("""
            SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()
    return [dict(r) for r in rows]
