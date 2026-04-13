# Phase 1: Single Agent Architecture - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 01-single-agent-architecture
**Areas discussed:** Skill doc structure, CLAUDE.md design

---

## Skill Doc Structure

### Q1: How detailed should each skill reference doc be?

| Option | Description | Selected |
|--------|-------------|----------|
| Structured frameworks | Step-by-step with decision criteria, formulas, examples. ~200-400 lines | ✓ |
| Concise checklists | Compact checklist, ~50-100 lines, more Claude autonomy | |
| Decision trees | Branching if/then logic, ~100-200 lines | |

**User's choice:** Structured frameworks (Recommended)
**Notes:** None

### Q2: Where should worked examples come from?

| Option | Description | Selected |
|--------|-------------|----------|
| Seed from polymarket_claude | Transplant real examples from trade passes, learnings, reports | ✓ |
| Start empty, Claude populates | Frameworks only, Claude adds examples from experience | |
| Synthetic examples | Hypothetical examples, Claude replaces with real ones over time | |

**User's choice:** Seed from polymarket_claude (Recommended)
**Notes:** None

### Q3: Should skill docs be static or living?

| Option | Description | Selected |
|--------|-------------|----------|
| Living documents | Claude can add examples, refine frameworks, annotate based on outcomes | ✓ |
| Static references | Locked — all evolution in strategy.md and golden-rules.md | |
| Mostly static, appendable | Can append examples but not modify framework sections | |

**User's choice:** Living documents (Recommended)
**Notes:** None

### Q4: Load all skills at start or on-demand?

| Option | Description | Selected |
|--------|-------------|----------|
| On-demand loading | CLAUDE.md tells Claude WHEN to load each skill | ✓ |
| Load all at start | Read all 6 at session initialization | |
| You decide | Claude's discretion | |

**User's choice:** On-demand loading (Recommended)
**Notes:** None

---

## CLAUDE.md Design

### Q1: How prescriptive should the new CLAUDE.md be?

| Option | Description | Selected |
|--------|-------------|----------|
| Phase outline + guardrails | High-level 5-phase description, points to skills/knowledge, sets guardrails. ~150-250 lines | ✓ |
| Detailed step-by-step | Comprehensive instruction set without sub-agents. ~400-600 lines | |
| Minimal + trust Claude | Just goal, tools, core-principles. ~50-80 lines | |

**User's choice:** Phase outline + guardrails (Recommended)
**Notes:** None

### Q2: Where should the new CLAUDE.md live?

| Option | Description | Selected |
|--------|-------------|----------|
| polymarket-trader/.claude/CLAUDE.md | New directory, original stays untouched | ✓ |
| Rewrite in-place | Modify polymarket-agent/ directly | |
| You decide | Claude's discretion | |

**User's choice:** polymarket-trader/.claude/CLAUDE.md (Recommended)
**Notes:** None

### Q3: Permission settings for autonomous operation?

| Option | Description | Selected |
|--------|-------------|----------|
| Full autonomous permissions | Bash, Read, Write, Edit, WebSearch, WebFetch all allowed | ✓ |
| Restricted permissions | Only read + bash, write/edit require approval | |
| You decide | Based on ARCH-05 requirements | |

**User's choice:** Full autonomous permissions (Recommended)
**Notes:** None

### Q4: Self-modification boundaries?

| Option | Description | Selected |
|--------|-------------|----------|
| Designated sections only | OPERATOR-SET (immutable) and CLAUDE-EDITABLE sections | ✓ |
| Full freedom | Claude can rewrite any part | |
| Append-only log | Separate self-improvement log, CLAUDE.md stays operator-controlled | |

**User's choice:** Designated sections only (Recommended)
**Notes:** None

---

## Claude's Discretion

- Sub-agent removal approach (how to distill vs delete logic from 8 existing agents)
- Exact skill doc internal formatting within the structured framework pattern

## Deferred Ideas

None — discussion stayed within phase scope
