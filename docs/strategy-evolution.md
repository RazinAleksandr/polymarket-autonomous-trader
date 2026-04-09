# Strategy Evolution

The agent builds its own trading strategy from scratch through autonomous learning.

## How It Works

After every trading cycle, the Reviewer and Strategy Updater agents analyze what happened and make evidence-backed changes. Over many cycles, the system develops a comprehensive playbook.

### Strategy Document

`state/strategy.md` -- The agent's evolving trading strategy. Starts minimal, grows with 4 domains:

1. **Market selection rules** -- What markets to trade and avoid
2. **Analysis approach** -- How to estimate probabilities
3. **Risk parameters** -- Position sizing and exposure rules
4. **Trade entry/exit rules** -- When to buy, hold, and sell

Max 3 changes per cycle to prevent drift. Each change requires evidence (a specific trade outcome or pattern).

### Core Principles

`state/core-principles.md` -- Immutable guardrails set by the operator. The agent reads these every cycle but **never modifies them**:

- Paper trading default
- 5% max per position
- 30% max total exposure
- Record every trade before confirming
- 5 consecutive losses triggers 24-hour pause

## Knowledge Base

The `knowledge/` directory accumulates trading wisdom:

### golden-rules.md

Hard-won rules extracted from trading outcomes. A new rule is added when:
- A single loss exceeds 2% of bankroll, OR
- The same mistake pattern repeats 2+ times

Each rule has a trigger condition and evidence. Examples:
- "Check all options not just frontrunners" (learned from Oscars loss)
- "Settlement != intraday pricing" (learned from oil market)
- "Minimum 4pp edge, no exceptions"
- "Never bet at 97%+ (no edge left)"

Max 3 new rules per cycle. Rules are permanent -- once learned, always applied.

### calibration.json

Per-category probability calibration data:

```json
{
  "crypto": {"brier": 0.18, "error_pp": -5.2, "trades": 12},
  "politics": {"brier": 0.22, "error_pp": 8.1, "trades": 8},
  ...
}
```

- **error_pp < 0**: Overconfident (stated probability too high)
- **error_pp > 0**: Underconfident (stated probability too low)

Updated automatically by `tools/record_outcome.py` after each resolution. The Analyst agent reads this before estimating probabilities and applies corrections.

### market-types/

Category-specific playbooks with accumulated lessons:

```
knowledge/market-types/
  crypto.md
  politics.md
  sports.md
  commodities.md
  entertainment.md
  finance.md
```

Each file accumulates dated "Lessons Learned" entries with observations and evidence from actual trades.

## Calibration System

The calibration system tracks how accurate the agent's probability estimates are over time.

### Recording Outcomes

When a position resolves:

```bash
python tools/record_outcome.py \
  --market-id <ID> --stated-prob 0.75 --actual WIN \
  --category politics --pnl 12.50
```

This:
1. Computes Brier score for the prediction
2. Computes error in percentage points (stated_prob vs actual outcome)
3. Stores in `calibration_records` SQLite table
4. Regenerates `knowledge/calibration.json`

### Health Check

```python
from lib.calibration import get_calibration_health

health = get_calibration_health(store)
# {
#   "healthy": True,
#   "categories": {"crypto": -5.2, "politics": 8.1},
#   "worst_bias_pp": -5.2,
#   "failing_categories": []
# }
```

A category fails if its average bias exceeds -20pp (severe overconfidence). This is one of the 4 live trading gate criteria.

### Corrections

`lib/calibration.py:generate_corrections()` produces adjustment factors the Analyst applies before making new predictions. If the agent has been 15pp overconfident on crypto, the correction nudges future crypto estimates down.

## Skills

The `.claude/skills/` directory contains decision-making frameworks loaded on demand:

| Skill | When Loaded | Purpose |
|-------|------------|---------|
| `evaluate-edge.md` | Phase C (Analysis) | Edge calculation with calibration corrections |
| `calibration-check.md` | Phase C + E | Interpreting biases, applying corrections |
| `size-position.md` | Phase D (Sizing) | Kelly criterion, bankroll management |
| `post-mortem.md` | Phase E (Learning) | Analyzing resolved position outcomes |
| `cycle-review.md` | Phase E (Learning) | Writing cycle reports, updating strategy |
| `resolution-parser.md` | Phase A (Positions) | Interpreting market resolution events |

Skills have `<!-- CLAUDE-EDITABLE -->` sections that the agent can annotate with observations over time.
