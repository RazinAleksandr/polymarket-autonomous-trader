---
phase: 03-new-instrument-tools
plan: 02
subsystem: market-intelligence
tags: [market-intel, macro-regime, fear-greed, news-sentiment, cli]
dependency_graph:
  requires: []
  provides: [market_intel_library, get_market_intel_cli]
  affects: [trading_cycle_phase_c, agent_layer_context]
tech_stack:
  added: [alternative.me_api, alpha_vantage_news_sentiment]
  patterns: [graceful_degradation_with_warnings, etf_sma_regime_detection]
key_files:
  created:
    - polymarket-trader/lib/market_intel.py
    - polymarket-trader/tools/get_market_intel.py
  modified:
    - polymarket-trader/tests/test_market_intel.py
decisions:
  - Used alternative.me free API for Fear & Greed (no key required)
  - Mapped categories to Alpha Vantage NEWS_SENTIMENT topics (BLOCKCHAIN, POLITICS, etc.)
  - Regime classification requires 2+ concordant signals with 0 opposing for risk-on/risk-off
metrics:
  duration: 287s
  completed: "2026-04-04T08:11:51Z"
  tasks: 2
  files: 3
---

# Phase 3 Plan 2: Market Intelligence Library Summary

Market intel library providing ETF-based macro regime detection, crypto Fear & Greed index, and Alpha Vantage news sentiment with graceful degradation on all API failures.

## What Was Built

### lib/market_intel.py (5 public functions + 1 private helper)

- `_fetch_etf_sma(symbol, api_key, period)` -- Fetches Alpha Vantage TIME_SERIES_DAILY and computes simple moving average
- `get_macro_regime(api_key)` -- Classifies macro environment as risk-on, risk-off, or mixed based on QQQ, GLD, XLP, UUP SMA positions (per D-05)
- `get_fear_greed()` -- Fetches crypto Fear & Greed index from alternative.me (free, no API key)
- `get_category_news(category, api_key, limit)` -- Fetches news sentiment from Alpha Vantage NEWS_SENTIMENT endpoint (per D-07)
- `get_category_intel(category, api_key)` -- Combines macro + Fear & Greed (crypto only) + category news
- `get_market_overview(api_key)` -- Cross-category overview with macro regime and Fear & Greed

### tools/get_market_intel.py (CLI wrapper)

- `--category {crypto,politics,sports,commodities,entertainment,finance}` -- Category-specific intel
- `--overview` -- Cross-category market overview
- `--pretty` -- Pretty-print JSON output
- Mutually exclusive args validation, graceful degradation on missing API key

### tests/test_market_intel.py (16 tests)

- All external APIs mocked at `requests.get` level per D-10
- Tests cover: success paths, API failures, partial degradation, missing API key, regime classification (risk-on, risk-off, mixed)

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 (RED) | 7ec450f | Failing tests for market intel library |
| 1 (GREEN) | 62e1c18 | Implement market intel library + fix tests |
| 2 | 5c5cf0e | CLI wrapper with --category and --overview |

## Deviations from Plan

None -- plan executed exactly as written.

## Decisions Made

1. **Alternative.me for Fear & Greed**: Free API, no key required, returns real-time crypto sentiment index
2. **Category-to-topic mapping**: crypto->BLOCKCHAIN, politics->POLITICS, sports->SPORTS, commodities->ENERGY_TRANSPORTATION, entertainment->ENTERTAINMENT, finance->FINANCE
3. **Regime threshold**: 2+ concordant signals with 0 opposing required for risk-on or risk-off; anything else classified as mixed

## Known Stubs

None -- all functions are fully wired to external APIs with graceful degradation.

## Verification Results

- `python -m pytest tests/test_market_intel.py -x -v` -- 16/16 passed
- `python tools/get_market_intel.py --overview --pretty` -- Returns JSON with macro_regime, crypto_fear_greed, categories (macro_regime null without API key as expected)
- `python tools/get_market_intel.py --category crypto --pretty` -- Returns JSON with category, fear_greed (live value), news, warnings
- All 199 existing tests still pass (excluding pre-existing test_strategy_evolution failure)

## Self-Check: PASSED
