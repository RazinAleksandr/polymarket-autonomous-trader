# Phase 2: Knowledge Base & Safety - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Transplant battle-tested trading knowledge from `polymarket_claude/` into `polymarket-trader/knowledge/`, seed learning files that Claude populates through trading experience, and establish immutable safety guardrails in `state/core-principles.md`. This phase creates the knowledge foundation — Claude starts every session by reading these files.

</domain>

<decisions>
## Implementation Decisions

### Golden Rules Transplant
- **D-01:** Transplant 14 golden rules from `polymarket_claude/knowledge/GOLDEN_RULES.md` as the base for `knowledge/golden-rules.md`. Dedup with unique principles from `polymarket_claude/output/learnings/general-principles.md`. Preserve all trade citations.
- **D-02:** Keep 20-rule cap with existing merge-or-remove discipline ("When adding a rule, merge or remove an existing one first").
- **D-03:** `state/strategy.md` rules stay separate — they are Claude's working operational memory, not permanent golden rules. No cross-contamination.

### Core Principles Rewrite
- **D-04:** Switch from fixed dollar amounts ($25 max, $200 exposure) to **percentage-based limits**: 5% max position, 30% max exposure. Dollar amounts become derived from `bankroll.json` at runtime.
- **D-05:** Remove all session-specific content (Overnight Crypto Sprint mode, 1-hour cycles, crypto-focused parameters). Core principles becomes a **pure immutable guardrails file** — session configs go elsewhere.
- **D-06:** Immutable guardrails per requirements: paper trading default, 5% max position, 30% max exposure, live gate required, no deletion of audit trail, record-before-confirm, 5-consecutive-loss pause.

### Category Playbooks
- **D-07:** Rename `oscars.md` → `entertainment.md` as a broader entertainment playbook (awards, TV ratings, box office). Oscars content becomes the seed; Claude expands through trading.
- **D-08:** Create new `finance.md` playbook seeded from commodity settlement lessons (Golden Rule 4) and near-certainty patterns from strategy rules. Covers: interest rates, Fed decisions, stock indices, GDP/CPI targets.
- **D-09:** 6 total playbooks in `knowledge/market-types/`: crypto, politics, sports, commodities, entertainment, finance.

### Strategy & Calibration
- **D-10:** Archive current `state/strategy.md` (18 rules from real trading) to `knowledge/prior-strategy-archive.md` as readable reference. Reset `state/strategy.md` to section headers only — Claude rebuilds from scratch through autonomous trading.
- **D-11:** `knowledge/calibration.json` starts as empty seed structure (valid JSON with schema, no data). Clean measurement of autonomous performance with no prior-era contamination.

### Claude's Discretion
- Exact formatting and section structure within each playbook (following the general pattern: base rates, edge sources, resolution mechanics, lessons learned)
- How to handle the 5 existing playbooks that need content review/cleanup during transplant
- `knowledge/strategies.md` and `knowledge/edge-sources.md` internal structure — follow `polymarket_claude/` patterns as starting point
- Whether `prior-strategy-archive.md` includes commentary or is a raw copy

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Knowledge Source (transplant from)
- `polymarket_claude/knowledge/GOLDEN_RULES.md` — 14 battle-tested golden rules with trade citations (primary transplant source)
- `polymarket_claude/knowledge/market_types/crypto.md` — Crypto category playbook
- `polymarket_claude/knowledge/market_types/politics.md` — Politics category playbook
- `polymarket_claude/knowledge/market_types/sports.md` — Sports category playbook
- `polymarket_claude/knowledge/market_types/commodities.md` — Commodities category playbook
- `polymarket_claude/knowledge/market_types/oscars.md` — Oscars playbook (rename to entertainment)
- `polymarket_claude/knowledge/strategies.md` — Strategy lifecycle framework (TESTING/PERFORMING/UNDERPERFORMING/RETIRED)
- `polymarket_claude/knowledge/edge_sources.md` — Edge source tracking with status categories
- `polymarket_claude/output/learnings/general-principles.md` — 10 general principles to dedup with golden rules

### Existing State (rewrite/archive)
- `polymarket-trader/state/core-principles.md` — Current operator-locked parameters (to be rewritten as percentage-based guardrails)
- `polymarket-trader/state/strategy.md` — 18 Claude-written rules (to be archived then reset)

### Architecture Context
- `.planning/codebase/STRUCTURE.md` — Directory layout for understanding where files go
- `.planning/phases/01-single-agent-architecture/01-CONTEXT.md` — Phase 1 decisions on skill docs and CLAUDE.md design

### Requirements
- `.planning/REQUIREMENTS.md` — KNOW-01 through KNOW-06, STRAT-01, STRAT-02, SAFE-01 through SAFE-07

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `polymarket_claude/knowledge/GOLDEN_RULES.md`: Complete 14-rule set with trade citations, categorized (Pre-Trade, Sizing, Research, Learning) — direct transplant source
- `polymarket_claude/knowledge/strategies.md`: Working lifecycle framework (TESTING → PERFORMING → UNDERPERFORMING → RETIRED) — transplant structure as-is
- `polymarket_claude/knowledge/edge_sources.md`: Edge tracking with Active/Untested/Failed sections — transplant structure as-is
- 5 existing market-type playbooks with varying depth — crypto and commodities are most developed

### Established Patterns
- Golden rules use numbered format with Trigger/Rule/Taught-by structure — preserve this
- Strategy rules use numbered entries with "Added cycle YYYYMMDD-HHMMSS" citations — the archive will preserve these
- Core principles use a table format for operator-locked parameters — keep table format but change to percentages
- Calibration tracking in `polymarket_claude/` uses `scripts/calibration.py` (Phase 3 builds the new lib version)

### Integration Points
- `knowledge/` directory doesn't exist yet in `polymarket-trader/` — needs creation with full subdirectory structure
- CLAUDE.md (from Phase 1) already references knowledge base loading at session start — file paths must match what CLAUDE.md expects
- `state/core-principles.md` is read by Claude at every cycle start — rewrite must preserve the "read first, never modify" contract
- `bankroll.json` already exists in `state/` — percentage-based sizing will reference this at runtime

</code_context>

<specifics>
## Specific Ideas

- Golden rules transplant preserves the "This rule cost real money to learn" framing and individual trade citations
- Core principles keeps the "Reality Check" opening (85-90% of retail accounts lose) as motivation
- Finance playbook seeded from Golden Rule 4 (settlement vs intraday) and general-principles on Fed rate decisions
- Prior strategy archive preserves cycle timestamps so Claude can see when rules were added/refined

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-knowledge-base-safety*
*Context gathered: 2026-04-03*
