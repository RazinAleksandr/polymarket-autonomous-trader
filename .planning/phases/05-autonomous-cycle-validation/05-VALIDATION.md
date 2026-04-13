---
phase: 5
slug: autonomous-cycle-validation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-04
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | none -- default pytest discovery |
| **Quick run command** | `cd /home/trader/polymarket-trader && source .venv/bin/activate && python -m pytest tests/ -x` |
| **Full suite command** | `cd /home/trader/polymarket-trader && source .venv/bin/activate && python -m pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd /home/trader/polymarket-trader && source .venv/bin/activate && python -m pytest tests/ -x`
- **After every plan wave:** Run `cd /home/trader/polymarket-trader && source .venv/bin/activate && python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | STRAT-03, STRAT-04, STRAT-05, STRAT-06, STRAT-07 | grep+count | `cd /home/trader/polymarket-trader && grep -c "record_outcome.py" .claude/CLAUDE.md && grep -c "golden-rules.md" .claude/CLAUDE.md && grep '"limit": 200' lib/market_data.py` | ✅ self-contained | ⬜ pending |
| 05-01-02 | 01 | 1 | STRAT-03 | unit | `cd /home/trader/polymarket-trader && source .venv/bin/activate && python -m pytest tests/test_strategy_evolution.py -x -v` | ✅ exists | ⬜ pending |
| 05-02-01 | 02 | 1 | STRAT-03, STRAT-04, STRAT-05, STRAT-06, STRAT-07 | unit | `cd /home/trader/polymarket-trader && source .venv/bin/activate && python -m pytest tests/test_validate_cycle.py -x` | ❌ W0 (created by plan 02) | ⬜ pending |
| 05-03-01 | 03 | 2 | STRAT-03 | integration | `cd /home/trader/polymarket-trader && source .venv/bin/activate && python tools/validate_cycle.py --summary --pretty` | depends on 05-02 | ⬜ pending |
| 05-03-02 | 03 | 2 | ALL | human | checkpoint:human-verify (real vs simulated gate) | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Plan 05-01 Task 1 verify is self-contained (grep checks on CLAUDE.md + market_data.py)
- [x] Plan 05-01 Task 2 verify uses existing `tests/test_strategy_evolution.py`
- [ ] `tests/test_validate_cycle.py` -- created by Plan 05-02 Task 1 (TDD: tests written first)

*Wave 0 is complete for Plan 05-01. Plan 05-02 creates its own test file as part of TDD execution.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 5+ real cycles show evolution | STRAT-03, STRAT-04 | Requires real cycle execution via run_cycle.sh | Run `run_cycle.sh --force` 5+ times, then `python tools/validate_cycle.py --summary` |
| Playbook has Lessons Learned | STRAT-06 | Requires Claude writing cycle report | Check `knowledge/market-types/*.md` for "Lessons Learned" section after cycles |
| Real vs simulated confirmation | ALL | Human judgment required | User must confirm in checkpoint whether cycles were real or simulated |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
