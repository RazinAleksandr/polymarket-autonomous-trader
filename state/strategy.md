# Strategy

This document is updated by the trading agent after each cycle.
It starts blank and evolves based on trading experience.
Claude builds all rules here through autonomous trading -- no pre-seeded content.

## Market Selection Rules

### Tennis Pricing Inefficiency (added cycle 7, 2026-04-04)
**Evidence:** 4 data points across 4 cycles. Polymarket consistently overprices tennis favorites by 6-12pp vs vig-adjusted sportsbook odds. Examples: Paul/Tiafoe 6-10pp gap (cycles 4-6), Pegula/Jovic 12pp gap (cycle 7).
**Rule:** When a tennis match has NOT yet started, compare Polymarket YES price to vig-adjusted sportsbook odds. If the gap exceeds 6pp, consider buying the underdog (NO side). Sports category caps apply (2% bankroll, 4pp min edge).

### Scan Timing (added cycle 7, 2026-04-04)
**Evidence:** 3 cycles of tennis matches starting before scan time (17:00+ UTC), rendering edges untradeable.
**Rule:** Run market scans before 16:00 UTC to catch tennis and other time-sensitive individual sport markets before they begin.

## Analysis Approach

### Deadline Exception to Status Quo Bias (added cycle 11, 2026-04-09)
**Evidence:** Iran ceasefire loss -$300.77 (3% bankroll). Entered NO at 95% on April 5; Hormuz ultimatum deadline April 6; Pakistan brokered ceasefire April 7. Rule 11 (status quo bias) was over-applied because the deadline fundamentally changed negotiation dynamics.
**Rule:** When a credible hard deadline with severe consequences exists within 7 days of the market resolution window, increase the base probability of change/resolution by 2-3x. Deadlines create negotiation pressure that overrides normal status quo inertia. Do NOT apply Rule 11 at full weight when a deadline is imminent.

### Geopolitical Probability Hard Caps (added cycle 11, 2026-04-09)
**Evidence:** Same Iran ceasefire trade. Our politics knowledge base (Rule 3) says cap geopolitical probabilities at 90% / floor at 5%. We estimated 95% NO (5% YES), violating the cap. The cap exists because geopolitical events are inherently unpredictable.
**Rule:** Hard-enforce 90/10 caps on all geopolitical probability estimates. If raw synthesis produces >90% for either side, automatically cap at 90% and recalculate edge. If edge disappears after capping, SKIP the trade. This is not optional — the cap is a pre-commitment against overconfidence.

### Position Identity Verification (added cycle 7, 2026-04-04)
**Evidence:** Cycles 4-6 misidentified position (market 1640919) as "Hungary PM Orban" when it was actually "US forces enter Iran by Apr 30" because the DB `question` field was empty.
**Rule:** At cycle start, verify every open position's market identity via Gamma API. Never rely solely on the database `question` field. Cross-reference market_id to confirm the actual question and resolution criteria.

## Risk Parameters

## Trade Entry/Exit Rules

## Cycle Health Tracking

### Zero-Trade Streak
- Cycles 4-7: 4 consecutive zero-trade cycles (excluding cycle 4's Iran trade)
- Binding constraint: non-sports market availability within 14-day resolution window
- Sports consistently show <4pp edge (7 cycles of evidence)
- Tennis is the exception but matches expire before scan time
