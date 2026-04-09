#!/usr/bin/env bash
# install_cron.sh -- Idempotent cron setup for polymarket-trader
#
# Installs 3 crontab entries:
#   1. Heartbeat every 10 minutes (zero LLM cost)
#   2. Gated cycle every 30 minutes (run_cycle.sh checks signal.json)
#   3. Daily forced full scan at 2 AM UTC (bypasses heartbeat gating)
#
# Features:
#   - Idempotent: running twice produces the same result
#   - Auto-removes old polymarket-agent cron entries
#   - --remove flag strips all polymarket-trader entries
#   - Marker comments for reliable identification
#
# Usage:
#   ./scripts/install_cron.sh           # Install all 3 entries
#   ./scripts/install_cron.sh --remove  # Remove all entries
#   ./scripts/install_cron.sh --show    # Show current polymarket entries
#
# Decisions: D-01, D-02, D-03, D-04

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Marker comments for identifying our entries
MARKER="# polymarket-trader"
OLD_MARKER="polymarket-agent"

# Scripts
HEARTBEAT_SCRIPT="$PROJECT_ROOT/scripts/heartbeat.py"
RUN_CYCLE_SCRIPT="$PROJECT_ROOT/scripts/run_cycle.sh"
VENV_ACTIVATE="$PROJECT_ROOT/.venv/bin/activate"

# ── Helpers ───────────────────────────────────────────────────────────

get_current_crontab() {
    crontab -l 2>/dev/null || echo ""
}

remove_our_entries() {
    # Remove lines containing our marker
    local current="$1"
    echo "$current" | grep -v "$MARKER" || true
}

remove_old_agent_entries() {
    # Remove old polymarket-agent entries (D-02)
    local current="$1"
    echo "$current" | grep -v "$OLD_MARKER" || true
}

show_our_entries() {
    local current
    current=$(get_current_crontab)
    local entries
    entries=$(echo "$current" | grep "$MARKER" || true)
    if [ -z "$entries" ]; then
        echo "No polymarket-trader cron entries found."
    else
        echo "Current polymarket-trader cron entries:"
        echo "$entries"
    fi
}

# ── Build Python command with venv ────────────────────────────────────

python_cmd() {
    if [ -f "$VENV_ACTIVATE" ]; then
        echo "cd $PROJECT_ROOT && source $VENV_ACTIVATE && python"
    else
        echo "cd $PROJECT_ROOT && python"
    fi
}

# ── Main ──────────────────────────────────────────────────────────────

main() {
    local action="install"

    for arg in "$@"; do
        case "$arg" in
            --remove) action="remove" ;;
            --show)   action="show" ;;
            *)        echo "Unknown argument: $arg" >&2; exit 1 ;;
        esac
    done

    # Handle --show
    if [ "$action" = "show" ]; then
        show_our_entries
        return
    fi

    local current
    current=$(get_current_crontab)

    # Always clean up: remove our entries and old agent entries
    local cleaned
    cleaned=$(remove_our_entries "$current")
    cleaned=$(remove_old_agent_entries "$cleaned")

    # Handle --remove (D-03)
    if [ "$action" = "remove" ]; then
        if [ -z "$(echo "$cleaned" | tr -d '[:space:]')" ]; then
            # Crontab would be empty
            crontab -r 2>/dev/null || true
        else
            echo "$cleaned" | crontab -
        fi
        echo "Polymarket-trader cron entries removed."
        # Check if old entries were also removed
        if echo "$current" | grep -q "$OLD_MARKER"; then
            echo "Also removed old polymarket-agent entries."
        fi
        return
    fi

    # Install mode
    local py_prefix
    py_prefix=$(python_cmd)

    # Build 3 cron entries
    local entry_heartbeat="*/10 * * * * $py_prefix $HEARTBEAT_SCRIPT >> $PROJECT_ROOT/state/heartbeat.log 2>&1 $MARKER"
    local entry_cycle="*/30 * * * * $RUN_CYCLE_SCRIPT >> $PROJECT_ROOT/state/run_cycle.log 2>&1 $MARKER"
    local entry_daily="0 2 * * * $RUN_CYCLE_SCRIPT --force >> $PROJECT_ROOT/state/run_cycle.log 2>&1 $MARKER"

    # Append our entries to cleaned crontab
    local new_crontab="$cleaned"
    # Remove trailing empty lines for clean output
    new_crontab=$(echo "$new_crontab" | sed '/^$/d')
    if [ -n "$new_crontab" ]; then
        new_crontab="$new_crontab"$'\n'
    fi
    new_crontab="${new_crontab}${entry_heartbeat}"$'\n'
    new_crontab="${new_crontab}${entry_cycle}"$'\n'
    new_crontab="${new_crontab}${entry_daily}"$'\n'

    echo "$new_crontab" | crontab -

    echo "Installed 3 cron entries:"
    echo "  1. Heartbeat every 10 min:  */10 * * * *  heartbeat.py"
    echo "  2. Gated cycle every 30 min: */30 * * * *  run_cycle.sh"
    echo "  3. Daily forced scan at 2 AM: 0 2 * * *   run_cycle.sh --force"

    # Report old entry removal
    if echo "$current" | grep -q "$OLD_MARKER"; then
        echo ""
        echo "Removed old polymarket-agent cron entries."
    fi

    echo ""
    echo "To verify: crontab -l"
    echo "To remove:  ./scripts/install_cron.sh --remove"
}

main "$@"
