# Commodities Markets -- Knowledge Base

## Category Profile

| Attribute | Value |
|-----------|-------|
| Variance level | HIGH (geopolitical shock risk) |
| Calibration status | No data |
| Max position size | 4% bankroll per bet |
| Min edge required | 4pp (standard) |

---

## Rules (Apply Before Every Commodities Bet)

### Rule 1 -- Settlement Price != Intraday Price (CRITICAL)
**Date learned**: 2026-03-15
**Rule**: Always research which price mechanism Polymarket uses for resolution. For WTI crude oil, Polymarket uses CME OFFICIAL SETTLEMENT price, NOT the intraday high/low.
**Why**: March 9, 2026: WTI intraday high = $119.94, but CME settlement = $94.65 (-21% gap). If you price binary targets off intraday data, you will massively overestimate the probability of hitting round-number thresholds.
**Apply when**: Any oil market (or any commodity) where the resolution says "settles at X" or "WTI settlement price."
**Settlement mechanics**: Settlement = volume-weighted average near market close. Professional sellers sell into intraday spikes, pulling settlement below intraday high.

### Rule 2 -- Know Which Benchmark (WTI vs Brent)
**Date learned**: 2026-03-15
**Rule**: Polymarket oil markets typically use WTI (NYMEX). Brent trades at a premium of $4-7 typically. Do not use Brent prices to estimate WTI resolution probability.
**Apply when**: Any crude oil binary market.
**Data source**: CME Group WTI settlement history (free on CME website or Bloomberg).

### Rule 3 -- Check Geopolitical Context Before Sizing
**Date learned**: 2026-03-15
**Rule**: During active geopolitical crises (Hormuz closure, OPEC+ emergency meetings, strategic reserve releases), oil markets have extreme volatility AND mean-reversion risk. Size down 25% from standard Kelly for any position opened during a crisis spike.
**Apply when**: Oil price is >25% above its 30-day average.

### Rule 4 -- Monitor Resolution Date vs Geopolitical Timeline
**Rule**: For monthly binary targets (e.g., "WTI >= $100 before end of March"), monitor the geopolitical situation daily. A ceasefire or diplomatic breakthrough can move the price by 15-20% overnight, converting a near-certain WIN to a LOSS.

---

## Base Rates

Claude populates through trading experience.

---

## Edge Sources

| Signal | Type | Reliability |
|--------|------|------------|
| Settlement < intraday gap > 15% | NO bias on round-number targets | THEORETICAL (untested) |
| Ceasefire imminent -> crash risk | Scenario risk | HIGH -- monitor daily |
| IEA release announced -> crash | Scenario risk | HIGH -- usually -10 to -15% |
| Brent already > X -> WTI approaching | Leading indicator | MEDIUM (5-7 day lag) |

---

## Resolution Mechanics

For commodity price targets on Polymarket:
- WTI crude: CME OFFICIAL SETTLEMENT price, not intraday high/low
- Settlement = volume-weighted average near market close
- Professional sellers sell into intraday spikes, pulling settlement below intraday high
- Always verify which specific data source the market uses for resolution

---

## Lessons Learned

### Settlement vs Intraday (March 2026)
March 9, 2026: WTI intraday high = $119.94, but CME settlement = $94.65. A 21% gap that would have caused massive mispricing if using intraday data for probability estimation. This lesson applies to ALL commodity price target markets -- always verify settlement mechanics.
