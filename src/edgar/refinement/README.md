# EDGAR Extractor Self-Refinement Module

Automatically analyze extraction failures and suggest improvements to extractors.

## Overview

The refinement module enables the EDGAR platform to **learn from failures** and **improve itself**:

1. **Analyze Failures**: Examine HTML from failed extractions
2. **Identify Patterns**: Find tables and structures that weren't detected
3. **Suggest Refinements**: Generate improvement suggestions with confidence scores
4. **Apply & Verify**: Update extractors and verify improvements

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Extraction Failures                     │
│  (Companies where extraction failed or returned zeros)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   ExtractorRefiner                          │
│                                                             │
│  1. Fetch HTML samples (first 50KB)                        │
│  2. Parse with BeautifulSoup                               │
│  3. Search for alternative table patterns                  │
│  4. Analyze why current patterns didn't match              │
│  5. Generate RefinementSuggestions                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              RefinementSuggestions (JSON)                   │
│                                                             │
│  - pattern_type: "table_header" | "table_structure"        │
│  - current_pattern: "summary compensation table"           │
│  - suggested_pattern: "named executive officers"           │
│  - confidence: 0.85                                         │
│  - reasoning: "Alternative header found in 3 companies"    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Manual Review & Application                    │
│  (Developer reviews suggestions and updates extractors)    │
└─────────────────────────────────────────────────────────────┘
```

## Data Structures

### ExtractionFailure

Records details of a failed extraction:

```python
@dataclass
class ExtractionFailure:
    company: Company                 # Company that failed
    form_type: str                   # "DEF 14A" or "10-K"
    html_sample: str                 # First 50KB for analysis
    error_message: str               # Exception message
    extractor_type: str              # "SCTExtractor" or "TaxExtractor"
    filing_url: str                  # URL for reference
```

### RefinementSuggestion

Suggested improvement with confidence score:

```python
@dataclass
class RefinementSuggestion:
    pattern_type: str                # Type of pattern (header, structure, etc.)
    current_pattern: str             # What we're currently looking for
    suggested_pattern: str           # Alternative pattern found
    confidence: float                # 0.0-1.0 confidence score
    example_html: str                # HTML snippet showing the pattern
    reasoning: str                   # Why this should work
    company_name: str                # Company where found
```

## Usage

### Command Line

```bash
# Analyze all failures
python scripts/refine_extractors.py

# Analyze SCT failures only
python scripts/refine_extractors.py --extractor sct

# Analyze Tax failures only
python scripts/refine_extractors.py --extractor tax

# Analyze specific companies
python scripts/refine_extractors.py --companies "Amazon.com Inc.,Berkshire Hathaway Inc."

# Adjust confidence threshold
python scripts/refine_extractors.py --min-confidence 0.8
```

### Programmatic API

```python
from edgar.refinement import ExtractorRefiner, ExtractionFailure
from edgar.services.sec_edgar_client import SecEdgarClient

# Initialize refiner
sec_client = SecEdgarClient()
refiner = ExtractorRefiner(sec_client=sec_client, min_confidence=0.7)

# Create failure record
failure = ExtractionFailure(
    company=company,
    form_type="DEF 14A",
    html_sample=html[:50_000],
    error_message="Summary Compensation Table not found",
    extractor_type="SCTExtractor",
)

# Analyze failures
suggestions = await refiner.analyze_failures([failure])

# Generate report
report = refiner.generate_refinement_report(suggestions)
print(report)
```

## Pattern Types

### SCT (Summary Compensation Table)

**Pattern Types:**

1. **table_header**: Alternative header text
   - Current: "summary compensation table"
   - Suggested: "named executive officers compensation"
   - Reason: Different companies use different terminology

2. **table_structure**: Non-standard column layout
   - Current: Standard 8-column SCT
   - Suggested: "5 columns: Salary, Stock, Non-Equity, Other, Total"
   - Reason: Some companies omit bonus/option columns

### Tax (Income Tax Expense)

**Pattern Types:**

1. **tax_table_structure**: Table layout variations
   - Current: "Standard current/deferred federal/state/foreign"
   - Suggested: Alternative row/column structure
   - Reason: Different formatting across companies

2. **tax_section_headers**: Section header variations
   - Current: "Current:" and "Deferred:" with colons
   - Suggested: "Current Tax Expense" and "Deferred Tax Benefit"
   - Reason: Some companies use full phrases instead of labels

## Confidence Scoring

Suggestions include confidence scores based on:

- **Keyword match count** (≥4 compensation keywords = high confidence)
- **Table structure validity** (proper rows/columns)
- **Pattern consistency** (seen across multiple companies)
- **Context relevance** (nearby text confirms purpose)

Default threshold: **0.7** (70% confidence)

## Output

Refinement suggestions are saved to:

```
output/refinements/
├── sct_refinements.json
└── tax_refinements.json
```

Each file contains:

```json
{
  "extractor": "edgar/extractors/sct/extractor.py",
  "suggestions_count": 3,
  "suggestions": [
    {
      "pattern_type": "table_header",
      "current_pattern": "summary compensation table",
      "suggested_pattern": "named executive officers",
      "confidence": 0.85,
      "reasoning": "Table contains compensation data but uses alternative header...",
      "company_name": "Amazon.com Inc."
    }
  ]
}
```

## Workflow

### Phase 1: Collect Failures

Run the Fortune 100 pipeline and identify failures:

```bash
# Run pipeline
python scripts/run_fortune100_pipeline.py

# Check results
cat output/fortune100_sct_results.csv
cat output/fortune100_tax_results.csv
```

### Phase 2: Analyze Failures

Run the refinement script:

```bash
python scripts/refine_extractors.py
```

This will:
- Fetch HTML for failed companies
- Search for alternative table patterns
- Generate suggestions with confidence scores
- Save to `output/refinements/`

### Phase 3: Review Suggestions

Review the JSON files and refinement report:

```bash
cat output/refinements/sct_refinements.json
cat output/refinements/tax_refinements.json
```

### Phase 4: Apply Improvements

Manually update extractors based on high-confidence suggestions:

```python
# In edgar/extractors/sct/extractor.py
def _find_sct_table(self, soup: BeautifulSoup) -> Tag | None:
    sct_patterns = [
        "summary compensation table",
        "summary of compensation",
        "named executive officers",  # ← Add suggested pattern
    ]
    ...
```

### Phase 5: Verify

Re-run the pipeline to verify improvements:

```bash
python scripts/run_fortune100_pipeline.py
```

## Testing

Run refinement module tests:

```bash
# All refinement tests
PYTHONPATH=src python3 -m pytest tests/test_refinement.py -v

# Specific test
PYTHONPATH=src python3 -m pytest tests/test_refinement.py::test_analyze_sct_failure -v
```

## Future Enhancements

### Automated Pattern Application

Currently, suggestions are saved for manual review. Future versions could:

1. **Auto-generate code patches** (using AST manipulation)
2. **Create feature branches** with suggested changes
3. **Run tests automatically** to verify improvements
4. **Submit PRs** for review

### Machine Learning Integration

- **Pattern clustering**: Group similar failures
- **Confidence calibration**: Learn from applied suggestions
- **Cross-company patterns**: Identify industry-specific patterns
- **Anomaly detection**: Flag unusual table structures

### Interactive Refinement

- **Web UI** for reviewing suggestions
- **Side-by-side comparison** of old vs. new patterns
- **A/B testing** of pattern alternatives
- **Feedback loop** to improve confidence scoring

## API Reference

### ExtractorRefiner

Main refinement class.

**Methods:**

- `analyze_failures(failures: list[ExtractionFailure]) -> list[RefinementSuggestion]`
  - Analyze failed extractions and generate suggestions

- `generate_refinement_report(suggestions: list[RefinementSuggestion]) -> str`
  - Generate human-readable report

- `apply_refinements(suggestions: list[RefinementSuggestion], extractor_path: Path) -> bool`
  - Save suggestions to JSON (manual application for now)

- `verify_refinement(company: Company, form_type: str, extractor: Any) -> bool`
  - Re-run extraction to verify fix

**Attributes:**

- `sec_client: SecEdgarClient` - API client
- `min_confidence: float` - Minimum confidence threshold (default: 0.7)

## Examples

### Example 1: Analyze SCT Failures

```python
# Analyze why Amazon, Berkshire, Exxon failed
failures = await analyze_sct_failures(
    refiner,
    registry,
    company_names=["Amazon.com Inc.", "Berkshire Hathaway Inc."]
)

# Generate suggestions
suggestions = await refiner.analyze_failures(failures)

# Print report
print(refiner.generate_refinement_report(suggestions))
```

### Example 2: Analyze Tax Zeros

```python
# Find companies returning $0 tax
failures = await analyze_tax_failures(refiner, registry)

# Filter high-confidence suggestions
high_confidence = [s for s in suggestions if s.confidence >= 0.85]

# Apply improvements
for suggestion in high_confidence:
    print(f"Pattern: {suggestion.suggested_pattern}")
    print(f"Reason: {suggestion.reasoning}")
```

## Contributing

When adding new pattern types:

1. Add to `_analyze_sct_failure()` or `_analyze_tax_failure()`
2. Define new `pattern_type` constant
3. Add confidence scoring logic
4. Update tests in `tests/test_refinement.py`
5. Document in this README
