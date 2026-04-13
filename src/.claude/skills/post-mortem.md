# Post-Mortem

<!-- CLAUDE-EDITABLE: Claude may add examples, refine criteria, annotate decisions -->

## When to Load

Load this skill during **Phase E (Learn and Evolve)** when analyzing resolved positions and
extracting lessons. Run this AFTER resolution-parser.md has processed the raw resolution data
and produced outcome records with P&L calculations.

**Also reference:** `.claude/skills/resolution-parser.md` for outcome data,
`.claude/skills/calibration-check.md` for recording accuracy metrics,
`state/reports/cycle-*.md` for historical context,
`knowledge/golden-rules.md` for accumulated trading wisdom.

---

## Framework

### Step 1: Gather Resolved Position Data

Before analyzing, collect all data for each resolved position:

1. **Run resolution-parser first** (load `.claude/skills/resolution-parser.md` if not already loaded)
   - This produces outcome records with: market_id, question, category, our_side, outcome,
     entry_price, estimated_prob, confidence, edge, P&L, brier_score

2. **For each resolved position, assemble the full record:**
   - `market_id`: unique market identifier
   - `question`: the market question text
   - `category`: market category (crypto, politics, sports, commodities, etc.)
   - `entry_price`: what we paid per share
   - `estimated_prob`: our probability estimate at time of entry
   - `confidence`: our confidence level at entry
   - `edge`: calculated edge at entry (estimated_prob - market_price)
   - `recommended_side`: YES or NO (which side we took)
   - `outcome`: actual result (YES or NO resolved, or early sell)
   - `realized_pnl`: actual profit or loss in USDC
   - `brier_score`: prediction accuracy metric from resolution-parser
   - `reasoning`: our reasoning at time of entry (from trade record)
   - `entry_date`: when we entered
   - `resolution_date`: when the market resolved (or when we sold)
   - `hold_duration_days`: resolution_date - entry_date

3. **Also read recent cycle reports** for additional context:
   - Were there notes about this market in previous cycles?
   - Did the position monitor flag any concerns during the hold period?
   - Were there sell recommendations that we did or didn't act on?

---

### Step 2: Classify the Outcome

For each resolved position, classify into one of four categories:

**Category A: Correct + Profitable**
- Predicted the right direction AND made money
- Validate: Was the edge real, or did we get lucky?
- Check: Did the market move toward our estimate before resolution?
- If the price moved against us first then recovered, note the drawdown
- Key question: "Would we make this trade again with the same information?"

**Category B: Correct + Unprofitable**
- Predicted the right direction BUT lost money
- Common causes:
  - Fees ate the edge (especially small edges at high prices)
  - Price moved against us before resolution (entered too early)
  - Sold early at a loss before the market resolved in our favor
- Investigate: Was sizing too aggressive? Was entry timing poor?
- Key question: "Was the edge real but the execution flawed?"

**Category C: Incorrect + Small Loss**
- Wrong direction but the position was small (< 2% of bankroll loss)
- Review: What information was missing or misweighted?
- Check: Was confidence appropriately low (leading to small sizing)?
- If confidence was high but position was small due to exposure limits, that's different
  from deliberately small sizing
- Key question: "Did the sizing framework protect us from our wrong analysis?"

**Category D: Incorrect + Large Loss**
- Wrong direction AND significant loss (>= 2% of bankroll)
- **Deep investigation required** -- this category demands the most attention
- Was there overconfidence? (confidence > 0.7 but outcome wrong)
- Was research shallow? (fewer than 3 bear-case evidence points)
- Was there a known bias? (category we're historically bad at)
- Key question: "What systematic failure led to this loss?"

**Classification matrix:**

| Direction | P&L | Category | Investigation Depth |
|-----------|-----|----------|-------------------|
| Correct | Profit | A: Correct + Profitable | Light (validate edge) |
| Correct | Loss | B: Correct + Unprofitable | Medium (execution analysis) |
| Incorrect | Small loss | C: Incorrect + Small Loss | Medium (information review) |
| Incorrect | Large loss | D: Incorrect + Large Loss | Deep (systematic failure) |

---

### Step 3: Root Cause Analysis

For each loss (Categories B, C, D) or suboptimal win (Category A where edge was smaller
than expected), perform root cause analysis across five dimensions:

**Dimension 1: Information Gap**
- Did we miss a key data point that was publicly available?
- Was there breaking news between our entry and resolution that we should have anticipated?
- Did we rely on stale information? (check dates of our evidence sources)
- Example: "We missed the Fed surprise announcement because our analysis used data from 3 days prior"

**Dimension 2: Reasoning Error**
- Was the Bull/Bear analysis structurally flawed?
- Did we ignore or underweight the base rate?
- Did recency bias dominate? (overweighting last event vs long-term patterns)
- Did anchoring bias pull our estimate toward the market price?
- Did we confuse correlation with causation in our evidence chain?
- Example: "We estimated 92% based on proximity to target ($1.29 gap) but underweighted
  the base rate of geopolitical de-escalation events causing sharp reversals"

**Dimension 3: Sizing Error**
- Was the position too large relative to the confidence level?
- Did Kelly math suggest a smaller position that we overrode?
- Was the confidence-adjusted size appropriate, or was confidence inflated?
- Example: "Position was $400 but confidence was only 0.50 -- the sizing framework
  would have suggested $280 if we'd been honest about uncertainty"

**Dimension 4: Category Mismatch**
- Does this category systematically produce worse results for us?
- Check calibration data: what's our Brier score and win rate in this category?
- If category accuracy < 50% over 5+ trades, flag for minimum-edge increase
- Example: "Third consecutive crypto loss -- Brier score for crypto is 0.45 vs 0.15 overall"

**Dimension 5: Timing Error**
- Was the entry too early (price moved against before moving with)?
- Was the entry too late (most of the edge had already been captured)?
- Could we have gotten a significantly better price by waiting?
- Was the resolution timeline misjudged? (thought it would resolve in 2 weeks, took 2 months)
- Example: "Entered at $0.65 but price dropped to $0.50 before recovering to $1.00 --
  could have entered 23% cheaper with patience"

**Record the primary root cause** (the single most impactful factor) and any
secondary contributing factors.

---

### Step 4: Extract Actionable Lessons

Each lesson extracted from a post-mortem MUST meet three criteria:

**Criterion 1: Specific**
- Bad: "Be careful with crypto markets"
- Good: "Crypto markets with active geopolitical drivers and < 48h to resolution tend to
  gap 10%+ on sudden de-escalation news. Lower max confidence to 0.65 for these setups."
- The lesson must be specific enough that another trader could apply it mechanically

**Criterion 2: Evidence-Backed**
- Every lesson MUST cite the specific trade that produced it:
  - Market ID and question
  - Entry date and resolution date
  - Entry price, estimated probability, and actual outcome
  - Realized P&L
- Format: `Evidence: [market question] — entered [date] at [price], estimated [prob],
  resolved [outcome], P&L: [amount]`

**Criterion 3: Actionable**
- The lesson must change a specific future behavior. Types of actionable changes:
  - **Sizing rule change**: "Reduce max position to 3% for commodity markets"
  - **Category filter**: "Raise min edge to 8pp for entertainment markets"
  - **Research step**: "Always check Fed calendar before entering macro-sensitive trades"
  - **Confidence adjustment**: "Cap confidence at 0.70 for markets dependent on negotiations"
  - **Timing rule**: "Wait for confirmation candle before entering momentum trades"

**Record each lesson in this format:**
```
LESSON: [concise statement of the lesson]
Evidence: [market_id] [market question] — [date], [entry] -> [outcome], P&L: [amount]
Action: [specific behavioral change to implement]
Applies to: [category/market type/all]
```

---

### Step 5: Determine if Golden Rule Warranted

A golden rule is a permanent addition to `knowledge/golden-rules.md` -- a battle-tested
principle extracted from actual trading outcomes. Golden rules are the highest-weight
lessons and persist across strategy changes.

**A golden rule is warranted when ANY of these conditions is met:**

1. **Repeated pattern**: The same mistake pattern has occurred 2+ times across different trades
   - Example: "Overconfident in commodity markets driven by geopolitical events" (seen in
     crude oil AND natural gas trades)

2. **Single large loss**: A single mistake caused > 2% bankroll loss
   - The magnitude of the loss alone justifies a permanent rule
   - Example: "RULE: Never assign > 80% probability to markets dependent on active
     geopolitical negotiations" -- learned from a $350 loss (3.5% of bankroll)

3. **Generalizable across categories**: The lesson applies broadly, not just to one market type
   - Example: "RULE: Always check for upcoming binary events (elections, hearings, data releases)
     within the resolution window before entering any trade"

**Golden rule format:**
```
RULE: [clear, imperative statement]
Learned from: [trade citation(s) with dates and P&L]
Added: [date]
Category: [which market types this applies to, or "ALL"]
```

**Golden rule governance:**
- Golden rules are NEVER deleted, only deprecated with evidence
- Deprecation requires 5+ trades showing the rule no longer applies
- Maximum 3 new golden rules per cycle (prevent rule explosion)
- If conflicting with an existing rule, flag for human review

---

### Step 6: Update Knowledge Files

After completing the post-mortem analysis:

1. **Append lessons to the cycle report** (written by cycle-review.md skill)
2. **Add golden rules** to `knowledge/golden-rules.md` if warranted
3. **Flag category concerns** for calibration-check.md to investigate
4. **Note strategy suggestions** for cycle-review.md to evaluate

---

## Examples

### Example 1: Correct Trade Post-Mortem (Arsenal EPL)

**Resolved position data:**
- Market: "Will Arsenal win the 2025-26 English Premier League?"
- Category: Sports
- Entry date: 2026-03-15, Entry price: $0.895 (YES)
- Estimated probability: 0.95, Confidence: 0.85, Edge: 0.055
- Resolution date: 2026-05-27, Outcome: YES
- Realized P&L: +$35.00 (335 shares * $1.00 - $300 cost)
- Brier score: 0.0025

**Classification:** Category A -- Correct + Profitable

**Root cause analysis:** N/A (profitable trade), but validate the edge:
- Our estimate of 0.95 was reasonable given the 9-point lead with 9 games remaining
- Historical base rate (97-99%) supported the thesis
- The market at 0.895 was slightly underpricing the outcome
- The 5.5pp edge was real, confirmed by resolution
- The bear case risks (CL fatigue, injuries) did not materialize

**Lessons extracted:**
```
LESSON: Sports markets with strong statistical base rates are high-reliability trades.
         A 9-point lead with 9 games left converts 97-99% historically, and the market
         consistently underprices these certainties by 3-8pp.
Evidence: Arsenal EPL — 2026-03-15 at $0.895, estimated 0.95, resolved YES, P&L: +$35
Action: Actively seek out sports markets with clear historical base rates as core positions.
Applies to: Sports
```

**Golden rule assessment:** Not yet -- need 2+ similar wins to establish the pattern.
Mark for tracking: "Sports base-rate thesis" with 1/2 confirmations needed.

---

### Example 2: Loss Post-Mortem Leading to Golden Rule (Crude Oil)

**Resolved position data:**
- Market: "Will crude oil (CL) hit $100 by end of March?"
- Category: Commodities
- Entry date: 2026-03-15, Entry price: $0.888 (YES)
- Estimated probability: 0.92, Confidence: 0.70, Edge: 0.032
- Resolution date: 2026-03-31, Outcome: NO (ceasefire announcement crashed oil March 25)
- Realized P&L: -$300.00 (total loss)
- Brier score: 0.8464

**Classification:** Category D -- Incorrect + Large Loss (3% of bankroll)

**Root cause analysis:**

- **Primary: Reasoning Error** -- We treated proximity to target ($1.29 gap, 1.3%) as
  high probability without adequately weighting the binary nature of geopolitical events.
  A ceasefire/de-escalation was always possible and would crash oil dramatically.
  We assigned only 8% to the failure case when geopolitical tail risks warranted 15-20%.

- **Secondary: Information Gap** -- Ceasefire negotiations were reportedly underway but
  we didn't search specifically for diplomatic developments. A "Iran ceasefire talks"
  web search on March 20 would have revealed this risk.

- **Secondary: Category Mismatch** -- Commodity markets driven by active conflicts have
  inherently binary outcomes (escalation vs de-escalation) that make probability estimation
  unreliable.

**Lessons extracted:**
```
LESSON: Commodity markets driven by active geopolitical conflicts have binary risk profiles
        that make high-confidence estimates unreliable. De-escalation events cause sharp
        reversals (10-20%+) that can occur without warning.
Evidence: Crude oil $100 — 2026-03-15 at $0.888, estimated 0.92, resolved NO, P&L: -$300
Action: Cap max confidence at 0.65 for commodity markets with active geopolitical drivers.
        Always search for diplomatic/negotiation news before entering.
Applies to: Commodities (geopolitical)

LESSON: Proximity to a price target does not equal high probability when the underlying
        driver is a binary geopolitical event. The $1.29 gap seemed small, but the event
        driving oil prices was binary (conflict continues vs ceasefire).
Evidence: Crude oil $100 — 2026-03-15 at $0.888, estimated 0.92, resolved NO, P&L: -$300
Action: When the price driver is a binary event (war/peace, approval/rejection), estimate
        probability based on the event likelihood, not the price proximity to target.
Applies to: All categories with binary event drivers
```

**Golden rule assessment:** Single loss > 2% of bankroll -- golden rule warranted:
```
RULE: Never assign > 80% probability to markets whose outcome depends on active
      geopolitical negotiations or binary diplomatic events. De-escalation can happen
      without warning and causes 10-20%+ reversals.
Learned from: Crude oil $100 March 2026 — entered $0.888, estimated 0.92, lost $300 (3%)
Added: 2026-03-31
Category: Commodities, Politics (geopolitical)
```

---

### Example 3: Category-Level Pattern Detection

**Scenario:** After processing 8 resolved positions across 3 cycles, we notice a pattern
in the crypto category.

**Resolved crypto positions (aggregate):**

| Trade | Entry Price | Est. Prob | Outcome | P&L | Brier |
|-------|------------|-----------|---------|-----|-------|
| BTC $100k June | $0.45 | 0.55 | NO | -$200 | 0.3025 |
| ETH $5k April | $0.30 | 0.42 | NO | -$150 | 0.1764 |
| SOL $250 May | $0.60 | 0.70 | YES | +$120 | 0.0900 |
| BTC $80k March | $0.78 | 0.85 | YES | +$50 | 0.0225 |
| ETH merge delay | $0.35 | 0.45 | YES | -$80 | 0.3025 |

**Category statistics:**
- Win rate: 2/5 = 40% (below 50% threshold)
- Average Brier score: 0.179 (acceptable but higher than overall 0.12)
- Total P&L: -$260
- Average confidence at entry: 0.59

**Pattern detected:** Systematic overconfidence in crypto markets. Our estimates are
consistently too high -- we assign probabilities averaging 0.59 but the actual outcome
rate is 0.40. This is a 19 percentage point overconfidence bias.

**Category-level lessons:**
```
LESSON: We are systematically overconfident in crypto markets by approximately 19pp.
        Our average estimate is 0.59 but actual win rate is 0.40 over 5 trades.
Evidence: Aggregate of 5 crypto trades (BTC $100k, ETH $5k, SOL $250, BTC $80k, ETH merge)
          Total P&L: -$260, Avg Brier: 0.179, Win rate: 40%
Action: Apply -0.15 calibration correction to all crypto probability estimates.
        Raise min edge threshold to 0.08 for crypto markets until win rate improves above 50%.
Applies to: Crypto

LESSON: Crypto markets with high volatility regimes are not well-suited to base-rate
        analysis because regime changes (regulatory news, macro shifts) invalidate
        historical patterns rapidly.
Evidence: Aggregate crypto performance — -$260 over 5 trades despite reasonable confidence
Action: For crypto markets, weight recent momentum (7-day price action) more heavily
        than historical base rates. Limit research horizon to 30 days.
Applies to: Crypto
```

**Golden rule assessment:** Pattern across 5 trades warrants a golden rule:
```
RULE: Apply a -0.15 calibration correction to all crypto probability estimates until
      the crypto Brier score drops below 0.15 and win rate exceeds 50% over 10+ trades.
Learned from: 5 crypto trades totaling -$260 P&L with 40% win rate (March-April 2026)
Added: 2026-04-15
Category: Crypto
```

---

## Post-Mortem Checklist

Before concluding a post-mortem session, verify:

- [ ] All resolved positions have been classified (A/B/C/D)
- [ ] Root cause analysis completed for all losses (Categories B, C, D)
- [ ] At least one lesson extracted per resolved position
- [ ] All lessons meet the Specific + Evidence-Backed + Actionable criteria
- [ ] Golden rules evaluated for each loss
- [ ] Category-level patterns checked (if 5+ trades in any category)
- [ ] Findings recorded for cycle-review skill to incorporate

---

## Updating This Skill

After each batch of post-mortems:

1. **Add real examples** -- replace or supplement the hypothetical examples above with
   actual post-mortem analyses from resolved trades
2. **Refine root cause categories** -- if new failure modes emerge that don't fit the
   five dimensions, add them
3. **Update golden rule thresholds** -- if 2% bankroll loss threshold feels too high
   or too low based on actual experience, adjust with evidence
4. **Track lesson effectiveness** -- do extracted lessons actually improve future performance?
   Annotate lessons with "VALIDATED" or "INEFFECTIVE" after 5+ subsequent trades

Record changes with a date stamp and brief rationale.
