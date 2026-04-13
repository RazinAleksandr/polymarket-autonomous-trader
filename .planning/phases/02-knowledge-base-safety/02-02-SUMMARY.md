---
phase: 02-knowledge-base-safety
plan: 02
subsystem: knowledge-base
tags: [knowledge, market-types, playbooks, transplant]
dependency_graph:
  requires: []
  provides: [category-playbooks, market-type-knowledge]
  affects: [trading-decisions, position-sizing, edge-evaluation]
tech_stack:
  added: []
  patterns: [category-profile-table, rule-apply-when-structure, percentage-based-sizing]
key_files:
  created:
    - polymarket-trader/knowledge/market-types/crypto.md
    - polymarket-trader/knowledge/market-types/politics.md
    - polymarket-trader/knowledge/market-types/sports.md
    - polymarket-trader/knowledge/market-types/commodities.md
    - polymarket-trader/knowledge/market-types/entertainment.md
    - polymarket-trader/knowledge/market-types/finance.md
  modified: []
decisions:
  - Broadened oscars.md to entertainment.md covering awards, TV, box office, streaming
  - Created finance.md as new playbook seeded from golden rules 4 and 5
  - Used hyphenated market-types directory name per D-09 convention
  - Removed stale position data and current context sections from transplanted files
metrics:
  duration: 179s
  completed: "2026-04-04T07:06:17Z"
---

# Phase 02 Plan 02: Category Playbooks Summary

6 category playbooks transplanted/created with consistent structure, percentage-based sizing, settlement and near-certainty seed rules from battle-tested golden rules.

## What Was Done

### Task 1: Transplant 4 existing playbooks (crypto, politics, sports, commodities)
**Commit:** `11c6ae2`

Transplanted 4 category playbooks from `polymarket_claude/knowledge/market_types/` to `polymarket-trader/knowledge/market-types/` (hyphen per D-09). Each file follows a consistent structure: Category Profile table, Rules section, Base Rates, Edge Sources, Resolution Mechanics, Lessons Learned.

Key changes from source:
- Removed stale position data ("Current positions: None", "4 open trades", etc.)
- Removed time-bound context sections (Iran conflict March 2026, EPL standings)
- Converted dollar-based sizing to percentage-based where needed (D-04)
- Sports: 2% bankroll single game, 3% season-long (was 4%/3%)
- Added missing section headers (Base Rates, Resolution Mechanics, Lessons Learned) with "Claude populates" placeholder where source had no content
- Preserved all rules, lessons, and trade citations intact

### Task 2: Create entertainment.md and finance.md
**Commit:** `d74dd75`

**entertainment.md**: Broadened from oscars.md to cover all entertainment markets. Preserved all 5 Oscars rules including the guild predictor weakness lesson (SAG Ensemble reliability dropped to 45-55% post-2020 Academy expansion). Added subsections for TV Ratings & Streaming, Box Office, and Other Awards. Set at 2% bankroll max, 8pp min edge (calibration probation).

**finance.md**: New playbook for interest rates, stock indices, GDP/CPI targets, employment data. Seeded with two rules from golden rules: (1) near-certainty financial events have no edge (Fed rate at 99.7%), (2) settlement mechanics apply to indices too (SPX close, GDP release, CPI print). Set at 3% bankroll max, 4pp min edge, MEDIUM variance.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

- 6 .md files in polymarket-trader/knowledge/market-types/: PASS
- All 6 have "Category Profile" section: PASS
- All 6 have "Rules" section: PASS
- All files have 30+ lines (range: 61-119): PASS
- No file contains "Current positions:": PASS
- commodities.md contains "settlement": PASS
- entertainment.md contains "SAG Ensemble" guild lesson: PASS
- finance.md contains "NEAR-CERTAINTY" seed rule: PASS

## Decisions Made

1. **Broadened oscars to entertainment**: Kept all Oscars content as primary subsection, added empty TV/box office/streaming subsections for Claude to populate through experience.
2. **Finance as new playbook**: Seeded from golden rules 4 (settlement mechanics) and 5 (near-certainty = no edge) rather than inventing untested rules.
3. **Hyphenated directory name**: Used `market-types` (hyphen) per D-09 convention rather than `market_types` (underscore) from the source project.
4. **Removed time-bound context**: Stripped sections like "Current Geopolitical Context (March 2026)" and "EPL 2025-26 Season Context" as these are stale data that would mislead Claude.

## Known Stubs

None -- all "Claude populates through trading experience" placeholders are intentional design. These sections are meant to be filled by Claude through actual trading, not pre-seeded with untested content.

## Self-Check: PASSED

All 7 files found. Both commits verified (11c6ae2, d74dd75).
