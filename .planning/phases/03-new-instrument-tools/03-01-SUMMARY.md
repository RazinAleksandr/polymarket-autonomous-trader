---
phase: 03-new-instrument-tools
plan: 01
subsystem: calibration
tags: [calibration, brier-score, feedback-loop, sqlite, cli]
dependency_graph:
  requires: []
  provides: [calibration-library, record-outcome-cli, calibration-records-table]
  affects: [calibration-check-skill, evaluate-edge-skill, strategy-evolution]
tech_stack:
  added: []
  patterns: [brier-score, calibration-corrections, tdd]
key_files:
  created:
    - polymarket-trader/lib/calibration.py
    - polymarket-trader/tools/record_outcome.py
    - polymarket-trader/tests/test_calibration.py
  modified:
    - polymarket-trader/lib/db.py
    - polymarket-trader/lib/models.py
    - polymarket-trader/tests/test_db.py
decisions:
  - "D-SIGN: error_pp sign convention follows plan definition: positive=underconfident, negative=overconfident, computed as (stated_prob - actual) * 100"
  - "D-CORR: Correction amount uses conservative 70% of observed error, capped at 20pp, matching plan specification"
metrics:
  duration: 224s
  completed: "2026-04-04T08:10:30Z"
  tasks: 2
  files: 6
---

# Phase 03 Plan 01: Calibration Tracking Library Summary

Brier score calculation, per-category accuracy tracking, auto-generated calibration corrections, and CLI wrapper for recording trade outcomes -- the core learning feedback loop that lets the agent improve from its own predictions.

## What Was Built

### lib/calibration.py (6 public functions)
- `compute_brier_score(stated_prob, outcome)` -- (stated_prob - actual)^2
- `interpret_error(error_pp, n_trades)` -- human-readable assessment with action recommendations
- `record_calibration_outcome(store, ...)` -- inserts row into calibration_records table
- `get_calibration_summary(store)` -- aggregates per-category and overall stats from DB
- `generate_corrections(store)` -- produces correction dicts for categories with >= 5 trades and |error_pp| > 10
- `regenerate_calibration_json(store, json_path)` -- writes complete calibration.json from DB state

### tools/record_outcome.py (CLI wrapper)
- argparse with --market-id, --stated-prob, --actual, --category, --pnl, --notes, --pretty
- Validates stated_prob [0.0, 1.0] and category against 6 valid options
- Calls record_calibration_outcome then regenerate_calibration_json (per D-02 auto-regenerate)
- JSON stdout output following get_prices.py pattern

### Database: calibration_records table
- Added to DataStore._create_tables() alongside existing 5 tables (6 total)
- Schema: id, timestamp, market_id, category, stated_prob, actual_outcome, brier_score, error_pp, pnl, notes

### CalibrationRecord dataclass
- Added to lib/models.py with to_dict() method

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 (RED) | a9997ee | Failing tests for calibration library (20 test functions) |
| 1 (GREEN) | c5c91e6 | Implement calibration library, models, DB table |
| 2 | b78e8b7 | Create record_outcome.py CLI wrapper |

## Test Results

- 21 calibration tests passing (Brier math, interpret_error, record/summary/corrections/regenerate, table creation)
- 9 existing DB tests passing (updated to expect 6 tables, no regressions)
- Total: 30 tests passing

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_generate_corrections_with_bias test data**
- **Found during:** Task 1 GREEN phase
- **Issue:** Test used 6 LOSS trades at stated_prob=0.70, yielding error_pp=+70 (underconfident by plan convention), but test expected direction="subtract" (overconfident correction). Sign convention mismatch.
- **Fix:** Changed test to use 6 WIN trades at stated_prob=0.30, yielding error_pp=-70 (overconfident by plan convention), correctly triggering direction="subtract".
- **Files modified:** polymarket-trader/tests/test_calibration.py
- **Commit:** c5c91e6

## Known Stubs

None -- all functions are fully wired to the SQLite database and produce real output.

## Self-Check: PASSED
