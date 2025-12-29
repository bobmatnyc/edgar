# Meta-Extractor Architecture

**Version**: 1.0.0 (Phase 4 Complete)
**Status**: Production Ready

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Design Decisions](#design-decisions)
- [Pipeline Stages](#pipeline-stages)
- [Template System](#template-system)
- [Self-Improvement Loop (Phase 4)](#self-improvement-loop-phase-4)
- [Performance Characteristics](#performance-characteristics)
- [Security Considerations](#security-considerations)

---

## System Overview

The Meta-Extractor is an **example-driven code generation system** that automatically creates custom data extractors from 2-3 input/output examples.

### Key Capabilities

1. **Pattern Detection** - Analyzes examples to detect 14 transformation pattern types
2. **Code Generation** - Renders Jinja2 templates to produce complete extractor packages
3. **Validation** - Ensures generated code meets quality standards
4. **Registry** - Manages dynamic loading and versioning of extractors
5. **Self-Improvement** - Iteratively refines extractors based on test failures (Phase 4)

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Meta-Extractor System                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │  Examples    │──▶│ Synthesizer  │──▶│  Generated   │       │
│  │  (JSON)      │   │              │   │  Code        │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│                              │                  │               │
│                              ▼                  ▼               │
│                     ┌──────────────┐   ┌──────────────┐       │
│                     │ Pattern      │   │ Validator    │       │
│                     │ Analysis     │   │              │       │
│                     └──────────────┘   └──────────────┘       │
│                              │                  │               │
│                              │                  ▼               │
│                              │         ┌──────────────┐       │
│                              │         │ Deployment   │       │
│                              │         │              │       │
│                              │         └──────────────┘       │
│                              │                  │               │
│                              ▼                  ▼               │
│                     ┌──────────────────────────────┐          │
│                     │   Extractor Registry         │          │
│                     │   (Dynamic Loading)          │          │
│                     └──────────────────────────────┘          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │         Phase 4: Self-Improvement Loop                    │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │ │
│  │  │ Evaluate   │─▶│  Analyze   │─▶│  Refine    │────┐    │ │
│  │  │ Test Cases │  │  Failures  │  │  Prompts   │    │    │ │
│  │  └────────────┘  └────────────┘  └────────────┘    │    │ │
│  │       ▲                                             │    │ │
│  │       └─────────────────────────────────────────────┘    │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. MetaExtractor (Orchestrator)

**File**: `src/edgar_analyzer/extractors/meta_extractor.py` (629 LOC)

**Responsibilities**:
- Coordinates entire pipeline
- Manages state transitions
- Handles error recovery
- Provides unified API

**Key Methods**:
```python
create()       # End-to-end extractor creation
validate_code() # Code quality validation
deploy()       # File system deployment
```

**State Machine**:
```
START
  │
  ├─▶ LOADING_EXAMPLES ──▶ ANALYZING_PATTERNS ──▶ GENERATING_CODE
  │                                                      │
  │                                                      ▼
  └─────────────────────────────────────────▶ VALIDATING_CODE
                                                         │
                                                         ▼
                                                   DEPLOYING
                                                         │
                                                         ▼
                                                   REGISTERING
                                                         │
                                                         ▼
                                                      SUCCESS
```

### 2. ExtractorSynthesizer (Pattern Analysis & Code Generation)

**File**: `src/edgar_analyzer/extractors/synthesizer.py` (790 LOC)

**Responsibilities**:
- Load and parse example JSON files
- Analyze patterns using SchemaAnalyzer + ExampleParser
- Render Jinja2 templates with pattern metadata
- Generate complete extractor packages

**Core Pipeline**:
```
Examples (JSON)
      │
      ▼
  ┌─────────────────┐
  │ Load Examples   │
  └─────────────────┘
      │
      ▼
  ┌─────────────────┐
  │ Schema Analysis │ ◀─── SchemaAnalyzer (platform)
  └─────────────────┘
      │
      ▼
  ┌─────────────────┐
  │ Pattern Detect  │ ◀─── ExampleParser (platform)
  └─────────────────┘
      │
      ▼
  ┌─────────────────┐
  │ Build Metadata  │
  └─────────────────┘
      │
      ▼
  ┌─────────────────┐
  │ Render Templates│ ◀─── Jinja2
  └─────────────────┘
      │
      ▼
  GeneratedExtractor
```

**Key Algorithms**:

1. **Confidence Calculation**:
```python
confidence = (
    schema_match_score * 0.4 +    # Input/output schema clarity
    pattern_coverage * 0.3 +       # % of fields with patterns
    pattern_consistency * 0.2 +    # Pattern agreement across examples
    example_diversity * 0.1        # Edge case coverage
)
```

2. **Type Inference**:
```python
def infer_field_type(values: List[Any]) -> FieldTypeEnum:
    """Infer Pydantic field type from example values."""
    if all(isinstance(v, bool) for v in values):
        return FieldTypeEnum.BOOLEAN
    elif all(isinstance(v, int) for v in values):
        return FieldTypeEnum.INTEGER
    elif all(isinstance(v, float) for v in values):
        return FieldTypeEnum.FLOAT
    elif all(isinstance(v, list) for v in values):
        return FieldTypeEnum.LIST
    # ... more type inference logic
```

### 3. ExtractorRegistry (Dynamic Loading)

**File**: `src/edgar_analyzer/extractors/registry.py` (509 LOC)

**Responsibilities**:
- JSON-based metadata persistence
- Dynamic class loading via `importlib`
- Filtering and search
- Version management

**Registry Schema** (`data/extractors/registry.json`):
```json
{
  "version": "1.0.0",
  "extractors": {
    "sct_extractor": {
      "name": "sct_extractor",
      "class_path": "edgar_analyzer.extractors.sct.extractor.SCTExtractor",
      "version": "1.0.0",
      "description": "Extract Summary Compensation Table",
      "domain": "sct",
      "confidence": 0.94,
      "examples_count": 3,
      "tags": ["sec", "proxy", "compensation"],
      "created_at": "2025-12-07T22:45:00Z",
      "updated_at": "2025-12-07T22:45:00Z"
    }
  }
}
```

**Dynamic Loading Flow**:
```
get("sct_extractor")
      │
      ▼
Read registry.json
      │
      ▼
Extract class_path
      │
      ▼
importlib.import_module("edgar_analyzer.extractors.sct.extractor")
      │
      ▼
getattr(module, "SCTExtractor")
      │
      ▼
Validate implements IDataExtractor
      │
      ▼
Return class
```

**Security Model**:
- **Namespace Restriction**: Only allow imports from `edgar_analyzer.extractors.*`
- **Interface Validation**: Verify class implements `IDataExtractor`
- **Atomic Writes**: Use temp file + rename to prevent corruption

### 4. SelfImprovementLoop (Phase 4)

**File**: `src/edgar_analyzer/extractors/self_improvement.py` (787 LOC)

**Responsibilities**:
- Run extractors on test cases
- Analyze failures with FailureAnalyzer
- Refine prompts/templates based on failure patterns
- Iterate until target accuracy or plateau

**Improvement Loop**:
```
┌─────────────────────────────────────────────────┐
│  Start: Initial Extractor v1.0.0                │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  Evaluate on Test Cases                         │
│  ▶ Run extractor on each test case             │
│  ▶ Compare output vs expected                  │
│  ▶ Calculate accuracy = passed / total         │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  Accuracy ≥ Target? ────────────────────────▶ SUCCESS
└─────────────────────────────────────────────────┘
              │ No
              ▼
┌─────────────────────────────────────────────────┐
│  Analyze Failures                               │
│  ▶ Categorize by FailureType                   │
│  ▶ Identify missing fields                     │
│  ▶ Find incorrect transformations              │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  Suggest Improvements                           │
│  ▶ Refine LLM system prompt                    │
│  ▶ Add parsing rules                           │
│  ▶ Update table validation rules               │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  Regenerate Extractor v1.1.0                    │
│  ▶ Update PatternAnalysis with improvements    │
│  ▶ Re-synthesize code                          │
│  ▶ Deploy new version                          │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  Iterations < Max? ──────────────────────────▶ LOOP
│  Improvement ≥ Min?                             │
└─────────────────────────────────────────────────┘
              │ No
              ▼
          PLATEAU
```

**Plateau Detection**:
```python
if iterations >= 2:
    recent_improvements = [
        history[i+1] - history[i]
        for i in range(len(history) - 2, len(history))
    ]
    if all(imp < min_improvement for imp in recent_improvements):
        return "PLATEAU_REACHED"
```

### 5. FailureAnalyzer (Phase 4)

**File**: `src/edgar_analyzer/extractors/failure_analyzer.py` (739 LOC)

**Failure Taxonomy**:
```
FailureType (Enum)
├── PARSING_ERROR          # JSON/HTML parsing failed
├── VALIDATION_ERROR       # Output doesn't match schema
├── MISSING_DATA           # Required fields missing
├── INCORRECT_TRANSFORMATION # Wrong values extracted
└── EXCEPTION              # Unhandled exception
```

**Analysis Algorithm**:
```python
def analyze_failure(test_case, actual_output, exception):
    if exception:
        if isinstance(exception, (JSONDecodeError, HTMLParseError)):
            return FailureAnalysis(type=PARSING_ERROR, ...)
        else:
            return FailureAnalysis(type=EXCEPTION, ...)

    if not actual_output:
        return FailureAnalysis(type=MISSING_DATA, ...)

    # Check schema validation
    try:
        validate_schema(actual_output)
    except ValidationError:
        return FailureAnalysis(type=VALIDATION_ERROR, ...)

    # Check field-by-field correctness
    missing = find_missing_fields(expected, actual_output)
    incorrect = find_incorrect_fields(expected, actual_output)

    if missing:
        return FailureAnalysis(type=MISSING_DATA, missing_fields=missing)
    elif incorrect:
        return FailureAnalysis(type=INCORRECT_TRANSFORMATION, incorrect_fields=incorrect)
```

**Improvement Suggestions**:
```python
def suggest_improvements(failures: List[FailureAnalysis]) -> List[str]:
    failure_counts = Counter(f.failure_type for f in failures)

    suggestions = []

    if failure_counts[PARSING_ERROR] > 2:
        suggestions.append("Improve HTML parsing: Add more robust table detection")

    if failure_counts[MISSING_DATA] > 3:
        suggestions.append("LLM missing required fields: Strengthen system prompt")

    if failure_counts[INCORRECT_TRANSFORMATION] > 2:
        suggestions.append("Add explicit parsing rules for value transformations")

    return suggestions
```

---

## Data Flow

### End-to-End Extractor Creation

```
User Input
    │
    ├─ name: "sct_extractor"
    ├─ examples_dir: Path("examples/sct/")
    └─ description: "Extract Summary Compensation Table"
    │
    ▼
╔═══════════════════════════════════════════════════════════╗
║               MetaExtractor.create()                      ║
╚═══════════════════════════════════════════════════════════╝
    │
    ├─▶ Load Examples (Synthesizer)
    │       │
    │       ├─ Read *.json files
    │       ├─ Parse {"input": {...}, "output": {...}}
    │       └─ Validate structure
    │       │
    │       ▼ examples: List[Dict]
    │
    ├─▶ Analyze Patterns (Synthesizer)
    │       │
    │       ├─ SchemaAnalyzer.analyze(examples)
    │       │     │
    │       │     ├─ Detect input schema
    │       │     ├─ Detect output schema
    │       │     └─ Calculate confidence
    │       │
    │       ├─ ExampleParser.parse(examples)
    │       │     │
    │       │     ├─ Extract patterns (14 types)
    │       │     ├─ Detect heading patterns
    │       │     └─ Build validation rules
    │       │
    │       └─ Build PatternAnalysis metadata
    │       │
    │       ▼ analysis: PatternAnalysis
    │
    ├─▶ Generate Code (Synthesizer)
    │       │
    │       ├─ Load Jinja2 templates
    │       ├─ Render extractor.py.j2
    │       ├─ Render models.py.j2
    │       ├─ Render prompts.py.j2
    │       ├─ Render test_*.py.j2
    │       └─ Render __init__.py.j2
    │       │
    │       ▼ extractor: GeneratedExtractor
    │
    ├─▶ Validate Code (MetaExtractor)
    │       │
    │       ├─ Syntax check (ast.parse)
    │       ├─ Interface check (IDataExtractor)
    │       ├─ Import check (importlib)
    │       └─ Test validity (pytest --collect-only)
    │       │
    │       ▼ validation: ValidationResult
    │
    ├─▶ Deploy (MetaExtractor)
    │       │
    │       ├─ Create directory: src/edgar_analyzer/extractors/sct/
    │       ├─ Write extractor.py
    │       ├─ Write models.py
    │       ├─ Write prompts.py
    │       ├─ Write test_sct_extractor.py
    │       ├─ Write __init__.py
    │       └─ Run black formatter
    │       │
    │       ▼ deployment: DeploymentResult
    │
    └─▶ Register (ExtractorRegistry)
            │
            ├─ Create ExtractorMetadata
            ├─ Add to registry.json
            └─ Atomic write (temp + rename)
            │
            ▼ result: CreateResult
```

### Runtime Extraction Flow

```
User Code
    │
    ▼
ExtractorRegistry.get("sct_extractor")
    │
    ├─ Read registry.json
    ├─ Extract class_path
    ├─ Dynamic import
    └─ Return SCTExtractor class
    │
    ▼
extractor = SCTExtractor(openrouter_client)
    │
    ▼
result = extractor.extract(input_data)
    │
    ├─▶ Validate input (Pydantic)
    │       │
    │       ▼ InputModel(**input_data)
    │
    ├─▶ Extract HTML table
    │       │
    │       ├─ Search for heading patterns
    │       ├─ Parse table with BeautifulSoup
    │       └─ Validate table structure
    │       │
    │       ▼ raw_table_data: List[Dict]
    │
    ├─▶ Transform via LLM (OpenRouter)
    │       │
    │       ├─ Build system prompt
    │       ├─ Add parsing rules
    │       ├─ Send to Claude Sonnet 4.5
    │       └─ Parse JSON response
    │       │
    │       ▼ llm_output: Dict
    │
    └─▶ Validate output (Pydantic)
            │
            ▼ OutputModel(**llm_output)
            │
            ▼ Validated result: Dict
```

---

## Design Decisions

### 1. Why Jinja2 Templates?

**Decision**: Use Jinja2 templates for code generation instead of AST manipulation

**Rationale**:
- ✅ **Maintainability**: Templates are easier to understand and modify
- ✅ **Flexibility**: Easy to add new extractor patterns
- ✅ **Readability**: Generated code matches hand-written style
- ✅ **Debugging**: Template errors are easier to trace

**Trade-offs**:
- ❌ No compile-time validation of generated code
- ✅ Mitigated by comprehensive validation step

### 2. Why JSON Registry?

**Decision**: Use JSON file for registry instead of SQLite database

**Rationale**:
- ✅ **Simplicity**: No database dependencies
- ✅ **Version Control**: Can be committed to git
- ✅ **Human Readable**: Easy to inspect and debug
- ✅ **Atomic Writes**: Temp file + rename prevents corruption

**Trade-offs**:
- ❌ Not suitable for >1000 extractors
- ✅ Acceptable for expected scale (<100 extractors)

### 3. Why Reuse Platform Components?

**Decision**: Leverage `SchemaAnalyzer` and `ExampleParser` from platform

**Rationale**:
- ✅ **Code Reuse**: 83% reuse target met
- ✅ **Consistency**: Same pattern detection logic across platform
- ✅ **Maintenance**: Fixes benefit both systems
- ✅ **Testing**: Already has comprehensive test coverage

### 4. Why Phase 4 Self-Improvement?

**Decision**: Add iterative refinement loop for accuracy improvement

**Rationale**:
- ✅ **Higher Accuracy**: Systematic improvement from initial 70% → 90%+
- ✅ **Automated**: No manual prompt tuning required
- ✅ **Failure Analysis**: Learn from mistakes systematically
- ✅ **Version Tracking**: Maintain improvement history

**Trade-offs**:
- ❌ Longer generation time (30s vs 3s)
- ✅ Optional feature, can be skipped for rapid prototyping

### 5. Why Namespace Restrictions?

**Decision**: Only allow imports from `edgar_analyzer.extractors.*`

**Rationale**:
- ✅ **Security**: Prevent arbitrary code execution
- ✅ **Safety**: Sandbox untrusted generated code
- ✅ **Predictability**: Known namespace for debugging

---

## Pipeline Stages

### Stage 1: Example Loading

**Input**: Directory path with `*.json` files
**Output**: `List[Dict[str, Any]]` with `input`/`output` keys
**Duration**: ~50ms for 3 files

**Validation**:
- ✅ All files are valid JSON
- ✅ Each file has `input` and `output` keys
- ✅ Structures are consistent across examples

### Stage 2: Pattern Analysis

**Input**: List of examples
**Output**: `PatternAnalysis` with confidence score
**Duration**: ~800ms for 3 examples with 50 fields

**Sub-stages**:
1. **Schema Detection** (SchemaAnalyzer) - 40% of time
2. **Pattern Extraction** (ExampleParser) - 50% of time
3. **Metadata Building** - 10% of time

**Confidence Calculation**:
```
confidence = 0.4 × schema_clarity +
             0.3 × pattern_coverage +
             0.2 × pattern_consistency +
             0.1 × example_diversity
```

### Stage 3: Code Generation

**Input**: `PatternAnalysis`
**Output**: `GeneratedExtractor` with 5 files
**Duration**: ~400ms

**Templates Rendered**:
1. `extractor.py.j2` → Main extractor class (~200 LOC)
2. `models.py.j2` → Pydantic models (~80 LOC)
3. `prompts.py.j2` → LLM prompts (~50 LOC)
4. `test_extractor.py.j2` → Unit tests (~150 LOC)
5. `__init__.py.j2` → Package init (~20 LOC)

### Stage 4: Validation

**Input**: `GeneratedExtractor`
**Output**: `ValidationResult`
**Duration**: ~200ms

**Checks**:
1. **Syntax** - `ast.parse()` all files
2. **Interface** - Class implements `IDataExtractor`
3. **Imports** - All imports resolvable
4. **Tests** - `pytest --collect-only` succeeds

### Stage 5: Deployment

**Input**: `GeneratedExtractor`, output directory
**Output**: `DeploymentResult`
**Duration**: ~150ms

**Operations**:
1. Create directory structure
2. Write files to disk
3. Run `black` formatter
4. Verify files exist

### Stage 6: Registration

**Input**: Extractor metadata
**Output**: Updated `registry.json`
**Duration**: ~50ms

**Operations**:
1. Load existing registry
2. Add new entry
3. Atomic write (temp + rename)
4. Verify registration

---

## Template System

### Template Structure

```
src/edgar_analyzer/extractors/templates/
├── extractor.py.j2          # Main extractor class
├── models.py.j2             # Pydantic models
├── prompts.py.j2            # LLM system prompts
├── test_extractor.py.j2     # Unit tests
└── __init__.py.j2           # Package initialization
```

### Template Variables

All templates receive a `ctx` (context) object:

```python
ctx = {
    "name": "sct_extractor",
    "domain": "sct",
    "class_name": "SCTExtractor",
    "description": "Extract Summary Compensation Table",
    "input_fields": [
        {"name": "html", "type": "str"},
        {"name": "url", "type": "str"},
    ],
    "output_fields": [
        {"name": "records", "type": "List[Dict]"},
        {"name": "record_count", "type": "int"},
    ],
    "patterns": [
        {
            "type": "FIELD_MAPPING",
            "source": "name",
            "target": "executive_name",
            "confidence": 1.0
        }
    ],
    "heading_patterns": [
        "Summary Compensation Table",
        "Executive Compensation"
    ],
    "system_prompt": "Extract executive compensation data...",
    "parsing_rules": [
        "Convert currency strings to floats",
        "Parse year as integer"
    ]
}
```

### Example Template: `extractor.py.j2`

```jinja2
"""{{ ctx.description }}"""

from typing import Dict, Any
import structlog
from bs4 import BeautifulSoup

from extract_transform_platform.core.base import IDataExtractor
from edgar_analyzer.services.openrouter_client import OpenRouterClient

from .models import {{ ctx.class_name }}Input, {{ ctx.class_name }}Output
from .prompts import SYSTEM_PROMPT, PARSING_RULES

logger = structlog.get_logger(__name__)


class {{ ctx.class_name }}(IDataExtractor):
    """{{ ctx.description }}"""

    def __init__(self, openrouter_client: OpenRouterClient):
        self.client = openrouter_client

    def extract(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from input."""
        # Validate input
        validated_input = {{ ctx.class_name }}Input(**input_data)

        # Extract table from HTML
        table_data = self._extract_table(validated_input.html)

        # Transform via LLM
        output = self._transform_via_llm(table_data)

        # Validate output
        validated_output = {{ ctx.class_name }}Output(**output)

        return validated_output.model_dump()

    def _extract_table(self, html: str) -> str:
        """Extract relevant table from HTML."""
        soup = BeautifulSoup(html, "html.parser")

        # Search for heading patterns
        {% for pattern in ctx.heading_patterns %}
        heading = soup.find(text=lambda t: "{{ pattern }}" in t if t else False)
        if heading:
            # Find next table
            table = heading.find_next("table")
            if table:
                return str(table)
        {% endfor %}

        return ""

    def _transform_via_llm(self, table_html: str) -> Dict[str, Any]:
        """Transform table via LLM."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": table_html}
        ]

        response = self.client.chat_completion(messages)
        return response  # Assume JSON response
```

---

## Self-Improvement Loop (Phase 4)

### Iterative Refinement Algorithm

```python
def run_improvement_loop(
    extractor_name: str,
    test_cases: List[TestCase],
    target_accuracy: float = 0.90,
    max_iterations: int = 5
) -> ImprovementResult:

    version = "1.0.0"
    history = []

    for iteration in range(max_iterations):
        # Evaluate current version
        eval_result = evaluate(extractor_name, test_cases)
        accuracy = eval_result.accuracy
        history.append(accuracy)

        logger.info(f"Iteration {iteration + 1}: {accuracy:.1%}")

        # Check success
        if accuracy >= target_accuracy:
            return ImprovementResult(
                success=True,
                final_accuracy=accuracy,
                iterations=iteration + 1
            )

        # Check plateau
        if is_plateau(history):
            logger.warning("Plateau detected - no significant improvement")
            break

        # Analyze failures
        failure_analysis = analyze_failures(eval_result.failures)

        # Suggest improvements
        suggestions = suggest_improvements(failure_analysis)

        # Regenerate with improvements
        version = bump_version(version)
        regenerate_extractor(extractor_name, suggestions, version)

    return ImprovementResult(
        success=False,
        final_accuracy=history[-1],
        iterations=len(history)
    )
```

### Failure-Driven Refinement

**Failure Type → Improvement Action**:

| Failure Type | Root Cause | Improvement Action |
|--------------|------------|-------------------|
| PARSING_ERROR | HTML parsing failed | Add robust table detection logic |
| VALIDATION_ERROR | Schema mismatch | Strengthen output validation rules |
| MISSING_DATA | LLM skipped fields | Add explicit field requirements to prompt |
| INCORRECT_TRANSFORMATION | Wrong value extraction | Add parsing rules for specific transformations |
| EXCEPTION | Unhandled edge case | Add error handling and fallback logic |

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Typical Time |
|-----------|------------|--------------|
| Load Examples | O(n × s) | 50ms for 3 files @ 10KB each |
| Analyze Patterns | O(n × m) | 800ms for 3 examples × 50 fields |
| Generate Code | O(p) | 400ms for 10 patterns |
| Validate Code | O(c) | 200ms for 500 LOC |
| Deploy | O(f) | 150ms for 5 files |
| Register | O(1) | 50ms |
| **Total** | **O(n × m + p + c)** | **~2-3 seconds** |

Where:
- n = number of examples
- m = fields per example
- p = number of patterns
- c = lines of generated code
- s = file size
- f = number of files

### Space Complexity

| Component | Complexity | Typical Size |
|-----------|------------|--------------|
| Examples in Memory | O(n × s) | 30KB for 3 examples @ 10KB each |
| Pattern Analysis | O(f + p) | 10KB for 50 fields + 10 patterns |
| Generated Code | O(f × l) | 100KB for 5 files @ 20KB each |
| Registry | O(e) | 50KB for 100 extractors |

Where:
- e = number of registered extractors
- l = lines per file

### Optimization Opportunities

1. **Caching** - Cache SchemaAnalyzer results for repeated examples
2. **Parallelization** - Analyze examples in parallel (3× speedup potential)
3. **Incremental Analysis** - Only re-analyze changed examples
4. **Template Compilation** - Compile Jinja2 templates once at startup

---

## Security Considerations

### 1. Dynamic Code Execution

**Risk**: Generated code could contain malicious logic

**Mitigations**:
- ✅ Namespace restrictions (`edgar_analyzer.extractors.*` only)
- ✅ Code validation before deployment
- ✅ Sandboxed execution environment recommended for production
- ✅ Review generated code before use in sensitive contexts

### 2. Registry Integrity

**Risk**: Registry JSON could be corrupted or tampered with

**Mitigations**:
- ✅ Atomic writes (temp file + rename)
- ✅ JSON schema validation on load
- ✅ File permissions (read/write restricted to user)

### 3. Template Injection

**Risk**: Malicious data in examples could inject code into templates

**Mitigations**:
- ✅ Jinja2 auto-escaping enabled
- ✅ Input validation before template rendering
- ✅ Sanitize all user-provided strings

### 4. LLM Prompt Injection

**Risk**: Malicious HTML input could manipulate LLM output

**Mitigations**:
- ✅ Pydantic validation on LLM output
- ✅ Explicit output schema enforcement
- ✅ Confidence scoring for anomaly detection

---

## Next Steps

- **[User Guide](../../user/META_EXTRACTOR_USER_GUIDE.md)** - How to use the system
- **[API Reference](../api/META_EXTRACTOR_API.md)** - Detailed API documentation
- **[Troubleshooting](../../user/META_EXTRACTOR_TROUBLESHOOTING.md)** - Common issues
- **[Platform Overview](../../user/PLATFORM_OVERVIEW.md)** - Platform architecture

---

**Built with the EDGAR Platform: From SEC filings to general-purpose data extraction.**
