---
phase: quick
plan: 260330-cb9
subsystem: scheduling
tags: [cron, environment, tmux, bugfix]
dependency_graph:
  requires: []
  provides: [cron-env-propagation, claude-pre-flight-check]
  affects: [run_cycle.sh, schedule_trading.sh]
tech_stack:
  added: []
  patterns: [runner-script-for-tmux-env, set-a-auto-export]
key_files:
  created: []
  modified:
    - run_cycle.sh
    - schedule_trading.sh
decisions:
  - Runner script pattern chosen over tmux send-keys for reliable env propagation
  - Fallback PATH updated for Linux (removed macOS-only /opt/homebrew/bin)
metrics:
  duration: 1min
  completed: "2026-03-30"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Quick Task 260330-cb9: Fix run_cycle.sh Cron Environment Bug

Runner script pattern for tmux env propagation, pre-flight claude check, and error capture logging.

## What Changed

### Task 1: Environment snapshot in schedule_trading.sh (a06b40f)

- Added `env` snapshot to `.cron-env` in `do_start()` after creating the session log file
- Full environment (minus `_`, `SHLVL`, `PWD`) captured with proper quoting for later sourcing
- `.cron-env` cleaned up in `do_stop()` alongside other temporary files

### Task 2: run_cycle.sh env propagation, pre-flight, and error logging (423672d)

- **Env loading**: Changed from bare `source .cron-env` to `set -a` / `source` / `set +a` for auto-export
- **Pre-flight check**: Added `command -v claude` check before launching tmux -- exits with FATAL log if missing
- **Runner script pattern**: Replaced interactive tmux + `send-keys` approach with a temporary runner script (`/tmp/polymarket-cycle-runner-$$.sh`) that:
  - Sources `.cron-env` inside the tmux session (guarantees env propagation)
  - Runs claude with `-p 'run a trading cycle'` (non-interactive)
  - Captures stdout/stderr to `logs/claude-{session}.log` via `tee`
  - Logs success/failure with timestamps
  - Self-cleans after execution
- **End logging**: Replaced single `log "END"` with log output that reports claude log line count and warns if minimal output detected (likely failed to start)
- **Fallback PATH**: Removed macOS-only `/opt/homebrew/bin`, added `/usr/bin` and `$HOME/.local/bin` for Linux

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED
