# Phase 6: Scheduling & Paper Validation - Context

**Gathered:** 2026-04-05
**Status:** Ready for planning

<domain>
## Phase Boundary

Unattended cron automation (heartbeat every 10min, gated cycles every 30min, daily forced scan at 2 AM UTC), 20+ autonomous paper trading cycles proving strategy evolution and calibration tracking, and a live trading gate that checks 4 criteria including calibration health before allowing real money. Deliverables: cron setup script, enhanced enable_live.py, status monitoring script, and evidence of 20+ successful cycles.

</domain>

<decisions>
## Implementation Decisions

### Cron Setup
- **D-01:** Build `scripts/install_cron.sh` — idempotent script that installs all 3 crontab entries (10-min heartbeat, 30-min gated cycle, 2 AM daily forced scan). Single command to go from zero to scheduled.
- **D-02:** `install_cron.sh` auto-detects and removes the old `polymarket-agent/run_cycle.sh` crontab entry. Clean cutover.
- **D-03:** `install_cron.sh --remove` strips all polymarket-trader cron entries. Clean on/off switch for the entire system.
- **D-04:** Daily 2 AM UTC scan uses `run_cycle.sh --force` directly — bypasses heartbeat gating entirely. Guarantees a full cycle even if signal.json says no work needed.

### Live Gate Upgrade
- **D-05:** `enable_live.py --check` runs all 4 criteria, any single failure blocks: (1) cycles >= 10, (2) P&L > 0, (3) win rate > 50%, (4) no category calibration bias > -20pp. Clear pass/fail with per-criterion status.
- **D-06:** Calibration health comes from `lib/calibration.py` — add a `get_calibration_health()` function that queries the DB for per-category bias. enable_live.py calls it. Keeps calibration logic centralized.
- **D-07:** `enable_live.py --check` outputs JSON to stdout (machine-readable) + human summary to stderr. Matches existing CLI conventions (JSON default, --pretty for human output).

### Validation Evidence
- **D-08:** `validate_cycle.py --summary` is the proof artifact for 20+ cycles. It already aggregates total cycles, rules added, calibration entries, playbooks modified, strategy growth. No new validation tooling needed.
- **D-09:** Let cron accumulate cycles naturally over 2+ days. 30-min intervals = real-world validation of unattended operation. No turbo/fast mode — the 2-day unattended run IS the test.

### Unattended Operations
- **D-10:** Build `scripts/status.sh` — shows last heartbeat time, last cycle time, total cycle count, any errors in last 24h. Quick health check on demand.
- **D-11:** No log rotation needed for v1. 2 days of 30-min cycles = ~96 log entries. Tiny. Can add later if needed.
- **D-12:** Auto-recovery via existing PID lock mechanism (25-min stale threshold). If a cycle crashes, next cron invocation cleans stale lock and launches fresh. No manual intervention needed, no crash counter.

### Claude's Discretion
- Internal structure of `install_cron.sh` (how it manages crontab entries — sed, grep, temp file approach)
- Exact format of `scripts/status.sh` output
- Whether `get_calibration_health()` returns raw bias numbers or a structured health report object
- How `enable_live.py` computes win rate (from DB trades table or from calibration records)
- SCHED-05 implementation details (--dangerously-skip-permissions in the cron-invoked Claude command)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scheduling Infrastructure (modification targets)
- `polymarket-trader/scripts/run_cycle.sh` — Existing cycle launcher with --force, PID lock, tmux, timeout. Cron calls this.
- `polymarket-trader/scripts/heartbeat.py` — Writes state/signal.json. Cron runs this every 10 min.

### Live Gate (enhancement target)
- `polymarket-trader/tools/enable_live.py` — Current version checks cycle count + P&L only. Needs win rate and calibration health added.
- `polymarket-trader/lib/calibration.py` — Calibration library. Needs get_calibration_health() function added.
- `polymarket-trader/lib/db.py` — DataStore class with get_paper_cycle_stats(). May need win rate query.

### Validation
- `polymarket-trader/tools/validate_cycle.py` — Per-cycle and --summary validation. The proof artifact.
- `polymarket-trader/state/reports/` — Cycle reports directory (evidence accumulates here)

### Config & State
- `polymarket-trader/lib/config.py` — Config dataclass. May need min_paper_cycles and gate criteria fields.
- `polymarket-trader/state/core-principles.md` — Immutable guardrails (NEVER modify)
- `polymarket-trader/.claude/CLAUDE.md` — Trading cycle instructions (reference only, no changes in this phase)

### Requirements
- `.planning/REQUIREMENTS.md` — SCHED-01, SCHED-02, SCHED-03, SCHED-05, SAFE-02, VAL-01 through VAL-05

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `run_cycle.sh` already has --force flag, PID locking, tmux, 20-min timeout — cron just calls it
- `heartbeat.py` already writes signal.json with scan/resolve/learn flags — cron just runs it
- `enable_live.py` has gate pass file pattern, DataStore integration, --status/--revoke flags — extend it
- `validate_cycle.py --summary` already aggregates cycle evidence — no new validation tooling
- `lib/calibration.py` already has Brier score and category tracking — add health check function
- Old crontab entry exists: `0 * * * * /home/trader/polymarket-agent/run_cycle.sh`

### Established Patterns
- CLI tools: argparse + JSON stdout + --pretty flag + human info to stderr
- State files: JSON in state/ directory
- Config: env vars loaded via config.py
- Tests: pytest with unittest.mock.patch, in-memory SQLite

### Integration Points
- `scripts/install_cron.sh` — new script, manages crontab entries
- `scripts/status.sh` — new script, reads run_cycle.log and state files
- `lib/calibration.py` — add get_calibration_health() function
- `tools/enable_live.py` — add win rate check, calibration health check, --check flag enhancement
- Crontab — 3 new entries replacing 1 old entry

</code_context>

<specifics>
## Specific Ideas

- The 3 cron entries: `*/10 * * * *` for heartbeat, `*/30 * * * *` for gated cycle, `0 2 * * *` for forced daily scan
- install_cron.sh should use a marker comment (e.g., `# polymarket-trader`) to identify its entries for idempotent add/remove
- status.sh is a quick sanity check — not a monitoring dashboard. Just: "last heartbeat 3 min ago, last cycle 22 min ago, 47 cycles total, 0 errors in 24h"
- enable_live.py --check is read-only (no gate pass writing). Separate from the existing enable flow that requires CONFIRM LIVE.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-scheduling-paper-validation*
*Context gathered: 2026-04-05*
