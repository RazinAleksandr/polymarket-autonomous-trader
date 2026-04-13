---
phase: 05-autonomous-cycle-validation
plan: 01
subsystem: claude-md-tuning
tags: [claude-md, discovery, phase-e, calibration, tests]
dependency_graph:
  requires: []
  provides: [phase-b-discovery-tuning, phase-e-learning-loop, gamma-batch-size]
  affects: [polymarket-trader/.claude/CLAUDE.md, polymarket-trader/lib/market_data.py, polymarket-trader/tests/test_strategy_evolution.py]
tech_stack:
  added: []
  patterns: [explicit-cli-instructions, golden-rule-triggers, playbook-evolution]
key_files:
  created: []
  modified:
    - polymarket-trader/.claude/CLAUDE.md
    - polymarket-trader/lib/market_data.py
    - polymarket-trader/tests/test_strategy_evolution.py
decisions:
  - "Phase B uses --limit 50 with 0.10-0.85 sweet spot and 14-day resolution filter"
  - "Phase E expanded to 8 steps with explicit record_outcome.py, golden-rules, and playbook evolution"
  - "Gamma API batch size set to 200 to ensure enough raw markets survive post-filters"
  - "Removed test_core_principles_has_placeholder as obsolete after Phase 2 rewrite"
metrics:
  duration: 180s
  completed: "2026-04-04T18:02:20Z"
---

# Phase 05 Plan 01: CLAUDE.md Phase B/E Tuning and Discovery Fix Summary

Updated CLAUDE.md with explicit Phase E instructions for record_outcome.py invocation, golden-rules.md updates, and category playbook evolution; tuned Phase B discovery to --limit 50 with widened price range and resolution filter; increased Gamma API batch size from 50 to 200 in market_data.py; fixed broken test assertions.

## Changes Made

### Task 1: CLAUDE.md Phase B/E Updates and Gamma API Batch Size

**Phase B changes:**
- Discovery command now uses `--limit 50` (was `--limit 20`)
- Added resolution filter as step 2: exclude markets resolving beyond 14 days
- Sweet-spot filter widened to `0.10-0.85` (was `0.15-0.85`)
- Fallback price range widened to `0.05-0.95` (was `0.10-0.90`)
- Total steps increased from 5 to 6

**Phase E changes (6 to 8 steps):**
- Step 2 now includes explicit `python tools/record_outcome.py --market-id {id} --stated-prob {prob} --actual {WIN|LOSS} --category {cat} --pnl {pnl} --pretty` CLI call for each resolved position
- Step 6 added: golden-rules.md update trigger on loss > 2% bankroll OR 2+ repeated patterns (max 3 new rules per cycle)
- Step 7 added: append dated "Lessons Learned" to `knowledge/market-types/{category}.md` for each category traded
- Old step 6 (log summary) becomes step 8

**Gamma API batch size:**
- Changed `"limit": 50` to `"limit": 200` in `lib/market_data.py` `fetch_active_markets()` params
- Ensures enough raw markets survive volume, liquidity, price, and resolution filters

**Commit:** b43ed31

### Task 2: Fix test_strategy_starts_blank Assertion

- `test_strategy_starts_blank` now checks for absence of bullet-point rule lines (`- ` or `* `) instead of checking for "No rules yet" placeholder text that no longer exists in strategy.md
- Removed `test_core_principles_has_placeholder` -- core-principles.md was rewritten in Phase 2 from placeholder to 7 immutable guardrails, making this test obsolete
- Fixed `test_core_principles_separate` assertion to match actual wording ("never modifies" instead of "never modified by the trading agent")
- Full test suite: 266 passed, 0 failed

**Commit:** 9c79bca

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_core_principles_separate assertion mismatch**
- **Found during:** Task 2
- **Issue:** test_core_principles_separate checked for "never modified by the trading agent" but core-principles.md actually says "NEVER modifies it" (different wording after Phase 2 rewrite)
- **Fix:** Updated assertion to accept both "never modifies" and "never modified"
- **Files modified:** polymarket-trader/tests/test_strategy_evolution.py
- **Commit:** 9c79bca

## Verification Results

- `grep "record_outcome.py" CLAUDE.md` -- found (1 match in Phase E)
- `grep "golden-rules.md" CLAUDE.md` -- found (2 matches: Phase E step 6 + Guardrails)
- `grep "market-types/" CLAUDE.md` -- found (1 match in Phase E step 7)
- `grep "limit 50" CLAUDE.md` -- confirmed in Phase B step 1
- `grep "0.10-0.85" CLAUDE.md` -- confirmed in Phase B step 3
- `grep "14 days" CLAUDE.md` -- confirmed in Phase B step 2
- Phase E step count: 8 (confirmed)
- Guardrails section: unchanged
- Session Start section: unchanged
- `grep '"limit": 200' lib/market_data.py` -- confirmed
- `python -m pytest tests/test_strategy_evolution.py -x` -- 5 passed
- `python -m pytest tests/ -x` -- 266 passed, 0 failed

## Known Stubs

None -- all changes are complete implementations with no placeholders.

## Self-Check: PASSED

- All 3 modified files exist on disk
- Both task commits (b43ed31, 9c79bca) found in git log
- SUMMARY.md created at expected path
