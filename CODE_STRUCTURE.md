# EDGAR Platform - Code Structure

**Purpose**: Comprehensive overview of codebase architecture and key components
**Last Updated**: 2025-12-28

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Service Layer](#service-layer)
- [Data Models](#data-models)
- [Validators](#validators)
- [Prompts](#prompts)
- [Design Patterns](#design-patterns)
- [Data Flow](#data-flow)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     EDGAR Platform                          │
│  Example-Driven Generation with AI Reasoning                │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ API Examples + Target Schema
                              ▼
        ┌───────────────────────────────────────┐
        │      Sonnet4_5Service                 │
        │  (Main Orchestrator)                  │
        └───────────────────────────────────────┘
                 │                    │
        PM Mode  │                    │ Coder Mode
                 ▼                    ▼
    ┌──────────────────┐    ┌──────────────────┐
    │ analyze_examples │    │  generate_code   │
    │                  │    │                  │
    │ Returns:         │───▶│ Input:           │
    │ ExtractionStrategy│    │ ExtractionStrategy│
    └──────────────────┘    └──────────────────┘
                                     │
                                     │ Generated Python Code
                                     ▼
                        ┌─────────────────────────┐
                        │  Validation Pipeline    │
                        │  1. AST Validator       │
                        │  2. Constraint Validator│
                        │  3. Accuracy Validator  │
                        └─────────────────────────┘
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │ Production-Ready Code   │
                        │ - Pydantic Models       │
                        │ - IDataSource Impl      │
                        │ - IDataExtractor Impl   │
                        └─────────────────────────┘
```

---

## Service Layer

### Sonnet4_5Service (`src/edgar/services/sonnet_service.py`)

**Purpose**: Main orchestrator for two-phase code generation

**Dependencies**:
- `OpenRouterClient`: HTTP client for Sonnet 4.5 API
- `ContextManager`: Conversation history management

**Key Methods**:

#### `analyze_examples(examples, target_schema) -> dict[str, Any]`
**Phase**: PM Mode (Analysis)

**Flow**:
1. Load PM Mode prompt template from `prompts/pm_mode.txt`
2. Format examples as numbered JSON blocks
3. Extract target schema (Pydantic JSON schema or string repr)
4. Build system message with template + examples + schema
5. Call OpenRouter API (temperature=0.3, max_tokens=4096)
6. Parse JSON response (handles markdown code blocks)
7. Validate against `ExtractionStrategy` Pydantic model
8. Update conversation context
9. Return strategy as dictionary

**Error Handling**:
- Empty examples → `ValueError`
- JSON parsing failure → `ValueError` with details
- Pydantic validation failure → `ValueError` with schema errors
- Auth failure → `OpenRouterAuthError` (no retry)
- Rate limit → `OpenRouterRateLimitError` (retry with backoff)

#### `generate_code(strategy, architecture_constraints) -> str`
**Phase**: Coder Mode (Implementation)

**Flow**:
1. Use default constraints if none provided (IDataSource, IDataExtractor, DI, Pydantic)
2. Load Coder Mode prompt template from `prompts/coder_mode.txt`
3. Format strategy and constraints as JSON
4. Build system message with template + strategy + constraints
5. Call OpenRouter API (temperature=0.2, max_tokens=8192)
6. Extract Python code from response (handles markdown)
7. Validate syntax using AST parser
8. Update conversation context
9. Return complete Python module as string

**Error Handling**:
- Empty strategy → `ValueError`
- No code generated → `ValueError`
- Syntax errors → `ValueError` with line number and details
- Auth/rate limit errors → Same as `analyze_examples`

#### `validate_and_refine(code, examples) -> str`
**Phase**: Validation & Refinement (NOT YET IMPLEMENTED)

**Planned Flow**:
1. Run AST validation
2. Run constraint validation (architecture compliance)
3. Run accuracy validation (test against examples)
4. If validation fails, refine through conversation
5. Return validated and refined code

**Private Helper Methods**:

- `_load_pm_template()`: Load PM Mode prompt from file
- `_load_coder_template()`: Load Coder Mode prompt from file
- `_format_examples(examples)`: Format examples as numbered JSON blocks
- `_format_schema(target_schema)`: Extract Pydantic JSON schema
- `_extract_json(content)`: Parse JSON from markdown-wrapped response
- `_extract_python_code(content)`: Extract Python code from markdown
- `_validate_code_syntax(code)`: AST syntax validation

---

### OpenRouterClient (`src/edgar/services/openrouter_client.py`)

**Purpose**: HTTP client for OpenRouter API with retry logic

**Configuration**:
- Base URL: `https://openrouter.ai/api/v1`
- Model: `anthropic/claude-sonnet-4.5` (configurable)
- Timeout: 60 seconds per request
- Max Retries: 3 attempts
- Backoff: Exponential (2s, 4s, 8s)

**Key Method**:

#### `chat_completion(messages, temperature, max_tokens) -> dict[str, Any]`

**Retry Strategy**:
```
Attempt 1 → Fail → Wait 2s
Attempt 2 → Fail → Wait 4s
Attempt 3 → Fail → Wait 8s
Attempt 4 → Raise exception
```

**Retryable Errors**:
- 429 Rate Limit
- 5xx Server Errors
- Network/Connection Errors

**Non-Retryable Errors** (Fail Immediately):
- 401 Unauthorized
- 403 Forbidden

**Response Format**:
```json
{
  "choices": [{
    "message": {
      "content": "LLM response text"
    }
  }],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 200
  },
  "model": "anthropic/claude-sonnet-4.5"
}
```

**Headers**:
- `Authorization: Bearer {api_key}`
- `Content-Type: application/json`
- `HTTP-Referer: https://github.com/masa-cloud/edgar-platform`
- `X-Title: EDGAR Platform`

**Exception Hierarchy**:
```
OpenRouterError (base)
├── OpenRouterAuthError (401/403)
├── OpenRouterRateLimitError (429)
└── OpenRouterServerError (5xx)
```

---

### ContextManager (`src/edgar/services/context_manager.py`)

**Purpose**: Manage conversation history for multi-turn interactions

**Configuration**:
- Max Messages: 20 (configurable)
- Max Tokens: 200,000 (approximate)

**Data Structure**:
```python
messages: list[dict[str, str]] = [
    {"role": "system", "content": "PM Mode prompt..."},
    {"role": "user", "content": "Analyze these examples..."},
    {"role": "assistant", "content": "Here's the strategy..."},
    {"role": "system", "content": "Coder Mode prompt..."},
    {"role": "user", "content": "Generate code..."},
    {"role": "assistant", "content": "```python\nclass...\n```"}
]
```

**Key Methods**:

- `add_user_message(content)`: Add user message + trim context
- `add_assistant_message(content)`: Add assistant response + trim context
- `add_system_message(content)`: Add system prompt + trim context
- `get_messages()`: Return copy of message history
- `clear()`: Clear all messages

**Context Trimming Strategy**:
1. Preserve all system messages (prompts)
2. Trim oldest user/assistant messages
3. Keep most recent `max_messages - len(system_messages)` conversation turns

**Token Estimation**:
- Approximate: 1 token ≈ 4 characters
- Used for soft limit enforcement
- Not exact, but sufficient for 200k context window

---

## Data Models

### ExtractionStrategy (`src/edgar/models/extraction_strategy.py`)

**Purpose**: Structured output from PM Mode analysis

**Schema**:
```python
{
  "data_source_type": "REST_API | GraphQL | RSS | WebSocket",
  "response_format": "JSON | XML | CSV",
  "extraction_patterns": {
    "field_name": {
      "source_path": "$.path.to.field",  # JSON path, XPath, regex
      "description": "What this field represents",
      "optional": false,
      "default_value": null
    }
  },
  "transformations": [
    {
      "field": "temperature",
      "operation": "type_conversion | calculation | string_manipulation | unit_conversion",
      "formula": "fahrenheit_to_celsius(temp)",
      "description": "Convert F to C"
    }
  ],
  "validation_rules": {
    "temperature": {
      "type": "float",
      "constraints": {"min": -100, "max": 200},
      "error_handling": "fail | use_default | skip_record",
      "default_value": 0.0
    }
  },
  "cross_field_validations": [
    {
      "rule": "min_temp <= max_temp",
      "fields": ["min_temp", "max_temp"],
      "validation_logic": "Ensure min is not greater than max"
    }
  ],
  "error_handling": {
    "missing_fields": "fail | use_defaults | skip_record",
    "invalid_types": "fail | coerce | skip_field",
    "validation_failures": "fail | log_and_continue | skip_record"
  },
  "assumptions": [
    "Temperature is always in Fahrenheit",
    "Negative values indicate missing data"
  ]
}
```

**Pydantic Models**:

- `ExtractionPattern`: Single field extraction pattern
- `Transformation`: Data transformation specification
- `ValidationRule`: Field validation rule
- `CrossFieldValidation`: Cross-field validation rule
- `ErrorHandlingStrategy`: Error handling configuration
- `ExtractionStrategy`: Complete strategy (root model)

---

### ArchitectureConstraints (`src/edgar/models/constraints.py`)

**Purpose**: Define architecture requirements for generated code

**Schema**:
```python
{
  "interfaces": [
    {
      "name": "IDataSource",
      "methods": ["async def fetch(self) -> dict[str, Any]"],
      "description": "Interface for fetching raw data"
    },
    {
      "name": "IDataExtractor",
      "methods": ["def extract(self, raw_data: dict[str, Any]) -> BaseModel"],
      "description": "Interface for extracting structured data"
    }
  ],
  "design_patterns": [
    {
      "pattern": "Dependency Injection",
      "requirements": [
        "Use frozen dataclasses",
        "Inject all dependencies via constructor",
        "No hardcoded configuration"
      ]
    }
  ],
  "type_safety": {
    "require_type_hints": true,
    "require_return_types": true,
    "forbid_any_type": true,
    "require_pydantic_models": true
  },
  "code_quality": [
    {
      "rule": "PEP 8 Compliance",
      "description": "Follow Python style guide",
      "severity": "error"
    }
  ],
  "forbidden_patterns": [
    "global variables",
    "hardcoded configuration",
    "bare except clauses",
    "mutable default arguments"
  ]
}
```

**Default Constraints** (`ArchitectureConstraints.default()`):
- IDataSource and IDataExtractor interfaces required
- Dependency Injection with frozen dataclasses
- Pydantic validation for all data structures
- 100% type hints, no `Any` types
- PEP 8 compliance
- Docstrings required for all public APIs
- Functions under 50 lines (warning)

---

## Validators

### ASTValidator (`src/edgar/validators/ast_validator.py`)

**Purpose**: Validate Python code syntax using AST parsing

**Current Status**: ✅ Syntax validation implemented, ⚠️ Structure validation TODO

**Key Method**:

#### `validate(code: str) -> ValidationResult`

**Validation Steps**:
1. Parse code using `ast.parse(code)`
2. Catch `SyntaxError` and format with line number
3. (TODO) Validate structure:
   - Check for class definitions
   - Check for function definitions
   - Validate type hint presence
   - Check for docstrings

**Returns**:
```python
ValidationResult(
    valid=True/False,
    errors=["Syntax error at line 10: ..."],
    warnings=["Function missing type hints"]
)
```

**Exception Types**:
- `ValidationError`: Base validation exception
- `SyntaxValidationError`: Python syntax error

---

### ConstraintValidator (`src/edgar/validators/constraint_validator.py`)

**Purpose**: Validate architecture compliance

**Current Status**: ⚠️ NOT YET IMPLEMENTED

**Planned Validations**:
- Interface implementation (IDataSource, IDataExtractor)
- Dependency injection pattern (frozen dataclasses, constructor injection)
- Type hint coverage (100% required)
- Pydantic model usage
- Forbidden patterns detection (global vars, bare except, etc.)
- Docstring coverage

---

### AccuracyValidator (`src/edgar/validators/accuracy_validator.py`)

**Purpose**: Test generated code against provided examples

**Current Status**: ⚠️ NOT YET IMPLEMENTED

**Planned Workflow**:
1. Execute generated code in isolated environment
2. Run extractor against each provided example
3. Compare extracted data with expected schema
4. Report mismatches and errors
5. Return validation result with accuracy metrics

---

## Prompts

### PM Mode Prompt (`src/edgar/prompts/pm_mode.txt`)

**Purpose**: System prompt for PM Mode analysis

**Template Variables**:
- `{examples}`: Formatted API response examples
- `{target_schema}`: Target Pydantic model JSON schema

**Expected Output**: JSON matching `ExtractionStrategy` schema

**Key Sections**:
1. Role definition (Product Manager analyzing API responses)
2. Task description (design extraction strategy)
3. Input format (examples + schema)
4. Output format (ExtractionStrategy JSON)
5. Analysis guidelines (identify patterns, transformations, validations)

---

### Coder Mode Prompt (`src/edgar/prompts/coder_mode.txt`)

**Purpose**: System prompt for Coder Mode implementation

**Template Variables**:
- `{extraction_strategy}`: JSON from PM Mode
- `{architecture_constraints}`: Architecture requirements JSON

**Expected Output**: Complete Python module with:
- Exception classes
- Pydantic models
- IDataSource implementation
- IDataExtractor implementation
- All code following architecture constraints

**Key Sections**:
1. Role definition (Senior Python engineer)
2. Task description (implement extraction strategy)
3. Input format (strategy + constraints)
4. Output format (complete Python module)
5. Code quality requirements (type hints, docstrings, PEP 8)
6. Architecture patterns (DI, interfaces, Pydantic)

---

## Design Patterns

### Dependency Injection

**Pattern**: Constructor injection with frozen dataclasses

**Example**:
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class WeatherExtractor:
    """Extract weather data from API responses."""

    # All dependencies injected via constructor
    data_source: IDataSource
    validator: IValidator

    async def extract_weather(self) -> WeatherData:
        """Extract weather data."""
        raw_data = await self.data_source.fetch()
        validated = self.validator.validate(raw_data)
        return WeatherData(**validated)
```

**Benefits**:
- Immutable services (thread-safe)
- Clear dependency graph
- Easy to test (inject mocks)
- No hidden dependencies

---

### Interface-Based Design

**Pattern**: Protocol-based interfaces for abstraction

**Example**:
```python
from typing import Protocol, Any
from pydantic import BaseModel

class IDataSource(Protocol):
    """Interface for data sources."""

    async def fetch(self) -> dict[str, Any]:
        """Fetch raw data from source."""
        ...

class IDataExtractor(Protocol):
    """Interface for data extractors."""

    def extract(self, raw_data: dict[str, Any]) -> BaseModel:
        """Extract structured data from raw response."""
        ...
```

**Benefits**:
- Separation of concerns (fetch vs. extract)
- Testability (mock implementations)
- Flexibility (swap implementations)
- Clear contracts

---

### Retry with Exponential Backoff

**Pattern**: Automatic retry for transient failures

**Implementation** (`OpenRouterClient.chat_completion`):
```python
for attempt in range(max_retries):
    try:
        response = await client.post(url, json=payload)
        return response.json()
    except (RateLimitError, ServerError, NetworkError) as e:
        if attempt < max_retries - 1:
            delay = 2 ** (attempt + 1)  # 2s, 4s, 8s
            await asyncio.sleep(delay)
        else:
            raise
```

**Benefits**:
- Resilience against transient failures
- Automatic recovery from rate limits
- No user intervention required
- Bounded retry time (2+4+8 = 14 seconds max overhead)

---

## Data Flow

### End-to-End Flow

```
1. User provides API examples + target schema
   │
   ▼
2. Sonnet4_5Service.analyze_examples()
   │
   ├─▶ Load PM Mode prompt template
   ├─▶ Format examples as JSON blocks
   ├─▶ Extract target schema (Pydantic)
   ├─▶ Build system message
   ├─▶ Call OpenRouter API (temp=0.3)
   ├─▶ Parse JSON response
   ├─▶ Validate against ExtractionStrategy
   └─▶ Update conversation context
   │
   ▼ ExtractionStrategy (JSON)
   │
3. Sonnet4_5Service.generate_code()
   │
   ├─▶ Load Coder Mode prompt template
   ├─▶ Format strategy + constraints as JSON
   ├─▶ Build system message
   ├─▶ Call OpenRouter API (temp=0.2)
   ├─▶ Extract Python code from markdown
   ├─▶ Validate syntax with AST
   └─▶ Update conversation context
   │
   ▼ Python Code (string)
   │
4. Validation Pipeline (FUTURE)
   │
   ├─▶ ASTValidator.validate()
   ├─▶ ConstraintValidator.validate()
   └─▶ AccuracyValidator.validate()
   │
   ▼ Validated Python Code
   │
5. Production-Ready Implementation
   - Pydantic models
   - IDataSource implementation
   - IDataExtractor implementation
   - 100% type hints
   - Full docstrings
   - Error handling
```

---

## File Size and Complexity Metrics

| File | Lines | Complexity | Status |
|------|-------|------------|--------|
| `sonnet_service.py` | ~522 | Medium | ✅ Complete |
| `openrouter_client.py` | ~223 | Low | ✅ Complete |
| `context_manager.py` | ~96 | Low | ✅ Complete |
| `extraction_strategy.py` | ~152 | Low | ✅ Complete |
| `constraints.py` | ~158 | Low | ✅ Complete |
| `ast_validator.py` | ~95 | Low | ⚠️ Structure validation TODO |
| `constraint_validator.py` | - | - | ⚠️ Not implemented |
| `accuracy_validator.py` | - | - | ⚠️ Not implemented |

**Notes**:
- All files under 800-line hard limit
- Largest file (sonnet_service.py) at 522 lines - acceptable
- Most files under 200 lines - excellent modularity
- Validators need implementation (priority for next sprint)

---

**Last Updated**: 2025-12-28
**Project Location**: `/Users/masa/Projects/edgar/`
