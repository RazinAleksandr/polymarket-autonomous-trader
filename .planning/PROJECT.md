# Autonomous Polymarket Trading Agent

## What This Is

A self-modifying autonomous trading agent for Polymarket prediction markets, where Claude Code IS the trader. Built on top of the working `polymarket-agent/` codebase (11 CLI tools, Gamma + CLOB API integration, SQLite database, 167 passing tests), this system copies that foundation into a new `polymarket-trader/` directory and restructures it so Claude operates as a single autonomous agent — reading its own strategy files, making all trading decisions through reasoning, and rewriting its own rules and playbooks based on outcomes. Python tools are hands (fetch data, place orders, do math); Claude's reasoning is the brain.

## Core Value

Claude autonomously trades Polymarket prediction markets, learns from every outcome, and evolves its own strategy over time — no human picks markets, sizes positions, or edits rules.

## Requirements

### Validated

- [x] Single-agent architecture: skill reference docs created, CLAUDE.md rewritten as autonomous trader — Validated in Phase 1
- [x] Knowledge base transplant: 16 golden rules, 6 category playbooks, calibration seed, strategy lifecycle, edge sources — Validated in Phase 2
- [x] Immutable guardrails: core-principles.md with 7 guardrails (paper-default, 5% max position, 30% max exposure, live gate, no deletion, record-before-confirm, 5-loss pause) — Validated in Phase 2
- [x] Self-modifying strategy: strategy.md reset for autonomous discovery, prior rules archived — Validated in Phase 2
- [x] Calibration tracking: lib/calibration.py with Brier scores, category accuracy, auto-generated corrections; record_outcome.py CLI — Validated in Phase 3
- [x] Market intelligence: lib/market_intel.py with ETF macro regime, Fear & Greed, news sentiment; get_market_intel.py CLI — Validated in Phase 3
- [x] Heartbeat signal: scripts/heartbeat.py reads local state only, writes signal.json with scan/resolve/learn flags — Validated in Phase 3
- [x] Test coverage: 234 tests passing (51 new for calibration, market_intel, heartbeat) — Validated in Phase 3
- [x] Config changes: widen resolution window (14d), lower min edge (4pp), bankroll-% position sizing via load_bankroll() — Validated in Phase 4
- [x] Cycle automation: run_cycle.sh with heartbeat gating, PID locking, tmux sessions, 20-min timeout — Validated in Phase 4
- [x] OpenAI removal: zero openai/anthropic references in code, requirements, env files; ALPHA_VANTAGE_API_KEY replaces OPENAI_API_KEY — Validated in Phase 4
- [x] Test coverage: 261 tests passing (32 new for config and run_cycle) — Validated in Phase 4
- [x] Autonomous cycle validation: CLAUDE.md Phase B/E tuned, validate_cycle.py built, 5 real cycles executed via Claude CLI, strategy evolved with 3 rules, first trade placed — Validated in Phase 5
- [x] Test coverage: 278 tests passing (17 new for validate_cycle and strategy evolution) — Validated in Phase 5

### Active

- [ ] Heartbeat + cron scheduling: 10-min heartbeat, 30-min gated cycles, daily forced full scan
- [ ] Paper trading validation: 20-50 autonomous cycles proving strategy evolution and positive P&L trend
- [ ] Live trading gate: enable_live.py with criteria (10 cycles, positive P&L, >50% win rate, operator confirmation)

### Out of Scope

- Frontend/dashboard — CLI agent only, no React UI (future milestone)
- Live money deployment — paper trading focus, wallet funding deferred
- Multi-agent architecture — single Claude session by design, no sub-agent spawning
- OpenAI/GPT integration — Claude IS the AI, no Python LLM wrappers
- Vibe-Trading/AI-Trader frontend code — ideas borrowed, code not ported
- Mobile app or web interface — monitored via logs and state files

## Context

**Base project:** `polymarket-agent/` — the only project with working end-to-end code. Has 11 Python CLI tools, Gamma API + CLOB API integration, paper + live order execution via py-clob-client, SQLite database with 5 tables, 167/189 tests passing, category-specific fee calculation, wallet signing for Polygon, cron scheduling via tmux.

**Knowledge source:** `polymarket_claude/` — 14 golden rules (battle-tested, loss-cited), 5 category playbooks, calibration tracking pattern, heartbeat-before-LLM pattern, Bayesian probability estimation framework, strategy lifecycle system.

**Idea sources:** Vibe-Trading (bull/bear adversarial debate structure, context compression), AI-Trader (macro regime detection, ETF flows, news sentiment).

**Key architectural insight:** Sub-agents fragment intelligence. A single Claude session that sees everything — portfolio, strategy, calibration history, market data — makes holistically better decisions than 8 specialized sub-agents passing JSON between each other.

**Working directory:** New `polymarket-trader/` directory (copy of polymarket-agent/ then restructured). Source projects remain untouched as reference.

## Constraints

- **Tech stack**: Python tools only (no LangChain, no OpenAI SDK). Claude Code is the AI runtime.
- **APIs**: Polymarket Gamma API (discovery), CLOB API (execution), Alpha Vantage (market intel), Fear & Greed API (crypto sentiment)
- **Database**: SQLite (existing, working) — immutable audit trail, Claude writes but never deletes
- **Scheduling**: Cron + tmux + heartbeat pattern — zero-cost when idle
- **Safety**: Paper trading default, live gate requires proof of competence, core principles are immutable
- **Dependencies**: Minimal — py-clob-client, web3, eth-account, requests, python-dotenv. No AI libraries.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Single agent, no sub-agents | Sub-agents fragment intelligence; one session sees everything and reasons holistically | — Pending |
| Skills (reference docs) instead of agents | Claude loads frameworks on demand vs rigid pipeline; preserves full reasoning chain | — Pending |
| Copy to polymarket-trader/ | Clean start without breaking working polymarket-agent/ reference | — Pending |
| Paper only for v1 | Prove the autonomous loop works before risking real money | — Pending |
| Claude modifies its own CLAUDE.md | Enables true self-improvement — Claude can fix its own process | — Pending |
| No frontend | CLI agent monitored via logs/state files; dashboard is future milestone | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-05 — Phase 5 (Autonomous Cycle Validation) complete: CLAUDE.md Phase B/E tuned, validate_cycle.py built, 5 real autonomous cycles executed, strategy evolved with 3 rules, first trade placed, 278 tests passing*
