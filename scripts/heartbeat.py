#!/usr/bin/env python3
"""
Lightweight heartbeat -- runs every ~10 min via cron (NO API or LLM calls).

Reads local state (trading.db, state/reports/) and writes state/signal.json
with boolean flags that run_cycle.sh (Phase 4) reads to decide whether
to launch an expensive Claude trading session.

Flags (per D-08, adapted to 5-phase trading cycle):
  scan_needed:    True if no cycle report in last 4 hours (Phase B trigger)
  resolve_needed: True if any position's end_date within 24h or no resolve in 1h (Phase A trigger)
  learn_needed:   True if calibration_records newer than last learn report (Phase E trigger)
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Allow running from project root or scripts/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.db import DataStore
from lib.config import load_config

SIGNAL_FILE = PROJECT_ROOT / "state" / "signal.json"
REPORTS_DIR = PROJECT_ROOT / "state" / "reports"
SCAN_INTERVAL = timedelta(hours=4)
RESOLVE_INTERVAL = timedelta(hours=1)
EXPIRY_WINDOW = timedelta(hours=24)
EXPIRY_SOON_WINDOW = timedelta(hours=48)


def latest_report_time(prefix: str, reports_dir: Path = REPORTS_DIR) -> datetime | None:
    """Return mtime (UTC) of the most recent report matching prefix, or None."""
    files = list(reports_dir.glob(f"{prefix}*.md"))
    if not files:
        return None
    latest = max(files, key=lambda f: f.stat().st_mtime)
    return datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc)


def scan_needed(now: datetime, reports_dir: Path = REPORTS_DIR) -> bool:
    """True if no cycle report exists within SCAN_INTERVAL."""
    t = latest_report_time("cycle-", reports_dir)
    if t is None:
        return True
    return (now - t) > SCAN_INTERVAL


def resolve_needed(now: datetime, store: DataStore, reports_dir: Path = REPORTS_DIR) -> bool:
    """True if any open position's market expires within 24h, or no resolve report in 1h."""
    open_positions = store.get_open_positions()
    open_market_ids = [p["market_id"] for p in open_positions]

    if open_market_ids:
        placeholders = ",".join("?" * len(open_market_ids))
        rows = store.conn.execute(
            f"SELECT DISTINCT market_id, end_date FROM market_snapshots "
            f"WHERE market_id IN ({placeholders}) AND end_date != '' "
            f"ORDER BY timestamp DESC",
            open_market_ids
        ).fetchall()
        for row in rows:
            try:
                end_dt = datetime.fromisoformat(row["end_date"])
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone.utc)
                if end_dt - now < EXPIRY_WINDOW:
                    return True
            except (ValueError, TypeError):
                pass

    # Fallback: check last resolve report time
    t = latest_report_time("resolve-", reports_dir)
    if t is None:
        return True
    return (now - t) > RESOLVE_INTERVAL


def learn_needed(now: datetime, store: DataStore, reports_dir: Path = REPORTS_DIR) -> bool:
    """True if calibration_records have entries newer than last learn report."""
    t = latest_report_time("learn-", reports_dir)
    if t is None:
        # No learn report yet -- check if any calibration records exist
        row = store.conn.execute(
            "SELECT COUNT(*) as cnt FROM calibration_records"
        ).fetchone()
        return row["cnt"] > 0

    cutoff = t.isoformat()
    row = store.conn.execute(
        "SELECT COUNT(*) as cnt FROM calibration_records WHERE timestamp > ?",
        (cutoff,)
    ).fetchone()
    return row["cnt"] > 0


def expiring_soon(now: datetime, store: DataStore) -> list[str]:
    """Return questions for open positions with market end_date within 48 hours."""
    open_positions = store.get_open_positions()
    if not open_positions:
        return []

    open_market_ids = [p["market_id"] for p in open_positions]
    # Build question lookup
    question_by_market = {p["market_id"]: p["question"] for p in open_positions}

    placeholders = ",".join("?" * len(open_market_ids))
    rows = store.conn.execute(
        f"SELECT DISTINCT market_id, end_date FROM market_snapshots "
        f"WHERE market_id IN ({placeholders}) AND end_date != '' "
        f"ORDER BY timestamp DESC",
        open_market_ids
    ).fetchall()

    result = []
    seen = set()
    for row in rows:
        mid = row["market_id"]
        if mid in seen:
            continue
        try:
            end_dt = datetime.fromisoformat(row["end_date"])
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            if end_dt - now < EXPIRY_SOON_WINDOW:
                q = question_by_market.get(mid, mid)
                result.append(q)
                seen.add(mid)
        except (ValueError, TypeError):
            pass

    return result


def main(db_path: str = None, signal_path: Path = None, reports_dir: Path = None) -> dict:
    """Generate heartbeat signal and write to signal.json.

    Parameters allow test injection; defaults use module constants.
    """
    if db_path is None:
        config = load_config()
        db_path = config.db_path
    if signal_path is None:
        signal_path = SIGNAL_FILE
    if reports_dir is None:
        reports_dir = REPORTS_DIR

    now = datetime.now(timezone.utc)

    # Ensure reports dir exists
    reports_dir.mkdir(parents=True, exist_ok=True)

    store = DataStore(db_path)
    try:
        signal = {
            "generated_at": now.isoformat(),
            "scan_needed": scan_needed(now, reports_dir),
            "resolve_needed": resolve_needed(now, store, reports_dir),
            "learn_needed": learn_needed(now, store, reports_dir),
            "expiring_soon": expiring_soon(now, store),
            "open_positions": len(store.get_open_positions()),
        }
    finally:
        store.close()

    # Ensure signal file parent dir exists
    signal_path.parent.mkdir(parents=True, exist_ok=True)
    signal_path.write_text(json.dumps(signal, indent=2) + "\n")

    # Print summary to stdout
    flags = [k for k in ("scan_needed", "resolve_needed", "learn_needed") if signal[k]]
    print(f"[heartbeat] {now.isoformat()}")
    print(f"  open_positions: {signal['open_positions']}")
    print(f"  flags: {', '.join(flags) if flags else 'none'}")
    if signal["expiring_soon"]:
        print(f"  expiring_soon: {signal['expiring_soon']}")
    print(f"  wrote: {signal_path}")

    return signal


if __name__ == "__main__":
    main()
