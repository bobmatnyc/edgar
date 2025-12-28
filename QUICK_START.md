# EDGAR Platform - Quick Start for AI Agents

**5-Minute Setup** | **Project**: EDGAR v0.1.0 | **Location**: `/Users/masa/Projects/edgar/`

---

## 1. Read Documentation (Priority Order)

```bash
# 🔴 CRITICAL - Read First
cat CLAUDE.md | grep -A 20 "🔴 CRITICAL"

# 🟡 IMPORTANT - Read Second
cat CLAUDE.md | grep -A 20 "🟡 IMPORTANT"

# Full Documentation
cat CLAUDE.md           # Comprehensive AI agent instructions
cat CODE_STRUCTURE.md   # Architecture and design patterns
cat README.md           # Project overview
```

---

## 2. Environment Setup

```bash
# Clone and navigate
cd /Users/masa/Projects/edgar

# Quick setup (installs deps + runs quality checks)
make dev

# Create .env file (REQUIRED)
cat > .env << EOF
OPENROUTER_API_KEY=sk-or-v1-your-key-here
EDGAR_MODEL=anthropic/claude-sonnet-4.5
EOF

# Activate virtual environment
source venv/bin/activate
```

---

## 3. Essential Commands

### Quality Checks (Run Before Committing)
```bash
make quality     # All checks: typecheck + lint + format + test
make typecheck   # Type checking with mypy (strict mode)
make lint        # Linting with ruff
make format      # Format with black
make test        # All tests
```

### Development Workflow
```bash
make test-unit          # Fast unit tests
make test-coverage      # With coverage report (90%+ required)
make lint-fix           # Auto-fix linting issues
make clean              # Clean build artifacts
make help               # Show all commands
```

---

## 4. Project Structure (Key Locations)

```
src/edgar/
├── services/
│   ├── sonnet_service.py      # 🔴 Main orchestrator (PM + Coder modes)
│   ├── openrouter_client.py   # HTTP client with retry logic
│   └── context_manager.py     # Conversation history
├── models/
│   ├── extraction_strategy.py # PM Mode output schema
│   └── constraints.py         # Coder Mode requirements
├── validators/
│   ├── ast_validator.py       # ✅ Syntax validation (implemented)
│   ├── constraint_validator.py # ⚠️  Architecture compliance (TODO)
│   └── accuracy_validator.py  # ⚠️  Example testing (TODO)
└── prompts/
    ├── pm_mode.txt            # PM Mode prompt template
    └── coder_mode.txt         # Coder Mode prompt template
```

---

## 5. Core Workflow (Two-Phase AI)

```python
from edgar.services import Sonnet4_5Service, OpenRouterClient, ContextManager
import os

# Initialize services (dependency injection)
client = OpenRouterClient(api_key=os.getenv("OPENROUTER_API_KEY"))
context = ContextManager(max_messages=20)
service = Sonnet4_5Service(client=client, context=context)

# Phase 1: PM Mode (Analysis)
strategy = await service.analyze_examples(
    examples=[{"temp": 72, "condition": "sunny"}],
    target_schema=WeatherData
)

# Phase 2: Coder Mode (Implementation)
code = await service.generate_code(
    strategy=strategy,
    architecture_constraints=ArchitectureConstraints.default()
)

# Phase 3: Validation (TODO - not yet implemented)
# validated_code = await service.validate_and_refine(code, examples)
```

---

## 6. Code Quality Standards

### Type Safety (100% Required)
```python
# ✅ CORRECT
async def fetch_data(url: str, timeout: float = 30.0) -> dict[str, Any]:
    """Fetch data from URL."""
    ...

# ❌ INCORRECT - Missing type hints
async def fetch_data(url, timeout=30.0):
    ...
```

### Dependency Injection Pattern
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class MyService:
    client: OpenRouterClient  # Injected
    context: ContextManager   # Injected

    async def do_work(self) -> str:
        messages = self.context.get_messages()
        response = await self.client.chat_completion(messages)
        return response
```

### Documentation (Required)
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
        KeyError: If required fields missing
    """
    ...
```

---

## 7. Security (🔴 CRITICAL)

### ✅ DO THIS
```bash
# Store API keys in .env (NEVER commit)
cat > .env << EOF
OPENROUTER_API_KEY=sk-or-v1-...
EOF

# Load from environment
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
```

### ❌ NEVER DO THIS
```python
# ❌ FORBIDDEN - Hardcoded API key
client = OpenRouterClient(api_key="sk-or-v1-abc123...")

# ❌ FORBIDDEN - Logging secrets
logger.info(f"Using API key: {api_key}")
```

### Pre-Commit Security Check
```bash
# Search for hardcoded secrets (should return nothing)
grep -r "sk-or-v1" src/ tests/

# Verify .env in .gitignore
grep -q ".env" .gitignore || echo "⚠️  WARNING: .env not in .gitignore!"
```

---

## 8. Testing Strategy

### Running Tests
```bash
make test              # All tests
make test-unit         # Fast unit tests only
make test-integration  # Slower integration tests
make test-coverage     # With coverage report (90%+ required)
```

### Writing Tests
```python
import pytest
from edgar.services import Sonnet4_5Service

@pytest.mark.asyncio
async def test_analyze_examples():
    """Test PM Mode analysis."""
    # Arrange
    service = Sonnet4_5Service(client=mock_client, context=mock_context)
    examples = [{"temp": 72, "humidity": 45}]

    # Act
    strategy = await service.analyze_examples(examples, WeatherData)

    # Assert
    assert strategy["data_source_type"] == "REST_API"
    assert "temperature" in strategy["extraction_patterns"]
```

---

## 9. Git Workflow

### Branch Naming
```bash
feature/description    # New features
fix/description        # Bug fixes
docs/description       # Documentation only
```

### Commit Message Format (Conventional Commits)
```bash
# Format
<type>: <description>

# Examples
git commit -m "feat: implement accuracy validator for generated code"
git commit -m "fix: resolve race condition in context manager"
git commit -m "docs: add architecture decision rationale to CLAUDE.md"
git commit -m "refactor: extract validation logic to separate module"
git commit -m "test: add integration tests for PM Mode"
```

### Pre-Commit Checklist
```bash
# 1. Run quality checks
make quality

# 2. Verify coverage
make test-coverage  # Must be 90%+

# 3. Check for secrets
grep -r "sk-or-v1" src/ tests/

# 4. Format commit message
git commit -m "type: description"
```

---

## 10. Common Issues and Solutions

### Issue: Import Error
```bash
# Solution: Install dependencies
make install
source venv/bin/activate
```

### Issue: API Authentication Failed
```bash
# Solution: Check .env file
cat .env | grep OPENROUTER_API_KEY

# Verify API key is valid
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/models
```

### Issue: Type Checking Errors
```bash
# Solution: Run mypy with verbose output
mypy src/ --show-error-codes --pretty

# Common fix: Add type hints
# Before: def fetch(self, url):
# After:  def fetch(self, url: str) -> dict[str, Any]:
```

### Issue: Test Failures
```bash
# Solution: Run tests with verbose output
pytest -v -s

# Run specific test
pytest tests/unit/test_sonnet_service.py::test_analyze_examples -v
```

---

## 11. Key Environment Variables

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | ✅ Yes | `sk-or-v1-...` | OpenRouter API key for Sonnet 4.5 |
| `EDGAR_MODEL` | ⚠️  Optional | `anthropic/claude-sonnet-4.5` | Model to use (defaults to Sonnet 4.5) |

---

## 12. Important File Locations

| File | Purpose |
|------|---------|
| `CLAUDE.md` | 🔴 AI agent instructions (READ FIRST) |
| `CODE_STRUCTURE.md` | Architecture documentation |
| `README.md` | Project overview |
| `Makefile` | Single-path workflow commands |
| `.env` | API keys and secrets (NEVER commit) |
| `.gitignore` | Git exclusions (includes .env) |
| `pyproject.toml` | Dependencies and tool configs |

---

## 13. Next Steps After Setup

1. **Read Critical Documentation**:
   ```bash
   cat CLAUDE.md | grep -A 50 "🔴 CRITICAL"
   ```

2. **Run Quality Checks**:
   ```bash
   make quality
   ```

3. **Review Architecture**:
   ```bash
   cat CODE_STRUCTURE.md
   ```

4. **Explore Code**:
   ```bash
   # Start with main orchestrator
   cat src/edgar/services/sonnet_service.py

   # Review data models
   cat src/edgar/models/extraction_strategy.py
   cat src/edgar/models/constraints.py
   ```

5. **Check TODO Items**:
   ```bash
   grep -r "TODO" src/
   # - ConstraintValidator implementation
   # - AccuracyValidator implementation
   # - validate_and_refine() implementation
   ```

---

## 14. Getting Help

**For Issues**:
1. Check `CLAUDE.md` (priority-ranked sections)
2. Review `CODE_STRUCTURE.md` (architecture patterns)
3. Check `README.md` (project overview)
4. Review tests in `tests/` (usage examples)

**For Bugs**:
1. Write failing test
2. Fix bug
3. Verify test passes
4. Commit with `fix:` prefix

**For Features**:
1. Check "Future Enhancements" in `CLAUDE.md`
2. Discuss architecture decision
3. Write tests first (TDD)
4. Implement feature
5. Update documentation
6. Commit with `feat:` prefix

---

## 15. Success Criteria

**Before declaring work complete**:
- ✅ `make quality` passes (typecheck + lint + format + test)
- ✅ Test coverage ≥ 90% (`make test-coverage`)
- ✅ No hardcoded secrets (`grep -r "sk-or-v1" src/ tests/`)
- ✅ Documentation updated (CLAUDE.md, CODE_STRUCTURE.md)
- ✅ Commit message follows Conventional Commits format
- ✅ All files under 800 lines
- ✅ 100% type hints (mypy strict)
- ✅ Comprehensive docstrings

---

**Status**: ✅ Ready for Development
**Setup Time**: < 5 minutes
**Main Branch**: `main`
**Python Version**: 3.11+

**Quick Start**: `make dev` → Create `.env` → `make quality` → Start coding!
