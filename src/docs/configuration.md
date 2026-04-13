# Configuration

All parameters are loaded from `.env` via `python-dotenv` into `lib/config.py`. CLI arguments override `.env` values.

## Setup

```bash
cp .env.example .env
# Edit .env -- no API keys needed for paper trading with defaults
```

## Parameters

### Trading

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `PAPER_TRADING` | bool | `true` | Paper mode. Set `false` only with live gate pass. |
| `MIN_EDGE_THRESHOLD` | float | `0.04` | Minimum edge (4pp) to consider a trade |
| `KELLY_FRACTION` | float | `0.25` | Quarter-Kelly for conservative sizing |
| `MAX_POSITION_PCT` | float | `0.05` | Max single position as % of bankroll (hard cap) |
| `MAX_EXPOSURE_PCT` | float | `0.30` | Max total open exposure as % of bankroll (hard cap) |
| `MAX_RESOLUTION_DAYS` | int | `14` | Exclude markets resolving beyond this many days |

### Market Discovery

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `MIN_VOLUME_24H` | float | `1000` | Min 24h volume in USDC |
| `MIN_LIQUIDITY` | float | `500` | Min orderbook depth in USDC |
| `MAX_MARKETS_PER_CYCLE` | int | `10` | Max markets returned per discovery call |

### Infrastructure

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `POLYMARKET_HOST` | str | `https://clob.polymarket.com` | CLOB API endpoint |
| `GAMMA_API_URL` | str | `https://gamma-api.polymarket.com` | Market metadata API |
| `CHAIN_ID` | int | `137` | Polygon mainnet |
| `DB_PATH` | str | `trading.db` | SQLite database location |
| `LOG_LEVEL` | str | `INFO` | DEBUG, INFO, WARNING, ERROR |
| `LOG_FILE` | str | `trading.log` | Structured JSON log output |
| `CYCLE_INTERVAL` | str | `4h` | Cron interval (used by setup_schedule.py) |
| `MIN_PAPER_CYCLES` | int | `10` | Required paper cycles before live gate opens |

### Secrets

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `PRIVATE_KEY` | str | (empty) | Ethereum private key. Required for live trading only. **Never commit.** |
| `ALPHA_VANTAGE_API_KEY` | str | (empty) | Market intelligence API key (optional) |

## Bankroll

Trading capital is tracked in `state/bankroll.json`:

```json
{
  "balance_usdc": 10000.0,
  "updated": "2026-04-05T18:30:00Z"
}
```

Default is $10,000 USDC if the file doesn't exist. Position sizes and exposure limits are calculated as percentages of this value.

## Config Loading Priority

1. CLI arguments (highest)
2. `.env` file values
3. `Config` dataclass defaults (lowest)

```python
from lib.config import load_config

config = load_config()           # From .env + defaults
config = load_config(args=args)  # CLI args override .env
```
