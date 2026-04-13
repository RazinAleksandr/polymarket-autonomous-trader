# External Integrations

**Analysis Date:** 2026-04-02

## APIs & External Services

**Polymarket CLOB (Central Limit Order Book):**
- Service: Polymarket decentralized prediction market exchange
- What it's used for: Order placement, cancellation, position management, real-time price feeds for paper trading
- SDK/Client: `py-clob-client` (>=0.17.0)
- Auth: Private key signing (EOA wallet signature required)
- Endpoint: `POLYMARKET_HOST` (default: https://clob.polymarket.com)
- Implementation: `lib/trading.py` handles order creation, signing with `OrderArgs`, posting to CLOB API
- Order format: GTC (Good-Til-Cancel) limit orders with signature_type=0 for EOA wallets

**Gamma API:**
- Service: Polymarket metadata and market discovery API
- What it's used for: Fetching active markets, market metadata (volumes, liquidity, prices), market snapshots
- SDK/Client: `requests` HTTP client (direct REST calls)
- Auth: None (public API)
- Endpoint: `GAMMA_API_URL` (default: https://gamma-api.polymarket.com)
- Implementation: `lib/market_data.py` (`fetch_active_markets()`, `fetch_market_by_id()`)
- Data format: JSON with stringified token IDs and outcome prices requiring `json.loads()` parsing

**OpenAI GPT-4o:**
- Service: Language model for market probability estimation and analysis
- What it's used for: Analyzing market questions, estimating win probabilities, calculating trading edges, generating reasoning for trade decisions
- SDK/Client: OpenAI Python SDK (referenced in legacy code, may need migration)
- Auth: `OPENAI_API_KEY` environment variable
- Feature: Responses API with optional `web_search` tool for real-time data
- Implementation: Market analysis layer uses GPT-4o for probability synthesis

**LangChain + LangGraph:**
- Service: Agent orchestration and state machine framework
- What it's used for: Vibe-Trading multi-agent workflow coordination, skill execution chains, persistent state management
- SDK/Client: `langchain`, `langchain-openai`, `langgraph`, `langgraph-checkpoint`
- Auth: Inherits from OpenAI API key (LangChain-OpenAI integration)
- Implementation: `src/core/runner.py`, `src/providers/llm.py`, `src/core/state.py`

**Data Providers:**
- **Yahoo Finance (yfinance):** Equity market data, historical prices for global stocks
- **Tushare:** Chinese A-share market data, fundamental data, technical analysis
- **Alpha Vantage:** Stock market data, forex, technical indicators (optional, default "demo" key)

## Data Storage

**Databases:**

**SQLite (polymarket-agent):**
- Type/Provider: SQLite3 (embedded, file-based)
- Connection: `DB_PATH` environment variable (default: `trading.db`)
- Client: Python `sqlite3` standard library
- Schema: 5 tables (trades, positions, decisions, market_snapshots, strategy_metrics)
- Location: `lib/db.py` (`DataStore` class)
- Purpose: Trade history audit, position tracking, decision logging, portfolio snapshots

**DuckDB (Vibe-Trading):**
- Type/Provider: DuckDB (embedded columnar database)
- Connection: In-memory or file-based via DuckDB API
- Client: DuckDB Python library
- Purpose: Efficient backtesting queries, historical data analysis, portfolio statistics

**PostgreSQL (AI-Trader optional):**
- Type/Provider: PostgreSQL (when DATABASE_URL set)
- Connection: `DATABASE_URL` environment variable (defaults to SQLite fallback)
- Purpose: Production database for AI-Trader service
- Fallback: SQLite at `DB_PATH` (service/server/data/clawtrader.db) if DATABASE_URL empty

**File Storage:**
- Local filesystem only
- Trading logs: `trading.log` (structured JSON format)
- State files: `state/strategy.md`, `state/core-principles.md` (markdown strategy documentation)
- Cycle artifacts: `state/cycles/{cycle_id}/` directory (JSON outputs from sub-agents)
- Reports: `state/reports/cycle-{cycle_id}.md` (cycle completion reports)

**Caching:**
- None detected (no Redis, Memcached, or similar)
- In-memory state via LangGraph checkpoints (Vibe-Trading)

## Authentication & Identity

**Auth Provider:**
- Custom: Ethereum wallet-based authentication
  - EOA (Externally Owned Account) wallets via private key
  - Polygon mainnet chain ID 137

**Implementation:**
- `eth-account` library for wallet generation and signing
- `web3.py` for Polygon RPC connectivity and transaction signing
- Private key stored in environment: `PRIVATE_KEY` (Ethereum hex string, required for live trading)
- Paper trading mode: No private key required (default safe mode)
- Token approvals: USDC approve, CTF (Conditional Token Framework) setApprovalForAll via `web3.py`

**Session/State Management:**
- LangGraph checkpoints for persistent agent state (Vibe-Trading)
- SQLite position tracking for portfolio continuity (polymarket-agent)
- No JWT or OAuth detected

## Monitoring & Observability

**Error Tracking:**
- None detected (no Sentry, DataDog, or similar external service)
- Error logging goes to file and console

**Logs:**
- File: Structured JSON format written to `LOG_FILE` (default: `trading.log`)
- Console: Human-readable with timestamp, level, module name
- Framework: Python `logging` module with custom `JsonFormatter` in `lib/logging_setup.py`
- Levels: DEBUG, INFO, WARNING, ERROR (configurable via `LOG_LEVEL`)
- Decision logging: Specialized `log_decision()` function for tracking trade decisions with full context

**Metrics:**
- P&L tracking via SQLite `positions` table (unrealized, realized, cost basis)
- Brier score calculation for closed positions (calibration analysis)
- Portfolio snapshots captured in `market_snapshots` table
- Strategy metrics table for tracking performance over time

## CI/CD & Deployment

**Hosting:**
- Local development: Vite dev server (npm run dev) on localhost:5173 or similar
- Production: Self-hosted (no cloud platform required)
  - FastAPI backend runs on Uvicorn (uvicorn[standard] >= 0.24.0)
  - Frontend: Static files served via nginx or FastAPI static middleware
  - Polymarket agent: Scheduled via cron or similar (no native CI detected)

**CI Pipeline:**
- None detected (no GitHub Actions, GitLab CI, or Travis CI configuration)
- Manual testing via pytest or direct script execution
- Potential: `.github/workflows/` directory may exist in Vibe-Trading (not analyzed)

**Scheduling:**
- Bash scripts: `run_cycle.sh`, `schedule_trading.sh` for cron-style execution
- Environment: `CYCLE_INTERVAL` (default: 4h)
- Execution: Direct Python invocation or Claude Code CLI spawning sub-agents

## Environment Configuration

**Required env vars (polymarket-agent):**
- `POLYMARKET_HOST`: CLOB API endpoint (default: https://clob.polymarket.com)
- `GAMMA_API_URL`: Market data endpoint (default: https://gamma-api.polymarket.com)
- `CHAIN_ID`: Polygon chain ID (default: 137)
- `PAPER_TRADING`: Boolean flag (default: true, set false for live)
- `PRIVATE_KEY`: Ethereum private key (required for live trading only)

**Optional env vars (polymarket-agent):**
- `MIN_EDGE_THRESHOLD`: Minimum edge for trades (default: 0.10)
- `KELLY_FRACTION`: Position sizing fraction (default: 0.25)
- `MAX_POSITION_SIZE_USDC`: Per-trade limit (default: 50.0)
- `MAX_TOTAL_EXPOSURE_USDC`: Portfolio limit (default: 200.0)
- `MIN_VOLUME_24H`: Market filter (default: 1000.0)
- `MIN_LIQUIDITY`: Market filter (default: 500.0)
- `LOG_LEVEL`: Logging verbosity (default: INFO)
- `CYCLE_INTERVAL`: Trading cycle frequency (default: 4h)

**Vibe-Trading env vars:**
- `OPENAI_API_KEY`: GPT-4o API key (required for LLM features)
- Data provider keys: `TUSHARE_TOKEN`, Yahoo Finance (implicit via yfinance)
- API endpoints: `ALPHA_VANTAGE_BASE_URL`, `HYPERLIQUID_API_URL`, etc.

**AI-Trader env vars:**
- `ALPHA_VANTAGE_API_KEY`: Stock data provider (default: "demo")
- `POLYMARKET_GAMMA_BASE_URL`, `POLYMARKET_CLOB_BASE_URL`: Market endpoints
- `DATABASE_URL`: PostgreSQL connection (optional, falls back to SQLite)
- `VITE_REFRESH_INTERVAL`: Frontend refresh milliseconds

**Secrets location:**
- `.env` file (never committed, listed in `.gitignore`)
- `PRIVATE_KEY`: Ethereum wallet private key (hex string starting with 0x)
- `OPENAI_API_KEY`: API key from OpenAI dashboard

## Webhooks & Callbacks

**Incoming:**
- None detected (no webhook endpoints for external systems calling back)

**Outgoing:**
- None detected (no outgoing webhook calls to external services)
- Market resolution notifications: Handled via polling in portfolio monitoring (check_for_resolved_markets)

**SSE (Server-Sent Events):**
- `sse-starlette` (>=1.6.0) integrated in Vibe-Trading for real-time streaming
- Used for agent response streaming to frontend clients

## Blockchain Integration

**Network:**
- Polygon mainnet (L2 scaling solution for Ethereum)
- Chain ID: 137
- RPC provider: Web3.py configured to connect to Polygon public RPC

**Token Standard:**
- ERC-20: USDC (stablecoin used for trading)
- ERC-1155: Conditional Tokens (CTF) - outcome tokens for prediction markets

**Transactions:**
- Token approvals: USDC `approve()` for trading contract
- CTF setApprovalForAll: Allow position management
- Order signing: Polymarket uses order signing (not on-chain submission for orders)

---

*Integration audit: 2026-04-02*
