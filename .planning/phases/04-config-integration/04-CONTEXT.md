# Phase 4: Config & Integration - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove all OpenAI dependency from the codebase, widen trading parameters for Claude's broader capability (resolution window, edge threshold, percentage-based sizing), create `state/bankroll.json` as the runtime bankroll source, and build `scripts/run_cycle.sh` — the heartbeat-gated cycle launcher with PID locking and timeout.

</domain>

<decisions>
## Implementation Decisions

### OpenAI Removal
- **D-01:** Full purge — remove OPENAI_API_KEY from `.env`, `.env.example`, `setup_wallet.py` hint, and all doc/CLAUDE.md references. Clean break: Claude IS the AI runtime.
- **D-02:** Remove both `openai` and `anthropic` Python packages from `requirements.txt`. Neither is needed — Claude Code runs as the AI runtime via CLI, not via Python SDK calls.

### Bankroll & Sizing Model
- **D-03:** `config.py` reads bankroll from `state/bankroll.json` via a `load_bankroll()` function. Config keeps percentage fields (`max_position_pct=0.05`, `max_exposure_pct=0.30`). Dollar limits are computed at runtime: `bankroll * pct`. Old dollar fields (`max_position_size_usdc`, `max_total_exposure_usdc`) removed entirely.
- **D-04:** `state/bankroll.json` uses simple schema: `{"balance_usdc": 10000, "updated": "ISO-timestamp"}`. Claude updates after each resolved trade. Default $10,000 if file missing (per core-principles.md).

### run_cycle.sh Design
- **D-05:** Invoke Claude with simple prompt: `claude -p "Run trading cycle. Read signal.json for what's needed." --dangerously-skip-permissions`. Claude reads CLAUDE.md automatically, sees signal flags, runs appropriate phases.
- **D-06:** Script reads `state/signal.json` — exits immediately if all flags are false; launches Claude when any flag is true.
- **D-07:** PID lock file at `state/cycle.pid`. Script checks if PID is still running, removes stale locks.
- **D-08:** 20-minute timeout: kill the Claude process, write a timeout entry to `trading.log`, remove PID lock. Next heartbeat triggers a fresh cycle. No partial report writing.
- **D-09:** tmux session management — run Claude inside a named tmux session for log capture and detached operation.

### Config Migration
- **D-10:** Clean replace — remove `max_position_size_usdc` and `max_total_exposure_usdc` from Config dataclass, `_ENV_MAP`, and `.env.example`. Replace with `max_position_pct=0.05` and `max_exposure_pct=0.30`. Breaking change is acceptable (not in production).
- **D-11:** Add `max_resolution_days=14` to Config dataclass and `.env.example`. Code that currently hardcodes the resolution window is NOT wired up in this phase — just made configurable.
- **D-12:** `MIN_EDGE_THRESHOLD` changed from 0.10 to 0.04 in `.env.example` and Config default.
- **D-13:** Add `ALPHA_VANTAGE_API_KEY` to `.env.example` (already used by Phase 3's market_intel.py).

### Claude's Discretion
- Exact structure of `load_bankroll()` function — whether it lives in `config.py` or a separate `lib/bankroll.py`
- tmux session naming convention in `run_cycle.sh`
- Whether to add config validation (e.g., percentage fields must be 0-1) or keep it simple
- Exact cleanup scope for OpenAI references in planning/doc files outside polymarket-trader/

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Config & Environment
- `polymarket-trader/lib/config.py` — Current Config dataclass with dollar-based fields to replace
- `polymarket-trader/.env.example` — Template with OPENAI_API_KEY to remove, new fields to add
- `polymarket-trader/.env` — Live env file with OPENAI_API_KEY to remove

### Safety & Sizing
- `polymarket-trader/state/core-principles.md` — Already references bankroll.json, percentage-based sizing, category-specific limits
- `polymarket-trader/.claude/skills/size-position.md` — Skill doc that uses config values for position sizing

### Heartbeat Integration
- `polymarket-trader/scripts/heartbeat.py` — Writes signal.json; run_cycle.sh reads it
- `polymarket-trader/state/signal.json` — Runtime signal file (gitignored)

### CLAUDE.md
- `polymarket-trader/.claude/CLAUDE.md` — References OpenAI in cross-cutting concerns; needs cleanup
- `polymarket-trader/CLAUDE.md` — Root CLAUDE.md with OpenAI SDK references

### Dependencies
- `polymarket-trader/requirements.txt` — Contains openai and anthropic packages to remove

### Requirements
- `.planning/REQUIREMENTS.md` — CONF-01 through CONF-04, SCHED-04

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lib/config.py` Config dataclass with `_ENV_MAP` and `_parse_value()` — extend pattern for new fields
- `scripts/heartbeat.py` writes `state/signal.json` — run_cycle.sh reads same file
- `state/core-principles.md` already defines bankroll.json contract ($10k default, percentage sizing)

### Established Patterns
- Config: env vars → `_ENV_MAP` → `_parse_value()` → Config fields. New fields follow same pattern.
- CLI tools: argparse + JSON stdout + `--pretty` flag
- State files: JSON in `state/` directory, gitignored when runtime-only
- Error handling: return safe defaults, log errors, continue

### Integration Points
- `state/bankroll.json` — new file, read by config/sizing code, updated by Claude after resolutions
- `state/cycle.pid` — new file, written/checked by run_cycle.sh
- `scripts/run_cycle.sh` — new script, reads signal.json, launches Claude, manages tmux/timeout
- `lib/config.py` — modified with new percentage fields, bankroll loading, removed dollar fields
- `requirements.txt` — openai and anthropic packages removed
- `.env` / `.env.example` — OPENAI_API_KEY removed, ALPHA_VANTAGE_API_KEY and new fields added

</code_context>

<specifics>
## Specific Ideas

- run_cycle.sh invocation: `claude -p "Run trading cycle. Read signal.json for what's needed." --dangerously-skip-permissions`
- bankroll.json minimal: `{"balance_usdc": 10000, "updated": "2026-04-04T00:00:00Z"}`
- Only one Python reference to OpenAI remains (setup_wallet.py:154 print hint) — easy cleanup
- The `openai` package has no import statements anywhere in polymarket-trader/ Python code

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-config-integration*
*Context gathered: 2026-04-04*
