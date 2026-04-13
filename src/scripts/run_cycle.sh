#!/usr/bin/env bash
# run_cycle.sh -- Heartbeat-gated cycle launcher
#
# Called by cron every ~30 minutes. Reads state/signal.json (written by
# heartbeat.py every ~10 minutes) and only launches an expensive Claude
# trading session when the heartbeat indicates work is needed.
#
# Features:
#   - Signal gating: exits immediately when all heartbeat flags are false
#   - PID locking: prevents concurrent cycle runs
#   - tmux session: runs Claude in a detached tmux session
#   - 20-minute timeout: kills runaway sessions
#   - Logging: all actions logged to state/run_cycle.log
#
# Usage:
#   ./scripts/run_cycle.sh           # Normal cron invocation
#   ./scripts/run_cycle.sh --force   # Skip signal check, always run
#   ./scripts/run_cycle.sh --dry-run # Check signal but don't launch

set -euo pipefail

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SIGNAL_FILE="$PROJECT_ROOT/state/signal.json"
PID_FILE="$PROJECT_ROOT/state/.run_cycle.pid"
LOG_FILE="$PROJECT_ROOT/state/run_cycle.log"
HEARTBEAT_SCRIPT="$PROJECT_ROOT/scripts/heartbeat.py"
VENV_ACTIVATE="$PROJECT_ROOT/.venv/bin/activate"

TMUX_SESSION="trader"
TIMEOUT_SECONDS=1200  # 20 minutes
STALE_PID_SECONDS=1500  # 25 minutes (timeout + buffer)

# ── Flags ──────────────────────────────────────────────────────────────
FORCE=false
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --force)   FORCE=true ;;
        --dry-run) DRY_RUN=true ;;
        *)         echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

# ── Logging ────────────────────────────────────────────────────────────
log() {
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    local msg="[$timestamp] $1"
    echo "$msg" >> "$LOG_FILE"
    echo "$msg"
}

# Ensure state directory and log file exist
mkdir -p "$PROJECT_ROOT/state"
touch "$LOG_FILE"

# ── PID Locking ────────────────────────────────────────────────────────
cleanup() {
    if [ -f "$PID_FILE" ]; then
        local stored_pid
        stored_pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [ "$stored_pid" = "$$" ]; then
            rm -f "$PID_FILE"
            log "Removed PID file (pid=$$)"
        fi
    fi
}
trap cleanup EXIT

check_pid_lock() {
    if [ ! -f "$PID_FILE" ]; then
        return 0  # No lock, safe to proceed
    fi

    local stored_pid
    stored_pid=$(cat "$PID_FILE" 2>/dev/null || echo "")

    # Empty PID file -- stale
    if [ -z "$stored_pid" ]; then
        log "Stale PID file (empty), removing"
        rm -f "$PID_FILE"
        return 0
    fi

    # Check if process is still running
    if kill -0 "$stored_pid" 2>/dev/null; then
        # Process exists -- check if it's stale by file age
        local pid_age
        pid_age=$(( $(date +%s) - $(stat -c %Y "$PID_FILE" 2>/dev/null || echo "0") ))

        if [ "$pid_age" -gt "$STALE_PID_SECONDS" ]; then
            log "Stale PID file (age=${pid_age}s > ${STALE_PID_SECONDS}s), killing pid=$stored_pid"
            kill "$stored_pid" 2>/dev/null || true
            sleep 1
            kill -9 "$stored_pid" 2>/dev/null || true
            rm -f "$PID_FILE"
            return 0
        fi

        log "Cycle already running (pid=$stored_pid, age=${pid_age}s), exiting"
        return 1
    fi

    # Process not running -- stale PID file
    log "Stale PID file (pid=$stored_pid not running), removing"
    rm -f "$PID_FILE"
    return 0
}

acquire_lock() {
    echo "$$" > "$PID_FILE"
    log "Acquired PID lock (pid=$$)"
}

# ── Signal Check ───────────────────────────────────────────────────────
check_signal() {
    # If signal.json doesn't exist, run heartbeat first
    if [ ! -f "$SIGNAL_FILE" ]; then
        log "No signal.json found, running heartbeat first"
        if [ -f "$VENV_ACTIVATE" ]; then
            (cd "$PROJECT_ROOT" && source "$VENV_ACTIVATE" && python "$HEARTBEAT_SCRIPT") >> "$LOG_FILE" 2>&1
        else
            (cd "$PROJECT_ROOT" && python "$HEARTBEAT_SCRIPT") >> "$LOG_FILE" 2>&1
        fi

        if [ ! -f "$SIGNAL_FILE" ]; then
            log "Heartbeat failed to create signal.json, aborting"
            return 1
        fi
    fi

    # Parse flags from signal.json using Python for reliable JSON parsing
    local any_flag
    any_flag=$(python3 -c "
import json, sys
try:
    with open('$SIGNAL_FILE') as f:
        sig = json.load(f)
    flags = [sig.get('scan_needed', False), sig.get('resolve_needed', False), sig.get('learn_needed', False)]
    active = [k for k, v in [('scan', sig.get('scan_needed')), ('resolve', sig.get('resolve_needed')), ('learn', sig.get('learn_needed'))] if v]
    if active:
        print('|'.join(active))
    else:
        print('NONE')
except Exception as e:
    print(f'ERROR:{e}', file=sys.stderr)
    print('ERROR')
" 2>>"$LOG_FILE")

    if [ "$any_flag" = "NONE" ]; then
        log "All flags false -- no work needed"
        return 1  # No work needed
    elif [ "$any_flag" = "ERROR" ]; then
        log "Error parsing signal.json"
        return 1
    else
        log "Active flags: $any_flag"
        return 0  # Work needed
    fi
}

# ── Cycle Launch ───────────────────────────────────────────────────────
launch_cycle() {
    local cycle_id
    cycle_id="$(date -u +"%Y%m%d-%H%M%S")"

    log "Launching trading cycle $cycle_id (timeout=${TIMEOUT_SECONDS}s)"

    # Build the Claude command
    # Claude Code CLI reads .claude/CLAUDE.md automatically from the project dir
    local claude_cmd="cd $PROJECT_ROOT && IS_SANDBOX=1 claude --dangerously-skip-permissions --print 'Run a complete trading cycle. Cycle ID: $cycle_id. Read .claude/CLAUDE.md for instructions.'"

    if command -v tmux &>/dev/null; then
        # Check if tmux session exists
        if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
            log "tmux session '$TMUX_SESSION' exists, sending command to it"
            tmux send-keys -t "$TMUX_SESSION" "timeout $TIMEOUT_SECONDS bash -c '$claude_cmd'" C-m
        else
            log "Creating tmux session '$TMUX_SESSION'"
            tmux new-session -d -s "$TMUX_SESSION" "timeout $TIMEOUT_SECONDS bash -c '$claude_cmd'; echo 'Cycle complete. Press Enter to close.'; read"
        fi

        log "Cycle $cycle_id launched in tmux session '$TMUX_SESSION'"
    else
        # Fallback: run directly with timeout (blocking)
        log "tmux not available, running directly with timeout"
        timeout "$TIMEOUT_SECONDS" bash -c "$claude_cmd" >> "$LOG_FILE" 2>&1 || {
            local exit_code=$?
            if [ "$exit_code" -eq 124 ]; then
                log "Cycle $cycle_id timed out after ${TIMEOUT_SECONDS}s"
            else
                log "Cycle $cycle_id exited with code $exit_code"
            fi
        }
        log "Cycle $cycle_id finished"
    fi
}

# ── Main ───────────────────────────────────────────────────────────────
main() {
    log "=== run_cycle.sh started (force=$FORCE, dry_run=$DRY_RUN) ==="

    # Check PID lock
    if ! check_pid_lock; then
        exit 0
    fi

    # Check signal (unless --force)
    if [ "$FORCE" = false ]; then
        if ! check_signal; then
            log "Exiting -- no work needed"
            exit 0
        fi
    else
        log "Force mode -- skipping signal check"
    fi

    # Dry run stops here
    if [ "$DRY_RUN" = true ]; then
        log "Dry run -- would launch cycle, exiting instead"
        exit 0
    fi

    # Acquire PID lock and launch
    acquire_lock
    launch_cycle

    log "=== run_cycle.sh complete ==="
}

main
