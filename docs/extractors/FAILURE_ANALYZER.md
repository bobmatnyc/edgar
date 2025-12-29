# FailureAnalyzer - Phase 4 Meta-Extractor

Deep analysis of extraction failures for systematic pattern detection and prompt refinement.

## Overview

The `FailureAnalyzer` class is part of the Phase 4 Meta-Extractor system, providing intelligent analysis of extraction failures to generate actionable refinement suggestions for improving extractor accuracy through iterative self-improvement.

## Architecture

### Core Components

1. **FailureAnalyzer** - Main analyzer class
2. **Data Models**:
   - `ExtractionFailure` - Single failure record
   - `FailurePattern` - Detected pattern in failures
   - `FailureAnalysisResult` - Complete analysis output
   - `Refinement` - Suggested improvement

### Integration

```
SelfImprovementLoop
    ├─→ evaluate()          # Generates FailureAnalysis objects
    ├─→ FailureAnalyzer     # ← Analyzes failures (NEW)
    │   ├─→ analyze()       # Detect patterns
    │   └─→ suggest_refinements()  # Generate fixes
    └─→ refine()            # Apply refinements
```

## Features

### 1. Failure Categorization

Categorizes failures by type:
- **PARSING_ERROR** - JSON/HTML parsing failures
- **VALIDATION_ERROR** - Schema validation failures
- **MISSING_DATA** - Required fields not extracted
- **INCORRECT_TRANSFORMATION** - Wrong values extracted
- **EXCEPTION** - Unhandled exceptions

### 2. Pattern Detection

Automatically detects systematic failure patterns:

| Pattern | Detection Criteria | Example |
|---------|-------------------|---------|
| **nested_object_parsing** | Nested structures + parse errors | Complex HTML tables |
| **currency_parsing** | Large numeric values (>1000) + missing/incorrect | "$95,000" → 95000.0 |
| **missing_field_X** | Field missing in >30% of failures | "salary" field consistently missing |
| **type_conversion** | Type mismatches between expected/actual | String "95000" instead of float 95000.0 |

### 3. Field-Level Statistics

Tracks per-field failure metrics:
```python
{
    "salary": {
        "missing_count": 3,       # Times field was missing
        "incorrect_count": 2,     # Times field had wrong value
        "total_failures": 5,      # Total failures for this field
        "failure_rate": 0.83      # 83% failure rate
    }
}
```

### 4. Refinement Suggestions

Generates prioritized, actionable refinements:

```python
Refinement(
    type=RefinementType.EXTRACTION_RULE,
    target="salary",
    suggestion="Add explicit extraction rule for 'salary' field",
    priority=RefinementPriority.HIGH,
    rationale="Field 'salary' missing in 60.0% of cases",
    affected_patterns=["missing_field_salary"]
)
```

#### Priority Levels

- **CRITICAL** (≥80% frequency) - Immediate attention required
- **HIGH** (50-80% frequency) - Significant impact
- **MEDIUM** (20-50% frequency) - Moderate impact
- **LOW** (<20% frequency) - Minor issue

## Usage

### Basic Usage

```python
from edgar_analyzer.extractors.failure_analyzer import FailureAnalyzer

# Initialize analyzer
analyzer = FailureAnalyzer(
    min_pattern_frequency=0.3,  # Detect patterns in 30%+ of failures
    min_field_failures=2        # Track fields failing 2+ times
)

# Analyze failures (from SelfImprovementLoop.evaluate)
analysis = analyzer.analyze(failures)

print(f"Total failures: {analysis.total_failures}")
print(f"Confidence: {analysis.confidence:.1%}")
print(f"Patterns detected: {len(analysis.patterns)}")

# Generate refinements
refinements = analyzer.suggest_refinements(analysis)

for refinement in refinements[:3]:  # Top 3 suggestions
    print(f"[{refinement.priority.value}] {refinement.suggestion}")
```

### Integration with SelfImprovementLoop

```python
from edgar_analyzer.extractors.self_improvement import SelfImprovementLoop
from edgar_analyzer.extractors.failure_analyzer import FailureAnalyzer

# Initialize components
loop = SelfImprovementLoop(meta_extractor)
analyzer = FailureAnalyzer()

# Evaluate extractor
eval_result = await loop.evaluate(extractor, test_cases)

# Analyze failures
if eval_result.failures:
    analysis = analyzer.analyze(eval_result.failures)

    # Get refinement suggestions
    refinements = analyzer.suggest_refinements(analysis)

    # Apply top refinements (manually or automatically)
    for refinement in refinements[:5]:
        # Apply refinement to extractor
        # ... (implementation specific)
```

### Complete Workflow Example

See `examples/failure_analyzer_demo.py` for a complete demonstration.

## Configuration

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_pattern_frequency` | 0.2 | Minimum frequency (0.0-1.0) to detect a pattern |
| `min_field_failures` | 2 | Minimum failures per field to track statistics |

### Thresholds

```python
# Strict pattern detection (only high-frequency patterns)
analyzer = FailureAnalyzer(
    min_pattern_frequency=0.5,  # 50%+ failures
    min_field_failures=3         # 3+ failures per field
)

# Sensitive pattern detection (catch more edge cases)
analyzer = FailureAnalyzer(
    min_pattern_frequency=0.1,  # 10%+ failures
    min_field_failures=1         # 1+ failures per field
)
```

## Performance

- **Time Complexity**: O(f × n) where f=failures, n=fields per failure
- **Space Complexity**: O(p) where p=unique patterns detected
- **Expected Performance**: <100ms for 50 failures with 20 fields each

### Benchmarks

| Failures | Fields/Failure | Analysis Time | Patterns Detected |
|----------|----------------|---------------|-------------------|
| 10 | 5 | ~10ms | 1-3 |
| 50 | 10 | ~50ms | 3-6 |
| 100 | 20 | ~120ms | 5-10 |

## Pattern Detection Logic

### 1. Nested Object Parsing

**Criteria**:
- Expected output has nested dicts/lists
- Failure type is `PARSING_ERROR`
- Error message contains "parse" or "json"

**Suggestion**: "Add explicit nested object handling to prompt with examples"

### 2. Currency Parsing

**Criteria**:
- Expected values contain large numbers (>1000)
- Failure type is `MISSING_DATA` or `INCORRECT_TRANSFORMATION`

**Suggestion**: "Add currency parsing examples (e.g., '$95,000' → 95000.0)"

### 3. Missing Field Pattern

**Criteria**:
- Specific field missing in ≥30% of failures
- Field fails at least 2 times

**Suggestion**: "Add explicit extraction rule for '{field_name}' field"

### 4. Type Conversion

**Criteria**:
- Expected and actual values have different types
- Failure type is `INCORRECT_TRANSFORMATION`

**Suggestion**: "Add type conversion examples to prompt (string → int, etc.)"

## Confidence Calculation

Confidence is calculated based on:

1. **Sample Size** (60% weight):
   - <5 failures: 0.5 confidence
   - 5-10 failures: 0.7 confidence
   - 10-20 failures: 0.85 confidence
   - >20 failures: 0.95 confidence

2. **Pattern Clarity** (40% weight):
   - Average frequency of detected patterns
   - Higher frequency = higher confidence

**Formula**: `confidence = 0.6 × size_confidence + 0.4 × pattern_confidence`

## Refinement Types

| Type | Target | When Used |
|------|--------|-----------|
| `PROMPT_ENHANCEMENT` | system_prompt | General prompt improvements |
| `PARSING_RULE` | parsing_rules | JSON/HTML parsing issues |
| `EXTRACTION_RULE` | field_name | Field-specific extraction issues |
| `VALIDATION_RULE` | output_schema | Schema validation issues |
| `EXAMPLE_ADDITION` | prompt_examples | Missing examples in prompt |
| `TEMPLATE_CHANGE` | code_template | Code template modifications |

## API Reference

### FailureAnalyzer

#### `__init__(min_pattern_frequency=0.2, min_field_failures=2)`

Initialize failure analyzer.

**Parameters**:
- `min_pattern_frequency` (float): Minimum frequency to detect pattern (0.0-1.0)
- `min_field_failures` (int): Minimum failures per field to track

#### `analyze(failures: List[FailureAnalysis]) -> FailureAnalysisResult`

Categorize and analyze extraction failures.

**Returns**: `FailureAnalysisResult` with:
- `total_failures` (int): Total number of failures
- `categories` (Dict[FailureType, int]): Failures by type
- `patterns` (List[FailurePattern]): Detected patterns
- `field_statistics` (Dict): Per-field failure stats
- `confidence` (float): Confidence in analysis (0.0-1.0)

#### `suggest_refinements(analysis: FailureAnalysisResult) -> List[Refinement]`

Generate refinement suggestions based on patterns.

**Returns**: List of `Refinement` objects sorted by priority

### Data Models

#### ExtractionFailure

```python
@dataclass
class ExtractionFailure:
    input: Dict[str, Any]              # Input data
    expected: Dict[str, Any]           # Expected output
    actual: Optional[Dict[str, Any]]   # Actual output (None if exception)
    error_message: str                 # Error description
    failure_type: FailureType          # Category of failure
    test_case_description: str = ""    # Test case description
```

#### FailurePattern

```python
@dataclass
class FailurePattern:
    name: str                          # Pattern name
    frequency: float                   # Occurrence rate (0.0-1.0)
    affected_fields: List[str]         # Fields affected
    failure_types: Set[FailureType]    # Failure types in pattern
    suggestion: str                    # Recommended fix
    examples: List[ExtractionFailure]  # Example failures
```

#### Refinement

```python
@dataclass
class Refinement:
    type: RefinementType               # Type of refinement
    target: str                        # What to modify
    suggestion: str                    # Specific suggestion
    priority: RefinementPriority       # Priority level
    rationale: str                     # Why this refinement
    affected_patterns: List[str]       # Patterns addressed
```

## Testing

### Unit Tests

```bash
# Run all FailureAnalyzer tests
python3 -m pytest tests/extractors/test_failure_analyzer.py -v

# Run with coverage
python3 -m pytest tests/extractors/test_failure_analyzer.py --cov=src/edgar_analyzer/extractors/failure_analyzer
```

### Test Coverage

- **29 unit tests** covering:
  - Pattern detection (nested objects, currency, type conversion, missing fields)
  - Failure categorization
  - Refinement generation
  - Priority mapping
  - Edge cases (empty failures, single failure type, etc.)
  - Integration with SelfImprovementLoop

### Demo

```bash
# Run interactive demo
python3 examples/failure_analyzer_demo.py
```

## Best Practices

### 1. Configure Thresholds Based on Use Case

```python
# Production: High-confidence patterns only
analyzer = FailureAnalyzer(
    min_pattern_frequency=0.5,  # 50%+ failures
    min_field_failures=3         # 3+ failures
)

# Development: Catch all patterns for debugging
analyzer = FailureAnalyzer(
    min_pattern_frequency=0.1,  # 10%+ failures
    min_field_failures=1         # 1+ failures
)
```

### 2. Prioritize High-Impact Refinements

```python
refinements = analyzer.suggest_refinements(analysis)

# Apply only critical and high priority
critical_refinements = [
    r for r in refinements
    if r.priority in [RefinementPriority.CRITICAL, RefinementPriority.HIGH]
]
```

### 3. Track Refinement Effectiveness

```python
# Before refinement
before_analysis = analyzer.analyze(failures_before)

# After refinement
after_analysis = analyzer.analyze(failures_after)

# Compare
improvement = before_analysis.total_failures - after_analysis.total_failures
print(f"Failures reduced by {improvement}")
```

### 4. Use Field Statistics for Targeted Fixes

```python
analysis = analyzer.analyze(failures)

# Find most problematic fields
problematic_fields = sorted(
    analysis.field_statistics.items(),
    key=lambda x: x[1]["failure_rate"],
    reverse=True
)[:3]

for field, stats in problematic_fields:
    print(f"{field}: {stats['failure_rate']:.1%} failure rate")
```

## Future Enhancements

1. **Machine Learning Integration**
   - Train ML model to predict failure patterns
   - Automatically suggest optimal refinements

2. **Pattern Library**
   - Build library of common patterns across extractors
   - Cross-extractor pattern reuse

3. **Automated Refinement Application**
   - Automatically apply refinements to extractors
   - A/B test refinement effectiveness

4. **Historical Analysis**
   - Track refinement effectiveness over time
   - Identify recurring failure patterns

5. **Custom Pattern Definitions**
   - Allow users to define custom patterns
   - Domain-specific pattern detection

## Related Documentation

- [SelfImprovementLoop](./SELF_IMPROVEMENT_LOOP.md) - Iterative refinement system
- [Meta-Extractor](./META_EXTRACTOR.md) - Overall architecture
- [Synthesizer](./SYNTHESIZER.md) - Code generation from patterns

## Changelog

### v1.0.0 (2025-12-07)

- Initial implementation
- Pattern detection for nested objects, currency, type conversion, missing fields
- Refinement suggestion generation
- Integration with SelfImprovementLoop
- Comprehensive unit tests (29 tests)
- Demo example included
