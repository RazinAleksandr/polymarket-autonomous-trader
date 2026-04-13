# Outer Repo — Polymarket Trader (Development Workspace)

This is the **outer** repo, not the trading agent itself. It holds two things:

1. **Outer planning** (`.planning/`) — GSD workspace used to design, restructure, and research the trading system. Contains PROJECT.md, ROADMAP.md, phase plans, and research artifacts (comparisons, integration plans).
2. **The trading system** (`src/`) — the actual autonomous Polymarket trader with its own Claude instructions (`src/.claude/CLAUDE.md`), its own GSD history (`src/.planning/`), and all runtime code.

## When working in this repo

- **Trading agent changes** (code, skills, strategy) → work inside `src/`. Read `src/.claude/CLAUDE.md` and `src/README.md` first.
- **System design / restructure / research work** → work at the outer level. Outer `.planning/` tracks that work.
- **Never confuse the two claudes.** The trading agent's claude in `src/.claude/` is the autonomous trader that runs on cron. This outer `.claude/` is just for guiding development sessions on the outer repo.

## Sibling reference projects

When this repo's `.git` is at `/home/trader/` level, sibling directories exist at the same level:
- `AI-Trader/`, `polymarket-agent/`, `polymarket_claude/`, `Vibe-Trading/`, `TradingAgents/`

These are reference implementations the trading system was built from. They are gitignored — do not commit them.

## Top-level docs

- `FINAL_SYSTEM_DESIGN.md` — the design document that drove the build
- `PROJECT_COMPARISON_REPORT.md` — comparison of the source projects (polymarket-agent, polymarket_claude, AI-Trader)
- `README.md` — brief repo overview
