# Live Trading

Live trading is disabled by default. Multiple safety gates prevent accidental activation.

## Prerequisites

1. Successful paper trading track record (20+ cycles recommended)
2. Funded Polygon wallet with MATIC (gas) and USDC (trading capital)
3. All 4 gate criteria passing

## Step 1: Set Up Wallet

```bash
python setup_wallet.py
```

This generates (or imports) an Ethereum wallet, derives L2 API credentials for Polymarket's CLOB, and sets token allowances on Polygon. You need:

- MATIC on Polygon for gas fees
- USDC on Polygon for trading capital

After setup, add to `.env`:
```
PRIVATE_KEY=your_ethereum_private_key
```

## Step 2: Check Gate Criteria

```bash
# Read-only check -- outputs JSON to stdout, human summary to stderr
python tools/enable_live.py --check
```

Four criteria must all pass:

| Criterion | Requirement | Why |
|-----------|-------------|-----|
| Cycles | >= 10 paper cycles | Enough data to evaluate performance |
| P&L | Aggregate > $0 | System must be profitable on paper |
| Win rate | > 50% | More wins than losses |
| Calibration | No category bias > -20pp | Probability estimates are not severely overconfident |

```
==================================================
LIVE TRADING GATE CHECK
==================================================
  [PASS] Paper cycles >= 10: 23
  [PASS] Aggregate P&L positive: 18.11
  [PASS] Win rate above 50%: 0.6250
  [FAIL] No category calibration bias > -20pp: -22.5
==================================================
  Result: GATE BLOCKED
==================================================
```

`--check` is read-only -- it does not write a gate pass file even if all criteria pass.

## Step 3: Enable Live Trading

```bash
# Interactive -- requires typing "CONFIRM LIVE"
python tools/enable_live.py
```

If all 4 criteria pass and you confirm, this creates `.live-gate-pass`. Then set in `.env`:

```
PAPER_TRADING=false
```

## Revoking

```bash
python tools/enable_live.py --revoke    # Delete gate pass
python tools/enable_live.py --status    # Check current state
```

## Safety Guardrails

These apply to both paper and live trading:

| Rule | Enforcement |
|------|-------------|
| Max 5% of bankroll per position | `lib/strategy.py` + core principles |
| Max 30% total exposure | `lib/portfolio.py` risk check |
| Record trade in DB before confirming | `lib/trading.py` execution flow |
| 5 consecutive losses = 24h pause | Cycle logic in `.claude/CLAUDE.md` |
| Min $5 order size | `lib/trading.py:validate_order()` |
| Price must be 0-1 range | Order validation |
| CLOB credentials auto-refresh on 401 | `lib/trading.py` retry logic |
| PID lockfile prevents overlapping cycles | `scripts/run_cycle.sh` |
| Each sub-agent has maxTurns limit | Agent definitions in `.claude/agents/` |

## Live vs Paper Differences

| Aspect | Paper | Live |
|--------|-------|------|
| Order execution | Simulated fill at orderbook price | Signed limit order via py-clob-client |
| Fill price | Best ask (buy) / best bid (sell) | Your limit price |
| Wallet | Not required | PRIVATE_KEY in .env |
| Gate pass | Not required | Required (.live-gate-pass) |
| P&L | Tracked in SQLite | Real USDC on Polygon |
| Fees | Estimated via `lib/fees.py` | Actual CLOB fees |
