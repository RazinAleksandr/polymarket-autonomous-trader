# Codebase Concerns

**Analysis Date:** 2026-04-02

## Tech Debt

**Schema Migrations in __init__ (Fragile):**
- Issue: Database schema migrations run inline in `DataStore.__init__()` via try-except blocks, swallowing `OperationalError` exceptions
- Files: `/home/trader/polymarket-agent/lib/db.py:99-111`
- Impact: Silent failures if ALTER TABLE commands fail for unexpected reasons (permission issues, concurrent access). New schema additions might silently not apply, causing downstream crashes.
- Fix approach: Implement proper migration framework or at minimum log all migration attempts and their results. Test against fresh and existing databases.

**Database Connection Pooling Missing:**
- Issue: Each DataStore instance creates a single `sqlite3.connect()` with no connection pooling or per-thread isolation
- Files: `/home/trader/polymarket-agent/lib/db.py:15`
- Impact: If multiple threads or processes access the same trading.db, SQLite's locking model may cause "database is locked" errors. Paper trading currently single-threaded but future parallelization (e.g., async sub-agents) could trigger this.
- Fix approach: Add WAL mode to SQLite or switch to connection pooling with per-request isolation if concurrency is added.

**API Request Timeout Hardcoded:**
- Issue: All external API calls use hardcoded timeouts (30s for Gamma API, 5s for fee API)
- Files: `/home/trader/polymarket-agent/lib/market_data.py:47`, `/home/trader/polymarket-agent/lib/fees.py:123`
- Impact: Slow networks or high-latency environments will experience more failures. No retry-with-backoff implemented.
- Fix approach: Make timeouts configurable via config.py. Add exponential backoff for transient failures.

**No Graceful Degradation for Missing API Fields:**
- Issue: Market data parsing defensively checks for both camelCase and snake_case field names, but silently defaults to 0.0 or 0.5 for missing fields
- Files: `/home/trader/polymarket-agent/lib/market_data.py:118-140`
- Impact: Malformed API responses could silently propagate zeroed prices into trading decisions. A market with `yes_price=0.5` (default) is indistinguishable from one with actual 0.5 price.
- Fix approach: Add explicit logging when defaults are used. Consider rejecting markets with missing required fields rather than defaulting.

## Known Bugs

**Price Parsing Double Negation Vulnerability:**
- Symptoms: If market.yes_price is None or empty string, line 118 in market_data.py evaluates to 0.5 silently
- Files: `/home/trader/polymarket-agent/lib/market_data.py:118-119`
- Trigger: Gamma API returns `outcomePrices: ["", "0.25"]` or missing field entirely
- Workaround: None currently; will accept 0.5 as actual price. Log monitoring can catch this.
- Impact: Zero position sizing or incorrect Kelly calculations on affected markets

**Position Reduce with Float Tolerance Too Lenient:**
- Symptoms: Partial sells may leave residual share fractions due to 0.001 tolerance rounding
- Files: `/home/trader/polymarket-agent/lib/db.py:326, 334`
- Trigger: Sell 10.0025 shares from position of 10.00 shares
- Workaround: Always round sell sizes to 2 decimals before calling reduce_position
- Impact: Closed position may incorrectly retain 0.0025 shares if float arithmetic rounds differently

**Fee Rate API Graceful Failure:**
- Symptoms: If /fee-rate endpoint returns no data or invalid JSON, fallback to category table happens silently without warning
- Files: `/home/trader/polymarket-agent/lib/fees.py:121-133`
- Trigger: CLOB API outage or malformed response
- Workaround: Monitor log files for "Fee rate API lookup failed" warnings
- Impact: Paper trading may use stale (March 2026) category fees rather than current API rates, underestimating actual costs

## Security Considerations

**Private Key Exposure via Logging:**
- Risk: If `config.private_key` is accidentally logged or included in exception tracebacks, it leaks the trading wallet
- Files: `/home/trader/polymarket-agent/lib/config.py:25`, all modules importing config
- Current mitigation: Private key never printed in log_decision() or standard logging. Config object properties are not logged.
- Recommendations: Add secret field masking in __str__ method of Config dataclass. Add unit test to prevent logging of private_key field.

**Unencrypted Database Storage:**
- Risk: SQLite database (trading.db) stores all position and trade history in plaintext. Any filesystem access compromise leaks position sizes, realized P&L, and strategies
- Files: `/home/trader/polymarket-agent/lib/db.py`
- Current mitigation: Reliance on OS-level filesystem permissions
- Recommendations: For production live trading, encrypt SQLite database at rest using sqlcipher or move to encrypted volume storage.

**No Input Validation on Market ID:**
- Risk: Market IDs are user-supplied strings passed directly to Gamma API requests without sanitization
- Files: `/home/trader/polymarket-agent/lib/market_data.py:82`
- Current mitigation: requests.get() URL-encodes parameters
- Recommendations: Add explicit validation that market_id matches expected format (hex/alphanumeric) before API calls.

## Performance Bottlenecks

**Sequential Analyst Spawning in Trading Cycle:**
- Problem: Per CLAUDE.md, analysts must run sequentially (not parallel) due to session failures. 10 markets = 10+ analyst spawns, each blocking until completion
- Files: `/home/trader/polymarket-agent/.claude/CLAUDE.md:Step 2`
- Cause: Sub-agent task queue or session state management issue not yet root-caused
- Improvement path: Investigate why parallel analyst spawns fail. Implement batch analyst endpoint to process 5-10 markets per agent invocation. Could reduce cycle time by 5-10x.

**Gamma API Redundant Calls in Cycle:**
- Problem: Position monitor, risk manager, and portfolio update all call fetch_market_by_id() for same markets, no caching
- Files: `/home/trader/polymarket-agent/lib/portfolio.py:43`, `/home/trader/polymarket-agent/lib/market_data.py:70-89`
- Cause: Stateless function design; no global or request-scoped cache
- Improvement path: Add market cache with 5-minute TTL. Batch fetch multiple market IDs in single API call if Gamma API supports it.

**JSON Parsing Overhead:**
- Problem: Market data parsing calls json.loads() on every market for outcomePrices (stringified JSON from API)
- Files: `/home/trader/polymarket-agent/lib/market_data.py:107-116`
- Cause: Gamma API limitation; necessary for compatibility
- Improvement path: If Gamma API ever supports native JSON, remove double-parsing. Otherwise, cache parsed prices alongside raw market objects.

## Fragile Areas

**Fee Parameters Table (Category-Specific Hardcoded):**
- Files: `/home/trader/polymarket-agent/lib/fees.py:17-29`
- Why fragile: Fee rate "exponent" parameters (e.g., 1, 0.5, 2) are hardcoded March 2026 assumptions. Polymarket docs may update without code change.
- Safe modification: Add config-driven fee table that can be updated via .env or JSON file without code deploy.
- Test coverage: No unit tests for fee calculations vs. actual Polymarket fees. Manual comparison needed after any fee update.

**Kelly Criterion Implementation:**
- Files: `/home/trader/polymarket-agent/lib/strategy.py:8-29`
- Why fragile: Fractional Kelly (default 0.25) is hardcoded. Any change to kelly_fraction config requires testing across all edge cases (extreme probabilities, zero edge, high edge scenarios).
- Safe modification: All callers pass kelly_fraction explicitly. Test against boundary cases (prob=0.01, prob=0.99, price near 0 or 1).
- Test coverage: No unit test file exists. Paper trading verification only.

**Position Tracking Assumptions:**
- Files: `/home/trader/polymarket-agent/lib/db.py:139-166` (upsert_position), `/home/trader/polymarket-agent/lib/portfolio.py:78-128` (check_resolved_markets)
- Why fragile: Assumes one position per market_id (UNIQUE constraint). If user holds both YES and NO on same market, system breaks.
- Safe modification: Change primary key to (market_id, side) if hedge trades planned. Audit all position queries to handle multiple per market.
- Test coverage: No test for hedge position scenarios.

**CLOB Client Instantiation Without Caching:**
- Files: `/home/trader/polymarket-agent/lib/pricing.py:41, 69, 90`
- Why fragile: Every get_fill_price/get_best_bid/get_best_ask call creates a new ClobClient. If network is slow, overhead multiplies.
- Safe modification: Create a module-level or class-level singleton ClobClient for read-only pricing. Be careful with live trading clients which need authentication.
- Test coverage: No benchmarking of overhead.

## Scaling Limits

**SQLite Lock Contention:**
- Current capacity: Single-threaded paper trading up to ~100 trades per cycle
- Limit: If cycles parallelized or multiple agents write simultaneously, SQLite's per-connection lock will become bottleneck
- Scaling path: Migrate to PostgreSQL for concurrent multi-writer scenarios. Alternatively, implement write queue with single writer thread.

**Market Discovery Pagination:**
- Current capacity: fetch_active_markets() fetches 50 markets from Gamma API and filters locally, returns top N
- Limit: If trading 100+ markets per cycle, API pagination inefficiency grows. Filtering happens client-side.
- Scaling path: Push filters to Gamma API query params. Implement cursor-based pagination for large result sets.

**Position Monitoring Cost:**
- Current capacity: Position monitor spawns one sub-agent task per cycle, reviews all open positions
- Limit: With 50+ open positions, review cost scales linearly with position count
- Scaling path: Batch position reviews (10-20 per analyzer) or implement lightweight heuristic pre-filters (e.g., only review positions down 20%+ or near resolution).

## Dependencies at Risk

**py-clob-client (>=0.17.0):**
- Risk: Package is maintained by Polymarket team; breaking API changes in future versions not contractually guaranteed
- Impact: If Polymarket updates py-clob-client with incompatible changes, live trading breaks until code updates
- Migration plan: Pin to exact version (e.g., ==0.17.0) in requirements.txt. Monitor release notes. Plan 1-2 week buffer for testing before upgrading.

**openai SDK (Python):**
- Risk: Used for market analysis (GPT-4o) but not pinned to version. API changes or model discontinuation could break analysis step
- Impact: If OpenAI deprecates "gpt-4o" model or changes Responses API, analyst sub-agent fails
- Migration plan: Use exact version pinning for openai package. Maintain fallback to GPT-4 turbo if gpt-4o unavailable. Test quarterly with latest SDK.

**requests (>=2.31.0):**
- Risk: Minor; widely stable. But used in critical paths (market discovery, fee lookup). Timeout behavior changes between versions could affect retry logic.
- Impact: Low; requests is mature
- Migration plan: Continue to pin minor version (2.31.x) in requirements.txt

## Missing Critical Features

**No Live Gate Verification:**
- Problem: Live trading is guarded only by PAPER_TRADING config boolean. No minimum paper trading requirement (e.g., 10 cycles, positive P&L) enforced
- Blocks: Cannot safely transition to real money trading without human manual review
- Impact: User could accidentally enable PAPER_TRADING=false and lose capital on untested strategy
- Fix approach: Implement check in config validation that requires min_paper_cycles (currently in Config but not enforced) and min_paper_pnl before allowing live mode

**No Position-Level Stop Loss:**
- Problem: Strategy can only generate new BUY signals. No automatic or manual stop-loss mechanism for losing positions
- Blocks: Cannot limit downside on bad analysis. User must manually monitor and close
- Impact: Uncapped losses on a single bad trade if edge estimate was wrong
- Fix approach: Add stop-loss_percent to position tracking. Trigger automatic SELL in portfolio update if position hits threshold.

**No Alert/Notification System:**
- Problem: All logging is to console and JSON file. No email, Slack, or webhook alerts for critical events
- Blocks: Unattended trading runs silently; user may not notice cycle failures or large losses for hours
- Impact: Slower incident response
- Fix approach: Add alerts module that sends notifications for: cycle failures, large P&L swings, risk limit breaches, unresolved trade execution failures

**No Manual Trade Override:**
- Problem: Trade plan execution is fully automated. User cannot inject manual trades or halt cycle mid-execution
- Blocks: Cannot react to breaking news or market anomalies during cycle
- Impact: Inflexibility for time-sensitive situations
- Fix approach: Add inter-process signal handling or webserver endpoint to pause/cancel cycle or inject manual trades

## Test Coverage Gaps

**Fee Calculation vs. Live Polymarket Fees:**
- What's not tested: No comparison between calculate_fee() results and actual fees charged on Polymarket CLOB
- Files: `/home/trader/polymarket-agent/lib/fees.py`
- Risk: Paper trading may underestimate fees by 10-50%, leading to live trading disappointment
- Priority: High — fee estimation drives Kelly sizing directly

**Kelly Criterion Edge Cases:**
- What's not tested: Probability at 0.0, 0.5, 1.0; price at 0.0, 0.5, 1.0; kelly_fraction=0, very high kelly_raw values
- Files: `/home/trader/polymarket-agent/lib/strategy.py:8-29`
- Risk: Extreme inputs could produce NaN, Infinity, or negative position sizes
- Priority: High — used in every trade signal

**Paper Trade Execution Accuracy:**
- What's not tested: Does get_fill_price() match actual trade fills on Polymarket? Slippage estimation?
- Files: `/home/trader/polymarket-agent/lib/pricing.py:16-53`, `/home/trader/polymarket-agent/lib/trading.py:51-163`
- Risk: Paper trading P&L may be 10-20% optimistic compared to live fills
- Priority: High — validates strategy profitability

**Position Resolution Detection:**
- What's not tested: Does market.closed flag accurately reflect on-chain resolution? Latency between resolution and flag update?
- Files: `/home/trader/polymarket-agent/lib/portfolio.py:78-128`
- Risk: Resolved positions may remain open incorrectly if Gamma API has lag
- Priority: Medium — affects P&L calculation accuracy

**Database Schema Migrations:**
- What's not tested: Adding new columns to existing database. Behavior on database with partial migration history.
- Files: `/home/trader/polymarket-agent/lib/db.py:99-111`
- Risk: Deployment to existing database with stale schema could silently fail to apply schema, causing crashes
- Priority: High — affects reliability on repeated deployments

---

*Concerns audit: 2026-04-02*
