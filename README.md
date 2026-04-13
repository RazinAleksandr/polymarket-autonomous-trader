# Polymarket Autonomous Trading Agent — Development Repo

This repo contains the autonomous Polymarket trading system plus its planning and design history.

## Structure

```
.
├── .claude/                        # Outer claude config (for working on this repo)
├── .planning/                      # Outer GSD workspace — design, research, restructure plans
├── FINAL_SYSTEM_DESIGN.md          # Master design doc that drove the build
├── PROJECT_COMPARISON_REPORT.md    # Comparison of the 3 source projects
└── src/                            # The trading system itself
    ├── .claude/                    # Trading agent's instructions (CLAUDE.md + skills)
    ├── .planning/                  # Trading system's GSD build history (4 phases, 15 plans)
    ├── README.md                   # Full trading agent docs — START HERE
    ├── docs/                       # Detailed docs (real results, architecture, live trading)
    ├── lib/                        # Core Python library (config, db, strategy, calibration)
    ├── tools/                      # CLI tools the agent calls via bash
    ├── scripts/                    # Operator scripts (cron, heartbeat, setup)
    ├── knowledge/                  # Agent's accumulated wisdom (golden rules, calibration, playbooks)
    ├── state/                      # Runtime state (strategy, reports, bankroll)
    ├── tests/                      # Pytest suite
    └── tests/                      # 24 test modules
```

## For the full trading agent documentation, see [`src/README.md`](src/README.md).

## Sibling reference projects

When this repo is checked out at `/home/trader/` level, these sibling directories are reference-only (gitignored):

- `AI-Trader/` — best platform infrastructure
- `polymarket-agent/` — best architecture & safety
- `polymarket_claude/` — best trading knowledge & strategy
- `TradingAgents/` — multi-agent debate framework (research target for future integration)
- `Vibe-Trading/` — additional patterns

See [`PROJECT_COMPARISON_REPORT.md`](PROJECT_COMPARISON_REPORT.md) for the full comparison and [`FINAL_SYSTEM_DESIGN.md`](FINAL_SYSTEM_DESIGN.md) for the design.

## Two-level development

This repo holds two concerns:

1. **Outer (this level)** — designing, restructuring, and researching the trading system. Use `.planning/` for GSD workspace.
2. **Inner (`src/`)** — the actual autonomous trading agent. Has its own Claude instructions (`src/.claude/`) and its own GSD build history (`src/.planning/`).

Work on the trading agent happens inside `src/`. Work on system-level design happens at the outer level.
