# Requirements: Autonomous Polymarket Trading Agent

**Defined:** 2026-04-03
**Core Value:** Claude autonomously trades Polymarket, learns from outcomes, and evolves its own strategy

## v1 Requirements

### Agent Architecture

- [ ] **ARCH-01**: Sub-agent directory (.claude/agents/) deleted — no scanner, analyst, risk-manager, planner, reviewer, strategy-updater, position-monitor, outcome-analyzer
- [ ] **ARCH-02**: Six skill reference docs created in .claude/skills/ — evaluate-edge, size-position, resolution-parser, post-mortem, calibration-check, cycle-review
- [ ] **ARCH-03**: CLAUDE.md rewritten as single autonomous trader with phases A-E (check positions, find opportunities, analyze markets, size and execute, learn and evolve)
- [ ] **ARCH-04**: Claude can read and modify its own CLAUDE.md to improve its process based on trading outcomes
- [ ] **ARCH-05**: Settings.json configured to allow bash, file read/write/edit, web search for autonomous operation

### Knowledge Base

- [x] **KNOW-01**: knowledge/golden-rules.md created with 14 seed rules transplanted from polymarket_claude (loss-cited, categorized: pre-trade, sizing, research, post-trade)
- [x] **KNOW-02**: knowledge/market-types/ directory with 6 category playbooks (crypto, politics, sports, commodities, entertainment, finance) with base rates, edge sources, resolution mechanics
- [x] **KNOW-03**: knowledge/calibration.json initialized as empty seed structure that Claude populates after each trade resolution
- [x] **KNOW-04**: lib/calibration.py implements Brier score calculation, category accuracy tracking, calibration corrections
- [x] **KNOW-05**: knowledge/strategies.md with strategy lifecycle framework (TESTING → PERFORMING → UNDERPERFORMING → RETIRED)
- [x] **KNOW-06**: knowledge/edge-sources.md with edge tracking (Confirmed, Testing, Failed, Hypothesized sections)

### Self-Modifying Strategy

- [x] **STRAT-01**: state/strategy.md rewritten as minimal seed that Claude builds from scratch through trading experience
- [x] **STRAT-02**: state/core-principles.md simplified to only true immutable guardrails (paper default, 5% max, live gate, no deletion, record-before-confirm, 5-loss pause, 30% max exposure)
- [x] **STRAT-03**: Claude writes cycle reports to state/reports/ after every trading cycle
- [x] **STRAT-04**: Claude updates golden-rules.md with new rules learned from losses (with trade citation)
- [x] **STRAT-05**: Claude updates calibration.json after every trade resolution with Brier score and category accuracy
- [x] **STRAT-06**: Claude evolves category playbooks in market-types/*.md based on trading experience
- [x] **STRAT-07**: Claude makes 0-3 strategy changes maximum per cycle to prevent drift

### Python Tools

- [x] **TOOL-01**: lib/market_intel.py implements macro regime detection (QQQ, XLP, GLD, UUP from Alpha Vantage), crypto Fear & Greed index, category news sentiment
- [x] **TOOL-02**: tools/get_market_intel.py CLI wrapper returns JSON with macro_regime, fear_greed, top_news, etf_flows, signals
- [x] **TOOL-03**: tools/record_outcome.py CLI records trade outcome to calibration database, returns brier_score and error_pp
- [x] **TOOL-04**: scripts/heartbeat.py checks timestamps and positions, writes state/signal.json with scan_needed, resolve_needed, learn_needed flags
- [x] **TOOL-05**: All 167 existing tests continue passing after changes
- [x] **TOOL-06**: New tests written for calibration.py and market_intel.py

### Configuration

- [x] **CONF-01**: .env modified — remove OPENAI_API_KEY, add ALPHA_VANTAGE_API_KEY
- [x] **CONF-02**: Config widened — MAX_RESOLUTION_DAYS=14 (was 3), MIN_EDGE_THRESHOLD=0.04 (was 0.10)
- [x] **CONF-03**: Position sizing changed to bankroll percentage (was fixed $25/$200)
- [x] **CONF-04**: lib/config.py updated with new config fields, backward compatible

### Scheduling & Automation

- [x] **SCHED-01**: Cron job: heartbeat.py runs every 10 minutes (zero LLM cost)
- [x] **SCHED-02**: Cron job: run_cycle.sh runs every 30 minutes, gated by heartbeat signals
- [x] **SCHED-03**: Cron job: daily forced full scan + learn at 2 AM UTC
- [x] **SCHED-04**: run_cycle.sh has PID locking (prevent concurrent cycles), tmux session management, 20-minute timeout
- [x] **SCHED-05**: Claude runs autonomously via cron with --dangerously-skip-permissions flag

### Safety & Validation

- [x] **SAFE-01**: Paper trading is default mode — no live trades without explicit gate pass
- [x] **SAFE-02**: enable_live.py checks gate criteria: ≥10 paper cycles, positive P&L, >50% win rate, operator confirmation
- [x] **SAFE-03**: Maximum 5% of bankroll on any single position (enforced in core-principles.md)
- [x] **SAFE-04**: Maximum 30% of bankroll in open positions at any time
- [x] **SAFE-05**: 5 consecutive losses triggers automatic 24-hour trading pause
- [x] **SAFE-06**: All trades recorded in database BEFORE confirming execution
- [x] **SAFE-07**: Cycle reports and calibration history cannot be deleted by Claude

### Paper Trading Validation

- [ ] **VAL-01**: System runs 20+ autonomous paper trading cycles without human intervention
- [ ] **VAL-02**: Claude demonstrates strategy evolution (strategy.md grows with evidence-backed changes)
- [ ] **VAL-03**: Calibration.json shows accuracy tracking across categories
- [ ] **VAL-04**: Golden-rules.md expands with new rules from actual trading outcomes
- [x] **VAL-05**: Live trading gate mechanism is built and verifiable (even though paper-only for now)

## v2 Requirements

### Live Trading

- **LIVE-01**: Funded Polygon wallet with USDC for live trading
- **LIVE-02**: Live order execution via py-clob-client with real money
- **LIVE-03**: Scale-up bankroll management as track record proves out

### Monitoring Dashboard

- **DASH-01**: Web UI showing portfolio, P&L, cycle history
- **DASH-02**: Real-time cycle status and strategy evolution visualization
- **DASH-03**: Calibration charts by category

### Advanced Analysis

- **ADV-01**: Bull/Bear adversarial debate structure from Vibe-Trading
- **ADV-02**: Cross-reference with Metaculus/Manifold prediction markets
- **ADV-03**: Context compression for long trading sessions

## Out of Scope

| Feature | Reason |
|---------|--------|
| React frontend / dashboard | CLI-only for v1 — monitoring via logs and state files |
| Live money deployment | Paper trading focus — wallet funding deferred |
| Multi-agent architecture | Single session by design — sub-agents fragment intelligence |
| OpenAI/GPT-4o integration | Claude IS the AI — no Python LLM wrappers needed |
| Vibe-Trading/AI-Trader frontend code | Ideas borrowed, code not ported |
| Mobile app | Not applicable for autonomous trading agent |
| Backtesting framework | Not in design doc — forward-looking paper trading validates instead |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ARCH-01 | Phase 1 | Pending |
| ARCH-02 | Phase 1 | Pending |
| ARCH-03 | Phase 1 | Pending |
| ARCH-04 | Phase 1 | Pending |
| ARCH-05 | Phase 1 | Pending |
| KNOW-01 | Phase 2 | Complete |
| KNOW-02 | Phase 2 | Complete |
| KNOW-03 | Phase 2 | Complete |
| KNOW-04 | Phase 3 | Complete |
| KNOW-05 | Phase 2 | Complete |
| KNOW-06 | Phase 2 | Complete |
| STRAT-01 | Phase 2 | Complete |
| STRAT-02 | Phase 2 | Complete |
| STRAT-03 | Phase 5 | Complete |
| STRAT-04 | Phase 5 | Complete |
| STRAT-05 | Phase 5 | Complete |
| STRAT-06 | Phase 5 | Complete |
| STRAT-07 | Phase 5 | Complete |
| TOOL-01 | Phase 3 | Complete |
| TOOL-02 | Phase 3 | Complete |
| TOOL-03 | Phase 3 | Complete |
| TOOL-04 | Phase 3 | Complete |
| TOOL-05 | Phase 3 | Complete |
| TOOL-06 | Phase 3 | Complete |
| CONF-01 | Phase 4 | Complete |
| CONF-02 | Phase 4 | Complete |
| CONF-03 | Phase 4 | Complete |
| CONF-04 | Phase 4 | Complete |
| SCHED-01 | Phase 6 | Complete |
| SCHED-02 | Phase 6 | Complete |
| SCHED-03 | Phase 6 | Complete |
| SCHED-04 | Phase 4 | Complete |
| SCHED-05 | Phase 6 | Complete |
| SAFE-01 | Phase 2 | Complete |
| SAFE-02 | Phase 6 | Complete |
| SAFE-03 | Phase 2 | Complete |
| SAFE-04 | Phase 2 | Complete |
| SAFE-05 | Phase 2 | Complete |
| SAFE-06 | Phase 2 | Complete |
| SAFE-07 | Phase 2 | Complete |
| VAL-01 | Phase 6 | Pending |
| VAL-02 | Phase 6 | Pending |
| VAL-03 | Phase 6 | Pending |
| VAL-04 | Phase 6 | Pending |
| VAL-05 | Phase 6 | Complete |

**Coverage:**
- v1 requirements: 42 total
- Mapped to phases: 42
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-03*
*Last updated: 2026-04-03 after roadmap creation*
