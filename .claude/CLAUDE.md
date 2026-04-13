# Outer Repo — Polymarket Trader (Development Workspace)

This is the **outer** repo, not the trading agent itself. It holds:

1. **Outer planning** (`.planning/`) — GSD workspace tracking system-level design, build history, and research.
2. **The trading system** (`src/`) — the actual autonomous Polymarket trader with its own Claude instructions (`src/.claude/CLAUDE.md`) and runtime code.

## Start here for context

- `.planning/PROJECT.md` — live overview, current state, validated requirements
- `.planning/STATE.md` — live execution status (cycles, P&L, cron schedule)
- `.planning/ROADMAP.md` — 6-phase v1.0 roadmap (all complete)
- `src/README.md` — full trading agent documentation
- `src/docs/real-results.md` — trade-by-trade history with current results

## When working in this repo

- **Trading agent changes** (Python code, skills, strategy, cron) → work inside `src/`. Read `src/.claude/CLAUDE.md` and `src/README.md` first.
- **System design / research / new phases** → work at the outer level. Use `.planning/` as the GSD workspace.
- **Never confuse the two claudes.** `src/.claude/CLAUDE.md` is the autonomous trader that runs on cron every 2 hours. This outer `.claude/CLAUDE.md` is just context for development sessions on the repo.

## Live system status

The trading agent runs unattended via cron (heartbeat/10min, cycle/2h, forced daily/2AM). Paper trading mode. v1.0 milestone complete as of 2026-04-09. Source of truth for current state is `.planning/STATE.md` and `src/state/reports/cycle-*.md`.

## Repo layout

```
.claude/                    ← you are here (outer dev config)
.planning/                  outer GSD workspace
  PROJECT.md                live overview (read first)
  STATE.md                  live execution state
  ROADMAP.md                6 phases, all complete
  phases/                   16 plans, all shipped
  codebase/                 reference docs about src/
  research/                 historical + forward-looking research
    FINAL_SYSTEM_DESIGN.md              [HISTORICAL]
    PROJECT_COMPARISON_REPORT.md        [HISTORICAL]
    TRADINGAGENTS-COMPARISON.md         [FORWARD — v2.0 candidate]
    TRADINGAGENTS-INTEGRATION-PLAN.md   [FORWARD — v2.0 candidate]
README.md                   brief repo overview
src/                        the trading system
```

## Candidate next work (v2.0)

Two research docs in `.planning/research/` propose the highest-leverage improvements:
- **Bull/Bear structured debate** (replaces single-agent Phase C research with adversarial multi-agent debate)
- **BM25 memory retrieval** (per-category lessons retrieved by similarity, not just recency)

Both are transplantable from the TradingAgents reference project. See `TRADINGAGENTS-INTEGRATION-PLAN.md` for the concrete plan.
