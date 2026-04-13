# Scheduling & Autonomous Operation

The system runs unattended via three cron jobs with a cost-efficient heartbeat gating pattern.

## How It Works

```
Every 10 min:  heartbeat.py  -->  Checks prices/state, writes signal.json  (zero LLM cost)
Every 30 min:  run_cycle.sh  -->  Reads signal.json, only launches Claude if work needed
Daily 2 AM:    run_cycle.sh --force  -->  Full scan regardless of signals
```

The heartbeat is a lightweight Python script that checks market prices and local state. It sets boolean flags (`scan_needed`, `resolve_needed`, `learn_needed`) in `state/signal.json`. The gated cycle reads those flags and only spins up an expensive Claude session when there's actual work to do.

This means most 30-minute intervals cost nothing -- Claude only runs when markets have moved, positions need checking, or it's time to learn from resolutions.

## Setup

```bash
# Install all 3 cron entries
./scripts/install_cron.sh

# Verify
crontab -l | grep polymarket-trader

# Remove all entries
./scripts/install_cron.sh --remove

# Show current crontab (no changes)
./scripts/install_cron.sh --show
```

The installer is idempotent -- running it twice produces the same result. It also removes legacy `polymarket-trading-agent` entries from older versions.

## Scripts

### heartbeat.py

Runs every 10 minutes. Reads local state and writes `state/signal.json`:

```json
{
  "generated_at": "2026-04-05T18:30:00Z",
  "scan_needed": true,
  "resolve_needed": false,
  "learn_needed": false,
  "expiring_soon": ["market-abc-123"],
  "open_positions": 2
}
```

Flags:
- `scan_needed` -- New markets available or prices moved significantly
- `resolve_needed` -- Open positions may have resolved
- `learn_needed` -- Resolved positions need post-mortem analysis

### run_cycle.sh

Launches a full trading cycle in a tmux session.

```bash
./scripts/run_cycle.sh           # Gated: only runs if signal.json has work
./scripts/run_cycle.sh --force   # Skip signal check, always run
./scripts/run_cycle.sh --dry-run # Show what would happen without running
```

Features:
- PID locking (`state/.run_cycle.pid`) prevents overlapping cycles
- 20-minute timeout per cycle
- Launches Claude with `--dangerously-skip-permissions` for unattended operation
- Logs to `state/run_cycle.log`

### status.sh

Quick health check for monitoring.

```bash
./scripts/status.sh
```

Output:
```
======================================
  POLYMARKET TRADER STATUS
======================================
  Last heartbeat:  3 min ago (2026-04-05T16:30:00Z)
  Last cycle:      22 min ago (2026-04-05T16:08:00Z)
  Total cycles:    47
  Open positions:  2
  Active flags:    scan_needed
  Errors (24h):    0
  Live trading:    DISABLED
======================================
```

## Logs

| Log | Location | Contents |
|-----|----------|----------|
| Heartbeat | `state/heartbeat.log` | Signal generation output |
| Cycle launcher | `state/run_cycle.log` | Cron execution: signal check, PID lock, launch result |
| Trading | `trading.log` | Structured JSON log from trading sessions |
| Cycle reports | `state/reports/cycle-{id}.md` | Per-cycle markdown reports |

## Monitoring

Check status anytime:
```bash
./scripts/status.sh              # Quick summary
tail -20 state/run_cycle.log     # Recent cron activity
ls -la state/reports/ | tail -5  # Recent cycle reports
```

Check for problems:
```bash
grep -i "error\|fail\|abort" state/run_cycle.log | tail -10
```
