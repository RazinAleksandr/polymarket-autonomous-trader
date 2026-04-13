"""Tests for lib/market_intel.py -- macro regime, Fear & Greed, news sentiment."""

from unittest.mock import patch, MagicMock

import pytest

from lib.market_intel import (
    get_macro_regime,
    get_fear_greed,
    get_category_news,
    get_category_intel,
    get_market_overview,
    _fetch_etf_sma,
)


# --- Fixture data ---

def _make_time_series_response(symbol: str, prices: list[float]) -> dict:
    """Build a fake Alpha Vantage TIME_SERIES_DAILY response.

    prices[0] is the MOST RECENT day's close. prices[-1] is the oldest.
    Dates are generated so that index 0 = most recent date.
    """
    daily = {}
    for i, price in enumerate(prices):
        # i=0 -> most recent date (April 3), i=1 -> April 2, etc.
        day = 25 - i  # Ensures unique positive days
        date = f"2026-03-{day:02d}" if day <= 31 else f"2026-04-{day - 31:02d}"
        # Simpler: just use sequential dates going backward
        from datetime import date as dt_date, timedelta
        d = dt_date(2026, 4, 3) - timedelta(days=i)
        date = d.isoformat()
        daily[date] = {
            "1. open": str(price),
            "2. high": str(price + 1),
            "3. low": str(price - 1),
            "4. close": str(price),
            "5. volume": "1000000",
        }
    return {
        "Meta Data": {"2. Symbol": symbol},
        "Time Series (Daily)": daily,
    }


def _make_fear_greed_response(value: int = 72, classification: str = "Greed") -> dict:
    return {
        "data": [
            {
                "value": str(value),
                "value_classification": classification,
                "timestamp": "1775290000",
            }
        ]
    }


def _make_news_response(articles: int = 3) -> dict:
    feed = []
    for i in range(articles):
        feed.append({
            "title": f"Article {i+1}",
            "url": f"https://example.com/{i+1}",
            "time_published": "20260403T120000",
            "overall_sentiment_score": 0.25 + i * 0.1,
            "overall_sentiment_label": "Somewhat-Bullish",
            "ticker_sentiment": [],
        })
    return {"feed": feed}


def _mock_requests_get(url, **kwargs):
    """Route mock responses by URL and params."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    params = kwargs.get("params", {})
    function = params.get("function", "")

    if "alphavantage" in url and function == "TIME_SERIES_DAILY":
        symbol = params.get("symbol", "QQQ")
        # prices[0] = most recent. For "above SMA": recent > average (trending up)
        # For "below SMA": recent < average (trending down)
        if symbol == "QQQ":
            # Trending up: current=474, older prices lower -> above SMA
            mock_resp.json.return_value = _make_time_series_response("QQQ", [474 - i for i in range(25)])
        elif symbol == "GLD":
            # Trending down: current=156, older prices higher -> below SMA
            mock_resp.json.return_value = _make_time_series_response("GLD", [156 + i for i in range(25)])
        elif symbol == "XLP":
            # Trending down -> below SMA (risk-on signal)
            mock_resp.json.return_value = _make_time_series_response("XLP", [51 + i for i in range(25)])
        elif symbol == "UUP":
            # Trending down -> below SMA (risk-on signal)
            mock_resp.json.return_value = _make_time_series_response("UUP", [4 + i for i in range(25)])
        else:
            mock_resp.json.return_value = _make_time_series_response(symbol, [100] * 25)
    elif "alphavantage" in url and function == "NEWS_SENTIMENT":
        mock_resp.json.return_value = _make_news_response()
    elif "alternative.me" in url:
        mock_resp.json.return_value = _make_fear_greed_response()
    else:
        mock_resp.json.return_value = {}

    return mock_resp


# --- _fetch_etf_sma tests ---

@patch("lib.market_intel.requests.get")
def test_fetch_etf_sma_success(mock_get):
    """Fetches ETF data and computes SMA correctly."""
    # 25 prices, most recent first: current=474, older prices lower
    prices = [474 - i for i in range(25)]
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_time_series_response("QQQ", prices)
    mock_get.return_value = mock_resp

    result = _fetch_etf_sma("QQQ", "test_key", period=20)

    assert result is not None
    assert result["symbol"] == "QQQ"
    assert "current" in result
    assert "sma_20" in result
    assert "above_sma" in result
    assert isinstance(result["above_sma"], bool)


@patch("lib.market_intel.requests.get")
def test_fetch_etf_sma_api_failure(mock_get):
    """Returns None on API failure."""
    mock_get.side_effect = Exception("Connection refused")

    result = _fetch_etf_sma("QQQ", "test_key")

    assert result is None


# --- get_macro_regime tests ---

@patch("lib.market_intel.requests.get", side_effect=_mock_requests_get)
def test_macro_regime_risk_on(mock_get):
    """Risk-on when QQQ above SMA and GLD below SMA."""
    result = get_macro_regime("test_key")

    assert result["regime"] == "risk-on"
    assert isinstance(result["etfs"], dict)
    assert isinstance(result["signals"], list)
    assert len(result["signals"]) > 0


@patch("lib.market_intel.requests.get")
def test_macro_regime_risk_off(mock_get):
    """Risk-off when QQQ below SMA and GLD above SMA."""
    def risk_off_side_effect(url, **kwargs):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        params = kwargs.get("params", {})
        symbol = params.get("symbol", "QQQ")
        # prices[0]=most recent. For below SMA: recent < average (trending down)
        if symbol == "QQQ":
            # Trending down: current=426, older higher -> below SMA
            mock_resp.json.return_value = _make_time_series_response("QQQ", [426 + i for i in range(25)])
        elif symbol == "GLD":
            # Trending up: current=204, older lower -> above SMA
            mock_resp.json.return_value = _make_time_series_response("GLD", [204 - i for i in range(25)])
        elif symbol == "XLP":
            # Trending up -> above SMA (defensive, risk-off)
            mock_resp.json.return_value = _make_time_series_response("XLP", [99 - i for i in range(25)])
        elif symbol == "UUP":
            # Trending up -> above SMA (dollar strength, risk-off)
            mock_resp.json.return_value = _make_time_series_response("UUP", [52 - i for i in range(25)])
        return mock_resp

    mock_get.side_effect = risk_off_side_effect

    result = get_macro_regime("test_key")

    assert result["regime"] == "risk-off"
    assert isinstance(result["signals"], list)


@patch("lib.market_intel.requests.get")
def test_macro_regime_mixed(mock_get):
    """Mixed when signals are contradictory."""
    def mixed_side_effect(url, **kwargs):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        params = kwargs.get("params", {})
        symbol = params.get("symbol", "QQQ")
        # QQQ above SMA (risk-on), GLD also above SMA (risk-off) -> mixed
        if symbol == "QQQ":
            # Trending up -> above SMA (risk-on)
            mock_resp.json.return_value = _make_time_series_response("QQQ", [474 - i for i in range(25)])
        elif symbol == "GLD":
            # Trending up -> above SMA (risk-off)
            mock_resp.json.return_value = _make_time_series_response("GLD", [204 - i for i in range(25)])
        elif symbol == "XLP":
            # Flat -> at SMA (neutral)
            mock_resp.json.return_value = _make_time_series_response("XLP", [75] * 25)
        elif symbol == "UUP":
            # Flat -> at SMA (neutral)
            mock_resp.json.return_value = _make_time_series_response("UUP", [28] * 25)
        return mock_resp

    mock_get.side_effect = mixed_side_effect

    result = get_macro_regime("test_key")

    assert result["regime"] == "mixed"


def test_macro_regime_no_api_key():
    """Returns null regime with warning when no API key."""
    result = get_macro_regime(None)

    assert result["regime"] is None
    assert "warnings" in result
    assert any("API_KEY" in w for w in result["warnings"])


@patch("lib.market_intel.requests.get")
def test_macro_regime_partial_failure(mock_get):
    """Returns available data with warnings on partial API failure (D-04)."""
    call_count = 0

    def partial_side_effect(url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            # First 2 ETFs succeed
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            mock_resp.json.return_value = _make_time_series_response("QQQ", [450 + i for i in range(25)])
            return mock_resp
        else:
            # Rest fail
            raise Exception("API rate limited")

    mock_get.side_effect = partial_side_effect

    result = get_macro_regime("test_key")

    assert "warnings" in result
    assert len(result["warnings"]) > 0
    # Should still have some ETF data
    assert isinstance(result["etfs"], dict)


# --- get_fear_greed tests ---

@patch("lib.market_intel.requests.get")
def test_fear_greed_success(mock_get):
    """Returns Fear & Greed value and classification."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_fear_greed_response(72, "Greed")
    mock_get.return_value = mock_resp

    result = get_fear_greed()

    assert result["value"] == 72
    assert result["classification"] == "Greed"


@patch("lib.market_intel.requests.get")
def test_fear_greed_api_failure(mock_get):
    """Returns null with warnings on API failure."""
    mock_get.side_effect = Exception("Connection refused")

    result = get_fear_greed()

    assert result["value"] is None
    assert result["classification"] is None
    assert "warnings" in result
    assert len(result["warnings"]) > 0


# --- get_category_news tests ---

@patch("lib.market_intel.requests.get")
def test_category_news_success(mock_get):
    """Returns articles with sentiment from Alpha Vantage NEWS_SENTIMENT."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = _make_news_response(3)
    mock_get.return_value = mock_resp

    result = get_category_news("crypto", "test_key")

    assert isinstance(result["articles"], list)
    assert len(result["articles"]) == 3
    assert "avg_sentiment" in result
    assert result["avg_sentiment"] is not None


@patch("lib.market_intel.requests.get")
def test_category_news_api_failure(mock_get):
    """Returns empty list with warnings on API failure."""
    mock_get.side_effect = Exception("API error")

    result = get_category_news("crypto", "test_key")

    assert result["articles"] == []
    assert "warnings" in result
    assert len(result["warnings"]) > 0


def test_category_news_no_api_key():
    """Returns empty with warning when no API key."""
    result = get_category_news("crypto", None)

    assert result["articles"] == []
    assert "warnings" in result


# --- get_category_intel tests ---

@patch("lib.market_intel.requests.get", side_effect=_mock_requests_get)
def test_category_intel_crypto(mock_get):
    """Returns full intel dict with macro, fear_greed, news for crypto."""
    result = get_category_intel("crypto", "test_key")

    assert result["category"] == "crypto"
    assert "generated_at" in result
    assert "macro_regime" in result
    assert "macro_signals" in result
    assert result["fear_greed"] is not None
    assert isinstance(result["news"], list)
    assert "warnings" in result


@patch("lib.market_intel.requests.get", side_effect=_mock_requests_get)
def test_category_intel_non_crypto(mock_get):
    """Non-crypto categories skip Fear & Greed."""
    result = get_category_intel("politics", "test_key")

    assert result["category"] == "politics"
    assert result["fear_greed"] is None


# --- get_market_overview tests ---

@patch("lib.market_intel.requests.get", side_effect=_mock_requests_get)
def test_market_overview(mock_get):
    """Returns cross-category overview with macro and fear_greed."""
    result = get_market_overview("test_key")

    assert "generated_at" in result
    assert "macro_regime" in result
    assert "macro_details" in result
    assert "crypto_fear_greed" in result
    assert "categories" in result
    assert isinstance(result["categories"], list)
    assert "warnings" in result


@patch("lib.market_intel.requests.get")
def test_market_overview_all_fail(mock_get):
    """Returns partial data with warnings when all APIs fail."""
    mock_get.side_effect = Exception("Network error")

    result = get_market_overview("test_key")

    assert "warnings" in result
    assert len(result["warnings"]) > 0
    assert "categories" in result
