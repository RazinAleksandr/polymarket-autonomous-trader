# Phase 5: Autonomous Cycle Validation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 05-autonomous-cycle-validation
**Areas discussed:** CLAUDE.md gaps, Validation approach, Cycle execution, Strategy drift guard

---

## CLAUDE.md Gaps

### Wiring golden-rules and playbook updates

| Option | Description | Selected |
|--------|-------------|----------|
| Update CLAUDE.md Phase E | Add explicit instructions to Phase E for golden-rules.md and playbook updates. Keeps all cycle instructions in one place. | ✓ |
| Expand skill docs only | Add logic to post-mortem.md and cycle-review.md skills. CLAUDE.md stays lean. | |
| Both CLAUDE.md + skills | Brief triggers in CLAUDE.md, detailed how-to in skill docs. | |

**User's choice:** Update CLAUDE.md Phase E (Recommended)
**Notes:** Single source of truth for cycle instructions.

### Calibration CLI call

| Option | Description | Selected |
|--------|-------------|----------|
| Add explicit CLI call | Phase E step 2 becomes explicit record_outcome.py invocation. | ✓ |
| Keep current instruction | Trust calibration-check.md skill to guide Claude to the CLI. | |

**User's choice:** Add explicit CLI call (Recommended)
**Notes:** Makes tool invocation unambiguous.

### Market intel in Phase E

| Option | Description | Selected |
|--------|-------------|----------|
| Phase C only | Market intel for pre-trade analysis only. Phase E is learning. | ✓ |
| Add to Phase E too | Compare original intel with outcome for richer post-mortems. | |
| You decide | Claude's discretion. | |

**User's choice:** Phase C only (Recommended)
**Notes:** Clean separation between analysis and learning phases.

---

## Validation Approach

### Validation method

| Option | Description | Selected |
|--------|-------------|----------|
| Validation script | Build validate_cycle.py with automated checks. | ✓ |
| Manual observation | Read reports and eyeball outputs. | |
| Checklist in CLAUDE.md | Self-validation checklist in Phase E. | |

**User's choice:** Validation script (Recommended)

### Validation checks (multi-select)

| Option | Description | Selected |
|--------|-------------|----------|
| Knowledge base references | Verify report mentions golden rules, calibration, playbook. | ✓ |
| Strategy change count | Parse strategy.md diff, verify 0-3 cap. | ✓ |
| DB integrity | Check trading.db has matching entries. | ✓ |
| Cycle report structure | Validate report follows template sections. | ✓ |

**User's choice:** All four checks selected.

### Cumulative progress tracker

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, cumulative tracker | validate_cycle.py --summary for cross-cycle evolution proof. | ✓ |
| Separate script | Keep per-cycle and cross-cycle validation separate. | |
| No, manual review | Read cycle reports manually. | |

**User's choice:** Yes, cumulative tracker (Recommended)

---

## Cycle Execution

### Trigger method

| Option | Description | Selected |
|--------|-------------|----------|
| run_cycle.sh --force | Use existing launcher, skip heartbeat check. Tests real execution path. | ✓ |
| Direct claude -p | Bypass run_cycle.sh. Simpler but doesn't test launcher. | |
| Interactive session | Manual control, least automated. | |

**User's choice:** run_cycle.sh --force (Recommended)

### Zero-market problem

| Option | Description | Selected |
|--------|-------------|----------|
| Tune discovery params | Adjust --limit, verify 14-day window, widen price range. Fix root cause. | ✓ |
| Accept zero-trade cycles | Valid validation but slow strategy evolution. | |
| Mock market data | Test fixtures for guaranteed tradeable markets. | |

**User's choice:** Tune discovery params (Recommended)

### Scope of cycle execution

| Option | Description | Selected |
|--------|-------------|----------|
| Build + run cycles | Deliver code changes AND evidence of 5+ cycles with validation output. | ✓ |
| Build only, user runs | Deliver tooling, user runs cycles separately. | |
| Build + 1-2 test cycles | Verify pipeline, leave full validation for Phase 6. | |

**User's choice:** Build + run cycles (Recommended)

---

## Strategy Drift Guard

### Enforcement mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| CLAUDE.md instruction + validate_cycle.py | Soft enforcement via instruction, hard detection via script. | ✓ |
| Git-based enforcement | Diff strategy.md before/after via git. More precise but semantic issues. | |
| Both report + git diff | Cross-reference declared and actual changes. | |

**User's choice:** CLAUDE.md instruction + validate_cycle.py check (Recommended)

### Golden rule addition threshold

| Option | Description | Selected |
|--------|-------------|----------|
| Loss > 2% bankroll or 2+ repeated pattern | Carried forward from Phase 2 decision. | ✓ |
| Any loss triggers rule review | Lower bar, more learning but risk of bloat. | |
| You decide | Claude's discretion. | |

**User's choice:** Loss > 2% bankroll or 2+ repeated pattern (Recommended)
**Notes:** Already decided in Phase 2, carried forward.

### Playbook evolution approach

| Option | Description | Selected |
|--------|-------------|----------|
| Append lessons section | Lessons Learned at bottom, base rates stay stable. | ✓ |
| Full revision allowed | Any section modifiable based on outcomes. | |
| You decide | Claude's discretion on what to update. | |

**User's choice:** Append lessons section (Recommended)

---

## Claude's Discretion

- validate_cycle.py internal structure and output format
- Exact discovery parameter tuning values
- Zero-trade cycle validation behavior
- Whether validate_cycle.py lives in tools/ or scripts/

## Deferred Ideas

None — discussion stayed within phase scope.
