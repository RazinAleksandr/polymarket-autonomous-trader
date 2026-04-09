# Architecture

## Two-Layer Design

The system has two independent layers:

### Instrument Layer (Python)

Stateless CLI tools and library modules. Each tool reads config from `.env`, performs one operation, and outputs JSON to stdout. No tool maintains state between invocations -- all persistence goes through SQLite (`trading.db`) via `lib/db.py`.

```
lib/           Core logic (config, models, DB, pricing, strategy, trading, calibration)
tools/         CLI entry points (discover, analyze, trade, portfolio, calibration)
scripts/       Operational scripts (cron installer, cycle launcher, heartbeat, status)
```

### Agent Layer (Claude Code CLI)

Multi-agent system running via Claude Code. The main trading cycle orchestrator spawns specialized sub-agents, each with a defined role and structured JSON output schema.

```
.claude/agents/       Sub-agent definitions (scanner, analyst, risk-manager, planner, reviewer, strategy-updater)
.claude/skills/       Decision-making frameworks loaded on demand
```

## Agent Pipeline

Each trading cycle runs this sequence:

```
Strategy Read --> Position Monitor --> Scanner --> Analyst --> Risk Manager --> Planner --> Execute --> Reviewer --> Strategy Update
```

| Agent | Role | Analogy |
|-------|------|---------|
| Position Monitor | Check open positions for sells/holds/resolutions | Portfolio manager |
| Scanner | Discover and filter tradable markets from Gamma API | Market screener |
| Analyst | Deep-dive with web search, Bull/Bear debate, probability estimate | Research analyst |
| Risk Manager | Kelly sizing, correlation detection, exposure limits | Risk desk |
| Planner | Create concrete trade plan applying strategy rules | Portfolio manager |
| Reviewer | Analyze cycle results, extract lessons | Performance analyst |
| Strategy Updater | Incrementally refine strategy based on evidence | CIO |

Each agent outputs structured JSON validated by `lib/agent_schemas.py`. The orchestrator (`trading-cycle.md`) chains them together and handles trade execution directly.

## Data Flow

```
Gamma API --> Scanner --> [Market objects]
                              |
                              v
                         Analyst --> [MarketAnalysis with probability estimates]
                              |
                              v
                        Risk Manager --> [Sized TradeSignals]
                              |
                              v
                          Planner --> [Trade plan]
                              |
                              v
                         Execute --> tools/execute_trade.py --> trading.db
                              |
                              v
                         Reviewer --> state/reports/cycle-{id}.md
                              |
                              v
                     Strategy Updater --> state/strategy.md
```

## Key Abstractions

| Dataclass | Location | Purpose |
|-----------|----------|---------|
| `Market` | `lib/models.py` | Single prediction market with pricing and metadata (11 fields) |
| `TradeSignal` | `lib/models.py` | Intent to trade with Kelly sizing and justification (11 fields) |
| `MarketAnalysis` | `lib/models.py` | Analyst output with probability estimate and confidence |
| `OrderResult` | `lib/models.py` | Trade execution result (paper or live) |
| `CalibrationRecord` | `lib/models.py` | Probability accuracy tracking per outcome |
| `Config` | `lib/config.py` | All runtime parameters (18 fields, loaded from `.env`) |

## Persistence

| Store | Location | Contents |
|-------|----------|----------|
| SQLite | `trading.db` | 5 tables: trades, positions, decisions, market_snapshots, calibration_records |
| Strategy | `state/strategy.md` | Evolving trading playbook (agent-written) |
| Core Principles | `state/core-principles.md` | Immutable guardrails (operator-set, never modified by agent) |
| Cycle Data | `state/cycles/{id}/` | Per-cycle JSON working files (full audit trail) |
| Reports | `state/reports/cycle-{id}.md` | Human-readable cycle reports |
| Knowledge | `knowledge/` | Golden rules, calibration data, category playbooks |
| Signal | `state/signal.json` | Heartbeat output for cron gating |

## Error Handling

Each layer fails independently:

- **Discovery failure**: Returns empty list, cycle skips to report
- **Analysis failure**: Skips individual market, continues with others
- **Execution failure**: Logs per-trade error, continues with remaining signals
- **Portfolio update failure**: Logs warning, cycle continues
- **Strategy update failure**: Logs error, cycle still marked complete

No exception escapes the main cycle loop. Phase E (Learn and Evolve) always runs, even if earlier phases failed.
