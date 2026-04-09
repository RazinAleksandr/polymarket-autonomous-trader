"""Market intelligence library for macro regime, Fear & Greed, and news sentiment.

Provides environmental context Claude needs before analyzing individual markets:
- Macro regime detection via ETF SMA comparison (risk-on, risk-off, mixed)
- Crypto Fear & Greed index from alternative.me
- Category news sentiment from Alpha Vantage NEWS_SENTIMENT

All API failures degrade gracefully with partial results and warnings (D-04).
"""

import os
import requests
from datetime import datetime, timezone
from lib.logging_setup import get_logger

log = get_logger("market_intel")

ETFS = {
    "QQQ": "tech/growth",
    "XLP": "consumer staples",
    "GLD": "gold/safe haven",
    "UUP": "dollar strength",
}

CATEGORIES = ["crypto", "politics", "sports", "commodities", "entertainment", "finance"]

ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"
FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1"

# Map categories to Alpha Vantage NEWS_SENTIMENT topics
_CATEGORY_TOPIC_MAP = {
    "crypto": "BLOCKCHAIN",
    "politics": "POLITICS",
    "sports": "SPORTS",
    "commodities": "ENERGY_TRANSPORTATION",
    "entertainment": "ENTERTAINMENT",
    "finance": "FINANCE",
}


def _fetch_etf_sma(symbol: str, api_key: str, period: int = 20) -> dict | None:
    """Fetch ETF daily prices and compute simple moving average.

    Args:
        symbol: ETF ticker symbol (e.g. QQQ, GLD).
        api_key: Alpha Vantage API key.
        period: Number of days for SMA calculation.

    Returns:
        Dict with symbol, current price, SMA, and above_sma flag.
        None on any failure.
    """
    try:
        resp = requests.get(
            ALPHA_VANTAGE_BASE,
            params={
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": "compact",
                "apikey": api_key,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        time_series = data.get("Time Series (Daily)", {})
        if not time_series:
            log.error(f"No time series data for {symbol}")
            return None

        # Sort dates descending to get most recent first
        sorted_dates = sorted(time_series.keys(), reverse=True)
        if len(sorted_dates) < period:
            log.error(f"Insufficient data for {symbol}: {len(sorted_dates)} days, need {period}")
            return None

        closes = [float(time_series[d]["4. close"]) for d in sorted_dates[:period]]
        current_price = closes[0]
        sma = sum(closes) / len(closes)

        return {
            "symbol": symbol,
            "current": current_price,
            "sma_20": round(sma, 4),
            "above_sma": current_price > sma,
        }
    except Exception as e:
        log.error(f"Failed to fetch ETF SMA for {symbol}: {e}")
        return None


def get_macro_regime(api_key: str | None = None) -> dict:
    """Detect macro regime from ETF SMA comparison.

    Classification (per D-05):
    - risk-on: QQQ above SMA, GLD below SMA (growth outperforming safety)
    - risk-off: QQQ below SMA, GLD above SMA (safety outperforming growth)
    - mixed: contradictory signals

    Args:
        api_key: Alpha Vantage API key. Falls back to ALPHA_VANTAGE_API_KEY env var.

    Returns:
        Dict with regime, etfs data, signals list, and warnings list.
    """
    if api_key is None:
        api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return {
            "regime": None,
            "etfs": {},
            "signals": [],
            "warnings": ["ALPHA_VANTAGE_API_KEY not set"],
        }

    etfs = {}
    warnings = []
    for symbol in ETFS:
        result = _fetch_etf_sma(symbol, api_key)
        if result:
            etfs[symbol] = {
                "current": result["current"],
                "sma_20": result["sma_20"],
                "above_sma": result["above_sma"],
            }
        else:
            warnings.append(f"Alpha Vantage API error for {symbol}")

    if not etfs:
        return {
            "regime": None,
            "etfs": {},
            "signals": [],
            "warnings": warnings,
        }

    # Count risk signals
    risk_on_signals = []
    risk_off_signals = []

    if "QQQ" in etfs:
        if etfs["QQQ"]["above_sma"]:
            risk_on_signals.append("QQQ above 20d SMA (bullish)")
        else:
            risk_off_signals.append("QQQ below 20d SMA (bearish)")

    if "GLD" in etfs:
        if etfs["GLD"]["above_sma"]:
            risk_off_signals.append("GLD above 20d SMA (safety demand)")
        else:
            risk_on_signals.append("GLD below 20d SMA (risk-on)")

    if "XLP" in etfs:
        if etfs["XLP"]["above_sma"]:
            risk_off_signals.append("XLP above 20d SMA (defensive)")
        else:
            risk_on_signals.append("XLP below 20d SMA (growth favored)")

    if "UUP" in etfs:
        if etfs["UUP"]["above_sma"]:
            risk_off_signals.append("UUP above 20d SMA (dollar strength)")
        else:
            risk_on_signals.append("UUP below 20d SMA (dollar weakness)")

    # Classify regime
    n_on = len(risk_on_signals)
    n_off = len(risk_off_signals)

    if n_on >= 2 and n_off == 0:
        regime = "risk-on"
    elif n_off >= 2 and n_on == 0:
        regime = "risk-off"
    else:
        regime = "mixed"

    all_signals = risk_on_signals + risk_off_signals

    return {
        "regime": regime,
        "etfs": etfs,
        "signals": all_signals,
        "warnings": warnings,
    }


def get_fear_greed() -> dict:
    """Fetch crypto Fear & Greed index from alternative.me.

    Returns:
        Dict with value (int), classification (str).
        On failure: value=None, classification=None, warnings list.
    """
    try:
        resp = requests.get(FEAR_GREED_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        entry = data["data"][0]
        return {
            "value": int(entry["value"]),
            "classification": entry["value_classification"],
        }
    except Exception as e:
        log.error(f"Fear & Greed API error: {e}")
        return {
            "value": None,
            "classification": None,
            "warnings": [f"Fear & Greed API error: {e}"],
        }


def get_category_news(category: str, api_key: str | None = None, limit: int = 5) -> dict:
    """Fetch news sentiment for a category from Alpha Vantage NEWS_SENTIMENT.

    Args:
        category: One of CATEGORIES (crypto, politics, sports, etc.).
        api_key: Alpha Vantage API key. Falls back to ALPHA_VANTAGE_API_KEY env var.
        limit: Maximum articles to return.

    Returns:
        Dict with articles list, avg_sentiment float, and warnings list.
    """
    if api_key is None:
        api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return {
            "articles": [],
            "avg_sentiment": None,
            "warnings": ["ALPHA_VANTAGE_API_KEY not set"],
        }

    topic = _CATEGORY_TOPIC_MAP.get(category, category.upper())

    try:
        resp = requests.get(
            ALPHA_VANTAGE_BASE,
            params={
                "function": "NEWS_SENTIMENT",
                "topics": topic,
                "limit": limit,
                "sort": "LATEST",
                "apikey": api_key,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        feed = data.get("feed", [])
        articles = []
        sentiments = []
        for item in feed[:limit]:
            score = float(item.get("overall_sentiment_score", 0))
            articles.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "sentiment_score": score,
                "sentiment_label": item.get("overall_sentiment_label", ""),
                "time_published": item.get("time_published", ""),
            })
            sentiments.append(score)

        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else None

        return {
            "articles": articles,
            "avg_sentiment": round(avg_sentiment, 4) if avg_sentiment is not None else None,
            "warnings": [],
        }
    except Exception as e:
        log.error(f"Category news API error for {category}: {e}")
        return {
            "articles": [],
            "avg_sentiment": None,
            "warnings": [f"News API error for {category}: {e}"],
        }


def get_category_intel(category: str, api_key: str | None = None) -> dict:
    """Get combined market intelligence for a specific category.

    Combines macro regime, Fear & Greed (crypto only), and category news.

    Args:
        category: One of CATEGORIES.
        api_key: Alpha Vantage API key.

    Returns:
        Full intel dict with all available data and aggregated warnings.
    """
    macro = get_macro_regime(api_key)
    fear_greed = get_fear_greed() if category == "crypto" else None
    news = get_category_news(category, api_key)

    all_warnings = list(macro.get("warnings", []))
    if fear_greed and "warnings" in fear_greed:
        all_warnings.extend(fear_greed["warnings"])
    all_warnings.extend(news.get("warnings", []))

    return {
        "category": category,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "macro_regime": macro["regime"],
        "macro_signals": macro["signals"],
        "fear_greed": fear_greed,
        "news": news["articles"],
        "avg_news_sentiment": news["avg_sentiment"],
        "warnings": all_warnings,
    }


def get_market_overview(api_key: str | None = None) -> dict:
    """Get cross-category market overview with macro indicators.

    Args:
        api_key: Alpha Vantage API key.

    Returns:
        Overview dict with macro regime, Fear & Greed, category list, warnings.
    """
    macro = get_macro_regime(api_key)
    fear_greed = get_fear_greed()

    all_warnings = list(macro.get("warnings", []))
    all_warnings.extend(fear_greed.get("warnings", []))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "macro_regime": macro["regime"],
        "macro_details": macro,
        "crypto_fear_greed": fear_greed,
        "categories": CATEGORIES,
        "warnings": all_warnings,
    }
