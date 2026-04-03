#!/usr/bin/env bash
set -euo pipefail

# Run a single trading cycle inside a tmux session.
# Cron calls this script. If a cycle is already running, it skips.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCKFILE="/tmp/polymarket-cycle.pid"
if [ -f "$SCRIPT_DIR/.trading-logfile" ]; then
    LOGFILE=$(cat "$SCRIPT_DIR/.trading-logfile")
else
    LOGFILE="$SCRIPT_DIR/logs/manual-$(date +%Y%m%d-%H%M%S).log"
fi
SESSION_NAME="trading-$(date +%H%M%S)"
STOP_FILE="$SCRIPT_DIR/.trading-stop-at"
CRON_MARKER="# polymarket-trading-agent"

mkdir -p "$SCRIPT_DIR/logs"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $1" >> "$LOGFILE"; }

# Auto-stop: if past the scheduled end time, remove cron and exit
if [ -f "$STOP_FILE" ]; then
    STOP_EPOCH=$(cat "$STOP_FILE")
    if [ "$(date +%s)" -gt "$STOP_EPOCH" ]; then
        log "STOP: Trading duration expired, removing cron job"
        crontab -l 2>/dev/null | grep -v "$CRON_MARKER" | crontab - 2>/dev/null || true
        rm -f "$STOP_FILE"
        exit 0
    fi
fi

# Skip if a previous cycle is still running
if [ -f "$LOCKFILE" ]; then
    OLD_PID=$(cat "$LOCKFILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        log "SKIP: Previous cycle still running (PID $OLD_PID)"
        exit 0
    else
        log "WARN: Stale lockfile removed (PID $OLD_PID)"
        rm -f "$LOCKFILE"
    fi
fi

echo $$ > "$LOCKFILE"
trap 'rm -f "$LOCKFILE"' EXIT

# Pre-flight: verify claude is available
if ! command -v claude &>/dev/null; then
    log "FATAL: claude not found in PATH"
    exit 1
fi

log "START: session=$SESSION_NAME"

CLAUDE_LOG="$SCRIPT_DIR/logs/claude-${SESSION_NAME}.log"

# Write runner script. Claude must run from the project directory
# so it discovers CLAUDE.md and .claude/ agents.
# env -i prevents inherited sudo/root context from blocking --dangerously-skip-permissions.
# Python tools load API keys from .env via dotenv at runtime.
RUNNER="/tmp/polymarket-cycle-runner-$$.sh"
cat > "$RUNNER" <<EOF
#!/usr/bin/env bash
cd "$SCRIPT_DIR"
echo "\$(date -u +%Y-%m-%dT%H:%M:%SZ) Claude starting..." >> "$CLAUDE_LOG"
if env -i HOME="$HOME" PATH="$PATH" LANG="${LANG:-en_US.UTF-8}" SHELL="${SHELL:-/bin/bash}" USER="${USER:-$(whoami)}" TERM="${TERM:-xterm-256color}" \
  claude --dangerously-skip-permissions -p 'run a trading cycle' --verbose 2>&1 | tee -a "$CLAUDE_LOG"; then
    echo "\$(date -u +%Y-%m-%dT%H:%M:%SZ) Claude exited successfully" >> "$CLAUDE_LOG"
else
    echo "\$(date -u +%Y-%m-%dT%H:%M:%SZ) Claude exited with code: \$?" >> "$CLAUDE_LOG"
fi
rm -f "$RUNNER"
EOF
chmod +x "$RUNNER"

tmux new-session -d -s "$SESSION_NAME" "$RUNNER"

# Wait for tmux session to finish
while tmux has-session -t "$SESSION_NAME" 2>/dev/null; do
    sleep 30
done

if [ -f "$CLAUDE_LOG" ]; then
    line_count=$(wc -l < "$CLAUDE_LOG")
    log "END: session=$SESSION_NAME (claude log: $line_count lines)"
    if [ "$line_count" -le 2 ]; then
        log "WARN: Claude produced minimal output — likely failed to start. Check $CLAUDE_LOG"
    fi
else
    log "END: session=$SESSION_NAME (WARNING: no claude log produced)"
fi
