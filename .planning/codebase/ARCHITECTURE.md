# Architecture

**Analysis Date:** 2026-04-02

## Pattern Overview

**Overall:** Multi-layered trading ecosystem with three independent projects (polymarket-agent, AI-Trader, Vibe-Trading) each following layered architecture patterns:

1. **polymarket-agent**: Two-tier system (Instrument Layer + Agent Layer) with strict separation between stateless CLI tools and autonomous Claude agents
2. **AI-Trader**: FastAPI backend + React frontend monolith with background task orchestration
3. **Vibe-Trading**: Modular research platform with Python agent backend + React frontend, emphasizing reproducible backtest execution and result visualization

**Key Characteristics:**
- Stateless tools + stateful coordination (polymarket-agent)
- Clear separation between API routes, business logic, and data persistence
- Domain-driven data flow with JSON-based inter-layer communication
- Async/concurrent processing for market analysis and backtesting
- Event-driven UI updates via Server-Sent Events (SSE) and WebSockets

## Layers

**Configuration & Runtime:**
- Purpose: Centralized parameter management, wallet initialization, environment setup
- Location: `config.py` (polymarket-agent), `.env` files with environment variable loading
- Contains: API keys, trading parameters (MIN_EDGE_THRESHOLD, KELLY_FRACTION, MAX_POSITION_SIZE_USDC), wallet secrets, database paths
- Depends on: `python-dotenv`, `eth-account`, `web3.py`
- Used by: All modules load from config on startup
- Pattern: Single-source-of-truth via environment variables; never committed to git

**Data Persistence:**
- Purpose: SQLite storage for trades, positions, decisions, market snapshots, strategy metrics
- Location: `lib/db.py` (polymarket-agent), `database.py` (AI-Trader)
- Contains: 5 tables in polymarket-agent (trades, positions, decisions, market_snapshots, strategy_metrics); multi-table schema in AI-Trader for agents, signals, discussions, leaderboards, polymarket positions
- Depends on: `sqlite3` (stdlib), connection pooling via concurrent access guards
- Used by: trader.py, portfolio.py, strategy.py for audit trail and position tracking
- Key methods: `record_trade()`, `upsert_position()`, `get_open_positions()`, `update_position_prices()`

**External Integration:**
- Purpose: Fetch market data, pricing, and analysis from external APIs
- Location: `lib/market_data.py` (Gamma API), `lib/pricing.py` (CLOB API), `price_fetcher.py` (AI-Trader)
- Contains: HTTP clients for Gamma API (market discovery), CLOB API (orderbook), web3.py (blockchain), OpenAI API (probability estimation)
- Depends on: `requests`, `py-clob-client`, `web3`, `openai`
- Used by: Market discovery, price fetching, analysis steps
- Pattern: API clients return dataclass instances (Market, OrderResult) for type safety

**Market Analysis:**
- Purpose: Generate probability estimates and trade signals using Claude Code agents (polymarket-agent) or GPT-4o (polymarket_claude legacy)
- Location: `.claude/agents/` (polymarket-agent sub-agents: scanner, analyst, risk-manager, planner, reviewer, strategy-updater)
- Contains: Sub-agent definitions with JSON output schemas, structured reasoning prompts, probability synthesis logic
- Depends on: Claude Code API, OpenAI API with web search tool for research
- Used by: Central trading cycle orchestrator
- Pattern: Sequential pipeline with JSON-based handoff between agents; each agent validates output schema before next step

**Trade Execution:**
- Purpose: Execute trades via CLOB API (live) or record locally (paper); manage order signing and fee modeling
- Location: `lib/trading.py` (polymarket-agent), `execute_trade.py` CLI tool
- Contains: Order validation (price range 0-1, minimum notional), paper fill logic (use best ask from CLOB), live order signing via eth-account, fee calculation per market category
- Depends on: `py-clob-client`, `eth-account`, `lib/fees.py`
- Used by: Execute step in trading cycle, direct trade execution from CLI
- Pattern: Pluggable paper/live mode via PAPER_TRADING config; all trades logged to SQLite for audit

**Portfolio Management:**
- Purpose: Track open positions, calculate unrealized P&L, detect resolved markets, enforce risk limits
- Location: `lib/portfolio.py` (polymarket-agent)
- Contains: Position tracking via positions table, unrealized P&L calculation from live Gamma API prices, resolution detection via market.closed flag
- Depends on: `lib/db.py`, `lib/market_data.py`, `lib/fees.py`
- Used by: Post-execution monitoring, risk checks, capital allocation
- Pattern: Stateless functions that query DB and Gamma API, return summary dict with positions and stats

**UI/Frontend:**
- Purpose: Real-time visualization of trading cycles, agent orchestration, backtest runs, portfolio management
- Location: `Vibe-Trading/frontend/src/` (React), `AI-Trader/service/frontend/`
- Contains: Components for chat interface (MessageBubble, ConversationTimeline, SwarmDashboard), charts (EquityChart, CandlestickChart), agent status monitoring, trading activity feeds
- Depends on: React 19, React Router 7, Zustand (state), Tailwind CSS, ECharts/Recharts (charting)
- Used by: Browser clients connecting via Vite dev server or production build
- Pattern: Component-based architecture; Zustand for lightweight state management; SSE/WebSocket for real-time updates from backend

**API Gateway:**
- Purpose: RESTful endpoints for agent operations, backtest execution, market data, trading, portfolio, leaderboards, discussions
- Location: `AI-Trader/service/server/routes.py`, `Vibe-Trading/agent/api_server.py`
- Contains: FastAPI route definitions, Pydantic models for request/response validation, WebSocket handlers for streaming
- Depends on: `fastapi`, `pydantic`, `uvicorn`, background task scheduling via asyncio
- Used by: Frontend clients, external CLI tools, agent coordination
- Pattern: RESTful endpoints with async handlers; middleware for CORS, logging, rate limiting

**Async Task Orchestration:**
- Purpose: Run background jobs for portfolio updates, market settlement, data snapshots, report generation
- Location: `AI-Trader/service/server/tasks.py`
- Contains: Async functions for position price updates, profit history recording, Polymarket settlement, snapshots of market news/macro signals/ETF flows/stock analysis
- Depends on: `asyncio`, database connections, API clients
- Used by: FastAPI startup event, continuous execution in event loop
- Pattern: Fire-and-forget async tasks that loop indefinitely with configurable intervals

**Agent Coordination:**
- Purpose: Orchestrate multi-agent trading cycles with sequential/parallel execution control
- Location: `.claude/agents/` definitions, invoked via `Task` tool in Claude Code
- Contains: Agent definitions (markdown files) with prompts, output schemas, error handling
- Depends on: Claude Code CLI, Python tools available via Bash
- Used by: Central trading cycle controller
- Pattern: Task-based spawning with sequential execution for analysts (avoid race conditions), parallel for other agents

## Data Flow

**Trading Cycle (polymarket-agent):**

1. **Initialization** → Load strategy.md, core-principles.md, recent reports from state/
2. **Position Monitor** → Check open positions for sell signals (optional, non-blocking)
3. **Market Scanner** → Discover active markets from Gamma API, output to scanner_output.json
4. **Sweet-Spot Filtering** → Filter by price range (0.15-0.85), remove existing positions, rank by volume
5. **Market Analysis** → Sequential analyst agents per market, output analyst_{market_id}.json
6. **Risk Manager** → Evaluate risk, size positions with Kelly criterion, output risk_output.json
7. **Planner** → Create trade plan from analysis + risk assessment, output trade_plan.json
8. **Execute Trades** → Run execute_trade.py for each trade, record to execution_results.json
9. **Reviewer** → Analyze cycle outcomes, write cycle-{cycle_id}.md report
10. **Strategy Updater** → Incrementally update strategy.md based on learnings

All intermediate outputs written to `state/cycles/{cycle_id}/` for audit trail.

**AI-Trader Backend Data Flow:**

1. **API Request** → FastAPI route handler
2. **Database Query** → Fetch agent/signal/position data
3. **Background Task** → Async update of prices, profits, market settlement
4. **Response** → JSON via FastAPI or streaming via SSE
5. **WebSocket** → Real-time event broadcasting to connected clients

**State Management (Vibe-Trading):**

- Frontend state managed via Zustand stores (`src/stores/agent.ts`)
- Backend session state via FastAPI session variables
- Backtest run results persisted as artifacts (CSV, JSON files)
- Real-time updates via SSE streaming from `/run/{runId}/events` endpoint

## Key Abstractions

**Market (dataclass):**
- Purpose: Represents a prediction market with pricing and metadata
- Examples: `lib/models.Market` with 25 fields (id, question_text, yes_token_id, no_token_id, yes_price, no_price, volume_24h, liquidity, end_date, category, active, closed, neg_risk, order_min_size, tick_size)
- Pattern: Immutable data container; created by parsing Gamma API response in `market_discovery.py`, passed through analysis → strategy → execution
- Used by: All downstream analysis and execution steps

**TradeSignal (dataclass):**
- Purpose: Output of signal generation with sizing and justification
- Examples: `lib/models.TradeSignal` with 11 fields (market_id, question, side, token_id, price, size, cost_usdc, edge, kelly_raw, kelly_adjusted, confidence, reasoning)
- Pattern: Product of strategy module; contains all info needed for trade execution; passed to trader.execute_signal()
- Usage: Logged to decisions table, included in trade_plan.json for planner review

**OrderResult (dataclass):**
- Purpose: Outcome of trade execution (paper or live)
- Examples: `lib/models.OrderResult` with 4 fields (order_id, success, message, is_paper)
- Pattern: Returned from execute_signal(); determines if position recorded; used in execution_results.json

**SwarmAgent (TypeScript interface):**
- Purpose: Tracks status of concurrent agents in real-time UI
- Examples: `Vibe-Trading/frontend/src/components/chat/SwarmDashboard.tsx` with fields (id, status, tool, iters, startedAt, elapsed, lastText, summary)
- Pattern: Updated via SSE events; UI renders color-coded agent status bars with timing and iteration count

## Entry Points

**polymarket-agent - Trading Cycle:**
- Location: `.claude/agents/trading-cycle.md` or called via `claude run a trading cycle` CLI
- Triggers: User command, cron job from `schedule_trading.sh`, or manual `./run_cycle.sh`
- Responsibilities: Orchestrate 8-step pipeline, spawn sub-agents, execute trades, write reports
- Safety gates: Paper trading default, live gate requires 10+ cycles with positive P&L, manual "CONFIRM LIVE" prompt

**polymarket-agent - CLI Tools:**
- Location: `tools/` directory (discover_markets.py, get_prices.py, calculate_kelly.py, execute_trade.py, get_portfolio.py, check_resolved.py)
- Triggers: Direct Python invocation with argument parsing
- Responsibilities: Stateless operations — fetch markets, price, execute trades, calculate risk metrics, check portfolio
- Output: JSON to stdout (add `--pretty` for human-readable)

**polymarket-agent - Wallet Setup:**
- Location: `setup_wallet.py`
- Triggers: One-time before live trading (`python setup_wallet.py`)
- Responsibilities: Generate/import Ethereum wallet, derive L2 API credentials, set token allowances
- Output: `.env` updated with PRIVATE_KEY

**AI-Trader - Backend Server:**
- Location: `AI-Trader/service/server/main.py`
- Triggers: `python main.py` or via uvicorn deployment
- Responsibilities: Initialize FastAPI app, load database, spawn background tasks, serve routes
- Startup: Register position update, profit history, Polymarket settlement, snapshot tasks

**AI-Trader - Frontend:**
- Location: `AI-Trader/service/frontend/` (Vite React app)
- Triggers: Browser navigation to `localhost:5173` (dev) or production build
- Responsibilities: Render trading dashboard, agent signals, copy trading UI, leaderboards

**Vibe-Trading - API Server:**
- Location: `Vibe-Trading/agent/api_server.py`
- Triggers: `python api_server.py` or FastAPI deployment
- Responsibilities: Serve backtest runs, artifact streaming, session management, SSE events
- Key endpoints: `/runs/{runId}`, `/runs/{runId}/events`, `/upload`, `/analyze/{runId}`

**Vibe-Trading - MCP Server:**
- Location: `Vibe-Trading/agent/mcp_server.py`
- Triggers: Claude Code integration via MCP protocol
- Responsibilities: Expose backtest execution, artifact reads, file I/O as tools for Claude agents

**Vibe-Trading - Frontend:**
- Location: `Vibe-Trading/frontend/` (Vite React app)
- Triggers: Browser navigation
- Responsibilities: Display agent runs, backtests, comparisons, equity curves

## Error Handling

**Strategy:** Graceful degradation — fail fast at validation, continue with partial results

- **Market Discovery Failure:** Log error, return empty list, skip cycle (proceed to reviewer)
- **Single Market Analysis Failure:** Log per-market error, skip that market, continue with others
- **Risk Manager Failure:** Log error, skip cycle (skip to reviewer)
- **Trade Execution Failure:** Log per-trade, mark as failed, continue with remaining trades
- **Portfolio Update Failure:** Log warning, cycle continues (state persisted to DB)
- **Sub-agent JSON Parse Failure:** Log error, skip that agent step, continue
- **Position Monitor Failure:** Non-blocking; log warning, proceed to Step 1

Pattern: Try-except at each stage; log with full context; central reviewer always runs for cycle closure.

## Cross-Cutting Concerns

**Logging:**
- Framework: Python `logging` module (polymarket-agent), FastAPI logging (AI-Trader)
- Dual output: Console (human-readable) + JSON file (machine-parseable for analysis)
- Levels: INFO (progress), WARNING (non-blocking issues), ERROR (failures with fallback)
- Trade decisions logged to SQLite decisions table for full audit trail

**Configuration Management:**
- Source: `.env` files via `python-dotenv`
- Never committed to git; `.env.example` provides template
- All parameters loaded at startup via `config.py`
- Trade parameters (MIN_EDGE_THRESHOLD, KELLY_FRACTION, MAX_POSITION_SIZE_USDC) read from config

**Validation:**
- Order validation: price ∈ (0, 1), notional ≥ $5 minimum, size rounded to 2 decimals
- Market selection: volume ≥ MIN_VOLUME_24H, liquidity ≥ MIN_LIQUIDITY
- Position sizing: Kelly criterion with configurable fraction (default 0.25 for conservative), respects MAX_POSITION_SIZE_USDC
- Sub-agent outputs: JSON schema validation before downstream consumption

**Graceful Shutdown:**
- Signal handlers: SIGINT, SIGTERM trigger controlled cleanup (close DB, finalize logs)
- PID lockfile prevents overlapping cycles
- Each cycle is atomic — either fully completes or fails with comprehensive report

**Safety Gates (Live Trading):**
- Paper trading always default (PAPER_TRADING=true)
- Live gate requires: ≥10 completed paper cycles, positive aggregate P&L, manual "CONFIRM LIVE" confirmation
- Gate implementation: `.live-gate-pass` file created only after interactive confirmation

