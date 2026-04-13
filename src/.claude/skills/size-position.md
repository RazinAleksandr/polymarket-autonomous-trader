# Size Position

<!-- CLAUDE-EDITABLE: Claude may add examples, refine criteria, annotate decisions -->

## When to Load

Load this skill during **Phase D (Size and Execute)** of the trading cycle, after evaluate-edge
has produced one or more trade candidates with estimated probability, confidence, and edge values.

**Also reference:** `tools/calculate_kelly.py` for Kelly math verification,
`tools/calculate_edge.py` for edge verification, `tools/get_portfolio.py --include-risk`
for current exposure, `lib/strategy.py` for the underlying Kelly implementation.

---

## Framework

### Step 1: Validate Trade Candidate

Before sizing, confirm the trade candidate passes all gates:

1. **Edge check:** `|edge| >= 0.04` (MIN_EDGE_THRESHOLD from config)
   - If edge is below threshold, this candidate should not have reached sizing
   - Double-check: `edge = estimated_probability - market_price` (for YES side)
   - Or: `edge = (1 - estimated_probability) - (1 - market_price)` (for NO side)

2. **Confidence check:** `confidence >= 0.3`
   - Below 0.3 = too uncertain to size a position

3. **Position monitor check:** If the position monitor flagged this market as WATCH
   (weakening thesis), do not enter a new position
   - Exception: opposing side trades when thesis has reversed (document reasoning)

4. **Verify with CLI tools (optional but recommended):**
   ```bash
   python tools/calculate_edge.py --estimated-prob 0.95 --market-price 0.895 --pretty
   ```
   Confirms the edge calculation is correct before sizing.

---

### Step 2: Kelly Criterion Calculation

The Kelly criterion determines the mathematically optimal bet size for a binary outcome.

**Core formula:**
```
Full Kelly: f* = (p * b - q) / b

Where:
  p = estimated_probability (our probability estimate)
  q = 1 - p (probability of being wrong)
  b = (1 - market_price) / market_price (net odds for YES side)
  b = market_price / (1 - market_price) (net odds for NO side)
```

**Conservative adjustment:**
```
Quarter Kelly: f_adj = f* * KELLY_FRACTION

Where:
  KELLY_FRACTION = 0.25 (default — quarter Kelly for conservative sizing)
```

Quarter Kelly is used because:
- Full Kelly assumes perfect probability estimates (we don't have those)
- Full Kelly leads to extreme variance and potential ruin
- Quarter Kelly captures ~50% of the growth rate with ~25% of the variance
- Industry standard for quantitative trading with imperfect models

**Calculate using the CLI tool:**
```bash
python tools/calculate_kelly.py \
  --estimated-prob 0.95 \
  --market-price 0.895 \
  --bankroll 10000 \
  --kelly-fraction 0.25 \
  --max-position 500 \
  --pretty
```

The tool returns: `kelly_raw`, `kelly_adjusted`, `position_size_usdc`, `num_shares`.

**Underlying implementation** is in `lib/strategy.py:kelly_criterion()`:
```python
b = (1 - odds_price) / odds_price  # net odds
q = 1 - prob
kelly = (b * prob - q) / b
kelly = max(0.0, kelly)  # no negative bets
return kelly * fraction
```

---

### Step 3: Confidence Weighting

Apply a confidence multiplier to the Kelly-adjusted size:

```
confidence_adjusted_fraction = kelly_adjusted * confidence
```

This naturally scales position size with analysis quality:

| Confidence | Effect on Position Size | Interpretation |
|------------|------------------------|----------------|
| 0.3-0.4 | Very small (30-40% of Kelly) | Exploratory bet — minimal conviction |
| 0.5-0.6 | Moderate (50-60% of Kelly) | Reasonable thesis with some uncertainty |
| 0.7-0.8 | Standard (70-80% of Kelly) | Strong evidence, clear base rates |
| 0.8-0.9 | Full Kelly-adjusted (80-90%) | High conviction with concordant evidence |
| 0.9-1.0 | Near-maximum Kelly | Exceptional clarity (rare — be honest) |

**Why this matters:** A market with 10% edge but 0.3 confidence should get a much
smaller position than a market with 5% edge but 0.9 confidence. The confidence
weighting ensures we bet bigger when we know more.

---

### Step 4: Apply Position Limits

Hard limits that cannot be exceeded regardless of Kelly math:

1. **Maximum single position:** 5% of bankroll
   - Source: `state/core-principles.md` — immutable safety rule
   - Example: $10,000 bankroll → max $500 per position
   - This overrides Kelly if Kelly says bigger

2. **Maximum total exposure:** 30% of bankroll across all open positions
   - Check current exposure: `python tools/get_portfolio.py --include-risk --pretty`
   - Parse: `total_exposure` and `remaining_capacity` from output
   - If `remaining_capacity < proposed_size` → reduce to remaining_capacity

3. **Minimum trade size:** $5 USDC
   - CLOB minimum notional order size (SAFE-05 in the codebase)
   - If the confidence-adjusted Kelly produces less than $5 → DO NOT TRADE
   - This is a natural filter for marginal opportunities

4. **Apply the most restrictive limit:**
   ```
   final_size = min(
       confidence_adjusted_kelly * bankroll,
       bankroll * 0.05,          # 5% max single position
       remaining_capacity,        # exposure limit headroom
       max_position_usdc          # config cap
   )
   
   if final_size < 5.0:
       DO NOT TRADE  # below CLOB minimum
   ```

---

### Step 5: Calculate Order Parameters

Convert the dollar size into order parameters:

1. **Size in USDC:**
   ```
   size_usdc = final_size (from Step 4, already capped)
   ```

2. **Number of shares:**
   ```
   shares = size_usdc / market_price  (for YES side)
   shares = size_usdc / (1 - market_price)  (for NO side)
   ```
   Round to 2 decimal places (SAFE-05 requirement).

3. **Verify bounds:**
   - `size_usdc >= 5.0` (minimum) — already checked in Step 4
   - `size_usdc <= bankroll * 0.05` (maximum) — already checked in Step 4
   - `shares > 0` (sanity check)

---

### Step 6: Risk Assessment

Before executing, calculate the risk profile of this trade:

1. **Maximum loss:** `size_usdc` (total loss if our side loses)
   - This is the cost basis — the most we can lose

2. **Potential profit:** `(shares * 1.0) - size_usdc` (profit if our side wins)
   - Each winning share pays $1.00

3. **Expected value:**
   ```
   EV = estimated_probability * potential_profit - (1 - estimated_probability) * size_usdc
   ```
   - If EV < 0: **DO NOT TRADE** — the math says this loses money in expectation
   - This should never happen if edge is positive, but serves as a sanity check

4. **Risk-reward ratio:** `potential_profit / size_usdc`
   - At high prices (0.90), risk-reward is poor: $11 profit vs $100 risk (0.11:1)
   - At mid prices (0.50), risk-reward is even: $100 profit vs $100 risk (1:1)
   - Factor this into whether the position size feels right

---

## Formulas Reference

| Formula | Expression | Notes |
|---------|-----------|-------|
| Edge (YES) | `estimated_prob - yes_price` | Positive = underpriced |
| Edge (NO) | `(1 - estimated_prob) - no_price` | Positive = overpriced |
| Net odds (YES) | `(1 - yes_price) / yes_price` | Payout ratio on win |
| Net odds (NO) | `yes_price / (1 - yes_price)` | Payout ratio on win |
| Full Kelly | `(p * b - q) / b` | Optimal fraction |
| Quarter Kelly | `full_kelly * 0.25` | Conservative adjustment |
| Confidence-adjusted | `quarter_kelly * confidence` | Analysis-quality scaling |
| Position cap | `min(kelly_size, bankroll * 0.05, remaining_capacity)` | Most restrictive wins |
| Shares | `size_usdc / price` | Round to 2 decimal places |
| Expected value | `p * profit - q * cost` | Must be positive |

---

## Examples

### Example 1: Standard Trade (Arsenal EPL, March 2026)

**Source:** polymarket_claude/output/trades/2026-03-15_arsenal-epl.md

**Inputs from evaluate-edge:**
- estimated_probability: 0.95
- market_price (YES): 0.895
- edge: 0.055 (5.5 percentage points)
- confidence: 0.85
- recommended_side: YES

**Step 2 — Kelly Calculation:**
```
b = (1 - 0.895) / 0.895 = 0.1173  (net odds)
p = 0.95, q = 0.05
Full Kelly: f* = (0.95 * 0.1173 - 0.05) / 0.1173 = (0.1114 - 0.05) / 0.1173 = 0.524
Quarter Kelly: f_adj = 0.524 * 0.25 = 0.131
```

**Step 3 — Confidence Weighting:**
```
confidence_adjusted = 0.131 * 0.85 = 0.111
```

**Step 4 — Position Limits:**
```
Bankroll: $10,000
Kelly size: 0.111 * $10,000 = $1,110
5% cap: $500
Remaining capacity: $8,000 (assuming low existing exposure)
Final size: min($1,110, $500, $8,000) = $500 (capped by 5% rule)
```

Wait — the original trader used $300 (3% of bankroll). Why?

The trader chose conservative sizing because:
- The market resolves in May 2026 (2+ months away) — more time = more uncertainty
- Edge per dollar is small at high prices ($0.895 → only 11.7 cents potential profit per dollar)
- A 3% allocation felt more appropriate than the 5% maximum

**Actual position: $300 (3% of $10,000)**
- Shares: 300 / 0.895 = 335 shares
- Max loss: $300
- Potential profit: $335 - $300 = $35
- EV: 0.95 * $35 - 0.05 * $300 = $33.25 - $15 = **+$18.25**
- Risk-reward: $35 / $300 = 0.117:1 (poor ratio, but high probability compensates)

**Lesson:** At high prices (>0.85), Kelly can suggest large positions because the edge
as a percentage of price is meaningful. But the risk-reward ratio is poor, so sizing
below the Kelly recommendation is prudent. Trust the math but apply judgment.

---

### Example 2: Small Position — Low Confidence (Commodities)

**Hypothetical based on crude oil patterns:**

**Inputs:**
- estimated_probability: 0.92
- market_price (YES): 0.888
- edge: 0.032 (borderline — just below threshold at strict 0.04)
- confidence: 0.50 (geopolitical events are inherently unpredictable)
- recommended_side: YES

**Step 2 — Kelly Calculation:**
```
b = (1 - 0.888) / 0.888 = 0.1261
p = 0.92, q = 0.08
Full Kelly: f* = (0.92 * 0.1261 - 0.08) / 0.1261 = (0.116 - 0.08) / 0.1261 = 0.285
Quarter Kelly: f_adj = 0.285 * 0.25 = 0.071
```

**Step 3 — Confidence Weighting:**
```
confidence_adjusted = 0.071 * 0.50 = 0.036
```

**Step 4 — Position Limits:**
```
Bankroll: $10,000
Kelly size: 0.036 * $10,000 = $360
5% cap: $500
Final size: $360 (within all limits)
```

**Result:** $360 position — much smaller than Example 1 because confidence is lower.
- Shares: 360 / 0.888 = 405 shares
- Max loss: $360
- Potential profit: $405 - $360 = $45
- EV: 0.92 * $45 - 0.08 * $360 = $41.40 - $28.80 = **+$12.60**

**Note:** The original trader sized this at $300 (3%) which is close to what the
framework produces. The confidence weighting naturally pushed the size down despite
the decent Kelly fraction, reflecting the uncertainty in commodity markets.

---

### Example 3: Position Capped by Exposure Limit

**Scenario:** Late in a cycle, several positions are open and we're near the exposure limit.

**Inputs:**
- estimated_probability: 0.70
- market_price (YES): 0.55
- edge: 0.15 (large edge!)
- confidence: 0.75
- recommended_side: YES

**Current portfolio state:**
```
Total bankroll: $10,000
Open positions: 5
Total exposure: $2,700 (27% of bankroll)
Remaining capacity: $300 (30% limit - 27% current = 3%)
```

**Step 2 — Kelly Calculation:**
```
b = (1 - 0.55) / 0.55 = 0.818
p = 0.70, q = 0.30
Full Kelly: f* = (0.70 * 0.818 - 0.30) / 0.818 = (0.573 - 0.30) / 0.818 = 0.334
Quarter Kelly: f_adj = 0.334 * 0.25 = 0.0835
```

**Step 3 — Confidence Weighting:**
```
confidence_adjusted = 0.0835 * 0.75 = 0.063
```

**Step 4 — Position Limits:**
```
Kelly size: 0.063 * $10,000 = $630
5% cap: $500
Remaining capacity: $300  ← BINDING CONSTRAINT
Final size: min($630, $500, $300) = $300
```

**Result:** Position capped at $300 by exposure limit, not Kelly.
- Shares: 300 / 0.55 = 545 shares
- Max loss: $300
- Potential profit: $545 - $300 = $245
- EV: 0.70 * $245 - 0.30 * $300 = $171.50 - $90 = **+$81.50**
- Risk-reward: $245 / $300 = 0.82:1 (much better than high-price trades)

**Lesson:** The 30% total exposure limit protects the bankroll from overconcentration.
Even with a strong edge (15 percentage points) and good confidence (0.75), the portfolio
constraint caps the position. This is by design — portfolio-level risk management is
more important than maximizing any single trade.

---

## Correlation Check

Before finalizing, check for correlated positions:

1. **Same category?** Markets in the same category may move together
2. **Same underlying event?** Different questions about the same event are correlated
3. **Outcome dependency?** If one resolving YES makes another more likely, they're linked

**If correlated with an existing position:**
- Apply a 0.5 correlation factor: reduce the new position size by 50%
- Document the correlation in the trade reasoning
- Example: If holding "Will Arsenal win EPL?" — don't also take a large position on
  "Will Man City NOT win EPL?" (nearly identical bets)

---

## Updating This Skill

After each trading cycle with resolved positions:

1. **Update examples** with real outcomes (mark wins/losses)
2. **Calibrate Kelly fraction** — if consistently overexposed, reduce from 0.25
3. **Adjust confidence ranges** based on Brier score calibration data
4. **Track position-cap frequency** — if hitting limits often, consider reducing per-trade max

Record changes with a date stamp and brief rationale.
