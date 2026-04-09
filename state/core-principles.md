# Core Principles

These principles are set by the human operator and are immutable. The agent reads this file at cycle start but NEVER modifies it. Any attempt to write to this file must hard-fail.

***

## Reality Check

85-90% of retail accounts on Polymarket end with net losses. The top 0.04% of wallets capture 70%+ of all profits. This agent exists to be in the other 10-15%. Every guardrail below serves that single goal.

***

## Immutable Guardrails

### 1. Paper Trading Default

Execution mode is PAPER until the operator explicitly enables live trading via `python tools/enable_live.py --activate`. Live trading requires passing all gate criteria. Claude NEVER switches to live mode on its own.

### 2. Maximum 5% Position Size

No single position may exceed 5% of current bankroll. Bankroll is read from `state/bankroll.json` at cycle start. If bankroll.json is missing, assume $10,000 default. This is a HARD cap -- never override upward regardless of confidence or edge.

### 3. Maximum 30% Total Exposure

Total open position exposure (sum of all position costs) must not exceed 30% of current bankroll. If adding a new position would breach this limit, skip the trade. Check exposure BEFORE every trade execution.

### 4. Live Trading Gate

Live trading requires ALL of: (a) 10+ completed paper trading cycles, (b) positive cumulative P&L, (c) win rate above 50%, (d) explicit operator confirmation via enable_live.py. If ANY criterion fails, remain in paper mode.

### 5. No Deletion of Audit Trail

Cycle reports in `state/reports/`, calibration history in `knowledge/calibration.json`, and trade records in `trading.db` must NEVER be deleted. Append only. If a file is corrupted, create a new file with a timestamp suffix -- do not overwrite the original.

### 6. Record Before Confirm

Every trade must be recorded in the database (via execute_trade.py) BEFORE the agent considers it confirmed. If the recording fails, the trade did not happen. Never report a trade as executed without a database record.

### 7. Five-Loss Trading Pause

After 5 consecutive losing trades (resolved positions with negative P&L), the agent must pause all new trade execution for 24 hours. During the pause: continue scanning, analyzing, and writing reports -- but execute zero trades. Log the pause in the cycle report. Resume after 24 hours from the 5th loss resolution timestamp.

***

## Sizing Reference

| Parameter | Value |
|-----------|-------|
| Max single position | 5% of bankroll |
| Max total exposure | 30% of bankroll |
| Kelly fraction | 0.25 (quarter-Kelly) |
| Min edge (default) | 0.04 (4pp) |
| Price sweet spot | YES price 0.15 - 0.85 |

Position sizes are calculated as bankroll percentages. The actual dollar amount is derived from state/bankroll.json at runtime.

***

## Category Size Caps

| Category | Max Per Bet | Min Edge | Notes |
|----------|-------------|----------|-------|
| Crypto | 3% bankroll | 5pp | High variance, high correlation |
| Politics | 3% bankroll | 4pp | Status quo bias applies |
| Sports | 2% bankroll | 4pp | Single games only; 3% for season-long |
| Commodities | 4% bankroll | 4pp | Settlement != intraday |
| Entertainment | 2% bankroll | 8pp | Calibration probation (Oscars loss) |
| Finance | 3% bankroll | 4pp | Near-certainty events have no edge |

***

## Execution Realism (Paper Mode)

Paper fills must use the order book: BUY at best_ask, SELL at best_bid. Quantize to tick_size. If the book is stale (>10s old), skip. No fills at mid-price. Apply actual CLOB fee schedules. Fees changed 2026-03-30 -- use current schedule.

***

## File Discipline

- NEVER modify: `.env`, `trading.db` (directly), `lib/config.py`, `state/core-principles.md`
- Cycle outputs go to `state/cycles/{cycle_id}/`
- Cycle reports go to `state/reports/cycle-{cycle_id}.md`
- All intermediate files kept for audit trail
