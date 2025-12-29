# Fortune 100 Company Registry

A comprehensive registry of Fortune 100 companies with SEC EDGAR Central Index Keys (CIKs) for efficient lookup and filtering operations.

## Features

- **Immutable Data Structures**: Type-safe, frozen dataclasses prevent accidental mutations
- **Multiple Lookup Methods**: Search by CIK, ticker symbol, or Fortune 100 rank
- **Efficient Filtering**: Filter companies by industry sector
- **Range Queries**: Retrieve companies within a rank range (e.g., top 10, 50-100)
- **Validation**: Built-in validation ensures data integrity (unique ranks, unique CIKs, proper formatting)
- **Type Safety**: 100% type hints with strict mypy compliance

## Installation

The Fortune 100 registry is part of the EDGAR platform package:

```bash
pip install -e .  # From the project root
```

## Quick Start

```python
from edgar.data import Fortune100Registry

# Load the default Fortune 100 registry (2024 data)
registry = Fortune100Registry.load_default()

# Lookup by CIK
apple = registry.get_by_cik("0000320193")
print(f"{apple.name} - Rank #{apple.rank}")  # Apple Inc. - Rank #3

# Lookup by ticker (case-insensitive)
walmart = registry.get_by_ticker("WMT")
print(f"{walmart.name} - CIK: {walmart.cik}")  # Walmart Inc. - CIK: 0000104169

# Get top 10 companies
top_10 = registry.get_by_rank_range(1, 10)
for company in top_10:
    print(f"#{company.rank}: {company.name}")

# Filter by sector
tech_companies = registry.filter_by_sector("Technology")
print(f"Found {len(tech_companies)} technology companies")
```

## API Reference

### Company

Immutable dataclass representing a Fortune 100 company.

**Attributes:**
- `rank` (int): Fortune 100 rank (1-100)
- `name` (str): Official company name
- `ticker` (str): Stock ticker symbol
- `cik` (str): SEC CIK (10-digit, zero-padded)
- `sector` (str): Industry sector

**Example:**
```python
from edgar.data import Company

company = Company(
    rank=3,
    name="Apple Inc.",
    ticker="AAPL",
    cik="0000320193",
    sector="Technology"
)
```

### Fortune100Registry

Registry of Fortune 100 companies with efficient lookup operations.

**Attributes:**
- `companies` (tuple[Company, ...]): Immutable tuple of Company instances

**Methods:**

#### `get_by_cik(cik: str) -> Company | None`

Get company by SEC CIK number (normalized to 10 digits).

```python
company = registry.get_by_cik("0000320193")  # Returns Apple
company = registry.get_by_cik("320193")      # Also returns Apple (normalized)
```

#### `get_by_ticker(ticker: str) -> Company | None`

Get company by stock ticker symbol (case-insensitive).

```python
company = registry.get_by_ticker("AAPL")  # Returns Apple
company = registry.get_by_ticker("aapl")  # Also returns Apple
```

#### `get_by_rank(rank: int) -> Company | None`

Get company by Fortune 100 rank.

```python
company = registry.get_by_rank(1)  # Returns Walmart
```

#### `get_by_rank_range(start: int, end: int) -> list[Company]`

Get companies within a rank range (inclusive), sorted by rank.

```python
top_10 = registry.get_by_rank_range(1, 10)
middle = registry.get_by_rank_range(45, 55)
```

#### `filter_by_sector(sector: str) -> list[Company]`

Filter companies by industry sector (case-insensitive), sorted by rank.

```python
tech = registry.filter_by_sector("Technology")
healthcare = registry.filter_by_sector("Healthcare")
```

#### `get_all() -> list[Company]`

Get all companies sorted by Fortune 100 rank.

```python
all_companies = registry.get_all()
```

#### `load_default() -> Fortune100Registry` (classmethod)

Load Fortune 100 registry from default JSON file (`fortune100_2024.json`).

```python
registry = Fortune100Registry.load_default()
```

#### `from_json(json_path: Path | str) -> Fortune100Registry` (classmethod)

Load Fortune 100 registry from custom JSON file.

```python
registry = Fortune100Registry.from_json("path/to/custom.json")
```

## Data Format

The registry data is stored in JSON format:

```json
{
  "version": "2024",
  "source": "Fortune 500 2024 Rankings",
  "companies": [
    {
      "rank": 1,
      "name": "Walmart Inc.",
      "ticker": "WMT",
      "cik": "0000104169",
      "sector": "Retail"
    },
    ...
  ]
}
```

### Data Validation

The registry enforces strict validation rules:

- **Exactly 100 companies**: Registry must contain exactly 100 companies
- **Unique ranks**: All ranks must be unique and cover 1-100
- **Unique CIKs**: All CIKs must be unique
- **CIK format**: CIKs must be 10-digit, zero-padded strings containing only digits
- **Valid ranks**: Ranks must be between 1 and 100 (inclusive)

## Sectors

The Fortune 100 companies span multiple industry sectors:

- **Healthcare** (18 companies): UnitedHealth Group, CVS Health, McKesson, etc.
- **Financials** (12 companies): Berkshire Hathaway, JPMorgan Chase, Bank of America, etc.
- **Technology** (11 companies): Amazon, Apple, Alphabet, Microsoft, Meta, etc.
- **Retail** (10 companies): Walmart, Costco, Home Depot, Target, etc.
- **Energy** (10 companies): Exxon Mobil, Chevron, Marathon Petroleum, etc.
- **Insurance** (8 companies): State Farm, Progressive, Allstate, etc.
- **Transportation** (5 companies): UPS, FedEx, United Airlines, American Airlines, Delta, etc.
- **Consumer Goods** (5 companies): PepsiCo, Procter & Gamble, Philip Morris, Coca-Cola, Nike
- **Automotive** (4 companies): Ford, General Motors, Tesla, Stellantis
- **Telecommunications** (4 companies): Verizon, AT&T, Comcast, Charter Communications
- **Food & Agriculture** (4 companies): Archer Daniels Midland, Sysco, Performance Food, Tyson Foods
- **Industrial** (4 companies): Caterpillar, General Electric, Deere, Nucor
- **Aerospace** (3 companies): Boeing, Lockheed Martin, RTX
- **Media** (2 companies): Walt Disney, Netflix

## Examples

See `examples/fortune100_demo.py` for comprehensive usage examples.

Run the demo:

```bash
python examples/fortune100_demo.py
```

## Testing

Run the test suite:

```bash
pytest tests/unit/test_fortune100_registry.py -v
```

Test coverage includes:
- Company creation and validation
- Registry loading and validation
- All lookup methods (CIK, ticker, rank, range)
- Sector filtering
- Data integrity (unique ranks, unique CIKs, proper formatting)
- Case-insensitive operations
- Error handling
- Integration workflows

## Data Sources

The Fortune 100 data is based on the 2024 Fortune 500 rankings. CIK numbers are sourced from the SEC EDGAR database.

**References:**
- [Fortune 500 Rankings](https://fortune.com/fortune500/)
- [SEC EDGAR CIK Lookup](https://www.sec.gov/search-filings/cik-lookup)
- [SEC EDGAR Company Search](https://www.sec.gov/edgar/search/)

## License

Part of the EDGAR platform. See project LICENSE for details.
