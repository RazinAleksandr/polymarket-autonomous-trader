# Autonomous Polymarket Trading Agent

## What This Is

A self-modifying autonomous trading agent for Polymarket prediction markets, where Claude Code IS the trader. Built by cherry-picking the best of three source projects (polymarket-agent for architecture, polymarket_claude for knowledge, AI-Trader for market intelligence) and restructuring into a **single-agent** design: Claude operates as one autonomous trader per cycle — reading its own strategy files, making all trading decisions through reasoning, and rewriting its own rules and playbooks based on outcomes. Python tools are hands (fetch data, place orders, do math); Claude's reasoning is the brain.

## Core Value

Claude autonomously trades Polymarket prediction markets, learns from every outcome, and evolves its own strategy over time — no human picks markets, sizes positions, or edits rules.

## Current State (Live System)

**System is running unattended on cron since 2026-04-05.** Paper trading mode.

- **35+ autonomous cycles** completed
- **7 trades** across 6 markets: 2 wins (+$21, +$131), 1 loss (-$301), 3 open positions
- **Realized P&L:** -$149.06 on $10,000 paper bankroll (dominated by Iran ceasefire loss)
- **Unrealized P&L:** +$21 (Hungary position +$83 after Orban conceded, pending Polymarket resolution)
- **Strategy evolved:** 7 self-learned rules in strategy.md, 17 golden rules in knowledge base
- **Calibration tracked:** Brier 0.270 overall across 4 resolved trades
- **Live trading gate:** Correctly BLOCKED by negative P&L — waiting for positive trend

See `src/docs/real-results.md` for the full trade-by-trade breakdown.

## Requirements

### Validated (v1.0 milestone complete)

- [x] Single-agent architecture: 6 skill reference docs (`src/.claude/skills/`), no sub-agents, 5-phase cycle in CLAUDE.md — Phase 1
- [x] Knowledge base transplant: 17 golden rules, 6 category playbooks, calibration seed — Phase 2
- [x] Immutable guardrails: `src/state/core-principles.md` with 7 guardrails (paper-default, 5% max position, 30% max exposure, live gate, no deletion, record-before-confirm, 5-loss pause) — Phase 2
- [x] Self-modifying strategy: `src/state/strategy.md` reset for autonomous discovery, prior rules archived — Phase 2
- [x] Calibration tracking: `src/lib/calibration.py` with Brier scores, category accuracy, auto-corrections; `tools/record_outcome.py` CLI — Phase 3
- [x] Market intelligence: `src/lib/market_intel.py` with ETF macro regime, Fear & Greed, news sentiment — Phase 3
- [x] Heartbeat signal: `src/scripts/heartbeat.py` reads local state only, writes signal.json with scan/resolve/learn flags — Phase 3
- [x] Config changes: MAX_RESOLUTION_DAYS=14, MIN_EDGE_THRESHOLD=0.04, bankroll-% position sizing — Phase 4
- [x] Cycle automation: `src/scripts/run_cycle.sh` with heartbeat gating, PID locking, tmux, 20-min timeout — Phase 4
- [x] OpenAI removal: zero `import openai` anywhere; ALPHA_VANTAGE_API_KEY replaces OPENAI_API_KEY — Phase 4
- [x] Autonomous cycle validation: 5+ real cycles executed via Claude CLI, strategy evolved autonomously, first trades placed — Phase 5
- [x] Unattended cron operation: heartbeat/10min, cycle/2h, forced daily 2AM — Phase 6
- [x] Live trading gate with calibration health: `tools/enable_live.py --check` verifies paper cycles, positive P&L, >50% win rate, calibration health (no category >-20pp) — Phase 6
- [x] Paper validation: 20+ autonomous cycles completed (actual: 35+) — Phase 6

### Active

No active work. v1.0 milestone complete.

Potential v2.0 ideas (see `.planning/research/`):
- Bull/bear structured debate from TradingAgents (replaces single-agent sequential research in Phase C)
- BM25 memory retrieval for past similar situations
- Structured reflection framework for automated lesson extraction

### Out of Scope

- Frontend/dashboard — CLI agent only, monitored via logs and markdown reports
- Multi-agent architecture — single Claude session by design, intentionally rejected sub-agents
- OpenAI/GPT integration — Claude IS the AI, no Python LLM wrappers
- Vibe-Trading/AI-Trader frontend code — ideas borrowed, code not ported
- Mobile app or web interface — monitored via logs and state files

## Context

**Source projects:**
- `polymarket-agent/` — working end-to-end code foundation (Gamma + CLOB APIs, SQLite, py-clob-client). The base layer.
- `polymarket_claude/` — golden rules, category playbooks, calibration pattern, Bayesian probability framework. The knowledge layer.
- `AI-Trader/` — macro regime detection, ETF flows, news sentiment. The intelligence layer.

**Key architectural insight (validated in production):** Sub-agents fragment intelligence. A single Claude session that sees everything — portfolio, strategy, calibration history, market data — makes holistically better decisions than specialized sub-agents passing JSON between each other.

**Working directory:** `src/` contains the complete trading system. Sibling reference projects (`AI-Trader/`, `polymarket-agent/`, `polymarket_claude/`, `Vibe-Trading/`, `TradingAgents/`) are gitignored.

**Repo layout:** Outer repo root holds `.planning/` (this workspace), design docs (`FINAL_SYSTEM_DESIGN.md`, `PROJECT_COMPARISON_REPORT.md`), and research artifacts (`research/`). Trading system lives in `src/` with its own `.claude/CLAUDE.md` (the agent instructions) and runtime state.

## Constraints

- **Tech stack:** Python tools only (no LangChain, no OpenAI SDK). Claude Code is the AI runtime.
- **APIs:** Polymarket Gamma API (discovery), CLOB API (execution), Alpha Vantage (market intel), alternative.me (Fear & Greed)
- **Database:** SQLite — immutable audit trail, append-only
- **Scheduling:** Cron + tmux + heartbeat pattern — zero LLM cost when idle
- **Safety:** Paper trading default, live gate requires proof of competence, core principles are immutable
- **Dependencies:** Minimal — py-clob-client, web3, eth-account, requests, python-dotenv. No AI libraries.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Single agent, no sub-agents | Sub-agents fragment intelligence; one session reasons holistically | ✅ Shipped — validated in production |
| Skills (reference docs) instead of agents | Claude loads frameworks on demand vs rigid pipeline | ✅ Shipped — 6 skills in active use |
| Copy to polymarket-trader/ | Clean start without breaking working polymarket-agent/ reference | ✅ Shipped |
| Paper only for v1 | Prove the autonomous loop works before risking real money | ✅ Shipped — live gate blocks real money until positive P&L |
| Claude modifies its own CLAUDE.md | Enables true self-improvement | ✅ Shipped — CLAUDE-EDITABLE sections defined |
| Heartbeat gates LLM cost | Only spin up Claude when there's work to do | ✅ Shipped — 10-min heartbeat, 2h gated cycle |
| Quarter-Kelly sizing | Full Kelly assumes perfect estimates; we don't | ✅ Shipped — KELLY_FRACTION=0.25 |
| MIN_EDGE_THRESHOLD=0.04 | Lower than old 0.10 because single-agent can find subtler edges | ✅ Shipped |
| No frontend | CLI agent monitored via logs/state files; dashboard is future milestone | ✅ Shipped |

## Evolution

This document evolves at milestone boundaries. For live state, also check:
- `STATE.md` — current execution position
- `ROADMAP.md` — phase status
- `research/TRADINGAGENTS-*.md` — v2.0 integration plans

---
*Last updated: 2026-04-13 — v1.0 milestone complete, system running 35+ autonomous cycles on cron. Source of truth for the build.*
