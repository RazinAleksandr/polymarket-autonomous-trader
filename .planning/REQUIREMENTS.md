# Requirements: Polymarket Autonomous Trading Agent v2 (Single Agent)

**Defined:** 2026-04-03
**Core Value:** Claude operates as a single autonomous trader that reads its own knowledge base, makes all trading decisions, and evolves its own strategy -- no sub-agent pipeline, no human intervention between scheduled cycles.

## v1 Requirements

Requirements for v2 single-agent release. Each maps to roadmap phases.

### Agent Restructure

- [ ] **ARST-01**: Delete `.claude/agents/` directory (8 sub-agent files) and replace multi-agent pipeline with single-agent session architecture
- [ ] **ARST-02**: Create `.claude/skills/` directory with 6 skill reference documents that Claude loads on demand during analysis (evaluate-edge, size-position, resolution-parser, post-mortem, calibration-check, cycle-review)
- [ ] **ARST-03**: Rewrite `.claude/CLAUDE.md` as single autonomous trader instructions covering 5 cycle phases (Check Positions, Find Opportunities, Analyze Markets, Size and Execute, Learn and Evolve)
- [ ] **ARST-04**: Verify `.claude/settings.json` allows bash execution, file read/write/edit, and web search tools
- [ ] **ARST-05**: Single agent reads `state/strategy.md`, `state/core-principles.md`, and last 3 cycle reports at session start before any trading decisions

### Knowledge Base

- [ ] **KNOW-01**: Transplant `knowledge/golden-rules.md` from polymarket_claude with 10+ battle-tested rules including loss citations
- [ ] **KNOW-02**: Create `knowledge/market-types/` with 5+ category playbooks (crypto, politics, sports, commodities, entertainment) transplanted from polymarket_claude
- [ ] **KNOW-03**: Create `knowledge/calibration.json` as empty seed structure that Claude fills with accuracy data per category after each trade resolution
- [ ] **KNOW-04**: Create `knowledge/strategies.md` with strategy lifecycle tracking (PERFORMING, TESTING, UNDERPERFORMING, RETIRED statuses)
- [ ] **KNOW-05**: Create `knowledge/edge-sources.md` for tracking where profitable edge comes from (Confirmed, Testing, Failed, Hypothesized)
- [ ] **KNOW-06**: Rewrite `state/strategy.md` as minimal seed document (section headers only) that Claude builds from scratch through trading experience
- [ ] **KNOW-07**: Simplify `state/core-principles.md` to only true immutable guardrails (max 5% per position, paper default, gate requirements, no deletion of history)

### New Instrument Tools

- [ ] **TOOL-01**: `lib/market_intel.py` fetches macro regime, news sentiment, and market signals from external APIs (Alpha Vantage, Fear and Greed)
- [ ] **TOOL-02**: `tools/get_market_intel.py` CLI wrapper returns macro context JSON for a given category or market overview
- [ ] **TOOL-03**: `lib/calibration.py` tracks prediction accuracy per category with Brier scores, calculates calibration corrections
- [ ] **TOOL-04**: `tools/record_outcome.py` CLI tool records trade outcome to calibration database and returns accuracy metrics (Brier score, error in percentage points)
- [ ] **TOOL-05**: `scripts/heartbeat.py` lightweight Python script (no LLM calls) that checks timestamps and positions, writes `state/signal.json` with action flags (scan_needed, resolve_needed, learn_needed)
- [ ] **TOOL-06**: All existing 11 CLI tools continue to pass their tests after restructuring; no regressions in existing functionality

### Config and Integration

- [ ] **CONF-01**: Remove OpenAI API dependency from analysis pipeline (Claude replaces GPT-4o for all market analysis)
- [ ] **CONF-02**: Add Alpha Vantage API key configuration for market intelligence tool
- [ ] **CONF-03**: Widen trading parameters: MAX_RESOLUTION_DAYS from 3 to 14, MIN_EDGE_THRESHOLD from 0.10 to 0.04, position sizing as bankroll percentage instead of fixed dollar amount
- [ ] **CONF-04**: Enhance `scripts/run_cycle.sh` to check `state/signal.json` before launching Claude session (heartbeat gating -- skip if no signals)

### Autonomous Validation

- [ ] **AVAL-01**: Run first autonomous cycle where Claude reads knowledge base, uses skills for analysis, makes trade decisions, writes cycle report, and updates strategy.md -- all in one session without sub-agents
- [ ] **AVAL-02**: Claude makes contextual decisions that reference its knowledge base (e.g., "passing on this edge because my calibration in this category is poor") rather than following fixed rules
- [ ] **AVAL-03**: After 5+ manual validation cycles, all tool integration issues are resolved and cycle completion rate is above 90%

### Scheduling and Operations

- [ ] **SCHD-01**: Heartbeat cron runs every 10 minutes writing signal.json; trading cycle cron runs every 30 minutes gated by heartbeat signals
- [ ] **SCHD-02**: Daily forced full cycle at configurable time (default 2 AM UTC) regardless of heartbeat signals
- [ ] **SCHD-03**: After 20+ autonomous paper cycles: calibration.json populated, golden-rules.md expanded with new rules from real experiences, strategy.md contains evidence-backed decisions
- [ ] **SCHD-04**: Live trading gate verifies calibration health (no category worse than -20pp error) in addition to existing cycle count and P&L requirements

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Analysis

- **ANLZ-01**: Market timing-to-resolution scoring (prefer markets with resolution within analysis horizon)
- **ANLZ-02**: Liquidity depth analysis before order placement
- **ANLZ-03**: Enhanced market filtering heuristics based on accumulated trading data

### Operations

- **OPS-01**: Multi-exchange support (Kalshi, Metaculus)
- **OPS-02**: Automated performance dashboards
- **OPS-03**: Context compression for long sessions (from Vibe-Trading pattern)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Web UI / dashboard | CLI/file-based only. Markdown reports are the visibility layer. |
| Real-time streaming / WebSocket feeds | Batch-cycle architecture. Snapshots at cycle start are sufficient. |
| Backtesting engine | Paper trading IS the validation environment. |
| Human approval per trade | Eliminates autonomous value. Knowledge files provide transparency. |
| Reinforcement learning / model fine-tuning | Strategy document evolution replaces ML infrastructure. |
| Sub-agent pipeline | Single-agent architecture -- Claude sees everything in one session. |
| OpenAI / GPT-4o dependency | Claude IS the AI. No external LLM needed. |
| Cross-exchange arbitrage | Extreme complexity for marginal gain. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ARST-01 | Phase 1 | Pending |
| ARST-02 | Phase 1 | Pending |
| ARST-03 | Phase 1 | Pending |
| ARST-04 | Phase 1 | Pending |
| ARST-05 | Phase 1 | Pending |
| KNOW-01 | Phase 2 | Pending |
| KNOW-02 | Phase 2 | Pending |
| KNOW-03 | Phase 2 | Pending |
| KNOW-04 | Phase 2 | Pending |
| KNOW-05 | Phase 2 | Pending |
| KNOW-06 | Phase 2 | Pending |
| KNOW-07 | Phase 2 | Pending |
| TOOL-01 | Phase 3 | Pending |
| TOOL-02 | Phase 3 | Pending |
| TOOL-03 | Phase 3 | Pending |
| TOOL-04 | Phase 3 | Pending |
| TOOL-05 | Phase 3 | Pending |
| TOOL-06 | Phase 3 | Pending |
| CONF-01 | Phase 4 | Pending |
| CONF-02 | Phase 4 | Pending |
| CONF-03 | Phase 4 | Pending |
| CONF-04 | Phase 4 | Pending |
| AVAL-01 | Phase 5 | Pending |
| AVAL-02 | Phase 5 | Pending |
| AVAL-03 | Phase 5 | Pending |
| SCHD-01 | Phase 6 | Pending |
| SCHD-02 | Phase 6 | Pending |
| SCHD-03 | Phase 6 | Pending |
| SCHD-04 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 29 total
- Mapped to phases: 29
- Unmapped: 0

---
*Requirements defined: 2026-04-03*
*Last updated: 2026-04-03 — all 29 requirements mapped to 6 phases*
