# Autonomous Polymarket Trading Agent — Final System Design

> **HISTORICAL DOCUMENT** — This is the original design doc that drove the v1.0 build (March-April 2026). The system has since been built and is running. For current live state see `.planning/PROJECT.md` and `src/README.md`. Some references (e.g. `strategies.md`, `edge-sources.md`) describe planned files that were later removed as redundant.

---

## Core Philosophy

**Claude IS the trader.** Not a bot with hardcoded rules. Not a Python program that follows if/else logic. Claude Code runs autonomously, makes all trading decisions through its own reasoning, and evolves its own strategy by reading outcomes and rewriting its own instructions.

Python tools are **hands, not brains** — they fetch data, place orders, calculate math. But every decision — what to trade, how much, when to exit, what rules to change — lives in Claude's reasoning, guided by files Claude itself writes and updates.

The system is a **self-modifying autonomous agent**:
```
Claude reads its own strategy → makes trades → sees results → rewrites its strategy → repeat
```

No human edits the strategy. No human picks markets. No human sizes positions. Claude does it all, 24/7, learning from every outcome.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                    │
│   CLAUDE CODE = THE AUTONOMOUS TRADER                             │
│                                                                    │
│   Claude reads these files        Claude calls these tools        │
│   every session:                  to act on the world:            │
│                                                                    │
│   ┌──────────────────┐           ┌──────────────────┐            │
│   │ CLAUDE.md         │           │ Python CLI Tools  │            │
│   │ (master prompt)   │           │                   │            │
│   │                   │           │ discover_markets   │            │
│   │ state/strategy.md │           │ get_prices         │            │
│   │ (Claude writes    │           │ execute_trade      │            │
│   │  and updates this)│           │ get_portfolio      │            │
│   │                   │           │ check_resolved     │            │
│   │ knowledge/        │           │ sell_position      │            │
│   │  golden-rules.md  │           │ get_market_intel   │            │
│   │  calibration.json │           │ record_outcome     │            │
│   │  market-types/*.md│           │                   │            │
│   │  strategies.md    │           │ (pure I/O — no     │            │
│   │  edge-sources.md  │           │  decisions inside) │            │
│   │                   │           └──────────┬─────────┘            │
│   │ state/            │                      │                     │
│   │  positions.json   │                      ▼                     │
│   │  bankroll.json    │           ┌──────────────────┐            │
│   │  cycle reports    │           │ Polymarket APIs    │            │
│   └──────────────────┘           │ Gamma (discovery)  │            │
│                                   │ CLOB (execution)   │            │
│   Claude writes these files:      │ Polygon (wallet)   │            │
│   - Updates strategy.md           └──────────────────┘            │
│   - Adds rules to golden-rules.md                                 │
│   - Updates calibration.json                                      │
│   - Edits market-types/*.md playbooks                             │
│   - Writes cycle reports                                          │
│   - Modifies its OWN CLAUDE.md                                    │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

### Base Project: polymarket-agent/

We build on top of `/home/trader/polymarket-agent/` — the only project with working end-to-end code:
- 11 Python CLI tools (all working, tested)
- Gamma API + CLOB API integration (complete)
- Paper + live order execution via py-clob-client (complete)
- SQLite database with 5 tables (working, has data)
- 167/189 tests passing
- Category-specific fee calculation (complete)
- Wallet signing for Polygon (complete)
- Cron scheduling via tmux (working)
- Has actually executed trades across multiple cycles

We transplant **knowledge** from `/home/trader/polymarket_claude/`:
- 14 golden rules (battle-tested, loss-cited)
- 5 category playbooks (crypto, politics, sports, commodities, entertainment)
- Calibration tracking pattern
- Heartbeat-before-LLM pattern
- Bayesian probability estimation framework
- Strategy lifecycle system (TESTING → PERFORMING → RETIRED)
- Edge source tracking

We borrow **ideas** from Vibe-Trading and AI-Trader:
- Bull/Bear adversarial debate structure (Vibe-Trading)
- Market intelligence: macro regime, ETF flows, news (AI-Trader)
- Context compression for long sessions (Vibe-Trading)

### .claude/ Directory — Claude's Configuration

**Critical design decision: Single agent, no sub-agents.**

Claude operates as ONE agent per session. No spawning sub-agents (scanner, analyst, risk-manager, etc.) — that fragments intelligence. Claude sees everything, reasons about everything, decides everything in one session.

`.claude/agents/` is **removed**. Instead we use `.claude/skills/` — reference documents Claude loads when it needs a specific framework.

```
.claude/
├── CLAUDE.md              ← Master instructions. Claude's identity + process.
│                            Claude CAN modify this to improve its own process.
│
├── settings.json          ← Claude Code permissions config.
│                            Allows tool execution, file writes, bash, web search.
│
└── skills/                ← Reference frameworks (NOT separate agents)
    ├── evaluate-edge.md       Bayesian probability estimation framework:
    │                          base rate → evidence → market blend → calibration
    │                          Claude loads this when analyzing a market.
    │
    ├── size-position.md       Kelly criterion + constraints checklist:
    │                          full Kelly → fractional → category cap → correlation
    │                          Claude loads this when sizing a trade.
    │
    ├── resolution-parser.md   How to read resolution criteria:
    │                          what source, what time, what threshold, gotchas
    │                          Claude loads this before any trade decision.
    │
    ├── post-mortem.md         Loss analysis framework:
    │                          classify error → extract rule → update knowledge
    │                          Claude loads this after any loss.
    │
    ├── calibration-check.md   Pre-trade calibration review:
    │                          read calibration.json → apply corrections
    │                          Claude loads this before sizing.
    │
    └── cycle-review.md        End-of-cycle learning extraction:
                               what worked → what failed → strategy changes
                               Claude loads this at end of every cycle.
```

**Why skills instead of agents:**

| Sub-agents (old design) | Skills (new design) |
|------------------------|---------------------|
| 8 separate Claude sessions | 1 Claude session |
| Each sees only its own context | Claude sees EVERYTHING |
| Can't make holistic decisions | "This market looks good but I already have 2 crypto positions" |
| Rigid pipeline order | Claude decides what to do based on situation |
| JSON handoff between agents loses nuance | Full reasoning chain preserved |
| 8x session overhead | 1 session, loads skill docs on demand |

**How skills work in practice:**
```
Claude's internal reasoning:
  "I found an interesting crypto market. Let me load my evaluation framework."
  → Reads .claude/skills/evaluate-edge.md
  "Base rate for BTC hitting round number in 7 days is ~45%..."
  "Now let me size this. Loading position sizing framework."
  → Reads .claude/skills/size-position.md
  "Quarter Kelly gives $280, but I already have a crypto position..."
  → Claude decides based on full context, not a rigid pipeline
```

### Concrete Modification Plan for polymarket-agent/

```
WHAT WE MODIFY IN polymarket-agent/:

.claude/
├── CLAUDE.md              ← REWRITE completely (single autonomous trader)
├── settings.json          ← KEEP, verify permissions
├── agents/                ← DELETE entire directory (no sub-agents)
│   ├── scanner.md            (Claude does this itself)
│   ├── analyst.md            (Claude does this itself)
│   ├── risk-manager.md       (Claude does this itself)
│   ├── planner.md            (Claude does this itself)
│   ├── reviewer.md           (Claude does this itself)
│   ├── strategy-updater.md   (Claude does this itself)
│   ├── position-monitor.md   (Claude does this itself)
│   └── outcome-analyzer.md   (Claude does this itself)
└── skills/                ← ADD new directory
    ├── evaluate-edge.md      (transplant from polymarket_claude)
    ├── size-position.md      (transplant from polymarket_claude)
    ├── resolution-parser.md  (transplant from polymarket_claude)
    ├── post-mortem.md        (NEW — loss analysis framework)
    ├── calibration-check.md  (transplant from polymarket_claude)
    └── cycle-review.md       (NEW — learning extraction)

knowledge/                 ← ADD entire directory (from polymarket_claude)
├── golden-rules.md           (14 rules, transplant + expand)
├── calibration.json          (empty seed, Claude fills it)
├── strategies.md             (strategy lifecycle tracker)
├── edge-sources.md           (edge tracking)
└── market-types/             (category playbooks)
    ├── crypto.md
    ├── politics.md
    ├── sports.md
    ├── commodities.md
    ├── entertainment.md
    └── finance.md

scripts/                   ← ADD
├── heartbeat.py              (from polymarket_claude pattern)
└── run_cycle.sh              (ENHANCE existing — add heartbeat gating)

lib/                       ← KEEP all existing (working, tested)
├── market_intel.py           ← ADD (macro regime, news — from AI-Trader)
├── calibration.py            ← ADD (calibration tracking — from polymarket_claude)
└── (all other files unchanged)

tools/                     ← KEEP all existing (working, tested)
├── get_market_intel.py       ← ADD (CLI wrapper for market_intel.py)
└── record_outcome.py         ← ADD (calibration recording)

state/
├── strategy.md            ← REWRITE (minimal seed — Claude builds from here)
├── core-principles.md     ← SIMPLIFY (only true immutable guardrails)
└── (cycles/, reports/ — keep existing infrastructure)

.env                       ← MODIFY
  - Remove OPENAI_API_KEY (not needed — Claude IS the AI)
  - Add ALPHA_VANTAGE_API_KEY (for market intel)
  - Widen params: resolution 72h→14d, edge 10%→4pp, position $25→bankroll%

tests/                     ← KEEP all 167 passing tests
├── test_calibration.py       ← ADD
└── test_market_intel.py      ← ADD
```

### What's Different From a Traditional Bot

| Traditional Bot | This System |
|----------------|-------------|
| Python `if edge > 0.04: trade()` | Claude reasons: "Edge is 6pp but this category has been unreliable, I'll pass" |
| Hardcoded Kelly fraction = 0.25 | Claude decides: "I've been too conservative on crypto, moving to 1/3 Kelly based on calibration data" |
| Fixed resolution window filter | Claude thinks: "14-day markets are fine for sports but too long for crypto — I'll note this in my strategy" |
| Rules only change when dev deploys | Claude rewrites golden-rules.md after a loss: "Rule 15: Never trust single-poll data for elections" |
| Same analysis every cycle | Claude updates its analyst approach: "For commodities, I now check CME settlement vs intraday first" |
| Strategy frozen in code | Claude evolves strategy.md every cycle based on what worked and what didn't |

### The Self-Improvement Loop

```
┌─────────────────────────────────────────────────────┐
│                                                       │
│  1. Claude reads strategy.md + golden-rules.md        │
│     ↓                                                 │
│  2. Claude scans markets, analyzes with web search    │
│     ↓                                                 │
│  3. Claude decides trades using its own reasoning     │
│     ↓                                                 │
│  4. Claude executes via Python tools                  │
│     ↓                                                 │
│  5. Time passes... markets resolve                    │
│     ↓                                                 │
│  6. Claude checks outcomes, calculates P&L            │
│     ↓                                                 │
│  7. Claude analyzes: what went right? what went       │
│     wrong? was I overconfident? underconfident?        │
│     ↓                                                 │
│  8. Claude REWRITES its own files:                    │
│     - Adds/modifies rules in golden-rules.md          │
│     - Updates calibration.json with new data          │
│     - Edits category playbooks with new insights      │
│     - Evolves strategy.md with new approach           │
│     - May even edit CLAUDE.md to change its own       │
│       analysis process for next cycle                 │
│     ↓                                                 │
│  9. Next cycle: Claude reads updated files            │
│     → now it's a smarter trader than last cycle       │
│                                                       │
│  LOOP FOREVER                                         │
└─────────────────────────────────────────────────────┘
```

---

## What Claude Reads (Its Brain State)

These files ARE Claude's trading brain. Claude reads them at the start of every session and they shape every decision. Claude also writes to them — this is how it learns.

### CLAUDE.md — The Master Prompt

This is the most important file. It tells Claude WHO it is and HOW to operate. Unlike traditional bots, Claude can modify even this file to improve its own process.

```markdown
# Autonomous Polymarket Trader

You are an autonomous prediction market trader. You run continuously,
making real trading decisions on Polymarket. You learn from every trade
and evolve your strategy over time.

## How You Operate

Every session, you are triggered by cron. You read state/signal.json
to determine what action is needed:
- scan_needed → full trading cycle (scan, analyze, trade, learn)
- resolve_needed → check positions only (monitor, sell resolved, record outcomes)
- learn_needed → learning cycle only (analyze recent outcomes, update strategy)
- nothing needed → exit immediately (save cost)

## Your Trading Cycle

### Phase A: Check Positions
1. Read state/positions.json for all open positions
2. Run: python tools/check_resolved.py
3. For any resolved markets: sell, record outcome, write post-mortem
4. For positions with evaporated edge: consider selling
5. Update state/positions.json and state/bankroll.json

### Phase B: Find Opportunities
1. Run: python tools/discover_markets.py --limit 200
2. Filter through YOUR current rules in knowledge/golden-rules.md
3. Apply YOUR current strategy from state/strategy.md
4. Select top candidates for deep analysis

### Phase C: Analyze Markets
For each candidate:
1. Run: python tools/get_market_intel.py --category {cat}
2. Search the web for latest news (use web search tool, 2-3 queries)
3. Read knowledge/market-types/{category}.md for your learned base rates
4. Read knowledge/calibration.json for your accuracy history in this category
5. Think through Bull Case and Bear Case (argue both sides seriously)
6. Estimate fair probability. Be specific about your reasoning.
7. Calculate edge vs market price
8. Decide: TRADE or PASS. Write your reasoning.

### Phase D: Size and Execute
For each TRADE decision:
1. Run: python tools/calculate_kelly.py --prob {p} --price {price} --bankroll {b}
2. Apply your category caps and confidence adjustments
3. Check correlation with existing positions
4. Pre-execution: run python tools/get_prices.py to verify current price
5. If price moved >5% from analysis: re-evaluate or skip
6. Execute: python tools/execute_trade.py --market-id {id} --side {side} --size {usdc}

### Phase E: Learn and Evolve
After every cycle:
1. Write a cycle report to state/reports/cycle-{id}.md
2. If any positions resolved this cycle:
   a. Calculate Brier score (how accurate was your probability?)
   b. Update knowledge/calibration.json
   c. If loss: classify error type, add lesson to golden-rules.md
   d. If win: note what worked in knowledge/edge-sources.md
3. Review your strategy.md: does anything need updating?
4. Review your golden-rules.md: any new rules learned?
5. Review your market-types/ playbooks: any category insights?
6. Make 0-3 changes maximum per cycle (prevent drift)

## Your Python Tools

These are your hands. They fetch data, do math, and execute trades.
They contain NO decision logic — all decisions are yours.

| Tool | What It Does |
|------|-------------|
| discover_markets.py | Fetches active markets from Gamma API, returns JSON list |
| get_prices.py | Gets best bid/ask from CLOB API for a token |
| get_market_intel.py | Returns macro regime, news, sentiment for a category |
| calculate_kelly.py | Pure math: Kelly fraction given prob, price, bankroll |
| calculate_edge.py | Pure math: net edge after fees given prob, price, category |
| execute_trade.py | Places paper or live order, returns fill result |
| get_portfolio.py | Returns all open positions with current P&L |
| check_resolved.py | Checks which markets have resolved |
| sell_position.py | Closes or reduces a position |
| record_outcome.py | Records trade outcome to calibration database |
| enable_live.py | Live trading gate verification |

## Constraints (Read-Only — You Cannot Change These)

These live in state/core-principles.md. They are the ONLY rules you cannot modify.
Everything else — golden rules, strategy, playbooks — you own and evolve.

- Paper trading is default. Live requires gate pass.
- Never risk more than 5% of bankroll on a single trade.
- Never trade with money you can't afford to lose.
- Always record every trade in the database before confirming.
- Never delete your own cycle reports or calibration history.

## Everything Else: You Decide

Your edge thresholds, resolution windows, category preferences, Kelly fractions,
analysis approach, market selection criteria — these are ALL yours to set and
change based on what you learn. They live in files you control:

- state/strategy.md — your current trading strategy (you write this)
- knowledge/golden-rules.md — your rules (you add/modify these)
- knowledge/calibration.json — your accuracy data (you update this)
- knowledge/market-types/*.md — your category playbooks (you evolve these)
- knowledge/strategies.md — your strategy inventory (you track what works)
- knowledge/edge-sources.md — where your edge comes from (you maintain this)
```

### state/strategy.md — Claude's Self-Written Strategy

This file starts nearly empty. Claude fills it in as it trades and learns. No human writes this — it's Claude's own evolving playbook.

**Initial seed** (minimal — Claude builds from here):

```markdown
# My Trading Strategy

Last updated: {date} | Cycle: {id}
Total changes: 0 | Active rules: 0

## Market Selection
(I'll develop preferences as I trade and see what works)

## Analysis Approach
(I'll refine my process based on accuracy feedback)

## Risk Parameters
(Starting with defaults from core-principles.md, will adjust based on results)

## Trade Entry/Exit Rules
(Will emerge from experience)

## What I've Learned
(Empty — I haven't traded yet)

## Change Log
(Each change I make goes here with evidence and cycle_id)
```

After 20+ cycles, this might look like:

```markdown
# My Trading Strategy

Last updated: 2026-05-15 | Cycle: 20260515-143000
Total changes: 34 | Active rules: 18

## Market Selection
1. I focus on crypto and commodities — my calibration is best there (+5pp underconfident)
2. I avoid entertainment markets — my calibration is terrible (-24pp, only 1 trade but lesson learned)
3. Resolution window: 1-14 days sweet spot. <1 day = not enough analysis time. >14 days = too much uncertainty
4. Minimum volume: $5k for crypto, $3k for sports, $2k for commodities
5. I skip markets with ambiguous resolution criteria (learned from Rule 12)
6. NEW (cycle 20260514): I now actively scan for commodity settlement-gap markets — they've been my best edge source (3/4 wins)

## Analysis Approach
1. Always start from category base rate, then update with evidence
2. For crypto: check macro regime first (risk-on/off from QQQ/GLD)
3. For commodities: ALWAYS check settlement mechanics before estimating
4. For politics: apply status quo bias (70% base rate for "will X change" markets)
5. Web search: minimum 3 queries per market. One for facts, one for expert opinion, one for contrarian view
6. Market blend: for volume >$50k, weight market price 25%. For <$10k, only 5%.
7. CHANGED (cycle 20260510): I no longer trust single news sources for crypto. Need 2+ confirming sources.

## Risk Parameters
1. Default Kelly: 1/4 for high confidence, 1/6 for medium, 1/10 for low
2. CHANGED (cycle 20260508): For commodities with <3 days to resolution, I use 1/3 Kelly (my calibration is strong here)
3. Category caps: crypto 4%, politics 3%, sports 3%, commodities 4%, entertainment 2%
4. I reduce all sizes by 50% after 3 consecutive losses (resets after a win)
5. Max 2 correlated positions. Second one at half size.
6. NEW (cycle 20260512): I add 2pp to my edge requirement during high-volatility macro regimes (UUP moving >1%/day)

## Trade Entry/Exit Rules
1. Entry: net edge ≥ 4pp after fees (category-specific minimums may be higher)
2. Exit: edge dropped below 2pp, or resolution <6h with uncertain outcome
3. Stop loss: if position down >15pp from entry, sell immediately
4. NEW (cycle 20260514): For sports "large lead" markets, I hold through volatility — don't stop-loss on temporary dips

## What I've Learned
- Commodities are my strongest category. Settlement vs intraday is a real, repeatable edge.
- I'm systematically underconfident on crypto (my estimates too low by ~5pp). Should trust my analysis more.
- Entertainment/awards are my worst category. Small sample but -24pp error is serious. Staying away until I understand the dynamics better.
- Status quo bias in politics is real and profitable. 3/4 of my "NO on change" trades have won.
- Web search quality matters enormously. A single bad source led to my worst trade (Rule 7).

## Change Log
- Cycle 20260508: Increased commodity Kelly to 1/3 (evidence: 3 consecutive wins with accurate estimates)
- Cycle 20260510: Added 2-source requirement for crypto (evidence: loss from single-source misinformation)
- Cycle 20260512: Added volatility adjustment (evidence: 2 losses during macro regime shifts)
- Cycle 20260514: Added settlement-gap scanning (evidence: best edge source at 75% win rate)
- Cycle 20260514: Added sports "hold through volatility" (evidence: premature stop-loss cost $40 on Arsenal position)
```

### knowledge/golden-rules.md — Claude's Self-Written Rules

Claude adds rules here when it learns painful lessons. Each rule cites the specific trade that taught it. Claude can also modify or retire rules based on new evidence.

**Initial seed** (borrowed from polymarket_claude's battle-tested rules):

```markdown
# Golden Rules

Apply before every trade. Each rule exists because of a real loss or near-miss.
I add new rules when I learn painful lessons. I retire rules that no longer apply.

## Pre-Trade
1. **Check ALL outcomes in multi-option markets.** Don't miss dark horses.
   Taught by: polymarket_claude's Oscars loss (missed Bugonia at 2%, which won)

2. **Read resolution criteria, not the title.** "Will oil hit $100" = CME settlement, not intraday.
   Taught by: polymarket_claude's commodity discovery (intraday $119.94 vs settlement $94.65)

3. **Minimum 4pp net edge.** Below this, fees + model error eat the edge.
   Taught by: standard practice, supported by fee analysis

4. **Never bet at 97%+.** No edge even if correct. Catastrophic downside.
   Taught by: standard practice

## Sizing
5. **Fractional Kelly only.** Full Kelly is too volatile. Start at 1/4 max.
   Taught by: standard practice (Kelly ruin probability)

6. **Category size caps.** Different markets have different variance.
   Taught by: polymarket_claude's category analysis

## Research
7. **Status quo wins ~70% of "will X change" markets.**
   Taught by: polymarket_claude's political market analysis

8. **Cross-check high-volume markets on Metaculus/Manifold.**
   Taught by: standard practice

## Post-Trade
9. **Post-mortem every loss immediately.** Classify: information/model/calibration/resolution/black swan.
   Taught by: polymarket_claude's systematic loss analysis

10. **Record every outcome to calibration.** Win or lose.
    Taught by: standard practice

## (I will add more rules as I trade and learn)
```

### knowledge/calibration.json — Claude's Accuracy Tracker

Claude updates this after every trade resolution. It reads it before every analysis to adjust confidence.

```json
{
    "last_updated": "2026-04-02",
    "global": {
        "total_trades": 0,
        "wins": 0,
        "win_rate": null,
        "avg_brier": null,
        "consecutive_losses": 0
    },
    "categories": {}
}
```

After trading, Claude builds this up:
```json
{
    "last_updated": "2026-05-15",
    "global": {
        "total_trades": 28,
        "wins": 19,
        "win_rate": 0.679,
        "avg_brier": 0.152,
        "consecutive_losses": 0
    },
    "categories": {
        "crypto": {
            "trades": 12, "wins": 9, "win_rate": 0.75,
            "avg_stated_prob": 0.68, "avg_actual": 0.75,
            "error_pp": 7.0, "status": "UNDERCONFIDENT",
            "note": "I can be more aggressive here — my estimates are too conservative"
        },
        "commodities": {
            "trades": 8, "wins": 6, "win_rate": 0.75,
            "avg_stated_prob": 0.71, "avg_actual": 0.75,
            "error_pp": 4.0, "status": "WELL_CALIBRATED",
            "note": "Settlement-gap trades performing well"
        },
        "politics": {
            "trades": 5, "wins": 3, "win_rate": 0.60,
            "avg_stated_prob": 0.65, "avg_actual": 0.60,
            "error_pp": -5.0, "status": "SLIGHTLY_OVERCONFIDENT",
            "note": "Need better base rates for non-US politics"
        },
        "entertainment": {
            "trades": 1, "wins": 0, "win_rate": 0.0,
            "avg_stated_prob": 0.24, "avg_actual": 0.0,
            "error_pp": -24.0, "status": "OVERCONFIDENT",
            "note": "Avoiding until I have better models. Sample too small but error too large."
        }
    }
}
```

### knowledge/market-types/*.md — Claude's Category Playbooks

Claude builds domain expertise over time. These start with seeds from polymarket_claude and grow.

**Example: knowledge/market-types/crypto.md**

```markdown
# Crypto Trading Playbook

## What I Know (updated by me as I learn)

### Base Rates
- BTC hitting round number within 7 days from <5% away: ~45%
- BTC hitting round number within 7 days from >10% away: ~15%
- "Will X crypto regulation pass by date": status quo wins ~65%
- Halving cycle: 6-month post-halving historically bullish (but priced in by now)

### Edge Sources I've Found
1. **Macro regime mismatch**: Market prices crypto targets based on current momentum,
   but doesn't adjust for macro regime shifts. When QQQ rolls over, crypto targets 
   become overpriced. (Win rate: 4/5)
2. **Settlement mechanics**: Some markets resolve on specific exchange, specific time.
   Knowing which exchange and when matters. (Win rate: exploring)

### Resolution Mechanics
- "BTC hits $X" usually means: any major exchange, any time before deadline
- "BTC price at date" usually means: CoinGecko or specific exchange closing price
- ALWAYS check the resolution source in market description

### My Category-Specific Rules
- Check Fear & Greed Index before analyzing (extreme readings are contrarian signals)
- Macro regime is critical: risk-on vs risk-off changes everything
- Never trust single-source price predictions
- 24/7 markets mean news can break anytime — price my time-to-resolution carefully

### My Calibration Here
- Currently UNDERCONFIDENT by ~7pp — I can trust my crypto analysis more
- Strongest when: macro alignment + technical setup + <7 day resolution
- Weakest when: regulatory/political crypto markets (hard to predict government)
```

### knowledge/strategies.md — Claude's Strategy Inventory

Claude tracks which strategies are working, testing, or failing.

```markdown
# My Active Strategies

## PERFORMING (>55% win rate, ≥5 trades)
(none yet — will graduate strategies from TESTING as they prove out)

## TESTING (1-4 trades, monitoring)
(strategies Claude discovers and is validating)

## UNDERPERFORMING (<45% win rate over ≥5 trades)
(strategies Claude has tried that aren't working)

## RETIRED (conclusively failed or no longer applicable)
(strategies Claude has abandoned with reasons)

## Ideas to Explore
(market patterns Claude has noticed but not yet traded on)
```

### knowledge/edge-sources.md — Where Claude's Edge Comes From

```markdown
# My Edge Sources

Tracking WHERE my profits actually come from. This helps me focus
on what works and stop doing what doesn't.

## Confirmed (≥3 wins from this source)
(none yet)

## Testing (1-2 wins, need more data)
(Claude adds sources as it discovers them)

## Failed (tried, didn't work)
(Claude documents failures so it doesn't repeat them)

## Hypothesized (not yet traded)
- Settlement vs intraday gap (from polymarket_claude's research)
- Status quo bias in political markets
- Macro regime mismatch in crypto pricing
```

---

## What Claude Calls (Its Hands)

Python tools are minimal, stateless, and contain ZERO decision logic. They take parameters, do I/O or math, and return JSON. Claude decides everything.

### Tool Design Principle

```
WRONG: tool decides what to trade
  def discover_markets():
      markets = fetch()
      filtered = [m for m in markets if m.edge > 0.04]  # <-- decision in Python
      return filtered

RIGHT: tool returns data, Claude decides
  def discover_markets(limit, min_volume):
      markets = fetch(limit=limit, min_volume=min_volume)
      return markets  # <-- raw data, Claude filters based on its current strategy
```

### Tools List

#### discover_markets.py
```
Input:  --limit 200 --min-volume 1000
Output: JSON array of markets with: id, question, yes_price, no_price, 
        volume_24h, end_date, category, tokens, resolution_source
Does:   Fetches from Gamma API with pagination. Returns raw data.
        Claude decides which ones to analyze based on its strategy.
```

#### get_prices.py
```
Input:  --token-id 0x1234
Output: {"best_bid": 0.62, "best_ask": 0.64, "spread": 0.02, "midpoint": 0.63}
Does:   Queries CLOB API. Returns current orderbook top-of-book.
```

#### get_market_intel.py
```
Input:  --category crypto  (or: --overview)
Output: {"macro_regime": "risk-on", "fear_greed": 72, "top_news": [...], 
         "etf_flows": {...}, "signals": {...}}
Does:   Aggregates from Alpha Vantage, Fear & Greed API, ETF data.
        Claude interprets the signals based on its strategy.
```

#### calculate_kelly.py
```
Input:  --prob 0.65 --price 0.55 --bankroll 10000
Output: {"full_kelly": 0.118, "quarter_kelly": 0.029, "sixth_kelly": 0.020,
         "tenth_kelly": 0.012, "dollar_quarter": 295.00, "dollar_sixth": 196.00}
Does:   Pure math. Returns ALL Kelly fractions.
        Claude picks which fraction based on its confidence and strategy.
```

#### calculate_edge.py
```
Input:  --prob 0.65 --price 0.55 --category crypto
Output: {"gross_edge": 0.10, "fee_estimate": 0.012, "net_edge": 0.088,
         "fee_rate": 0.072, "fee_formula": "shares * price * 0.072 * (p*(1-p))^1"}
Does:   Pure math. Calculates edge and fees.
        Claude decides if edge is sufficient based on its current thresholds.
```

#### execute_trade.py
```
Input:  --market-id 0x1234 --token-id 0x5678 --side BUY --size-usdc 200
Output: {"status": "filled", "fill_price": 0.55, "shares": 363.6, 
         "fee": 2.45, "effective_price": 0.557, "order_id": "...", "is_paper": true}
Does:   Places order (paper or live based on config).
        Records to database. Returns result.
        Claude already decided to trade — this just executes.
```

#### get_portfolio.py
```
Input:  (no args)
Output: {"bankroll": 10000, "cash": 8500, "exposure": 1500,
         "positions": [{market_id, question, side, entry_price, current_price, 
                        pnl, days_to_resolution, edge_at_entry}],
         "total_pnl": 245.00, "win_rate": 0.68}
Does:   Reads database + fetches current prices. Returns current state.
```

#### check_resolved.py
```
Input:  (no args — checks all open positions)
Output: {"resolved": [{market_id, question, outcome, pnl}], 
         "still_open": [{market_id, question, days_remaining}]}
Does:   Queries Gamma API for each open position's resolution status.
```

#### sell_position.py
```
Input:  --market-id 0x1234 --reason "Market resolved YES"
Output: {"status": "sold", "sell_price": 0.98, "pnl": 15.40}
Does:   Sells/claims position. Records to database.
```

#### record_outcome.py
```
Input:  --market-id 0x1234 --stated-prob 0.65 --actual WIN --category crypto
Output: {"recorded": true, "brier_score": 0.122, "error_pp": -5.0}
Does:   Appends to calibration database. Returns accuracy metrics.
        Claude uses this to update knowledge/calibration.json.
```

#### enable_live.py
```
Input:  --check (or --enable, or --revoke)
Output: {"gate_status": "locked", "paper_cycles": 8, "required": 10,
         "total_pnl": 145.00, "win_rate": 0.68, "blocking_reasons": ["need 2 more cycles"]}
Does:   Checks/manages live trading gate.
        Claude can check readiness but must meet ALL criteria to enable.
```

---

## What Claude Cannot Change (Guardrails)

**state/core-principles.md** — the ONLY read-only file:

```markdown
# Core Principles (IMMUTABLE — Claude cannot modify this file)

1. Paper trading is default. Live requires passing the gate.
2. Maximum 5% of bankroll on any single position.
3. Live trading gate requires:
   - Minimum 10 completed paper trading cycles
   - Positive aggregate P&L on closed positions
   - Win rate > 50%
   - Manual "CONFIRM LIVE TRADING" typed by operator
4. Never delete cycle reports, calibration history, or trade records.
5. Always record trades in database BEFORE confirming execution.
6. If 5 consecutive losses: pause trading for 24 hours automatically.
7. Maximum 30% of bankroll in open positions at any time.
```

**Everything else — Claude owns and evolves:**
- strategy.md → Claude's trading approach
- golden-rules.md → Claude's learned rules
- calibration.json → Claude's accuracy data
- market-types/*.md → Claude's category expertise
- strategies.md → Claude's strategy inventory
- edge-sources.md → Claude's edge tracking
- CLAUDE.md → Claude can even modify its own master prompt

---

## How Claude Runs Autonomously

### Scheduling

```bash
# Heartbeat: every 10 minutes, pure Python, zero LLM cost
*/10 * * * * cd /home/trader/polymarket-trader && python scripts/heartbeat.py

# Trading cycle: every 30 minutes, but ONLY runs if heartbeat says needed
*/30 * * * * cd /home/trader/polymarket-trader && ./scripts/run_cycle.sh

# Daily deep cycle: force a full scan + learn at 2 AM UTC regardless of heartbeat
0 2 * * * cd /home/trader/polymarket-trader && FORCE_FULL=1 ./scripts/run_cycle.sh
```

### Heartbeat (scripts/heartbeat.py)

Cheap Python script that checks timestamps and writes signal flags. No LLM. No API calls to Polymarket. Just reads local files and writes signal.json.

```python
"""
Heartbeat — runs every 10 minutes via cron.
Reads local state files. Writes state/signal.json.
Decides IF Claude needs to wake up, but never WHAT Claude should do.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

WORKDIR = Path("/home/trader/polymarket-trader")
STATE = WORKDIR / "state"
SIGNAL_FILE = STATE / "signal.json"
POSITIONS_FILE = STATE / "positions.json"
REPORTS_DIR = STATE / "reports"

SCAN_STALENESS = timedelta(hours=2)
RESOLVE_STALENESS = timedelta(hours=1)
EXPIRY_WARNING = timedelta(hours=24)

def main():
    now = datetime.utcnow()
    
    # When was the last full scan?
    last_scan = get_last_cycle_time("scan")
    scan_needed = last_scan is None or (now - last_scan) > SCAN_STALENESS
    
    # Any positions needing resolution check?
    positions = load_json(POSITIONS_FILE, {"positions": []})["positions"]
    last_resolve = get_last_cycle_time("resolve")
    expiring = [p["question"] for p in positions 
                if parse_date(p.get("resolution_date")) 
                and parse_date(p["resolution_date"]) - now < EXPIRY_WARNING]
    resolve_needed = (
        len(positions) > 0 and 
        (last_resolve is None or (now - last_resolve) > RESOLVE_STALENESS or len(expiring) > 0)
    )
    
    # Any recent outcomes to learn from?
    learn_needed = check_unprocessed_outcomes()
    
    signal = {
        "generated_at": now.isoformat() + "Z",
        "scan_needed": scan_needed,
        "resolve_needed": resolve_needed,
        "learn_needed": learn_needed,
        "expiring_soon": expiring,
        "open_positions": len(positions),
    }
    
    with open(SIGNAL_FILE, "w") as f:
        json.dump(signal, f, indent=2)

if __name__ == "__main__":
    main()
```

### Cycle Runner (scripts/run_cycle.sh)

```bash
#!/bin/bash
set -euo pipefail

WORKDIR="/home/trader/polymarket-trader"
PIDFILE="$WORKDIR/.cycle.pid"
SIGNAL_FILE="$WORKDIR/state/signal.json"

# Prevent concurrent cycles
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    exit 0
fi
echo $$ > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT

# Check signals (skip if nothing needed, unless FORCE_FULL)
if [ "${FORCE_FULL:-0}" != "1" ] && [ -f "$SIGNAL_FILE" ]; then
    ANY_NEEDED=$(python3 -c "
import json
d = json.load(open('$SIGNAL_FILE'))
print(d.get('scan_needed') or d.get('resolve_needed') or d.get('learn_needed'))
")
    if [ "$ANY_NEEDED" = "False" ]; then
        exit 0
    fi
fi

CYCLE_ID=$(date +%Y%m%d-%H%M%S)
mkdir -p "$WORKDIR/state/cycles/$CYCLE_ID" "$WORKDIR/logs"

# Claude runs the cycle autonomously
# It reads signal.json to decide scope, reads its strategy files,
# makes all trading decisions, and updates its own knowledge
tmux new-session -d -s "cycle-$CYCLE_ID" \
    "cd $WORKDIR && claude --dangerously-skip-permissions \
     -p 'Trading cycle $CYCLE_ID. Read state/signal.json to determine scope. Execute your trading cycle per CLAUDE.md instructions.' \
     2>&1 | tee logs/cycle-$CYCLE_ID.log; \
     sleep 2"

# Wait for completion (max 20 minutes)
for i in $(seq 1 120); do
    if ! tmux has-session -t "cycle-$CYCLE_ID" 2>/dev/null; then
        break
    fi
    sleep 10
done

# Kill if still running
tmux kill-session -t "cycle-$CYCLE_ID" 2>/dev/null || true
```

### What Happens Each Cycle (Claude's Perspective)

Claude wakes up and sees:

```
Session start → reads CLAUDE.md → reads state/signal.json → decides what to do

If scan_needed:
  1. Claude reads its strategy.md: "I focus on crypto and commodities..."
  2. Claude reads golden-rules.md: "Check all outcomes, min 4pp edge..."
  3. Claude calls discover_markets.py → gets 150 markets
  4. Claude THINKS: "Based on my strategy, I want crypto <7 days and commodities with settlement gaps"
  5. Claude filters to 8 candidates using its own judgment
  6. For each, Claude calls get_market_intel.py, searches web, reasons through Bull/Bear
  7. Claude THINKS: "My calibration in crypto is +7pp underconfident, I can trust my estimates more"
  8. Claude decides: 3 trades approved, 5 passed
  9. Claude calls execute_trade.py for each approved trade
  10. Claude writes cycle report, updates calibration.json
  11. Claude THINKS: "I notice I keep passing on sports markets. Adding to strategy.md: explore sports next cycle"
  12. Claude edits strategy.md with new insight

If resolve_needed only:
  1. Claude calls check_resolved.py → 1 market resolved
  2. Claude calls sell_position.py → records P&L
  3. Claude THINKS: "I estimated 0.72, it resolved YES. Brier score 0.078 — good."
  4. Claude updates calibration.json
  5. Claude THINKS: "This is my 4th crypto win in a row. My edge source 'macro regime mismatch' is working."
  6. Claude updates edge-sources.md: moves source from TESTING to CONFIRMED

If learn_needed only:
  1. Claude reviews recent outcomes
  2. Claude THINKS: "I lost on the politics market. My error: I trusted a single poll."
  3. Claude adds golden-rules.md Rule 11: "Never trust single-poll data. Need 3+ polls or aggregator."
  4. Claude updates strategy.md: adds politics-specific note
```

---

## The Key Insight: Claude Modifies Its Own CLAUDE.md

This is what makes the system truly autonomous. Over time, Claude can realize that its own process is suboptimal and fix it:

```
Cycle 25: Claude notices it keeps running out of time analyzing 10 markets.
→ Claude edits CLAUDE.md Phase C: "Select top 5 candidates (not 10) — quality over quantity"

Cycle 40: Claude notices commodity trades are most profitable.
→ Claude edits CLAUDE.md Phase B: "Prioritize commodity settlement-gap scans. Run these first."

Cycle 60: Claude notices it's not catching market regime shifts fast enough.
→ Claude edits CLAUDE.md Phase C: "ALWAYS check macro regime before any analysis. If regime shifted since last cycle, re-evaluate all open positions."
```

This is the self-modifying agent loop. Claude's instructions ARE its strategy, and it evolves them based on evidence.

---

## Database Schema

The database is the immutable audit trail. Claude writes to it but never deletes from it.

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    cycle_id TEXT NOT NULL,
    market_id TEXT NOT NULL,
    token_id TEXT,
    question TEXT,
    category TEXT,
    side TEXT NOT NULL,
    action TEXT NOT NULL,
    price REAL NOT NULL,
    size_shares REAL NOT NULL,
    cost_usdc REAL NOT NULL,
    fill_price REAL,
    fee_amount REAL DEFAULT 0,
    order_id TEXT,
    status TEXT DEFAULT 'filled',
    is_paper INTEGER DEFAULT 1,
    estimated_prob REAL,
    edge REAL,
    confidence TEXT,
    reasoning TEXT
);

CREATE TABLE positions (
    market_id TEXT PRIMARY KEY,
    token_id TEXT,
    question TEXT,
    category TEXT,
    side TEXT NOT NULL,
    avg_price REAL NOT NULL,
    size_shares REAL NOT NULL,
    cost_basis REAL NOT NULL,
    current_price REAL,
    unrealized_pnl REAL DEFAULT 0,
    realized_pnl REAL DEFAULT 0,
    status TEXT DEFAULT 'open',
    opened_at TEXT,
    closed_at TEXT,
    resolution_date TEXT,
    stated_prob REAL,
    edge_at_entry REAL
);

CREATE TABLE calibration_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    market_id TEXT NOT NULL,
    category TEXT NOT NULL,
    stated_prob REAL NOT NULL,
    actual_outcome INTEGER NOT NULL,
    pnl REAL,
    brier_score REAL,
    error_classification TEXT,
    post_mortem TEXT
);

CREATE TABLE cycle_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id TEXT NOT NULL UNIQUE,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    scope TEXT NOT NULL,
    markets_scanned INTEGER DEFAULT 0,
    markets_analyzed INTEGER DEFAULT 0,
    trades_executed INTEGER DEFAULT 0,
    positions_closed INTEGER DEFAULT 0,
    realized_pnl REAL DEFAULT 0,
    strategy_changes INTEGER DEFAULT 0,
    duration_seconds INTEGER
);
```

---

## Python Library (lib/)

### Polymarket Integration

```python
# lib/market_data.py — Gamma API with proper pagination

GAMMA_API = "https://gamma-api.polymarket.com"

def fetch_markets(limit=200, min_volume=1000):
    """Fetch active markets from Gamma API with pagination."""
    all_markets = []
    offset = 0
    page_size = 100
    
    while len(all_markets) < limit:
        resp = requests.get(f"{GAMMA_API}/markets", params={
            "active": "true",
            "closed": "false",
            "order": "volume24hr",
            "ascending": "false",
            "limit": page_size,
            "offset": offset
        })
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        all_markets.extend(batch)
        offset += len(batch)
        if len(batch) < page_size:
            break
    
    # Parse stringified JSON fields (Gamma API quirk)
    parsed = []
    for m in all_markets:
        try:
            prices = json.loads(m.get("outcomePrices", "[]"))
            tokens = json.loads(m.get("clobTokenIds", "[]"))
            volume = float(m.get("volume24hr", 0) or m.get("volumeNum", 0) or 0)
            if volume < min_volume:
                continue
            parsed.append({
                "id": m["id"],
                "question": m["question"],
                "category": m.get("category", "other"),
                "yes_price": float(prices[0]) if len(prices) > 0 else None,
                "no_price": float(prices[1]) if len(prices) > 1 else None,
                "yes_token_id": tokens[0] if len(tokens) > 0 else None,
                "no_token_id": tokens[1] if len(tokens) > 1 else None,
                "volume_24h": volume,
                "end_date": m.get("endDate") or m.get("end_date_iso"),
                "description": m.get("description", ""),
                "resolution_source": m.get("resolutionSource", ""),
            })
        except (json.JSONDecodeError, ValueError, IndexError):
            continue
    
    return parsed[:limit]
```

```python
# lib/pricing.py — CLOB API pricing

CLOB_API = "https://clob.polymarket.com"

def get_book_price(token_id: str) -> dict:
    """Get best bid/ask from CLOB orderbook.
    
    CRITICAL: CLOB API semantics are inverted from taker perspective:
    - get_price(token, 'SELL') = best ASK = what a BUYER pays
    - get_price(token, 'BUY') = best BID = what a SELLER receives
    """
    try:
        # Use book endpoint for both sides
        resp = requests.get(f"{CLOB_API}/book", params={"token_id": token_id})
        resp.raise_for_status()
        book = resp.json()
        
        best_bid = float(book["bids"][0]["price"]) if book.get("bids") else None
        best_ask = float(book["asks"][0]["price"]) if book.get("asks") else None
        
        return {
            "token_id": token_id,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": round(best_ask - best_bid, 4) if best_bid and best_ask else None,
            "midpoint": round((best_bid + best_ask) / 2, 4) if best_bid and best_ask else None,
        }
    except Exception as e:
        return {"token_id": token_id, "error": str(e)}
```

```python
# lib/trading.py — Order execution (paper and live)

from py_clob_client.client import ClobClient
from py_clob_client.order_builder.constants import BUY, SELL

def execute_paper_trade(market_id, token_id, side, size_usdc, category, db):
    """Paper trade: simulate fill at current CLOB price."""
    book = get_book_price(token_id)
    
    if side == "BUY":
        fill_price = book["best_ask"]  # buyer pays the ask
    else:
        fill_price = book["best_bid"]  # seller receives the bid
    
    if fill_price is None:
        return {"status": "failed", "error": "No liquidity"}
    
    shares = size_usdc / fill_price
    fee = calculate_fee(shares, fill_price, category)
    effective_price = fill_price + (fee / shares) if side == "BUY" else fill_price - (fee / shares)
    
    trade = {
        "market_id": market_id,
        "token_id": token_id,
        "side": side,
        "action": "BUY" if side in ("YES", "BUY") else "SELL",
        "fill_price": fill_price,
        "shares": round(shares, 4),
        "cost_usdc": round(size_usdc, 2),
        "fee": round(fee, 4),
        "effective_price": round(effective_price, 6),
        "status": "filled",
        "is_paper": True
    }
    
    db.record_trade(trade)
    db.update_position(market_id, trade)
    return trade


def execute_live_trade(market_id, token_id, side, size_usdc, price, config, db):
    """Live trade via CLOB API. Requires .live-gate-pass."""
    if not os.path.exists(".live-gate-pass"):
        return {"status": "blocked", "error": "Live gate not passed"}
    
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=config.private_key,
        chain_id=137,
        signature_type=0  # EOA
    )
    
    # Derive API credentials (retry on 401)
    for attempt in range(3):
        try:
            creds = client.derive_api_key()
            client.set_api_creds(creds)
            break
        except Exception:
            if attempt == 2:
                raise
    
    shares = size_usdc / price
    order = client.create_and_post_order({
        "token_id": token_id,
        "price": price,
        "size": round(shares, 2),
        "side": BUY if side == "BUY" else SELL,
    })
    
    trade = {
        "market_id": market_id, "token_id": token_id,
        "side": side, "fill_price": price,
        "shares": round(shares, 4), "cost_usdc": round(size_usdc, 2),
        "order_id": order.get("id"), "status": order.get("status", "pending"),
        "is_paper": False
    }
    db.record_trade(trade)
    return trade
```

### Fee Calculation

```python
# lib/fees.py — Category-specific Polymarket fees

CATEGORY_FEES = {
    "crypto":        {"rate": 0.072, "exponent": 1},
    "sports":        {"rate": 0.030, "exponent": 1},
    "politics":      {"rate": 0.040, "exponent": 1},
    "finance":       {"rate": 0.040, "exponent": 1},
    "entertainment": {"rate": 0.250, "exponent": 2},
    "commodities":   {"rate": 0.040, "exponent": 1},
    "geopolitics":   {"rate": 0.000, "exponent": 1},
}

def calculate_fee(shares: float, price: float, category: str) -> float:
    params = CATEGORY_FEES.get(category, {"rate": 0.04, "exponent": 1})
    fee = shares * price * params["rate"] * (price * (1 - price)) ** params["exponent"]
    return round(fee, 4)
```

### Kelly Criterion

```python
# lib/strategy.py — Pure math, no decisions

def kelly_criterion(prob: float, price: float) -> float:
    """Full Kelly for binary Polymarket outcome."""
    if prob <= 0 or prob >= 1 or price <= 0 or price >= 1:
        return 0.0
    b = (1.0 - price) / price
    q = 1.0 - prob
    kelly = (b * prob - q) / b
    return max(0.0, kelly)

def kelly_all_fractions(prob: float, price: float, bankroll: float) -> dict:
    """Return all standard Kelly fractions for Claude to choose from."""
    full = kelly_criterion(prob, price)
    return {
        "full_kelly": round(full, 4),
        "quarter_kelly": round(full * 0.25, 4),
        "sixth_kelly": round(full * (1/6), 4),
        "tenth_kelly": round(full * 0.10, 4),
        "dollar_quarter": round(full * 0.25 * bankroll, 2),
        "dollar_sixth": round(full * (1/6) * bankroll, 2),
        "dollar_tenth": round(full * 0.10 * bankroll, 2),
    }
```

### Market Intelligence

```python
# lib/market_intel.py — Data enrichment for Claude's analysis

import requests
from datetime import datetime, timedelta

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
FEAR_GREED_URL = "https://api.alternative.me/fng/"
MACRO_SYMBOLS = {"growth": "QQQ", "defensive": "XLP", "safe_haven": "GLD", "dollar": "UUP"}

def get_macro_regime(api_key: str) -> dict:
    """Detect risk-on/risk-off regime from ETF performance."""
    signals = {}
    for label, symbol in MACRO_SYMBOLS.items():
        resp = requests.get(ALPHA_VANTAGE_URL, params={
            "function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key
        })
        data = resp.json().get("Global Quote", {})
        change_pct = float(data.get("10. change percent", "0").replace("%", ""))
        signals[label] = {"symbol": symbol, "change_pct": change_pct}
    
    # Simple regime classification
    growth = signals["growth"]["change_pct"]
    safe = signals["safe_haven"]["change_pct"]
    if growth > 0.5 and safe < 0:
        regime = "risk-on"
    elif growth < -0.5 and safe > 0:
        regime = "risk-off"
    else:
        regime = "mixed"
    
    return {"regime": regime, "signals": signals}

def get_crypto_fear_greed() -> dict:
    """Alternative.me Fear & Greed Index."""
    try:
        resp = requests.get(FEAR_GREED_URL, params={"limit": 1})
        data = resp.json()["data"][0]
        return {
            "value": int(data["value"]),
            "classification": data["value_classification"],
            "timestamp": data["timestamp"]
        }
    except Exception:
        return {"value": None, "error": "unavailable"}

def get_category_news(category: str, api_key: str, lookback_hours: int = 48) -> list:
    """Fetch recent news for a category from Alpha Vantage."""
    topic_map = {
        "crypto": "blockchain",
        "commodities": "energy_transportation",
        "finance": "economy_macro",
        "politics": "politics",
        "sports": "sports",
    }
    topic = topic_map.get(category, "financial_markets")
    time_from = (datetime.utcnow() - timedelta(hours=lookback_hours)).strftime("%Y%m%dT%H%M")
    
    resp = requests.get(ALPHA_VANTAGE_URL, params={
        "function": "NEWS_SENTIMENT",
        "topics": topic,
        "time_from": time_from,
        "limit": 10,
        "apikey": api_key
    })
    
    articles = resp.json().get("feed", [])
    return [{
        "title": a["title"],
        "summary": a.get("summary", ""),
        "source": a.get("source", ""),
        "sentiment": float(a.get("overall_sentiment_score", 0)),
        "published": a.get("time_published", "")
    } for a in articles[:10]]
```

---

## Dependencies

```
# requirements.txt — Minimal. Only what the tools need.
py-clob-client>=0.17.0        # Polymarket CLOB API
web3>=7.0.0                    # Polygon wallet operations
eth-account>=0.13.0            # Transaction signing
requests>=2.31.0               # HTTP (Gamma API, news, data)
python-dotenv>=1.0.0           # .env loading
```

No AI libraries. No LangChain. No OpenAI SDK. Claude Code IS the AI — it doesn't need a Python wrapper around another LLM.

---

## Implementation Phases

Starting from **polymarket-agent/** as base. Existing working code is kept — we add, modify, and restructure.

### Phase 1: Restructure .claude/ (Single Agent Design)
We start here because this defines HOW Claude operates.
```
1. Delete .claude/agents/ entirely (8 sub-agent files)
2. Create .claude/skills/ with 6 skill reference docs:
   - Transplant evaluate-edge.md, size-position.md, resolution-parser.md,
     calibration-check.md from polymarket_claude/.claude/skills/
   - Write new: post-mortem.md, cycle-review.md
3. REWRITE .claude/CLAUDE.md — single autonomous trader instructions
   - No sub-agent spawning, Claude does everything in one session
   - Reads its own knowledge base, makes all decisions, updates its own files
4. Verify .claude/settings.json allows: bash, file read/write/edit, web search
```

### Phase 2: Transplant Knowledge Base
```
1. Create knowledge/ directory in polymarket-agent/
2. Transplant from polymarket_claude/knowledge/:
   - golden-rules.md (14 rules — adapt format, keep citations)
   - market-types/*.md (5 category playbooks)
   - strategies.md (strategy lifecycle framework)
   - edge-sources.md (edge tracking template)
3. Create knowledge/calibration.json (empty seed — Claude fills it)
4. Create knowledge/market-types/finance.md (new — not in source)
5. Rewrite state/strategy.md (minimal seed — Claude builds from here)
6. Simplify state/core-principles.md (only true immutable guardrails)
```

### Phase 3: Add Missing Python Tools
Existing tools are kept as-is (11 working tools). We add:
```
1. lib/market_intel.py — macro regime, news, sentiment (from AI-Trader patterns)
2. lib/calibration.py — calibration tracking + corrections (from polymarket_claude)
3. tools/get_market_intel.py — CLI wrapper for market_intel.py
4. tools/record_outcome.py — calibration recording after trade resolution
5. scripts/heartbeat.py — lightweight signal generator (from polymarket_claude)
6. Enhance scripts/run_cycle.sh — add heartbeat gating (skip if no signals)
7. Write tests: test_calibration.py, test_market_intel.py
8. Verify all 167 existing tests still pass
```

### Phase 4: Config Changes
```
1. .env modifications:
   - Remove OPENAI_API_KEY (Claude IS the AI)
   - Add ALPHA_VANTAGE_API_KEY (market intel)
   - Widen: MAX_RESOLUTION_DAYS=14 (was 3)
   - Widen: MIN_EDGE_THRESHOLD=0.04 (was 0.10)
   - Widen: MAX_POSITION_SIZE based on bankroll % (was fixed $25)
   - Widen: MAX_TOTAL_EXPOSURE based on bankroll % (was fixed $200)
2. lib/config.py — add new config fields, keep backward compatibility
```

### Phase 5: First Autonomous Cycle (Manual Validation)
```
1. Run: claude -p "Run your first trading cycle"
2. Watch Claude:
   - Does it read its knowledge base?
   - Does it use skills when analyzing markets?
   - Does it make reasonable decisions?
   - Does it write a cycle report?
   - Does it update its own strategy.md?
3. Fix tool bugs or CLAUDE.md issues found
4. Repeat 5-10 times manually
5. Key validation: Claude should be making DIFFERENT decisions than a hardcoded bot
   (e.g., "I'm passing on this 5pp edge because my calibration in this category is bad")
```

### Phase 6: Automate Scheduling
```
1. Deploy heartbeat.py to cron (every 10 minutes)
2. Deploy run_cycle.sh to cron (every 30 minutes, gated by heartbeat)
3. Add daily forced full cycle at 2 AM UTC
4. Let Claude run unattended for 2-3 days
5. Monitor:
   - Are cycle reports being written? (state/reports/)
   - Is strategy.md growing? (Claude adding learned rules)
   - Is calibration.json being updated? (tracking accuracy)
   - Is golden-rules.md expanding? (new rules from losses)
6. Intervention only if Claude is stuck or tools are failing
```

### Phase 7: Paper Trading Validation (2-4 weeks)
```
1. Let it run 20-50+ cycles autonomously
2. Track evolution:
   - Is calibration improving? (error_pp trending toward 0)
   - Are golden rules growing? (new rules from real experiences)
   - Is strategy.md getting smarter? (more nuanced, evidence-backed)
   - Is edge-sources.md showing confirmed sources?
3. Key metric: Is paper P&L trending positive?
4. Review: Has Claude made any surprising/clever strategy changes?
   (This is the test — a bot can't do this, but Claude can)
```

### Phase 8: Live Money
```
1. Claude runs: python tools/enable_live.py --check
2. Gate criteria:
   - ≥10 completed paper cycles with positive P&L
   - Win rate > 50%
   - Calibration healthy (no category > -20pp error)
3. If all met: operator types "CONFIRM LIVE TRADING"
4. Start with $100-500 bankroll
5. Claude continues same loop — now with real money feedback
6. Scale up bankroll as track record proves out
7. Claude's strategy evolves differently with real stakes
   (losses hurt more → rules tighten → better risk management)
```

---

## Why This Design Wins

1. **Claude IS the intelligence.** No GPT-4o, no LangChain, no hardcoded Python rules. Claude's reasoning power drives every decision.

2. **Self-modifying strategy.** Claude writes and rewrites its own rules, playbooks, and process. It literally gets smarter every cycle.

3. **Claude can fix its own bugs.** If Claude notices its analysis process is flawed, it edits CLAUDE.md to improve it. No human deployment needed.

4. **Minimal code surface.** ~1000 lines of Python tools. Everything else is markdown files that Claude reads and writes. Less code = fewer bugs.

5. **The knowledge compounds forever.** Golden rules grow. Calibration gets more accurate. Category playbooks deepen. Edge sources get tracked. Every cycle adds intelligence.

6. **Truly autonomous.** Heartbeat + cron + Claude Code = runs 24/7 with zero human intervention. Self-scheduling, self-analyzing, self-improving.

7. **Safe by design.** Core principles are immutable. Paper mode is default. Live gate requires proof of competence. But within those guardrails, Claude has complete freedom to evolve its approach.
