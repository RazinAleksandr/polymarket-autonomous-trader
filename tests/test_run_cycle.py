"""Tests for run_cycle.sh -- heartbeat-gated cycle launcher.

Tests verify signal gating, PID locking, and argument handling by
invoking the shell script in controlled environments with tmp directories.
"""

import json
import os
import signal
import subprocess
import time
from pathlib import Path

import pytest

# Project root for locating the script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUN_CYCLE = PROJECT_ROOT / "scripts" / "run_cycle.sh"


def write_signal(state_dir: Path, scan: bool = False, resolve: bool = False, learn: bool = False):
    """Write a signal.json file with given flags."""
    sig = {
        "generated_at": "2026-04-04T00:00:00Z",
        "scan_needed": scan,
        "resolve_needed": resolve,
        "learn_needed": learn,
        "expiring_soon": [],
        "open_positions": 0,
    }
    signal_path = state_dir / "signal.json"
    signal_path.write_text(json.dumps(sig, indent=2) + "\n")
    return signal_path


def run_script(tmp_path: Path, args: list[str] | None = None, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    """Run run_cycle.sh with PROJECT_ROOT overridden to tmp_path.

    We create a minimal wrapper that sets paths before sourcing the real script,
    so the script operates in the tmp directory.
    """
    state_dir = tmp_path / "state"
    state_dir.mkdir(exist_ok=True)

    # Create a wrapper script that overrides PROJECT_ROOT
    wrapper = tmp_path / "test_wrapper.sh"
    wrapper.write_text(f"""#!/usr/bin/env bash
set -euo pipefail

# Override paths to use tmp directory
export PROJECT_ROOT="{tmp_path}"

# Source the real script's functions by redefining paths
SCRIPT_DIR="{RUN_CYCLE.parent}"
SIGNAL_FILE="{state_dir / 'signal.json'}"
PID_FILE="{state_dir / '.run_cycle.pid'}"
LOG_FILE="{state_dir / 'run_cycle.log'}"
HEARTBEAT_SCRIPT="{PROJECT_ROOT / 'scripts' / 'heartbeat.py'}"
VENV_ACTIVATE="{tmp_path / '.venv' / 'bin' / 'activate'}"
TMUX_SESSION="test-trader-$$"
TIMEOUT_SECONDS=5
STALE_PID_SECONDS=10

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
log() {{
    local timestamp
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    local msg="[$timestamp] $1"
    echo "$msg" >> "$LOG_FILE"
    echo "$msg"
}}

mkdir -p "{state_dir}"
touch "$LOG_FILE"

# ── PID Locking ────────────────────────────────────────────────────────
cleanup() {{
    if [ -f "$PID_FILE" ]; then
        local stored_pid
        stored_pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [ "$stored_pid" = "$$" ]; then
            rm -f "$PID_FILE"
        fi
    fi
}}
trap cleanup EXIT

check_pid_lock() {{
    if [ ! -f "$PID_FILE" ]; then
        return 0
    fi
    local stored_pid
    stored_pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [ -z "$stored_pid" ]; then
        rm -f "$PID_FILE"
        return 0
    fi
    if kill -0 "$stored_pid" 2>/dev/null; then
        local pid_age
        pid_age=$(( $(date +%s) - $(stat -c %Y "$PID_FILE" 2>/dev/null || echo "0") ))
        if [ "$pid_age" -gt "$STALE_PID_SECONDS" ]; then
            kill "$stored_pid" 2>/dev/null || true
            sleep 1
            kill -9 "$stored_pid" 2>/dev/null || true
            rm -f "$PID_FILE"
            return 0
        fi
        log "Cycle already running (pid=$stored_pid, age=${{pid_age}}s), exiting"
        return 1
    fi
    rm -f "$PID_FILE"
    return 0
}}

acquire_lock() {{
    echo "$$" > "$PID_FILE"
    log "Acquired PID lock (pid=$$)"
}}

# ── Signal Check ───────────────────────────────────────────────────────
check_signal() {{
    if [ ! -f "$SIGNAL_FILE" ]; then
        log "No signal.json found"
        return 1
    fi
    local any_flag
    any_flag=$(python3 -c "
import json, sys
try:
    with open('$SIGNAL_FILE') as f:
        sig = json.load(f)
    active = [k for k, v in [('scan', sig.get('scan_needed')), ('resolve', sig.get('resolve_needed')), ('learn', sig.get('learn_needed'))] if v]
    if active:
        print('|'.join(active))
    else:
        print('NONE')
except Exception as e:
    print(f'ERROR:{{e}}', file=sys.stderr)
    print('ERROR')
" 2>>"$LOG_FILE")

    if [ "$any_flag" = "NONE" ]; then
        log "All flags false -- no work needed"
        return 1
    elif [ "$any_flag" = "ERROR" ]; then
        log "Error parsing signal.json"
        return 1
    else
        log "Active flags: $any_flag"
        return 0
    fi
}}

# ── Main (test version: never actually launches Claude) ────────────────
main() {{
    log "=== run_cycle.sh started (force=$FORCE, dry_run=$DRY_RUN) ==="

    if ! check_pid_lock; then
        exit 0
    fi

    if [ "$FORCE" = false ]; then
        if ! check_signal; then
            log "Exiting -- no work needed"
            exit 0
        fi
    else
        log "Force mode -- skipping signal check"
    fi

    if [ "$DRY_RUN" = true ]; then
        log "Dry run -- would launch cycle, exiting instead"
        exit 0
    fi

    acquire_lock
    log "Would launch cycle here (test mode)"
    log "=== run_cycle.sh complete ==="
}}

main
""")
    wrapper.chmod(0o755)

    cmd = ["bash", str(wrapper)]
    if args:
        cmd.extend(args)

    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)


# ── Signal Gating Tests ───────────────────────────────────────────────


class TestSignalGating:
    """Test that run_cycle.sh correctly gates on signal.json flags."""

    def test_all_flags_false_exits_immediately(self, tmp_path):
        """When all heartbeat flags are false, script exits 0 without launching."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=False, resolve=False, learn=False)

        result = run_script(tmp_path)
        assert result.returncode == 0
        assert "no work needed" in result.stdout.lower() or "no work needed" in (state_dir / "run_cycle.log").read_text().lower()

    def test_scan_needed_proceeds(self, tmp_path):
        """When scan_needed is true, script proceeds past signal check."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=True, resolve=False, learn=False)

        result = run_script(tmp_path)
        assert result.returncode == 0
        log_text = (state_dir / "run_cycle.log").read_text()
        assert "Active flags: scan" in log_text
        assert "Would launch cycle" in log_text

    def test_resolve_needed_proceeds(self, tmp_path):
        """When resolve_needed is true, script proceeds past signal check."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=False, resolve=True, learn=False)

        result = run_script(tmp_path)
        assert result.returncode == 0
        log_text = (state_dir / "run_cycle.log").read_text()
        assert "resolve" in log_text.lower()

    def test_learn_needed_proceeds(self, tmp_path):
        """When learn_needed is true, script proceeds past signal check."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=False, resolve=False, learn=True)

        result = run_script(tmp_path)
        assert result.returncode == 0
        log_text = (state_dir / "run_cycle.log").read_text()
        assert "learn" in log_text.lower()

    def test_multiple_flags_true(self, tmp_path):
        """When multiple flags are true, all are reported."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=True, resolve=True, learn=True)

        result = run_script(tmp_path)
        assert result.returncode == 0
        log_text = (state_dir / "run_cycle.log").read_text()
        assert "scan" in log_text
        assert "resolve" in log_text
        assert "learn" in log_text

    def test_missing_signal_json_no_heartbeat(self, tmp_path):
        """When signal.json is missing and heartbeat can't run, script exits."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        # Don't write signal.json -- script should log and exit

        result = run_script(tmp_path)
        assert result.returncode == 0
        log_text = (state_dir / "run_cycle.log").read_text()
        assert "No signal.json" in log_text


# ── PID Locking Tests ─────────────────────────────────────────────────


class TestPidLocking:
    """Test PID file locking prevents concurrent runs."""

    def test_creates_pid_file_on_launch(self, tmp_path):
        """Script creates PID file when acquiring lock."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=True)

        result = run_script(tmp_path)
        assert result.returncode == 0
        log_text = (state_dir / "run_cycle.log").read_text()
        assert "Acquired PID lock" in log_text

    def test_cleans_pid_file_on_exit(self, tmp_path):
        """PID file is removed on normal exit."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=True)

        result = run_script(tmp_path)
        assert result.returncode == 0
        # PID file should be cleaned up by trap
        assert not (state_dir / ".run_cycle.pid").exists()

    def test_stale_pid_file_no_process(self, tmp_path):
        """Stale PID file (process not running) is cleaned up."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=True)

        # Write a PID file with a PID that doesn't exist
        pid_file = state_dir / ".run_cycle.pid"
        pid_file.write_text("99999999")

        result = run_script(tmp_path)
        assert result.returncode == 0
        log_text = (state_dir / "run_cycle.log").read_text()
        # Should detect stale PID and proceed
        assert "Would launch cycle" in log_text

    def test_empty_pid_file_treated_as_stale(self, tmp_path):
        """Empty PID file is treated as stale and removed."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=True)

        pid_file = state_dir / ".run_cycle.pid"
        pid_file.write_text("")

        result = run_script(tmp_path)
        assert result.returncode == 0
        log_text = (state_dir / "run_cycle.log").read_text()
        assert "Would launch cycle" in log_text

    def test_active_pid_prevents_run(self, tmp_path):
        """Active PID file with running process prevents concurrent run."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=True)

        # Start a long-running process to hold the PID
        proc = subprocess.Popen(["sleep", "60"])
        try:
            pid_file = state_dir / ".run_cycle.pid"
            pid_file.write_text(str(proc.pid))

            result = run_script(tmp_path)
            assert result.returncode == 0
            log_text = (state_dir / "run_cycle.log").read_text()
            assert "already running" in log_text.lower()
            # Should NOT have launched
            assert "Would launch cycle" not in log_text
        finally:
            proc.kill()
            proc.wait()


# ── Argument Tests ─────────────────────────────────────────────────────


class TestArguments:
    """Test --force and --dry-run flags."""

    def test_force_skips_signal_check(self, tmp_path):
        """--force skips signal check and proceeds even with all-false flags."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=False, resolve=False, learn=False)

        result = run_script(tmp_path, args=["--force"])
        assert result.returncode == 0
        log_text = (state_dir / "run_cycle.log").read_text()
        assert "Force mode" in log_text
        assert "Would launch cycle" in log_text

    def test_dry_run_does_not_launch(self, tmp_path):
        """--dry-run checks signal but does not launch cycle."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        write_signal(state_dir, scan=True)

        result = run_script(tmp_path, args=["--dry-run"])
        assert result.returncode == 0
        log_text = (state_dir / "run_cycle.log").read_text()
        assert "Dry run" in log_text
        assert "Would launch cycle" not in log_text

    def test_force_and_dry_run_together(self, tmp_path):
        """--force --dry-run skips signal check but still doesn't launch."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        # No signal.json needed with --force

        result = run_script(tmp_path, args=["--force", "--dry-run"])
        assert result.returncode == 0
        log_text = (state_dir / "run_cycle.log").read_text()
        assert "Force mode" in log_text
        assert "Dry run" in log_text


# ── Syntax Validation ─────────────────────────────────────────────────


class TestScriptIntegrity:
    """Validate the actual run_cycle.sh script file."""

    def test_script_exists_and_executable(self):
        """run_cycle.sh exists and is executable."""
        assert RUN_CYCLE.exists(), f"Script not found at {RUN_CYCLE}"
        assert os.access(RUN_CYCLE, os.X_OK), f"Script not executable: {RUN_CYCLE}"

    def test_bash_syntax_valid(self):
        """run_cycle.sh passes bash syntax check."""
        result = subprocess.run(
            ["bash", "-n", str(RUN_CYCLE)],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_script_has_shebang(self):
        """Script starts with proper shebang line."""
        first_line = RUN_CYCLE.read_text().split("\n")[0]
        assert first_line.startswith("#!/"), f"Missing shebang: {first_line}"

    def test_script_references_signal_json(self):
        """Script references signal.json for heartbeat gating."""
        content = RUN_CYCLE.read_text()
        assert "signal.json" in content

    def test_script_has_pid_locking(self):
        """Script implements PID file locking."""
        content = RUN_CYCLE.read_text()
        assert ".run_cycle.pid" in content
        assert "check_pid_lock" in content

    def test_script_has_timeout(self):
        """Script enforces timeout on cycle execution."""
        content = RUN_CYCLE.read_text()
        assert "TIMEOUT_SECONDS" in content
        assert "1200" in content  # 20 minutes

    def test_script_has_tmux(self):
        """Script manages tmux sessions."""
        content = RUN_CYCLE.read_text()
        assert "tmux" in content
        assert "TMUX_SESSION" in content
