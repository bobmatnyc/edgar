# Meta-Extractor API Reference

**Package**: `edgar_analyzer.extractors`
**Version**: 1.0.0 (Phase 4 Complete)
**Status**: Production Ready

## Table of Contents

- [MetaExtractor](#metaextractor) - End-to-end orchestrator
- [ExtractorRegistry](#extractorregistry) - Dynamic loading and registration
- [ExtractorSynthesizer](#extractorsynthesizer) - Pattern analysis and code generation
- [SelfImprovementLoop](#selfimprovementloop) - Iterative refinement (Phase 4)
- [FailureAnalyzer](#failureanalyzer) - Failure categorization (Phase 4)
- [CLI Commands](#cli-commands) - Command-line interface
- [Data Models](#data-models) - Pydantic models and types

---

## MetaExtractor

**Module**: `edgar_analyzer.extractors.meta_extractor`

End-to-end orchestrator for generating extractors from examples.

### Class: `MetaExtractor`

Coordinates the full pipeline: analyze → generate → validate → deploy → register

#### Constructor

```python
from edgar_analyzer.extractors.meta_extractor import MetaExtractor

meta = MetaExtractor(
    output_base_dir: Optional[Path] = None,
    templates_dir: Optional[Path] = None,
    auto_validate: bool = True
)
```

**Parameters**:
- `output_base_dir` (Path, optional) - Base directory for generated extractors. Default: `src/edgar_analyzer/extractors/`
- `templates_dir` (Path, optional) - Jinja2 templates directory. Default: `src/edgar_analyzer/extractors/templates/`
- `auto_validate` (bool) - Automatically validate generated code. Default: `True`

#### Methods

##### `create()`

Create a new extractor from examples.

```python
result: CreateResult = meta.create(
    name: str,
    examples_dir: Path,
    description: str = "",
    domain: Optional[str] = None,
    auto_register: bool = True,
    skip_validation: bool = False
)
```

**Parameters**:
- `name` (str) - Extractor name (e.g., "sct_extractor")
- `examples_dir` (Path) - Directory containing example JSON files
- `description` (str) - Human-readable description
- `domain` (str, optional) - Domain slug (defaults to name without "_extractor")
- `auto_register` (bool) - Automatically register in ExtractorRegistry. Default: `True`
- `skip_validation` (bool) - Skip code validation (not recommended). Default: `False`

**Returns**: `CreateResult` dataclass with:
- `status` (str) - "success", "validation_failed", "deployment_failed", or "error"
- `name` (str) - Extractor name
- `domain` (str) - Domain slug
- `analysis` (PatternAnalysis) - Pattern analysis results
- `extractor` (GeneratedExtractor) - Generated code
- `validation` (ValidationResult) - Validation results
- `deployment` (DeploymentResult) - Deployment results
- `total_time_seconds` (float) - Total execution time
- `files_created` (List[Path]) - List of created files
- `error_message` (str, optional) - Error message if failed
- `error_stage` (str, optional) - Pipeline stage where error occurred

**Example**:
```python
from pathlib import Path
from edgar_analyzer.extractors.meta_extractor import MetaExtractor

meta = MetaExtractor()
result = meta.create(
    name="sct_extractor",
    examples_dir=Path("examples/sct/"),
    description="Extract Summary Compensation Table from SEC proxy filings",
    domain="sct"
)

if result.status == "success":
    print(f"✅ Created: {result.deployment.extractor_path}")
    print(f"   Confidence: {result.analysis.confidence:.1%}")
    print(f"   Time: {result.total_time_seconds:.2f}s")
else:
    print(f"❌ Failed at stage: {result.error_stage}")
    print(f"   Error: {result.error_message}")
```

##### `validate_code()`

Validate generated extractor code.

```python
validation: ValidationResult = meta.validate_code(
    extractor: GeneratedExtractor
)
```

**Parameters**:
- `extractor` (GeneratedExtractor) - Generated extractor to validate

**Returns**: `ValidationResult` with:
- `valid` (bool) - Overall validation status
- `syntax_valid` (bool) - Python syntax check
- `interface_valid` (bool) - IDataExtractor interface compliance
- `imports_valid` (bool) - All imports resolvable
- `tests_valid` (bool) - Unit tests valid
- `errors` (List[str]) - Critical errors
- `warnings` (List[str]) - Non-critical warnings

**Example**:
```python
validation = meta.validate_code(extractor)

if not validation.valid:
    print("Validation errors:")
    for error in validation.errors:
        print(f"  ❌ {error}")

if validation.warnings:
    print("Warnings:")
    for warning in validation.warnings:
        print(f"  ⚠️  {warning}")
```

##### `deploy()`

Deploy generated extractor to file system.

```python
deployment: DeploymentResult = meta.deploy(
    extractor: GeneratedExtractor,
    output_dir: Path,
    auto_register: bool = True
)
```

**Parameters**:
- `extractor` (GeneratedExtractor) - Extractor to deploy
- `output_dir` (Path) - Deployment directory
- `auto_register` (bool) - Register in ExtractorRegistry after deployment

**Returns**: `DeploymentResult` with:
- `success` (bool) - Deployment status
- `extractor_path` (Path) - Path to deployed extractor
- `registered` (bool) - Whether registered in registry
- `registry_name` (str, optional) - Name in registry
- `error_message` (str, optional) - Error message if failed

---

## ExtractorRegistry

**Module**: `edgar_analyzer.extractors.registry`

Registry for dynamic extractor loading and metadata management.

### Class: `ExtractorRegistry`

Manages extractor registration, discovery, and dynamic loading.

#### Constructor

```python
from edgar_analyzer.extractors.registry import ExtractorRegistry

registry = ExtractorRegistry(
    registry_path: Optional[Path] = None
)
```

**Parameters**:
- `registry_path` (Path, optional) - Path to registry JSON file. Default: `data/extractors/registry.json`

#### Methods

##### `register()`

Register a new extractor.

```python
registry.register(
    name: str,
    class_path: str,
    version: str,
    description: str,
    domain: str,
    confidence: float = 0.0,
    examples_count: int = 0,
    tags: List[str] = []
)
```

**Parameters**:
- `name` (str) - Unique extractor name (e.g., "sct_extractor")
- `class_path` (str) - Importable class path (e.g., "edgar_analyzer.extractors.sct.extractor.SCTExtractor")
- `version` (str) - Semantic version (e.g., "1.0.0")
- `description` (str) - Human-readable description
- `domain` (str) - Domain slug (e.g., "sct")
- `confidence` (float) - Pattern analysis confidence (0.0-1.0)
- `examples_count` (int) - Number of training examples
- `tags` (List[str]) - Searchable tags

**Example**:
```python
registry = ExtractorRegistry()
registry.register(
    name="sct_extractor",
    class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
    version="1.0.0",
    description="Extract Summary Compensation Table",
    domain="sct",
    confidence=0.94,
    examples_count=3,
    tags=["sec", "proxy", "compensation"]
)
```

##### `get()`

Load extractor class dynamically.

```python
extractor_class: Type[IDataExtractor] = registry.get(name: str)
```

**Parameters**:
- `name` (str) - Registered extractor name

**Returns**: Extractor class (not instance)

**Raises**:
- `KeyError` - Extractor not found in registry
- `ImportError` - Failed to import extractor class

**Example**:
```python
# Get class
SCTExtractor = registry.get("sct_extractor")

# Instantiate
from edgar_analyzer.services.openrouter_client import OpenRouterClient
openrouter = OpenRouterClient()
extractor = SCTExtractor(openrouter_client=openrouter)

# Use
result = extractor.extract(input_data)
```

##### `list()`

List all registered extractors with optional filtering.

```python
extractors: List[ExtractorMetadata] = registry.list(
    domain: Optional[str] = None,
    min_confidence: float = 0.0,
    tags: Optional[List[str]] = None
)
```

**Parameters**:
- `domain` (str, optional) - Filter by domain
- `min_confidence` (float) - Minimum confidence threshold (0.0-1.0)
- `tags` (List[str], optional) - Filter by tags (AND logic)

**Returns**: List of `ExtractorMetadata` objects

**Example**:
```python
# List all extractors
all_extractors = registry.list()

# Filter by domain
sct_extractors = registry.list(domain="sct")

# Filter by confidence
high_confidence = registry.list(min_confidence=0.9)

# Filter by tags
sec_extractors = registry.list(tags=["sec", "proxy"])
```

##### `get_metadata()`

Get metadata for a registered extractor.

```python
metadata: ExtractorMetadata = registry.get_metadata(name: str)
```

**Parameters**:
- `name` (str) - Extractor name

**Returns**: `ExtractorMetadata` object

**Raises**:
- `KeyError` - Extractor not found

**Example**:
```python
metadata = registry.get_metadata("sct_extractor")
print(f"Confidence: {metadata.confidence:.1%}")
print(f"Created: {metadata.created_at}")
```

##### `unregister()`

Remove extractor from registry.

```python
registry.unregister(name: str)
```

**Parameters**:
- `name` (str) - Extractor name to remove

**Example**:
```python
registry.unregister("old_extractor")
```

##### `update()`

Update extractor metadata.

```python
registry.update(
    name: str,
    **kwargs  # Any ExtractorMetadata fields
)
```

**Parameters**:
- `name` (str) - Extractor name
- `**kwargs` - Fields to update (version, description, confidence, etc.)

**Example**:
```python
registry.update(
    "sct_extractor",
    version="1.1.0",
    confidence=0.96,
    description="Updated description"
)
```

---

## ExtractorSynthesizer

**Module**: `edgar_analyzer.extractors.synthesizer`

Pattern analysis and code generation from examples.

### Class: `ExtractorSynthesizer`

Analyzes examples to detect patterns, then generates extractor code using Jinja2 templates.

#### Constructor

```python
from edgar_analyzer.extractors.synthesizer import ExtractorSynthesizer

synthesizer = ExtractorSynthesizer(
    templates_dir: Optional[Path] = None
)
```

**Parameters**:
- `templates_dir` (Path, optional) - Jinja2 templates directory. Default: `src/edgar_analyzer/extractors/templates/`

#### Methods

##### `analyze()`

Analyze examples to detect transformation patterns.

```python
analysis: PatternAnalysis = synthesizer.analyze(
    name: str,
    examples: List[Dict[str, Any]],
    description: str = "",
    domain: Optional[str] = None
)
```

**Parameters**:
- `name` (str) - Extractor name
- `examples` (List[Dict]) - List of input/output example pairs
- `description` (str) - Human-readable description
- `domain` (str, optional) - Domain slug

**Returns**: `PatternAnalysis` with:
- `name` (str) - Extractor name
- `domain` (str) - Domain slug
- `description` (str) - Description
- `input_schema` (Dict) - Detected input structure
- `output_schema` (Dict) - Detected output structure
- `patterns` (List[Dict]) - Transformation patterns
- `confidence` (float) - Pattern detection confidence (0.0-1.0)
- `examples_count` (int) - Number of examples analyzed
- `heading_patterns` (List[str]) - HTML heading patterns
- `table_validation_rules` (Dict) - Table validation rules
- `system_prompt` (str) - LLM system prompt
- `parsing_rules` (List[str]) - LLM parsing instructions

**Example**:
```python
examples = [
    {
        "input": {"html": "<table>...</table>"},
        "output": {"records": [...]}
    },
    # More examples...
]

analysis = synthesizer.analyze(
    name="sct_extractor",
    examples=examples,
    description="Extract Summary Compensation Table",
    domain="sct"
)

print(f"Confidence: {analysis.confidence:.1%}")
print(f"Patterns detected: {len(analysis.patterns)}")
```

##### `synthesize()`

Generate extractor code from pattern analysis.

```python
extractor: GeneratedExtractor = synthesizer.synthesize(
    analysis: PatternAnalysis
)
```

**Parameters**:
- `analysis` (PatternAnalysis) - Results from `analyze()`

**Returns**: `GeneratedExtractor` with:
- `name` (str) - Extractor name
- `domain` (str) - Domain slug
- `extractor_code` (str) - Main extractor class code
- `models_code` (str) - Pydantic models code
- `prompts_code` (str) - LLM prompts code
- `tests_code` (str) - Unit tests code
- `init_code` (str) - Package `__init__.py`
- `metadata` (Dict) - Package metadata

**Example**:
```python
extractor = synthesizer.synthesize(analysis)

# Preview generated code
print("=== Extractor Class ===")
print(extractor.extractor_code[:500])

print("\n=== Models ===")
print(extractor.models_code[:500])
```

##### `write()`

Write generated extractor to disk.

```python
output_dir: Path = synthesizer.write(
    extractor: GeneratedExtractor,
    output_dir: Path
)
```

**Parameters**:
- `extractor` (GeneratedExtractor) - Generated extractor
- `output_dir` (Path) - Target directory

**Returns**: Path to written extractor directory

**Example**:
```python
output = synthesizer.write(
    extractor,
    output_dir=Path("src/edgar_analyzer/extractors/sct")
)
print(f"Written to: {output}")
```

##### `load_examples()`

Load examples from directory.

```python
examples: List[Dict[str, Any]] = synthesizer.load_examples(
    examples_dir: Path
)
```

**Parameters**:
- `examples_dir` (Path) - Directory containing `*.json` example files

**Returns**: List of example dicts with `input` and `output` keys

**Raises**:
- `FileNotFoundError` - Examples directory not found
- `ValueError` - Invalid example format

**Example**:
```python
examples = synthesizer.load_examples(Path("examples/sct/"))
print(f"Loaded {len(examples)} examples")
```

---

## SelfImprovementLoop

**Module**: `edgar_analyzer.extractors.self_improvement`

Iterative refinement system for improving extractor accuracy (Phase 4).

### Class: `SelfImprovementLoop`

Evaluates extractor performance, analyzes failures, and refines prompts/templates.

#### Constructor

```python
from edgar_analyzer.extractors.self_improvement import SelfImprovementLoop

loop = SelfImprovementLoop(
    meta_extractor: MetaExtractor,
    max_iterations: int = 5,
    target_accuracy: float = 0.90,
    min_improvement: float = 0.05
)
```

**Parameters**:
- `meta_extractor` (MetaExtractor) - MetaExtractor instance for regeneration
- `max_iterations` (int) - Maximum refinement iterations. Default: 5
- `target_accuracy` (float) - Target accuracy to achieve (0.0-1.0). Default: 0.90
- `min_improvement` (float) - Minimum accuracy improvement per iteration. Default: 0.05

#### Methods

##### `run()`

Run improvement loop on test cases.

```python
result: ImprovementResult = await loop.run(
    extractor_name: str,
    test_cases: List[TestCase],
    examples_dir: Path
)
```

**Parameters**:
- `extractor_name` (str) - Name of extractor to improve
- `test_cases` (List[TestCase]) - Test cases for evaluation
- `examples_dir` (Path) - Original examples directory

**Returns**: `ImprovementResult` with:
- `success` (bool) - Whether target accuracy achieved
- `initial_accuracy` (float) - Starting accuracy
- `final_accuracy` (float) - Ending accuracy
- `iterations` (int) - Number of iterations run
- `improvement_history` (List[Dict]) - Accuracy per iteration
- `final_version` (str) - Final extractor version
- `total_time_seconds` (float) - Total execution time

**Example**:
```python
from edgar_analyzer.extractors.self_improvement import SelfImprovementLoop, TestCase

test_cases = [
    TestCase(
        input={"html": "<table>...</table>"},
        expected_output={"records": [...]},
        description="Typical case"
    ),
    # More test cases...
]

loop = SelfImprovementLoop(meta_extractor)
result = await loop.run(
    extractor_name="sct_extractor",
    test_cases=test_cases,
    examples_dir=Path("examples/sct/")
)

print(f"Improved: {result.initial_accuracy:.1%} → {result.final_accuracy:.1%}")
print(f"Iterations: {result.iterations}")
```

##### `evaluate()`

Evaluate extractor on test cases.

```python
eval_result: EvaluationResult = await loop.evaluate(
    extractor_name: str,
    test_cases: List[TestCase]
)
```

**Parameters**:
- `extractor_name` (str) - Extractor to evaluate
- `test_cases` (List[TestCase]) - Test cases

**Returns**: `EvaluationResult` with:
- `accuracy` (float) - Success rate (0.0-1.0)
- `passed` (int) - Number of passed tests
- `failed` (int) - Number of failed tests
- `failures` (List[FailureAnalysis]) - Detailed failure analysis

---

## FailureAnalyzer

**Module**: `edgar_analyzer.extractors.failure_analyzer`

Analyzes extraction failures and categorizes them (Phase 4).

### Class: `FailureAnalyzer`

Categorizes failures and suggests improvements.

#### Methods

##### `analyze_failure()`

Analyze a single failure.

```python
from edgar_analyzer.extractors.failure_analyzer import FailureAnalyzer

analyzer = FailureAnalyzer()
failure: FailureAnalysis = analyzer.analyze_failure(
    test_case: TestCase,
    actual_output: Optional[Dict],
    exception: Optional[Exception]
)
```

**Parameters**:
- `test_case` (TestCase) - Failed test case
- `actual_output` (Dict, optional) - Actual output from extractor
- `exception` (Exception, optional) - Exception if raised

**Returns**: `FailureAnalysis` with:
- `failure_type` (FailureType) - PARSING_ERROR, VALIDATION_ERROR, MISSING_DATA, INCORRECT_TRANSFORMATION, or EXCEPTION
- `test_case` (TestCase) - Original test case
- `actual_output` (Dict, optional) - Actual output
- `error_message` (str) - Error description
- `missing_fields` (List[str]) - Missing required fields
- `incorrect_fields` (Dict) - Field mismatches

##### `suggest_improvements()`

Suggest improvements based on failures.

```python
suggestions: List[str] = analyzer.suggest_improvements(
    failures: List[FailureAnalysis]
)
```

**Parameters**:
- `failures` (List[FailureAnalysis]) - List of failures

**Returns**: List of improvement suggestions

---

## CLI Commands

### `edgar extractors create`

Create new extractor from examples.

```bash
edgar extractors create <name> --examples <dir> [OPTIONS]
```

**See**: [User Guide - CLI Commands](../../user/META_EXTRACTOR_USER_GUIDE.md#cli-command-reference)

### `edgar extractors list`

List registered extractors.

```bash
edgar extractors list [--domain <domain>] [--min-confidence <0.0-1.0>] [--format <table|json>]
```

### `edgar extractors info`

Show extractor details.

```bash
edgar extractors info <name>
```

### `edgar extractors validate`

Validate registered extractor.

```bash
edgar extractors validate <name>
```

---

## Data Models

### `ExtractorMetadata`

**Module**: `edgar_analyzer.extractors.registry`

```python
@dataclass
class ExtractorMetadata:
    name: str                    # Unique identifier
    class_path: str              # Importable class path
    version: str                 # Semantic version
    description: str             # Human-readable description
    domain: str                  # Domain slug
    confidence: float            # Pattern analysis confidence (0.0-1.0)
    examples_count: int          # Number of training examples
    tags: List[str]              # Searchable tags
    created_at: str              # ISO timestamp
    updated_at: str              # ISO timestamp
```

### `PatternAnalysis`

**Module**: `edgar_analyzer.extractors.synthesizer`

```python
@dataclass
class PatternAnalysis:
    name: str
    domain: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    patterns: List[Dict[str, Any]]
    confidence: float
    examples_count: int
    heading_patterns: List[str]
    table_validation_rules: Dict[str, Any]
    system_prompt: str
    parsing_rules: List[str]
```

### `GeneratedExtractor`

**Module**: `edgar_analyzer.extractors.synthesizer`

```python
@dataclass
class GeneratedExtractor:
    name: str
    domain: str
    extractor_code: str          # Main extractor class
    models_code: str             # Pydantic models
    prompts_code: str            # LLM prompts
    tests_code: str              # Unit tests
    init_code: str               # Package __init__.py
    metadata: Dict[str, Any]
```

### `CreateResult`

**Module**: `edgar_analyzer.extractors.meta_extractor`

```python
@dataclass
class CreateResult:
    status: str                  # "success", "validation_failed", "deployment_failed", "error"
    name: str
    domain: str
    analysis: Optional[PatternAnalysis]
    extractor: Optional[GeneratedExtractor]
    validation: Optional[ValidationResult]
    deployment: Optional[DeploymentResult]
    total_time_seconds: float
    files_created: List[Path]
    error_message: Optional[str]
    error_stage: Optional[str]
```

### `TestCase`

**Module**: `edgar_analyzer.extractors.self_improvement`

```python
@dataclass
class TestCase:
    input: Dict[str, Any]
    expected_output: Dict[str, Any]
    description: str = ""
```

### `FailureAnalysis`

**Module**: `edgar_analyzer.extractors.self_improvement`

```python
@dataclass
class FailureAnalysis:
    failure_type: FailureType
    test_case: TestCase
    actual_output: Optional[Dict[str, Any]]
    error_message: str
    missing_fields: List[str]
    incorrect_fields: Dict[str, tuple[Any, Any]]
```

---

## Integration with Platform Components

The Meta-Extractor system **reuses core platform components**:

### Schema Analysis

```python
from extract_transform_platform.services.analysis import SchemaAnalyzer, ExampleParser

# Used internally by ExtractorSynthesizer
schema_analyzer = SchemaAnalyzer()
example_parser = ExampleParser()
```

### Pattern Models

```python
from extract_transform_platform.models.patterns import Pattern, PatternType, FieldTypeEnum

# 14 pattern types supported:
# FIELD_MAPPING, CONCATENATION, TYPE_CONVERSION, BOOLEAN_CONVERSION,
# VALUE_MAPPING, FIELD_EXTRACTION, NESTED_ACCESS, LIST_AGGREGATION,
# CONDITIONAL, DATE_PARSING, MATH_OPERATION, STRING_FORMATTING,
# DEFAULT_VALUE, CUSTOM
```

### Data Extractor Interface

All generated extractors implement:

```python
from extract_transform_platform.core.base import IDataExtractor

class GeneratedExtractor(IDataExtractor):
    def extract(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from input."""
        pass
```

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Typical Time |
|-----------|------------|--------------|
| `analyze()` | O(n × m) | <1s for 3 examples with 50 fields |
| `synthesize()` | O(p) | <500ms for 10 patterns |
| `validate_code()` | O(c) | <200ms for 500 LOC |
| `registry.get()` | O(1) | <10ms (import cached) |
| `registry.list()` | O(n) | <50ms for 100 extractors |

Where:
- n = number of examples
- m = fields per example
- p = number of patterns
- c = lines of code

### Space Complexity

| Component | Complexity | Typical Size |
|-----------|------------|--------------|
| Registry JSON | O(n) | <50KB for 100 extractors |
| Pattern Analysis | O(f + p) | <10KB for 50 fields, 10 patterns |
| Generated Code | O(f) | <20KB for 50 fields |

---

## Thread Safety

- **ExtractorRegistry**: Not thread-safe (file writes use atomic rename)
- **MetaExtractor**: Thread-safe for read operations
- **ExtractorSynthesizer**: Thread-safe (stateless)
- **SelfImprovementLoop**: Not thread-safe (designed for sequential execution)

**Recommendation**: Use in single-threaded CLI context or add locking for concurrent access.

---

## Error Handling

All methods raise specific exceptions:

```python
try:
    result = meta.create(...)
    if result.status != "success":
        print(f"Error at {result.error_stage}: {result.error_message}")
except ValueError as e:
    print(f"Invalid input: {e}")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    logger.exception("Unexpected error", error=str(e))
```

---

## Next Steps

- **[User Guide](../../user/META_EXTRACTOR_USER_GUIDE.md)** - How to use the system
- **[Architecture](../architecture/META_EXTRACTOR_ARCHITECTURE.md)** - System design
- **[Troubleshooting](../../user/META_EXTRACTOR_TROUBLESHOOTING.md)** - Common issues
- **[Platform API](PLATFORM_API.md)** - Core platform components

---

**Built with the EDGAR Platform: From SEC filings to general-purpose data extraction.**
