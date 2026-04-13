# Codebase Structure

**Analysis Date:** 2026-04-02

## Directory Layout

```
/home/trader/
├── polymarket-agent/           # Main autonomous trading system (Python + Claude agents)
│   ├── lib/                    # Core Python library modules
│   ├── tools/                  # CLI tools for market data, pricing, execution
│   ├── .claude/agents/         # Claude Code sub-agent definitions
│   ├── state/                  # Runtime state (strategy, principles, cycle data)
│   ├── tests/                  # Pytest test suite
│   ├── requirements.txt        # Python dependencies
│   ├── run_cycle.sh            # Single trading cycle runner
│   ├── schedule_trading.sh     # Cron-based scheduling
│   └── .env.example            # Configuration template
├── Vibe-Trading/               # Research & backtesting platform (React + Python)
│   ├── frontend/               # React SPA for visualizations
│   ├── agent/                  # Python API server + agent tools
│   └── assets/                 # Logo and images
├── AI-Trader/                  # Multi-market trading platform (FastAPI + React)
│   ├── service/                # Backend (FastAPI) + frontend (React)
│   ├── skills/                 # Agent skill definitions
│   ├── docs/                   # API specifications and guides
│   └── assets/                 # Images
├── polymarket_claude/          # Legacy single-agent research system
│   ├── output/                 # Generated trade passes, learnings, reports
│   ├── knowledge/              # Market research documents
│   ├── scripts/                # Research and analysis scripts
│   └── research/               # Domain-specific analysis
├── AI-Trader/                  # Trading platform (legacy structure)
└── .planning/codebase/         # This analysis output

## Directory Purposes

**polymarket-agent/lib/**
- Purpose: Core reusable modules for market data, pricing, strategy, execution, portfolio, database
- Contains: Python modules for all trading logic
- Key files: 
  - `config.py`: Environment and parameter loading
  - `models.py`: Dataclasses for Market, TradeSignal, OrderResult
  - `market_data.py`: Gamma API client for market discovery
  - `pricing.py`: CLOB API price fetching
  - `strategy.py`: Kelly criterion sizing, signal generation
  - `trading.py`: Paper and live trade execution
  - `portfolio.py`: Position tracking and risk checks
  - `db.py`: SQLite persistence (5 tables)
  - `agent_schemas.py`: JSON schema validation for sub-agent outputs
  - `logging_setup.py`: Dual logging (console + JSON file)

**polymarket-agent/tools/**
- Purpose: Stateless CLI tools for individual operations (JSON output to stdout)
- Contains: Executable Python scripts for market discovery, pricing, sizing, execution
- Key files:
  - `discover_markets.py`: Find active markets from Gamma API
  - `get_prices.py`: Fetch orderbook prices for a token
  - `calculate_edge.py`: Calculate estimated edge (your prob vs market price)
  - `calculate_kelly.py`: Calculate Kelly criterion position size
  - `execute_trade.py`: Execute paper or live trade
  - `get_portfolio.py`: View open positions and P&L
  - `check_resolved.py`: Detect resolved markets for settlement
  - `enable_live.py`: Live trading gate check and activation
  - `sell_position.py`: Sell portion of position
  - `setup_schedule.py`: Cron job management

**polymarket-agent/.claude/agents/**
- Purpose: Claude Code sub-agent definitions (markdown files with prompts and schemas)
- Contains: Modular agents spawned via Task tool in orchestration
- Key files:
  - `trading-cycle.md`: Main orchestrator (8-step pipeline)
  - `scanner.md`: Market discovery agent
  - `analyst.md`: Probability estimation (Bull/Bear debate, web search)
  - `risk-manager.md`: Position sizing, correlation detection
  - `planner.md`: Trade plan generation from analysis + risk
  - `reviewer.md`: Cycle analysis and report writing
  - `strategy-updater.md`: Incremental strategy.md updates based on learnings
  - `position-monitor.md`: Check open positions for sells/holds (optional)
  - `outcome-analyzer.md`: Closed position analysis (Brier scores, calibration)

**polymarket-agent/state/**
- Purpose: Runtime state that evolves over time
- Contains: Agent-maintained strategy document, human principles, cycle results
- Key files:
  - `strategy.md`: Evolving trading strategy (4 domains: market selection, analysis, risk, entry/exit)
  - `core-principles.md`: Human-set guardrails (read-only for agents)
  - `cycles/{cycle_id}/`: Per-cycle JSON outputs from each agent step
  - `reports/cycle-{cycle_id}.md`: Human-readable cycle reports
  - Trading database `trading.db`: SQLite with 5 tables (trades, positions, decisions, market_snapshots, strategy_metrics)

**polymarket-agent/tests/**
- Purpose: Pytest test suite for core modules
- Contains: Unit and integration tests for market discovery, strategy, portfolio, trading
- Key file: `test_paper_trading.py`: Smoke tests of key workflow steps

**Vibe-Trading/frontend/src/**
- Purpose: React SPA for real-time trading visualization
- Contains: React components, hooks, stores, pages, types
- Structure:
  - `components/`:
    - `layout/`: Layout wrapper, connection banner
    - `chat/`: Message bubble, thinking timeline, agent avatar, metrics card, welcome screen, swarm dashboard, conversation timeline, run complete card
    - `charts/`: Equity chart, mini equity chart, candlestick chart
    - `common/`: Skeleton loader, error boundary
  - `pages/`: Home, Agent, RunDetail, Compare
  - `stores/`: Zustand state (agent.ts for shared state)
  - `hooks/`: useSSE (Server-Sent Events), useDarkMode
  - `lib/`: API client (api.ts), formatters, i18n, ECharts config, indicators
  - `types/`: TypeScript interfaces (agent.ts for SwarmAgent)
  - `router.tsx`: React Router 7 configuration
  - `index.css`: Tailwind CSS setup

**Vibe-Trading/agent/src/**
- Purpose: Python agent backend for backtest execution and analysis
- Contains: FastAPI API server, tools for code execution, artifact management, analysis
- Structure:
  - `core/`: Runner (subprocess execution), state management
  - `providers/`: LLM (Claude via API), chat (Claude Code protocol)
  - `tools/`: CLI tools (bash, write_file, edit_file, doc_reader, pattern analysis, swarm coordination, factor analysis, background tasks)
  - `ui_services.py`: Build run analysis, load context
  - `backtest/`: Backtest runner and result collection

**AI-Trader/service/server/**
- Purpose: FastAPI backend for multi-market trading platform
- Contains: Routes, business logic, database, background tasks
- Key files:
  - `main.py`: FastAPI app initialization, background task scheduling
  - `routes.py`: API endpoints for agents, signals, discussions, leaderboards, copy trading, Polymarket
  - `database.py`: SQLite schema with 20+ tables (agents, signals, discussions, leaderboards, trades, positions, Polymarket markets)
  - `services.py`: Business logic for signal aggregation, copy trading, leaderboard calculation
  - `tasks.py`: Background async tasks (price updates, profit history, Polymarket settlement, data snapshots)
  - `price_fetcher.py`: Market data integration (stocks, crypto, Polymarket, futures, options)
  - `market_intel.py`: Market news, macro signals, ETF flows, stock analysis
  - `config.py`: Configuration loading
  - `utils.py`: Utility functions
  - `fees.py`: Trading fee calculation

**AI-Trader/service/frontend/**
- Purpose: React SPA for AI-Trader trading platform
- Contains: Trading dashboard, agent signals, copy trading UI, leaderboards
- Key packages: React 19, Vite, Tailwind CSS, ECharts/Recharts, Zustand

**AI-Trader/skills/**
- Purpose: OpenClaw-compatible agent skill definitions
- Key skills:
  - `ai4trade/SKILL.md`: Main trading platform skill
  - `copytrade/SKILL.md`: Copy trading skill
  - `tradesync/SKILL.md`: Trade sync (signal provider) skill
  - `market-intel/SKILL.md`: Market intelligence and news
  - `polymarket/SKILL.md`: Polymarket integration
  - `heartbeat/SKILL.md`: Periodic signal monitoring

**polymarket_claude/**
- Purpose: Legacy single-agent research system (predecessor to polymarket-agent)
- Contains: Accumulated market research, trade passes, learnings
- Structure:
  - `output/passes/`: Trading passes (market analysis + recommendations)
  - `output/trades/`: Trade execution records
  - `output/learnings/`: General principles, market-specific learnings
  - `output/reports/`: Daily reports, scan reports, resolution reports
  - `knowledge/`: Market research documents (politics, sports, crypto, commodities, oscars)
  - `scripts/`: Research execution scripts
  - `research/`: Detailed analysis (e.g., crude oil futures)

## Key File Locations

**Entry Points:**
- `polymarket-agent`: `.claude/agents/trading-cycle.md` (main orchestrator)
- `polymarket-agent`: `tools/discover_markets.py` (market discovery CLI)
- `polymarket-agent`: `setup_wallet.py` (one-time wallet setup)
- `Vibe-Trading`: `agent/api_server.py` (FastAPI server)
- `Vibe-Trading`: `agent/mcp_server.py` (MCP protocol server for Claude integration)
- `AI-Trader`: `service/server/main.py` (FastAPI backend)
- `AI-Trader`: `service/frontend/src/main.tsx` (React entry point)

**Configuration:**
- `polymarket-agent/.env.example`: Template for all trading parameters
- `Vibe-Trading/.env.example`: Agent configuration template
- `AI-Trader/.env.example`: Multi-market platform config
- `Vibe-Trading/agent/backtest/runner.py`: Backtest execution configuration

**Core Logic:**
- `polymarket-agent/lib/strategy.py`: Kelly criterion, edge calculation, signal generation
- `polymarket-agent/lib/trading.py`: Paper and live trade execution
- `polymarket-agent/lib/portfolio.py`: Position tracking, risk limits, P&L calculation
- `AI-Trader/service/server/routes.py`: All REST API endpoints (2700+ lines)
- `Vibe-Trading/agent/src/core/runner.py`: Backtest subprocess execution and artifact collection

**Testing:**
- `polymarket-agent/tests/test_paper_trading.py`: Integration tests for core workflow

**Documentation:**
- `polymarket-agent/README.md`: Complete system guide with CLI reference
- `AI-Trader/README.md`: Platform overview and quick links
- `Vibe-Trading/README.md`: Research platform documentation
- `AI-Trader/docs/api/openapi.yaml`: Full OpenAPI specification
- `AI-Trader/docs/README_AGENT.md`: Agent integration guide
- `AI-Trader/docs/README_USER.md`: End-user guide

## Naming Conventions

**Python Files:**
- All lowercase with underscores: `market_discovery.py`, `price_fetcher.py`, `data_store.py`
- Purpose-driven names matching primary class/function: `strategy.py` contains Kelly criterion
- Test files follow pattern: `test_*.py` (e.g., `test_paper_trading.py`)

**Python Functions:**
- Snake case: `fetch_active_markets()`, `calculate_kelly_criterion()`, `execute_paper_trade()`
- Descriptive verb-noun: `record_trade()`, `upsert_position()`, `check_risk_limits()`
- Private functions prefixed with underscore: `_parse_market()`, `_extract_json_from_response()`
- Boolean functions: `check_*()`, `is_*()`, `has_*()`

**Python Variables:**
- Snake case: `cycle_start`, `remaining_capital`, `estimated_prob`, `kelly_adjusted`
- Constants: UPPERCASE `PRIVATE_KEY`, `MIN_EDGE_THRESHOLD`, `MAX_POSITION_SIZE_USDC`
- Boolean flags: `paper_mode`, `is_paper`, `shutdown_requested`
- Loop variables: Single letter `m` (market), `t` (trade), `pos` (position) for short iterations

**React/TypeScript Files:**
- PascalCase for components: `SwarmDashboard.tsx`, `MessageBubble.tsx`, `Layout.tsx`
- camelCase for utilities/hooks: `useSSE.ts`, `useDarkMode.ts`, `formatters.ts`
- Lowercase with dashes for directories: `components/chat/`, `pages/`, `hooks/`

**React Components:**
- Functional components with hooks
- Props interfaces: `SwarmDashboardProps`, `MessageBubbleProps`
- State management via Zustand for cross-component sharing

**TypeScript Interfaces:**
- PascalCase: `SwarmAgent`, `RunResult`, `BacktestMetrics`
- Suffixed with Props for component props: `SwarmDashboardProps`

**Agent Definitions:**
- Filename matches agent role: `scanner.md`, `analyst.md`, `risk-manager.md`, `strategy-updater.md`
- Schema naming in agent files: `output_schema` with `$id` field

**State Files:**
- `strategy.md`: Evolving trading strategy (markdown)
- `core-principles.md`: Human guardrails (markdown)
- `cycles/{cycle_id}/scanner_output.json`: Scanner agent output
- `cycles/{cycle_id}/analyst_{market_id}.json`: Per-market analysis
- `cycles/{cycle_id}/risk_output.json`: Risk manager assessment
- `cycles/{cycle_id}/trade_plan.json`: Proposed trades
- `cycles/{cycle_id}/execution_results.json`: Trade execution results
- `reports/cycle-{cycle_id}.md`: Cycle report (human-readable)

## Where to Add New Code

**New Trading Strategy Rules:**
- Primary code: Update `state/core-principles.md` (human-written principles)
- Agent implementation: Modify `strategy-updater.md` to expand rules
- Tests: Add validation logic to `lib/strategy.py`

**New Market Analysis Technique:**
- Implementation: Create new sub-agent in `.claude/agents/{technique}.md`
- Integration: Spawn via Task tool in `trading-cycle.md`, add to pipeline
- Output schema: Define JSON schema in agent markdown file

**New Risk Check:**
- Implementation: Add function to `lib/portfolio.py`
- Invocation: Call from risk-manager agent or planner agent
- Configuration: Add max exposure parameter to `.env` and `config.py`

**New CLI Tool:**
- Implementation: Create new file in `tools/{name}.py`
- Pattern: Argument parsing with `argparse`, JSON output via `print(json.dumps(...))`
- Usage: `python tools/{name}.py [args] --pretty` for human-readable output
- Integration: Reference in README.md CLI Tools section

**New API Endpoint (AI-Trader):**
- Implementation: Add route handler to `AI-Trader/service/server/routes.py`
- Request/Response Models: Define Pydantic models in `routes.py`
- Business Logic: Extract to `services.py` if logic is reused
- Database: Add queries to `database.py` if new tables needed
- Testing: Add curl/httpie example in documentation

**New React Component (Vibe-Trading/AI-Trader):**
- Implementation: Create file in `frontend/src/components/{category}/{ComponentName}.tsx`
- Props Interface: Define in same file or `types/` directory
- State: Use Zustand stores in `stores/` if cross-component sharing needed
- Styling: Use Tailwind CSS classes, no separate CSS files
- Hooks: Create custom hooks in `hooks/` directory if logic is reused

**New Backtest Feature (Vibe-Trading):**
- Implementation: Extend `agent/src/core/runner.py` or add to `backtest/runner.py`
- Artifacts: Define new artifact types in runner configuration
- Visualization: Add React component in `frontend/src/components/charts/`
- API: Expose via new endpoint in `agent/api_server.py`

**Utilities/Helpers:**
- Python: `lib/` directory for reusable modules, `tools/` for CLI-specific
- TypeScript: `src/lib/` directory for utilities (formatters, API clients, etc.)
- Shared logic: Extract to separate module if used by multiple components

## Special Directories

**polymarket-agent/state/cycles/{cycle_id}/**
- Purpose: Per-cycle JSON intermediate outputs for audit trail
- Generated: Yes (by sub-agents)
- Committed: No (gitignored; regenerated each cycle)
- Contents: scanner_output.json, analyst_*.json, risk_output.json, trade_plan.json, execution_results.json, reviewer_output.json, strategy_update.json

**polymarket-agent/state/reports/**
- Purpose: Human-readable cycle reports (Markdown)
- Generated: Yes (by reviewer agent)
- Committed: No (gitignored; archive for analysis)
- Pattern: `cycle-{cycle_id}.md` (e.g., `cycle-20260327-143000.md`)

**polymarket-agent/.venv/**
- Purpose: Python virtual environment
- Generated: Yes (`python3.12 -m venv .venv`)
- Committed: No (gitignored)
- Requirements: Installed via `pip install -r requirements.txt`

**Vibe-Trading/frontend/node_modules/, dist/**
- Purpose: npm dependencies and build output
- Generated: Yes (via `npm install` and `npm run build`)
- Committed: No (gitignored)

**AI-Trader/service/frontend/node_modules/, dist/**
- Purpose: npm dependencies and build output
- Generated: Yes
- Committed: No (gitignored)

**.env files (all projects)**
- Purpose: Environment variables and secrets
- Generated: Copy from `.env.example` and edit
- Committed: No (critical — never commit secrets)
- Contents: API keys, trading parameters, database paths, wallet private keys

**trading.db (polymarket-agent)**
- Purpose: SQLite database for trade history, positions, decisions
- Generated: Yes (auto-created on first run)
- Committed: No (gitignored; state database)
- Location: `polymarket-agent/trading.db`

**trading.log (polymarket-agent)**
- Purpose: JSON-formatted trading logs
- Generated: Yes (appended each cycle)
- Committed: No (gitignored)
- Rotation: Configured in logger setup

## Gitignore Pattern

Files typically gitignored (never committed):
- `.env` files (secrets)
- `*.db` files (runtime state)
- `*.log` files (execution logs)
- `.venv/`, `node_modules/`, `dist/`, `build/` (generated)
- `.pytest_cache/`, `__pycache__/` (test artifacts)
- `state/cycles/`, `state/reports/` (cycle outputs)
- `.claude/sessions/`, `.claude/cache/` (Claude runtime)

