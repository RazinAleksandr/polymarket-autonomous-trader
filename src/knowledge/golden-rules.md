# GOLDEN RULES

**Read this file first. Every session. No exceptions.**

These rules cost real money to learn. Each one has a trade behind it.
The list is capped at 20. When adding a rule, merge or remove an existing one first.

Last updated: 2026-04-09 | Rules: 17

---

## Pre-Trade Rules (Before Every Bet)

**Rule 1 — CHECK ALL OPTIONS, not just the frontrunners**
- Trigger: Any market with 3+ possible outcomes (awards, tournaments, elections)
- Rule: List every outcome and its price before forming a view. Give any serious contender priced < 10% a minimum floor of 3-5%.
- Taught by: Oscars 2026 — Bugonia at ~2% won Best Picture. We never even looked at it.

**Rule 2 — READ THE RESOLUTION CRITERIA, not the title**
- Trigger: Every single bet, no exceptions
- Rule: The market title and the resolution text can differ materially. Read the full `description` field. Build a decision tree: exactly what must happen for YES? For NO? Are there edge cases?
- Taught by: Oil markets — "WTI hits $100" resolved on CME SETTLEMENT not intraday. Two completely different things.

**Rule 3 — CHECK CALIBRATION BEFORE SIZING**
- Trigger: Before placing any bet in a category you've traded before
- Rule: Check `knowledge/calibration.json` for category-specific accuracy data before sizing. If calibration error < -10pp, require +2pp additional edge and reduce size by 25%.
- Taught by: Oscars — stated 24%, won 0%. We didn't correct for overconfidence.

**Rule 4 — SETTLEMENT != INTRADAY (commodities)**
- Trigger: Any commodity price target market (oil, gold, gas)
- Rule: CME settlement is the volume-weighted average near close. It is ALWAYS lower than intraday highs during volatile sessions. On March 9, 2026: intraday $119.94, settlement $94.65 (-21%). Never estimate probability of settlement targets using intraday price data.
- Taught by: Oil markets, session 1.

**Rule 5 — MINIMUM 4pp EDGE, no exceptions**
- Trigger: Any market where Kelly says bet but edge is < 4pp
- Rule: Pass. Transaction costs, model error, and uncertainty consume edges below 4pp. No amount of "it feels right" justifies sub-4pp bets.
- Taught by: Fed rate decision at 99.7% — 0.3pp upside, no edge worth taking.

**Rule 6 — CORRELATED POSITION CHECK before sizing**
- Trigger: Before placing any new bet
- Rule: Check open positions. If new bet is positively correlated with existing open bets (both lose in the same scenario), reduce size. Max correlated exposure in one scenario: 10% bankroll.
- Taught by: Oil $100 YES + Iran regime NO both depend on the Iran conflict continuing.

**Rule 7 — NEVER BET AT 97%+ (no edge left)**
- Trigger: Any market where YES or NO is priced above 97%
- Rule: Pass. Maximum upside is $0.03 per dollar. Transaction costs and black swan risk make this negative EV.
- Taught by: Fed rate no-change at 99.7% — correctly passed.

**Rule 15 — DISTINGUISH WTI FROM BRENT**
- Trigger: Any crude oil market
- Rule: News says "oil at $100+" often means Brent. Polymarket uses WTI (NYMEX). WTI trades $4-5 below Brent. Always verify which benchmark the market resolves on and which benchmark the news references.
- Taught by: March 12-13 2026 — Brent above $100, WTI at $98.71.

---

## Sizing Rules

**Rule 8 — CATEGORY SIZE CAPS (hard limits)**
- Trigger: Any bet
- Rule: Max single bet = 5% bankroll. Max category exposure = 15% bankroll.
  - Politics: max 3% per bet
  - Awards (Oscars, BAFTAs): max 2% per bet, require 8pp edge (calibration probation)
  - Sports (single game): max 2% per bet
  - Commodities: max 4% per bet
- Taught by: Oscars 2026 — $200 loss on a single category. Awards cap tightened to 2% with 8pp edge floor.

**Rule 9 — USE FRACTIONAL KELLY, never full Kelly**
- Trigger: Every sizing decision
- Rule: High confidence -> 1/4 Kelly. Medium -> 1/6 Kelly. Low -> 1/10 Kelly. Full Kelly assumes a perfect model. We never have a perfect model.
- Taught by: Kelly criterion literature + early sizing experiments. Full Kelly leads to ruin with imperfect estimates.

**Rule 10 — LOSING STREAK RESTRICTION**
- Trigger: 3 consecutive losses in any category
- Rule: That category requires 8pp minimum edge (vs standard 4pp) until a win. Max bet drops to 2% bankroll. The streak is information — something is wrong with the model.
- Taught by: Oscars category — consecutive losses revealed systematic overconfidence in guild predictors.

---

## Research Rules

**Rule 11 — STATUS QUO HAS MORE INERTIA THAN MARKETS PRICE**
- Trigger: Any market asking "will X change by date Y?" (ceasefires, regime changes, policy reversals)
- Rule: Markets systematically overprice dramatic change in the short term. The status quo wins ~70% of the time vs the market-implied ~40-50%. Start with status quo as the base case and require strong evidence to deviate.
- Taught by: Iran regime fall March 31 at 3.2% (fair ~1.5%), Russia-Ukraine ceasefire at 37.5% (fair ~24%).

**Rule 12 — GUILD PREDICTORS WEAKENED (post-2020 Academy expansion)**
- Trigger: Any Oscars/awards market
- Rule: SAG Ensemble -> Best Picture reliability dropped from ~65% to ~45-55%. DGA + PGA double -> ~50% (was 70%). The Academy's expanded international membership diverges from US guild consensus. Give auteur dark horses (Lanthimos, Lynch, Anderson) a minimum 5-8% floor.
- Taught by: Oscars 2026 — Bugonia (Lanthimos) at ~2% won. All guild winners lost.

**Rule 13 — CROSS-PLATFORM CHECK before finalising probability**
- Trigger: Any market with volume > $50k where you have a directional view
- Rule: Check Metaculus/Manifold implied probability for the same question. If their estimate differs from yours by > 10pp, explain why before proceeding.
- Note: Cross-platform checking is aspirational — no automated script exists in polymarket-trader yet. Perform manually via web research when possible.
- Taught by: General forecasting best practice — superforecasters consistently cross-reference multiple prediction platforms.

**Rule 16 — HIGH VARIANCE = WIDER DISTRIBUTIONS**
- Trigger: Oscars, elections, geopolitical events
- Rule: Never assign 92%+ to any Oscars category or similar high-variance event. Give dark-horse contenders a minimum 5-8% floor. Fat-tailed distributions demand humility — the "impossible" outcome happens more often than models predict.
- Taught by: Oscars 2026 — Bugonia at ~2% won Best Picture despite zero guild wins.

---

## Deadline Rules

**Rule 17 — DEADLINES OVERRIDE STATUS QUO BIAS**
- Trigger: Any market where a major deadline or ultimatum exists within the resolution window
- Rule: When a powerful actor sets a hard deadline with severe consequences for non-compliance (e.g., military ultimatum, trade sanctions deadline, regulatory filing date), status quo bias (Rule 11) is weakened. Deadlines create negotiation pressure that can produce rapid outcomes. When a credible deadline exists within 7 days of resolution, increase the base probability of change/resolution by 2-3x versus the no-deadline base rate. The more severe the consequences of the deadline passing without resolution, the stronger the override.
- Taught by: Iran ceasefire April 2026 — entered NO at $0.90 (95% confidence in no ceasefire), Hormuz ultimatum deadline was April 6 (next day). Pakistan brokered ceasefire on April 7. Lost $300.77 (3% of bankroll). The deadline created negotiation pressure that we dismissed as "just an escalation signal."

---

## Learning Rules

**Rule 14 — POST-MORTEM EVERY LOSS, immediately**
- Trigger: Any resolved LOSS
- Rule: Write the post-mortem BEFORE moving to the next task. Classify the error: information / model / calibration / resolution / black_swan. Extract one specific actionable rule. Add it to this file if it's general enough, or to `knowledge/market_types/<category>.md` if category-specific. Never leave a loss unexamined.
- Taught by: Every loss ever. The agent that skips post-mortems repeats mistakes indefinitely.

---

## How to Update This File

- Add rule: only if it's general enough to apply across categories. Category-specific rules go in `knowledge/market_types/`.
- When adding: remove or merge an existing rule if count would exceed 20.
- Never remove a rule without replacing it — loss of institutional memory is costly.
- Every rule needs a "Taught by" citation. Rules without citations get removed at next review.
