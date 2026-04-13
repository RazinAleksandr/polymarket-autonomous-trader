---
phase: 04-config-integration
plan: 02
subsystem: scheduling
tags: [run-cycle, heartbeat-gating, pid-lock, tmux, timeout, bash]
dependency_graph:
  requires: [heartbeat-signal]
  provides: [cycle-launcher, heartbeat-gating]
  affects: [cron-scheduling, autonomous-cycles]
tech_stack:
  added: [bash-script]
  patterns: [pid-locking, signal-gating, tmux-sessions]
key_files:
  created:
    - polymarket-trader/scripts/run_cycle.sh
    - polymarket-trader/tests/test_run_cycle.py
  modified: []
decisions:
  - "D-TIMEOUT: 20-minute (1200s) timeout on Claude sessions, with 25-minute stale PID threshold"
  - "D-TMUX: Falls back to direct execution if tmux not available"
  - "D-WRAPPER: Tests use wrapper scripts overriding paths to tmp_path for isolation"
metrics:
  duration: 194s
  completed: "2026-04-04T09:38:12Z"
  tasks: 2
  files: 2
---

# Phase 04 Plan 02: Heartbeat-Gated Cycle Launcher Summary

Bash cycle launcher that reads heartbeat signal.json and only launches expensive Claude trading sessions when work is needed -- with PID locking, tmux session management, and 20-minute timeout.

## What Was Built

### run_cycle.sh (scripts/run_cycle.sh)
- **Signal gating**: Reads `state/signal.json` and exits 0 immediately when all flags (scan_needed, resolve_needed, learn_needed) are false
- **Flag detection**: When any flag is true, proceeds to launch a Claude Code CLI trading session
- **PID locking**: Creates `state/.run_cycle.pid` to prevent concurrent cycle runs; detects and cleans stale PIDs (>25min or dead process)
- **tmux sessions**: Manages a "trader" tmux session for background execution; falls back to direct execution if tmux unavailable
- **20-minute timeout**: Uses `timeout 1200` to kill runaway Claude sessions
- **Auto-heartbeat**: If signal.json is missing, runs heartbeat.py first to generate it
- **CLI flags**: `--force` skips signal check, `--dry-run` checks signal without launching
- **Logging**: All actions logged to `state/run_cycle.log` with UTC timestamps

### Tests (tests/test_run_cycle.py)
- 21 tests covering signal gating, PID locking, argument handling, and script integrity
- Tests use wrapper scripts with overridden paths for tmp_path isolation
- Signal gating: all-false exits, each individual flag triggers, multiple flags, missing signal.json
- PID locking: creation, cleanup on exit, stale (no process), stale (empty), active PID blocks
- Arguments: --force, --dry-run, both combined
- Script integrity: exists, executable, syntax, shebang, references signal.json/PID/timeout/tmux

## Test Results

261/262 total tests pass (1 pre-existing failure in test_strategy_evolution.py unrelated to changes).
21 new tests for run_cycle.sh all pass.

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all functionality is complete and wired.

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 23784ea | feat | Heartbeat-gated cycle launcher run_cycle.sh |
| 96d4af1 | test | 21 tests for run_cycle.sh signal gating, PID locking, arguments |

## Self-Check: PASSED

All 2 files verified present. All 2 commits verified in git log.
