# Polymarket Autonomous Trader

<!-- OPERATOR-SET: Do not modify this section -->
Paper trading is the default mode. NEVER switch to live trading without explicit user request.

## Quick Reference
- **Venv:** `source .venv/bin/activate` (required before any Python command)
- **Tools dir:** `tools/` -- CLI scripts for market discovery, pricing, trading, portfolio
- **State dir:** `state/` -- `strategy.md`, `core-principles.md`, `cycles/`, `reports/`
- **Skills dir:** `.claude/skills/` -- 6 skill reference docs loaded on demand
- **Config:** `lib/config.py` loads from `.env` via python-dotenv
- **DB:** `trading.db` (SQLite, auto-created)

---

## Session Start

Every trading session begins with:

1. Generate cycle ID: `YYYYMMDD-HHMMSS` format using current UTC time
2. Create directories: `mkdir -p state/cycles/{cycle_id} state/reports`
3. Read these files for context:
   - `state/strategy.md` -- your evolving trading strategy
   - `state/core-principles.md` -- immutable guardrails (NEVER modify)
   - 3 most recent `state/reports/cycle-*.md` files (sorted descending)
   - `knowledge/golden-rules.md` -- accumulated trading wisdom (when it exists)
4. Log: "Starting trading cycle {cycle_id}"

If this is the first-ever cycle (no prior reports exist), note it as the inaugural cycle.
The strategy file may be minimal -- that is expected. It will evolve through Phase E
after positions start resolving.

If `knowledge/calibration.json` exists, load it for pre-analysis calibration corrections
in Phase C. If it does not exist yet, Phase E will create it after the first resolutions.

---

## Trading Cycle

### Phase A: Check Positions
<!-- OPERATOR-SET -->
Review all open positions for sell signals, resolved markets, and thesis changes.

1. Run: `python tools/get_portfolio.py --include-risk --pretty`
2. Run: `python tools/check_resolved.py --pretty`
3. For resolved markets: load `.claude/skills/resolution-parser.md` and follow its framework
4. For positions needing sell evaluation: assess current thesis vs entry thesis
5. Execute sells via `python tools/sell_position.py` for positions with invalidated thesis or hit stop-loss

### Phase B: Find Opportunities
<!-- OPERATOR-SET -->
Discover and filter tradeable markets from Polymarket.

1. Run: `python tools/discover_markets.py --limit 50 --pretty`
2. Apply resolution filter: exclude markets resolving beyond 14 days (MAX_RESOLUTION_DAYS in config)
3. Apply sweet-spot filter: YES price between 0.10-0.85
4. Remove markets where we already hold positions (from Phase A portfolio)
5. Rank by volume_24h descending, take top 5-8 candidates
6. If fewer than 3 pass, relax price range to 0.05-0.95

### Phase C: Analyze Markets
<!-- OPERATOR-SET -->
Deep-dive each candidate market with web research and probability estimation.

1. Load `.claude/skills/evaluate-edge.md` and follow its framework for each candidate
2. Load `.claude/skills/calibration-check.md` to check for known biases in this category
3. For each market: search the web for Bull and Bear evidence, synthesize probability, calculate edge
4. Skip markets with |edge| < MIN_EDGE_THRESHOLD or confidence < 0.3
5. Record analysis to `state/cycles/{cycle_id}/analysis_{market_id}.json`

### Phase D: Size and Execute
<!-- OPERATOR-SET -->
Size positions and execute trades for markets with sufficient edge.

1. Load `.claude/skills/size-position.md` and follow its framework for each trade candidate
2. Check portfolio capacity: remaining exposure vs 30% bankroll limit
3. Calculate Kelly-adjusted, confidence-weighted position sizes
4. Cap each position at 5% of bankroll (core principle)
5. Execute via: `python tools/execute_trade.py --market-id {id} --token-id {token} --side {side} --size {size} --price {price} --estimated-prob {prob} --edge {edge} --reasoning "{reason}" --category "{cat}" --pretty`
6. Record results to `state/cycles/{cycle_id}/execution_results.json`

### Phase E: Learn and Evolve
<!-- OPERATOR-SET -->
Analyze outcomes, update calibration, write cycle report, evolve strategy.

1. Load `.claude/skills/post-mortem.md` for any resolved positions from Phase A
2. Load `.claude/skills/calibration-check.md` to record outcomes and update calibration data
   - For each resolved position, run: `python tools/record_outcome.py --market-id {id} --stated-prob {prob} --actual {WIN|LOSS} --category {cat} --pnl {pnl} --pretty`
   - Then interpret results using the calibration-check framework
3. Load `.claude/skills/cycle-review.md` to write the cycle report and update strategy
4. Write cycle report to `state/reports/cycle-{cycle_id}.md`
5. Update `state/strategy.md` with max 0-3 evidence-backed changes
6. If any post-mortem yielded a golden-rule candidate (loss > 2% bankroll OR 2+ repeated patterns): add to `knowledge/golden-rules.md` following its format. Max 3 new rules per cycle.
7. For each category traded this cycle: append a dated "Lessons Learned" entry to `knowledge/market-types/{category}.md` with observation and evidence
8. Log cycle summary: markets scanned, analyzed, traded, P&L impact

---

## Guardrails
<!-- OPERATOR-SET: Do not modify this section -->

### Safety
- Paper trading default -- never enable live without explicit user instruction
- Maximum 5% of bankroll on any single position
- Maximum 30% of bankroll in total open exposure
- Record every trade in database BEFORE confirming execution
- 5 consecutive losses -> 24-hour trading pause

### File Discipline
- NEVER modify: `.env`, `trading.db` (directly), `lib/config.py`, `state/core-principles.md`
- Cycle outputs go to `state/cycles/{cycle_id}/`
- Cycle reports go to `state/reports/cycle-{cycle_id}.md`
- All intermediate files kept for audit trail

### Self-Modification Rules
- Skill docs (`.claude/skills/*.md`): You MAY add examples, refine criteria, annotate decisions within `<!-- CLAUDE-EDITABLE -->` sections
- Strategy (`state/strategy.md`): You MAY update with evidence-backed changes (max 3 per cycle)
- CLAUDE.md: You MAY update `<!-- CLAUDE-EDITABLE -->` sections below with process improvements
- You MUST NOT modify `<!-- OPERATOR-SET -->` sections

---

## Process Notes
<!-- CLAUDE-EDITABLE: Claude may update this section based on trading experience -->

_No process notes yet. Claude will add observations about what works and what to improve as trading cycles accumulate._

---

## Error Handling
<!-- OPERATOR-SET -->

| Failure | Action |
|---------|--------|
| Portfolio check fails | Log warning, continue to Phase B |
| Market discovery fails | STOP cycle, skip to Phase E (write report) |
| Single market analysis fails | Skip that market, continue with others |
| Trade execution fails | Log error per trade, continue with remaining |
| Strategy update fails | Log error, cycle still complete |

Always complete Phase E (write cycle report) even if earlier phases failed.

---

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->
