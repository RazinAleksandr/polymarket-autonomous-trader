# Phase 2: Knowledge Base & Safety - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 02-knowledge-base-safety
**Areas discussed:** Golden rules transplant, Core principles rewrite, Category playbooks scope, Strategy seed vs blank slate

---

## Golden Rules Transplant

### Merge Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Transplant + dedup (Recommended) | Copy 14 golden rules as base. Merge unique principles from general-principles.md. Leave strategy.md untouched. | ✓ |
| Fresh synthesis | Combine all three sources into one curated set. Risk: loses original trade citations. | |
| Strict transplant only | Copy 14 rules exactly. Ignore general-principles.md overlap. | |

**User's choice:** Transplant + dedup
**Notes:** None

### Rule Cap

| Option | Description | Selected |
|--------|-------------|----------|
| Keep 20 cap (Recommended) | Forces merge/prioritize. Matches existing design. | ✓ |
| Raise to 30 | More room but dilutes purpose. | |
| No cap | Organic growth. Risk: becomes dump file. | |

**User's choice:** Keep 20 cap
**Notes:** None

---

## Core Principles Rewrite

### Sizing Model

| Option | Description | Selected |
|--------|-------------|----------|
| Percentage-based (Recommended) | 5% max position, 30% max exposure. Scales with bankroll. | ✓ |
| Keep dollar amounts | Keep $25/$200 hard caps. Simple but doesn't scale. | |
| Both — percentage + dollar ceiling | Belt-and-suspenders. Whichever is lower. | |

**User's choice:** Percentage-based
**Notes:** None

### Session-Specific Content

| Option | Description | Selected |
|--------|-------------|----------|
| Remove session mode entirely (Recommended) | Core principles = pure immutable guardrails. Session configs go elsewhere. | ✓ |
| Keep as default session profile | Overnight Sprint stays as default but overridable. | |
| Move to session-profiles/ directory | Separate session profiles. Core principles stays pure. | |

**User's choice:** Remove session mode entirely
**Notes:** None

---

## Category Playbooks Scope

### Oscars → Entertainment Mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Rename oscars → entertainment (Recommended) | Oscars becomes seed for broader entertainment playbook. Claude expands through trading. | ✓ |
| Keep oscars + add entertainment | 7 playbooks total. Oscars stays separate. | |
| Merge oscars into politics | Treat as one-time event, don't create category. | |

**User's choice:** Rename oscars → entertainment
**Notes:** None

### Finance Playbook Content

| Option | Description | Selected |
|--------|-------------|----------|
| Seed from commodity + strategy rules (Recommended) | Covers interest rates, Fed decisions, stock indices, GDP/CPI. Seed from Rule 4 and near-certainty patterns. | ✓ |
| Blank template only | Section headers only. Claude populates entirely from experience. | |
| You decide | Claude's discretion on structure and initial content. | |

**User's choice:** Seed from commodity + strategy rules
**Notes:** None

---

## Strategy Seed vs Blank Slate

### Existing Strategy Rules

| Option | Description | Selected |
|--------|-------------|----------|
| Archive + reset (Recommended) | Move current strategy.md to knowledge/prior-strategy-archive.md. Reset to headers only. Claude re-derives. | ✓ |
| Keep as-is, update requirement | 18 rules are battle-tested. Change STRAT-01 instead. | |
| Promote best rules to golden-rules | Move 3-5 most universal to golden-rules. Reset the rest. | |

**User's choice:** Archive + reset
**Notes:** None

### Calibration Seed

| Option | Description | Selected |
|--------|-------------|----------|
| Empty seed structure (Recommended) | Valid JSON with schema, no data. Clean autonomous measurement. | ✓ |
| Seed with prior trade data | Import Brier scores from polymarket_claude/. Risk: mixes human-guided and autonomous data. | |

**User's choice:** Empty seed structure
**Notes:** None

---

## Claude's Discretion

- Exact formatting within each playbook (following base rates / edge sources / resolution mechanics pattern)
- Playbook content review/cleanup during transplant
- strategies.md and edge-sources.md internal structure
- Whether prior-strategy-archive.md includes commentary or is raw copy

## Deferred Ideas

None — discussion stayed within phase scope
