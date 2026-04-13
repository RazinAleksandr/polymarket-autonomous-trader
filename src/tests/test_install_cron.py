"""Tests for scripts/install_cron.sh -- crontab entry building and management."""

import subprocess
import os

import pytest

SCRIPT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts"
)
INSTALL_SCRIPT = os.path.join(SCRIPT_DIR, "install_cron.sh")


class TestInstallCronScript:
    """Test install_cron.sh exists and is executable."""

    def test_script_exists(self):
        assert os.path.exists(INSTALL_SCRIPT)

    def test_script_is_executable(self):
        assert os.access(INSTALL_SCRIPT, os.X_OK)

    def test_script_has_shebang(self):
        with open(INSTALL_SCRIPT) as f:
            first_line = f.readline()
        assert first_line.startswith("#!/")

    def test_script_contains_marker(self):
        """Script uses polymarket-trader marker comment."""
        with open(INSTALL_SCRIPT) as f:
            content = f.read()
        assert "# polymarket-trader" in content

    def test_script_contains_three_schedules(self):
        """Script defines 3 cron schedules."""
        with open(INSTALL_SCRIPT) as f:
            content = f.read()
        assert "*/10" in content  # heartbeat
        assert "*/30" in content  # gated cycle
        assert "0 2 * * *" in content  # daily forced scan

    def test_script_has_remove_flag(self):
        """Script supports --remove flag."""
        with open(INSTALL_SCRIPT) as f:
            content = f.read()
        assert "--remove" in content

    def test_script_has_show_flag(self):
        """Script supports --show flag."""
        with open(INSTALL_SCRIPT) as f:
            content = f.read()
        assert "--show" in content

    def test_script_removes_old_agent_entries(self):
        """Script references old polymarket-agent for cleanup."""
        with open(INSTALL_SCRIPT) as f:
            content = f.read()
        assert "polymarket-agent" in content

    def test_script_references_heartbeat(self):
        """Script references heartbeat.py."""
        with open(INSTALL_SCRIPT) as f:
            content = f.read()
        assert "heartbeat.py" in content

    def test_script_references_run_cycle(self):
        """Script references run_cycle.sh."""
        with open(INSTALL_SCRIPT) as f:
            content = f.read()
        assert "run_cycle.sh" in content

    def test_script_uses_force_for_daily(self):
        """Daily 2 AM scan uses --force flag."""
        with open(INSTALL_SCRIPT) as f:
            content = f.read()
        assert "--force" in content


class TestStatusScript:
    """Test scripts/status.sh exists and is correct."""

    STATUS_SCRIPT = os.path.join(SCRIPT_DIR, "status.sh")

    def test_script_exists(self):
        assert os.path.exists(self.STATUS_SCRIPT)

    def test_script_is_executable(self):
        assert os.access(self.STATUS_SCRIPT, os.X_OK)

    def test_script_has_json_mode(self):
        """status.sh supports --json flag."""
        with open(self.STATUS_SCRIPT) as f:
            content = f.read()
        assert "--json" in content

    def test_script_reads_signal_file(self):
        """status.sh reads signal.json."""
        with open(self.STATUS_SCRIPT) as f:
            content = f.read()
        assert "signal.json" in content

    def test_script_reads_log_file(self):
        """status.sh reads run_cycle.log."""
        with open(self.STATUS_SCRIPT) as f:
            content = f.read()
        assert "run_cycle.log" in content

    def test_script_counts_cycles(self):
        """status.sh counts cycle reports."""
        with open(self.STATUS_SCRIPT) as f:
            content = f.read()
        assert "cycle_count" in content or "cycle-*.md" in content
