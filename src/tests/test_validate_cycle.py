"""Tests for tools/validate_cycle.py -- cycle validation and summary generation."""

import json
import os
import re
import sqlite3
import subprocess
import sys
import textwrap

import pytest

# Ensure project root is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from tools.validate_cycle import (
    check_knowledge_refs,
    check_report_structure,
    check_strategy_drift,
    generate_summary,
    validate_cycle,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Dynamically count rules in the REAL golden-rules.md so tests don't hardcode
_GOLDEN_RULES_PATH = os.path.join(PROJECT_ROOT, "knowledge", "golden-rules.md")
with open(_GOLDEN_RULES_PATH) as _f:
    BASELINE_RULE_COUNT = len(re.findall(r"\*\*Rule \d+", _f.read()))


FULL_REPORT = textwrap.dedent("""\
    # Cycle Report: 20260404-140000

    **Date:** 2026-04-04
    **Cycle start:** 14:00:00 UTC
    **Status:** Completed

    ---

    ## Summary

    | Metric | Value |
    |---|---|
    | Markets scanned | 60 |
    | Markets analyzed | 5 |
    | Trades executed | 2 |
    | Strategy changes | 1 |

    Applied golden rules during analysis. Calibration scores improved.
    Reviewed crypto playbook for BTC target market.

    ---

    ## Market Discovery

    Found 60 markets via Gamma API.

    ---

    ## Trades Executed

    Bought YES on BTC $70k by Friday at 0.45, size $10.

    ---

    ## Position Monitor

    | Position | Side | Entry | Current |
    |---|---|---|---|
    | BTC $70k | YES | 0.45 | 0.52 |

    ---

    ## Resolutions

    No resolutions this cycle.

    ---

    ## Lessons Learned

    - Crypto markets move fast near expiry

    ---

    ## Strategy Changes

    - Added rule: check 4h chart before crypto entry

    ---

    ## Cycle Metrics

    | Metric | Value |
    |---|---|
    | Duration | 12m |
    | Strategy changes | 1 |
""")


REPORT_MISSING_RESOLUTIONS = textwrap.dedent("""\
    # Cycle Report: 20260404-140000

    ## Summary

    | Metric | Value |
    |---|---|
    | Trades executed | 1 |

    ## Market Discovery

    Found markets.

    ## Trades Executed

    One trade.

    ## Position Monitor

    No positions.

    ## Lessons Learned

    Nothing.

    ## Strategy Changes

    None.

    ## Cycle Metrics

    | Metric | Value |
    |---|---|
    | Strategy changes | 0 |
""")


ZERO_TRADE_REPORT = textwrap.dedent("""\
    # Cycle Report: 20260404-140000

    ## Summary

    | Metric | Value |
    |---|---|
    | Trades executed | 0 |
    | Strategy changes | 0 |

    No trades this cycle.

    ## Market Discovery

    Scanned 60 markets.

    ## Trades Executed

    No trades executed.

    ## Position Monitor

    Empty portfolio.

    ## Resolutions

    None.

    ## Lessons

    Nothing new.

    ## Strategy Suggestions

    Keep scanning.

    ## Cycle Metrics

    | Metric | Value |
    |---|---|
    | Strategy changes | 0 |
""")


@pytest.fixture
def project_dir(tmp_path):
    """Create a realistic project structure for testing."""
    # Reports
    reports_dir = tmp_path / "state" / "reports"
    reports_dir.mkdir(parents=True)

    # Golden rules with exact BASELINE_RULE_COUNT rules
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    rules_content = "# GOLDEN RULES\n\nRules: {}\n\n".format(BASELINE_RULE_COUNT)
    for i in range(1, BASELINE_RULE_COUNT + 1):
        rules_content += f"**Rule {i} -- Test rule {i}**\n- Some rule text\n\n"
    (knowledge_dir / "golden-rules.md").write_text(rules_content)

    # Market type playbooks (no Lessons Learned yet)
    mt_dir = knowledge_dir / "market-types"
    mt_dir.mkdir()
    (mt_dir / "crypto.md").write_text("# Crypto Playbook\n\nBasic crypto rules.\n")
    (mt_dir / "politics.md").write_text("# Politics Playbook\n\nBasic politics rules.\n")

    # Strategy baseline (15 lines)
    state_dir = tmp_path / "state"
    strategy_lines = [
        "# Strategy",
        "",
        "This document is updated by the trading agent after each cycle.",
        "It starts blank and evolves based on trading experience.",
        "Claude builds all rules here through autonomous trading.",
        "",
        "## Market Selection Rules",
        "",
        "## Analysis Approach",
        "",
        "## Risk Parameters",
        "",
        "## Trade Entry/Exit Rules",
        "",
        "## Cycle Health Tracking",
    ]
    (state_dir / "strategy.md").write_text("\n".join(strategy_lines))

    # SQLite DB with tables
    db_path = tmp_path / "trading.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            market_id TEXT NOT NULL,
            side TEXT NOT NULL,
            price REAL NOT NULL,
            size REAL NOT NULL,
            cost_usdc REAL NOT NULL,
            status TEXT DEFAULT 'filled'
        );
        CREATE TABLE IF NOT EXISTS calibration_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            market_id TEXT NOT NULL,
            category TEXT NOT NULL,
            stated_prob REAL NOT NULL,
            actual_outcome INTEGER NOT NULL,
            brier_score REAL NOT NULL,
            error_pp REAL NOT NULL,
            pnl REAL DEFAULT 0,
            notes TEXT DEFAULT ''
        );
    """)
    conn.commit()
    conn.close()

    return tmp_path


# ---------------------------------------------------------------------------
# Tests: Report Structure
# ---------------------------------------------------------------------------


def test_report_structure_valid():
    """A well-formed report with all 8 sections returns all-true structure checks."""
    result = check_report_structure(FULL_REPORT)
    for section, present in result.items():
        assert present, f"Section '{section}' should be present but was not"


def test_report_structure_missing_sections():
    """Report missing Resolutions fails that check."""
    result = check_report_structure(REPORT_MISSING_RESOLUTIONS)
    assert result["Resolutions"] is False


# ---------------------------------------------------------------------------
# Tests: Knowledge Base References
# ---------------------------------------------------------------------------


def test_knowledge_refs_with_trades():
    """Report mentioning golden rules, calibration, crypto passes all 3 checks."""
    refs = check_knowledge_refs(FULL_REPORT, has_trades=True)
    assert refs["golden_rules"] is True
    assert refs["calibration"] is True
    assert refs["playbook"] is True


def test_knowledge_refs_zero_trade():
    """Report with no trades passes even without playbook reference."""
    refs = check_knowledge_refs(ZERO_TRADE_REPORT, has_trades=False)
    # playbook not required for zero-trade cycles
    assert refs["playbook"] is True  # passes by default when no trades


# ---------------------------------------------------------------------------
# Tests: Strategy Drift
# ---------------------------------------------------------------------------


def test_strategy_drift_zero():
    """Report with Strategy changes | 0 returns count=0, drift=False."""
    report = "## Cycle Metrics\n\n| Metric | Value |\n|---|---|\n| Strategy changes | 0 |\n"
    count, drift = check_strategy_drift(report)
    assert count == 0
    assert drift is False


def test_strategy_drift_three():
    """Report with Strategy changes | 3 returns count=3, drift=False."""
    report = "## Cycle Metrics\n\n| Metric | Value |\n|---|---|\n| Strategy changes | 3 |\n"
    count, drift = check_strategy_drift(report)
    assert count == 3
    assert drift is False


def test_strategy_drift_four():
    """Report with Strategy changes | 4 returns count=4, drift=True."""
    report = "## Cycle Metrics\n\n| Metric | Value |\n|---|---|\n| Strategy changes | 4 |\n"
    count, drift = check_strategy_drift(report)
    assert count == 4
    assert drift is True


# ---------------------------------------------------------------------------
# Tests: Summary
# ---------------------------------------------------------------------------


def test_summary_counts_reports(project_dir):
    """Summary with 3 reports in directory returns total_cycles=3."""
    reports_dir = project_dir / "state" / "reports"
    for i in range(3):
        (reports_dir / f"cycle-2026040{i}-120000.md").write_text(ZERO_TRADE_REPORT)

    result = generate_summary(str(project_dir))
    assert result["total_cycles"] == 3


def test_summary_baseline_rules(project_dir):
    """Summary returns rules_added=0 when golden-rules has the current baseline count."""
    # project_dir fixture creates exactly BASELINE_RULE_COUNT rules
    result = generate_summary(str(project_dir))
    assert result["baseline_golden_rules"] == BASELINE_RULE_COUNT
    assert result["current_golden_rules"] == BASELINE_RULE_COUNT
    assert result["rules_added"] == 0


def test_summary_playbooks_modified(project_dir):
    """Summary detects Lessons Learned sections in playbook files."""
    # Add Lessons Learned to crypto playbook
    mt_dir = project_dir / "knowledge" / "market-types"
    (mt_dir / "crypto.md").write_text(
        "# Crypto Playbook\n\n## Lessons Learned\n\n- BTC volatile near expiry\n"
    )
    result = generate_summary(str(project_dir))
    assert result["playbooks_modified"] == 1


# ---------------------------------------------------------------------------
# Tests: CLI
# ---------------------------------------------------------------------------


def test_cli_per_cycle(project_dir):
    """Running validate_cycle.py --cycle-id X returns valid JSON."""
    # Write a report
    reports_dir = project_dir / "state" / "reports"
    (reports_dir / "cycle-20260404-140000.md").write_text(FULL_REPORT)

    result = subprocess.run(
        [
            sys.executable,
            os.path.join(PROJECT_ROOT, "tools", "validate_cycle.py"),
            "--cycle-id", "20260404-140000",
            "--project-root", str(project_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert "valid" in data
    assert data["cycle_id"] == "20260404-140000"


def test_cli_summary(project_dir):
    """Running validate_cycle.py --summary returns valid JSON with expected keys."""
    result = subprocess.run(
        [
            sys.executable,
            os.path.join(PROJECT_ROOT, "tools", "validate_cycle.py"),
            "--summary",
            "--project-root", str(project_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    data = json.loads(result.stdout)
    assert "total_cycles" in data
    assert "baseline_golden_rules" in data
    assert "current_golden_rules" in data
