# EDGAR Platform Self-Refinement System

## Overview

The self-refinement system enables the EDGAR platform to **automatically learn from extraction failures** and **improve extractors** over time.

## Problem Statement

From the Fortune 100 pipeline run:
- **3/10 DEF 14A extractions failed** (Amazon, Berkshire Hathaway, Exxon)
- **Tax extraction returning $0** for most companies

These failures occur because:
1. Companies use **different table headers** ("Named Executive Officers" vs. "Summary Compensation Table")
2. Companies have **non-standard table structures** (5 columns vs. 8 columns)
3. Companies use **alternative section labels** ("Current Tax Expense" vs. "Current:")

The platform needs to **detect these variations** and **adapt** automatically.

## Solution Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Extraction Pipeline                     │
│                    (Fortune 100 Run)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Failures detected
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  ExtractionFailure Records                  │
│  - Company, Form Type, HTML Sample                         │
│  - Error Message, Extractor Type                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Analyze HTML
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   ExtractorRefiner                          │
│                                                             │
│  1. Parse HTML with BeautifulSoup                          │
│  2. Search for compensation/tax tables                     │
│  3. Identify alternative patterns                          │
│  4. Score patterns by confidence                           │
│  5. Generate RefinementSuggestions                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ High-confidence patterns
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              RefinementSuggestions (JSON)                   │
│  - Pattern Type, Confidence, Reasoning                     │
│  - Current vs. Suggested Pattern                           │
│  - Example HTML                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Manual review
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 Extractor Code Updates                      │
│  (Developer applies high-confidence suggestions)           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Re-run pipeline
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Verification                             │
│  (Verify failures are now resolved)                        │
└─────────────────────────────────────────────────────────────┘
```

## Implementation

### File Structure

```
edgar/
├── src/edgar/refinement/
│   ├── __init__.py              # Exports
│   ├── refiner.py               # ExtractorRefiner class
│   └── README.md                # Module documentation
├── scripts/
│   └── refine_extractors.py    # CLI script
├── examples/
│   └── refinement_example.py   # Usage examples
├── tests/
│   └── test_refinement.py      # 12 tests (all passing)
└── docs/
    └── self_refinement.md       # This document
```

### Key Classes

#### ExtractionFailure

```python
@dataclass
class ExtractionFailure:
    company: Company
    form_type: str
    html_sample: str              # First 50KB
    error_message: str
    extractor_type: str
    filing_url: str = ""
```

#### RefinementSuggestion

```python
@dataclass
class RefinementSuggestion:
    pattern_type: str             # "table_header", "table_structure", etc.
    current_pattern: str
    suggested_pattern: str
    confidence: float             # 0.0-1.0
    example_html: str
    reasoning: str
    company_name: str = ""
```

#### ExtractorRefiner

```python
@dataclass(frozen=True)
class ExtractorRefiner:
    sec_client: SecEdgarClient
    min_confidence: float = 0.7

    async def analyze_failures(
        self,
        failures: list[ExtractionFailure],
    ) -> list[RefinementSuggestion]:
        """Analyze failures and generate suggestions."""
        ...

    def generate_refinement_report(
        self,
        suggestions: list[RefinementSuggestion],
    ) -> str:
        """Generate human-readable report."""
        ...
```

## Pattern Detection

### SCT (Summary Compensation Table)

**Detection Strategy:**

1. Find all `<table>` elements
2. Count compensation keywords in table text:
   - "compensation", "salary", "bonus", "stock", "award", "executive", "officer", "named", "neo", "pay", "total"
3. If ≥4 keywords found → likely SCT
4. Analyze why current patterns didn't match:
   - Extract actual header text
   - Analyze table structure (rows, columns, rowspan/colspan)
   - Generate suggestions

**Suggested Pattern Types:**

- `table_header`: Alternative header text
  - Example: "Named Executive Officers" instead of "Summary Compensation Table"
- `table_structure`: Non-standard column layout
  - Example: 5-column condensed format vs. 8-column standard

### Tax (Income Tax Expense)

**Detection Strategy:**

1. Find all `<table>` elements
2. Count tax keywords in table text:
   - "income tax", "provision for", "tax expense", "deferred tax", "current tax", "federal", "state", "foreign"
3. If ≥3 keywords found → likely tax table
4. Analyze structure:
   - Find year columns
   - Identify section headers
   - Map row structure

**Suggested Pattern Types:**

- `tax_table_structure`: Alternative row/column layout
- `tax_section_headers`: Alternative section labels
  - Example: "Current Tax Expense" instead of "Current:"

## Confidence Scoring

Suggestions include confidence scores (0.0-1.0):

| Confidence | Criteria                                      | Action                |
|-----------|-----------------------------------------------|-----------------------|
| 0.85-1.0  | ≥4 keywords, clear structure, consistent      | Apply immediately     |
| 0.70-0.84 | ≥3 keywords, valid structure                  | Review and apply      |
| 0.50-0.69 | ≥2 keywords, uncertain structure              | Review carefully      |
| 0.00-0.49 | Low keyword match, unclear structure          | Ignore                |

Default threshold: **0.7** (70% confidence)

## Usage

### CLI Script

```bash
# Analyze all failures (both SCT and Tax)
python scripts/refine_extractors.py

# Analyze SCT failures only
python scripts/refine_extractors.py --extractor sct

# Analyze specific companies
python scripts/refine_extractors.py --companies "Amazon.com Inc.,Berkshire Hathaway Inc."

# Increase confidence threshold
python scripts/refine_extractors.py --min-confidence 0.85
```

### Example Output

```
============================================================
EDGAR Self-Refinement: Analyzing Extraction Failures
============================================================

============================================================
Analyzing SCT Failures: 3 companies
============================================================

📄 Amazon.com Inc....
   ❌ Failed: Summary Compensation Table not found

📄 Berkshire Hathaway Inc....
   ❌ Failed: Summary Compensation Table not found

📄 Exxon Mobil Corporation...
   ❌ Failed: Summary Compensation Table not found

============================================================
Generating Refinement Suggestions
============================================================

✅ Generated 5 suggestions

================================================================================
EXTRACTOR REFINEMENT REPORT
================================================================================

Total Suggestions: 5

## Table Header
   Count: 3

   1. Company: Amazon.com Inc.
      Confidence: 0.85
      Current: summary compensation table
      Suggested: named executive officers compensation
      Reason: Table contains compensation data but uses alternative header...

💾 Saved 3 SCT suggestions to: output/refinements/sct_refinements.json
💾 Saved 2 Tax suggestions to: output/refinements/tax_refinements.json

============================================================
Refinement Analysis Complete
============================================================

Next Steps:
1. Review suggestions in output/refinements/
2. Manually apply high-confidence patterns to extractors
3. Re-run pipeline to verify improvements
4. Iterate as needed
```

## Workflow

### Step 1: Run Pipeline

```bash
python scripts/run_fortune100_pipeline.py
```

This generates results and identifies failures.

### Step 2: Analyze Failures

```bash
python scripts/refine_extractors.py
```

This:
- Fetches HTML for failed companies
- Searches for alternative patterns
- Generates suggestions with confidence scores
- Saves to `output/refinements/`

### Step 3: Review Suggestions

```bash
cat output/refinements/sct_refinements.json
```

Example suggestion:

```json
{
  "pattern_type": "table_header",
  "current_pattern": "summary compensation table",
  "suggested_pattern": "named executive officers",
  "confidence": 0.85,
  "reasoning": "Table contains compensation data but uses alternative header...",
  "company_name": "Amazon.com Inc."
}
```

### Step 4: Apply High-Confidence Suggestions

Update extractor code:

```python
# edgar/extractors/sct/extractor.py
def _find_sct_table(self, soup: BeautifulSoup) -> Tag | None:
    sct_patterns = [
        "summary compensation table",
        "summary of compensation",
        "named executive officers",  # ← ADD THIS
    ]
    ...
```

### Step 5: Verify Improvements

Re-run pipeline:

```bash
python scripts/run_fortune100_pipeline.py
```

Check if previously failed companies now succeed.

### Step 6: Iterate

Repeat cycle until extraction success rate is satisfactory.

## Testing

All refinement functionality is tested:

```bash
# Run all refinement tests (12 tests)
PYTHONPATH=src python3 -m pytest tests/test_refinement.py -v

# Test pattern detection
PYTHONPATH=src python3 -m pytest tests/test_refinement.py::test_analyze_sct_failure -v
PYTHONPATH=src python3 -m pytest tests/test_refinement.py::test_analyze_tax_failure -v

# Test confidence scoring
PYTHONPATH=src python3 -m pytest tests/test_refinement.py::test_refinement_suggestion_creation -v
```

All tests pass ✅

## Example Code

Run the interactive example:

```bash
PYTHONPATH=src python3 examples/refinement_example.py
```

This demonstrates:
- Creating extraction failure records
- Analyzing failures
- Generating suggestions
- Reviewing suggestions

## Benefits

### 1. **Automatic Pattern Discovery**

Instead of manually inspecting 100+ company filings, the system:
- Scans HTML automatically
- Identifies alternative patterns
- Ranks by confidence
- Surfaces high-value improvements

### 2. **Reduced Manual Work**

Developers don't need to:
- Manually download filings
- Inspect HTML in browser
- Guess at patterns
- Trial-and-error testing

### 3. **Continuous Improvement**

Each pipeline run:
- Identifies new failures
- Suggests new patterns
- Improves extraction coverage
- Reduces manual intervention over time

### 4. **Data-Driven Decisions**

Suggestions include:
- Confidence scores
- Example HTML
- Reasoning
- Company names

Developers can prioritize high-confidence, high-impact changes.

## Future Enhancements

### Phase 1: Automated Application (Future)

Currently, suggestions are saved for manual review. Future versions could:

1. **Auto-generate code patches** using AST manipulation
2. **Create feature branches** with suggested changes
3. **Run tests automatically** to verify improvements
4. **Submit PRs** for developer review

### Phase 2: Machine Learning (Future)

- **Pattern clustering**: Group similar failures across companies
- **Confidence calibration**: Learn from applied suggestions
- **Cross-company patterns**: Identify industry-specific patterns
- **Anomaly detection**: Flag unusual table structures

### Phase 3: Interactive UI (Future)

- **Web interface** for reviewing suggestions
- **Side-by-side comparison** of old vs. new patterns
- **A/B testing** of pattern alternatives
- **Feedback loop** to improve confidence scoring

## Metrics

### Current Implementation

- **12 unit tests** (all passing)
- **4 pattern types** supported (table_header, table_structure, tax_table_structure, tax_section_headers)
- **2 extractors** supported (SCT, Tax)
- **Confidence threshold**: 0.7 (70%)

### Expected Impact

Based on Fortune 100 run:

| Metric                  | Before | After (Expected) |
|------------------------|--------|------------------|
| SCT Success Rate       | 70%    | 90%+             |
| Tax Success Rate       | ~30%   | 80%+             |
| Manual Investigation   | Hours  | Minutes          |
| Pattern Discovery      | Manual | Automatic        |

## Conclusion

The self-refinement system enables the EDGAR platform to:

1. **Learn from failures** automatically
2. **Discover alternative patterns** without manual inspection
3. **Suggest improvements** with confidence scores
4. **Continuously improve** extraction accuracy

This creates a **virtuous cycle**:
- Run pipeline → Identify failures → Analyze patterns → Apply improvements → Re-run pipeline → Higher success rate

Over time, the platform becomes **more robust** and **self-healing**, requiring less manual intervention as it adapts to the diversity of SEC filing formats.

## References

- **Module**: `src/edgar/refinement/`
- **CLI**: `scripts/refine_extractors.py`
- **Example**: `examples/refinement_example.py`
- **Tests**: `tests/test_refinement.py`
- **Docs**: `src/edgar/refinement/README.md`
