# Testing Patterns

**Analysis Date:** 2026-04-02

## Test Framework

**Runner:**
- pytest 7.x+ (inferred from pytest.ini and test patterns)
- Config: `pytest.ini` at `/home/trader/polymarket-agent/pytest.ini`

**Assertion Library:**
- pytest built-in assertions
- pytest.approx() for floating-point comparisons (see `test_kelly.py`)

**Run Commands:**
```bash
cd /home/trader/polymarket-agent && source .venv/bin/activate
pytest                           # Run all tests
pytest tests/test_kelly.py       # Run specific test file
pytest -k test_positive_edge     # Run tests matching pattern
pytest --tb=short                # Short traceback format (configured in pytest.ini)
pytest -q                        # Quiet mode (configured in pytest.ini)
```

**Configuration:**
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -x -q --tb=short
```
- `-x`: Stop on first failure
- `-q`: Quiet output
- `--tb=short`: Short traceback format

## Test File Organization

**Location:**
- Tests in `tests/` directory (sibling to `lib/` and `tools/`)
- Co-located by purpose, not by module

**Naming:**
- Test files: `test_*.py` (e.g., `test_kelly.py`, `test_trading.py`, `test_market_data.py`)
- Test functions: `test_*` (e.g., `test_positive_edge`, `test_no_edge`)
- Test classes: `Test*` (e.g., `TestKellyCriterion`, `TestCalculateEdge`)

**Structure:**
```
tests/
├── conftest.py              # Shared fixtures
├── test_kelly.py            # lib/strategy.py tests
├── test_trading.py          # lib/trading.py tests
├── test_pricing.py          # lib/pricing.py tests
├── test_market_data.py      # lib/market_data.py tests
├── test_config.py           # lib/config.py tests
├── test_db.py               # lib/db.py tests
└── test_portfolio.py        # lib/portfolio.py tests
```

**Total Test Coverage:** ~3304 lines across test files (calculated: `wc -l tests/*.py`)

## Test Structure

**Suite Organization - Class-based:**

Most test files use class grouping by function/concern:

```python
class TestKellyCriterion:
    """Tests for kelly_criterion() function."""

    def test_positive_edge(self):
        """kelly_criterion with positive edge returns positive fraction."""
        result = kelly_criterion(0.60, 0.50, fraction=1.0)
        assert result > 0

    def test_no_edge(self):
        """kelly_criterion with no edge (prob == price) returns 0."""
        result = kelly_criterion(0.50, 0.50, fraction=1.0)
        assert result == 0.0
```

From `tests/test_kelly.py`:
- Classes group related tests: `TestKellyCriterion`, `TestCalculateEdge`, `TestCalculatePositionSize`
- Each test method is independent and focused on one behavior
- Docstrings describe the test scenario in human-readable form

**Setup & Teardown - Fixtures:**

Fixtures in `conftest.py` handle setup/teardown:

```python
@pytest.fixture
def tmp_db_path():
    """Provide a temporary database file path, cleaned up after test."""
    path = tempfile.mktemp(suffix=".db")
    yield path
    if os.path.exists(path):
        os.remove(path)

@pytest.fixture
def test_config(tmp_db_path, tmp_log_path):
    """Create a Config with temporary file paths for testing."""
    return Config(db_path=tmp_db_path, log_file=tmp_log_path, paper_trading=True)

@pytest.fixture
def store(tmp_db_path):
    """Create a DataStore with a temporary database, closed after test."""
    ds = DataStore(db_path=tmp_db_path)
    yield ds
    ds.close()
```

**Assertions:**

Simple, specific assertions:
- Direct comparison: `assert result == 0.0`
- Inequality: `assert result > 0`
- Approximate floating-point: `assert result == pytest.approx(0.15)`
- Membership: `assert "error message" in result`
- Type/existence: `assert market is not None`

## Mocking

**Framework:** `unittest.mock` (built-in)

**Patterns:**

1. **Mocking functions:**
   ```python
   @patch("lib.pricing.ClobClient")
   def test_get_fill_price_buy(mock_clob_cls):
       mock_client = MagicMock()
       mock_client.get_price.return_value = {"price": "0.65"}
       mock_clob_cls.return_value = mock_client
       
       price = get_fill_price(FAKE_TOKEN, "BUY", FAKE_HOST)
       assert price == 0.65
   ```
   - `@patch()` replaces the target at test time
   - `MagicMock()` creates a mock object with arbitrary methods
   - `return_value` sets what the mock returns when called
   - `assert_called_once_with()` verifies the mock was called with correct args

2. **Mocking side effects (exceptions):**
   ```python
   @patch("lib.trading.get_fill_price")
   def test_paper_trade_fails_on_no_liquidity(mock_fill_price):
       mock_fill_price.side_effect = ValueError("No liquidity for BUY on token tok-1")
       store = MagicMock()

       with pytest.raises(ValueError, match="No liquidity"):
           execute_paper_trade(...)
   ```
   - `side_effect` makes the mock raise an exception

3. **Verifying mock calls:**
   ```python
   mock_client.get_price.assert_called_once_with(FAKE_TOKEN, "SELL")
   store.record_trade.assert_called_once()
   ```

**What to Mock:**
- External APIs: `requests.get`, `ClobClient`
- Database: `DataStore` methods when testing logic that depends on DB
- Side effects: file I/O, network calls

**What NOT to Mock:**
- Pure logic functions: `kelly_criterion()`, `calculate_edge()`
- Dataclass creation: `Market(...)`, `TradeSignal(...)`
- Simple getters/setters
- Configuration loading (use fixture instead)

## Fixtures and Factories

**Test Data Patterns:**

1. **Factory functions for test data:**
   ```python
   def _make_raw_market(**overrides) -> dict:
       """Create a raw Gamma API market dict with sensible defaults."""
       base = {
           "id": "12345",
           "conditionId": "0xcondition123",
           "question": "Will X happen?",
           # ... more fields
       }
       base.update(overrides)
       return base

   def _make_market(**overrides) -> Market:
       """Create a Market dataclass with sensible defaults."""
       defaults = {
           "id": "12345",
           "condition_id": "0xcondition123",
           # ... more fields
       }
       defaults.update(overrides)
       return Market(**defaults)
   ```

   From `tests/test_market_data.py` — factories provide sensible defaults and allow override for specific test cases.

2. **Shared fixtures:**
   - `conftest.py` provides: `tmp_db_path`, `tmp_log_path`, `test_config`, `store`
   - Fixtures use `tempfile.mktemp()` for isolated, cleaned-up test artifacts

**Location:**
- Fixtures: `tests/conftest.py` (shared across all tests)
- Test data factories: within test files as helper functions (e.g., `_make_raw_market()`)

## Coverage

**Requirements:** No explicit coverage target enforced

**View Coverage:**
```bash
pip install pytest-cov
pytest --cov=lib --cov-report=html
# Open htmlcov/index.html
```

**Observational coverage:** Test files cover:
- Core business logic: `lib/strategy.py` (Kelly criterion, edge calculation)
- Data parsing: `lib/market_data.py` (Gamma API parsing, filtering)
- Execution: `lib/trading.py` (paper/live trade execution)
- Configuration: `lib/config.py` (env var + CLI override chain)
- Persistence: `lib/db.py` (SQLite CRUD operations)
- Pricing: `lib/pricing.py` (CLOB pricing with side semantics)

## Test Types

**Unit Tests (Primary):**
- Scope: Single function or method in isolation
- Approach: Mock external dependencies, test logic path by path
- Example: `test_kelly.py` tests Kelly criterion math with various inputs (positive edge, no edge, negative edge, boundaries)
- Focus: Input → Output behavior, not integration

**Integration Tests (Secondary):**
- Scope: Multiple modules working together
- Approach: Real fixtures where practical (e.g., real DataStore with temp DB)
- Example: `test_trading.py` tests trade execution with mocked CLOB but real DB writes
- Pattern: Use `store` fixture to test actual data flow through SQLite

**E2E Tests (Not used):**
- No end-to-end tests in codebase
- Would require running actual Polymarket API and wallet — not practical in CI

## Common Patterns

**Async Testing:**
Not used — all code is synchronous

**Error Testing:**
```python
def test_paper_trade_fails_on_no_liquidity(mock_fill_price):
    """Paper trade fails when CLOB API is unreachable."""
    mock_fill_price.side_effect = ValueError("No liquidity for BUY on token tok-1")
    store = MagicMock()

    with pytest.raises(ValueError, match="No liquidity"):
        execute_paper_trade(
            market_id="mkt-3",
            # ... args
        )
```

**Floating-point Comparisons:**
```python
def test_edge_positive(self):
    """Positive edge when estimated prob > market price."""
    result = calculate_edge(0.65, 0.50)
    assert result == pytest.approx(0.15)

# For tighter tolerance:
assert result == pytest.approx(0.166667, abs=1e-5)
```

**Boolean/Tuple Return Testing:**
```python
def test_validate_order_valid():
    """Valid order: notional 10.0 >= 5.0 minimum."""
    valid, msg = validate_order(0.50, 20.0, 5.0)
    assert valid is True
    assert msg == ""

def test_validate_order_minimum():
    """Order notional 0.20 below 5 USDC minimum."""
    valid, msg = validate_order(0.10, 2.0, 5.0)
    assert valid is False
    assert "below minimum" in msg
```

**Boundary & Edge Case Testing:**
```python
def test_boundary_zero_price(self):
    """kelly_criterion returns 0 when price is 0."""
    result = kelly_criterion(0.60, 0.0)
    assert result == 0.0

def test_boundary_price_at_one(self):
    """kelly_criterion returns 0 when price is 1.0."""
    result = kelly_criterion(0.60, 1.0)
    assert result == 0.0

def test_position_size_respects_bankroll(self):
    """Position size does not exceed available bankroll."""
    result = calculate_position_size(
        0.90, 0.50, bankroll=30.0,
        kelly_fraction=1.0, max_position_usdc=100.0,
    )
    assert result["size_usdc"] <= 30.0
```

**Exact Math Verification:**
```python
def test_full_kelly_math(self):
    """Verify the exact Kelly math: (b*p - q) / b where b=(1-price)/price."""
    prob = 0.70
    price = 0.50
    b = (1 - price) / price  # net odds = 1.0
    q = 1 - prob  # 0.30
    expected = (b * prob - q) / b  # (0.70 - 0.30) / 1.0 = 0.40
    result = kelly_criterion(prob, price, fraction=1.0)
    assert result == pytest.approx(expected)
```

## Test Execution Notes

**No test parametrization found:**
- Each test case is separate function/method
- Values are hardcoded in each test

**No fixtures for state cleanup across test classes:**
- `monkeypatch` used in `test_config.py` to manage environment variables
- Temp files cleaned up by fixture teardown (`yield` pattern)

**Frontend Testing (Vibe-Trading):**
- No test files found
- No testing framework configured
- No vitest.config or jest.config present
- Components are untested

---

*Testing analysis: 2026-04-02*
