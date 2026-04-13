# Technology Stack

**Analysis Date:** 2026-04-02

## Languages

**Primary:**
- Python 3.12.9 - Polymarket agent trading logic, market analysis, portfolio management, database operations
- Python 3.11+ - Vibe-Trading agent with LangGraph orchestration, backtesting, MCP server
- JavaScript/TypeScript - Frontend UIs for AI-Trader and Vibe-Trading dashboards

**Secondary:**
- Bash - Trading cycle orchestration scripts, environment setup
- YAML - Configuration for Vibe-Trading swarm agents and trading strategies

## Runtime

**Environment:**
- Python 3.12.9 (polymarket-agent primary)
- Python 3.11+ (Vibe-Trading)
- Node.js/npm (frontend applications)

**Package Managers:**
- pip (Python)
- npm (Node.js frontend packages)

**Lockfiles:**
- `requirements.txt` in polymarket-agent and Vibe-Trading (pinned versions)
- `package.json` with dependencies for all frontend projects
- `pyproject.toml` for Vibe-Trading (setuptools-based packaging)

## Frameworks

**Core:**
- py-clob-client (>=0.17.0) - Polymarket CLOB API client for order placement, position management, market data
- LangChain (>=0.1.0) - Agent orchestration in Vibe-Trading
- LangGraph (>=0.2.50, <0.3) - State machine for multi-agent workflows
- FastAPI (>=0.104.0) - REST API server in Vibe-Trading agent

**Frontend:**
- React (^19.0.0 in Vibe-Trading, ^18.2.0 in AI-Trader) - UI framework
- Vite (^6.0.0 in Vibe-Trading, ^5.0.8 in AI-Trader) - Build tool and dev server
- TypeScript (^5.7.0 in Vibe-Trading, ^5.2.2 in AI-Trader) - Type safety

**Testing:**
- pytest (via trading.db schema and test discovery)
- LangChain testing utilities (integrated in Vibe-Trading)

**Build/Dev:**
- Vite (build bundler, dev server)
- Autoprefixer (^10.4.0) - CSS vendor prefixes
- PostCSS (^8.4.0) - CSS transformation

## Key Dependencies

**Critical:**

- **py-clob-client** (>=0.17.0) - Core trading execution; signs and posts orders to Polymarket CLOB API; handles L2 credentials
- **web3** (>=7.0.0) - Ethereum/Polygon wallet interaction, token approvals, USDC transfers for live trading
- **eth-account** (>=0.13.0) - Wallet generation, account management, private key signing for EOA transactions
- **requests** (>=2.31.0) - HTTP client for Gamma API (market discovery), Polymarket CLOB API pricing
- **pandas** (>=2.0.0) - Data manipulation for backtesting and analysis in Vibe-Trading
- **numpy** (>=1.24.0) - Numerical computing for price calculations and portfolio metrics
- **LangChain** (>=0.1.0) - LLM integration backbone for Vibe-Trading agents
- **langchain-openai** (>=0.0.5) - OpenAI GPT integration for market analysis

**Infrastructure:**

- **SQLite3** (standard library) - Local database for trade history, positions, decisions, market snapshots in polymarket-agent
- **DuckDB** (>=1.2.0) - Columnar analytics engine for efficient backtesting queries
- **FastAPI** (>=0.104.0) - REST API server for Vibe-Trading agent and trade endpoints
- **Uvicorn** (>=0.24.0) - ASGI server for FastAPI
- **python-dotenv** (>=1.0.0) - Environment variable loading from .env files
- **pydantic** (>=2.0.0) - Data validation and settings management
- **sse-starlette** (>=1.6.0) - Server-sent events for real-time streaming responses
- **fastmcp** (>=2.0.0) - Model Context Protocol server for Vibe-Trading MCP integration

**Data/Analysis:**

- **yfinance** (>=0.2.30) - Yahoo Finance data provider for stock prices
- **tushare** (>=1.2.89) - Chinese stock market data (A-shares)
- **scikit-learn** (>=1.3.0) - Machine learning models for signal generation
- **scipy** (>=1.10.0) - Statistical functions for calibration and probability analysis
- **joblib** (>=1.3.0) - Parallel computation for backtesting
- **smartmoneyconcepts** (>=0.0.1) - Smart money trading concepts (technical analysis)
- **pyharmonics** (>=1.5.0) - Harmonic pattern detection for trading

**Frontend:**

- **ethers** (^6.10.0) - Ethereum interaction for AI-Trader frontend (wallet connection)
- **react-router-dom** (^7.1.0 in Vibe-Trading, ^6.21.0 in AI-Trader) - Client-side routing
- **recharts** (^3.8.0) - Charting library for financial visualizations
- **echarts** (^6.0.0) - Advanced charting in Vibe-Trading frontend
- **zustand** (^5.0.0) - Lightweight state management
- **tailwindcss** (^3.4.0) - Utility-first CSS framework
- **react-markdown** (^9.0.0) - Markdown rendering in Vibe-Trading UI

## Configuration

**Environment:**
- Configuration via `.env` file (must exist, never committed) in each project
- Managed through:
  - `lib/config.py` in polymarket-agent (loads via python-dotenv)
  - Pydantic models in Vibe-Trading agent (validates environment settings)
  - `.env.example` files document all required and optional variables

**Build:**
- `vite.config.ts` in both frontend projects (Vite dev/build configuration)
- `tsconfig.json` for TypeScript compilation
- `pyproject.toml` in Vibe-Trading (packaging metadata, tool configuration)
- `ruff` linter configured in Vibe-Trading's `pyproject.toml` (target: Python 3.11, line-length 120)

## Platform Requirements

**Development:**
- Python 3.12.9 (polymarket-agent) or 3.11+ (Vibe-Trading)
- Node.js with npm (for frontend development)
- Virtual environment for Python projects (`.venv/` in polymarket-agent)
- SQLite3 (included in Python stdlib)
- Git for version control
- Bash shell for orchestration scripts

**Production:**
- Python 3.12.9 runtime with pip installed packages
- Polygon mainnet chain ID: 137 (Polygon L2 for Polymarket)
- Internet connectivity for:
  - Polymarket CLOB API (https://clob.polymarket.com)
  - Gamma API (https://gamma-api.polymarket.com)
  - External data providers (yfinance, tushare)
  - OpenAI API (if using GPT-4o for analysis)
- Web server (Node.js + Vite/FastAPI for serving frontend, or reverse proxy like nginx)
- Persistent storage for SQLite database files and log files

**Network/APIs:**
- OPENAI_API_KEY for market probability analysis (GPT-4o with web search)
- PRIVATE_KEY for live trading on Polygon (Ethereum private key)
- Alpha Vantage API key (optional, default "demo")

---

*Stack analysis: 2026-04-02*
