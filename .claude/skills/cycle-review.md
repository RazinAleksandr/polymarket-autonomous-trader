# Cycle Review

<!-- CLAUDE-EDITABLE: Claude may add examples, refine criteria, annotate decisions -->

## When to Load

Load this skill during **Phase E (Learn and Evolve)** at the end of every trading cycle to
write the cycle report and update strategy. This is the LAST skill loaded in a cycle -- it
synthesizes all prior analysis into a permanent record and controlled strategy evolution.

**Also reference:** `state/strategy.md` for current strategy,
`state/core-principles.md` for immutable guardrails (NEVER modify),
`.claude/skills/post-mortem.md` for resolved position analysis,
`.claude/skills/calibration-check.md` for accuracy data,
`knowledge/golden-rules.md` for accumulated wisdom.

---

## Framework

### Step 1: Gather Cycle Data

Read all cycle artifacts from `state/cycles/{cycle_id}/`:

1. **Position monitoring data:**
   - `position_monitor.json` (if Phase A produced monitoring output)
   - Any sell results from positions exited this cycle

2. **Market discovery data:**
   - `scanner_output.json` -- markets discovered
   - Filtered candidate list (from Phase B sweet-spot filtering)

3. **Analysis data:**
   - `analysis_{market_id}.json` -- individual market analyses (from Phase C)
   - Number of markets analyzed vs discovered

4. **Execution data:**
   - `risk_output.json` -- position sizing decisions (from Phase D)
   - `execution_results.json` -- executed trades (from Phase D)
   - Any trade failures or skipped trades

5. **Learning data:**
   - Post-mortem results (from post-mortem.md skill earlier in Phase E)
   - Calibration updates (from calibration-check.md skill earlier in Phase E)

6. **Portfolio state:**
   - Run: `python tools/get_portfolio.py --include-risk --pretty`
   - Current positions, exposure, unrealized P&L

7. **Previous cycle reports:**
   - Read the 3 most recent `state/reports/cycle-*.md` files
   - Check for continuity: are strategy suggestions from last cycle reflected in behavior?

---

### Step 2: Write Cycle Report

Write the cycle report to `state/reports/cycle-{cycle_id}.md` with these sections:

```markdown
# Cycle Report: {cycle_id}

**Date:** {YYYY-MM-DD HH:MM UTC}
**Duration:** {how long the cycle took}
**Previous cycle:** {previous cycle_id or "None (inaugural)"}

---

## Summary

{2-3 sentence overview: how many markets scanned, how many analyzed, how many traded,
total capital deployed, any resolved positions, net P&L impact}

---

## Markets Analyzed

| Market | Category | Est. Prob | Edge | Confidence | Decision |
|--------|----------|----------|------|------------|----------|
| {question} | {cat} | {prob} | {edge} | {conf} | {TRADE/PASS + reason} |

**Discovery stats:** {N} markets scanned, {M} passed sweet-spot filter, {K} analyzed
**Pass rate:** {K}/{M} analyzed -> {T} traded ({percentage}%)

---

## Trades Executed

| Market | Side | Size | Entry Price | Edge | Reasoning |
|--------|------|------|-------------|------|-----------|
| {question} | {YES/NO} | ${size} | ${price} | {edge} | {1-line reasoning} |

**Capital deployed this cycle:** ${total}
**New positions:** {count}

---

## Portfolio State

**Total positions:** {N}
**Total exposure:** ${amount} ({percentage}% of bankroll)
**Remaining capacity:** ${amount} ({percentage}% of bankroll)
**Unrealized P&L:** ${amount}

| Position | Side | Entry | Current | Unrealized P&L | Days Held |
|----------|------|-------|---------|----------------|-----------|
| {question} | {YES/NO} | ${entry} | ${current} | ${pnl} | {days} |

---

## Resolutions

{If no resolutions: "No markets resolved this cycle."}

| Market | Side | Entry | Outcome | P&L | Brier |
|--------|------|-------|---------|-----|-------|
| {question} | {YES/NO} | ${entry} | {WON/LOST} | ${pnl} | {score} |

**Resolved this cycle:** {N} positions
**Realized P&L:** ${total}
**Average Brier score:** {score}

---

## Lessons

{1-3 observations from this cycle. These are specific, not generic.}

1. {lesson 1 — cite specific market or data}
2. {lesson 2 — cite specific observation}
3. {lesson 3 — if applicable}

---

## Strategy Suggestions

{0-3 specific changes to consider, with evidence.}

{If none: "No strategy changes warranted this cycle — insufficient new evidence."}

1. **Suggestion:** {what to change}
   **Evidence:** {specific outcome, calibration data, or pattern}
   **Category:** {Market Selection | Analysis Approach | Risk Parameters | Trade Entry/Exit}
   **Confidence:** {High | Medium | Low}

---

## Cycle Metrics

| Metric | Value |
|--------|-------|
| Markets scanned | {N} |
| Markets analyzed | {N} |
| Trades executed | {N} |
| Capital deployed | ${N} |
| Positions resolved | {N} |
| Realized P&L | ${N} |
| Win rate (if resolutions) | {N}% |
| Avg Brier (if resolutions) | {N} |
| Strategy changes | {N} |
```

---

### Step 3: Evaluate Strategy Suggestions

For each suggestion from Step 2, apply the evidence hierarchy to determine whether
to implement it:

**Evidence Tier 1: Outcome-Backed (highest weight)**
- Derived from actual P&L results
- Example: "Lost money on 4/5 crypto trades" -- directly backed by realized losses
- Weight: implement if the pattern is across 3+ trades

**Evidence Tier 2: Calibration-Backed (high weight)**
- Derived from calibration data (Brier scores, category accuracy)
- Example: "Overestimate crypto probability by 15pp" -- backed by calibration analysis
- Weight: implement if based on 5+ data points

**Evidence Tier 3: Process-Based (lower weight)**
- Derived from cycle observations (not yet backed by outcomes)
- Example: "Sports edges seem small" -- observation without enough outcome data
- Weight: defer unless corroborated by Tier 1 or Tier 2 evidence

**Decision matrix:**

| Evidence Tier | Data Points | Action |
|--------------|-------------|--------|
| Tier 1 | 3+ trades | Implement |
| Tier 1 | 1-2 trades | Defer (note for future review) |
| Tier 2 | 5+ data points | Implement |
| Tier 2 | < 5 data points | Defer |
| Tier 3 | Any | Defer unless corroborated |

**For each suggestion, record the evaluation:**
```
Suggestion: [what]
Evidence tier: [1/2/3]
Data points: [N]
Decision: [IMPLEMENT / DEFER]
Rationale: [why]
```

---

### Step 4: Update Strategy (Maximum 0-3 Changes Per Cycle)

Read `state/strategy.md`. For each APPROVED suggestion (from Step 3):

1. **Identify the target section:**
   - Market Selection (which markets to trade)
   - Analysis Approach (how to estimate probabilities)
   - Risk Parameters (sizing, exposure limits, Kelly fraction)
   - Trade Entry/Exit (when to enter, when to sell)

2. **Check for duplicates:**
   - Search existing strategy rules for overlap
   - If the rule already exists in some form, refine rather than add
   - If it contradicts an existing rule, do NOT overwrite -- add to "## Needs Review"

3. **Add the new rule with full provenance:**
   ```markdown
   - **[Date added]:** [Rule text]
     - Based on: [specific trade citation or calibration data]
     - Evidence: [Tier 1/2/3], [N] data points
     - Expected impact: [what behavior this changes]
   ```

4. **Enforce the 0-3 change limit:**
   - Never apply more than 3 changes in a single cycle
   - This prevents strategy drift from a single bad cycle
   - If more than 3 suggestions are approved, prioritize by:
     a. Loss-preventing changes first
     b. Tier 1 evidence first
     c. Larger expected impact first
   - Deferred changes carry over to next cycle's review

5. **NEVER modify core-principles.md.** Strategy evolution happens in strategy.md only.
   Core principles are immutable guardrails set by the operator.

---

### Step 5: Commit Changes

After writing the cycle report and updating strategy:

1. **Write updated `state/strategy.md`** with new rules (if any)
2. **Log strategy changes:**
   - If changes were made: "Strategy updated: {N} changes applied -- [brief description of each]"
   - If no changes: "Strategy unchanged this cycle -- no actionable evidence"
3. **Verify the cycle report** exists at `state/reports/cycle-{cycle_id}.md`
4. **Verify the strategy file** has the correct number of new rules

---

## Anti-Drift Rules

These rules prevent strategy corruption from emotional reactions to short-term results:

1. **Never remove existing rules** -- only deprecate with evidence
   - Deprecation format: "~~[old rule]~~ Deprecated [date]: [evidence for removal based on N trades]"
   - Requires 5+ trades showing the rule no longer applies

2. **Never change more than 3 rules per cycle**
   - Prevents overreaction to a single bad cycle
   - Forces prioritization of the most impactful changes

3. **Every new rule must cite a specific trade or calibration data point**
   - No vague rules like "Be more careful" -- must be evidence-backed
   - The citation ensures the rule is grounded in reality

4. **If conflicting rules emerge, flag for human review**
   - Add to `state/strategy.md` under a "## Needs Review" section
   - Include both rules, the evidence for each, and the conflict
   - Do NOT resolve the conflict autonomously -- let the operator decide

5. **Track rule effectiveness over time**
   - After 10 trades since a rule was added, check: has it improved outcomes?
   - If not, flag for review (not automatic removal)
   - Format: "Rule added [date], 10 trades since: [improved/no change/worsened]"

6. **No retroactive strategy changes**
   - Rules apply to FUTURE trades only
   - Do not re-evaluate past trades under new rules
   - Past trades are evaluated under the rules that were active at entry time

---

## Examples

### Example 1: Full Cycle Report

```markdown
# Cycle Report: 20260401-140000

**Date:** 2026-04-01 14:00 UTC
**Duration:** 12 minutes
**Previous cycle:** 20260331-140000

---

## Summary

Scanned 20 markets, analyzed 6 candidates, executed 2 trades deploying $550.
One position (Arsenal EPL) resolved profitably (+$35). Portfolio at 18% exposure
with 4 open positions. Net realized P&L this cycle: +$35.

---

## Markets Analyzed

| Market | Category | Est. Prob | Edge | Confidence | Decision |
|--------|----------|----------|------|------------|----------|
| Arsenal EPL winner? | Sports | 0.95 | +0.055 | 0.85 | TRADE (strong base rate) |
| BTC $100k June? | Crypto | 0.45 | +0.10 | 0.50 | TRADE (mid-range opportunity) |
| Fed rate cut May? | Finance | 0.70 | +0.02 | 0.60 | PASS (edge < 0.04) |
| Iran regime fall? | Politics | 0.02 | -0.005 | 0.40 | PASS (price outside sweet spot) |
| Oil $100 March? | Commodities | 0.92 | +0.032 | 0.70 | PASS (edge < 0.04) |
| Oscars best picture? | Entertainment | 0.35 | +0.05 | 0.35 | PASS (low confidence) |

**Discovery stats:** 20 scanned, 8 passed filter, 6 analyzed
**Pass rate:** 6 analyzed -> 2 traded (33%)

---

## Trades Executed

| Market | Side | Size | Entry Price | Edge | Reasoning |
|--------|------|------|-------------|------|-----------|
| Arsenal EPL winner? | YES | $300 | $0.895 | +0.055 | 9pt lead with 9 games, 97-99% base rate |
| BTC $100k June? | YES | $250 | $0.45 | +0.10 | Institutional momentum, halving cycle |

**Capital deployed this cycle:** $550
**New positions:** 2

---

## Resolutions

| Market | Side | Entry | Outcome | P&L | Brier |
|--------|------|-------|---------|-----|-------|
| Arsenal EPL | YES | $0.895 | WON | +$35.00 | 0.0025 |

**Resolved this cycle:** 1 position
**Realized P&L:** +$35.00
**Average Brier score:** 0.0025

---

## Lessons

1. Sports markets with strong statistical base rates continue to be our best category.
   Arsenal at 0.895 with 97-99% base rate produced a clean win with excellent Brier (0.0025).
2. The sweet-spot filter correctly eliminated 12/20 markets -- the 8 that passed were
   all reasonable candidates. The filter is working as intended.
3. We passed on oil $100 (edge 0.032 < 0.04 threshold) -- correct decision based on our
   minimum edge rule, though the original trader took the trade and lost $300.

---

## Strategy Suggestions

1. **Suggestion:** Actively seek sports markets with clear base rates
   **Evidence:** Arsenal EPL win (Tier 1, 1 trade) + consistent category performance
   **Category:** Market Selection
   **Confidence:** Medium (only 1 resolved trade so far, need more data)

---

## Cycle Metrics

| Metric | Value |
|--------|-------|
| Markets scanned | 20 |
| Markets analyzed | 6 |
| Trades executed | 2 |
| Capital deployed | $550 |
| Positions resolved | 1 |
| Realized P&L | +$35.00 |
| Win rate | 100% (1/1) |
| Avg Brier | 0.0025 |
| Strategy changes | 0 |
```

---

### Example 2: Strategy Update with Evidence

**Cycle context:** After 3 cycles with crypto trades, all 5 crypto positions have been
resolved. Results: 2 wins, 3 losses, total P&L -$260, average Brier 0.28.

**Strategy suggestion evaluation:**
```
Suggestion: Raise minimum edge threshold for crypto to 0.08
Evidence tier: Tier 1 (outcome-backed, 5 resolved trades)
Data points: 5 trades with -$260 P&L and 40% win rate
Decision: IMPLEMENT
Rationale: 5 trades is sufficient. The 40% win rate and negative P&L over 5 trades
is a clear signal. Raising the edge threshold forces us to only take crypto trades
where we have a larger margin of safety.
```

**Strategy update (added to state/strategy.md):**
```markdown
### Market Selection

- **2026-04-15:** Raise minimum edge threshold for crypto markets to 0.08 (8pp).
  - Based on: 5 crypto trades with -$260 total P&L, 40% win rate, 0.28 avg Brier
  - Evidence: Tier 1, 5 data points
  - Expected impact: Fewer crypto trades but higher quality; filters out marginal opportunities
    where our overconfidence bias causes losses
```

**Log:** "Strategy updated: 1 change applied -- raised crypto min edge to 0.08 based on
5 trades with -$260 P&L."

---

### Example 3: Cycle with No Changes

**Cycle context:** Inaugural cycle. 20 markets scanned, 5 analyzed, 2 traded.
No resolutions yet (positions are new). No calibration data yet.

**Strategy suggestion evaluation:**
```
Suggestion: None warranted
Evidence tier: N/A
Data points: 0 resolved trades, 0 calibration data points
Decision: N/A
Rationale: First cycle -- no outcome data exists to drive strategy changes.
All observations are Tier 3 (process-based) at best. Strategy will evolve
once positions start resolving and calibration data accumulates.
```

**Cycle report strategy section:**
```markdown
## Strategy Suggestions

No strategy changes warranted this cycle -- insufficient evidence.
This is the inaugural cycle; strategy changes will begin after positions resolve
and calibration data accumulates (typically after 3-5 cycles).
```

**Log:** "Strategy unchanged this cycle -- no actionable evidence (inaugural cycle)."

---

## Cycle Report Archive

All cycle reports are kept permanently in `state/reports/`. They serve as:

1. **Audit trail** -- every trading decision is recorded and justified
2. **Strategy context** -- future cycles read the last 3 reports for continuity
3. **Performance tracking** -- realized P&L, Brier scores, and win rates over time
4. **Learning history** -- lessons and strategy changes tracked chronologically
5. **Drift detection** -- comparing early vs recent reports reveals strategy evolution

**Naming convention:** `cycle-{cycle_id}.md` where cycle_id is `YYYYMMDD-HHMMSS`

**Never delete** cycle reports. If a report has errors, append a correction section
rather than modifying the original.

---

## Updating This Skill

After each cycle review:

1. **Add real examples** from actual cycle reports (supplement or replace hypothetical examples)
2. **Refine the report template** if sections are missing important information
3. **Adjust the evidence hierarchy** if Tier 3 observations are proving more predictive than expected
4. **Update anti-drift rules** if the current limits (3 changes/cycle) feel too restrictive
   or too permissive based on actual strategy evolution experience
5. **Improve strategy suggestion evaluation** based on which changes actually improved performance

Record changes with a date stamp and brief rationale.
