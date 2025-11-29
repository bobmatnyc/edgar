# EDGAR Platform

**E**xample-**D**riven **G**eneration with **A**I **R**easoning

AI-powered data extraction platform that generates production-ready Python code from API response examples using Sonnet 4.5.

## Overview

EDGAR uses a two-phase AI approach to transform API response examples into type-safe, validated data extraction code:

1. **PM Mode (Analysis)**: Sonnet 4.5 analyzes API response examples and designs a structured extraction strategy
2. **Coder Mode (Implementation)**: Sonnet 4.5 generates production-ready Python code implementing the strategy
3. **Validation Pipeline**: Automated validation ensures code quality, correctness, and architecture compliance

### Key Features

- **Example-Driven Design**: Show examples, get code - no manual API documentation needed
- **Type-Safe Code Generation**: Pydantic models with full type hints
- **Architecture Enforcement**: Generated code follows DI patterns and interfaces
- **Validation Pipeline**: AST validation, constraint checking, accuracy testing
- **Conversation Context**: Iterative refinement through multi-turn conversations

## Quick Start

### 1. Setup Virtual Environment

```bash
cd /Users/masa/Projects/edgar-platform
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure OpenRouter API Key

Create `.env` file with your OpenRouter API key:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
EDGAR_MODEL=anthropic/claude-sonnet-4.5
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=edgar --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
```

### 4. Type Checking and Linting

```bash
# Type checking
mypy src/

# Linting
ruff check src/

# Formatting
black src/
```

## Project Structure

```
edgar-platform/
├── src/edgar/
│   ├── services/           # Core AI services
│   │   ├── sonnet_service.py      # Main Sonnet4_5Service orchestrator
│   │   ├── openrouter_client.py   # OpenRouter API client
│   │   └── context_manager.py     # Conversation context management
│   ├── prompts/           # AI prompt templates
│   │   ├── pm_mode.txt           # PM mode analysis prompt
│   │   └── coder_mode.txt        # Coder mode generation prompt
│   ├── validators/        # Code validation pipeline
│   │   ├── ast_validator.py      # Python AST syntax validation
│   │   ├── constraint_validator.py # Architecture constraint checking
│   │   └── accuracy_validator.py  # Example accuracy testing
│   └── models/            # Data models
│       ├── extraction_strategy.py # Strategy data model
│       └── constraints.py         # Architecture constraints
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
└── examples/
    └── weather_api/       # Example project (Weather API extractor)
```

## Architecture

### Service-Oriented Design

EDGAR follows service-oriented architecture with dependency injection:

```python
# Example: Using Sonnet4_5Service
from edgar.services import Sonnet4_5Service, OpenRouterClient, ContextManager

# Initialize with dependency injection
client = OpenRouterClient(api_key="sk-or-v1-...")
context = ContextManager(max_messages=20)
service = Sonnet4_5Service(client=client, context=context)

# PM Mode: Analyze examples
strategy = await service.analyze_examples(
    examples=[{"temp": 72, "condition": "sunny"}],
    target_schema=WeatherData
)

# Coder Mode: Generate code
code = await service.generate_code(
    strategy=strategy,
    constraints=architecture_constraints
)
```

### Validation Pipeline

Generated code passes through three validation stages:

1. **AST Validation**: Ensures syntactically valid Python code
2. **Constraint Validation**: Checks architecture compliance (interfaces, DI, type hints)
3. **Accuracy Validation**: Tests code against provided examples

## Development

### Requirements

- **Python**: 3.11 or higher
- **OpenRouter API Key**: Required for Sonnet 4.5 access
- **Dependencies**: See `pyproject.toml`

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Write Tests First** (TDD)
   ```bash
   # Create test file
   touch tests/unit/test_your_feature.py

   # Run tests (they should fail)
   pytest tests/unit/test_your_feature.py
   ```

3. **Implement Feature**
   ```bash
   # Create implementation file
   touch src/edgar/your_feature.py

   # Run tests until they pass
   pytest tests/unit/test_your_feature.py
   ```

4. **Validate Code Quality**
   ```bash
   # Type checking
   mypy src/

   # Linting
   ruff check src/

   # Formatting
   black src/

   # Full test suite
   pytest --cov=edgar
   ```

5. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature
   ```

### Code Quality Standards

- **Type Safety**: 100% mypy strict compliance
- **Test Coverage**: 90%+ coverage required
- **Code Style**: Black + Ruff (PEP 8)
- **Documentation**: Docstrings for all public APIs
- **Complexity**: Max cyclomatic complexity of 10

## Examples

### Weather API Extractor

See `examples/weather_api/` for a complete example of using EDGAR to generate a weather data extractor.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests and implementation
4. Ensure all tests pass and coverage is >90%
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Related Projects

- **mcp-smartthings**: SmartThings MCP server (parent project)
- **OpenRouter**: AI model routing platform

## Support

For issues and questions, please open an issue on GitHub.
