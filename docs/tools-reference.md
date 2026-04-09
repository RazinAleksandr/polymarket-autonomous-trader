# Tools Reference

All tools live in `tools/` and output JSON to stdout. Add `--pretty` for human-readable formatting.

Activate the virtualenv first: `source .venv/bin/activate`

## Market Discovery

### discover_markets.py

Find active, tradable markets from Polymarket's Gamma API.

```bash
python tools/discover_markets.py --pretty
python tools/discover_markets.py --min-volume 5000 --min-liquidity 1000 --limit 5 --pretty
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--min-volume` | float | 1000 | Min 24h volume in USDC |
| `--min-liquidity` | float | 500 | Min orderbook depth |
| `--limit` | int | 10 | Max markets returned |
| `--pretty` | flag | | Human-readable output |

### get_prices.py

Get orderbook bid/ask/spread for a CLOB token.

```bash
python tools/get_prices.py --token-id <CLOB_TOKEN_ID> --pretty
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--token-id` | str | yes | CLOB token ID |
| `--pretty` | flag | | Human-readable output |

### get_market_intel.py

Market intelligence: macro regime (ETF SMAs), crypto Fear & Greed, category news.

```bash
python tools/get_market_intel.py --overview --pretty
python tools/get_market_intel.py --category politics --pretty
```

| Flag | Type | Description |
|------|------|-------------|
| `--overview` | flag | Macro overview (mutually exclusive with --category) |
| `--category` | str | One of: crypto, politics, sports, commodities, entertainment, finance |
| `--pretty` | flag | Human-readable output |

## Edge & Sizing

### calculate_edge.py

Calculate edge between your probability estimate and market price.

```bash
python tools/calculate_edge.py --estimated-prob 0.70 --market-price 0.55 --pretty
```

Returns: edge value, edge percentage, direction (BUY_YES, BUY_NO, or NO_EDGE).

### calculate_kelly.py

Kelly criterion position sizing.

```bash
python tools/calculate_kelly.py --estimated-prob 0.70 --market-price 0.55 --bankroll 200 --pretty
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--estimated-prob` | float | required | Your probability estimate |
| `--market-price` | float | required | Current market price |
| `--bankroll` | float | from config | Available capital |
| `--kelly-fraction` | float | 0.25 | Kelly fraction (quarter-Kelly default) |
| `--max-position` | float | from config | Max position cap |
| `--pretty` | flag | | Human-readable output |

## Trade Execution

### execute_trade.py

Execute a paper or live trade.

```bash
# Paper trade
python tools/execute_trade.py \
  --market-id <ID> --token-id <TOKEN> --side YES --size 10 --pretty

# Live trade (requires gate pass + PAPER_TRADING=false)
python tools/execute_trade.py \
  --market-id <ID> --token-id <TOKEN> --side YES --size 10 \
  --price 0.55 --live --pretty
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--market-id` | str | yes | Polymarket market ID |
| `--token-id` | str | yes | CLOB token ID |
| `--side` | YES/NO | yes | Trade direction |
| `--size` | float | yes | Position size in USDC |
| `--price` | float | live only | Limit order price |
| `--estimated-prob` | float | | Your probability estimate |
| `--edge` | float | | Calculated edge |
| `--reasoning` | str | | Trade rationale |
| `--category` | str | | Market category |
| `--neg-risk` | flag | | Neg-risk market flag |
| `--live` | flag | | Execute as live trade |
| `--pretty` | flag | | Human-readable output |

### sell_position.py

Close or reduce an existing position.

```bash
python tools/sell_position.py \
  --market-id <ID> --token-id <TOKEN> --side YES --size 10 --pretty
```

Same flags as execute_trade.py minus `--estimated-prob`, `--edge`, `--neg-risk`. Validates that held size >= sell size.

## Portfolio

### get_portfolio.py

View open positions and P&L.

```bash
python tools/get_portfolio.py --pretty
python tools/get_portfolio.py --include-risk --pretty
```

| Flag | Description |
|------|-------------|
| `--pretty` | Human-readable output |
| `--include-risk` | Include risk limit warnings |

### check_resolved.py

Detect resolved markets and finalize P&L.

```bash
python tools/check_resolved.py --pretty
```

## Calibration

### record_outcome.py

Record a trade outcome for calibration tracking.

```bash
python tools/record_outcome.py \
  --market-id <ID> --stated-prob 0.75 --actual WIN \
  --category politics --pnl 12.50 --pretty
```

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--market-id` | str | yes | Market ID |
| `--stated-prob` | float | yes | Your probability estimate at entry |
| `--actual` | WIN/LOSS | yes | Outcome |
| `--category` | str | yes | crypto/politics/sports/commodities/entertainment/finance |
| `--pnl` | float | | Realized P&L |
| `--notes` | str | | Additional notes |
| `--pretty` | flag | | Human-readable output |

Computes Brier score and error in percentage points. Regenerates `knowledge/calibration.json`.

## Validation & Gate

### validate_cycle.py

Validate cycle reports and generate cumulative summary.

```bash
python tools/validate_cycle.py --summary --pretty          # Aggregate stats
python tools/validate_cycle.py --cycle-id 20260405-183118   # Validate one cycle
```

### enable_live.py

Live trading gate with 4 criteria.

```bash
python tools/enable_live.py --check     # Read-only: check all 4 criteria (JSON + human summary)
python tools/enable_live.py --status    # Current gate state
python tools/enable_live.py             # Interactive: enable live trading (requires confirmation)
python tools/enable_live.py --revoke    # Revoke live trading gate pass
```

Gate criteria (all must pass):
1. Paper cycles >= 10 (configurable via `MIN_PAPER_CYCLES`)
2. Aggregate P&L > 0
3. Win rate > 50%
4. Calibration health: no category bias > -20pp

`--check` outputs JSON to stdout and human summary to stderr. Does not write `.live-gate-pass`.
