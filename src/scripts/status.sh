#!/usr/bin/env bash
# status.sh -- Quick health check for polymarket-trader
#
# Shows: last heartbeat, last cycle, total cycles, recent errors.
# Not a monitoring dashboard -- just a quick sanity check.
#
# Usage:
#   ./scripts/status.sh           # Human-readable summary
#   ./scripts/status.sh --json    # JSON output
#
# Decision: D-10

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SIGNAL_FILE="$PROJECT_ROOT/state/signal.json"
LOG_FILE="$PROJECT_ROOT/state/run_cycle.log"
HEARTBEAT_LOG="$PROJECT_ROOT/state/heartbeat.log"
REPORTS_DIR="$PROJECT_ROOT/state/reports"

JSON_MODE=false
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        *)      echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

# ── Data Collection ───────────────────────────────────────────────────

# Last heartbeat time (from signal.json)
last_heartbeat="unknown"
if [ -f "$SIGNAL_FILE" ]; then
    last_heartbeat=$(python3 -c "
import json
try:
    with open('$SIGNAL_FILE') as f:
        sig = json.load(f)
    print(sig.get('generated_at', 'unknown'))
except:
    print('unknown')
" 2>/dev/null)
fi

# Time since last heartbeat
heartbeat_ago="unknown"
if [ "$last_heartbeat" != "unknown" ]; then
    heartbeat_ago=$(python3 -c "
from datetime import datetime, timezone
try:
    t = datetime.fromisoformat('$last_heartbeat')
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - t
    mins = int(delta.total_seconds() / 60)
    if mins < 60:
        print(f'{mins} min ago')
    elif mins < 1440:
        print(f'{mins // 60}h {mins % 60}m ago')
    else:
        print(f'{mins // 1440}d {(mins % 1440) // 60}h ago')
except:
    print('unknown')
" 2>/dev/null)
fi

# Last cycle time (from most recent cycle report)
last_cycle="none"
last_cycle_ago="never"
if [ -d "$REPORTS_DIR" ]; then
    latest_report=$(ls -t "$REPORTS_DIR"/cycle-*.md 2>/dev/null | head -1)
    if [ -n "$latest_report" ]; then
        # Extract timestamp from filename or file mtime
        last_cycle=$(date -u -r "$latest_report" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "unknown")
        last_cycle_ago=$(python3 -c "
import os
from datetime import datetime, timezone
try:
    mtime = os.path.getmtime('$latest_report')
    t = datetime.fromtimestamp(mtime, tz=timezone.utc)
    delta = datetime.now(timezone.utc) - t
    mins = int(delta.total_seconds() / 60)
    if mins < 60:
        print(f'{mins} min ago')
    elif mins < 1440:
        print(f'{mins // 60}h {mins % 60}m ago')
    else:
        print(f'{mins // 1440}d {(mins % 1440) // 60}h ago')
except:
    print('unknown')
" 2>/dev/null)
    fi
fi

# Total cycle count
cycle_count=0
if [ -d "$REPORTS_DIR" ]; then
    cycle_count=$(ls "$REPORTS_DIR"/cycle-*.md 2>/dev/null | wc -l)
fi

# Errors in last 24h from run_cycle.log
errors_24h=0
if [ -f "$LOG_FILE" ]; then
    cutoff=$(date -u -d "24 hours ago" +"%Y-%m-%dT%H:%M:%S" 2>/dev/null || date -u -v-24H +"%Y-%m-%dT%H:%M:%S" 2>/dev/null || echo "")
    if [ -n "$cutoff" ]; then
        errors_24h=$(grep -i -c "error\|failed\|aborting\|timed out" "$LOG_FILE" 2>/dev/null | tail -1 || echo "0")
    fi
fi

# Active flags from signal.json
active_flags="none"
if [ -f "$SIGNAL_FILE" ]; then
    active_flags=$(python3 -c "
import json
try:
    with open('$SIGNAL_FILE') as f:
        sig = json.load(f)
    flags = [k for k in ('scan_needed', 'resolve_needed', 'learn_needed') if sig.get(k)]
    print(', '.join(flags) if flags else 'none')
except:
    print('unknown')
" 2>/dev/null)
fi

# Open positions
open_positions=0
if [ -f "$SIGNAL_FILE" ]; then
    open_positions=$(python3 -c "
import json
try:
    with open('$SIGNAL_FILE') as f:
        sig = json.load(f)
    print(sig.get('open_positions', 0))
except:
    print(0)
" 2>/dev/null)
fi

# Gate pass status
gate_status="DISABLED"
if [ -f "$PROJECT_ROOT/.live-gate-pass" ]; then
    gate_status="ENABLED"
fi

# ── Output ────────────────────────────────────────────────────────────

if [ "$JSON_MODE" = true ]; then
    python3 -c "
import json
data = {
    'last_heartbeat': '$last_heartbeat',
    'heartbeat_ago': '$heartbeat_ago',
    'last_cycle': '$last_cycle',
    'last_cycle_ago': '$last_cycle_ago',
    'cycle_count': $cycle_count,
    'errors_24h': $errors_24h,
    'active_flags': '$active_flags',
    'open_positions': $open_positions,
    'live_trading': '$gate_status'
}
print(json.dumps(data, indent=2))
"
else
    echo "======================================"
    echo "  POLYMARKET TRADER STATUS"
    echo "======================================"
    echo "  Last heartbeat:  $heartbeat_ago ($last_heartbeat)"
    echo "  Last cycle:      $last_cycle_ago ($last_cycle)"
    echo "  Total cycles:    $cycle_count"
    echo "  Open positions:  $open_positions"
    echo "  Active flags:    $active_flags"
    echo "  Errors (24h):    $errors_24h"
    echo "  Live trading:    $gate_status"
    echo "======================================"
fi
