"""Tests for scripts/heartbeat.py -- lightweight signal generator."""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

# Ensure polymarket-trader root is on sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.db import DataStore
from scripts.heartbeat import (
    latest_report_time,
    scan_needed,
    resolve_needed,
    learn_needed,
    expiring_soon,
    main,
)


@pytest.fixture
def store(tmp_path):
    """In-memory-like DataStore with a temp DB file."""
    db_path = str(tmp_path / "test.db")
    ds = DataStore(db_path=db_path)
    yield ds
    ds.close()


@pytest.fixture
def reports_dir(tmp_path):
    """Temporary reports directory."""
    d = tmp_path / "reports"
    d.mkdir()
    return d


def _create_report(reports_dir: Path, prefix: str, age_hours: float):
    """Create a fake report file with mtime set to `age_hours` ago."""
    fname = f"{prefix}{datetime.now(timezone.utc).strftime('%Y%m%d')}.md"
    fpath = reports_dir / fname
    fpath.write_text("# Report\n")
    target_time = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    os.utime(fpath, (target_time.timestamp(), target_time.timestamp()))
    return fpath


# --- latest_report_time ---

def test_latest_report_time_no_files(reports_dir):
    """Returns None when no matching report files exist."""
    result = latest_report_time("cycle-", reports_dir)
    assert result is None


def test_latest_report_time_returns_mtime(reports_dir):
    """Returns the mtime of the most recent matching file."""
    _create_report(reports_dir, "cycle-", age_hours=2.0)
    result = latest_report_time("cycle-", reports_dir)
    assert result is not None
    assert isinstance(result, datetime)
    # Should be roughly 2 hours ago
    age = datetime.now(timezone.utc) - result
    assert 1.9 < age.total_seconds() / 3600 < 2.5


# --- scan_needed ---

def test_scan_needed_empty_dir(reports_dir):
    """scan_needed True when state/reports/ has no cycle reports."""
    now = datetime.now(timezone.utc)
    assert scan_needed(now, reports_dir) is True


def test_scan_needed_old_report(reports_dir):
    """scan_needed True when most recent cycle report is > 4 hours old."""
    _create_report(reports_dir, "cycle-", age_hours=5.0)
    now = datetime.now(timezone.utc)
    assert scan_needed(now, reports_dir) is True


def test_scan_needed_recent_report(reports_dir):
    """scan_needed False when most recent cycle report is < 4 hours old."""
    _create_report(reports_dir, "cycle-", age_hours=1.0)
    now = datetime.now(timezone.utc)
    assert scan_needed(now, reports_dir) is False


# --- resolve_needed ---

def test_resolve_needed_expiring_position(store, reports_dir):
    """resolve_needed True when a market_snapshots end_date is within 24 hours."""
    now = datetime.now(timezone.utc)
    # Insert an open position
    store.upsert_position(
        market_id="mkt-1", question="Will BTC hit 100k?",
        side="YES", price=0.65, size=10.0
    )
    # Insert a market snapshot with end_date within 24h
    end_dt = (now + timedelta(hours=12)).isoformat()
    store.conn.execute(
        "INSERT INTO market_snapshots (timestamp, market_id, question, yes_price, no_price, volume_24h, liquidity, end_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (now.isoformat(), "mkt-1", "Will BTC hit 100k?", 0.65, 0.35, 5000.0, 2000.0, end_dt)
    )
    store.conn.commit()
    # Recent resolve report so fallback doesn't trigger
    _create_report(reports_dir, "resolve-", age_hours=0.5)
    assert resolve_needed(now, store, reports_dir) is True


def test_resolve_needed_first_run(store, reports_dir):
    """resolve_needed True when no resolve report exists (first run)."""
    now = datetime.now(timezone.utc)
    # No resolve report files, no positions -- but first run = True
    assert resolve_needed(now, store, reports_dir) is True


def test_resolve_needed_no_positions_recent_resolve(store, reports_dir):
    """resolve_needed False when no positions are open and resolve ran recently."""
    now = datetime.now(timezone.utc)
    _create_report(reports_dir, "resolve-", age_hours=0.3)
    assert resolve_needed(now, store, reports_dir) is False


# --- learn_needed ---

def test_learn_needed_new_calibration(store, reports_dir):
    """learn_needed True when calibration_records has entries newer than last learn report."""
    now = datetime.now(timezone.utc)
    _create_report(reports_dir, "learn-", age_hours=2.0)
    # Insert a calibration record with a timestamp newer than learn report
    recent = (now - timedelta(hours=0.5)).isoformat()
    store.conn.execute(
        "INSERT INTO calibration_records (timestamp, market_id, category, stated_prob, actual_outcome, brier_score, error_pp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (recent, "mkt-1", "politics", 0.7, 1, 0.09, -20.0)
    )
    store.conn.commit()
    assert learn_needed(now, store, reports_dir) is True


def test_learn_needed_empty_calibration(store, reports_dir):
    """learn_needed False when calibration_records is empty."""
    now = datetime.now(timezone.utc)
    assert learn_needed(now, store, reports_dir) is False


def test_learn_needed_learn_report_newer(store, reports_dir):
    """learn_needed False when last learn report is newer than all calibration_records."""
    now = datetime.now(timezone.utc)
    _create_report(reports_dir, "learn-", age_hours=1.0)
    # Insert calibration record older than learn report
    old = (now - timedelta(hours=3.0)).isoformat()
    store.conn.execute(
        "INSERT INTO calibration_records (timestamp, market_id, category, stated_prob, actual_outcome, brier_score, error_pp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (old, "mkt-2", "sports", 0.5, 0, 0.25, 50.0)
    )
    store.conn.commit()
    assert learn_needed(now, store, reports_dir) is False


# --- expiring_soon ---

def test_expiring_soon_lists_questions(store):
    """expiring_soon lists questions for positions with end_dates within 48 hours."""
    now = datetime.now(timezone.utc)
    store.upsert_position(
        market_id="mkt-exp", question="Will ETH merge?",
        side="YES", price=0.80, size=5.0
    )
    end_dt = (now + timedelta(hours=36)).isoformat()
    store.conn.execute(
        "INSERT INTO market_snapshots (timestamp, market_id, question, yes_price, no_price, volume_24h, liquidity, end_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (now.isoformat(), "mkt-exp", "Will ETH merge?", 0.80, 0.20, 3000.0, 1000.0, end_dt)
    )
    store.conn.commit()
    result = expiring_soon(now, store)
    assert "Will ETH merge?" in result


# --- main() ---

def test_main_writes_signal_json(store, tmp_path):
    """main() writes valid signal.json with all required fields."""
    signal_path = tmp_path / "signal.json"
    reports = tmp_path / "reports"
    # Don't create reports dir -- main should create it
    result = main(
        db_path=store.db_path,
        signal_path=signal_path,
        reports_dir=reports,
    )
    assert signal_path.exists()
    data = json.loads(signal_path.read_text())
    assert "generated_at" in data
    assert "scan_needed" in data
    assert "resolve_needed" in data
    assert "learn_needed" in data
    assert "expiring_soon" in data
    assert "open_positions" in data
    assert isinstance(data["scan_needed"], bool)
    assert isinstance(data["resolve_needed"], bool)
    assert isinstance(data["learn_needed"], bool)
    assert isinstance(data["expiring_soon"], list)
    assert isinstance(data["open_positions"], int)


def test_main_creates_missing_reports_dir(store, tmp_path):
    """main() handles missing state/reports/ directory gracefully (creates it)."""
    signal_path = tmp_path / "signal.json"
    reports = tmp_path / "nonexistent" / "reports"
    assert not reports.exists()
    main(
        db_path=store.db_path,
        signal_path=signal_path,
        reports_dir=reports,
    )
    # reports_dir should be created by main
    assert reports.exists()
