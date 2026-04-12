# Polymarket Autonomous Trading Agent

![python](https://img.shields.io/badge/python-3.12-blue)
![agent](https://img.shields.io/badge/agent-Claude_Code-orange)
![license](https://img.shields.io/badge/license-MIT-green)
![mode](https://img.shields.io/badge/mode-paper_+_live-grey)
![chain](https://img.shields.io/badge/chain-Polygon-blueviolet)

An AI agent that autonomously trades prediction markets on [Polymarket](https://polymarket.com) — discovering opportunities, estimating probabilities with web research, sizing positions via Kelly criterion, and evolving its own strategy from experience.

Built as a two-layer system:

1. **Instrument Layer** (Python) — Stateless CLI tools for market data, order execution, portfolio tracking, and calibration
2. **Agent Layer** (Claude Code) — Orchestrates the full trading cycle: scan → analyze → size → execute → review → learn

The agent starts with zero knowledge. After each cycle it writes a detailed report, tracks calibration accuracy per category, extracts golden rules from mistakes, and updates its strategy — like a junior analyst building a playbook over months on the job.

> **Paper trading by default.** Live trading requires passing a 4-criteria safety gate.

## Real Results

After 30 autonomous cycles (April 4–12, 2026), the agent:

- Scanned 1,500+ markets, analyzed ~100 in depth with web research
- Executed **7 paper trades** across geopolitics, elections, and sports
- **2 wins:** +$21 (US forces Iran YES), +$131 (Thunder/Nuggets NO — 23.5pp edge from rest-day mispricing)
- **1 loss:** -$301 (Iran ceasefire NO — Pakistan brokered a surprise deal in 2 days)
- **3 open positions:** Hungary election (resolving today), Iran conflict, US-Iran meeting
- Self-diagnosed every loss, extracted 7 strategy rules and 17 golden rules autonomously
- Learned to verify sportsbook odds across 3+ sources — prevented at least 2 bad trades

See **[Real Results: 30 Autonomous Trading Cycles](docs/real-results.md)** for the full trade-by-trade breakdown, strategy evolution timeline, and how math analytics and web search drive every decision.

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Trading Cycle (every 2h)                  │
│                                                             │
│  Phase A: Check Positions                                   │
│    └─ Resolved markets → P&L, sell signals, thesis review   │
│                                                             │
│  Phase B: Find Opportunities                                │
│    └─ Gamma API → filter by resolution, price, volume       │
│                                                             │
│  Phase C: Analyze Markets                                   │
│    └─ Web research → Bull/Bear evidence → probability est.  │
│    └─ Calibration correction from past accuracy             │
│                                                             │
│  Phase D: Size and Execute                                  │
│    └─ Kelly criterion → confidence weighting → paper/live   │
│                                                             │
│  Phase E: Learn and Evolve                                  │
│    └─ Post-mortem → calibration update → strategy update    │
│    └─ Golden rules from losses > 2% bankroll                │
└─────────────────────────────────────────────────────────────┘
```

The **heartbeat system** (Python, no LLM) runs every 10 minutes and checks if there's work to do — expiring positions, new calibration data, time since last scan. The expensive Claude cycle only runs when the heartbeat signals a need.

## Prerequisites

- Python 3.12+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`npm install -g @anthropic-ai/claude-code`)
- Anthropic API key
- tmux, cron
- Internet access (Polymarket APIs, web search for market analysis)

## Setup

```bash
git clone git@github.com:RazinAleksandr/polymarket-autonomous-trader.git
cd polymarket-autonomous-trader

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# No API keys needed for paper trading
```

## Quick Start

### Run a single trading cycle

```bash
./scripts/run_cycle.sh --force
```

Launches Claude in tmux. It reads its strategy, scans markets, runs web research on candidates, sizes positions, executes paper trades, writes a cycle report, and updates its strategy.

### Run autonomously on a schedule

```bash
# Install cron entries (heartbeat/10min, gated cycle/2h, daily force/2AM)
./scripts/install_cron.sh

# Check health
./scripts/status.sh

# Remove cron
./scripts/install_cron.sh --remove
```

### Run interactively

```bash
source .venv/bin/activate
IS_SANDBOX=1 claude --dangerously-skip-permissions
# Then type: run a trading cycle
```

## CLI Tools

All tools output JSON. Add `--pretty` for human-readable format.

```bash
source .venv/bin/activate

# Market discovery
python tools/discover_markets.py --limit 50 --pretty

# Portfolio and risk
python tools/get_portfolio.py --include-risk --pretty

# Check resolved markets
python tools/check_resolved.py --pretty

# Position sizing
python tools/calculate_kelly.py --estimated-prob 0.70 --market-price 0.55 --bankroll 200 --pretty

# Execute paper trade
python tools/execute_trade.py --market-id <ID> --token-id <TOKEN> --side YES --size 10 --pretty

# Record outcome for calibration
python tools/record_outcome.py --market-id <ID> --stated-prob 0.85 --actual WIN --category politics --pretty

# Market intelligence (macro signals, sector news)
python tools/get_market_intel.py --pretty

# Live trading gate check
python tools/enable_live.py --check

# Validate cycle reports
python tools/validate_cycle.py --summary --pretty
```

## Strategy Evolution

The agent builds its trading knowledge from scratch:

| Layer | File | Purpose |
|-------|------|---------|
| **Strategy** | `state/strategy.md` | Evolving playbook — updated 0–3 changes per cycle with evidence |
| **Guardrails** | `state/core-principles.md` | Immutable rules set by operator (agent reads, never modifies) |
| **Golden Rules** | `knowledge/golden-rules.md` | Hard-won lessons from losses > 2% bankroll |
| **Calibration** | `knowledge/calibration.json` | Per-category probability accuracy tracking |
| **Category Playbooks** | `knowledge/market-types/*.md` | Category-specific patterns (politics, crypto, sports, etc.) |
| **Skills** | `.claude/skills/*.md` | Decision frameworks: edge evaluation, position sizing, post-mortem |
| **Cycle Reports** | `state/reports/cycle-*.md` | Full per-cycle analysis with trade reasoning |

The strategy starts minimal. Over cycles, it becomes a comprehensive playbook — entirely written by the agent based on what works and what doesn't.

## Project Structure

```
polymarket-autonomous-trader/
  lib/                        # Core Python library
    config.py                 #   Configuration from .env
    models.py                 #   Market, TradeSignal, OrderResult dataclasses
    market_data.py            #   Gamma API client (discovery, pricing, resolution)
    market_intel.py           #   Macro signals (ETF trends, Fear & Greed, news)
    db.py                     #   SQLite persistence (7 tables)
    calibration.py            #   Brier scores, category accuracy tracking
  tools/                      # CLI tools (all JSON output)
    discover_markets.py       #   Market discovery with filters
    execute_trade.py          #   Paper and live execution
    sell_position.py          #   Position exit
    get_portfolio.py          #   Portfolio, P&L, risk limits
    check_resolved.py         #   Resolution detection
    calculate_kelly.py        #   Kelly criterion sizing
    record_outcome.py         #   Calibration outcome recording
    get_market_intel.py       #   Macro intelligence
    enable_live.py            #   Live trading gate (4 criteria)
    validate_cycle.py         #   Cycle report validation
  scripts/                    # Operations
    run_cycle.sh              #   Cycle launcher (tmux, PID lock, timeout)
    heartbeat.py              #   Lightweight signal generator (no LLM)
    install_cron.sh           #   Cron management
    status.sh                 #   System health check
  .claude/
    CLAUDE.md                 #   Agent instructions (5-phase cycle)
    skills/                   #   Decision frameworks (6 skill docs)
  state/                      # Runtime state
    strategy.md               #   Agent-evolved trading strategy
    core-principles.md        #   Immutable operator guardrails
    bankroll.json             #   Current bankroll tracking
    signal.json               #   Heartbeat output for cron gating
    cycles/                   #   Per-cycle working data
    reports/                  #   Per-cycle markdown reports
  knowledge/                  # Accumulated wisdom
    golden-rules.md           #   Rules from costly mistakes
    calibration.json          #   Probability accuracy by category
    market-types/             #   Category playbooks
  tests/                      # Pytest suite
  docs/                       # Documentation
```

## Live Trading

Live trading has a 4-criteria safety gate:

1. **10+ paper cycles** completed
2. **Positive** aggregate paper P&L
3. **Win rate > 50%**
4. **Calibration health** — no category bias exceeding -20pp

```bash
python tools/enable_live.py --check   # Read-only status
python tools/enable_live.py           # Interactive enable (requires "CONFIRM LIVE")
python tools/enable_live.py --revoke  # Revoke access
```

Then set in `.env`:
```env
PAPER_TRADING=false
PRIVATE_KEY=your_ethereum_private_key
```

Wallet setup for Polygon: `python setup_wallet.py`

See [docs/live-trading.md](docs/live-trading.md) for full details.

## Configuration

All parameters in `.env`. See [`.env.example`](.env.example) for the full list.

| Parameter | Default | Description |
|-----------|---------|-------------|
| `PAPER_TRADING` | `true` | Paper mode (no real orders) |
| `MIN_EDGE_THRESHOLD` | `0.04` | Minimum edge to trade (4pp) |
| `KELLY_FRACTION` | `0.25` | Quarter Kelly for conservative sizing |
| `MAX_POSITION_PCT` | `0.05` | Max 5% of bankroll per position |
| `MAX_EXPOSURE_PCT` | `0.30` | Max 30% total portfolio exposure |
| `MAX_RESOLUTION_DAYS` | `14` | Only trade markets resolving within 14 days |
| `MIN_VOLUME_24H` | `1000` | Minimum 24h volume filter |
| `MIN_LIQUIDITY` | `500` | Minimum liquidity filter |

## Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Documentation

| Doc | Contents |
|-----|----------|
| [Real Results](docs/real-results.md) | Trade-by-trade history, P&L, strategy evolution, analytics in action |
| [Architecture](docs/architecture.md) | Two-layer design, agent pipeline, data flow |
| [Tools Reference](docs/tools-reference.md) | All CLI tools with flags and examples |
| [Scheduling](docs/scheduling.md) | Cron setup, heartbeat gating, monitoring |
| [Strategy Evolution](docs/strategy-evolution.md) | Calibration, golden rules, knowledge base |
| [Live Trading](docs/live-trading.md) | Gate criteria, wallet setup, safety |
| [Configuration](docs/configuration.md) | All .env parameters with defaults |

## Safety

- Paper trading is always the default
- Live trading requires positive P&L over 10+ cycles, plus manual confirmation
- Maximum 5% bankroll per position, 30% total exposure
- Agent cannot modify core principles or enable live mode
- PID lockfile prevents overlapping cycles
- 20-minute timeout kills runaway sessions
- All decisions logged to SQLite and cycle reports for full audit trail
- 5 consecutive losses trigger a 24-hour trading pause
