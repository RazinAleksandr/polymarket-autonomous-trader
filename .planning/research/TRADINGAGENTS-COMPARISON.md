# TradingAgents vs Polymarket-Trader: Full Comparison

Comparison of `/home/trader/polymarket-trader/` (our production system) with `/home/trader/TradingAgents/` (TauricResearch multi-agent framework, arXiv 2412.20138).

Date: 2026-04-12

---

## What Each Project Is

- **polymarket-trader** — Production autonomous trading agent for Polymarket prediction markets. Actually executes paper trades, runs on cron unattended, learns from results. Python + Claude Code CLI.
- **TradingAgents** — Research framework for stock market analysis. Multi-agent LLM debate system that produces Buy/Hold/Sell recommendations. No execution. LangGraph + multi-provider LLM support.

---

## Architecture

- **polymarket-trader:** Two layers — Python instrument layer (14 CLI tools in `tools/`) + Claude Code agent layer (single agent following `.claude/CLAUDE.md`, loading 6 skill docs as decision frameworks). Linear 5-phase cycle: check positions → find opportunities → analyze → size/execute → learn.
- **TradingAgents:** LangGraph state machine with 10+ specialized LLM agents in 4 teams. Agents communicate via shared graph state. Multi-step pipeline with configurable debate rounds.

---

## Agent Design

- **polymarket-trader:** Single Claude Code session runs the whole cycle. No sub-agents. Uses `.claude/skills/` as decision frameworks.
- **TradingAgents:** 10+ agents with distinct roles:
  - 4 Analysts (Market, Social Media, News, Fundamentals) — gather data via tools
  - 3 Researchers (Bull, Bear, Manager) — structured adversarial debate
  - 1 Trader — synthesizes debate into action
  - 3 Risk Analysts (Aggressive, Conservative, Neutral) + Portfolio Manager — risk debate
  - Configurable debate rounds (default: 1 round bull/bear, 1 round risk)

---

## Markets & Data Sources

- **polymarket-trader:** Polymarket prediction markets (binary YES/NO). Data from Gamma API (discovery, metadata), CLOB API (orderbook, pricing). Claude's WebSearch for real-time evidence.
- **TradingAgents:** US/international equities. Data from yfinance or Alpha Vantage (OHLCV, fundamentals, income statements, balance sheets, news, insider transactions). Technical indicators (MACD, RSI, Bollinger, SMA, EMA, ATR, VWMA). No web search.

---

## Math & Quantitative Analysis

**polymarket-trader:**
- Kelly criterion with quarter-Kelly fraction for position sizing
- Edge calculation: `estimated_prob - market_price - fees`
- Brier score calibration per category with auto-corrections
- Category-specific fee modeling (12 fee schedules)
- Correlation-adjusted sizing (0.5 factor)
- Hard limits: 5% per position, 30% total exposure, category caps

**TradingAgents:**
- Technical indicators (MACD, RSI, Bollinger, ATR, VWMA)
- No Kelly criterion, no position sizing, no edge calculation
- No calibration or Brier tracking
- No fee modeling
- Risk is qualitative debate, not quantitative metrics
- Output: 5-tier rating (Buy/Overweight/Hold/Underweight/Sell) — no dollar amounts

---

## Web Search & Research

- **polymarket-trader:** Claude's built-in WebSearch during Phase C. Structured bull/bear research per market. Cites real sources (FanDuel, Al Jazeera, CBS). Sportsbook odds de-vigged across 3+ sources.
- **TradingAgents:** No web search. Analysts use API tools (yfinance, Alpha Vantage) for structured data only. News from API feeds only.

---

## Strategy Evolution & Learning

**polymarket-trader:**
- `state/strategy.md` — updated 0-3 times per cycle with evidence from real trades
- `knowledge/golden-rules.md` — 17 rules from losses >2% bankroll
- `knowledge/calibration.json` — per-category Brier scores, auto-corrections
- `knowledge/market-types/{category}.md` — category-specific lessons
- Fully autonomous learning — no human input needed

**TradingAgents:**
- BM25-based memory retrieval (lexical matching via `rank-bm25`)
- 5 separate memory instances (bull/bear researchers, trader, judge, portfolio manager)
- Learning requires manual `reflect_and_remember(returns)` call
- Lessons stored as (situation, recommendation) pairs
- Not autonomous — human triggers reflection and provides returns data

---

## Execution

- **polymarket-trader:** Paper mode with realistic orderbook fills (best ask/bid). Live mode via py-clob-client on Polygon. 4-criteria safety gate. Running: 30+ autonomous cycles, 7 real paper trades.
- **TradingAgents:** No execution — recommendation only. No paper trading. No live trading. Backtrader dependency listed but never used.

---

## Scheduling & Autonomy

- **polymarket-trader:** Fully autonomous via cron — heartbeat/10min, full cycle/2h, forced daily/2AM. PID lockfile, 20-min timeout. Zero human intervention.
- **TradingAgents:** Single-shot analysis via `ta.propagate("NVDA", "2026-01-15")`. No scheduling, no continuous operation.

---

## Data Persistence

- **polymarket-trader:** SQLite (7 tables), markdown cycle reports, JSON calibration/bankroll. Full append-only audit trail.
- **TradingAgents:** JSON state logs per analysis. In-memory BM25 index (lost on restart). No database.

---

## Testing

- **polymarket-trader:** 24 pytest modules — Kelly math, market data, calibration, safety gates, scheduling, strategy evolution.
- **TradingAgents:** 3 test files — model validation, ticker handling, API key validation. No execution or backtesting tests.

---

## LLM Provider Support

- **polymarket-trader:** Claude only (via Claude Code CLI).
- **TradingAgents:** OpenAI, Anthropic, Google, xAI, OpenRouter, Ollama. Extended thinking support. Configurable per-agent.

---

## Summary Comparison

| Dimension | polymarket-trader | TradingAgents |
|-----------|-------------------|---------------|
| Purpose | Production autonomous trader | Research analysis framework |
| Markets | Prediction markets (Polymarket) | Equities (stocks) |
| Execution | Paper + live trading | None (recommendations only) |
| Agents | 1 agent, 6 skill docs | 10+ specialized agents |
| Debate | Single-agent bull/bear research | Multi-agent adversarial debate |
| Position sizing | Kelly criterion, category caps | None |
| Risk mgmt | Quantitative limits + correlation | Qualitative agent debate |
| Calibration | Brier scores, auto-correction | None |
| Web search | Yes (real-time) | No (API data feeds only) |
| Learning | Fully autonomous | Manual trigger required |
| Scheduling | Cron, fully autonomous | Single-shot, manual |
| Persistence | SQLite + markdown + JSON | JSON logs, in-memory BM25 |
| LLM providers | Claude only | OpenAI, Anthropic, Google, xAI, Ollama |
| Testing | 24 test modules | 3 test files |
| Proven | 30+ live cycles, real P&L | Academic paper, no live results |

---

## Key Strengths Each Has That the Other Lacks

**TradingAgents has, polymarket-trader lacks:**
- Structured multi-agent adversarial debate (bull vs bear with explicit counter-arguments)
- BM25 memory system for retrieving past similar situations
- Structured reflection framework for extracting lessons post-trade
- Multi-provider LLM support

**polymarket-trader has, TradingAgents lacks:**
- Actual trade execution (paper + live)
- Kelly criterion position sizing with fees
- Brier calibration tracking with auto-corrections
- Autonomous scheduling and unattended operation
- Web search for real-time evidence
- Safety gates and risk limits
- Full audit trail (SQLite + markdown)
- Comprehensive test suite
