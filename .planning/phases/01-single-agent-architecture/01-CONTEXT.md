# Phase 1: Single Agent Architecture - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the sub-agent pipeline (8 agents in `.claude/agents/`) with a single autonomous trader session. Claude operates as one session per trading cycle — no Task-spawning — loading skill reference docs on demand. Copy polymarket-agent/ into polymarket-trader/ and restructure there.

</domain>

<decisions>
## Implementation Decisions

### Skill Document Structure
- **D-01:** Skill docs use **structured frameworks** — step-by-step with decision criteria, formulas, and 2-3 worked examples. ~200-400 lines each. Not checklists or decision trees.
- **D-02:** Seed examples from **polymarket_claude/** real trade data — passes/ for evaluate-edge, trades/ for size-position, learnings/ for post-mortem, reports/ for cycle-review. Claude evolves examples over time.
- **D-03:** Skill docs are **living documents** — Claude can add examples, refine frameworks, and annotate decision criteria based on trading outcomes. Only core-principles.md stays immutable.
- **D-04:** Skills are loaded **on-demand** during the relevant phase of the trading cycle. CLAUDE.md tells Claude WHEN to load each skill (e.g., "Before analyzing a market, read .claude/skills/evaluate-edge.md"). Not all loaded at session start.

### CLAUDE.md Design
- **D-05:** CLAUDE.md uses **phase outline + guardrails** style — describes the 5 trading cycle phases (Check Positions, Find Opportunities, Analyze Markets, Size+Execute, Learn+Evolve) at a high level, points to skill docs and knowledge base, sets guardrails. ~150-250 lines. Claude decides how to execute within each phase.
- **D-06:** New CLAUDE.md lives at **polymarket-trader/.claude/CLAUDE.md**. polymarket-agent/ stays untouched as reference. Copy-and-restructure is part of Phase 1.
- **D-07:** settings.json pre-configured with **full autonomous permissions** — Bash, Read, Write, Edit, WebSearch, WebFetch all allowed. Required for future cron automation.
- **D-08:** Self-modification uses **designated sections** — CLAUDE.md has `<!-- OPERATOR-SET -->` sections (immutable: phase structure, guardrails) and `<!-- CLAUDE-EDITABLE -->` sections (Claude's process notes, learnings). Structure stays stable.

### Claude's Discretion
- Sub-agent removal approach: Claude decides how to distill useful reasoning patterns from existing agents into skill docs vs what to simply delete. The 8 agents (scanner, analyst, risk-manager, planner, reviewer, strategy-updater, position-monitor, outcome-analyzer) contain logic that maps to the 6 skills.
- Exact skill doc section headings and internal formatting within the structured framework pattern.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Source Projects
- `polymarket-agent/.claude/agents/` — All 8 existing sub-agent definitions to understand current logic before removal
- `polymarket-agent/.claude/CLAUDE.md` — Current orchestration CLAUDE.md to understand what's being replaced
- `polymarket-agent/.claude/settings.json` — Current settings to inform new autonomous permissions config

### Knowledge Source
- `polymarket_claude/output/passes/` — Real trade passes for seeding evaluate-edge skill examples
- `polymarket_claude/output/trades/` — Trade execution records for seeding size-position skill examples
- `polymarket_claude/output/learnings/` — Learnings for seeding post-mortem skill examples
- `polymarket_claude/output/reports/` — Cycle reports for seeding cycle-review skill examples

### Existing Skills Reference
- `AI-Trader/skills/` — Alternative skill doc format (SKILL.md files) for reference, not to copy

### Codebase Analysis
- `.planning/codebase/ARCHITECTURE.md` — Full architecture analysis including agent coordination patterns
- `.planning/codebase/STRUCTURE.md` — Directory layout and file purposes

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- 8 sub-agent markdown files in `.claude/agents/` contain reasoning frameworks that map to the 6 new skills
- Current CLAUDE.md has a working 10-step trading cycle pipeline — the new 5-phase cycle is a simplification of this
- AI-Trader `skills/` directory shows an alternative skill doc format (not copied, but informative)

### Established Patterns
- Sub-agents use JSON output schemas for structured handoff — new skill docs don't need this since there's one session
- State files in `state/` (strategy.md, core-principles.md, cycles/, reports/) remain the same structure
- CLI tools in `tools/` are stateless JSON-output scripts — these stay unchanged

### Integration Points
- New polymarket-trader/ is a copy of polymarket-agent/ with `.claude/` restructured
- `.claude/agents/` → deleted, replaced by `.claude/skills/`
- `.claude/CLAUDE.md` → rewritten as autonomous trader instructions
- `.claude/settings.json` → updated with full autonomous permissions
- All `lib/`, `tools/`, `tests/`, `state/` directories carry over unchanged

</code_context>

<specifics>
## Specific Ideas

- Skill doc preview format shown in discussion: "When to Load" section, numbered "Framework" steps, "Examples" section with real trade data
- CLAUDE.md preview format: Session Start (read strategy, principles, recent reports), then 5 lettered phases (A-E), then Guardrails section
- Self-modification pattern: `<!-- OPERATOR-SET -->` and `<!-- CLAUDE-EDITABLE -->` HTML comments to mark sections

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-single-agent-architecture*
*Context gathered: 2026-04-03*
