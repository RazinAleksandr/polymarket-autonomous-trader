#!/usr/bin/env python3
"""Live trading gate -- verify paper performance before enabling live mode.

Checks that:
1. At least MIN_PAPER_CYCLES paper trading cycles have been completed
2. Aggregate paper P&L is positive
3. Win rate > 50%
4. No category calibration bias worse than -20pp (overconfident)

Modes:
    --check   Read-only gate verification (JSON stdout, summary stderr). No gate pass.
    (default) Interactive: verify + prompt CONFIRM LIVE to write gate pass.
    --revoke  Remove gate pass (re-lock).
    --status  Check gate status only.

Usage:
    python tools/enable_live.py --check   # Read-only check (D-05, D-06, D-07)
    python tools/enable_live.py           # Verify and enable (interactive)
    python tools/enable_live.py --revoke  # Remove gate pass
    python tools/enable_live.py --status  # Check gate status only
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.calibration import get_calibration_health
from lib.config import load_config
from lib.db import DataStore

GATE_PASS_FILE = ".live-gate-pass"


def get_project_root() -> str:
    """Return the project root directory (parent of tools/)."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def compute_win_rate(store) -> dict:
    """Compute win rate from closed positions.

    Returns:
        dict with win_rate (float 0-1), wins (int), total (int).
    """
    closed = store.conn.execute(
        "SELECT realized_pnl FROM positions WHERE status = 'closed'"
    ).fetchall()

    if not closed:
        return {"win_rate": 0.0, "wins": 0, "total": 0}

    total = len(closed)
    wins = sum(1 for c in closed if c["realized_pnl"] > 0)
    return {
        "win_rate": wins / total if total > 0 else 0.0,
        "wins": wins,
        "total": total,
    }


def run_gate_check(store, config, reports_dir: str) -> dict:
    """Run all 4 gate criteria. Returns structured result.

    Criteria (D-05):
      1. cycles >= min_paper_cycles (default 10)
      2. P&L > 0
      3. win rate > 50%
      4. No category calibration bias > -20pp (D-06)

    Returns:
        dict with overall pass/fail, per-criterion results.
    """
    # Criterion 1 & 2: cycles and P&L
    stats = store.get_paper_cycle_stats(reports_dir=reports_dir)
    cycles = stats["cycle_count"]
    pnl = stats["total_pnl"]

    # Criterion 3: win rate
    wr = compute_win_rate(store)

    # Criterion 4: calibration health (D-06)
    cal_health = get_calibration_health(store)

    criteria = {
        "cycles": {
            "name": "Paper cycles completed",
            "required": f">= {config.min_paper_cycles}",
            "actual": cycles,
            "passed": cycles >= config.min_paper_cycles,
        },
        "pnl": {
            "name": "Aggregate P&L positive",
            "required": "> $0.00",
            "actual": round(pnl, 2),
            "passed": pnl > 0,
        },
        "win_rate": {
            "name": "Win rate above 50%",
            "required": "> 50%",
            "actual": round(wr["win_rate"] * 100, 1),
            "detail": f"{wr['wins']}/{wr['total']} trades",
            "passed": wr["win_rate"] > 0.5,
        },
        "calibration": {
            "name": "Calibration health",
            "required": "No category bias > -20pp",
            "actual": {
                "healthy": cal_health["healthy"],
                "worst_bias": cal_health["worst_bias"],
                "worst_category": cal_health["worst_category"],
            },
            "passed": cal_health["healthy"],
        },
    }

    all_passed = all(c["passed"] for c in criteria.values())

    return {
        "passed": all_passed,
        "criteria": criteria,
        "summary": {
            "cycles": cycles,
            "pnl": round(pnl, 2),
            "win_rate": round(wr["win_rate"] * 100, 1),
            "calibration_healthy": cal_health["healthy"],
        },
    }


def print_check_summary(result: dict) -> None:
    """Print human-readable gate check summary to stderr (D-07)."""
    print(f"\n{'='*55}", file=sys.stderr)
    print("  LIVE TRADING GATE CHECK", file=sys.stderr)
    print(f"{'='*55}", file=sys.stderr)

    for key, crit in result["criteria"].items():
        status = "PASS" if crit["passed"] else "FAIL"
        icon = "+" if crit["passed"] else "X"
        actual = crit["actual"]
        if key == "pnl":
            actual = f"${actual:.2f}"
        elif key == "win_rate":
            actual = f"{actual}% ({crit.get('detail', '')})"
        elif key == "calibration":
            if crit["actual"]["healthy"]:
                actual = "OK"
            else:
                actual = f"UNHEALTHY (worst: {crit['actual']['worst_category']} at {crit['actual']['worst_bias']:.1f}pp)"

        print(f"  [{icon}] {crit['name']}: {actual}  ({crit['required']})",
              file=sys.stderr)

    print(f"{'='*55}", file=sys.stderr)
    if result["passed"]:
        print("  RESULT: ALL CRITERIA PASSED", file=sys.stderr)
    else:
        failed = [c["name"] for c in result["criteria"].values() if not c["passed"]]
        print(f"  RESULT: BLOCKED ({len(failed)} criterion failed)", file=sys.stderr)
        for f in failed:
            print(f"    - {f}", file=sys.stderr)
    print(f"{'='*55}\n", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Verify paper performance and enable live trading"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Read-only gate check (JSON stdout, summary stderr)"
    )
    parser.add_argument(
        "--revoke", action="store_true",
        help="Remove gate pass (disable live trading)"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Check gate status without modifying anything"
    )
    args = parser.parse_args()

    project_root = get_project_root()
    gate_path = os.path.join(project_root, GATE_PASS_FILE)

    # Handle --revoke
    if args.revoke:
        if os.path.exists(gate_path):
            os.remove(gate_path)
            print("Gate pass removed. Live trading disabled.", file=sys.stderr)
        else:
            print("No gate pass found. Live trading already disabled.",
                  file=sys.stderr)
        return

    # Load config and connect to database
    config = load_config()
    reports_dir = os.path.join(project_root, "state", "reports")
    store = DataStore(db_path=config.db_path)

    try:
        # Handle --check (D-05, D-07: read-only, JSON + summary)
        if args.check:
            result = run_gate_check(store, config, reports_dir)
            print_check_summary(result)
            # JSON to stdout (D-07)
            json.dump(result, sys.stdout, indent=2)
            sys.stdout.write("\n")
            # Exit 1 if any criterion failed
            if not result["passed"]:
                sys.exit(1)
            return

        # Handle --status
        if args.status:
            stats = store.get_paper_cycle_stats(reports_dir=reports_dir)
            print(f"\n{'='*50}", file=sys.stderr)
            print("LIVE TRADING GATE STATUS", file=sys.stderr)
            print(f"{'='*50}", file=sys.stderr)
            print(f"Completed paper cycles: {stats['cycle_count']}", file=sys.stderr)
            print(f"Minimum required:       {config.min_paper_cycles}",
                  file=sys.stderr)
            print(f"Aggregate paper P&L:    ${stats['total_pnl']:.2f}",
                  file=sys.stderr)
            print(f"Gate pass file:         {GATE_PASS_FILE}", file=sys.stderr)
            print(f"Gate pass exists:       {os.path.exists(gate_path)}",
                  file=sys.stderr)
            print(f"{'='*50}\n", file=sys.stderr)
            if os.path.exists(gate_path):
                print("Status: LIVE TRADING ENABLED (gate pass exists)",
                      file=sys.stderr)
            else:
                print("Status: LIVE TRADING DISABLED (no gate pass)",
                      file=sys.stderr)
            return

        # Interactive mode (original behavior + new criteria)
        result = run_gate_check(store, config, reports_dir)
        print_check_summary(result)

        if not result["passed"]:
            failed = [c["name"] for c in result["criteria"].values()
                      if not c["passed"]]
            print(f"BLOCKED: {len(failed)} criterion failed. "
                  f"Fix before retrying.", file=sys.stderr)
            sys.exit(1)

        # All conditions met -- request confirmation
        print(
            "All conditions met. To enable live trading, type CONFIRM LIVE:",
            file=sys.stderr,
        )
        confirmation = input("> ").strip()

        if confirmation != "CONFIRM LIVE":
            print("Confirmation failed. Live trading NOT enabled.",
                  file=sys.stderr)
            sys.exit(1)

        # Write gate pass file
        gate_data = {
            "enabled_at": datetime.now(timezone.utc).isoformat(),
            "cycles_at_gate": result["summary"]["cycles"],
            "pnl_at_gate": result["summary"]["pnl"],
            "win_rate_at_gate": result["summary"]["win_rate"],
            "calibration_healthy": result["summary"]["calibration_healthy"],
            "min_paper_cycles": config.min_paper_cycles,
        }
        with open(gate_path, "w") as f:
            json.dump(gate_data, f, indent=2)
            f.write("\n")

        print(f"\nGate pass written to {GATE_PASS_FILE}", file=sys.stderr)
        print(
            "Live trading enabled. Delete the file to re-lock.",
            file=sys.stderr,
        )

        # Output gate data as JSON to stdout
        json.dump(gate_data, sys.stdout, indent=2)
        sys.stdout.write("\n")

    finally:
        store.close()


if __name__ == "__main__":
    main()
