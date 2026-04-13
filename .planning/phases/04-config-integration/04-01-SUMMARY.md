---
phase: 04-config-integration
plan: 01
subsystem: config
tags: [config, bankroll, percentage-sizing, openai-removal, env-cleanup]
dependency_graph:
  requires: []
  provides: [percentage-config, bankroll-loading, clean-dependencies]
  affects: [portfolio-risk-checks, position-sizing, strategy-sizing]
tech_stack:
  added: []
  patterns: [bankroll-json, percentage-based-sizing, tdd]
key_files:
  created:
    - polymarket-trader/state/bankroll.json
  modified:
    - polymarket-trader/lib/config.py
    - polymarket-trader/tests/test_config.py
    - polymarket-trader/requirements.txt
    - polymarket-trader/.env.example
    - polymarket-trader/setup_wallet.py
    - polymarket-trader/CLAUDE.md
decisions:
  - "D-BANKROLL: load_bankroll() placed in config.py per plan decision D-03, returns safe $10k default on missing/corrupt file"
  - "D-CLEAN: Removed all OpenAI/anthropic references from requirements, env files, setup_wallet.py, and CLAUDE.md per D-01/D-02"
  - "D-PREEXIST: test_strategy_starts_blank failure is pre-existing (Phase 1 commit f3d55bb), not caused by config changes"
metrics:
  duration: 269s
  completed: "2026-04-04T09:31:39Z"
  tasks: 2
  files: 8
---

# Phase 04 Plan 01: Config Overhaul and OpenAI Removal Summary

Percentage-based position sizing with bankroll.json runtime source, widened trading parameters (14d resolution, 4pp edge), full OpenAI/anthropic dependency removal -- clean break where Claude IS the AI runtime.

## What Was Built

### Config Overhaul (lib/config.py)
- Replaced `max_position_size_usdc` (50.0) and `max_total_exposure_usdc` (200.0) with `max_position_pct` (0.05) and `max_exposure_pct` (0.30)
- Added `max_resolution_days: int = 14` field
- Changed `min_edge_threshold` default from 0.10 to 0.04
- Updated `_ENV_MAP` to match new percentage-based env var names
- Added `load_bankroll()` function reading `state/bankroll.json` with safe $10k default

### Bankroll Seed (state/bankroll.json)
- Created with `{"balance_usdc": 10000, "updated": "2026-04-04T00:00:00Z"}`
- Runtime source for position sizing calculations

### Dependency Cleanup
- Removed `anthropic>=0.49.0` from requirements.txt
- No `openai` package was present (already absent from imports)

### Environment Files
- .env.example rewritten: OPENAI_API_KEY removed, ALPHA_VANTAGE_API_KEY added, percentage-based risk params
- .env created with matching config (gitignored, not committed)

### Documentation Cleanup
- setup_wallet.py: Changed "Set OPENAI_API_KEY" to "Set ALPHA_VANTAGE_API_KEY"
- CLAUDE.md: Removed all OpenAI SDK, GPT-4o, anthropic references; updated analysis layer description to "Claude (via Claude Code CLI)"

## Test Results

11 config tests pass covering:
- Percentage field defaults (0.05 position, 0.30 exposure, 14 days, 0.04 edge)
- Removal of dollar-based fields
- load_bankroll() with valid file, missing file, corrupted JSON
- _ENV_MAP has percentage keys, not dollar keys
- Env override and CLI override precedence

240/241 total tests pass (1 pre-existing failure in test_strategy_evolution.py unrelated to changes).

## Deviations from Plan

### Out-of-Scope Discovery (Deferred)

**1. Portfolio/tools still reference dollar-based parameters**
- `lib/portfolio.py`, `tools/get_portfolio.py`, `tools/calculate_kelly.py` use `max_position_size_usdc` and `max_total_exposure_usdc` as function parameters (not Config fields)
- These are function-local parameter names, not broken by Config field removal
- Will need updating when portfolio code is wired to percentage-based config

## Known Stubs

None -- all functionality is complete and wired.

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 3aab4d6 | test | Add failing tests for percentage-based config and bankroll loading |
| 97ce3e8 | feat | Percentage-based config with bankroll loading |
| 04162d7 | chore | Remove OpenAI/Anthropic deps, clean all references |

## Self-Check: PASSED

All 8 files verified present. All 3 commits verified in git log.
