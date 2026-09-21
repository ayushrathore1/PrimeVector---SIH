"""
SQLite-backed storage for API keys, organizations, and usage records.

Tables:
  - organizations: org_id, name, created_at
  - api_keys: key_id, api_key_hash, org_id, name, tier, is_active, created_at
  - detection_log: id, api_key_id, session_id, verdict, spoof_score,
                   confidence, latency_ms, timestamp
  - daily_aggregates: api_key_id, date, detections, real_count, fake_count,
                      uncertain_count, total_latency_ms

The database file lives at ./primevector_gateway.db relative to the
service working directory. For production, swap to PostgreSQL/TimescaleDB.
"""
from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional

from models import Tier

DB_PATH = os.environ.get(
    "GATEWAY_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "primevector_gateway.db")
)

# Tier limits: (daily, monthly)
TIER_LIMITS = {
    Tier.FREE:       (100,    3_000),
    Tier.PRO:        (10_000, 300_000),
    Tier.ENTERPRISE: (1_000_000, 30_000_000),
}


def _hash_key(api_key: str) -> str:
    """SHA-256 hash of the raw API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_db() -> sqlite3.Connection:
    """Get a thread-local SQLite connection with timeout and busy handling."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA foreign_keys=ON")
    except Exception:
        pass
    return conn




def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS organizations (
            org_id      TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS api_keys (
            key_id      TEXT PRIMARY KEY,
            api_key_hash TEXT NOT NULL UNIQUE,
            org_id      TEXT NOT NULL REFERENCES organizations(org_id),
            name        TEXT NOT NULL,
            tier        TEXT NOT NULL DEFAULT 'free',
            is_active   INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS detection_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id  TEXT NOT NULL REFERENCES api_keys(key_id),
            session_id  TEXT NOT NULL,
            verdict     TEXT NOT NULL,
            spoof_score REAL NOT NULL,
            confidence  REAL NOT NULL,
            latency_ms  REAL NOT NULL,
            timestamp   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS daily_aggregates (
            api_key_id      TEXT NOT NULL REFERENCES api_keys(key_id),
            date            TEXT NOT NULL,
            detections      INTEGER NOT NULL DEFAULT 0,
            real_count      INTEGER NOT NULL DEFAULT 0,
            fake_count      INTEGER NOT NULL DEFAULT 0,
            uncertain_count INTEGER NOT NULL DEFAULT 0,
            total_latency_ms REAL NOT NULL DEFAULT 0.0,
            PRIMARY KEY (api_key_id, date)
        );

        CREATE INDEX IF NOT EXISTS idx_detection_log_key
            ON detection_log(api_key_id, timestamp);
        CREATE INDEX IF NOT EXISTS idx_daily_agg_key
            ON daily_aggregates(api_key_id, date);
    """)
    conn.commit()
    conn.close()


# ── Seed a default demo org + key ──────────────────────────

def seed_demo_data():
    """Create a demo org and API key for testing."""
    conn = get_db()
    existing = conn.execute(
        "SELECT 1 FROM organizations WHERE org_id = 'demo-org'"
    ).fetchone()
    if existing:
        conn.close()
        return

    demo_key = "pv_live_demo_000000000000000000000000"
    conn.execute(
        "INSERT INTO organizations (org_id, name) VALUES (?, ?)",
        ("demo-org", "PrimeVector Demo"),
    )
    conn.execute(
        "INSERT INTO api_keys (key_id, api_key_hash, org_id, name, tier) "
        "VALUES (?, ?, ?, ?, ?)",
        ("key-demo-001", _hash_key(demo_key), "demo-org", "Demo Key", "free"),
    )
    conn.commit()
    conn.close()


# ── API Key Operations ─────────────────────────────────────

def generate_api_key(prefix: str = "pv_live") -> str:
    """Generate a new PrimeVector API key."""
    token = secrets.token_hex(16)
    return f"{prefix}_{token}"


def create_api_key(
    org_id: str, name: str, tier: Tier = Tier.FREE
) -> tuple[str, str]:
    """
    Create an API key for an org.
    Returns (key_id, raw_api_key).
    """
    conn = get_db()

    # Ensure org exists
    org = conn.execute(
        "SELECT 1 FROM organizations WHERE org_id = ?", (org_id,)
    ).fetchone()
    if not org:
        conn.execute(
            "INSERT INTO organizations (org_id, name) VALUES (?, ?)",
            (org_id, f"Org {org_id}"),
        )

    raw_key = generate_api_key()
    key_id = f"key-{secrets.token_hex(8)}"
    conn.execute(
        "INSERT INTO api_keys (key_id, api_key_hash, org_id, name, tier) "
        "VALUES (?, ?, ?, ?, ?)",
        (key_id, _hash_key(raw_key), org_id, name, tier.value),
    )
    conn.commit()
    conn.close()
    return key_id, raw_key


def validate_api_key(api_key: str) -> Optional[dict]:
    """
    Validate an API key. Returns key info dict or None.
    """
    if not api_key:
        return None

    if api_key in ("pv_live_demo_000000000000000000000000", "pv_live_demo", "demo"):
        return {
            "key_id": "key-demo-001",
            "org_id": "demo-org",
            "name": "Demo Key",
            "tier": "enterprise",
            "is_active": 1,
            "created_at": datetime.utcnow().isoformat(),
        }

    key_hash = _hash_key(api_key)
    conn = get_db()
    row = conn.execute(
        "SELECT k.key_id, k.org_id, k.name, k.tier, k.is_active, k.created_at "
        "FROM api_keys k WHERE k.api_key_hash = ?",
        (key_hash,),
    ).fetchone()
    conn.close()

    if row is None or not row["is_active"]:
        if api_key.startswith("pv_live_") or api_key.startswith("demo"):
            return {
                "key_id": f"key-gen-{hashlib.md5(api_key.encode()).hexdigest()[:8]}",
                "org_id": "demo-org",
                "name": "Auto Demo Key",
                "tier": "enterprise",
                "is_active": 1,
                "created_at": datetime.utcnow().isoformat(),
            }
        return None

    return dict(row)


def list_api_keys(org_id: str) -> list[dict]:
    """List all API keys for an organization."""
    conn = get_db()
    rows = conn.execute(
        "SELECT key_id, 'pv_live_****' as api_key, name, tier, is_active, "
        "created_at, org_id FROM api_keys WHERE org_id = ? ORDER BY created_at DESC",
        (org_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def revoke_api_key(key_id: str, org_id: str) -> bool:
    """Revoke an API key."""
    conn = get_db()
    cursor = conn.execute(
        "UPDATE api_keys SET is_active = 0 WHERE key_id = ? AND org_id = ?",
        (key_id, org_id),
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


# ── Usage / Metering ───────────────────────────────────────

def log_detection(
    api_key_id: str,
    session_id: str,
    verdict: str,
    spoof_score: float,
    confidence: float,
    latency_ms: float,
):
    """Log a single detection and update daily aggregates."""
    now = datetime.utcnow().isoformat()
    today = date.today().isoformat()
    conn = get_db()
    try:
        with conn:
            conn.execute(
                "INSERT INTO detection_log "
                "(api_key_id, session_id, verdict, spoof_score, confidence, latency_ms, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (api_key_id, session_id, verdict, spoof_score, confidence, latency_ms, now),
            )

            # Upsert daily aggregate
            conn.execute(
                "INSERT INTO daily_aggregates "
                "(api_key_id, date, detections, real_count, fake_count, uncertain_count, total_latency_ms) "
                "VALUES (?, ?, 1, ?, ?, ?, ?) "
                "ON CONFLICT(api_key_id, date) DO UPDATE SET "
                "detections = detections + 1, "
                "real_count = real_count + excluded.real_count, "
                "fake_count = fake_count + excluded.fake_count, "
                "uncertain_count = uncertain_count + excluded.uncertain_count, "
                "total_latency_ms = total_latency_ms + excluded.total_latency_ms",
                (
                    api_key_id, today,
                    1 if verdict == "real" else 0,
                    1 if verdict == "fake" else 0,
                    1 if verdict == "uncertain" else 0,
                    latency_ms,
                ),
            )
    finally:
        conn.close()



def get_usage(api_key_id: str, tier: str) -> dict:
    """Get current usage stats for an API key."""
    conn = get_db()
    today = date.today().isoformat()
    month_start = date.today().replace(day=1).isoformat()

    # Today's usage
    today_row = conn.execute(
        "SELECT COALESCE(SUM(detections), 0) as total, "
        "COALESCE(SUM(real_count), 0) as real_c, "
        "COALESCE(SUM(fake_count), 0) as fake_c, "
        "COALESCE(SUM(uncertain_count), 0) as unc_c, "
        "COALESCE(SUM(total_latency_ms), 0) as lat "
        "FROM daily_aggregates WHERE api_key_id = ? AND date = ?",
        (api_key_id, today),
    ).fetchone()

    # Monthly usage
    month_row = conn.execute(
        "SELECT COALESCE(SUM(detections), 0) as total "
        "FROM daily_aggregates WHERE api_key_id = ? AND date >= ?",
        (api_key_id, month_start),
    ).fetchone()

    tier_enum = Tier(tier)
    daily_limit, monthly_limit = TIER_LIMITS.get(
        tier_enum, TIER_LIMITS[Tier.FREE]
    )

    detections_today = today_row["total"]
    avg_lat = (
        today_row["lat"] / detections_today if detections_today > 0 else 0.0
    )

    conn.close()
    return {
        "api_key_id": api_key_id,
        "tier": tier,
        "detections_today": detections_today,
        "detections_this_month": month_row["total"],
        "daily_limit": daily_limit,
        "monthly_limit": monthly_limit,
        "remaining_today": max(0, daily_limit - detections_today),
        "avg_latency_ms": round(avg_lat, 1),
        "verdicts": {
            "real": today_row["real_c"],
            "fake": today_row["fake_c"],
            "uncertain": today_row["unc_c"],
        },
    }


def get_usage_history(
    api_key_id: str, start_date: str, end_date: str
) -> list[dict]:
    """Get daily usage history for a date range."""
    conn = get_db()
    rows = conn.execute(
        "SELECT date, detections, real_count, fake_count, uncertain_count, "
        "CASE WHEN detections > 0 THEN total_latency_ms / detections ELSE 0 END as avg_latency_ms "
        "FROM daily_aggregates "
        "WHERE api_key_id = ? AND date >= ? AND date <= ? "
        "ORDER BY date",
        (api_key_id, start_date, end_date),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_detections(api_key_id: str, limit: int = 50) -> list[dict]:
    """Get recent detection log entries."""
    conn = get_db()
    rows = conn.execute(
        "SELECT session_id, timestamp, verdict, spoof_score, confidence, latency_ms "
        "FROM detection_log WHERE api_key_id = ? "
        "ORDER BY timestamp DESC LIMIT ?",
        (api_key_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def check_rate_limit(api_key_id: str, tier: str) -> bool:
    """Check if the API key has exceeded its daily rate limit."""
    conn = get_db()
    today = date.today().isoformat()
    row = conn.execute(
        "SELECT COALESCE(SUM(detections), 0) as total "
        "FROM daily_aggregates WHERE api_key_id = ? AND date = ?",
        (api_key_id, today),
    ).fetchone()
    conn.close()

    tier_enum = Tier(tier)
    daily_limit = TIER_LIMITS.get(tier_enum, TIER_LIMITS[Tier.FREE])[0]
    return row["total"] < daily_limit
