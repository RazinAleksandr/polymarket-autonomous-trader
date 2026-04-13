# Phase 3: New Instrument Tools - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 03-new-instrument-tools
**Areas discussed:** Calibration storage, Market intel sources, Heartbeat design, Test strategy

---

## Calibration Storage

| Option | Description | Selected |
|--------|-------------|----------|
| SQLite only | Add calibration_records table to trading.db. calibration.json becomes computed summary. | ✓ |
| JSON file only | Keep calibration.json as primary store. Simpler but harder to query. | |
| Both independent | SQLite for raw records, JSON for summaries maintained independently. | |

**User's choice:** SQLite only (Recommended)
**Notes:** Single source of truth, queryable, matches existing DataStore pattern.

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-regenerate | record_outcome.py writes DB then regenerates calibration.json in one call. | ✓ |
| Separate command | record_outcome.py only writes DB. Separate refresh step. | |
| You decide | Claude's discretion. | |

**User's choice:** Auto-regenerate (Recommended)
**Notes:** Claude always sees fresh summary after each outcome recording.

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-generate corrections | Compute corrections automatically using thresholds from reference. | ✓ |
| Claude decides | Only report error_pp. Claude decides on corrections via skill. | |
| You decide | Claude's discretion. | |

**User's choice:** Auto-generate (Recommended)
**Notes:** Thresholds from reference: >10pp, >20pp, >30pp severity levels.

---

## Market Intel Sources

| Option | Description | Selected |
|--------|-------------|----------|
| Graceful degradation | Return partial results with null fields and warnings array. | ✓ |
| Cache + fallback | Cache last response, return stale data on failure. | |
| Fail loudly | Return error JSON if any source fails. | |

**User's choice:** Graceful degradation (Recommended)
**Notes:** Never block a trading cycle over missing macro data.

| Option | Description | Selected |
|--------|-------------|----------|
| Simple trend | Current price vs 20-day SMA for each ETF. Classify as risk-on/off/mixed. | ✓ |
| Multi-signal composite | Price vs SMA + volume trends + cross-ETF correlations. | |
| You decide | Claude's discretion. | |

**User's choice:** Simple trend (Recommended)
**Notes:** Straightforward, easy to test, sufficient for trading context.

| Option | Description | Selected |
|--------|-------------|----------|
| Both modes | --category for specific intel, --overview for cross-category summary. | ✓ |
| Always full dump | Single call returns all categories. | |
| You decide | Claude's discretion. | |

**User's choice:** Both modes (Recommended)
**Notes:** Matches ROADMAP.md success criteria.

| Option | Description | Selected |
|--------|-------------|----------|
| Alpha Vantage news | Use NEWS_SENTIMENT endpoint for structured news with sentiment. | ✓ |
| Skip news in tool | Only macro + Fear & Greed. Claude handles news via web search. | |
| You decide | Claude's discretion. | |

**User's choice:** Alpha Vantage news (Recommended)
**Notes:** Already have API key. Structured headlines + sentiment scores.

---

## Heartbeat Design

| Option | Description | Selected |
|--------|-------------|----------|
| Adapt to new cycle | 3 flags (scan, resolve, learn) with thresholds tuned for 30-min cycle interval. | ✓ |
| Add position_check flag | 4 flags including position_check_needed for Phase A. | |
| You decide | Claude's discretion. | |

**User's choice:** Adapt to new cycle (Recommended)
**Notes:** Same 3 flags as reference, tuned for new architecture.

| Option | Description | Selected |
|--------|-------------|----------|
| DB + reports + positions | Read trading.db, state/reports/, positions table. No new state files. | ✓ |
| Dedicated state file | Maintain heartbeat-state.json with timestamps. | |
| You decide | Claude's discretion. | |

**User's choice:** DB + reports + positions (Recommended)
**Notes:** Uses existing data sources, no new state files needed.

| Option | Description | Selected |
|--------|-------------|----------|
| scripts/ | New directory for infrastructure scripts. Separates from user-facing tools. | |
| tools/ | Keep everything in one directory. | |
| You decide | Claude's discretion on file organization. | ✓ |

**User's choice:** You decide
**Notes:** Claude has discretion on whether heartbeat lives in scripts/ or tools/.

---

## Test Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Mock at requests level | unittest.mock.patch on requests.get/post. Fixture files with sample JSON. | ✓ |
| Abstract behind interface | MarketIntelProvider protocol/ABC with fake for tests. | |
| You decide | Claude's discretion. | |

**User's choice:** Mock at requests level (Recommended)
**Notes:** Matches existing test patterns for Gamma API.

| Option | Description | Selected |
|--------|-------------|----------|
| Real in-memory DB | sqlite3 ':memory:' with real DataStore. Tests actual SQL and schema. | ✓ |
| Mock DataStore | Mock methods to return canned data. | |
| You decide | Claude's discretion. | |

**User's choice:** Real in-memory DB (Recommended)
**Notes:** Matches test_db.py pattern. Fast, no I/O.

| Option | Description | Selected |
|--------|-------------|----------|
| Brier score math + edge cases | Focus on calculation correctness, category aggregation, correction thresholds. | ✓ |
| CLI integration tests | Test full CLI wrappers end-to-end with subprocess calls. | |
| Both equally | Equal coverage for math/logic and CLI integration. | |
| You decide | Claude's discretion. | |

**User's choice:** Brier score math + edge cases (Recommended)
**Notes:** Math must be right. Edge cases: empty DB, single trade, all-wins, all-losses.

---

## Claude's Discretion

- Heartbeat file location (scripts/ vs tools/)
- Internal module structure of lib/market_intel.py and lib/calibration.py
- Exact heartbeat time window thresholds
- CLI integration test coverage beyond core math/logic tests

## Deferred Ideas

None — discussion stayed within phase scope
