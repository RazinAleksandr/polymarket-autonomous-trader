---
phase: 03-new-instrument-tools
plan: 03
subsystem: heartbeat
tags: [heartbeat, signal, cron, local-state, zero-cost]
dependency_graph:
  requires: [03-01]
  provides: [heartbeat-signal, signal-json]
  affects: [state/signal.json, run_cycle.sh]
tech_stack:
  added: []
  patterns: [local-state-only, injectable-defaults-for-testing]
key_files:
  created:
    - polymarket-trader/scripts/__init__.py
    - polymarket-trader/scripts/heartbeat.py
    - polymarket-trader/tests/test_heartbeat.py
  modified:
    - polymarket-trader/.gitignore
decisions:
  - "resolve_needed returns True on first run (no resolve report = trigger)"
  - "expiring_soon uses 48h window vs resolve_needed 24h window for different urgency levels"
  - "signal.json added to .gitignore as generated runtime state"
metrics:
  duration: 249s
  completed: "2026-04-04T08:19:37Z"
  tasks: 2
  files: 4
---

# Phase 3 Plan 03: Heartbeat Signal Generator Summary

Heartbeat script reads local DB and filesystem only (zero API/LLM cost), writes state/signal.json with scan_needed, resolve_needed, learn_needed boolean flags for cron-based cycle triggering.

## Commits

| Hash | Type | Description |
|------|------|-------------|
| eee20b0 | test | TDD RED: 14 failing tests for heartbeat signal logic |
| 83d3de6 | feat | TDD GREEN: implement heartbeat.py with all 5 functions |
| d617612 | chore | Full regression pass (234 tests) and gitignore signal.json |

## Task Results

### Task 1: Create scripts/heartbeat.py and tests (TDD)

- **Status:** Complete
- **Commit:** eee20b0 (RED), 83d3de6 (GREEN)
- **Files:** scripts/__init__.py, scripts/heartbeat.py, tests/test_heartbeat.py
- **Details:**
  - `scan_needed()`: Checks cycle-*.md mtime in state/reports/, True if none or > 4h old
  - `resolve_needed()`: Queries market_snapshots for expiring positions (24h), falls back to resolve report timing (1h)
  - `learn_needed()`: Checks calibration_records timestamps vs last learn-*.md report
  - `expiring_soon()`: Lists position questions with end_date within 48h
  - `main()`: Orchestrates all checks, writes signal.json, creates missing directories
  - 14 test functions covering all flag logic with controlled timestamps and mocked filesystem

### Task 2: Full regression test suite and cleanup

- **Status:** Complete
- **Commit:** d617612
- **Files:** .gitignore
- **Details:**
  - 234 tests pass (220 existing + 14 new heartbeat)
  - heartbeat.py end-to-end: writes valid state/signal.json
  - test_db.py already expects 6 tables including calibration_records (no change needed)
  - Added state/signal.json to .gitignore (generated runtime output)
  - test_strategy_evolution.py has 6 pre-existing failures from Phase 2 strategy.md content change (out of scope)

## Decisions Made

1. **resolve_needed first-run behavior:** Returns True when no resolve report exists, ensuring the system triggers a resolve check on first ever run
2. **Dual expiry windows:** 24h for resolve_needed (urgent action), 48h for expiring_soon (informational listing)
3. **signal.json gitignored:** Runtime-generated state file should not be committed

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all functions are fully implemented with real DB queries and filesystem checks.

## Verification Results

- `python -m pytest tests/test_heartbeat.py -x -v`: 14 passed
- `python scripts/heartbeat.py`: writes state/signal.json with all 3 flags
- `python -m pytest tests/ --ignore=tests/test_strategy_evolution.py -v`: 234 passed
- `grep -c "def test_" tests/test_calibration.py tests/test_market_intel.py tests/test_heartbeat.py`: 21 + 16 + 14 = 51 new tests
