# Polymarket Autonomous Trading Agent — Development Repo

This repo contains the autonomous Polymarket trading system plus its planning and design history.

**For the full trading agent documentation, see [`src/README.md`](src/README.md).**

## Structure

```
.
├── .claude/                        # Outer claude config (guides repo-level dev sessions)
├── .planning/                      # Outer GSD workspace — see section below
├── README.md                       # This file
└── src/                            # The trading system itself
    ├── .claude/                    # Trading agent's instructions (CLAUDE.md + 6 skills)
    ├── CLAUDE.md
    ├── README.md                   # Full trading agent docs — START HERE
    ├── docs/                       # Real results, architecture, live trading, scheduling
    ├── lib/                        # Core Python library (config, db, strategy, calibration)
    ├── tools/                      # CLI tools the agent calls via bash
    ├── scripts/                    # Operator scripts (cron, heartbeat, setup)
    ├── knowledge/                  # Golden rules, calibration, category playbooks
    ├── state/                      # Runtime state (strategy, reports, bankroll)
    ├── tests/                      # Pytest suite (24+ modules)
    ├── reset_agent.sh              # Manual reset utility
    ├── setup_wallet.py             # One-time wallet setup for live trading
    ├── pytest.ini
    └── requirements.txt
```

## `.planning/` — Outer Planning Workspace

GSD (Get Shit Done) workspace that tracks system-level design, build history, and forward-looking research. Entry points for a new agent session:

- **`PROJECT.md`** — start here. Project overview, current live state, validated requirements, what's next.
- **`STATE.md`** — live execution status (cycle count, P&L, recent changes).
- **`ROADMAP.md`** — 6-phase roadmap, all complete.

```
.planning/
├── PROJECT.md              Live overview with current state (read first)
├── STATE.md                Execution state, cron schedule, real P&L
├── ROADMAP.md              6 phases, all complete
├── REQUIREMENTS.md         Full requirements list
├── config.json             GSD config
│
├── codebase/               Reference docs about the src/ codebase
│   ├── ARCHITECTURE.md
│   ├── CONCERNS.md
│   ├── CONVENTIONS.md
│   ├── INTEGRATIONS.md
│   ├── STACK.md
│   ├── STRUCTURE.md
│   └── TESTING.md
│
├── phases/                 Historical build record — all 6 phases shipped
│   ├── 01-single-agent-architecture/       2 plans
│   ├── 02-knowledge-base-safety/           3 plans
│   ├── 03-new-instrument-tools/            3 plans
│   ├── 04-config-integration/              2 plans
│   ├── 05-autonomous-cycle-validation/     3 plans
│   └── 06-scheduling-paper-validation/     3 plans
│
└── research/               Historical and forward-looking research
    ├── FINAL_SYSTEM_DESIGN.md              [HISTORICAL] Original design doc that drove the build
    ├── PROJECT_COMPARISON_REPORT.md        [HISTORICAL] Comparison of the 3 source projects
    ├── TRADINGAGENTS-COMPARISON.md         [FORWARD]    Comparison with TradingAgents framework
    └── TRADINGAGENTS-INTEGRATION-PLAN.md   [FORWARD]    Bull/bear debate + BM25 memory plan
```

Each phase folder has: `XX-YY-PLAN.md` + `XX-YY-SUMMARY.md` per plan, plus phase-level `CONTEXT.md`, `DISCUSSION-LOG.md`, optional `RESEARCH.md` / `VALIDATION.md` / `VERIFICATION.md`.

## Source Projects

The trading system was built by cherry-picking from three reference implementations. See [`.planning/research/PROJECT_COMPARISON_REPORT.md`](.planning/research/PROJECT_COMPARISON_REPORT.md) for the comparison and [`.planning/research/FINAL_SYSTEM_DESIGN.md`](.planning/research/FINAL_SYSTEM_DESIGN.md) for the original design that drove the build. Both are historical — current live docs are `src/README.md` and `.planning/PROJECT.md`.

## Two-Level Development

This repo holds two concerns:

1. **Outer (this level)** — designing, planning, researching the trading system. Uses `.planning/` as GSD workspace and `.claude/CLAUDE.md` to guide dev sessions.
2. **Inner (`src/`)** — the actual autonomous trading agent that runs on cron. Has its own `.claude/CLAUDE.md` (5-phase trading cycle instructions), 6 skill docs, and runtime state.

Work on the trading agent itself happens inside `src/`. Work on system-level design, research, or new phase planning happens at the outer level.
