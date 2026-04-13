# Sports Markets -- Knowledge Base

## Category Profile

| Attribute | Value |
|-----------|-------|
| Variance level | MEDIUM (season-long) to HIGH (single game) |
| Calibration status | No data yet |
| Max position size | 2% bankroll per bet (single game), 3% bankroll (season-long) |
| Min edge required | 4pp standard |

---

## Rules (Apply Before Every Sports Bet)

### Rule 1 -- Distinguish Season-Long vs Single-Game Risk
**Rule**: Season-long markets (EPL winner, NBA champion) have much lower variance than single-game markets. Apply different max position sizes accordingly.
- Season-long with large lead: up to 3% bankroll
- Single playoff game: max 2% bankroll (anything can happen in 90 minutes)
- Championship match: max 2% (neutral venue, motivation even)

### Rule 2 -- Calculate Mathematical Elimination Probability
**Rule**: Before betting on a team to win a league, do the full math:
- What points does the leader need from remaining games?
- What perfect record would the chaser need?
- Is there a scenario where the chaser can win?
- Weight that scenario by its probability.

**Template**:
```
Leader: {X} pts from {N} games ({M} remaining)
Expected: {base rate} pts from {M} games -> final {total}
Chaser: {Y} pts from {N} games ({M+1} remaining)
Maximum possible: {Y + 3*(M+1)} pts
For chaser to win: needs {A} pts AND leader needs <= {B} pts
Probability of both: {calc}%
```

### Rule 3 -- Champions League / Cup Competition Distraction Risk
**Rule**: When a team is deep in cup/CL competition alongside a league title race, factor in fatigue and squad rotation risk. Adjust probability -2 to -5pp depending on schedule congestion.
**Apply when**: Team has CL knockout rounds or domestic cup final within 2 weeks.

### Rule 4 -- Form Window for Single-Game Markets
**Rule**: For single-game markets, use last 5 games (not season average) as primary form indicator. Recent form matters more than season-long stats for one-off games.

### Rule 5 -- Injury News Before Betting
**Rule**: Always check injury news within 24 hours of any single-game bet. A key player absence can shift probability by 5-10pp.
**Sources**: Official club injury reports, reputable football journalists (Sky Sports, BBC Sport, L'Equipe)

---

## Base Rates

| Scenario | Win Probability |
|----------|----------------|
| EPL lead of 9+ pts with 9 games left | 97-99% |
| EPL lead of 5-8 pts with 9 games left | 85-90% |
| EPL lead of 1-4 pts with 9 games left | 55-70% |
| Home team in EPL (average) | 45% |
| Favorite in Champions League knockout | 60-65% |

---

## Edge Sources

Claude populates through trading experience.

---

## Resolution Mechanics

Claude populates through trading experience.

---

## Lessons Learned

### 2026-04-11 — Thunder vs Nuggets WIN (+$130.55, 65.4% return)
**Observation:** Bought NO (against Thunder) at $0.57, 350 shares. OKC rested ALL starters (SGA, Williams, Holmgren, Hartenstein OUT), only 8 players available including 3 two-way contracts. Sportsbook consensus had Nuggets at 78-85% implied but Polymarket had Thunder at 43.5% — a 23.5pp edge, the largest ever found. Five independent sportsbook sources confirmed the line. Nuggets won easily, resolved same day.
**Takeaway:** Rest-day games in the NBA regular season finale can produce massive Polymarket mispricing. Retail bettors on Polymarket don't adjust for lineup news as fast as sportsbooks. When structural factors (all starters sitting) exist AND 3+ sportsbooks confirm, the edge is real. This is a seasonal anomaly — NBA regular season ended April 11, 2026.

### 2026-04-11 — Soccer markets show zero structural edge (6+ cycles of data)
**Observation:** Across 6+ cycles (Atletico Madrid, Arsenal, Brighton, Man City, Newcastle, Crystal Palace), soccer match markets on Polymarket consistently showed 0-1.5pp gap after multi-source sportsbook de-vig verification. No tradeable edge was found in any soccer single-match market.
**Takeaway:** Soccer single-match markets on Polymarket are efficiently priced. Do not spend analysis bandwidth on them unless a structural factor (major injury, suspension, fixture congestion) creates a clear reason for mispricing. Season-long markets (EPL winner) may differ.
