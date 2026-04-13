---
phase: 06-scheduling-paper-validation
plan: 02
subsystem: live-gate-and-status
tags: [safety, calibration, monitoring, live-gate]
dependency_graph:
  requires: [lib/calibration.py, lib/db.py, tools/enable_live.py]
  provides: [get_calibration_health, enable_live --check, status.sh]
  affects: [live trading gate, system monitoring]
tech_stack:
  added: []
  patterns: [4-criteria gate verification, read-only --check mode]
key_files:
  created:
    - polymarket-trader/scripts/status.sh
    - polymarket-trader/tests/test_enable_live.py
  modified:
    - polymarket-trader/lib/calibration.py
    - polymarket-trader/tools/enable_live.py
decisions:
  - "get_calibration_health() uses -20pp threshold for unhealthy category detection"
  - "enable_live.py --check is strictly read-only with JSON stdout and human stderr"
  - "Win rate computed from closed positions realized_pnl (positive = win)"
metrics:
  duration: 237s
  completed: "2026-04-05T18:26:44Z"
---

# Phase 6 Plan 2: Live Gate Enhancement & Status Monitoring Summary

Enhanced live trading gate with 4-criteria verification (cycles, P&L, win rate, calibration health) and created status.sh for quick system health checks.

## What Was Done

### Task 1: get_calibration_health() and enable_live.py enhancement
- Added `get_calibration_health(store)` to `lib/calibration.py` -- returns per-category bias data, overall health status, worst category identification
- A category is "unhealthy" when average error_pp < -20 (severely overconfident)
- Enhanced `tools/enable_live.py` with `--check` flag for read-only 4-criteria gate verification
- The 4 criteria: (1) cycles >= min_paper_cycles, (2) P&L > 0, (3) win rate > 50%, (4) no category bias > -20pp
- `--check` outputs structured JSON to stdout and human-readable summary to stderr
- Also updated the main enable flow to check all 4 criteria before allowing CONFIRM LIVE
- **Commit:** 017f46e

### Task 2: status.sh health check script
- Created `scripts/status.sh` showing: last heartbeat time, active signals, last cycle, total cycle count, errors in 24h, PID lock status
- Uses stat for file modification times, python3 for JSON parsing of signal.json
- Handles missing files gracefully
- **Commit:** 44e405d

### Task 3: Tests for enable_live.py and get_calibration_health()
- Created 11 tests covering:
  - get_calibration_health() with empty DB, healthy, unhealthy, and mixed categories
  - run_check() with all 4 criteria verification
  - Failure modes: insufficient cycles, low win rate, unhealthy calibration
  - Read-only verification (no gate pass file created by --check)
- All 289 tests passing (11 new, 0 regressions)
- **Commit:** c7f8e8a

## Deviations from Plan

### Auto-created Plan (Rule 3 - Blocking)
- Plan file 06-02-PLAN.md did not exist when executor started
- Created the plan inline based on phase 6 context (decisions D-05 through D-07, D-10) and REQUIREMENTS.md (SAFE-02, VAL-05)
- Execution proceeded normally after plan creation

## Decisions Made

1. **Calibration health threshold:** -20pp error_pp marks a category as "unhealthy" (per D-05 in context)
2. **Win rate source:** Computed from closed positions in the positions table (realized_pnl > 0 = win)
3. **--check output:** JSON to stdout, human summary to stderr (per D-07, matching existing CLI conventions)

## Known Stubs

None -- all functionality is fully wired.

## Self-Check: PASSED

All 4 files verified on disk. All 3 commit hashes found in git log.
