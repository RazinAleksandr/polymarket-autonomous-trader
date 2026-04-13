# Polymarket Autonomous Trading Agent — Development Repo

This repo contains the autonomous Polymarket trading system plus its planning and design history.

**For the full trading agent documentation, see [`src/README.md`](src/README.md).**

## TLDR

An AI agent that autonomously trades [Polymarket](https://polymarket.com) prediction markets — binary YES/NO contracts on real-world events (elections, ceasefires, sports outcomes). Every 2 hours, cron wakes Claude up; Claude scans markets, researches each candidate with real-time web search, estimates probabilities, and executes paper trades where it finds edge. After each cycle it writes a post-mortem, tracks its own calibration with Brier scores, and updates its strategy. Starts with zero rules, builds its own playbook from experience.

- **Learns from itself.** Every trade (win or loss) becomes a recorded outcome, updates per-category calibration, and may spawn a new strategy rule or golden rule
- **Not a hardcoded bot.** Claude reads news, reasons about events, and forms its own probability estimates
- **Safe by design.** Paper trading default, 5% max per position, 30% max exposure, 5-loss pause, live trading locked behind a performance gate
- **Full audit trail.** Every cycle writes a detailed markdown report with sources, reasoning, P&L — 35+ cycles and counting

Current: 35+ autonomous paper cycles, 7 trades, realized -$149 on $10K bankroll (one big geopolitical loss dominates), 3 open positions. See [`src/docs/real-results.md`](src/docs/real-results.md) for the full trade-by-trade breakdown.

## TLDR: Architecture

Two layers that talk through the command line.

**Python instrument layer** (`src/lib/`, `src/tools/`) — stateless CLI scripts. `discover_markets.py` hits Polymarket's Gamma API. `execute_trade.py` places orders on CLOB via py-clob-client. `calculate_kelly.py` does the sizing math. `record_outcome.py` updates calibration. They take args, print JSON to stdout, exit. No AI.

**Claude Code agent layer** (`src/.claude/`) — one Claude Code session per cycle, no sub-agents. Reads `CLAUDE.md` for the 5-phase cycle (check positions → find opportunities → analyze → size & execute → learn & evolve). Loads 6 skill docs on demand as analytical frameworks:

- `evaluate-edge.md` — bull/bear research and probability synthesis
- `size-position.md` — Kelly criterion with category caps
- `calibration-check.md` — apply past-accuracy corrections
- `resolution-parser.md` — handle resolved markets
- `post-mortem.md` — classify mistakes, extract rules
- `cycle-review.md` — write report, update strategy

**Every cycle Claude reads:** `state/strategy.md` (its own evolving playbook), `state/core-principles.md` (immutable guardrails), `state/bankroll.json`, `knowledge/golden-rules.md`, `knowledge/calibration.json`, last 3 cycle reports.

**Every cycle Claude writes:** a report in `state/reports/`, 0-3 strategy updates, category lessons, bankroll/calibration deltas.

**Scheduling:** `scripts/heartbeat.py` (every 10 min, no LLM) signals whether there's work. `scripts/run_cycle.sh` (every 2h) launches Claude in tmux with a 20-min timeout if the signal is hot. Forced daily cycle at 2 AM UTC.

**Persistence:** SQLite (`trading.db`) for trades/positions/decisions, markdown for strategy/reports/rules, JSON for calibration/bankroll/signals. Everything append-only, git-versioned, fully auditable.

## Structure

```
.
├── .claude/                        # Outer claude config (guides repo-level dev sessions)
├── .planning/                      # Outer GSD workspace — see section below
├── README.md                       # This file
└── src/                            # The trading system itself
    ├── .claude/                    # Trading agent's instructions (CLAUDE.md + 6 skills)
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
