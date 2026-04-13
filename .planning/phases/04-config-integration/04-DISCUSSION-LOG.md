# Phase 4: Config & Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 04-config-integration
**Areas discussed:** OpenAI removal scope, Bankroll & sizing model, run_cycle.sh design, Config migration

---

## OpenAI Removal Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Full purge | Remove OPENAI_API_KEY from .env, .env.example, setup_wallet.py hint, and any doc/CLAUDE.md references. Clean break. | ✓ |
| Code only | Remove from .env and .env.example, fix setup_wallet.py. Leave doc references as historical context. | |
| You decide | Claude's discretion on what to clean vs leave | |

**User's choice:** Full purge
**Notes:** Only one Python reference to OpenAI exists (setup_wallet.py:154 print hint). No market_analyzer.py in codebase.

### Follow-up: AI SDK Packages

| Option | Description | Selected |
|--------|-------------|----------|
| Remove both | Neither openai nor anthropic Python packages needed — Claude Code is the AI runtime via CLI | ✓ |
| Remove openai only | Keep anthropic in case of future Python SDK use | |
| Keep both | Leave requirements.txt alone | |

**User's choice:** Remove both
**Notes:** Claude Code runs as CLI runtime, no Python AI SDK calls needed.

---

## Bankroll & Sizing Model

| Option | Description | Selected |
|--------|-------------|----------|
| Config reads bankroll.json | Add load_bankroll(). Config keeps percentage fields. Dollar limits computed at runtime. Old dollar fields removed. | ✓ |
| Bankroll in .env | BANKROLL_USDC=10000 in .env. Simpler but less dynamic. | |
| Keep both systems | Percentage fields alongside old dollar fields. | |

**User's choice:** Config reads bankroll.json
**Notes:** core-principles.md already references state/bankroll.json with $10k default.

### Follow-up: bankroll.json Schema

| Option | Description | Selected |
|--------|-------------|----------|
| Simple balance | {"balance_usdc": 10000, "updated": "ISO-timestamp"} — Claude updates after resolved trades | ✓ |
| With history | Includes initial, high_water, and history array | |
| You decide | Claude's discretion on schema | |

**User's choice:** Simple balance
**Notes:** None

---

## run_cycle.sh Design

### Claude Invocation

| Option | Description | Selected |
|--------|-------------|----------|
| claude with prompt | claude -p "Run trading cycle..." --dangerously-skip-permissions. Claude reads CLAUDE.md and signal flags. | ✓ |
| claude with specific phases | Script parses signal.json and passes specific phase instructions. More targeted. | |
| claude with task file | Script writes temp task file with instructions based on signals. Most control. | |

**User's choice:** claude with prompt
**Notes:** Simple approach — Claude reads signal.json itself and decides what phases to run.

### PID Lock Location

| Option | Description | Selected |
|--------|-------------|----------|
| state/cycle.pid | Alongside other runtime state. Checks if PID still running. | ✓ |
| /tmp/polymarket-cycle.pid | Standard Unix temp location. Auto-cleaned on reboot. | |
| You decide | Claude's discretion | |

**User's choice:** state/cycle.pid
**Notes:** None

### Timeout Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Kill and log | Kill Claude process, write timeout to trading.log, remove PID lock. Next heartbeat triggers fresh cycle. | ✓ |
| Kill and write report | Kill process, then run quick Claude session for partial report. | |
| You decide | Claude's discretion | |

**User's choice:** Kill and log
**Notes:** Simple and safe approach.

---

## Config Migration

### Dollar to Percentage Transition

| Option | Description | Selected |
|--------|-------------|----------|
| Clean replace | Remove dollar fields entirely. Replace with percentage fields. Breaking change acceptable. | ✓ |
| Deprecation period | Keep old fields with warnings, add new. Remove in Phase 6. | |
| You decide | Claude's discretion | |

**User's choice:** Clean replace
**Notes:** Not in production yet, breaking change is fine.

### MAX_RESOLUTION_DAYS Integration

| Option | Description | Selected |
|--------|-------------|----------|
| Add to config only | Add field to Config dataclass and .env.example. Don't wire up existing code. | ✓ |
| Add and wire up | Add to config AND update all code that hardcodes resolution window. | |
| You decide | Claude's discretion | |

**User's choice:** Add to config only
**Notes:** Just make it configurable; wiring up can happen when code needs it.

---

## Claude's Discretion

- load_bankroll() function location (config.py vs separate lib/bankroll.py)
- tmux session naming convention
- Config validation for percentage fields
- Cleanup scope for OpenAI references in planning/doc files

## Deferred Ideas

None — discussion stayed within phase scope
