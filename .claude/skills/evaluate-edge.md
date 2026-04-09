# Evaluate Edge

<!-- CLAUDE-EDITABLE: Claude may add examples, refine criteria, annotate decisions -->

## When to Load

Load this skill during **Phase C (Analyze Markets)** of the trading cycle, after market discovery
has produced candidate markets. Use this framework to evaluate each candidate for tradeable edge
before passing trade candidates to size-position.

**Also reference:** `tools/discover_markets.py` for fetching market data, `tools/get_prices.py`
for fresh orderbook prices, `tools/get_portfolio.py` for existing positions.

---

## Framework

### Step 1: Market Triage (2 minutes per market)

For each candidate market from discovery, perform rapid filtering:

1. **Price sweet spot check:** Is the YES price between 0.15 and 0.85?
   - Markets at extremes (>0.85 or <0.15) have compressed payout ranges where edge is tiny
   - Even a correct assessment at 99% vs market 97% yields only 2 cents edge per dollar
   - Exception: If you have very high conviction AND the position sizing makes sense at
     the compressed odds, you may proceed (rare — document reasoning)

2. **Volume check:** Does the market have at least $10,000 in 24-hour volume?
   - Low-volume markets have wide spreads, making entry/exit expensive
   - Check with: `python tools/discover_markets.py --limit 20 --pretty`
   - The `volume_24h` field in the output gives this number

3. **Resolution timeline check:** Does the market resolve within a reasonable horizon?
   - Shorter resolution = more predictable = higher confidence possible
   - Very long-dated markets (6+ months) have high uncertainty discounts
   - Check the `end_date` field from market discovery output

4. **Existing position check:** Do we already hold a position in this market?
   - Run: `python tools/get_portfolio.py --pretty`
   - If we hold a position, PASS — avoid doubling down
   - Exception: If the position monitor has flagged for exit, a new opposing position
     may be warranted (rare)

5. **Decision gate:**
   - ANY filter fails → **PASS** (record reason, move to next market)
   - ALL filters pass → **CONTINUE** to Step 2

---

### Step 2: Bull Case Research (web search required)

Build the strongest possible case FOR the YES outcome:

1. **Search for supporting evidence** using web search:
   - Query 1: `[event name] [year]` (e.g., "Arsenal Premier League 2026")
   - Query 2: `[key entities] + [expected outcome]` (e.g., "Arsenal 9 point lead EPL")
   - Query 3: `[topic] latest news [month year]` (e.g., "crude oil price March 2026")

2. **Record 3-5 specific evidence points**, each with:
   - The factual claim (be specific: numbers, dates, names)
   - The source (URL or publication name)
   - The date of the information (recency matters)

3. **Estimate the bull-only probability:**
   - Ask: "If ONLY this evidence existed, what would the probability be?"
   - This is intentionally biased high — it represents the strongest bull case
   - Record this number (e.g., 0.97)

4. **Weight recent information more heavily:**
   - Information from the last 7 days gets 2x weight vs older data
   - Breaking news from the last 24 hours gets 3x weight
   - Base rates and historical data provide the foundation but can be overridden
     by very recent developments

---

### Step 3: Bear Case Research (web search required)

Build the strongest possible case AGAINST the YES outcome:

1. **Search for counter-evidence** using web search:
   - Query 1: `[event] risks obstacles unlikely` (e.g., "Arsenal title collapse risks")
   - Query 2: `[topic] historical base rate` (e.g., "how often does 9 point lead win EPL")
   - Query 3: `[topic] bear case against` (e.g., "why oil might drop below $100")

2. **Record 3-5 specific counter-evidence points**, each with source and date.

3. **Explicitly look for base rates:**
   - "How often does [event type] actually happen?"
   - "What is the historical frequency of [outcome]?"
   - Base rates anchor the analysis and prevent overconfidence
   - Example: "Teams with 9+ point leads with 9 games left win 97-99% of the time"

4. **Estimate the bear-only probability:**
   - Ask: "If ONLY this counter-evidence existed, what would the probability be?"
   - This is intentionally biased low — it represents the strongest bear case
   - Record this number (e.g., 0.80)

---

### Step 4: Synthesis

Combine bull and bear cases into a final probability estimate:

1. **Weigh evidence by four factors:**
   - **Recency:** More recent evidence gets more weight (see Step 2, point 4)
   - **Source credibility:** Official data > news reports > opinion > social media
   - **Specificity:** Concrete numbers/facts > vague claims
   - **Base rate alignment:** Estimates far from historical base rates need strong evidence

2. **Calculate estimated_probability (0.0-1.0):**
   - Start from the base rate if available
   - Adjust up for bull evidence, down for bear evidence
   - The final number should be between (but not necessarily at the midpoint of)
     the bull-only and bear-only estimates
   - Never estimate 0.0 or 1.0 — nothing is certain

3. **Calculate edge:**
   - For YES side: `edge = estimated_probability - yes_price`
   - For NO side: `edge = (1 - estimated_probability) - no_price`
   - Use whichever side has positive edge (that's the recommended side)

4. **Calculate confidence (0.0-1.0):**
   - 0.8-1.0: Strong, concordant evidence; clear base rate; near-term resolution
   - 0.5-0.7: Moderate evidence; some ambiguity; medium-term resolution
   - 0.3-0.5: Sparse or conflicting evidence; long-term resolution
   - Below 0.3: Highly uncertain — almost certainly a PASS

5. **Apply decision criteria:**

   | Condition | Action |
   |-----------|--------|
   | `|edge| >= 0.04` AND `confidence >= 0.3` | **TRADE CANDIDATE** → proceed to size-position |
   | `|edge| >= 0.04` AND `confidence < 0.3` | **PASS** — edge exists but too uncertain |
   | `|edge| < 0.04` | **PASS** — insufficient edge regardless of confidence |

   The MIN_EDGE_THRESHOLD of 0.04 (4 percentage points) comes from configuration.
   This is lower than the old agent system's 0.10 threshold because the single-agent
   architecture produces more nuanced analysis.

---

### Step 5: Recommended Side and Reasoning

1. **Determine side:**
   - If `estimated_probability > yes_price` → recommend **YES**
   - If `estimated_probability < yes_price` → recommend **NO**

2. **Record reasoning (2-3 sentences):**
   - State WHY you disagree with the market
   - Reference the most compelling evidence
   - Note the key risk that could prove you wrong

3. **Format the output** for the next skill (size-position):
   - `estimated_probability`: your final number
   - `confidence`: your certainty level
   - `edge`: calculated edge value
   - `recommended_side`: YES or NO
   - `reasoning`: your 2-3 sentence summary

---

## Decision Criteria Summary

| Condition | Action | Rationale |
|-----------|--------|-----------|
| YES price outside 0.15-0.85 | PASS | No edge in extreme prices |
| Volume < $10,000/24h | PASS | Insufficient liquidity, wide spreads |
| Already hold position | PASS | Avoid doubling down |
| `|edge| < 0.04` | PASS | Below minimum edge threshold |
| `confidence < 0.3` | PASS | Too uncertain to act on |
| All checks pass | **TRADE CANDIDATE** | Proceed to size-position skill |

---

## Category-Specific Guidance

Different market categories have different dynamics. Apply these adjustments:

| Category | Typical Confidence Range | Key Consideration |
|----------|------------------------|-------------------|
| Crypto | 0.3-0.6 | Extremely volatile; base rates unreliable; weight momentum |
| Politics | 0.4-0.7 | Polls have error margins; look for base rates of similar events |
| Sports | 0.5-0.9 | Strong statistical base rates available; use them heavily |
| Commodities | 0.4-0.7 | Geopolitical supply shocks create regime changes; be cautious |
| Entertainment | 0.3-0.6 | Awards are subjective; critic consensus is the best base rate |
| Finance/Macro | 0.5-0.8 | Fed/ECB are highly telegraphed; economic data has clear trends |

If a category has 3 or more consecutive losses in our trading history, raise the
minimum edge threshold to 0.08 (8 percentage points) for that category until a
win breaks the streak.

---

## Examples

### Example 1: PASS — No Edge (Fed Rate Decision, March 2026)

**Market:** "Will there be no change in Fed interest rates after the March 2026 meeting?"
**Source:** polymarket_claude/output/passes/2026-03-15_fed-rate-decision.md

- **YES price:** $0.997, **NO price:** $0.004
- **Volume:** $60,152,603 (high liquidity)
- **Triage result:** **FAIL at Step 1** — price outside sweet spot (0.997 >> 0.85)

**Analysis shortcut:** At 99.7%, the market is essentially resolved. The Fed had clearly
telegraphed a pause, and market consensus was overwhelming. Buying YES at $0.997 gives
less than 0.3 cents upside per dollar while carrying residual surprise risk.

**Decision:** PASS — untradeable price.

**Lesson learned:** Markets at 99%+ have zero practical edge. The compressed payout means
even correct analysis yields trivial returns. Don't chase resolved outcomes.

---

### Example 2: TRADE CANDIDATE — Arsenal EPL (March 2026)

**Market:** "Will Arsenal win the 2025-26 English Premier League?"
**Source:** polymarket_claude/output/trades/2026-03-15_arsenal-epl.md

- **YES price:** $0.895
- **Volume:** High (actively traded market)
- **Triage:** PASS all filters — price in sweet spot, good volume, resolves May 2026

**Bull Case (estimated probability: 0.97-0.99):**
1. Arsenal lead the EPL by 9 points with 9 games remaining
2. Historical base rate: teams with 9+ point leads at this stage win 97-99% of the time
3. Arsenal expected ~19-21 points from remaining 9 games at 65% win rate
4. Man City would need to win ALL 10 remaining games AND Arsenal would need a historic collapse

**Bear Case (estimated probability: 0.85-0.90):**
1. Arsenal's historical anxiety — fans and bettors remember previous collapses
2. Champions League distraction (Round of 16 vs Leverkusen creates fatigue/injury risk)
3. Direct match vs Man City at the Etihad in April — a heavy loss could shift momentum
4. Key player injuries (Gyokeres etc.) could derail the campaign

**Synthesis:**
- Base rate (97-99%) strongly favors Arsenal
- Bear case risks are real but don't override a 9-point gap with 9 games left
- **estimated_probability = 0.95**
- **edge = 0.95 - 0.895 = 0.055** (5.5 percentage points)
- **confidence = 0.85** (strong base rate, clear evidence, some residual uncertainty)

**Decision:** **TRADE CANDIDATE** — edge 0.055 > 0.04 threshold, confidence 0.85 > 0.3
**Recommended side:** YES
**Reasoning:** "The market underprices Arsenal's title probability by ~5pp. A 9-point lead
with 9 games left historically converts 97-99% of the time, and the bear case risks
(CL fatigue, Etihad match) don't justify 10.5% failure probability. Key risk: an
unprecedented late-season collapse or major injury crisis."

---

### Example 3: PASS — Edge Below Threshold (Iran Regime Fall, March 2026)

**Market:** "Will the Iranian regime fall by March 31?"
**Source:** polymarket_claude/output/passes/2026-03-15_iran-regime-fall.md

- **YES price:** $0.025, **NO price:** $0.975
- **Volume:** $33,723,117 (high liquidity)
- **Triage:** FAIL at Step 1 — YES price outside sweet spot (0.025 < 0.15)

**Analysis (even though triage failed, for illustration):**
- The Iran-US/Israel conflict was active, but "regime fall by March 31" is extremely specific
- The Islamic Republic has survived decades of pressure; no organized armed opposition exists
- 16 days is far too short for regime change of this magnitude
- Fair value estimate: ~1.5-2% (YES), meaning NO at $0.975 has ~0.5-1% edge
- **edge = ~0.01** (1 percentage point) — well below the 0.04 threshold
- **confidence = 0.4** — geopolitical events are inherently unpredictable

**Decision:** PASS — edge too small relative to uncertainty, and price outside sweet spot.

**Lesson learned:** Political tail-risk markets often look like "easy NO" bets but the
edge per dollar is tiny, and black-swan risk (US ground invasion, internal coup) means
the small edge isn't worth the tail risk.

---

### Example 4: TRADE CANDIDATE — Crude Oil $100 (March 2026)

**Market:** "Will crude oil (CL) hit $100 by end of March?"
**Source:** polymarket_claude/output/trades/2026-03-15_crude-oil-100-high.md

- **YES price:** $0.888
- **Volume:** Active commodity market
- **Triage:** PASS all filters — price in sweet spot, good volume, resolves March 31

**Bull Case (estimated probability: 0.95-0.97):**
1. WTI settlement at $98.71 on March 13 — only $1.29 (1.3%) away from target
2. Strait of Hormuz closed by Iran — 20% of global oil supply disrupted
3. Brent crude already above $100 — WTI typically follows with a lag
4. 11 trading days remaining — ample time for a 1.3% move
5. Strong upward trend: +17.9% recovery from March 10 dip

**Bear Case (estimated probability: 0.80-0.85):**
1. Sudden de-escalation — ceasefire/talks could crash prices overnight
2. IEA emergency oil release could suppress prices
3. March 10 precedent: -11.8% single-day crash shows downside volatility
4. WTI-Brent spread of $4-5 means WTI could stay below $100 even with Brent above it

**Synthesis:**
- The proximity to target ($1.29 gap) is the dominant factor
- With 11 trading days and a bullish trend, the probability is high
- De-escalation risk is real but hard to time
- **estimated_probability = 0.92**
- **edge = 0.92 - 0.888 = 0.032** (3.2 percentage points)
- **confidence = 0.70** (good data but commodity volatility is high)

**Decision:** PASS at strict 0.04 threshold (edge = 0.032 < 0.04). The original trader
took this trade, estimating 91-93% vs market 88.8%, giving a 2-4pp edge — right at the
boundary. This is a judgment call: the trader accepted the position at conservative sizing.

**Lesson learned:** Borderline edge cases require extra scrutiny. If the edge is within
1pp of the threshold, consider whether the confidence level truly supports the trade.
A 0.032 edge with 0.70 confidence is a marginal opportunity.

---

## Updating This Skill

This document is a living reference. After each trading cycle:

1. **Add new examples** from resolved trades (both wins and losses)
2. **Refine category guidance** based on calibration data
3. **Adjust confidence ranges** if systematic over/under-confidence is detected
4. **Update decision thresholds** only with strong evidence from 10+ trades

Record changes with a date stamp and brief rationale.
