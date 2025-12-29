# EDGAR Platform - AI Agent Instructions

**Version**: 0.1.0
**Purpose**: Example-driven data extraction platform with AI code generation
**Primary Language**: Python 3.11+

## Quick Navigation

- [Security (CRITICAL)](#-critical-security)
- [Core Business Logic (CRITICAL)](#-critical-core-business-logic)
- [Architecture Decisions (IMPORTANT)](#-important-architecture-decisions)
- [Development Workflow (IMPORTANT)](#-important-development-workflow)
- [Code Quality Standards (STANDARD)](#-standard-code-quality-standards)
- [Common Operations (STANDARD)](#-standard-common-operations)
- [Future Enhancements (OPTIONAL)](#-optional-future-enhancements)

---

## 🔴 CRITICAL: Security

### API Key Management

**NEVER hardcode API keys in source code.** All secrets must be in `.env` file.

Required environment variables:
```bash
# .env (NEVER commit this file)
OPENROUTER_API_KEY=sk-or-v1-...
EDGAR_MODEL=anthropic/claude-sonnet-4.5
```

**Loading API Keys** (from `.env`):
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found in environment")
```

**Pre-commit Checks**:
```bash
# Before committing, verify .env is in .gitignore
grep -q ".env" .gitignore || echo "⚠️  WARNING: .env not in .gitignore!"

# Search for hardcoded secrets (should return nothing)
grep -r "sk-or-v1" src/ tests/ && echo "🚨 DANGER: Found hardcoded API key!"
```

### Security Violations

These patterns are **FORBIDDEN** in production code:
- Hardcoded API keys in source files
- Committing `.env` to git
- Logging API keys or secrets
- Storing credentials in config files committed to git

---

## 🔴 CRITICAL: Core Business Logic

### EDGAR's Core Function

EDGAR transforms API response examples into production-ready Python code using a **two-phase AI approach**:

1. **PM Mode (Analysis)**: Sonnet 4.5 analyzes examples → extraction strategy
2. **Coder Mode (Implementation)**: Sonnet 4.5 generates Python code → validated implementation
3. **Validation Pipeline**: AST + Constraint + Accuracy validation

### Dual-Mode Integration Architecture

**PM Mode Purpose**: Design extraction strategy from examples
- Input: API response examples + target schema
- Output: Structured `ExtractionStrategy` (JSON)
- Prompt Template: `src/edgar/prompts/pm_mode.txt`
- Temperature: 0.3 (structured output)
- Max Tokens: 4096

**Coder Mode Purpose**: Generate production Python code
- Input: `ExtractionStrategy` + architecture constraints
- Output: Complete Python module (classes, validators, interfaces)
- Prompt Template: `src/edgar/prompts/coder_mode.txt`
- Temperature: 0.2 (deterministic code)
- Max Tokens: 8192

**Service Orchestration** (`Sonnet4_5Service`):
```python
from edgar.services import Sonnet4_5Service, OpenRouterClient, ContextManager

# Initialize with dependency injection
client = OpenRouterClient(api_key=os.getenv("OPENROUTER_API_KEY"))
context = ContextManager(max_messages=20)
service = Sonnet4_5Service(client=client, context=context)

# Phase 1: PM Mode
strategy = await service.analyze_examples(
    examples=[{"temp": 72, "condition": "sunny"}],
    target_schema=WeatherData
)

# Phase 2: Coder Mode
code = await service.generate_code(
    strategy=strategy,
    architecture_constraints=ArchitectureConstraints.default()
)

# Phase 3: Validation (TODO - not yet implemented)
# validated_code = await service.validate_and_refine(code, examples)
```

### Validation Pipeline (In Development)

**Current State**:
- ✅ AST Validator: Syntax validation implemented
- ⚠️  Constraint Validator: Interface checks not implemented
- ⚠️  Accuracy Validator: Example testing not implemented

**Validators** (`src/edgar/validators/`):
1. `ASTValidator`: Python syntax validation via AST parsing
2. `ConstraintValidator`: Architecture compliance (interfaces, DI, type hints)
3. `AccuracyValidator`: Test generated code against provided examples

**When adding validation logic**:
- AST validation must run FIRST (syntax errors block everything)
- Constraint validation checks architecture patterns
- Accuracy validation tests real examples
- All validators return `ValidationResult` with `valid`, `errors`, `warnings`

---

## 🟡 IMPORTANT: Architecture Decisions

### Service-Oriented Design with Dependency Injection

**Why Frozen Dataclasses?**
- Immutable services prevent accidental state mutation
- Clear dependency graph (all deps in constructor)
- Thread-safe by default
- Easy to test (inject mocks)

**Example Pattern**:
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class MyService:
    client: OpenRouterClient  # Injected dependency
    context: ContextManager   # Injected dependency

    async def do_work(self) -> str:
        # Use injected dependencies
        messages = self.context.get_messages()
        response = await self.client.chat_completion(messages)
        return response
```

### Key Interfaces (Architecture Constraints)

**IDataSource** (Fetch raw data):
```python
class IDataSource(Protocol):
    async def fetch(self) -> dict[str, Any]:
        """Fetch raw data from external source."""
        ...
```

**IDataExtractor** (Extract structured data):
```python
class IDataExtractor(Protocol):
    def extract(self, raw_data: dict[str, Any]) -> BaseModel:
        """Extract structured data from raw response."""
        ...
```

**Why These Interfaces?**
- Separation of concerns: fetching vs. extraction
- Testability: mock data sources easily
- Flexibility: swap implementations without changing consumers
- Generated code follows consistent patterns

### Error Handling Strategy

**OpenRouter API Errors** (`OpenRouterClient`):
- **401/403 (Auth)**: Fail immediately, no retry
- **429 (Rate Limit)**: Retry with exponential backoff (2s, 4s, 8s)
- **5xx (Server)**: Retry with exponential backoff
- **Network Errors**: Retry with exponential backoff
- **Max Retries**: 3 attempts before raising

**LLM Response Parsing**:
- Markdown code blocks (```json, ```python): Automatically extracted
- Invalid JSON: Raise `ValueError` with detailed message
- Missing required fields: Pydantic validation catches with clear errors
- Syntax errors in generated code: AST validation catches before execution

---

## 🟡 IMPORTANT: Development Workflow

### Local Development Setup

**1. Clone and Setup Virtual Environment**:
```bash
cd /Users/masa/Projects/edgar
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

**2. Configure Environment**:
```bash
# Create .env file
cat > .env << EOF
OPENROUTER_API_KEY=sk-or-v1-your-key-here
EDGAR_MODEL=anthropic/claude-sonnet-4.5
EOF
```

**3. Verify Setup**:
```bash
# Run tests
pytest

# Type checking
mypy src/

# Linting
ruff check src/

# Formatting
black src/
```

### Testing Strategy

**Test Organization**:
```
tests/
├── unit/              # Unit tests (fast, isolated)
│   ├── test_sonnet_service.py
│   ├── test_openrouter_client.py
│   └── test_context_manager.py
└── integration/       # Integration tests (slower, real API calls)
    └── test_end_to_end.py
```

**Running Tests**:
```bash
# All tests
pytest

# Unit tests only (fast)
pytest tests/unit/

# Integration tests only (slower)
pytest tests/integration/

# With coverage
pytest --cov=edgar --cov-report=html
```

**Test Requirements**:
- Minimum 90% code coverage
- All async functions must use `pytest-asyncio`
- Mock external API calls in unit tests
- Use real API (with test account) in integration tests
- Test error cases (auth failures, rate limits, invalid responses)

### Git Workflow

**Branch Naming**:
- Features: `feature/description`
- Bugs: `fix/description`
- Docs: `docs/description`

**Commit Message Format** (Conventional Commits):
```
<type>: <description>

<optional body>

<optional footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code change without behavior change
- `perf`: Performance improvement
- `test`: Adding/updating tests
- `chore`: Build/tooling changes

**Example**:
```bash
git checkout -b feature/accuracy-validator
# ... make changes ...
git add .
git commit -m "feat: implement accuracy validator for generated code

Adds AccuracyValidator that tests generated extractor code against
provided API examples. Includes error reporting for failed extractions.

Closes #15"
git push origin feature/accuracy-validator
```

---

## 🟢 STANDARD: Code Quality Standards

### Type Safety (100% Required)

**Mypy Configuration** (`pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**All functions MUST have type hints**:
```python
# ✅ CORRECT
async def fetch_data(url: str, timeout: float = 30.0) -> dict[str, Any]:
    """Fetch data from URL."""
    ...

# ❌ INCORRECT - Missing type hints
async def fetch_data(url, timeout=30.0):
    """Fetch data from URL."""
    ...
```

**No `Any` type without justification**:
```python
# ✅ CORRECT - Use specific types
def process_user(user: User) -> ProcessedUser:
    ...

# ⚠️  ACCEPTABLE - When structure is truly dynamic
def parse_json(content: str) -> dict[str, Any]:
    """Parse arbitrary JSON - structure unknown at compile time."""
    ...

# ❌ INCORRECT - Lazy typing
def process_data(data: Any) -> Any:
    ...
```

### Code Style (Black + Ruff)

**Black Configuration** (`pyproject.toml`):
```toml
[tool.black]
line-length = 100
target-version = ['py311']
```

**Ruff Configuration** (`pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py311"
```

**Formatting Rules**:
- Line length: 100 characters
- Double quotes for strings
- Trailing commas in multi-line structures
- Black reformats automatically - don't fight it

### Documentation Requirements

**All public functions/classes MUST have docstrings**:
```python
def extract_data(raw: dict[str, Any], schema: type[BaseModel]) -> BaseModel:
    """Extract structured data from raw API response.

    Args:
        raw: Raw API response dictionary
        schema: Target Pydantic model class

    Returns:
        Instance of schema with extracted data

    Raises:
        ValidationError: If extraction fails validation
        KeyError: If required fields missing from raw data

    Example:
        >>> raw = {"temp": 72, "humidity": 45}
        >>> weather = extract_data(raw, WeatherData)
        >>> print(weather.temp)
        72
    """
    ...
```

**Docstring Format**:
- One-line summary (imperative mood: "Extract data", not "Extracts data")
- Blank line
- Detailed description (if needed)
- Args section with types and descriptions
- Returns section with type and description
- Raises section with exception types and conditions
- Example section (for complex APIs)

### File Organization

**File Size Limits**:
- Hard limit: 800 lines per file
- Recommended: Under 400 lines
- If approaching 600 lines, plan modularization

**Module Structure** (top to bottom):
1. Module docstring
2. Imports (standard library → third-party → local)
3. Constants/types
4. Exception classes
5. Data models (Pydantic, dataclasses)
6. Main classes/functions
7. Helper functions (private, prefixed with `_`)

---

## 🟢 STANDARD: Common Operations

### ONE Command for Each Task

**Testing**:
```bash
pytest                          # Run all tests
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest --cov=edgar              # With coverage
pytest -v -s                    # Verbose with print output
```

**Type Checking**:
```bash
mypy src/                       # Type check all source code
mypy src/edgar/services/        # Type check specific module
```

**Linting**:
```bash
ruff check src/                 # Check all linting issues
ruff check --fix src/           # Auto-fix linting issues
```

**Formatting**:
```bash
black src/                      # Format all source code
black --check src/              # Check formatting without changes
```

**Combined Quality Check**:
```bash
# Run all quality checks before committing
mypy src/ && ruff check src/ && black --check src/ && pytest
```

### Project Structure Reference

```
/Users/masa/Projects/edgar/
├── src/edgar/                  # Source code
│   ├── __init__.py
│   ├── services/               # Core AI services
│   │   ├── sonnet_service.py       # Main orchestrator (PM + Coder modes)
│   │   ├── openrouter_client.py    # OpenRouter API client
│   │   └── context_manager.py      # Conversation context
│   ├── prompts/                # AI prompt templates
│   │   ├── pm_mode.txt             # PM Mode analysis prompt
│   │   └── coder_mode.txt          # Coder Mode generation prompt
│   ├── validators/             # Code validation pipeline
│   │   ├── ast_validator.py        # Python AST syntax validation
│   │   ├── constraint_validator.py # Architecture compliance (TODO)
│   │   └── accuracy_validator.py   # Example testing (TODO)
│   └── models/                 # Data models
│       ├── extraction_strategy.py  # ExtractionStrategy model
│       └── constraints.py          # ArchitectureConstraints model
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests (fast)
│   └── integration/            # Integration tests (slower)
├── docs/                       # Documentation
├── examples/                   # Example projects
│   └── weather_api/            # Weather API extractor example
├── pyproject.toml              # Python project config
├── .env                        # Environment variables (NEVER commit)
├── .gitignore                  # Git ignore patterns
└── README.md                   # Project overview
```

### Key Files and Their Purpose

**Service Layer**:
- `sonnet_service.py`: Orchestrates PM Mode → Coder Mode → Validation
- `openrouter_client.py`: HTTP client for Sonnet 4.5 via OpenRouter API
- `context_manager.py`: Manages conversation history for multi-turn refinement

**Data Models**:
- `extraction_strategy.py`: Defines structure of PM Mode output
- `constraints.py`: Defines architecture requirements for Coder Mode

**Validators**:
- `ast_validator.py`: Validates Python syntax using AST
- `constraint_validator.py`: Checks architecture compliance (DI, interfaces, types)
- `accuracy_validator.py`: Tests generated code against examples

**Configuration**:
- `pyproject.toml`: Dependencies, tool configs (black, ruff, mypy, pytest)
- `.env`: API keys and environment-specific config (NEVER commit)

---

## ⚪ OPTIONAL: Future Enhancements

### Planned Features (Not Yet Implemented)

**Validation Pipeline Completion**:
- Implement constraint validation (architecture compliance)
- Implement accuracy validation (test against examples)
- Add iterative refinement loop (validate → refine → re-generate)

**Conversation Context Improvements**:
- Token counting (currently approximated at 4 chars/token)
- Smart context trimming (keep important messages)
- Context compression for long conversations

**Code Generation Enhancements**:
- Support for GraphQL APIs (currently REST-focused)
- Support for XML/CSV response formats (currently JSON-focused)
- Custom error handling strategies per project

**Developer Experience**:
- CLI tool for running EDGAR from command line
- Web UI for interactive code generation
- VS Code extension for inline code generation

### Known Limitations

**Current Constraints**:
- PM Mode and Coder Mode prompts are text files (not templates with variables)
- Validation loop not implemented (manual refinement required)
- No support for streaming responses (full response only)
- Context manager uses character-based token estimation (not exact)

**Workarounds**:
- For prompt customization: Edit `pm_mode.txt` and `coder_mode.txt` directly
- For validation: Run validators manually after code generation
- For streaming: Future feature, not critical for MVP
- For token counting: Approximation works for most cases (200k token limit)

---

## Quick Reference: Environment Variables

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | ✅ Yes | `sk-or-v1-...` | OpenRouter API key for Sonnet 4.5 |
| `EDGAR_MODEL` | ⚠️  Optional | `anthropic/claude-sonnet-4.5` | Model to use (defaults to Sonnet 4.5) |

---

## Quick Reference: Important Types

```python
# Service Types
from edgar.services import Sonnet4_5Service, OpenRouterClient, ContextManager

# Model Types
from edgar.models import ExtractionStrategy, ArchitectureConstraints

# Validator Types
from edgar.validators import ASTValidator, ValidationResult

# Error Types
from edgar.services.openrouter_client import (
    OpenRouterError,
    OpenRouterAuthError,
    OpenRouterRateLimitError,
    OpenRouterServerError
)
```

---

## Getting Help

**For Issues**:
1. Check this CLAUDE.md first
2. Review README.md for project overview
3. Check existing code in `src/edgar/` for patterns
4. Review tests in `tests/` for usage examples

**For Bugs**:
1. Write a failing test first
2. Fix the bug
3. Verify test passes
4. Commit with `fix:` prefix

**For Features**:
1. Check "Future Enhancements" section above
2. Discuss architecture decision before implementing
3. Write tests first (TDD)
4. Implement feature
5. Update documentation
6. Commit with `feat:` prefix

---

**Last Updated**: 2025-12-28
**Project Location**: `/Users/masa/Projects/edgar/`
**Python Version**: 3.11+
**Main Branch**: `main`
