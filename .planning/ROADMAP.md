# Roadmap: Polymarket Autonomous Trading Agent v2 (Single Agent)

## Overview

Transform the working multi-agent trading system into a single autonomous Claude trader that reads its own knowledge base, makes all decisions in one session, and evolves its strategy through experience. The existing 11 CLI tools and SQLite persistence are kept as-is -- we restructure how Claude operates (single agent, skills, knowledge files) and add new tools for calibration tracking and market intelligence. Each phase delivers something independently verifiable before the next begins.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Single Agent Architecture** - Replace sub-agent pipeline with single autonomous trader session and skill reference docs
- [ ] **Phase 2: Knowledge Base** - Transplant battle-tested knowledge from polymarket_claude and seed Claude's learning files
- [ ] **Phase 3: New Instrument Tools** - Market intelligence, calibration tracking, heartbeat signal generator
- [ ] **Phase 4: Config and Integration** - Remove OpenAI dependency, widen parameters, heartbeat-gated cycle launcher
- [ ] **Phase 5: Autonomous Cycle Validation** - Manual validation cycles proving single-agent behavior works end-to-end
- [ ] **Phase 6: Scheduling and Paper Validation** - Heartbeat-gated cron, extended autonomous paper trading, live gate enhancement

## Phase Details

### Phase 1: Single Agent Architecture
**Goal**: Claude operates as one autonomous trader per session -- no sub-agent spawning -- loading skill reference documents on demand to guide analysis, sizing, and learning
**Depends on**: Nothing (first phase)
**Requirements**: ARST-01, ARST-02, ARST-03, ARST-04, ARST-05
**Success Criteria** (what must be TRUE):
  1. The `.claude/agents/` directory no longer exists and no code references sub-agent spawning via Task tool
  2. Running `ls .claude/skills/` shows 6 skill documents (evaluate-edge.md, size-position.md, resolution-parser.md, post-mortem.md, calibration-check.md, cycle-review.md) each containing a structured analytical framework
  3. The `.claude/CLAUDE.md` file describes a 5-phase trading cycle (Check Positions, Find Opportunities, Analyze Markets, Size and Execute, Learn and Evolve) with explicit instructions for Claude to read strategy.md, core-principles.md, and last 3 cycle reports at session start
  4. Claude Code session launched with the new CLAUDE.md can read files, execute bash commands, search the web, and write/edit files without permission errors
**Plans**: TBD

### Phase 2: Knowledge Base
**Goal**: Claude starts every session with transplanted trading wisdom -- battle-tested rules from real losses, category-specific playbooks, and accuracy tracking structures -- rather than learning everything from zero
**Depends on**: Phase 1
**Requirements**: KNOW-01, KNOW-02, KNOW-03, KNOW-04, KNOW-05, KNOW-06, KNOW-07
**Success Criteria** (what must be TRUE):
  1. `knowledge/golden-rules.md` contains 10+ rules each citing a specific trade or loss that motivated the rule, organized by Pre-Trade, Sizing, Research, and Post-Trade sections
  2. `knowledge/market-types/` contains playbooks for at least 5 categories (crypto, politics, sports, commodities, entertainment) each with base rates, edge sources, resolution mechanics, and category-specific rules
  3. `knowledge/calibration.json` is valid JSON with global and per-category structure; `knowledge/strategies.md` and `knowledge/edge-sources.md` have lifecycle/tracking frameworks ready for Claude to populate
  4. `state/strategy.md` contains only section headers (Market Selection, Analysis Approach, Risk Parameters, Trade Entry/Exit Rules, What I've Learned, Change Log) with no pre-seeded rules -- Claude writes all content
  5. `state/core-principles.md` contains only immutable guardrails (paper default, max position %, gate requirements, no history deletion) and nothing Claude should be able to evolve
**Plans**: TBD

### Phase 3: New Instrument Tools
**Goal**: Claude has Python CLI tools for macro market intelligence and calibration tracking that existing tools lack, plus a lightweight heartbeat script for scheduling
**Depends on**: Phase 1
**Requirements**: TOOL-01, TOOL-02, TOOL-03, TOOL-04, TOOL-05, TOOL-06
**Success Criteria** (what must be TRUE):
  1. Running `python tools/get_market_intel.py --category crypto` returns JSON with macro regime, sentiment indicators, and recent news; running with `--overview` returns cross-category summary
  2. Running `python tools/record_outcome.py --market-id X --stated-prob 0.65 --actual WIN --category crypto` returns JSON with Brier score and error in percentage points, and appends to calibration database
  3. Running `python scripts/heartbeat.py` reads local state files (no API calls, no LLM) and writes `state/signal.json` with action flags (scan_needed, resolve_needed, learn_needed) based on timestamp staleness and position status
  4. All existing tests pass (`pytest tests/` exits 0) with no regressions from new code additions
**Plans**: TBD

### Phase 4: Config and Integration
**Goal**: The system no longer depends on OpenAI for analysis, trading parameters are widened for Claude's broader analytical capability, and the cycle launcher respects heartbeat signals
**Depends on**: Phase 3
**Requirements**: CONF-01, CONF-02, CONF-03, CONF-04
**Success Criteria** (what must be TRUE):
  1. No Python import of `openai` exists anywhere in the codebase; `.env.example` does not list OPENAI_API_KEY; Claude performs all market analysis directly
  2. `.env.example` lists ALPHA_VANTAGE_API_KEY and new widened parameters (MAX_RESOLUTION_DAYS=14, MIN_EDGE_THRESHOLD=0.04, position sizing as bankroll percentage)
  3. Running `scripts/run_cycle.sh` when `state/signal.json` contains `{"scan_needed": false, "resolve_needed": false, "learn_needed": false}` exits immediately without launching a Claude session
  4. Running `scripts/run_cycle.sh` when `state/signal.json` contains any true flag launches a Claude session that reads the appropriate context for that signal type
**Plans**: TBD

### Phase 5: Autonomous Cycle Validation
**Goal**: Claude runs complete trading cycles as a single agent -- scanning markets, analyzing with web search, sizing positions, executing trades, writing reports, and updating its own strategy -- proving the architecture works before automation
**Depends on**: Phase 2, Phase 4
**Requirements**: AVAL-01, AVAL-02, AVAL-03
**Success Criteria** (what must be TRUE):
  1. A manually triggered cycle produces: a cycle report in `state/reports/`, updated `state/strategy.md` with Claude's own observations, and (if trades were taken) entries in the SQLite database -- all from one Claude session without sub-agent spawning
  2. Claude's cycle report references specific knowledge base content (golden rules applied, calibration data checked, category playbook consulted) showing it reads and uses its own knowledge
  3. After 5+ manual cycles, Claude has added at least one new rule to golden-rules.md or updated calibration.json based on observed outcomes, demonstrating the self-improvement loop works
**Plans**: TBD

### Phase 6: Scheduling and Paper Validation
**Goal**: The system runs unattended via heartbeat-gated cron, accumulates 20+ paper trading cycles with measurable calibration improvement, and the live trading gate checks calibration health before allowing real money
**Depends on**: Phase 5
**Requirements**: SCHD-01, SCHD-02, SCHD-03, SCHD-04
**Success Criteria** (what must be TRUE):
  1. Crontab shows heartbeat running every 10 minutes and trading cycle running every 30 minutes; a daily forced full cycle runs at the configured time; `state/signal.json` is updated by heartbeat without any LLM API calls
  2. After 20+ autonomous cycles: `knowledge/calibration.json` has per-category accuracy data, `knowledge/golden-rules.md` has rules beyond the initial seed, and `state/strategy.md` contains evidence-backed trading decisions written by Claude
  3. Running `python tools/enable_live.py --check` verifies calibration health (no category worse than -20pp error) in addition to existing cycle count and P&L requirements; the gate blocks live trading if calibration is unhealthy
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6
(Phase 2 and Phase 3 can execute in parallel after Phase 1)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Single Agent Architecture | 0/TBD | Not started | - |
| 2. Knowledge Base | 0/TBD | Not started | - |
| 3. New Instrument Tools | 0/TBD | Not started | - |
| 4. Config and Integration | 0/TBD | Not started | - |
| 5. Autonomous Cycle Validation | 0/TBD | Not started | - |
| 6. Scheduling and Paper Validation | 0/TBD | Not started | - |
