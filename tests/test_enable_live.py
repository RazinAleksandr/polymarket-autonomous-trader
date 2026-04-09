"""Tests for enhanced enable_live.py and get_calibration_health()."""

import json
import os
import subprocess
import sys
import tempfile

import pytest

from lib.calibration import (
    get_calibration_health,
    record_calibration_outcome,
)
from lib.db import DataStore


# --- get_calibration_health() tests ---


def test_calibration_health_empty_db(store):
    """get_calibration_health returns healthy=True with no data."""
    result = get_calibration_health(store)
    assert result["healthy"] is True
    assert result["worst_category"] is None
    assert result["worst_bias"] is None
    for cat_data in result["categories"].values():
        assert cat_data["trades"] == 0
        assert cat_data["assessment"] in ("NO DATA", "INSUFFICIENT DATA")


def test_calibration_health_healthy_category(store):
    """Categories with moderate bias are reported as healthy."""
    # Record well-calibrated outcomes: mix of wins at high prob and losses at low prob
    # WIN with stated_prob=0.90 -> error_pp = (0.90 - 1.0) * 100 = -10 (within bounds)
    for i in range(3):
        record_calibration_outcome(store, f"w-{i}", "crypto", 0.90, "WIN")
    # LOSS with stated_prob=0.10 -> error_pp = (0.10 - 0.0) * 100 = +10 (within bounds)
    for i in range(3):
        record_calibration_outcome(store, f"l-{i}", "crypto", 0.10, "LOSS")

    result = get_calibration_health(store)
    assert result["healthy"] is True
    assert result["categories"]["crypto"]["healthy"] is True
    assert result["categories"]["crypto"]["trades"] == 6


def test_calibration_health_unhealthy_category(store):
    """Category with severe overconfidence (error_pp < -20) is unhealthy."""
    # Record outcomes where stated_prob was very high but all lost
    # stated_prob=0.85, outcome=LOSS -> error_pp = (0.85 - 0) * 100 = 85
    # Wait - that's underconfident. We need overconfident:
    # stated_prob=0.85, outcome=LOSS -> error_pp = (0.85 - 0) * 100 = +85? No.
    # error_pp = (stated_prob - actual) * 100
    # For LOSS: actual=0, so error_pp = stated_prob * 100 (positive = underconfident)
    # For overconfident: we need negative error_pp
    # stated_prob=0.15, outcome=WIN -> error_pp = (0.15 - 1) * 100 = -85

    for i in range(6):
        record_calibration_outcome(store, f"mkt-{i}", "politics", 0.15, "WIN")

    result = get_calibration_health(store)
    assert result["healthy"] is False
    assert result["categories"]["politics"]["healthy"] is False
    assert result["worst_category"] == "politics"
    assert result["worst_bias"] < -20


def test_calibration_health_mixed_categories(store):
    """One unhealthy category makes overall unhealthy even if others are fine."""
    # Healthy crypto: stated_prob=0.90, WIN -> error_pp = -10 (within bounds)
    for i in range(5):
        record_calibration_outcome(store, f"c-{i}", "crypto", 0.90, "WIN")

    # Unhealthy politics (overconfident): stated_prob=0.10, WIN -> error_pp = -90
    for i in range(5):
        record_calibration_outcome(store, f"p-{i}", "politics", 0.10, "WIN")

    result = get_calibration_health(store)
    assert result["healthy"] is False
    assert result["categories"]["crypto"]["healthy"] is True
    assert result["categories"]["politics"]["healthy"] is False


def test_calibration_health_structure(store):
    """get_calibration_health returns expected structure with all 6 categories."""
    result = get_calibration_health(store)
    assert "healthy" in result
    assert "categories" in result
    assert "worst_category" in result
    assert "worst_bias" in result

    expected_cats = ["crypto", "politics", "sports", "commodities",
                     "entertainment", "finance"]
    for cat in expected_cats:
        assert cat in result["categories"]
        cat_data = result["categories"][cat]
        assert "trades" in cat_data
        assert "error_pp" in cat_data
        assert "healthy" in cat_data


# --- enable_live.py --check tests ---


@pytest.fixture
def enable_live_env(tmp_path):
    """Set up environment for running enable_live.py --check."""
    # Create minimal project structure
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "state" / "reports").mkdir(parents=True)
    (project_dir / "tools").mkdir()
    (project_dir / "lib").mkdir()

    # Create .env with test db path
    db_path = str(project_dir / "test.db")
    env_file = project_dir / ".env"
    env_file.write_text(f"DB_PATH={db_path}\nMIN_PAPER_CYCLES=10\n")

    return project_dir, db_path


def _run_check(project_dir):
    """Run enable_live.py --check and return (returncode, stdout_json, stderr)."""
    # We need to test via the actual module's run_check function
    # rather than subprocess since the worktree paths complicate things
    pass


def test_check_outputs_json_with_all_criteria(store, tmp_path):
    """run_check returns dict with all 4 criteria."""
    from lib.config import Config
    from tools.enable_live import run_gate_check

    reports_dir = str(tmp_path / "reports")
    os.makedirs(reports_dir, exist_ok=True)

    config = Config(min_paper_cycles=10, db_path=":memory:")
    result = run_gate_check(store, config, reports_dir)

    assert "passed" in result
    assert "criteria" in result
    assert "summary" in result
    assert "cycles" in result["criteria"]
    assert "pnl" in result["criteria"]
    assert "win_rate" in result["criteria"]
    assert "calibration" in result["criteria"]


def test_check_fails_insufficient_cycles(store, tmp_path):
    """--check fails when cycle count below threshold."""
    from lib.config import Config
    from tools.enable_live import run_gate_check

    reports_dir = str(tmp_path / "reports")
    os.makedirs(reports_dir, exist_ok=True)
    # Only create 3 cycle reports
    for i in range(3):
        (tmp_path / "reports" / f"cycle-2026-{i:02d}.md").write_text("test")

    config = Config(min_paper_cycles=10, db_path=":memory:")
    result = run_gate_check(store, config, reports_dir)

    assert result["passed"] is False
    assert result["criteria"]["cycles"]["passed"] is False


def test_check_fails_low_win_rate(store, tmp_path):
    """--check fails when win rate below 50%."""
    from lib.config import Config
    from tools.enable_live import run_gate_check

    reports_dir = str(tmp_path / "reports")
    os.makedirs(reports_dir, exist_ok=True)
    for i in range(12):
        (tmp_path / "reports" / f"cycle-2026-{i:02d}.md").write_text("test")

    # Create closed positions with bad win rate (1 win, 4 losses)
    for i in range(4):
        store.upsert_position(f"loss-{i}", f"Losing market {i}", "YES", 0.50, 10.0)
        store.close_position(f"loss-{i}", 0.20)  # loss
    store.upsert_position("win-0", "Winning market", "YES", 0.40, 10.0)
    store.close_position("win-0", 0.80)  # win

    config = Config(min_paper_cycles=10, db_path=":memory:")
    result = run_gate_check(store, config, reports_dir)

    assert result["criteria"]["win_rate"]["passed"] is False
    assert result["criteria"]["win_rate"]["actual"] < 50.0


def test_check_fails_unhealthy_calibration(store, tmp_path):
    """--check fails when calibration is unhealthy."""
    from lib.config import Config
    from tools.enable_live import run_gate_check

    reports_dir = str(tmp_path / "reports")
    os.makedirs(reports_dir, exist_ok=True)
    for i in range(12):
        (tmp_path / "reports" / f"cycle-2026-{i:02d}.md").write_text("test")

    # Create winning positions for good win rate and positive P&L
    for i in range(8):
        store.upsert_position(f"win-{i}", f"Good market {i}", "YES", 0.40, 10.0)
        store.close_position(f"win-{i}", 0.80)

    # Create severely overconfident calibration data
    for i in range(6):
        record_calibration_outcome(store, f"cal-{i}", "crypto", 0.10, "WIN")

    config = Config(min_paper_cycles=10, db_path=":memory:")
    result = run_gate_check(store, config, reports_dir)

    assert result["criteria"]["calibration"]["passed"] is False


def test_check_passes_all_criteria(store, tmp_path):
    """--check passes when all 4 criteria are met."""
    from lib.config import Config
    from tools.enable_live import run_gate_check

    reports_dir = str(tmp_path / "reports")
    os.makedirs(reports_dir, exist_ok=True)
    for i in range(12):
        (tmp_path / "reports" / f"cycle-2026-{i:02d}.md").write_text("test")

    # Create winning positions (good P&L and win rate)
    for i in range(8):
        store.upsert_position(f"win-{i}", f"Good market {i}", "YES", 0.40, 10.0)
        store.close_position(f"win-{i}", 0.80)

    # Create well-calibrated outcomes: stated_prob=0.90, WIN -> error_pp = -10
    for i in range(6):
        record_calibration_outcome(store, f"cal-{i}", "crypto", 0.90, "WIN")

    config = Config(min_paper_cycles=10, db_path=":memory:")
    result = run_gate_check(store, config, reports_dir)

    assert result["passed"] is True
    assert result["criteria"]["cycles"]["passed"] is True
    assert result["criteria"]["pnl"]["passed"] is True
    assert result["criteria"]["win_rate"]["passed"] is True
    assert result["criteria"]["calibration"]["passed"] is True


def test_check_is_read_only(store, tmp_path):
    """--check never creates a gate pass file."""
    from lib.config import Config
    from tools.enable_live import run_gate_check

    reports_dir = str(tmp_path / "reports")
    os.makedirs(reports_dir, exist_ok=True)
    for i in range(12):
        (tmp_path / "reports" / f"cycle-2026-{i:02d}.md").write_text("test")

    for i in range(8):
        store.upsert_position(f"win-{i}", f"Good market {i}", "YES", 0.40, 10.0)
        store.close_position(f"win-{i}", 0.80)

    config = Config(min_paper_cycles=10, db_path=":memory:")
    result = run_gate_check(store, config, reports_dir)

    # Even with all criteria passing, no gate pass file should exist
    gate_path = tmp_path / ".live-gate-pass"
    assert not gate_path.exists()
    # run_check itself never writes the file -- it's purely read-only
    assert result["passed"] is True
