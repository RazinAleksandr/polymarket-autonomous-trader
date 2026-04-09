"""Tests for calibration health check and live gate upgrade.

Tests get_calibration_health() and enable_live.py --check with all 4 criteria.
"""

import json
import os
import sys
import tempfile

import pytest

from lib.db import DataStore
from lib.calibration import (
    get_calibration_health,
    record_calibration_outcome,
)

# Make tools/ importable
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
)


# --- get_calibration_health tests ---


class TestCalibrationHealth:
    """Test get_calibration_health() with various DB states."""

    def test_empty_db_is_healthy(self, store):
        """Empty DB returns healthy (no data to be unhealthy about)."""
        health = get_calibration_health(store)
        assert health["healthy"] is True
        assert health["worst_bias"] is None
        assert health["worst_category"] is None

    def test_insufficient_trades_is_healthy(self, store):
        """< 5 trades per category returns healthy (insufficient data)."""
        for i in range(4):
            record_calibration_outcome(store, f"m{i}", "crypto", 0.30, "WIN")
        health = get_calibration_health(store)
        assert health["healthy"] is True
        assert health["categories"]["crypto"]["assessment"] == "INSUFFICIENT DATA"

    def test_well_calibrated_is_healthy(self, store):
        """Category with small error_pp returns healthy."""
        # 5 trades with error_pp near 0 (stated ~0.5, mixed wins/losses)
        record_calibration_outcome(store, "m1", "crypto", 0.55, "WIN")
        record_calibration_outcome(store, "m2", "crypto", 0.45, "LOSS")
        record_calibration_outcome(store, "m3", "crypto", 0.50, "WIN")
        record_calibration_outcome(store, "m4", "crypto", 0.50, "LOSS")
        record_calibration_outcome(store, "m5", "crypto", 0.52, "WIN")

        health = get_calibration_health(store)
        assert health["healthy"] is True
        assert health["categories"]["crypto"]["healthy"] is True
        assert "WELL CALIBRATED" in health["categories"]["crypto"]["assessment"]

    def test_overconfident_is_unhealthy(self, store):
        """Category with error_pp <= -20 returns unhealthy."""
        # 6 trades with low stated_prob that all win -> very negative error_pp
        # error_pp per trade = (0.20 - 1.0) * 100 = -80
        for i in range(6):
            record_calibration_outcome(store, f"m{i}", "crypto", 0.20, "WIN")

        health = get_calibration_health(store)
        assert health["healthy"] is False
        assert health["categories"]["crypto"]["healthy"] is False
        assert health["worst_category"] == "crypto"
        assert health["worst_bias"] < -20

    def test_multiple_categories_one_unhealthy(self, store):
        """One unhealthy category makes overall unhealthy."""
        # Crypto: well calibrated
        for i in range(5):
            record_calibration_outcome(store, f"c{i}", "crypto", 0.50, "WIN" if i % 2 == 0 else "LOSS")

        # Politics: severely overconfident
        for i in range(6):
            record_calibration_outcome(store, f"p{i}", "politics", 0.20, "WIN")

        health = get_calibration_health(store)
        assert health["healthy"] is False
        assert health["categories"]["crypto"]["healthy"] is True
        assert health["categories"]["politics"]["healthy"] is False
        assert health["worst_category"] == "politics"

    def test_health_returns_all_categories(self, store):
        """Health report includes all 6 standard categories."""
        health = get_calibration_health(store)
        expected_cats = ["crypto", "politics", "sports", "commodities", "entertainment", "finance"]
        for cat in expected_cats:
            assert cat in health["categories"]

    def test_borderline_healthy_at_minus_19(self, store):
        """error_pp of -19 is still healthy (threshold is -20)."""
        # Need avg error_pp around -19
        # 5 trades: stated=0.31, outcome=WIN -> error_pp = (0.31-1)*100 = -69
        # That's way too negative. Let's be more precise.
        # We want avg error_pp = -19, so (stated - actual)*100 = -19 per trade
        # If outcome=WIN (actual=1): stated = 1 - 19/100 = 0.81
        for i in range(5):
            record_calibration_outcome(store, f"m{i}", "crypto", 0.81, "WIN")

        health = get_calibration_health(store)
        # error_pp = (0.81 - 1.0) * 100 = -19.0
        assert health["categories"]["crypto"]["healthy"] is True
        assert health["healthy"] is True

    def test_borderline_unhealthy_beyond_minus_20(self, store):
        """error_pp worse than -20 is unhealthy."""
        # error_pp = (0.79 - 1.0) * 100 = -21.0
        for i in range(5):
            record_calibration_outcome(store, f"m{i}", "crypto", 0.79, "WIN")

        health = get_calibration_health(store)
        assert health["categories"]["crypto"]["healthy"] is False
        assert health["healthy"] is False


# --- enable_live.py --check integration tests ---


class TestEnableLiveCheck:
    """Test enable_live.py --check with various gate states."""

    @pytest.fixture
    def setup_env(self, tmp_path, store):
        """Set up environment for enable_live.py tests."""
        # Create reports directory
        reports_dir = tmp_path / "state" / "reports"
        reports_dir.mkdir(parents=True)

        return {
            "store": store,
            "reports_dir": str(reports_dir),
            "tmp_path": tmp_path,
        }

    def test_run_gate_check_all_fail(self, store, tmp_path):
        """All criteria fail with empty DB and no reports."""
        from enable_live import run_gate_check
        from lib.config import Config

        reports_dir = str(tmp_path / "reports")
        os.makedirs(reports_dir, exist_ok=True)
        config = Config(min_paper_cycles=10)

        result = run_gate_check(store, config, reports_dir)
        assert result["passed"] is False
        assert result["criteria"]["cycles"]["passed"] is False
        assert result["criteria"]["pnl"]["passed"] is False
        assert result["criteria"]["win_rate"]["passed"] is False
        # Calibration passes with empty DB (no data = healthy)
        assert result["criteria"]["calibration"]["passed"] is True

    def test_run_gate_check_all_pass(self, store, tmp_path):
        """All criteria pass with sufficient data."""
        from enable_live import run_gate_check
        from lib.config import Config

        # Create 10 cycle reports
        reports_dir = str(tmp_path / "reports")
        os.makedirs(reports_dir, exist_ok=True)
        for i in range(10):
            with open(os.path.join(reports_dir, f"cycle-2026-{i:02d}.md"), "w") as f:
                f.write(f"# Cycle {i}\n")

        # Create closed positions with positive P&L and >50% win rate
        # 6 wins, 3 losses
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        for i in range(9):
            store.conn.execute(
                """INSERT INTO positions
                   (market_id, question, side, avg_price, size, cost_basis,
                    opened_at, status, closed_at, realized_pnl)
                   VALUES (?, ?, 'YES', 0.50, 10, 5.0, ?, 'closed', ?, ?)""",
                (f"mkt{i}", f"Question {i}", now, now,
                 10.0 if i < 6 else -5.0)
            )
        store.conn.commit()

        config = Config(min_paper_cycles=10)
        result = run_gate_check(store, config, reports_dir)

        assert result["passed"] is True
        assert result["criteria"]["cycles"]["passed"] is True
        assert result["criteria"]["pnl"]["passed"] is True
        assert result["criteria"]["win_rate"]["passed"] is True
        assert result["criteria"]["calibration"]["passed"] is True

    def test_run_gate_check_calibration_blocks(self, store, tmp_path):
        """Unhealthy calibration blocks even when other criteria pass."""
        from enable_live import run_gate_check
        from lib.config import Config

        # Create cycle reports
        reports_dir = str(tmp_path / "reports")
        os.makedirs(reports_dir, exist_ok=True)
        for i in range(10):
            with open(os.path.join(reports_dir, f"cycle-2026-{i:02d}.md"), "w") as f:
                f.write(f"# Cycle {i}\n")

        # Create winning positions
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        for i in range(6):
            store.conn.execute(
                """INSERT INTO positions
                   (market_id, question, side, avg_price, size, cost_basis,
                    opened_at, status, closed_at, realized_pnl)
                   VALUES (?, ?, 'YES', 0.50, 10, 5.0, ?, 'closed', ?, 10.0)""",
                (f"mkt{i}", f"Question {i}", now, now)
            )
        store.conn.commit()

        # Make crypto calibration severely overconfident
        for i in range(6):
            record_calibration_outcome(store, f"cal{i}", "crypto", 0.20, "WIN")

        config = Config(min_paper_cycles=10)
        result = run_gate_check(store, config, reports_dir)

        assert result["passed"] is False
        assert result["criteria"]["calibration"]["passed"] is False
        # Other criteria still pass
        assert result["criteria"]["cycles"]["passed"] is True
        assert result["criteria"]["pnl"]["passed"] is True
        assert result["criteria"]["win_rate"]["passed"] is True

    def test_run_gate_check_win_rate_blocks(self, store, tmp_path):
        """Win rate <= 50% blocks."""
        from enable_live import run_gate_check
        from lib.config import Config

        reports_dir = str(tmp_path / "reports")
        os.makedirs(reports_dir, exist_ok=True)
        for i in range(10):
            with open(os.path.join(reports_dir, f"cycle-2026-{i:02d}.md"), "w") as f:
                f.write(f"# Cycle {i}\n")

        # 5 wins, 5 losses (50% = not > 50%)
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        for i in range(10):
            store.conn.execute(
                """INSERT INTO positions
                   (market_id, question, side, avg_price, size, cost_basis,
                    opened_at, status, closed_at, realized_pnl)
                   VALUES (?, ?, 'YES', 0.50, 10, 5.0, ?, 'closed', ?, ?)""",
                (f"mkt{i}", f"Question {i}", now, now,
                 10.0 if i < 5 else -5.0)
            )
        store.conn.commit()

        config = Config(min_paper_cycles=10)
        result = run_gate_check(store, config, reports_dir)

        assert result["criteria"]["win_rate"]["passed"] is False

    def test_compute_win_rate_empty(self, store):
        """Win rate with no closed positions returns 0."""
        from enable_live import compute_win_rate
        wr = compute_win_rate(store)
        assert wr["win_rate"] == 0.0
        assert wr["total"] == 0

    def test_compute_win_rate_mixed(self, store):
        """Win rate computed correctly from closed positions."""
        from enable_live import compute_win_rate
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        # 3 wins, 2 losses
        for i in range(5):
            store.conn.execute(
                """INSERT INTO positions
                   (market_id, question, side, avg_price, size, cost_basis,
                    opened_at, status, closed_at, realized_pnl)
                   VALUES (?, ?, 'YES', 0.50, 10, 5.0, ?, 'closed', ?, ?)""",
                (f"mkt{i}", f"Q{i}", now, now,
                 10.0 if i < 3 else -5.0)
            )
        store.conn.commit()

        wr = compute_win_rate(store)
        assert wr["win_rate"] == 0.6
        assert wr["wins"] == 3
        assert wr["total"] == 5
