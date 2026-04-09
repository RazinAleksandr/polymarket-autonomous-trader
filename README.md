# Polymarket Autonomous Trading Agent

An autonomous prediction market trading agent for [Polymarket](https://polymarket.com).

**Instrument layer** (Python) provides stateless CLI tools for market data, order execution, and portfolio tracking. **Agent layer** (Claude Code) runs a multi-agent system that discovers markets, estimates probabilities, sizes positions, executes trades, and evolves its own strategy from experience.

The agent starts with zero knowledge. After each cycle it reviews its decisions, tracks calibration accuracy per category, extracts golden rules from mistakes, and updates its strategy -- like a human analyst building a playbook.

Paper trading is the default. Live trading requires passing a 4-criteria safety gate.

## Prerequisites

- Python 3.12+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code)
- Anthropic API key
- tmux, cron
- Internet access (Polymarket APIs, web search)

## Setup

```bash
git clone <repo-url>
cd polymarket-trader
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # No API keys needed for paper trading
```

## Quick Start

### Run a single trading cycle

```bash
./scripts/run_cycle.sh --force
```

This launches a Claude session in tmux that runs the full pipeline: scan markets, analyze with web research, size positions via Kelly criterion, execute paper trades, write a cycle report, and update strategy.

### Run autonomously on a schedule

```bash
# Install 3 cron entries (heartbeat/10min, gated cycle/30min, daily scan/2AM UTC)
./scripts/install_cron.sh

# Check system health anytime
./scripts/status.sh

# Remove all cron entries
./scripts/install_cron.sh --remove
```

The heartbeat checks market state every 10 minutes (zero LLM cost). Full trading cycles only run when the heartbeat signals there's work to do. See [docs/scheduling.md](docs/scheduling.md).

### Run interactively

```bash
source .venv/bin/activate
claude --dangerously-skip-permissions
# Then type: run a trading cycle
```

## CLI Tools

All tools output JSON to stdout. Add `--pretty` for human-readable format.

```bash
source .venv/bin/activate

# Discover markets
python tools/discover_markets.py --pretty

# Portfolio and P&L
python tools/get_portfolio.py --include-risk --pretty

# Check resolved markets
python tools/check_resolved.py --pretty

# Calculate edge and position size
python tools/calculate_edge.py --estimated-prob 0.70 --market-price 0.55 --pretty
python tools/calculate_kelly.py --estimated-prob 0.70 --market-price 0.55 --bankroll 200 --pretty

# Execute a paper trade
python tools/execute_trade.py --market-id <ID> --token-id <TOKEN> --side YES --size 10 --pretty

# Check live trading gate (read-only)
python tools/enable_live.py --check

# Validate cycle reports
python tools/validate_cycle.py --summary --pretty
```

Full reference: [docs/tools-reference.md](docs/tools-reference.md)

## Project Structure

```
polymarket-trader/
  lib/                    # Core Python library (config, models, DB, trading, calibration)
  tools/                  # CLI tools (14 tools, all JSON output)
  scripts/                # Operational scripts (cron, heartbeat, status, cycle launcher)
  .claude/agents/         # Claude sub-agent definitions
  .claude/skills/         # Trading decision frameworks (loaded on demand)
  state/                  # Runtime state
    strategy.md           #   Agent-evolved trading strategy
    core-principles.md    #   Immutable guardrails (never modified by agent)
    signal.json           #   Heartbeat output for cron gating
    cycles/               #   Per-cycle JSON working data
    reports/              #   Per-cycle markdown reports
  knowledge/              # Accumulated trading wisdom
    golden-rules.md       #   Hard-won rules from trading outcomes
    calibration.json      #   Per-category probability accuracy
    market-types/         #   Category-specific playbooks
  tests/                  # Pytest test suite (23 test files)
  docs/                   # Detailed documentation
```

## Live Trading

Live trading requires passing all 4 gate criteria:

1. 10+ paper trading cycles completed
2. Positive aggregate P&L
3. Win rate > 50%
4. Calibration health (no category bias > -20pp)

```bash
python tools/enable_live.py --check   # Check criteria (read-only)
python tools/enable_live.py           # Enable (interactive, requires confirmation)
```

See [docs/live-trading.md](docs/live-trading.md).

## Tests

```bash
source .venv/bin/activate
pytest tests/ -v
```

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/architecture.md](docs/architecture.md) | Two-layer design, agent pipeline, data flow |
| [docs/tools-reference.md](docs/tools-reference.md) | All CLI tools with flags and examples |
| [docs/scheduling.md](docs/scheduling.md) | Cron setup, heartbeat gating, monitoring |
| [docs/strategy-evolution.md](docs/strategy-evolution.md) | Calibration system, golden rules, knowledge base |
| [docs/live-trading.md](docs/live-trading.md) | Gate criteria, wallet setup, safety guardrails |
| [docs/configuration.md](docs/configuration.md) | All .env parameters with defaults |
