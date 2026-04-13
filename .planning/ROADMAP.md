# Roadmap: Autonomous Polymarket Trading Agent

## Overview

Transform the working multi-agent trading system (polymarket-agent/) into a single autonomous Claude trader that reads its own knowledge base, makes all decisions in one session, and evolves its strategy through experience. Existing 11 CLI tools and SQLite persistence are kept — we restructure how Claude operates and add new tools for calibration and market intelligence.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Single Agent Architecture** — Replace sub-agent pipeline with single autonomous trader session and skill reference docs (completed 2026-04-03)
- [x] **Phase 2: Knowledge Base & Safety** — Transplant battle-tested knowledge, seed learning files, establish immutable guardrails (completed 2026-04-04)
- [x] **Phase 3: New Instrument Tools** — Market intelligence, calibration tracking, heartbeat signal generator, tests (completed 2026-04-04)
- [x] **Phase 4: Config & Integration** — Remove OpenAI dependency, widen parameters, heartbeat-gated cycle launcher (completed 2026-04-04)
- [x] **Phase 5: Autonomous Cycle Validation** — Manual cycles proving single-agent architecture works end-to-end with self-improvement (completed 2026-04-05)
- [x] **Phase 6: Scheduling & Paper Validation** — Cron automation, 11 autonomous cycles (root bug ate 5 days), live gate with calibration health (completed 2026-04-09)

## Phase Details

### Phase 1: Single Agent Architecture
**Goal**: Claude operates as one autonomous trader per session — no sub-agent spawning — loading skill reference documents on demand to guide analysis, sizing, and learning
**Depends on**: Nothing (first phase)
**Requirements**: ARCH-01, ARCH-02, ARCH-03, ARCH-04, ARCH-05
**Success Criteria** (what must be TRUE):
  1. `.claude/agents/` directory no longer exists and no code references sub-agent spawning via Task tool
  2. `.claude/skills/` contains 6 skill documents (evaluate-edge.md, size-position.md, resolution-parser.md, post-mortem.md, calibration-check.md, cycle-review.md) each containing a structured analytical framework
  3. `.claude/CLAUDE.md` describes a 5-phase trading cycle (Check Positions, Find Opportunities, Analyze Markets, Size and Execute, Learn and Evolve) with explicit instructions for Claude to read its knowledge base at session start
  4. Claude Code session launched with the new CLAUDE.md can read files, execute bash, search the web, and write/edit files without permission errors
  5. CLAUDE.md includes explicit permission for Claude to modify its own CLAUDE.md to improve process
**Plans:** 2/2 plans complete
Plans:
- [x] 01-01-PLAN.md — Copy repo, remove sub-agents, create 3 analysis-phase skill docs
- [x] 01-02-PLAN.md — Create 3 learning-phase skill docs, rewrite CLAUDE.md, configure settings.json

### Phase 2: Knowledge Base & Safety
**Goal**: Claude starts every session with transplanted trading wisdom — battle-tested rules, category playbooks, accuracy tracking — and immutable safety guardrails that it cannot override
**Depends on**: Phase 1
**Requirements**: KNOW-01, KNOW-02, KNOW-03, KNOW-05, KNOW-06, STRAT-01, STRAT-02, SAFE-01, SAFE-03, SAFE-04, SAFE-05, SAFE-06, SAFE-07
**Success Criteria** (what must be TRUE):
  1. `knowledge/golden-rules.md` contains 14+ rules citing specific trades/losses, organized by Pre-Trade, Sizing, Research, Post-Trade
  2. `knowledge/market-types/` contains 6 category playbooks (crypto, politics, sports, commodities, entertainment, finance) with base rates, edge sources, resolution mechanics
  3. `knowledge/calibration.json` is valid JSON seed; `knowledge/strategies.md` and `knowledge/edge-sources.md` have lifecycle frameworks ready for Claude to populate
  4. `state/strategy.md` contains only section headers — no pre-seeded rules (Claude writes all content)
  5. `state/core-principles.md` contains only immutable guardrails (paper default, 5% max position, 30% max exposure, live gate, no deletion, record-before-confirm, 5-loss pause)
**Plans:** 3/3 plans complete
Plans:
- [x] 02-01-PLAN.md — Golden rules, calibration seed, strategy and edge-source frameworks
- [x] 02-02-PLAN.md — 6 category playbooks (crypto, politics, sports, commodities, entertainment, finance)
- [x] 02-03-PLAN.md — Archive strategy, reset strategy.md, rewrite core-principles as immutable guardrails

### Phase 3: New Instrument Tools
**Goal**: Market intelligence, calibration tracking, and heartbeat signal tools — the new capabilities the existing codebase lacks
**Depends on**: Phase 1
**Requirements**: KNOW-04, TOOL-01, TOOL-02, TOOL-03, TOOL-04, TOOL-05, TOOL-06
**Success Criteria** (what must be TRUE):
  1. `python tools/get_market_intel.py --category crypto` returns JSON with macro regime, sentiment, news; `--overview` returns cross-category summary
  2. `python tools/record_outcome.py --market-id X --stated-prob 0.65 --actual WIN --category crypto` returns JSON with Brier score and error_pp, appends to calibration DB
  3. `python scripts/heartbeat.py` reads local state (no API/LLM calls), writes `state/signal.json` with scan_needed, resolve_needed, learn_needed flags
  4. `lib/calibration.py` computes Brier scores and tracks per-category accuracy
  5. All 167 existing tests pass with no regressions; new tests cover calibration.py and market_intel.py
**Plans:** 3/3 plans complete
Plans:
- [x] 03-01-PLAN.md — Calibration library (lib/calibration.py) + record_outcome.py CLI + DB table + tests
- [x] 03-02-PLAN.md — Market intelligence library (lib/market_intel.py) + get_market_intel.py CLI + tests
- [x] 03-03-PLAN.md — Heartbeat signal generator (scripts/heartbeat.py) + full regression suite

### Phase 4: Config & Integration
**Goal**: Remove OpenAI dependency, widen parameters for Claude's broader capability, integrate heartbeat-gated cycle launching
**Depends on**: Phase 3
**Requirements**: CONF-01, CONF-02, CONF-03, CONF-04, SCHED-04
**Success Criteria** (what must be TRUE):
  1. No `import openai` anywhere in codebase; `.env.example` lists ALPHA_VANTAGE_API_KEY instead of OPENAI_API_KEY
  2. Widened parameters: MAX_RESOLUTION_DAYS=14, MIN_EDGE_THRESHOLD=0.04, position sizing as bankroll percentage
  3. `run_cycle.sh` exits immediately when signal.json has all-false flags; launches Claude when any flag is true
  4. `run_cycle.sh` has PID locking, tmux session management, and 20-minute timeout
**Plans:** 2/2 plans complete
Plans:
- [x] 04-01-PLAN.md — Config overhaul: percentage-based sizing, bankroll.json, OpenAI removal
- [x] 04-02-PLAN.md — Heartbeat-gated cycle launcher (run_cycle.sh)

### Phase 5: Autonomous Cycle Validation
**Goal**: Prove the single-agent architecture works end-to-end — Claude scans markets, analyzes with web search, trades, writes reports, and updates its own strategy
**Depends on**: Phase 2, Phase 4
**Requirements**: STRAT-03, STRAT-04, STRAT-05, STRAT-06, STRAT-07
**Success Criteria** (what must be TRUE):
  1. A manually triggered cycle produces: cycle report in state/reports/, strategy.md updates, DB entries — all from one Claude session
  2. Cycle report references knowledge base (golden rules applied, calibration checked, playbook consulted)
  3. After 5+ manual cycles, Claude has added new rules or updated calibration from observed outcomes
  4. Claude makes 0-3 changes per cycle (drift prevention working)
  5. Claude evolves at least one category playbook based on trading experience
**Plans:** 3/3 plans complete
Plans:
- [x] 05-01-PLAN.md — CLAUDE.md Phase B/E updates, discovery tuning, fix broken test
- [x] 05-02-PLAN.md — validate_cycle.py CLI tool with per-cycle and summary validation modes
- [x] 05-03-PLAN.md — Execute 5+ manual cycles, collect evidence, human verification

### Phase 6: Scheduling & Paper Validation
**Goal**: Unattended cron operation, 20+ autonomous paper cycles with calibration improvement, and live gate that checks calibration health
**Depends on**: Phase 5
**Requirements**: SCHED-01, SCHED-02, SCHED-03, SCHED-05, SAFE-02, VAL-01, VAL-02, VAL-03, VAL-04, VAL-05
**Success Criteria** (what must be TRUE):
  1. Crontab: heartbeat every 10min, cycle every 30min, daily forced scan at 2 AM UTC
  2. After 20+ cycles: calibration.json populated, golden-rules.md expanded, strategy.md evidence-backed
  3. `python tools/enable_live.py --check` verifies calibration health (no category > -20pp) plus existing gate criteria
  4. Live gate blocks trading if calibration unhealthy (even if P&L and win rate pass)
  5. System runs unattended for 2+ days producing cycle reports without intervention

## Progress

**Execution Order:**
Phases 1 → (2 + 3 in parallel) → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Single Agent Architecture | 2/2 | Complete | 2026-04-03 |
| 2. Knowledge Base & Safety | 3/3 | Complete | 2026-04-04 |
| 3. New Instrument Tools | 3/3 | Complete | 2026-04-04 |
| 4. Config & Integration | 2/2 | Complete | 2026-04-04 |
| 5. Autonomous Cycle Validation | 3/3 | Complete | 2026-04-05 |
| 6. Scheduling & Paper Validation | 3/3 | Complete | 2026-04-09 |
Plans:
- [x] 06-01-PLAN.md -- Cron setup (install_cron.sh) with heartbeat, gated cycle, daily forced scan
- [x] 06-02-PLAN.md -- Live gate enhancement (--check, win rate, calibration health) and status.sh
- [x] 06-03-PLAN.md -- Paper trading validation (20+ autonomous cycles, evidence collection)
