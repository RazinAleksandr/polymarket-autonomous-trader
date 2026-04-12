# Resolution Parser

<!-- CLAUDE-EDITABLE: Claude may add examples, refine criteria, annotate decisions -->

## When to Load

Load this skill during **Phase A (Check Positions)** when checking for resolved markets and
calculating outcomes, and during **Phase E (Learn and Evolve)** when analyzing trade performance
to update strategy.

**Also reference:** `tools/check_resolved.py` for resolution detection,
`tools/get_portfolio.py` for current positions, `lib/db.py` for trade history queries,
`state/performance.md` for historical performance tracking.

---

## Framework

### Step 1: Check for Resolved Markets

Detect which open positions have resolved (market closed with a definitive outcome):

1. **Run the resolution checker:**
   ```bash
   python tools/check_resolved.py --pretty
   ```
   This queries the Gamma API for `market.closed` status on all open positions in the database.

2. **Parse the output:** The tool returns a list of resolved markets with:
   - `market_id`: the unique market identifier
   - `question`: the market question text
   - `outcome`: YES or NO (which side won)
   - `resolution_date`: when the market was officially resolved
   - `our_side`: which side we held (YES or NO)
   - `won`: boolean — did our side win?

3. **Handle edge cases:**
   - Market still open (not resolved yet) → skip, check again next cycle
   - Market resolved but our position was already closed (sold early) → skip
   - Resolution contested or delayed → note as "PENDING RESOLUTION" and recheck next cycle

---

### Step 2: Record Outcomes

For each newly resolved market, build the complete outcome record:

1. **Match to original trade:**
   - Query the trading database for the BUY entry with this `market_id`
   - Extract from the original trade record:
     - `entry_price`: what we paid per share
     - `estimated_prob`: our probability estimate at entry time
     - `edge`: the edge we calculated when entering
     - `confidence`: our confidence level at entry
     - `reasoning`: why we took the trade
     - `category`: market category (crypto, politics, sports, etc.)
     - `entry_date`: when we entered the position
     - `size_usdc`: how much we invested

2. **Calculate actual outcome value:**
   - If our side WON: `actual_outcome = 1.0` (each share pays $1.00)
   - If our side LOST: `actual_outcome = 0.0` (shares worth nothing)
   - If we sold early (before resolution): `actual_outcome = sell_price`
     (the exit price reflects the market's updated probability at sell time)

3. **Calculate P&L:**
   ```
   For resolved positions:
     payout = shares * actual_outcome  (shares * $1.00 if won, $0.00 if lost)
     cost_basis = size_usdc  (what we paid to enter)
     realized_pnl = payout - cost_basis
   
   For early sells:
     sell_proceeds = shares * sell_price
     cost_basis = size_usdc
     realized_pnl = sell_proceeds - cost_basis
   ```

4. **Account for fees:**
   - Trading fees reduce realized P&L
   - The fee calculation is in `lib/fees.py` — category-specific fee rates apply
   - Net P&L: `realized_pnl - total_fees`

---

### Step 3: Calculate Prediction Accuracy

Measure how well our probability estimates matched reality:

1. **Brier Score** (primary accuracy metric):
   ```
   brier_score = (estimated_prob - actual_outcome)^2
   ```
   
   | Brier Score | Interpretation |
   |-------------|---------------|
   | 0.00 | Perfect prediction (estimated exactly matched outcome) |
   | 0.00-0.10 | Excellent — well-calibrated estimate |
   | 0.10-0.25 | Acceptable — some miscalibration but reasonable |
   | 0.25-0.50 | Poor — significant prediction error |
   | 0.50+ | Very poor — worse than random |
   | 1.00 | Worst possible (predicted 100% confident, was 100% wrong) |
   
   **Benchmark:** Random prediction (always guessing 0.5) gives Brier = 0.25.
   We should consistently beat 0.25 to demonstrate skill.

2. **Error in percentage points:**
   ```
   error_pp = |estimated_prob - actual_outcome| * 100
   ```
   Example: Estimated 0.95, actual 1.0 → error = 5 percentage points

3. **Direction accuracy:**
   - Did we correctly predict which side would win?
   - If `estimated_prob > 0.5` and `actual_outcome = 1.0` → correct direction
   - If `estimated_prob < 0.5` and `actual_outcome = 0.0` → correct direction
   - Track this as a simple win/loss for directional accuracy

---

### Step 4: Categorize the Outcome

Classify each resolved position along multiple dimensions:

1. **By category:**
   - Record the market category (crypto, politics, sports, commodities, etc.)
   - Track category-level statistics: win rate, avg Brier score, total P&L
   - Use this to identify strong and weak categories over time

2. **Edge quality assessment:**
   | Criteria | Classification |
   |----------|---------------|
   | Correct direction AND profitable | **Real edge** — the market was mispriced and we capitalized |
   | Correct direction BUT unprofitable (fees/timing) | **Edge existed** — execution or fees ate the profit |
   | Wrong direction BUT small loss | **No edge** — we were wrong but sized appropriately |
   | Wrong direction AND large loss | **Anti-edge** — we were wrong and exposed; investigate |

3. **Calibration assessment:**
   | Pattern | Classification |
   |---------|---------------|
   | estimated_prob > actual_outcome (when winning) | **Overconfident** — we overestimated probability |
   | estimated_prob < actual_outcome (when winning) | **Underconfident** — we underestimated (left money on table) |
   | estimated_prob close to actual_outcome | **Well-calibrated** — estimates were accurate |

4. **Timing assessment:**
   - How long did we hold? (entry_date to resolution_date)
   - Was the hold period within our expected timeframe?
   - Could we have entered at a better price by waiting?

---

### Step 5: Extract Lessons

For each resolved position, extract actionable learnings:

1. **What did we get right?**
   - Was our thesis confirmed? (e.g., "Arsenal's 9-point lead was indeed insurmountable")
   - Was our timing correct? (entered before the market repriced)
   - Was our sizing appropriate? (didn't overexpose on a single bet)

2. **What did we get wrong?**
   - Was our thesis invalid? (e.g., "We underestimated geopolitical risk")
   - Was our timing off? (entered too early/late, could have gotten better price)
   - Did we miss key information? (news event we should have caught)

3. **What would we do differently?**
   - Different sizing? (too big → reduce, too small → increase)
   - Different entry? (price target, wait for better odds)
   - Pass entirely? (was the edge real or imagined?)

4. **Should this inform a golden rule?**
   - If we see a pattern of similar mistakes across 3+ trades, create a golden rule
   - Example: "Never bet on award shows — consistently wrong" → add to golden rules
   - Example: "Sports bets with strong base rates are our best category" → increase allocation

---

## Resolution Mechanics by Market Category

Different categories resolve through different mechanisms. Understanding resolution
mechanics helps anticipate timing and dispute risks:

| Category | Typical Resolution | Data Source | Common Pitfalls |
|----------|-------------------|-------------|-----------------|
| Crypto | Price feed at specific date/time | CMC, CoinGecko, exchange APIs | Flash crashes, exchange differences, "settlement" vs "spot" price |
| Politics | Official result/announcement | Government/election authority | Delayed results, contested outcomes, recounts, legal challenges |
| Sports | Final score/result | Official league/federation data | Overtime/extra time, disqualifications, protests, walkovers |
| Commodities | Official settlement price | CME/ICE settlement data | Contract month confusion (front month vs specific month), settlement vs intraday |
| Entertainment | Award ceremony/official announcement | Official ceremony results | Ties (rare), rule changes, ceremony cancellations |
| Finance/Macro | Official data release | BLS, Fed, Treasury, BEA | Revisions to initial data, seasonal adjustments, methodology changes |

**Key principle:** Always verify resolution against the EXACT criteria stated in the
market description. Markets resolve on specific, precise conditions — not on
general impressions.

---

## Aggregation and Tracking

After processing individual outcomes, calculate aggregate metrics:

1. **Running totals:**
   - Total positions resolved (all time)
   - Overall win rate (directional accuracy)
   - Total realized P&L
   - Average Brier score

2. **Calibration buckets:**
   Group all resolved positions by estimated_prob range:
   ```
   0.00-0.20: count, avg_estimated, avg_actual, avg_brier
   0.20-0.40: count, avg_estimated, avg_actual, avg_brier
   0.40-0.60: count, avg_estimated, avg_actual, avg_brier
   0.60-0.80: count, avg_estimated, avg_actual, avg_brier
   0.80-1.00: count, avg_estimated, avg_actual, avg_brier
   ```
   
   **Good calibration means:** the average actual_outcome in each bucket is close to
   the average estimated_prob. If we say 70% on average and win 70% of the time
   in that bucket, we're well-calibrated.

3. **Update calibration tracker:**
   - Record outcomes via `python tools/record_outcome.py` to update `knowledge/calibration.json`
   - Flag categories with deteriorating performance (Brier > 0.30 or |error_pp| > 20)

---

## Examples

### Example 1: Winning Trade Resolution — Arsenal EPL

**Hypothetical outcome based on the March 2026 entry:**

**Trade record:**
- Market: "Will Arsenal win the 2025-26 English Premier League?"
- Side: YES
- Entry price: $0.895 per share
- Entry date: 2026-03-15
- Estimated prob: 0.95
- Edge: 0.055
- Confidence: 0.85
- Size: $300 (335 shares)

**Resolution (hypothetical):**
- Resolution date: 2026-05-27
- Outcome: YES (Arsenal won the league)
- Our side won: TRUE

**Calculations:**
```
Payout: 335 shares * $1.00 = $335.00
Cost basis: $300.00
Realized P&L: $335.00 - $300.00 = +$35.00

Brier score: (0.95 - 1.0)^2 = 0.0025  (excellent)
Error: |0.95 - 1.0| = 5 percentage points
Direction: CORRECT
```

**Categorization:**
- Category: Sports
- Edge quality: **Real edge** — correct direction, profitable
- Calibration: Slightly underconfident (0.95 vs actual 1.0 — we gave 5% chance to failure)
- Timing: 73-day hold — within expected timeframe (season end)

**Lessons:**
1. Got right: The 9-point lead thesis was correct. Historical base rates were reliable.
2. Got right: Sizing at 3% was appropriate — confident but not overexposed.
3. Could improve: Could have entered larger since confidence was high (but 5% cap is there for a reason).
4. Golden rule candidate: "Sports markets with strong statistical base rates are high-confidence bets."

---

### Example 2: Losing Trade Resolution — Crude Oil

**Hypothetical losing scenario:**

**Trade record:**
- Market: "Will crude oil (CL) hit $100 by end of March?"
- Side: YES
- Entry price: $0.888
- Entry date: 2026-03-15
- Estimated prob: 0.92
- Edge: 0.032
- Confidence: 0.70
- Size: $300 (337.84 shares)

**Resolution (hypothetical loss):**
- Resolution date: 2026-03-31
- Outcome: NO (WTI never settled at $100+; surprise ceasefire announcement March 25 crashed oil)
- Our side won: FALSE

**Calculations:**
```
Payout: 337.84 shares * $0.00 = $0.00
Cost basis: $300.00
Realized P&L: $0.00 - $300.00 = -$300.00

Brier score: (0.92 - 0.0)^2 = 0.8464  (very poor)
Error: |0.92 - 0.0| = 92 percentage points
Direction: INCORRECT
```

**Categorization:**
- Category: Commodities
- Edge quality: **Anti-edge** — wrong direction, full loss
- Calibration: Severely overconfident (0.92 vs actual 0.0)
- Timing: 16-day hold (full duration to resolution)

**Lessons:**
1. Got wrong: Underestimated geopolitical de-escalation risk
2. Got wrong: Treated a small numerical gap ($1.29) as high probability without adequate
   weighting of tail-risk scenarios
3. Would do differently: Lower confidence on commodity markets with active geopolitical
   drivers (ceasefire/escalation is binary and unpredictable)
4. **Golden rule candidate:** "Commodity markets driven by active conflicts have high tail
   risk. Never assign >80% probability when outcomes depend on geopolitical negotiation."

**Impact on strategy:**
- Commodities category: 1 loss, 0 wins → watch list
- If 2 more consecutive commodity losses: raise minimum edge to 8pp for commodities
- Consider lowering max confidence for geopolitical-driven markets to 0.70

---

### Example 3: Early Sell — Thesis Changed

**Hypothetical partial exit:**

**Trade record:**
- Market: "Will Bitcoin hit $100,000 by June 2026?"
- Side: YES
- Entry price: $0.45
- Entry date: 2026-03-20
- Estimated prob: 0.55
- Edge: 0.10
- Confidence: 0.50
- Size: $200 (444 shares)

**Early exit (not resolution):**
- Sell date: 2026-04-15
- Sell price: $0.60 (thesis strengthened, market repriced higher)
- Reason: Took profit as market moved toward our estimate

**Calculations:**
```
Sell proceeds: 444 shares * $0.60 = $266.40
Cost basis: $200.00
Realized P&L: $266.40 - $200.00 = +$66.40

Brier score: (0.55 - 0.60)^2 = 0.0025  (excellent — exit price close to estimate)
Error: |0.55 - 0.60| = 5 percentage points
Direction: CORRECT (price moved toward our estimate)
```

**Categorization:**
- Category: Crypto
- Edge quality: **Real edge** — correctly identified underpricing
- Calibration: Well-calibrated (sold near our estimated fair value)
- Timing: 26-day hold — exited before resolution

**Lessons:**
1. Got right: Identified genuine mispricing in a mid-range market
2. Got right: Took profit when the market moved to fair value
3. Question: Should we have held for the full resolution? The remaining 40% uncertainty
   means continuing to hold exposes us to the "hold through resolution" risk
4. **Observation:** Selling at fair value locks in profits. Holding for resolution is
   only better if we believe our estimate is STILL below fair value at the exit point.

---

## Updating This Skill

After each batch of resolutions:

1. **Add real examples** — replace hypothetical scenarios with actual outcomes
2. **Update calibration data** — are we consistently over/underconfident in certain ranges?
3. **Refine category guidance** — which categories are we best/worst at?
4. **Create golden rules** — patterns of 3+ similar mistakes become rules
5. **Adjust the performance tracker format** if current metrics don't capture the right signals

Record changes with a date stamp and brief rationale.
