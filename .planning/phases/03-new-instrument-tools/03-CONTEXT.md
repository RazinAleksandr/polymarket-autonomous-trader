# Phase 3: New Instrument Tools - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Build three new Python modules (`lib/market_intel.py`, `lib/calibration.py`, `scripts/heartbeat.py`) with CLI wrappers (`tools/get_market_intel.py`, `tools/record_outcome.py`) and comprehensive tests. These are the new capabilities the existing codebase lacks for autonomous trading — market intelligence, calibration tracking, and heartbeat signal generation.

</domain>

<decisions>
## Implementation Decisions

### Calibration Storage
- **D-01:** SQLite is the single source of truth for calibration data. Add a `calibration_records` table to `trading.db` via DataStore. `knowledge/calibration.json` becomes a computed summary regenerated from DB.
- **D-02:** `record_outcome.py` auto-regenerates `calibration.json` after each recording — write to DB then regenerate JSON in one call. Claude always sees a fresh summary file.
- **D-03:** Calibration corrections are auto-generated when `error_pp` exceeds thresholds (from reference: >10pp slight, >20pp moderate, >30pp severe). Claude reads corrections from `calibration.json` and applies during analysis via calibration-check skill.

### Market Intel Sources
- **D-04:** Graceful degradation on API failures — return partial results with null fields and a `warnings` array. Never block a trading cycle over missing macro data.
- **D-05:** Simple trend-based macro regime detection — compare current price vs 20-day SMA for each ETF (QQQ, XLP, GLD, UUP). Classify as risk-on, risk-off, or mixed.
- **D-06:** `get_market_intel.py` supports both `--category crypto` (category-specific intel) and `--overview` (cross-category summary). Matches ROADMAP.md success criteria.
- **D-07:** Use Alpha Vantage NEWS_SENTIMENT endpoint for structured news with sentiment scores. Provides headlines, relevance, and sentiment per ticker/topic.

### Heartbeat Design
- **D-08:** Three signal flags adapted to the 5-phase trading cycle: `scan_needed` (Phase B), `resolve_needed` (Phase A), `learn_needed` (Phase E). Same 3 flags as reference but thresholds tuned for 30-min cycle interval.
- **D-09:** Heartbeat reads `trading.db` (last trade timestamps), `state/reports/` (last cycle time), and positions table (approaching end_dates). No new state files needed — uses existing data.

### Test Strategy
- **D-10:** Mock external APIs at the `requests.get`/`requests.post` level using `unittest.mock.patch`. Fixture files with sample JSON responses. Matches existing test patterns for Gamma API.
- **D-11:** Calibration tests use real in-memory SQLite (`':memory:'`) with real DataStore. Tests actual SQL, schema, and queries. Matches existing `test_db.py` pattern.
- **D-12:** Primary test focus on Brier score math correctness and edge cases — empty DB, single trade, all-wins, all-losses, category aggregation, correction threshold boundaries.

### Claude's Discretion
- Whether `heartbeat.py` lives in `scripts/` (new directory) or `tools/` (existing CLI dir). Infrastructure scripts vs user-facing tools distinction is Claude's call.
- Internal module structure of `lib/market_intel.py` and `lib/calibration.py` — function signatures, helper decomposition, class vs function approach.
- Exact thresholds for heartbeat time windows (how long since last scan/resolve/learn triggers each flag).
- CLI integration test coverage beyond the core math/logic tests.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Reference Implementations
- `polymarket_claude/scripts/calibration.py` — Reference calibration with Brier scores, `interpret_error()` thresholds, category tracking
- `polymarket_claude/scripts/heartbeat.py` — Reference heartbeat with `scan_needed`, `resolve_needed`, `learn_needed` flags and time-based triggers

### Existing Codebase (extend/integrate with)
- `polymarket-trader/lib/db.py` — DataStore class with SQLite schema; add `calibration_records` table here
- `polymarket-trader/lib/config.py` — Config dataclass with env-var loading; add ALPHA_VANTAGE_API_KEY field
- `polymarket-trader/knowledge/calibration.json` — Empty seed structure (Phase 2); becomes computed output from DB
- `polymarket-trader/lib/market_data.py` — Existing Gamma API client; pattern reference for new API clients

### Skill Docs (tools must produce compatible output)
- `polymarket-trader/.claude/skills/calibration-check.md` — Skill that consumes calibration data; tool output must match what this skill expects
- `polymarket-trader/.claude/skills/evaluate-edge.md` — Skill that uses market intel; tool JSON should be usable here

### Test Infrastructure
- `polymarket-trader/tests/conftest.py` — Existing test fixtures and patterns
- `polymarket-trader/tests/test_db.py` — DataStore test patterns with in-memory SQLite

### Requirements
- `.planning/REQUIREMENTS.md` — KNOW-04, TOOL-01 through TOOL-06

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lib/db.py` DataStore: SQLite with trades/positions/decisions tables — extend with calibration_records table
- `lib/config.py` Config dataclass: env-var loading pattern — add ALPHA_VANTAGE_API_KEY
- `lib/market_data.py`: Gamma API client with `requests` — pattern for Alpha Vantage client
- `lib/models.py`: dataclass patterns (Market, TradeSignal, etc.) — use for MarketIntel, CalibrationRecord
- `tests/conftest.py`: existing test fixtures — extend for new modules
- 11 existing CLI tools in `tools/`: consistent argparse + JSON output + `--pretty` flag pattern

### Established Patterns
- CLI tools: argparse, JSON stdout, `--pretty` flag for human-readable, exit code 0/1
- Lib modules: functions with type hints, dataclass return types, `get_logger()` for logging
- Config: environment variables via `python-dotenv`, Config dataclass fields with defaults
- Error handling: return safe defaults (empty list, None), log errors, continue

### Integration Points
- `trading.db` — new calibration_records table via DataStore._create_tables()
- `knowledge/calibration.json` — regenerated by calibration.py after each record_outcome call
- `state/signal.json` — written by heartbeat.py, read by future run_cycle.sh (Phase 4)
- `lib/config.py` — needs ALPHA_VANTAGE_API_KEY field added (or deferred to Phase 4 CONF-01)

</code_context>

<specifics>
## Specific Ideas

- Brier score formula: `(stated_prob - actual)^2` where actual = 1 (WIN) or 0 (LOSS). Lower is better.
- Calibration corrections use the reference thresholds: >10pp underconfident (can size up), <-10pp slightly overconfident (require +6pp edge, -25% size), <-20pp overconfident (require +8pp edge, -50% size), <-30pp severely overconfident (require +10pp edge, max 1% bankroll)
- ETF regime detection: QQQ (tech/growth), XLP (consumer staples/defensive), GLD (gold/safe haven), UUP (dollar strength). Risk-on = QQQ above SMA + GLD below SMA; risk-off = opposite; mixed = everything else.
- Fear & Greed index: alternative.me API (free, no key needed) — returns 0-100 scale

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-new-instrument-tools*
*Context gathered: 2026-04-04*
