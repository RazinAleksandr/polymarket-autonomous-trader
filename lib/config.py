import json
import os
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_BANKROLL_PATH = Path(__file__).resolve().parent.parent / "state" / "bankroll.json"
_DEFAULT_BANKROLL = 10000.0


@dataclass
class Config:
    paper_trading: bool = True
    min_volume_24h: float = 1000.0
    min_liquidity: float = 500.0
    max_markets_per_cycle: int = 10
    min_edge_threshold: float = 0.04
    kelly_fraction: float = 0.25
    max_position_pct: float = 0.05
    max_exposure_pct: float = 0.30
    max_resolution_days: int = 14
    db_path: str = "trading.db"
    log_level: str = "INFO"
    log_file: str = "trading.log"
    polymarket_host: str = "https://clob.polymarket.com"
    gamma_api_url: str = "https://gamma-api.polymarket.com"
    chain_id: int = 137
    private_key: str = ""
    cycle_interval: str = "4h"
    min_paper_cycles: int = 10


# Mapping from env var names to Config field names
_ENV_MAP = {
    "PAPER_TRADING": "paper_trading",
    "MIN_VOLUME_24H": "min_volume_24h",
    "MIN_LIQUIDITY": "min_liquidity",
    "MAX_MARKETS_PER_CYCLE": "max_markets_per_cycle",
    "MIN_EDGE_THRESHOLD": "min_edge_threshold",
    "KELLY_FRACTION": "kelly_fraction",
    "MAX_POSITION_PCT": "max_position_pct",
    "MAX_EXPOSURE_PCT": "max_exposure_pct",
    "MAX_RESOLUTION_DAYS": "max_resolution_days",
    "DB_PATH": "db_path",
    "LOG_LEVEL": "log_level",
    "LOG_FILE": "log_file",
    "POLYMARKET_HOST": "polymarket_host",
    "GAMMA_API_URL": "gamma_api_url",
    "CHAIN_ID": "chain_id",
    "PRIVATE_KEY": "private_key",
    "CYCLE_INTERVAL": "cycle_interval",
    "MIN_PAPER_CYCLES": "min_paper_cycles",
}


def _parse_value(field_type: type, raw: str):
    """Parse a string value into the correct type for a Config field."""
    if field_type is bool:
        return raw.lower() == "true"
    elif field_type is int:
        return int(raw)
    elif field_type is float:
        return float(raw)
    return raw


def load_config(args=None) -> Config:
    """Load configuration from .env, then override with CLI args if provided.

    Priority: CLI args > .env values > dataclass defaults
    """
    config = Config()

    # Build a lookup of field name -> field type
    field_types = {f.name: f.type for f in fields(Config)}

    # Override from environment variables
    for env_name, field_name in _ENV_MAP.items():
        env_val = os.getenv(env_name)
        if env_val is not None:
            parsed = _parse_value(field_types[field_name], env_val)
            setattr(config, field_name, parsed)

    # Override from CLI args (argparse Namespace)
    if args is not None:
        for attr_name, attr_val in vars(args).items():
            if attr_val is not None and attr_name in field_types:
                setattr(config, attr_name, attr_val)

    return config


def load_bankroll(path: Path | None = None) -> dict:
    """Load bankroll from state/bankroll.json. Returns safe default if missing/corrupt."""
    bp = path or _BANKROLL_PATH
    try:
        with open(bp) as f:
            data = json.load(f)
        balance = float(data["balance_usdc"])
        return {"balance_usdc": balance, "updated": data.get("updated", "")}
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError):
        return {"balance_usdc": _DEFAULT_BANKROLL, "updated": datetime.now(timezone.utc).isoformat()}
