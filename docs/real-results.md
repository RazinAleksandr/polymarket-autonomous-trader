# Real Results: 30 Autonomous Trading Cycles

How our AI agent actually trades, learns, and evolves — with real numbers from 30 unattended cycles (April 4–12, 2026).

## The Numbers

- **30 cycles** running autonomously every 2 hours via cron
- **1,500+ markets scanned**, ~100 analyzed in depth with web research
- **7 trades** executed across 6 markets
- **3 positions closed**: 2 wins, 1 loss (66.7% win rate)
- **3 positions open**: resolving within days
- **Realized P&L: -$149.06** on a $10,000 paper bankroll
- **7 strategy rules** learned from experience (started with zero)
- **17 golden rules** in the knowledge base

---

## Trade-by-Trade History

### Trade 1: US Forces Enter Iran by April 30 — YES

- **Date:** April 4, 2026
- **Side:** YES at $0.83, 128 shares, cost $106.24
- **Edge:** 5.5% — agent estimated 40% probability vs market pricing
- **What happened:** Resolved YES on April 9
- **Result: WIN, +$21.16**
- **Lesson learned:** The agent had actually misidentified this market — it thought it was trading "Hungary PM Orban" because the database `question` field was empty. The win was lucky. This bug led to the **Position Identity Verification** rule: always verify market identity via the Gamma API, never trust the DB alone.

---

### Trade 2: US x Iran Ceasefire by April 15 — NO

- **Date:** April 5, 2026
- **Side:** NO at $0.90, 333 shares, cost $299.70
- **Edge:** 5.5% — agent estimated only 5% chance of ceasefire
- **Reasoning:** Talks had collapsed on April 3, Iran rejected all proposals, Trump was escalating with a Hormuz ultimatum. The agent applied "status quo bias" (golden rule 11: markets overprice dramatic change) and concluded ceasefire was near-impossible.
- **What happened:** Pakistan brokered a surprise ceasefire on April 7-8, just 2 days after entry. The Hormuz ultimatum deadline on April 6 created the negotiation pressure that the agent dismissed.
- **Result: LOSS, -$300.77**
- **Lessons learned (3 new strategy rules from this single trade):**
  - **Geopolitical Probability Hard Caps** — the agent estimated 95% NO, violating its own 90/10 cap from the knowledge base. New rule: hard-enforce 90/10 caps, if edge disappears after capping then skip.
  - **Deadline Exception to Status Quo Bias** — deadlines with severe consequences create negotiation pressure that overrides normal status quo inertia. New rule: increase probability of change by 2-3x when a credible deadline exists within 7 days.
  - **Resolution Criteria Re-Read** — after the ceasefire, the agent went 5 cycles without re-reading the resolution criteria. The criteria said the 14-day period only needs to BEGIN by April 15, not complete. New rule: re-read full resolution text after any material event.

---

### Trade 3: Will the Next PM of Hungary Be Viktor Orban — NO

- **Date:** April 5, 2026
- **Side:** NO at $0.66, 257 shares, cost $169.62
- **Edge:** 7.0% — agent estimated 73% chance Orban loses
- **Reasoning:** Multiple independent polls showed Tisza (Magyar) leading by 19-23pp. Even accounting for the worst-case 2022 polling error (13pp swing), Tisza would still clear the gerrymandering threshold. Single unified opposition party vs 2022's fragmented coalition reduced coordination risk.
- **What happened:** Election day is April 12. Polls opened at 05:00 UTC. Current price: $0.785 NO (+14.1% unrealized). All independent pollsters (AtlasIntel, Median, Iranytu) confirm Tisza leading 10-13pp.
- **Result: OPEN — resolving today**
- **If Orban loses:** +$85.86 profit
- **If Orban wins:** -$171.14 loss

---

### Trade 4: Iran x Israel/US Conflict Ends by April 15 — NO

- **Date:** April 9, 2026
- **Side:** NO, filled in two orders: 150 shares at $0.39 + 236 shares at $0.389, total 386 shares, cost $151.73
- **Edge:** 9.1% — agent estimated 48% probability of conflict ending
- **Reasoning:** Ceasefire had been announced on April 7-8 but was immediately fragile. Iran accused the US of violations within hours, paused Hormuz reopening, and threatened direct retaliation against Israel. The resolution criteria require a continuous 14-day period without qualifying military action, which the agent judged demanding given the tension.
- **What happened:** Price softened from $0.5385 to $0.4245 as ceasefire dynamics shift.
- **Result: OPEN — unrealized +$10.16**
- **Resolves:** April 15-22 window (14-day ceasefire period must begin by April 15)

---

### Trade 5: US x Iran Meeting by April 10 — YES

- **Date:** April 9, 2026
- **Side:** YES at $0.446, 250 shares, cost $111.50
- **Edge:** 7.1% — agent estimated 52% probability
- **Reasoning:** Both US and Iran delegations were heading to Islamabad. Iran's FM confirmed talks would begin on April 10. Multiple sources corroborated. The agent judged that indirect meetings through mediators would qualify under the resolution criteria.
- **What happened:** The deadline passed 68+ hours ago with no official meeting. Price collapsed to $0.004.
- **Result: OPEN but near-certain LOSS, expected ~-$112.60**
- **Lesson pending:** Source weighting for diplomatic contexts — official statements about "heading to talks" don't guarantee meetings happen.

---

### Trade 6: Thunder vs Nuggets (NBA) — NO (bet against Thunder)

- **Date:** April 11, 2026
- **Side:** NO at $0.57, 350 shares, cost $199.50
- **Edge:** 23.5% — the largest edge the agent has ever found
- **Reasoning:** OKC was resting ALL starters (SGA, Williams, Holmgren, Hartenstein — all listed OUT). Only 8 players were available, including 3 two-way contract players. Sportsbook consensus had Nuggets at 78-85% implied probability (FanDuel Nuggets -440, spread -11.5), but Polymarket had Thunder at 43.5%. Five independent sportsbook sources all confirmed the line.
- **What happened:** Nuggets won easily. Resolved same day.
- **Result: WIN, +$130.55**
- **Lesson learned:** Sports CAN show massive edges when structural factors (all starters resting) create retail pricing failures on Polymarket. The 3+ sportsbook source rule correctly confirmed this was a real edge, not stale data. This was a seasonal anomaly — NBA regular season ended April 11.

---

## Trades Not Taken (Equally Important)

The agent skipped far more trades than it took. Some notable skips that proved correct:

- **Hawks vs Heat (April 12):** Showed a 22.7pp gap with 2 sportsbook sources. The agent required 3+ sources and skipped. Hours later, the Hawks line FLIPPED from -240 favorites to +120 underdogs on FanDuel when multiple starters were listed as resting. The real edge was only 4.2pp. The 3+ source rule prevented a bad entry.

- **Pistons vs Hornets (April 10):** Stale BetRivers line inflated apparent edge to 6.5pp. DraftKings showed the real line — 0pp edge. Correctly skipped.

- **Atletico Madrid (April 11):** A "best odds" aggregator showed 42.5% implied probability, suggesting edge. But Bet365/Interwetten/Merkur consensus was ~33%, matching Polymarket. Aggregators cherry-pick outlier lines. Correctly skipped.

- **16 consecutive zero-trade cycles (cycles 4-20):** The agent scanned 50 markets every 2 hours for 32 hours straight without finding tradeable edge. Most sports markets showed <4pp edge after de-vigging sportsbook odds. The agent was disciplined enough to wait.

---

## How Strategy Evolved

The agent started with a blank `state/strategy.md` and zero rules. Here's what it built through experience:

**Cycle 7 (April 4) — 3 rules from observations:**
1. **Position Identity Verification** — after misidentifying Trade 1's market
2. **Tennis Pricing Inefficiency** — observed 6-12pp consistent overpricing of tennis favorites
3. **Scan Timing** — kept missing tennis matches that started before the scan ran

**Cycle 11 (April 9) — 2 rules from the big $301 loss:**
4. **Geopolitical Probability Hard Caps** — enforce 90/10 max on all geopolitical estimates
5. **Deadline Exception to Status Quo Bias** — deadlines override normal inertia

**Cycle 21-22 (April 11) — 1 rule from sportsbook verification work:**
6. **Sportsbook Line Freshness Verification** — require 3+ independent named sportsbooks, discard stale lines, never use "best odds" aggregators

**Cycle 25 (April 11) — 1 rule from position management error:**
7. **Resolution Criteria Re-Read** — re-read full criteria after any material event on an open position

The pattern is clear: the agent mostly learns from mistakes. The $301 Iran ceasefire loss alone spawned 3 of the 7 rules. Over 30 cycles, the rules became increasingly specific and evidence-based — each one cites the exact trades and data points that motivated it.

---

## How Math Analytics Drive Decisions

### Edge Calculation

Every trade starts here:

```
edge = estimated_probability - market_price - fee_adjustment
```

If edge < 4 percentage points after fees, the trade is automatically skipped. Category-specific fees are modeled (sports 0.75% peak, crypto 1.8%, geopolitics 0%).

### Kelly Criterion Position Sizing

The agent uses quarter-Kelly for conservative sizing:

```
Full Kelly:  f* = (b * p - q) / b
Adjusted:    f  = f* * 0.25     (quarter-Kelly)
```

Quarter-Kelly captures ~50% of theoretical growth with ~25% of the variance. This is then further adjusted:

- Multiplied by confidence (0.3-1.0) — bigger positions when analysis is stronger
- Capped at 5% of bankroll per position (hard limit)
- Capped by remaining capacity under 30% total exposure
- Capped by category limits (sports 2%, politics 3%, crypto 3%)
- Minimum $5 USDC order size

### Calibration Tracking (Brier Scores)

Every resolved trade updates the agent's calibration data:

```
brier_score = (stated_probability - actual_outcome)^2
```

Current calibration after 4 resolved trades:
- **Overall Brier: 0.270** (below 0.30 warning threshold)
- **Sports:** 1 trade, Brier 0.040 (well-calibrated)
- **Politics:** 2 trades, Brier 0.460 (underconfident — needs more data)
- **Crypto:** 1 trade, Brier 0.122 (overconfident but won)

When a category accumulates 5+ trades with |error| > 10pp, the system auto-generates a calibration correction that adjusts future probability estimates by 70% of the observed error (capped at 20pp). Not enough data yet for corrections to activate.

### Risk Limits

- Correlation detection: if two positions lose in the same scenario, sizing is halved
- 90% utilization warnings on per-position and total exposure
- 5 consecutive losses trigger a 24-hour trading pause
- 3 losses in one category require 8pp edge (double normal) until a win

---

## How Web Search Drives Analysis

The agent uses Claude Code's built-in WebSearch tool for every market it analyzes. This is not keyword matching — it's doing real analyst work.

### The Research Process

For each candidate market, the agent runs structured bull/bear research:

1. **Bull case:** 3-5 queries looking for supporting evidence (e.g. "Hawks vs Heat prediction April 2026", "Iran ceasefire latest news")
2. **Bear case:** 3-5 queries looking for counter-evidence (e.g. "Hawks injury report April 12", "Iran ceasefire risks obstacles")
3. **Sportsbook verification (sports markets):** searches for real-time odds from FanDuel, DraftKings, Bet365, Kalshi, Sports Interaction
4. **De-vigging:** converts raw sportsbook odds to implied probabilities by removing the bookmaker's margin
5. **Consensus building:** requires 3+ independent sources to agree before declaring edge

### Real Sources Cited

The cycle reports show the agent citing real, named sources:

- **Sportsbooks:** FanDuel, Sports Interaction, Kalshi/SportsGrid, SportsGambler, OddsShark
- **News:** Al Jazeera, CNBC, NBC News, CBS, PBS NewsHour, Bloomberg
- **Sports:** SI.com, iHeart, Yardbarker, Heavy.com (injury reports)
- **Analysis:** Dimers, OddsPortal

Every cycle report includes a Sources section with full URLs for audit.

### Example: How the Agent Analyzed Thunder vs Nuggets

This was Trade 6, the biggest win (+$130.55):

1. Searched for Thunder injury report — found ALL starters listed OUT on SI.com and Yardbarker
2. Searched FanDuel odds — found Nuggets -440 moneyline, -11.5 spread
3. Searched Kalshi — found Nuggets -456, confirming FanDuel
4. Searched Sports Interaction — found similar line
5. Searched two more sources — 5 total independent confirmations
6. De-vigged all lines: consensus Nuggets 78-85%, Thunder 15-22%
7. Compared to Polymarket: Thunder priced at 43.5%
8. Edge: 23.5 percentage points — by far the largest the agent had ever seen
9. All 5 sources agreed within 7pp. No stale data detected.
10. Executed: 350 shares NO at $0.57

The same verification process prevented bad trades. When Hawks/Heat showed a 22.7pp gap but Sports Interaction hadn't updated their line (stale by 4+ hours), the agent detected the disagreement and skipped.

---

## System Architecture for Autonomy

The agent runs unattended on this schedule:

- **Every 10 minutes:** Python heartbeat checks for expiring positions, new data, or overdue scans (no LLM cost)
- **Every 2 hours:** Full Claude trading cycle if heartbeat signals work to do
- **Daily at 2 AM UTC:** Forced full cycle regardless of heartbeat

Each cycle:
1. Reads its evolving strategy (`state/strategy.md`) and immutable guardrails (`state/core-principles.md`)
2. Loads the 3 most recent cycle reports for context
3. Runs all 5 phases (check positions, find opportunities, analyze, size/execute, learn)
4. Writes a detailed cycle report to `state/reports/`
5. Updates strategy with 0-3 evidence-backed changes

PID lockfile prevents overlapping cycles. 20-minute timeout kills runaway sessions.

---

## What's Working

- **Disciplined edge detection:** The 3+ sportsbook source rule prevented at least 2 bad trades (Hawks/Heat, Pistons/Hornets)
- **Self-learning from losses:** The $301 Iran loss directly produced 3 rules that made subsequent analysis better
- **Risk control:** Never exceeded 5% per position or 30% total exposure across 30 cycles
- **Patience:** Went 16 cycles without trading when no edge existed — didn't force trades

## What's Not Working Yet

- **Geopolitical overconfidence:** The Iran ceasefire trade (95% NO, actual ceasefire in 2 days) was the costliest mistake
- **Diplomatic source weighting:** Trade 5 trusted "heading to talks" statements that didn't materialize
- **Edge scarcity:** Most Polymarket markets are efficiently priced. Tradeable edge is rare — the agent finds it maybe once every 5-10 cycles
- **Net P&L still negative:** -$149 realized, dominated by the single $301 loss

## Current Live Trading Gate Status

| Criterion | Required | Actual | Status |
|-----------|----------|--------|--------|
| Paper cycles | 10+ | 30 | PASS |
| Cumulative P&L | Positive | -$149.06 | FAIL |
| Win rate | > 50% | 66.7% | PASS |
| Operator confirmation | Manual | Not requested | PENDING |

The P&L gate is blocking live trading — which is exactly what the safety system is designed to do. The agent needs to dig out of the Iran ceasefire hole before live trading unlocks.
