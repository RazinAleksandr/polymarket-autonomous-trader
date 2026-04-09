# Calibration Check

<!-- CLAUDE-EDITABLE: Claude may add examples, refine criteria, annotate decisions -->

## When to Load

Load this skill during **Phase E (Learn and Evolve)** when updating calibration data after
resolutions, and during **Phase C (Analyze Markets)** to check for known calibration biases
before estimating probabilities.

**Also reference:** `knowledge/calibration.json` for historical accuracy data,
`.claude/skills/resolution-parser.md` for outcome data,
`.claude/skills/evaluate-edge.md` for where calibration corrections are applied,
`state/strategy.md` for current strategy parameters.

---

## Framework

### Step 1: Load Current Calibration Data

Read `knowledge/calibration.json` for the historical accuracy dataset. If the file does not
exist yet (first cycles), initialize it with the empty structure below.

**Calibration data structure:**
```json
{
  "last_updated": "2026-04-01T00:00:00Z",
  "overall": {
    "total_predictions": 0,
    "correct_direction": 0,
    "avg_brier_score": 0.0,
    "avg_error_pp": 0.0,
    "win_rate": 0.0
  },
  "by_category": {
    "crypto": {
      "total": 0,
      "correct": 0,
      "avg_brier": 0.0,
      "avg_error_pp": 0.0,
      "win_rate": 0.0,
      "total_pnl": 0.0
    }
  },
  "by_confidence_bucket": {
    "0.30-0.40": {
      "count": 0,
      "avg_estimated": 0.0,
      "avg_actual": 0.0,
      "avg_brier": 0.0,
      "win_rate": 0.0
    },
    "0.40-0.50": { "count": 0, "avg_estimated": 0.0, "avg_actual": 0.0, "avg_brier": 0.0, "win_rate": 0.0 },
    "0.50-0.60": { "count": 0, "avg_estimated": 0.0, "avg_actual": 0.0, "avg_brier": 0.0, "win_rate": 0.0 },
    "0.60-0.70": { "count": 0, "avg_estimated": 0.0, "avg_actual": 0.0, "avg_brier": 0.0, "win_rate": 0.0 },
    "0.70-0.80": { "count": 0, "avg_estimated": 0.0, "avg_actual": 0.0, "avg_brier": 0.0, "win_rate": 0.0 },
    "0.80-0.90": { "count": 0, "avg_estimated": 0.0, "avg_actual": 0.0, "avg_brier": 0.0, "win_rate": 0.0 },
    "0.90-1.00": { "count": 0, "avg_estimated": 0.0, "avg_actual": 0.0, "avg_brier": 0.0, "win_rate": 0.0 }
  },
  "by_estimated_prob_bucket": {
    "0.00-0.20": { "count": 0, "avg_estimated": 0.0, "avg_actual": 0.0 },
    "0.20-0.40": { "count": 0, "avg_estimated": 0.0, "avg_actual": 0.0 },
    "0.40-0.60": { "count": 0, "avg_estimated": 0.0, "avg_actual": 0.0 },
    "0.60-0.80": { "count": 0, "avg_estimated": 0.0, "avg_actual": 0.0 },
    "0.80-1.00": { "count": 0, "avg_estimated": 0.0, "avg_actual": 0.0 }
  },
  "corrections": {},
  "history": []
}
```

**If the file exists**, read and parse it. If it is malformed, back it up and reinitialize.

---

### Step 2: Record New Outcomes (Post-Resolution)

For each newly resolved position (data from resolution-parser), append to calibration data:

1. **Add to history array:**
   ```json
   {
     "market_id": "abc123",
     "category": "sports",
     "estimated_prob": 0.95,
     "actual_outcome": 1.0,
     "brier_score": 0.0025,
     "confidence_at_entry": 0.85,
     "edge_at_entry": 0.055,
     "realized_pnl": 35.00,
     "date": "2026-05-27"
   }
   ```

2. **Update running averages:**

   **Overall:**
   ```
   total_predictions += 1
   correct_direction += 1 if direction was correct
   avg_brier_score = sum(all brier_scores) / total_predictions
   avg_error_pp = sum(all |estimated - actual|) / total_predictions * 100
   win_rate = correct_direction / total_predictions
   ```

   **By category** (e.g., sports, crypto, politics):
   ```
   category.total += 1
   category.correct += 1 if direction correct
   category.avg_brier = sum(category brier_scores) / category.total
   category.avg_error_pp = sum(category errors) / category.total * 100
   category.win_rate = category.correct / category.total
   category.total_pnl += realized_pnl
   ```

   **By confidence bucket** (group by confidence_at_entry range):
   ```
   bucket.count += 1
   bucket.avg_estimated = running average of estimated_prob values in this bucket
   bucket.avg_actual = running average of actual_outcome values in this bucket
   bucket.avg_brier = running average of brier_scores in this bucket
   bucket.win_rate = correct_in_bucket / bucket.count
   ```

   **By estimated probability bucket** (group by estimated_prob range):
   ```
   prob_bucket.count += 1
   prob_bucket.avg_estimated = running average of estimated_prob values
   prob_bucket.avg_actual = running average of actual_outcome values
   ```

3. **Write updated calibration.json** with new `last_updated` timestamp.

---

### Step 3: Analyze Calibration Quality

After updating, assess the quality of our probability estimates:

**Perfect calibration** means: when we say 70%, it happens 70% of the time.
Plot (mentally or in a table) avg_estimated vs avg_actual for each probability bucket.

**Overconfidence detection:**
- In a probability bucket, if `avg_estimated > avg_actual` consistently
- Example: We say 80% on average, but outcomes are 60% -- we're overconfident by 20pp
- Signal: Brier scores trending up in this bucket

**Underconfidence detection:**
- In a probability bucket, if `avg_estimated < avg_actual` consistently
- Example: We say 60% on average, but outcomes are 80% -- we're underconfident by 20pp
- Signal: We're leaving money on the table by undersizing positions

**Category bias detection:**
- Compare Brier scores across categories
- Some categories may be systematically miscalibrated while others are well-calibrated
- Example: Crypto Brier = 0.35 (poor) vs Sports Brier = 0.08 (excellent)

**Calculate calibration metrics:**
```
For each bucket with 5+ data points:
  mean_error_pp = mean(|estimated_prob - actual_outcome|) * 100
  calibration_gap = avg_estimated - avg_actual  (positive = overconfident)
  
For each category with 5+ data points:
  category_bias = avg_estimated_in_category - category_win_rate
```

**Calibration summary table:**

| Bucket | N | Avg Est. | Avg Actual | Gap (pp) | Assessment |
|--------|---|----------|-----------|----------|------------|
| 0.30-0.40 | ? | ? | ? | ? | ? |
| 0.40-0.50 | ? | ? | ? | ? | ? |
| ... | | | | | |

---

### Step 4: Generate Calibration Corrections

If a clear pattern exists (requires **5+ data points** in a bucket or category):

**Category corrections:**
- Overconfident in crypto by 15pp: correction = -0.15
  "When analyzing crypto markets, subtract 0.15 from initial estimate"
- Underconfident in politics by 8pp: correction = +0.08
  "When analyzing politics markets, add 0.08 to initial estimate"

**Confidence bucket corrections:**
- When we say 0.80-0.90, actual rate is 0.65: correction = -0.15
  "When confidence is 0.80-0.90, apply -0.15 correction to estimated probability"

**Write corrections to calibration.json:**
```json
{
  "corrections": {
    "crypto": {
      "direction": "subtract",
      "amount": 0.15,
      "reason": "Overconfident by 15pp over 8 trades (avg est 0.59, actual win rate 0.40)",
      "data_points": 8,
      "added_date": "2026-04-15",
      "expires_after_n_trades": 10
    },
    "politics": {
      "direction": "add",
      "amount": 0.08,
      "reason": "Underconfident by 8pp over 6 trades",
      "data_points": 6,
      "added_date": "2026-04-15",
      "expires_after_n_trades": 10
    }
  }
}
```

**Correction expiration:** Each correction has an `expires_after_n_trades` field.
After that many additional trades in the category, recalculate the correction.
If the bias has disappeared, remove the correction. If it persists, renew it.

---

### Step 5: Pre-Analysis Calibration Adjustment (Phase C Use)

When loading this skill during **Phase C (Analyze Markets)**, before analyzing a new market:

1. **Check if the market's category has an active calibration correction:**
   - Read `knowledge/calibration.json`, check `corrections` field
   - Look up the current market's category

2. **If a correction exists:**
   - After completing the Bull/Bear synthesis in evaluate-edge, apply the correction:
   ```
   raw_estimate = 0.75  (from evaluate-edge synthesis)
   correction = -0.10  (crypto is overconfident by 10pp)
   adjusted_estimate = 0.75 - 0.10 = 0.65
   ```
   - Use the adjusted_estimate for edge calculation and sizing
   - Log: "Applied calibration correction: crypto -10pp (0.75 -> 0.65)"

3. **If no correction exists:** Use the raw estimate unchanged.

4. **Confidence bucket check:**
   - If you're about to assign confidence in a bucket that's historically overconfident,
     note this in the analysis
   - Example: "Note: trades in the 0.80-0.90 confidence bucket have historically
     underperformed. Consider whether confidence is truly this high."

---

## Calibration Health Thresholds

| Metric | Healthy | Warning | Unhealthy |
|--------|---------|---------|-----------|
| Overall Brier score | < 0.20 | 0.20-0.30 | > 0.30 |
| Category Brier score | < 0.20 | 0.20-0.30 | > 0.30 |
| Category error (pp) | < 15pp | 15-25pp | > 25pp |
| Calibration gap (pp) | < 10pp | 10-20pp | > 20pp |
| N predictions (overall) | > 20 | 10-20 | < 10 (too few to judge) |
| N predictions (category) | > 10 | 5-10 | < 5 (too few to judge) |
| Win rate | > 55% | 45-55% | < 45% |

**Action triggers:**
- Any category reaches "Unhealthy": increase min_edge_threshold to 0.08 for that category
- Overall Brier > 0.30: pause trading and perform full calibration review
- Win rate < 45% over 10+ trades: halt automated trading, request human review
- 5 consecutive losses in any category: halt that category until manual review

---

## Examples

### Example 1: Recording a New Outcome

**Incoming data from resolution-parser:**
- Market: "Will Arsenal win the 2025-26 EPL?"
- Category: sports
- Estimated probability: 0.95
- Actual outcome: 1.0 (YES won)
- Brier score: 0.0025
- Confidence at entry: 0.85
- P&L: +$35.00

**Before update:**
```json
{
  "overall": { "total_predictions": 4, "correct_direction": 3, "avg_brier_score": 0.12 },
  "by_category": { "sports": { "total": 1, "correct": 1, "avg_brier": 0.01 } }
}
```

**After update:**
```json
{
  "overall": { "total_predictions": 5, "correct_direction": 4, "avg_brier_score": 0.0965 },
  "by_category": { "sports": { "total": 2, "correct": 2, "avg_brier": 0.006 } }
}
```

**Log:** "Calibration updated: overall Brier 0.12 -> 0.097 (improving). Sports category:
2/2 correct, Brier 0.006 (excellent)."

---

### Example 2: Detecting Overconfidence Pattern

**After processing 8 crypto trades, the calibration data shows:**

| Bucket | N | Avg Estimated | Avg Actual | Gap |
|--------|---|--------------|-----------|-----|
| 0.40-0.50 | 2 | 0.45 | 0.50 | -5pp (underconfident) |
| 0.50-0.60 | 3 | 0.56 | 0.33 | +23pp (overconfident) |
| 0.70-0.80 | 2 | 0.75 | 0.50 | +25pp (overconfident) |
| 0.80-0.90 | 1 | 0.85 | 1.00 | -15pp (underconfident) |

**Category summary:**
- Crypto: 8 trades, avg estimated 0.60, avg actual 0.375, avg Brier 0.28
- Gap: +22.5pp overconfident

**Analysis:**
- Clear overconfidence in the 0.50-0.80 range for crypto
- When we say "60% likely" for crypto, it actually happens only 33% of the time
- The 0.80-0.90 bucket has only 1 data point -- insufficient to draw conclusions

**Correction generated:**
```json
{
  "corrections": {
    "crypto": {
      "direction": "subtract",
      "amount": 0.15,
      "reason": "Overconfident by 22.5pp over 8 trades. Conservative correction of 15pp applied (not full 22.5pp due to small sample).",
      "data_points": 8,
      "added_date": "2026-04-15",
      "expires_after_n_trades": 10
    }
  }
}
```

**Log:** "CALIBRATION WARNING: Crypto category overconfident by 22.5pp (Brier 0.28 = Warning).
Applied -15pp correction. Raising min_edge to 0.08 for crypto."

---

### Example 3: Applying Pre-Analysis Correction

**Scenario:** Analyzing a new crypto market during Phase C.

**Market:** "Will Bitcoin reach $120,000 by June 2026?"
- Current YES price: $0.35

**Raw analysis from evaluate-edge:**
- Bull case probability: 0.55
- Bear case probability: 0.30
- Synthesized raw estimate: 0.45
- Confidence: 0.55

**Calibration check:**
1. Read `knowledge/calibration.json` -- crypto correction exists: subtract 0.15
2. Apply: `adjusted_estimate = 0.45 - 0.15 = 0.30`
3. Recalculate edge: `edge = 0.30 - 0.35 = -0.05`

**Result:** After calibration correction, the edge is NEGATIVE. The market price of $0.35
actually overestimates the probability given our historical overconfidence in crypto.

**Decision:** PASS -- calibration correction reveals no real edge.

**Without the correction:** We would have estimated 0.45 vs market 0.35 = +10pp edge,
potentially entering a losing trade. The calibration system prevented this.

**Log:** "Applied calibration correction: crypto -15pp (0.45 -> 0.30). Edge now -0.05.
PASS -- no edge after correction."

---

## Calibration Review Cadence

**After every cycle with resolutions:** Run Steps 1-4 (update data, analyze quality)

**Every 5 cycles:** Full calibration review:
- Review all buckets and categories
- Recalculate corrections
- Expire stale corrections (past expires_after_n_trades)
- Report calibration health to cycle report

**Every 20 trades:** Comprehensive assessment:
- Is overall Brier trending up or down?
- Which categories are improving, which are deteriorating?
- Are corrections working? (compare pre/post-correction performance)

---

## Updating This Skill

After each calibration update:

1. **Add real examples** from actual calibration data (replace hypothetical examples)
2. **Refine correction methodology** if corrections are consistently over/under-adjusting
3. **Adjust health thresholds** based on trading experience (e.g., if Brier < 0.15 is
   achievable, tighten the "Healthy" threshold)
4. **Update bucket boundaries** if the current buckets don't capture meaningful differences

Record changes with a date stamp and brief rationale.
