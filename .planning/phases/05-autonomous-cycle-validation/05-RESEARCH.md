# Phase 5: Autonomous Cycle Validation - Research

**Researched:** 2026-04-04
**Domain:** Trading cycle orchestration, validation scripting, CLAUDE.md instruction design
**Confidence:** HIGH

## Summary

Phase 5 bridges the gap between infrastructure (Phases 1-4) and autonomous operation (Phase 6). The codebase has all the building blocks -- cycle launcher, skill docs, CLI tools, knowledge base -- but CLAUDE.md Phase E is missing explicit instructions for golden-rule updates (STRAT-04) and category playbook evolution (STRAT-06). The `record_outcome.py` CLI exists but is never referenced in CLAUDE.md. The validation script (`validate_cycle.py`) is entirely new code. Market discovery returns zero-trade cycles due to Claude applying an old 72h filter from prior instructions despite `max_resolution_days` being set to 14 in config.py since Phase 4.

The phase has three distinct work streams: (1) CLAUDE.md Phase E instruction updates (small text changes with outsized impact), (2) a validation script that parses cycle reports and cross-references state files, and (3) actual cycle execution with evidence collection. The first two are code deliverables; the third is operational validation that proves the system works.

**Primary recommendation:** Start with CLAUDE.md updates and discovery tuning (unblocking productive cycles), then build validate_cycle.py, then execute 5+ cycles collecting evidence.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Update CLAUDE.md Phase E with explicit instructions for golden-rules.md updates (STRAT-04) and category playbook evolution (STRAT-06). All cycle instructions live in CLAUDE.md -- skill docs provide the detailed frameworks but CLAUDE.md is the trigger.
- D-02: Add explicit `record_outcome.py` CLI call to Phase E step 2: "For each resolved position, run `python tools/record_outcome.py --market-id X --stated-prob Y --actual Z --category W`. Then load calibration-check.md to interpret results." Makes tool invocation unambiguous.
- D-03: Market intel stays in Phase C only. Phase E is about learning from outcomes, not re-fetching market data. Keep the separation clean.
- D-04: Build `tools/validate_cycle.py` that checks per-cycle: (a) cycle report exists with correct structure, (b) report references knowledge base (golden rules, calibration, playbook), (c) strategy.md change count is 0-3, (d) DB has matching entries for trades and calibration records if resolutions occurred.
- D-05: `validate_cycle.py --summary` produces cumulative progress report across all cycles: total cycles run, rules added, calibration entries, playbooks modified, strategy.md growth. Proves evolution over 5+ cycles (Success Criteria #3).
- D-06: Manual cycles triggered via `run_cycle.sh --force` -- tests the real execution path (tmux, PID lock, timeout) that Phase 6 cron will use. Most realistic validation.
- D-07: Tune discover_markets.py parameters: higher --limit (50-100), verify 14-day resolution window is applied (not old 72h), widen price sweet spot if needed. Fix root cause of zero-market cycles.
- D-08: Phase deliverables include CLAUDE.md updates, validation script, discovery tuning, AND evidence of 5+ cycles run with validate_cycle.py output. Full proof the system works.
- D-09: Soft enforcement via CLAUDE.md instruction ("max 3 changes, log each change with evidence") + hard detection via validate_cycle.py parsing the cycle report's Strategy Changes section. Flags violations.
- D-10: Golden rule addition threshold: loss > 2% bankroll OR 2+ repeated patterns (carried forward from Phase 2 decision). Already established, not re-decided.
- D-11: Playbook evolution via "Lessons Learned" append section at bottom of each category playbook. Claude appends observations after trading that category. Base rates and edge sources stay stable until enough evidence accumulates.

### Claude's Discretion
- Internal structure and output format of validate_cycle.py (JSON, table, markdown)
- Exact discovery parameter tuning values (--limit, price range) based on current Polymarket inventory
- How to handle cycles where no trades occur -- validation script should still pass for zero-trade cycles that correctly report the situation
- Whether validate_cycle.py lives in tools/ or scripts/

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STRAT-03 | Claude writes cycle reports to state/reports/ after every trading cycle | Cycle report template already in cycle-review.md skill. CLAUDE.md Phase E step 4 already writes reports. Validation script confirms report structure. |
| STRAT-04 | Claude updates golden-rules.md with new rules learned from losses (with trade citation) | CLAUDE.md Phase E needs explicit instruction to check golden-rule thresholds after post-mortem. post-mortem.md skill Step 5 has the full framework. |
| STRAT-05 | Claude updates calibration.json after every trade resolution with Brier score and category accuracy | record_outcome.py CLI exists and works. CLAUDE.md Phase E step 2 needs explicit CLI invocation added per D-02. |
| STRAT-06 | Claude evolves category playbooks in market-types/*.md based on trading experience | CLAUDE.md Phase E needs new instruction for "Lessons Learned" append to category playbooks. 6 playbooks exist in knowledge/market-types/. |
| STRAT-07 | Claude makes 0-3 strategy changes maximum per cycle to prevent drift | Already in cycle-review.md Step 4 and CLAUDE.md Phase E step 5. validate_cycle.py enforces via report parsing (D-09). |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | Test framework for validate_cycle.py | Already installed, 261 tests passing |
| argparse | stdlib | CLI for validate_cycle.py | Matches all other tools/ scripts |
| json | stdlib | Parsing cycle reports, calibration.json, signal.json | Standard across project |
| sqlite3 | stdlib | DB queries in validate_cycle.py | Already used via lib/db.py |
| pathlib | stdlib | File path handling | Used in lib/config.py |
| re | stdlib | Parsing markdown cycle reports for structure/content | Needed for report validation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lib.db.DataStore | project | DB access for trade/calibration records | validate_cycle.py DB checks |
| lib.config.load_config | project | Config loading | validate_cycle.py config access |
| lib.calibration | project | Calibration record queries | validate_cycle.py calibration checks |

### Alternatives Considered
None -- this phase uses only existing project infrastructure. No new external dependencies needed.

## Architecture Patterns

### Recommended Project Structure
```
polymarket-trader/
  .claude/CLAUDE.md          # Phase E updates (3-4 new instruction lines)
  tools/validate_cycle.py    # NEW: per-cycle and summary validation
  tools/discover_markets.py  # Existing: parameter tuning
  lib/config.py              # Existing: may need discovery defaults update
  knowledge/golden-rules.md  # Evolution target (Claude adds rules)
  knowledge/market-types/*.md # Evolution target (Claude appends lessons)
  state/strategy.md          # Evolution target (Claude adds rules)
  state/reports/cycle-*.md   # Validation targets (Claude writes, script validates)
  tests/test_validate_cycle.py # NEW: tests for validation script
```

### Pattern 1: validate_cycle.py Design
**What:** A CLI tool that validates cycle outputs and produces summary reports.
**When to use:** After each cycle (per-cycle mode) and after 5+ cycles (summary mode).

The script follows the established project CLI pattern:
- argparse with `--pretty` flag (JSON default, human-readable optional)
- `--cycle-id YYYYMMDD-HHMMSS` for per-cycle validation
- `--summary` for cumulative progress report
- Uses `lib.config.load_config` and `lib.db.DataStore`
- Returns structured JSON (success/failure with details)

**Per-cycle checks (D-04):**
1. Report exists at `state/reports/cycle-{cycle_id}.md`
2. Report has required sections (Summary, Markets Analyzed, Trades Executed, Portfolio State, Resolutions, Lessons, Strategy Suggestions, Cycle Metrics)
3. Report references knowledge base: "golden" or "golden-rules" appears in text, "calibration" appears, category playbook name appears
4. Strategy.md changes counted by diffing against previous version or parsing the "Strategy changes" metric in the report -- must be 0-3
5. If trades occurred: DB has matching trade records
6. If resolutions occurred: DB has calibration_outcomes records

**Summary checks (D-05):**
1. Count total cycle reports in state/reports/
2. Count golden rules (parse golden-rules.md for rule count, compare to baseline 16)
3. Count calibration entries (query calibration_outcomes table)
4. Check market-types/*.md for "Lessons Learned" sections (evidence of playbook evolution)
5. Measure strategy.md growth (line count vs baseline empty state)
6. Output: total_cycles, rules_added, calibration_entries, playbooks_modified, strategy_lines_added

**Example output structure:**
```json
{
  "cycle_id": "20260404-140000",
  "valid": true,
  "checks": {
    "report_exists": true,
    "report_structure": true,
    "knowledge_base_refs": {"golden_rules": true, "calibration": true, "playbook": false},
    "strategy_changes": 1,
    "strategy_drift": false,
    "db_trades_match": true,
    "db_calibration_match": true
  },
  "warnings": ["No playbook reference in report -- zero trades in established categories"]
}
```

### Pattern 2: CLAUDE.md Phase E Updates
**What:** Adding 3-4 instruction lines to Phase E that explicitly trigger golden-rules updates, playbook evolution, and record_outcome.py calls.
**When to use:** This is a one-time text edit.

Current Phase E (from CLAUDE.md lines 84-90):
```markdown
### Phase E: Learn and Evolve
1. Load post-mortem.md for any resolved positions from Phase A
2. Load calibration-check.md to record outcomes and update calibration data
3. Load cycle-review.md to write the cycle report and update strategy
4. Write cycle report to state/reports/cycle-{cycle_id}.md
5. Update state/strategy.md with max 0-3 evidence-backed changes
6. Log cycle summary
```

Updated Phase E should add after step 2:
```markdown
2b. For each resolved position, run: python tools/record_outcome.py --market-id {id} --stated-prob {prob} --actual {WIN|LOSS} --category {cat} --pnl {pnl} --pretty
```

And add after step 5:
```markdown
5b. If any post-mortem produced a golden-rule candidate (loss > 2% bankroll OR 2+ repeated patterns), add to knowledge/golden-rules.md following the format in that file
5c. For each category traded this cycle, append a "Lessons Learned" entry to knowledge/market-types/{category}.md with date, observation, and evidence
```

### Pattern 3: Discovery Parameter Tuning (D-07)
**What:** Fix zero-trade cycles by ensuring the 14-day resolution window is used.
**Root cause analysis:**

The cycle reports show Claude rejecting all markets with ">72h resolution" -- but `lib/config.py` already has `max_resolution_days=14`. The problem is:
1. `lib/market_data._passes_filters()` does NOT filter on resolution window at all -- it only checks volume, liquidity, price, and token IDs
2. The resolution filtering happens at the Claude instruction layer (CLAUDE.md Phase B) where Claude reads markets and applies its own judgment
3. The old cycle reports reference "72h hard limit" which was the pre-Phase-4 value

**Fix approach:**
- Update CLAUDE.md Phase B to explicitly reference config's `max_resolution_days` (14 days)
- Alternatively, add end_date filtering to `discover_markets.py` / `_passes_filters()` to pre-filter
- Increase `--limit` in CLAUDE.md Phase B from 20 to 50-100
- Widen price sweet spot from 0.15-0.85 to 0.10-0.90 as the primary range (currently 0.10-0.90 is only the relaxed fallback)

The CLAUDE.md Phase B currently says:
```
1. Run: python tools/discover_markets.py --limit 20 --pretty
2. Apply sweet-spot filter: YES price between 0.15-0.85
```

Should become:
```
1. Run: python tools/discover_markets.py --limit 50 --pretty
2. Apply resolution filter: exclude markets resolving beyond 14 days (MAX_RESOLUTION_DAYS in config)
3. Apply sweet-spot filter: YES price between 0.10-0.85
```

### Anti-Patterns to Avoid
- **Over-engineering validate_cycle.py:** It parses markdown reports and queries SQLite. Keep it simple -- regex for structure, string matching for knowledge base references. No need for a full markdown parser.
- **Modifying core-principles.md:** The CLAUDE.md explicitly says never modify this file. Phase E instructions must reiterate this.
- **Adding resolution filtering to _passes_filters():** The Gamma API `end_date` field is inconsistent (some markets have it, some don't). Better to let Claude filter with judgment than hard-code a brittle date filter in Python. Instead, update CLAUDE.md instructions.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Markdown parsing | Full AST parser | Regex + string matching | Cycle reports have predictable structure; regex is sufficient |
| DB queries | Raw SQL in validate_cycle.py | lib.db.DataStore methods | Already has get_open_positions, trade queries |
| Calibration recording | Custom calibration JSON writer | tools/record_outcome.py | Already built and tested (Phase 3) |
| Strategy diff | Git-based diffing | Parse report's "Strategy changes: N" metric | Report already contains the count |

## Common Pitfalls

### Pitfall 1: Old 72h Filter Persists in Claude's "Memory"
**What goes wrong:** Even after updating CLAUDE.md, Claude sessions may recall the old 72h limit from prior cycle reports (which it reads as context).
**Why it happens:** CLAUDE.md Phase E says to read the 3 most recent cycle reports. Those reports all reference "72h hard limit."
**How to avoid:** The first manual cycle after updating CLAUDE.md should explicitly note the parameter change in the cycle report, establishing the new context for future cycles.
**Warning signs:** First cycle still shows "Resolution >72h" rejections.

### Pitfall 2: validate_cycle.py False Positives on Knowledge Base References
**What goes wrong:** A zero-trade cycle may not reference category playbooks because no categories were traded.
**Why it happens:** D-04(b) requires "report references knowledge base" but not all knowledge base files are relevant every cycle.
**How to avoid:** Make knowledge base reference checks context-aware. Golden rules should always be referenced (read at session start). Calibration check is always referenced (Part of Phase E). Playbook reference is only required if trades occurred in a specific category.
**Warning signs:** validate_cycle.py fails on legitimate zero-trade cycles.

### Pitfall 3: Strategy Evolution Test Breaks
**What goes wrong:** `test_strategy_starts_blank` already fails because strategy.md content was modified.
**Why it happens:** The test expects "No rules yet" or "No approach defined" placeholder text, but strategy.md currently has section headers without that exact text.
**How to avoid:** Fix or update the test expectation before this phase adds real strategy content. Otherwise the test will conflict with STRAT-03/STRAT-07 which requires strategy evolution.
**Warning signs:** Test suite fails after first cycle writes strategy updates.

### Pitfall 4: Counting Strategy Changes Incorrectly
**What goes wrong:** validate_cycle.py miscounts changes because it parses the wrong section or format.
**Why it happens:** The cycle report "Strategy changes: N" metric relies on Claude reporting honestly. If Claude writes the wrong number, validation catches it -- but only if the validator also independently counts.
**How to avoid:** Primary check: parse the "Strategy changes" metric from the Cycle Metrics table. Secondary check: count lines with dates in strategy.md that match the cycle's date. If they disagree, flag it.
**Warning signs:** "Strategy changes: 0" in report but strategy.md actually changed.

### Pitfall 5: record_outcome.py Argument Mismatch
**What goes wrong:** Claude passes wrong arguments to record_outcome.py because CLAUDE.md instruction doesn't match actual CLI interface.
**Why it happens:** The CLI takes `--actual WIN|LOSS` (string), not a numeric outcome. Also takes `--stated-prob` (hyphenated) not `--stated_prob`.
**How to avoid:** The CLAUDE.md instruction must exactly match the CLI: `python tools/record_outcome.py --market-id {id} --stated-prob {prob} --actual {WIN|LOSS} --category {cat} --pnl {pnl} --pretty`
**Warning signs:** "Record outcome failed" errors in cycle logs.

## Code Examples

### validate_cycle.py Per-Cycle Check
```python
# Pattern for checking cycle report structure
import re

REQUIRED_SECTIONS = [
    r"## Summary",
    r"## Markets Analyzed",
    r"## Trades Executed",
    r"## Portfolio State",
    r"## Resolutions",
    r"## Lessons",
    r"## Strategy Suggestions",
    r"## Cycle Metrics",
]

def check_report_structure(report_content: str) -> dict:
    results = {}
    for section in REQUIRED_SECTIONS:
        results[section.replace("## ", "")] = bool(re.search(section, report_content))
    return results

def check_knowledge_refs(report_content: str, had_trades: bool) -> dict:
    lower = report_content.lower()
    return {
        "golden_rules": "golden" in lower or "golden-rules" in lower,
        "calibration": "calibration" in lower or "brier" in lower,
        "playbook": not had_trades or any(
            cat in lower for cat in ["crypto", "politics", "sports", "commodities", "entertainment", "finance"]
        ),
    }

def check_strategy_drift(report_content: str) -> tuple[int, bool]:
    """Returns (change_count, is_drift)."""
    match = re.search(r"Strategy changes\s*\|\s*(\d+)", report_content)
    count = int(match.group(1)) if match else 0
    return count, count > 3
```

### validate_cycle.py Summary Mode
```python
import glob
import os

def generate_summary(project_root: str) -> dict:
    reports = sorted(glob.glob(os.path.join(project_root, "state/reports/cycle-*.md")))
    
    # Count golden rules
    gr_path = os.path.join(project_root, "knowledge/golden-rules.md")
    with open(gr_path) as f:
        gr_content = f.read()
    rule_count = len(re.findall(r"\*\*Rule \d+", gr_content))
    baseline_rules = 16  # Phase 2 baseline
    
    # Check playbook evolution
    playbooks_modified = 0
    for pb in glob.glob(os.path.join(project_root, "knowledge/market-types/*.md")):
        with open(pb) as f:
            if "Lessons Learned" in f.read():
                playbooks_modified += 1
    
    # Strategy growth
    strat_path = os.path.join(project_root, "state/strategy.md")
    with open(strat_path) as f:
        strat_lines = len(f.readlines())
    baseline_strat = 12  # Empty template line count
    
    return {
        "total_cycles": len(reports),
        "rules_added": rule_count - baseline_rules,
        "playbooks_modified": playbooks_modified,
        "strategy_lines_added": strat_lines - baseline_strat,
    }
```

### CLAUDE.md Phase E Addition
```markdown
### Phase E: Learn and Evolve
<!-- OPERATOR-SET -->
Analyze outcomes, update calibration, write cycle report, evolve strategy.

1. Load `.claude/skills/post-mortem.md` for any resolved positions from Phase A
2. Load `.claude/skills/calibration-check.md` to record outcomes and update calibration data
   - For each resolved position, run: `python tools/record_outcome.py --market-id {id} --stated-prob {prob} --actual {WIN|LOSS} --category {cat} --pnl {pnl} --pretty`
   - Then interpret results using the calibration-check framework
3. Load `.claude/skills/cycle-review.md` to write the cycle report and update strategy
4. Write cycle report to `state/reports/cycle-{cycle_id}.md`
5. Update `state/strategy.md` with max 0-3 evidence-backed changes
6. If any post-mortem yielded a golden-rule candidate (loss > 2% bankroll OR 2+ repeated patterns): add to `knowledge/golden-rules.md` following its format. Max 3 new rules per cycle.
7. For each category traded this cycle: append a dated "Lessons Learned" entry to `knowledge/market-types/{category}.md` with observation and evidence
8. Log cycle summary: markets scanned, analyzed, traded, P&L impact
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 72h resolution window | 14-day resolution window | Phase 4 (config.py) | CLAUDE.md Phase B still references old approach indirectly |
| Fixed $25/$200 sizing | Percentage-based bankroll sizing | Phase 4 | Sizing is config-driven now |
| Multi-agent architecture | Single Claude session | Phase 1 | All cycle logic in one CLAUDE.md |
| Manual golden rule creation | Phase 2 seeded 16 rules | Phase 2 | Claude extends from Phase 5 onward |

## Open Questions

1. **test_strategy_starts_blank failure**
   - What we know: The test expects "No rules yet" or "No approach defined" in strategy.md, but the current file has section headers without those exact phrases.
   - What's unclear: Whether to fix the test to match current reality or update strategy.md to include the expected text.
   - Recommendation: Update the test assertion to match the current strategy.md format (section headers with no rules). This test will need further updating or removal once Phase 5 cycles add real strategy content.

2. **Discovery tuning requires live API testing**
   - What we know: `discover_markets.py` calls Gamma API with `limit: 50` hardcoded in market_data.py, but the CLI `--limit` parameter controls post-filter truncation.
   - What's unclear: Whether increasing the API fetch limit (currently 50 raw markets from Gamma) is needed, or just the post-filter limit.
   - Recommendation: First try updating CLAUDE.md to use `--limit 50` and widen the price sweet spot. If that fails, increase the Gamma API fetch batch size in `lib/market_data.py`.

3. **End-date filtering gap**
   - What we know: `_passes_filters()` does not check resolution date. The Market model has an `end_date` field populated from Gamma API.
   - What's unclear: How reliable the Gamma API `endDate` field is across all market types.
   - Recommendation: Add resolution date filtering to CLAUDE.md Phase B instructions (Claude interprets dates with judgment) rather than to `_passes_filters()` (brittle if field is missing). If Claude consistently gets it wrong, consider adding a soft filter to Python code later.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | All Python tools | Yes | 3.12.3 | -- |
| pytest | Test suite | Yes | 9.0.2 | -- |
| tmux | run_cycle.sh | Yes | 3.4 | Direct execution (already implemented) |
| Claude Code CLI | Cycle execution | Yes | 2.1.92 | -- |
| SQLite | DB queries | Yes | stdlib | -- |
| Gamma API | Market discovery | Yes (network) | -- | -- |

No missing dependencies.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None (default pytest discovery) |
| Quick run command | `cd /home/trader/polymarket-trader && source .venv/bin/activate && python -m pytest tests/test_validate_cycle.py -x` |
| Full suite command | `cd /home/trader/polymarket-trader && source .venv/bin/activate && python -m pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STRAT-03 | Cycle report written to state/reports/ | unit (validate_cycle) | `pytest tests/test_validate_cycle.py::test_report_structure -x` | Wave 0 |
| STRAT-04 | Golden rules updated after losses | unit (validate_cycle) | `pytest tests/test_validate_cycle.py::test_golden_rule_detection -x` | Wave 0 |
| STRAT-05 | Calibration updated after resolution | unit (existing + validate) | `pytest tests/test_calibration.py -x` | Exists |
| STRAT-06 | Category playbooks evolve | unit (validate_cycle) | `pytest tests/test_validate_cycle.py::test_playbook_evolution -x` | Wave 0 |
| STRAT-07 | 0-3 strategy changes max | unit (validate_cycle) | `pytest tests/test_validate_cycle.py::test_strategy_drift -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_validate_cycle.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green + validate_cycle.py --summary showing 5+ cycles

### Wave 0 Gaps
- [ ] `tests/test_validate_cycle.py` -- covers STRAT-03, STRAT-04, STRAT-06, STRAT-07
- [ ] Fix `tests/test_strategy_evolution.py::test_strategy_starts_blank` -- currently fails, needs updated assertion

## Sources

### Primary (HIGH confidence)
- `/home/trader/polymarket-trader/.claude/CLAUDE.md` -- current Phase E instructions, modification target
- `/home/trader/polymarket-trader/.claude/skills/cycle-review.md` -- cycle report template, strategy update framework
- `/home/trader/polymarket-trader/.claude/skills/post-mortem.md` -- golden-rule creation framework
- `/home/trader/polymarket-trader/.claude/skills/calibration-check.md` -- calibration recording framework
- `/home/trader/polymarket-trader/tools/record_outcome.py` -- CLI interface for calibration recording
- `/home/trader/polymarket-trader/lib/market_data.py` -- _passes_filters() does NOT filter on resolution date
- `/home/trader/polymarket-trader/lib/config.py` -- max_resolution_days=14 confirmed
- `/home/trader/polymarket-trader/state/reports/cycle-20260401-120009.md` -- zero-trade cycle showing 72h filter problem
- `/home/trader/polymarket-trader/state/reports/cycle-20260331-200654.md` -- confirms multi-cycle zero-trade pattern

### Secondary (MEDIUM confidence)
- Gamma API endDate field reliability -- observed in market_data.py parsing but not validated against live API

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing infrastructure
- Architecture: HIGH -- validate_cycle.py follows established CLI patterns, CLAUDE.md changes are well-scoped
- Pitfalls: HIGH -- identified from actual cycle report evidence and code analysis

**Research date:** 2026-04-04
**Valid until:** 2026-05-04 (stable -- no external API changes expected)
