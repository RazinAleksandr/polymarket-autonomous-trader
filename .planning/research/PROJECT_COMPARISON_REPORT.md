# Polymarket Autonomous Trading Agent - Project Comparison Report

> **HISTORICAL DOCUMENT** — This analysis of 3 source projects (polymarket-agent, polymarket_claude, AI-Trader) drove the decision to cherry-pick architecture from one, knowledge from another, and market intelligence from the third. Those decisions are now baked into the current system. Kept for reference on why the architecture looks the way it does.

---

## Executive Summary

Three projects were analyzed for building an autonomous Polymarket trading agent. Each takes a fundamentally different approach:

| Project | Language | Philosophy | Status |
|---------|----------|-----------|--------|
| **polymarket-agent** | Python + Claude Code agents | Self-improving instrument layer + AI agent orchestration | Paper trading, 3+ cycles, 0 live trades |
| **polymarket_claude** | Python + Claude Code skills | Probabilistic discipline + loss-driven learning | Paper trading, 5 trades, -$200 P&L |
| **AI-Trader** | TypeScript/Python (FastAPI + React) | Signal marketplace + copy trading platform | Platform infrastructure, no autonomous trading logic |

---

## 1. POLYMARKET-AGENT (Best for: Agent Architecture & Safety)

### What It Is
A two-layer system: stateless Python CLI tools (instrument layer) + Claude Code multi-agent orchestration (agent layer). Runs hourly cycles through an 8-step pipeline: discover → analyze → risk-check → plan → execute → review → learn → update strategy.

### Architecture Highlights
- **8 specialized sub-agents**: scanner, analyst, risk-manager, planner, reviewer, strategy-updater, position-monitor, outcome-analyzer
- **JSON interchange** between agents with schema validation
- **SQLite database** with 5 tables (trades, positions, decisions, market_snapshots, strategy_metrics)
- **Dual logging**: human-readable console + structured JSON file
- **Tmux + cron** for unattended autonomous operation

### Strengths
1. **Best safety system**: Multi-stage live trading gate (10+ paper cycles, positive P&L, manual "CONFIRM LIVE" confirmation, private key requirement)
2. **Best agent architecture**: Clean separation of concerns, each agent has defined inputs/outputs with JSON schemas
3. **Self-improving strategy**: Agent writes and updates `state/strategy.md` after each cycle (21 learned rules so far)
4. **Realistic paper trading**: Uses actual CLOB orderbook prices, models category-specific fees
5. **Comprehensive test suite**: pytest covering Kelly math, market parsing, order validation, safety gates
6. **Slippage protection**: Hard-learned rule rejects trades if actual price exceeds plan by >5%
7. **Graceful shutdown**: Signal handlers ensure no half-finished cycles
8. **Fee transparency**: Category-specific fee modeling (crypto 1.8%, sports 0.75%, geopolitics 0%)

### Weaknesses
1. **Zero actual trades executed** - 3 consecutive zero-trade cycles due to market availability
2. **Gamma API under-delivery**: Gets ~15 markets when requesting 120 (no pagination)
3. **Over-constrained**: 72h resolution window + 10% edge minimum filters out nearly everything
4. **Sequential analyst**: Markets analyzed one-at-a-time (slow but stable)
5. **Uses OpenAI GPT-4o** for analysis (not Claude) - potential quality gap
6. **No stop-loss, no partial profit-taking**
7. **Small position limits**: $25/trade, $200 portfolio cap

### Key Technical Details
- **Dependencies**: py-clob-client, web3, openai, requests, eth-account
- **APIs**: Gamma API (discovery), CLOB API (execution/pricing)
- **Sizing**: Quarter-Kelly with $25 max per trade
- **Edge threshold**: 10% minimum gross edge

---

## 2. POLYMARKET_CLAUDE (Best for: Trading Knowledge & Strategy)

### What It Is
A knowledge-driven trading system with $10K→$100K goal. Uses layered execution: lightweight Python heartbeat (every 13 min, no LLM) → cron-triggered Claude sessions (scan/resolve/learn/report) → manual deep trading loops.

### Architecture Highlights
- **4 specialized agents**: researcher, evaluator, resolver, synthesizer
- **5-layer knowledge base**: GOLDEN_RULES.md (14 hard rules), category playbooks, strategies inventory, edge sources tracking, learnings archive
- **Heartbeat system**: Pure logic signal generator (no LLM cost) that triggers expensive agent sessions only when needed
- **State via JSON files**: positions.json, bankroll.json, signal.json
- **Per-trade audit files**: Markdown documents with full pre-trade reasoning and post-trade analysis

### Strengths
1. **Best trading knowledge**: 14 golden rules each cited with the specific loss that taught them
2. **Best calibration system**: Tracks stated probability vs actual outcome by category, applies corrections
3. **Best post-mortem discipline**: Every loss triggers immediate analysis with error classification (information/model/calibration/resolution/black swan)
4. **Best category-specific playbooks**: Detailed knowledge for oscars, sports, commodities, politics, crypto
5. **Cost-efficient**: Heartbeat prevents unnecessary LLM calls; scans only when signal.json says needed
6. **Strongest edge identification**: Documents specific market inefficiencies (settlement vs intraday gap, status quo bias, guild predictor drift)
7. **Realistic bankroll management**: $10K starting capital, category caps (politics 3%, sports 4%, etc.)
8. **Bayesian probability framework**: Base rates + evidence updates + market signal blending + uncertainty widening

### Weaknesses
1. **Tiny sample size**: Only 5 trades (1 resolved loss: Oscars -$200)
2. **No live execution**: Paper trading with hardcoded bankroll in JSON
3. **Overcorrection risk**: Single Oscars loss drove massive rule changes (24pp error → 8pp minimum edge for awards)
4. **Temporal gaps**: ~1 hour between scan and execution; prices move
5. **No structured data sources**: Relies on ad-hoc WebSearch, no CME/CFTC/on-chain data
6. **Path hardcoding**: `/root/workspace/polymarket` baked into scripts
7. **No test suite**: Zero automated tests
8. **Manual execution**: No actual order routing to Polymarket

### Key Technical Details
- **Dependencies**: requests, sqlite3, standard library only
- **APIs**: Gamma API (discovery), no CLOB integration
- **Sizing**: Fractional Kelly (1/4 high conf, 1/6 medium, 1/10 low), max 5% bankroll/trade
- **Edge threshold**: 4pp minimum (more aggressive than polymarket-agent's 10%)
- **Unique**: "Settlement != Intraday" insight - systematic edge from commodity settlement mechanics

---

## 3. AI-TRADER (Best for: Platform Infrastructure & Multi-Asset)

### What It Is
A full-stack signal marketplace and copy trading platform for AI agents. FastAPI backend + React frontend. Designed for OpenClaw agent ecosystem, not specifically for autonomous Polymarket trading.

### Architecture Highlights
- **Full-stack web app**: React SPA + FastAPI REST API
- **Multi-asset support**: US stocks, crypto, Polymarket, forex, options, futures
- **Copy trading**: 1:1 automatic position replication across followers
- **Points/rewards system**: Incentivizes signal quality
- **Skill files**: Markdown-based API docs that agents fetch at runtime
- **Dual notification**: WebSocket (realtime) + heartbeat polling (reliable)

### Strengths
1. **Best platform infrastructure**: Production-ready web app with auth, CORS, rate limiting, caching
2. **Best multi-asset support**: Stocks, crypto, predictions unified in one platform
3. **Best data sources**: Alpha Vantage (stocks/news), Hyperliquid (crypto), Polymarket (predictions)
4. **Copy trading mechanism**: Unique among the three projects
5. **Database flexibility**: SQLite dev → PostgreSQL production with abstraction layer
6. **Internationalization**: Full EN/ZH support
7. **Background task system**: Async position updates, profit tracking, Polymarket settlement
8. **Market intelligence**: Macro regime tracking (QQQ/XLP/GLD/UUP), ETF flow analysis, news aggregation

### Weaknesses
1. **NOT an autonomous trader**: It's a platform/marketplace, not a trading agent
2. **No trading strategy or decision logic**: No probability estimation, no edge calculation, no Kelly sizing
3. **No Polymarket order execution**: Only simulated paper positions
4. **No learning loop**: No post-trade analysis, no calibration, no strategy evolution
5. **No test suite**: Zero automated tests for critical trading logic
6. **Paper trading only**: $100K simulated capital, no real money integration
7. **Heavy dependency stack**: React + TypeScript + FastAPI + multiple APIs
8. **Designed for agent marketplace**: Not for a single autonomous trader

### Key Technical Details
- **Backend**: FastAPI 0.109, Pydantic, SQLite/PostgreSQL
- **Frontend**: React 18, TypeScript 5, Recharts, Vite
- **APIs**: Alpha Vantage, Hyperliquid, Polymarket Gamma/CLOB
- **Caching**: In-memory with TTLs (15s-60s for different data types)
- **Rate limiting**: Per-agent cooldowns for posts, replies, price queries

---

## HEAD-TO-HEAD COMPARISON

### Trading Logic & Strategy

| Feature | polymarket-agent | polymarket_claude | AI-Trader |
|---------|-----------------|-------------------|-----------|
| Probability estimation | GPT-4o Bull/Bear debate | Bayesian + base rates + calibration | None |
| Edge calculation | estimated_prob - price - fees | fair_value - market_price (4pp min) | None |
| Position sizing | Quarter-Kelly, $25 max | Fractional Kelly by confidence | Fixed amounts |
| Risk management | $200 portfolio cap, correlation checks | Category caps (2-4%), 5% max/trade | $100K simulated |
| Strategy evolution | Auto-updates strategy.md each cycle | Golden rules + category playbooks | None |
| Calibration tracking | Brier scores on closed positions | Category error tracking with corrections | None |
| Post-trade learning | Outcome analyzer + strategy updater | Post-mortem every loss + synthesis | None |

### Technical Quality

| Feature | polymarket-agent | polymarket_claude | AI-Trader |
|---------|-----------------|-------------------|-----------|
| Test suite | Comprehensive (pytest) | None | None |
| Error handling | Graceful degradation, safe defaults | Bare try/except | Retryable DB errors |
| Logging | Dual format (console + JSON) | stdout only | Rotating file handler |
| Database | SQLite, 5 tables, migrations | SQLite, simple schema | SQLite/PostgreSQL, abstraction |
| Code quality | Clean, typed, dataclasses | Readable but basic | Well-structured, typed |
| Documentation | Excellent (CLAUDE.md) | Good (knowledge/*.md) | Skill files + README |

### Polymarket Integration

| Feature | polymarket-agent | polymarket_claude | AI-Trader |
|---------|-----------------|-------------------|-----------|
| Market discovery | Gamma API with filters | Gamma API with filters | Gamma API (via agents) |
| Orderbook pricing | CLOB API get_price() | None | CLOB API (read-only) |
| Order execution | py-clob-client (paper + live ready) | None (paper only) | None (simulated only) |
| Fee modeling | Category-specific formula | None | None |
| Wallet/signing | web3 + eth-account (EOA) | None | None |
| Token approvals | setup_wallet.py | None | None |

### Autonomous Operation

| Feature | polymarket-agent | polymarket_claude | AI-Trader |
|---------|-----------------|-------------------|-----------|
| Scheduling | Cron + tmux + PID locking | Cron + heartbeat + ralph-wiggum | Background tasks only |
| Cycle management | Full 8-step pipeline per cycle | Scan/resolve/learn/report sessions | No cycle concept |
| Unattended operation | Yes (run_cycle.sh + schedule) | Yes (cron-triggered sessions) | Requires external agents |
| State persistence | SQLite + JSON + markdown reports | JSON files + trade markdown | Database + caching |
| Self-improvement | Strategy.md auto-updated | Golden rules + calibration | None |

---

## WHAT TO TAKE FROM EACH PROJECT

### From polymarket-agent (Architecture & Safety)
1. **Agent orchestration pattern**: 8 specialized agents with JSON schemas - clean, testable, composable
2. **Live trading gate**: Multi-stage verification before real money (10 cycles + positive P&L + manual confirm)
3. **Instrument layer design**: Stateless CLI tools that output JSON to stdout - perfect for agent consumption
4. **Test suite**: Comprehensive pytest coverage of critical trading math
5. **CLOB API integration**: Full order execution pipeline with credential management and retry logic
6. **Fee modeling**: Category-specific Polymarket fee calculation
7. **Slippage protection**: Pre-execution price verification
8. **Graceful shutdown**: Signal handlers for clean cycle termination
9. **Cycle state management**: Per-cycle directories with all intermediate JSON artifacts

### From polymarket_claude (Trading Knowledge & Strategy)
1. **Golden Rules framework**: Hard-coded rules with citations to the loss that taught each one
2. **Calibration system**: Track stated vs actual probability by category, apply corrections to future trades
3. **Post-mortem discipline**: Mandatory loss analysis with error classification taxonomy
4. **Category playbooks**: Deep domain knowledge per market type (settlement mechanics, status quo bias, etc.)
5. **Heartbeat pattern**: Cheap logic-only checks trigger expensive LLM sessions only when needed
6. **Edge source tracking**: Document WHERE edge comes from, not just that edge exists
7. **Bayesian probability framework**: Base rates + evidence + market blending + uncertainty widening
8. **Strategy lifecycle**: TESTING → WINNING → UNDERPERFORMING → RETIRED with promotion criteria
9. **4pp minimum edge**: More practical than 10% - captures more opportunities while covering costs
10. **Settlement vs Intraday insight**: Reproducible edge from understanding resolution mechanics

### From AI-Trader (Platform & Data)
1. **Market intelligence system**: Macro regime tracking, ETF flows, news aggregation - enriches analysis
2. **Multi-source price data**: Alpha Vantage + Hyperliquid + Polymarket - redundancy and breadth
3. **Database abstraction**: SQLite for dev, PostgreSQL for prod - clean migration path
4. **Background task architecture**: Async position updates, profit tracking, settlement checking
5. **Rate limiting patterns**: Per-agent cooldowns prevent API abuse
6. **Profit history compaction**: Full resolution for 24h, 15-min buckets for older data
7. **WebSocket + polling dual notification**: Reliability where it matters

---

## RECOMMENDED BEST SYSTEM ARCHITECTURE

### Core Design: Combine polymarket-agent's architecture with polymarket_claude's trading knowledge

```
Best Autonomous Polymarket Trader
├── Instrument Layer (from polymarket-agent)
│   ├── Market discovery (Gamma API + pagination fix)
│   ├── Orderbook pricing (CLOB API)
│   ├── Order execution (py-clob-client, paper + live)
│   ├── Fee calculation (category-specific)
│   ├── Portfolio tracking (SQLite)
│   └── Wallet management (web3 + eth-account)
│
├── Knowledge Layer (from polymarket_claude)
│   ├── Golden Rules (hard constraints with loss citations)
│   ├── Category Playbooks (market-type-specific knowledge)
│   ├── Edge Source Registry (where edge actually comes from)
│   ├── Calibration System (stated vs actual tracking)
│   ├── Strategy Inventory (lifecycle: testing→winning→retired)
│   └── Post-Mortem Framework (mandatory loss analysis)
│
├── Agent Layer (from polymarket-agent, enhanced)
│   ├── Scanner → uses category playbooks for filtering
│   ├── Analyst → Bayesian framework from polymarket_claude
│   ├── Risk Manager → Kelly + category caps + correlation
│   ├── Planner → trade plan with slippage protection
│   ├── Executor → CLOB API with live gate
│   ├── Reviewer → cycle analysis with calibration updates
│   ├── Strategy Updater → golden rules + strategy evolution
│   └── Outcome Analyzer → Brier scores + post-mortems
│
├── Intelligence Layer (from AI-Trader)
│   ├── Market news aggregation (Alpha Vantage)
│   ├── Macro regime tracking (QQQ/XLP/GLD/UUP)
│   ├── Multi-source pricing (Alpha Vantage + Hyperliquid)
│   └── Background data refresh tasks
│
├── Scheduling Layer (combined best)
│   ├── Heartbeat (from polymarket_claude) - cheap signal checks
│   ├── Cron cycles (from polymarket-agent) - tmux + PID lock
│   ├── Graceful shutdown (from polymarket-agent) - signal handlers
│   └── Background tasks (from AI-Trader) - async data refresh
│
└── Safety Layer (from polymarket-agent, enhanced)
    ├── Paper trading default
    ├── Live gate (10 cycles + positive P&L + manual confirm)
    ├── Slippage protection (5% max deviation)
    ├── Category caps (from polymarket_claude)
    ├── Portfolio limits + correlation checks
    └── Immutable core principles (read-only by agents)
```

### Key Configuration Changes from Current Projects
1. **Lower edge threshold**: 4-6pp (from polymarket_claude) not 10% (polymarket-agent) - captures more opportunities
2. **Wider resolution window**: 7-14 days (not 72h) - dramatically increases market availability
3. **Larger position sizes**: $50-100/trade with $500-1000 portfolio (scale up from polymarket-agent's $25/$200)
4. **Use Claude for analysis**: Not GPT-4o - better reasoning for probability estimation
5. **Fix Gamma API pagination**: Implement proper offset/cursor to get full market inventory
6. **Add market intelligence**: Macro context from AI-Trader improves analysis quality
7. **Implement heartbeat**: Don't waste LLM calls when no action needed (from polymarket_claude)

### Priority Implementation Order
1. **Phase 1**: Instrument layer (polymarket-agent tools) + knowledge base (polymarket_claude)
2. **Phase 2**: Agent orchestration with Bayesian analysis + calibration
3. **Phase 3**: Scheduling + heartbeat + autonomous cycling
4. **Phase 4**: Market intelligence integration
5. **Phase 5**: Live trading gate + real money deployment
