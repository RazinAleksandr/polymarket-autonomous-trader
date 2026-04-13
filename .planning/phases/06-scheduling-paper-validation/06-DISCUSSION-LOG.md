# Phase 6: Scheduling & Paper Validation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-05
**Phase:** 06-scheduling-paper-validation
**Areas discussed:** Cron setup, Live gate upgrade, Validation evidence, Unattended ops

---

## Cron Setup

### Q1: How should the cron entries be installed?

| Option | Description | Selected |
|--------|-------------|----------|
| Setup script | Build scripts/install_cron.sh — idempotent, adds all 3 entries, removes old agent entry | ✓ |
| Manual crontab instructions | Document crontab lines, user pastes manually | |
| You decide | Claude picks best approach | |

**User's choice:** Setup script (Recommended)
**Notes:** Single command to go from zero to scheduled.

### Q2: Should install_cron.sh remove old polymarket-agent cron entry?

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-remove | Detect and remove old polymarket-agent cron entry automatically | ✓ |
| Warn only | Detect and warn but don't touch it | |
| Ignore it | Don't check for old entries | |

**User's choice:** Auto-remove (Recommended)
**Notes:** Clean cutover to new system.

### Q3: Should install_cron.sh have a --remove flag?

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, --remove flag | Strips all polymarket-trader cron entries. Clean on/off switch. | ✓ |
| No, install only | User removes entries manually via crontab -e | |

**User's choice:** Yes, --remove flag (Recommended)

### Q4: Daily 2 AM UTC forced scan approach?

| Option | Description | Selected |
|--------|-------------|----------|
| run_cycle.sh --force | Bypass heartbeat gating entirely. Guarantees full cycle. | ✓ |
| heartbeat.py --force-all | Force heartbeat to set all flags, let normal cycle pick it up | |
| You decide | Claude picks based on script design | |

**User's choice:** run_cycle.sh --force (Recommended)

---

## Live Gate Upgrade

### Q1: How should --check mode work?

| Option | Description | Selected |
|--------|-------------|----------|
| All 4 checks, any blocks | Cycles >= 10, P&L > 0, win rate > 50%, no category bias > -20pp. Any failure blocks. | ✓ |
| Tiered: hard + soft | Cycles/P&L hard block, win rate/calibration are overridable warnings | |
| You decide | Claude designs gate logic | |

**User's choice:** All 4 checks, any blocks (Recommended)

### Q2: Where should calibration health data come from?

| Option | Description | Selected |
|--------|-------------|----------|
| calibration.py library | Add get_calibration_health() to lib/calibration.py. Centralized. | ✓ |
| Direct DB query | enable_live.py queries calibration table directly | |
| Read calibration.json | Parse the knowledge/calibration.json file | |

**User's choice:** calibration.py library (Recommended)

### Q3: Output format for enable_live.py --check?

| Option | Description | Selected |
|--------|-------------|----------|
| Both: JSON + summary | JSON to stdout, human summary to stderr. Matches CLI conventions. | ✓ |
| JSON only | Pure JSON, use --pretty or jq for human reading | |
| Human report only | Formatted text, harder to script | |

**User's choice:** Both: JSON + summary (Recommended)

---

## Validation Evidence

### Q1: What counts as 'validated' for 20+ cycles?

| Option | Description | Selected |
|--------|-------------|----------|
| validate_cycle.py --summary | Already aggregates evidence. That output IS the proof. | ✓ |
| Dedicated validation report | New script with P&L curve, strategy diffs, calibration trends | |
| Manual spot-check | Eyeball reports, strategy.md, calibration.json | |

**User's choice:** validate_cycle.py --summary (Recommended)

### Q2: How to accumulate 20+ cycles?

| Option | Description | Selected |
|--------|-------------|----------|
| Natural cron pace | 30-min intervals over 2+ days. Real-world validation. | ✓ |
| Turbo mode script | Back-to-back cycles for fast proof. Artificial. | |
| Both options | Natural for real validation + turbo for dev smoke testing | |

**User's choice:** Natural cron pace (Recommended)

---

## Unattended Ops

### Q1: How to monitor during 2+ days unattended?

| Option | Description | Selected |
|--------|-------------|----------|
| Log files + status script | Build scripts/status.sh showing last heartbeat, last cycle, errors | ✓ |
| Heartbeat watchdog | Alert via email/webhook if no cycle in N hours | |
| Logs only | Check run_cycle.log and reports/ manually | |

**User's choice:** Log files + status script (Recommended)

### Q2: Log rotation?

| Option | Description | Selected |
|--------|-------------|----------|
| No rotation needed | ~96 entries over 2 days. Tiny. Add later if needed. | ✓ |
| Simple size-based rotation | Rotate at 1MB, keep last 3 | |
| You decide | Claude picks based on expected volume | |

**User's choice:** No rotation needed (Recommended)

### Q3: Error recovery approach?

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-recover via PID lock | Existing 25-min stale detection. Next cron cleans and relaunches. | ✓ |
| Add crash counter | Stop after 3 consecutive crashes. Prevents crash loops. | |
| You decide | Claude picks recovery strategy | |

**User's choice:** Auto-recover via PID lock (Recommended)

---

## Claude's Discretion

- Internal structure of install_cron.sh
- Format of status.sh output
- get_calibration_health() return type
- How win rate is computed
- SCHED-05 implementation details

## Deferred Ideas

None — discussion stayed within phase scope
