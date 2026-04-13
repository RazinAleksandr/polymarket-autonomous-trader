"""Tests for calibration tracking library."""

import json
import os

import pytest

from lib.db import DataStore
from lib.calibration import (
    compute_brier_score,
    interpret_error,
    record_calibration_outcome,
    get_calibration_summary,
    generate_corrections,
    regenerate_calibration_json,
)


# --- Brier score tests ---


def test_brier_score_win():
    """compute_brier_score(0.65, 'WIN') = (0.65 - 1.0)^2 = 0.1225."""
    assert abs(compute_brier_score(0.65, "WIN") - 0.1225) < 1e-9


def test_brier_score_loss():
    """compute_brier_score(0.65, 'LOSS') = (0.65 - 0.0)^2 = 0.4225."""
    assert abs(compute_brier_score(0.65, "LOSS") - 0.4225) < 1e-9


def test_brier_score_perfect_win():
    """compute_brier_score(1.0, 'WIN') = 0.0 (perfect prediction)."""
    assert compute_brier_score(1.0, "WIN") == 0.0


def test_brier_score_perfect_loss():
    """compute_brier_score(0.0, 'LOSS') = 0.0 (perfect prediction)."""
    assert compute_brier_score(0.0, "LOSS") == 0.0


def test_brier_score_max_uncertainty():
    """compute_brier_score(0.5, 'WIN') = 0.25 (maximum uncertainty)."""
    assert compute_brier_score(0.5, "WIN") == 0.25


# --- interpret_error tests ---


def test_interpret_error_insufficient_data():
    """n_trades < 5 returns INSUFFICIENT DATA."""
    result = interpret_error(0, 4)
    assert "INSUFFICIENT DATA" in result


def test_interpret_error_underconfident():
    """error_pp > 10 returns underconfident."""
    result = interpret_error(15, 10)
    assert "nderconfident" in result.lower() or "UNDERCONFIDENT" in result


def test_interpret_error_well_calibrated():
    """error_pp = 0 with enough trades returns WELL CALIBRATED."""
    result = interpret_error(0, 10)
    assert "WELL CALIBRATED" in result


def test_interpret_error_slightly_overconfident():
    """error_pp = -15 returns slightly overconfident with +6pp edge, -25% size."""
    result = interpret_error(-15, 10)
    assert "OVERCONFIDENT" in result
    assert "+6pp" in result
    assert "-25%" in result


def test_interpret_error_overconfident():
    """error_pp = -25 returns overconfident with +8pp edge, -50% size."""
    result = interpret_error(-25, 10)
    assert "OVERCONFIDENT" in result
    assert "+8pp" in result
    assert "-50%" in result


def test_interpret_error_severely_overconfident():
    """error_pp = -35 returns severely overconfident with +10pp edge, max 1% bankroll."""
    result = interpret_error(-35, 10)
    assert "SEVERELY OVERCONFIDENT" in result
    assert "+10pp" in result
    assert "1%" in result


# --- record_calibration_outcome tests ---


def test_record_calibration_outcome_inserts_row(store):
    """record_calibration_outcome inserts a row into calibration_records."""
    result = record_calibration_outcome(
        store, "mkt1", "crypto", 0.65, "WIN", pnl=10.0, notes="test"
    )
    assert "brier_score" in result
    assert abs(result["brier_score"] - 0.1225) < 1e-9
    assert result["category"] == "crypto"
    assert result["market_id"] == "mkt1"

    # Verify row exists in DB
    rows = store.conn.execute("SELECT * FROM calibration_records").fetchall()
    assert len(rows) == 1
    row = dict(rows[0])
    assert row["market_id"] == "mkt1"
    assert row["category"] == "crypto"
    assert abs(row["brier_score"] - 0.1225) < 1e-9
    assert row["actual_outcome"] == 1


def test_record_calibration_outcome_error_pp(store):
    """error_pp is computed as (stated_prob - actual) * 100."""
    result = record_calibration_outcome(store, "mkt2", "crypto", 0.65, "WIN")
    # error_pp = (0.65 - 1.0) * 100 = -35.0
    assert abs(result["error_pp"] - (-35.0)) < 1e-9


# --- get_calibration_summary tests ---


def test_get_calibration_summary_empty(store):
    """Empty DB returns zeroed summary dict."""
    summary = get_calibration_summary(store)
    assert summary["summary"]["total_trades"] == 0
    assert summary["summary"]["overall_brier"] is None
    assert summary["summary"]["overall_error_pp"] is None


def test_get_calibration_summary_single_category(store):
    """3 crypto WINs returns correct brier avg, error_pp, win_rate for crypto."""
    record_calibration_outcome(store, "m1", "crypto", 0.70, "WIN", pnl=5.0)
    record_calibration_outcome(store, "m2", "crypto", 0.80, "WIN", pnl=8.0)
    record_calibration_outcome(store, "m3", "crypto", 0.60, "WIN", pnl=3.0)

    summary = get_calibration_summary(store)
    assert summary["summary"]["total_trades"] == 3

    crypto = summary["categories"]["crypto"]
    assert crypto["trades"] == 3
    assert crypto["win_rate"] == 1.0

    # Brier scores: (0.70-1)^2=0.09, (0.80-1)^2=0.04, (0.60-1)^2=0.16
    expected_brier = (0.09 + 0.04 + 0.16) / 3
    assert abs(crypto["brier"] - expected_brier) < 1e-6


def test_get_calibration_summary_mixed_categories(store):
    """Mixed categories return correct per-category stats."""
    record_calibration_outcome(store, "m1", "crypto", 0.70, "WIN", pnl=5.0)
    record_calibration_outcome(store, "m2", "politics", 0.60, "LOSS", pnl=-3.0)
    record_calibration_outcome(store, "m3", "sports", 0.80, "WIN", pnl=10.0)

    summary = get_calibration_summary(store)
    assert summary["summary"]["total_trades"] == 3
    assert summary["categories"]["crypto"]["trades"] == 1
    assert summary["categories"]["politics"]["trades"] == 1
    assert summary["categories"]["sports"]["trades"] == 1
    assert summary["categories"]["politics"]["win_rate"] == 0.0
    assert summary["categories"]["sports"]["win_rate"] == 1.0


# --- generate_corrections tests ---


def test_generate_corrections_insufficient_trades(store):
    """Returns empty list when all categories have < 5 trades."""
    record_calibration_outcome(store, "m1", "crypto", 0.70, "WIN")
    record_calibration_outcome(store, "m2", "crypto", 0.80, "WIN")
    corrections = generate_corrections(store)
    assert corrections == []


def test_generate_corrections_with_bias(store):
    """Returns correction dict when crypto has 6 trades with significant error_pp."""
    # 6 WIN trades with low stated_prob -> negative error_pp -> overconfident
    # error_pp = (0.30 - 1.0) * 100 = -70 per trade
    for i in range(6):
        record_calibration_outcome(store, f"m{i}", "crypto", 0.30, "WIN")

    corrections = generate_corrections(store)
    assert len(corrections) >= 1
    crypto_corr = [c for c in corrections if c["category"] == "crypto"]
    assert len(crypto_corr) == 1
    assert crypto_corr[0]["direction"] == "subtract"  # overconfident (negative error_pp)
    assert crypto_corr[0]["data_points"] == 6
    assert "expires_after_n_trades" in crypto_corr[0]


# --- regenerate_calibration_json tests ---


def test_regenerate_calibration_json(store, tmp_path):
    """regenerate_calibration_json writes valid JSON matching schema."""
    record_calibration_outcome(store, "m1", "crypto", 0.70, "WIN", pnl=5.0)
    record_calibration_outcome(store, "m2", "politics", 0.60, "LOSS", pnl=-3.0)

    json_path = str(tmp_path / "calibration.json")
    regenerate_calibration_json(store, json_path=json_path)

    assert os.path.exists(json_path)
    with open(json_path) as f:
        data = json.load(f)

    assert data["schema_version"] == "1.0"
    assert data["summary"]["total_trades"] == 2
    assert "categories" in data
    assert "corrections" in data
    assert "last_updated" in data
    # All 6 categories present
    for cat in ["crypto", "politics", "sports", "commodities", "entertainment", "finance"]:
        assert cat in data["categories"]


# --- Table creation regression tests ---


def test_calibration_records_table_exists(store):
    """calibration_records table created alongside existing 5 tables."""
    rows = store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = sorted([
        r["name"] for r in rows
        if not r["name"].startswith("sqlite_")
    ])
    assert "calibration_records" in table_names


def test_existing_tables_still_exist(store):
    """All original 5 tables plus calibration_records exist (6 total)."""
    rows = store.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = sorted([
        r["name"] for r in rows
        if not r["name"].startswith("sqlite_")
    ])
    expected = sorted([
        "trades", "positions", "decisions", "market_snapshots",
        "strategy_metrics", "calibration_records",
    ])
    assert table_names == expected
