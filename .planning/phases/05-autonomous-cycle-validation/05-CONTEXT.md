# Phase 5: Autonomous Cycle Validation - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove the single-agent architecture works end-to-end by running 5+ manual trading cycles. This phase closes CLAUDE.md gaps (golden-rules and playbook updates), builds a validation script to verify cycle outputs, tunes market discovery parameters, and produces evidence of strategy evolution across multiple cycles. Deliverables include code changes AND cycle execution evidence.

</domain>

<decisions>
## Implementation Decisions

### CLAUDE.md Phase E Updates
- **D-01:** Update CLAUDE.md Phase E with explicit instructions for golden-rules.md updates (STRAT-04) and category playbook evolution (STRAT-06). All cycle instructions live in CLAUDE.md — skill docs provide the detailed frameworks but CLAUDE.md is the trigger.
- **D-02:** Add explicit `record_outcome.py` CLI call to Phase E step 2: "For each resolved position, run `python tools/record_outcome.py --market-id X --stated-prob Y --actual Z --category W`. Then load calibration-check.md to interpret results." Makes tool invocation unambiguous.
- **D-03:** Market intel stays in Phase C only. Phase E is about learning from outcomes, not re-fetching market data. Keep the separation clean.

### Validation Script
- **D-04:** Build `tools/validate_cycle.py` that checks per-cycle: (a) cycle report exists with correct structure, (b) report references knowledge base (golden rules, calibration, playbook), (c) strategy.md change count is 0-3, (d) DB has matching entries for trades and calibration records if resolutions occurred.
- **D-05:** `validate_cycle.py --summary` produces cumulative progress report across all cycles: total cycles run, rules added, calibration entries, playbooks modified, strategy.md growth. Proves evolution over 5+ cycles (Success Criteria #3).

### Cycle Execution
- **D-06:** Manual cycles triggered via `run_cycle.sh --force` — tests the real execution path (tmux, PID lock, timeout) that Phase 6 cron will use. Most realistic validation.
- **D-07:** Tune discover_markets.py parameters: higher --limit (50-100), verify 14-day resolution window is applied (not old 72h), widen price sweet spot if needed. Fix root cause of zero-market cycles.
- **D-08:** Phase deliverables include CLAUDE.md updates, validation script, discovery tuning, AND evidence of 5+ cycles run with validate_cycle.py output. Full proof the system works.

### Strategy Drift Guard
- **D-09:** Soft enforcement via CLAUDE.md instruction ("max 3 changes, log each change with evidence") + hard detection via validate_cycle.py parsing the cycle report's Strategy Changes section. Flags violations.
- **D-10:** Golden rule addition threshold: loss > 2% bankroll OR 2+ repeated patterns (carried forward from Phase 2 decision). Already established, not re-decided.
- **D-11:** Playbook evolution via "Lessons Learned" append section at bottom of each category playbook. Claude appends observations after trading that category. Base rates and edge sources stay stable until enough evidence accumulates.

### Claude's Discretion
- Internal structure and output format of validate_cycle.py (JSON, table, markdown)
- Exact discovery parameter tuning values (--limit, price range) based on current Polymarket inventory
- How to handle cycles where no trades occur — validation script should still pass for zero-trade cycles that correctly report the situation
- Whether validate_cycle.py lives in tools/ or scripts/

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CLAUDE.md (primary modification target)
- `polymarket-trader/.claude/CLAUDE.md` — Phase E section needs golden-rules, playbook, and record_outcome.py instructions added

### Skill Docs (context for CLAUDE.md updates)
- `polymarket-trader/.claude/skills/cycle-review.md` — Cycle report template and strategy update framework
- `polymarket-trader/.claude/skills/post-mortem.md` — Post-mortem framework for resolved positions
- `polymarket-trader/.claude/skills/calibration-check.md` — Calibration interpretation framework

### Existing Cycle Reports (validation reference)
- `polymarket-trader/state/reports/cycle-20260401-120009.md` — Most recent cycle report, shows zero-trade cycle format
- `polymarket-trader/state/reports/cycle-20260331-200654.md` — Earlier cycle report

### Tools (validation targets)
- `polymarket-trader/tools/record_outcome.py` — CLI for calibration recording (to be explicitly called in Phase E)
- `polymarket-trader/tools/discover_markets.py` — Market discovery (needs parameter tuning)
- `polymarket-trader/scripts/run_cycle.sh` — Cycle launcher (manual trigger via --force)

### Knowledge Base (evolution targets)
- `polymarket-trader/knowledge/golden-rules.md` — 14 rules, Claude adds new ones from losses
- `polymarket-trader/knowledge/market-types/*.md` — 6 category playbooks, Claude appends lessons
- `polymarket-trader/state/strategy.md` — Blank strategy Claude builds through trading

### State & Config
- `polymarket-trader/state/core-principles.md` — Immutable guardrails (NEVER modify)
- `polymarket-trader/lib/config.py` — Config with 14-day resolution window, 4pp edge threshold

### Requirements
- `.planning/REQUIREMENTS.md` — STRAT-03, STRAT-04, STRAT-05, STRAT-06, STRAT-07

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `run_cycle.sh` with --force flag already supports manual cycle triggering
- 3 existing cycle reports in `state/reports/` provide template for validation checks
- `lib/calibration.py` and `tools/record_outcome.py` are built and tested — just need explicit CLAUDE.md wiring
- 6 skill docs with detailed frameworks — CLAUDE.md just needs to point to them for golden-rules and playbook updates

### Established Patterns
- Cycle reports follow markdown template from cycle-review.md skill
- Strategy changes logged in report's "Strategy Changes" section with evidence
- CLI tools use `--pretty` flag for human-readable output, JSON by default
- Tests use pytest with `unittest.mock.patch` for external APIs, in-memory SQLite for DB

### Integration Points
- CLAUDE.md Phase E is the main modification point — add 3-4 new instruction lines
- validate_cycle.py reads: state/reports/, state/strategy.md, trading.db, knowledge/golden-rules.md, knowledge/market-types/
- discover_markets.py parameter tuning may touch lib/config.py defaults or CLAUDE.md Phase B instructions

</code_context>

<specifics>
## Specific Ideas

- validate_cycle.py --summary is the key deliverable for proving evolution — it aggregates evidence across 5+ cycles showing strategy growth, rule additions, and calibration entries
- The 14-day resolution window (Phase 4) should dramatically increase tradeable markets vs old 72h filter, but needs verification against live Polymarket inventory
- Zero-trade cycles are valid — validation script should pass them as long as reporting is correct

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-autonomous-cycle-validation*
*Context gathered: 2026-04-04*
