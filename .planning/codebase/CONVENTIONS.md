# Coding Conventions

**Analysis Date:** 2026-04-02

## Naming Patterns

**Files:**
- All lowercase with underscores: `lib/market_data.py`, `tools/calculate_edge.py`, `tests/test_kelly.py`
- Purpose-driven: file names match their primary module responsibility
- Test files: `test_*.py` in `tests/` directory (e.g., `test_kelly.py`, `test_trading.py`, `test_pricing.py`)
- Tools/scripts: verb-noun pattern: `calculate_edge.py`, `execute_trade.py`, `get_portfolio.py`

**Functions & Methods:**
- Snake case throughout: `fetch_active_markets()`, `kelly_criterion()`, `calculate_edge()`, `execute_paper_trade()`
- Descriptive verb-noun: `record_trade()`, `upsert_position()`, `validate_order()`, `check_risk_limits()`
- Private functions prefixed with underscore: `_parse_market()`, `_passes_filters()`, `_evaluate_signal()`

**Variables & Parameters:**
- Snake case: `market_id`, `yes_price`, `kelly_fraction`, `bankroll`, `remaining_capital`
- Boolean flags: `paper_trading`, `is_paper`, `active`, `closed`
- Loop variables: Single letter for short-lived iterations: `m` (market), `t` (trade), `pos` (position), `c` (closed position)
- Config variables in CONSTANTS: `PAPER_TRADING`, `MIN_EDGE_THRESHOLD`, `MAX_POSITION_SIZE_USDC`, `OPENAI_API_KEY`

**Types & Classes:**
- Dataclasses for data models: `@dataclass` used for `Market`, `TradeSignal`, `OrderResult`, `MarketAnalysis`
- Class names: PascalCase (e.g., `DataStore`, `ClobClient`, `PortfolioManager`)
- Type hints on all function parameters and returns: `def kelly_criterion(prob: float, odds_price: float) -> float`
- Optional types: `Optional[ClobClient]`, `Market | None` (Python 3.12+ union syntax)
- Return type alternatives: `list[Market]`, `dict[str, float]`, `tuple[bool, str]`

**TypeScript/Frontend (Vibe-Trading):**
- camelCase for variables/functions: `sessionId`, `streamingText`, `addMessage()`, `setCachedSession()`
- CONSTANTS in camelCase: `SESSION_CACHE_MAX`
- React components: PascalCase: `<Home />`, `<Agent />`, `<Layout />`
- Type definitions: PascalCase with `Type` or `Interface` suffix: `AgentMessageType`, `AgentMessage`, `ToolCallEntry`
- Zustand store: `useAgentStore` (hook naming convention)

## Code Style

**Python:**
- No explicit formatter (Black/ruff) configured — follows PEP 8 manually
- Indentation: 4 spaces
- Line length: practical limit ~100 characters (observed in code)
- Import grouping: stdlib → third-party → local (with blank lines between groups)
  - Example from `lib/market_data.py`:
    ```python
    import json
    import requests
    from lib.logging_setup import get_logger
    from lib.models import Market
    ```
- Trailing commas in multi-line structures for consistency
- No linter config found (no `.pylintrc`, `.flake8`, etc.)

**TypeScript/Frontend:**
- No explicit formatter config (Prettier assumed)
- Indentation: 2 spaces (observed in Vibe-Trading)
- TypeScript strict mode assumed (see type annotations throughout)
- React functional components with hooks pattern
- Zustand for state management (reactive stores with create)
- Tailwind CSS for styling with utility classes

## Import Organization

**Python:**
1. Standard library: `import os`, `import sys`, `import json`
2. Third-party: `import requests`, `from py_clob_client import ...`
3. Local modules: `from lib.config import load_config`, `from lib.db import DataStore`

**TypeScript:**
1. React/framework imports: `import { create } from "zustand"`
2. Local types: `import type { AgentMessage } from "@/types/agent"`
3. Local components/stores: `import { useI18n } from "@/lib/i18n"`
- Path aliases used: `@/` maps to `src/`

## Error Handling

**Pattern:** Explicit error handling with logging and safe defaults

- **API failures:** Return empty list/None on error, log error, continue processing
  - `fetch_active_markets()` in `lib/market_data.py`: returns `[]` on API error
  - `fetch_market_by_id()`: returns `None` on error
- **Parsing failures:** Try-except with logging, skip invalid item, continue
  - `_parse_market()`: catches exceptions per item, returns `None` for invalid markets
- **Validation failures:** Return error tuple `(bool, str)` or raise with message
  - `validate_order(price, size)` returns `(False, error_message)` on validation failure
- **Database failures:** Log and continue (critical but non-blocking)
- **Live trade failures:** Log error, skip to next trade, record failure status
- **No exit() calls in library code** — only in CLI scripts via `error_exit()` function
  - `error_exit(message, code, exit_code)` in `lib/errors.py` writes JSON error to stderr

## Logging

**Framework:** Python `logging` module with dual formatters

**Output:**
- Console (stderr): human-readable with timestamp, level, module name
  - Format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- File: JSON format for machine parsing (`trading.log`)
  - Contains: `timestamp`, `level`, `module`, `message`, `data` (if provided)

**Levels:**
- **INFO:** Progress and cycle info — `log.info(f"Step 1: Discovering markets...")`
- **WARNING:** Non-blocking issues — `log.warning(f"Could not fetch market {signal.market_id}")`
- **ERROR:** Failures with fallback — `log.error(f"Market discovery failed: {e}")`

**Decision logging:** `log_decision(logger, decision_type, data)` in `lib/logging_setup.py`
- Structured decision logging with extra_data dict
- Example: `log_decision(log, "trade_signal", {"market_id": "...", "edge": 0.15, ...})`

**Frontend (TypeScript):** No explicit logging framework — uses console methods in development

## Comments

**When to comment:**
- Non-obvious algorithm explanation (e.g., Kelly criterion math in `lib/strategy.py`)
- Data format details: "Handle stringified JSON from Gamma API" in `lib/market_data.py`
- Workarounds and tricky logic: "Minimum $1 trade threshold" safety constraint
- Safety decisions: "SAFE-05: below minimum order size" (references design document)

**Docstrings:**
- Triple-quoted on all functions and classes
- Brief description first line
- Args section with parameter descriptions and types
- Returns section with return type and semantics
- Example from `lib/strategy.py`:
  ```python
  def kelly_criterion(prob: float, odds_price: float, fraction: float = 0.25) -> float:
      """Fractional Kelly criterion for binary outcome.

      Args:
          prob: Estimated true probability of winning (0.0-1.0).
          odds_price: Price per share -- payout is 1.0 on win (0.0-1.0).
          fraction: Kelly fraction for conservative sizing (0.25 = quarter Kelly).

      Returns:
          Fraction of bankroll to bet (0.0 if no edge or invalid price).
      """
  ```

## Function Design

**Parameters:**
- Positional for required params: `def kelly_criterion(prob: float, odds_price: float, ...)`
- Keyword-only config defaults: functions use `config.KELLY_FRACTION`, not passed as args
- Dataclass parameters preferred over many positional args
- Type hints on every parameter

**Return Values:**
- Single return type per function
- Dataclasses for multi-field returns: `TradeSignal`, `OrderResult`, `MarketAnalysis`
  - Example: `execute_paper_trade()` returns `OrderResult(order_id, success, message, is_paper)`
- None for side-effect-only functions: `record_trade()`, `upsert_position()`
- Tuples for (status, message) patterns: `(bool, str)` from `validate_order()`
- Safe defaults on error: `[]`, `None`, `{}`, `False`

**Size guidelines:**
- Functions typically 20-50 lines
- Larger functions (100+ lines) break data processing into sub-functions with underscore prefix
- Pure logic functions (strategy, pricing) are <30 lines for clarity

## Module Design

**Organization:**
- No subpackages; all `.py` files in `lib/`, tools in `tools/`, tests in `tests/`
- Each module focused on one responsibility:
  - `lib/market_data.py`: API calls to Gamma only
  - `lib/pricing.py`: CLOB pricing only
  - `lib/trading.py`: execution (paper/live) only
  - `lib/strategy.py`: signal generation (pure logic only)
  - `lib/db.py`: persistence layer only

**Exports:**
- Library modules export core functions/classes at module level
- Tools (CLI scripts) have `if __name__ == "__main__": main()` pattern
- Test modules import directly: `from lib.strategy import kelly_criterion`

**Dataclass Pattern:**
- Prefer dataclasses over dicts for data containers
- Use `.to_dict()` method when JSON serialization needed
  - Example in `lib/models.py`:
    ```python
    @dataclass
    class Market:
        id: str
        condition_id: str
        yes_price: float
        ...
        def to_dict(self) -> dict:
            return asdict(self)
    ```

**Initialization Pattern:**
- Database connections: `DataStore(db_path)` with `self.conn` and `_create_tables()`
- Logger per module: `log = get_logger("module_name")` at module level
- Config loading: `load_config(args)` with env var + CLI override chain

## Argument Parsing

**Pattern:** `argparse` with descriptive help text

- Required args: `required=True, dest="snake_case"`
- Optional args: default values provided
- Boolean flags: `action="store_true"`, `action="store_false"`
- Pretty-print JSON: `--pretty` flag present in most CLI tools
- Help text format: brief action description + type info

Example from `tools/execute_trade.py`:
```python
parser.add_argument(
    "--market-id",
    type=str,
    required=True,
    dest="market_id",
    help="Market ID",
)
```

## Configuration Management

**Pattern:** Environment variables + dataclass + CLI override chain

- Config loaded via `python-dotenv` from `.env` file
- Defaults in `Config` dataclass in `lib/config.py`
- Environment variable mapping: `_ENV_MAP` dict (UPPERCASE env → snake_case field)
- CLI args override env vars (lowest → highest priority: defaults → env → CLI)
- All config accessed via singleton: `config = load_config()`

## TypeScript/React Patterns

**Component structure:**
- Functional components with hooks
- Props interfaces defined above component
- Example from `Home.tsx`:
  ```typescript
  export function Home() {
    const { t } = useI18n();
    // render JSX
  }
  ```

**State management:**
- Zustand for global state (`useAgentStore`)
- Stores use create() factory with actions as methods
- State immutability: spread operators for updates

**Type safety:**
- All component props typed via interfaces
- Union types for limited values: `type AgentMessageType = "user" | "thinking" | ...`
- Record types for key-value collections: `Record<string, string>`

---

*Convention analysis: 2026-04-02*
