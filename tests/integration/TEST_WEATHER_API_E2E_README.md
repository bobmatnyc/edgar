# Weather API E2E Tests - Quick Reference

**Test File**: `tests/integration/test_weather_api_e2e.py`
**Test Count**: 10 tests
**Pass Rate**: 100% (10/10 passing)
**Execution Time**: <1 second

---

## Quick Start

### Run All Tests
```bash
pytest tests/integration/test_weather_api_e2e.py -v
```

### Run Specific Test Class
```bash
# Run lifecycle tests only
pytest tests/integration/test_weather_api_e2e.py::TestWeatherAPILifecycle -v

# Run example tests only
pytest tests/integration/test_weather_api_e2e.py::TestWeatherAPIExamples -v

# Run code generation tests only
pytest tests/integration/test_weather_api_e2e.py::TestWeatherAPICodeGeneration -v
```

### Run Specific Test
```bash
pytest tests/integration/test_weather_api_e2e.py::TestWeatherAPILifecycle::test_weather_api_smoke_test -v
```

### Run with Coverage
```bash
pytest tests/integration/test_weather_api_e2e.py --cov=extract_transform_platform --cov-report=html
```

---

## Test Catalog

### TestWeatherAPILifecycle (4 tests)

#### 1. test_weather_api_complete_lifecycle
**Purpose**: Validate complete project workflow from loading to code validation

**What it tests**:
- ProjectManager loads weather_api_extractor project
- project.yaml is valid (7 examples, proper config)
- All 7 examples load successfully
- ExampleParser extracts transformation patterns
- High-confidence patterns detected (≥0.9)
- Generated code exists and compiles

**Dependencies**: T7 (ProjectManager), T3 (ExampleParser)

**Execution time**: ~0.3 seconds

---

#### 2. test_weather_api_cli_commands
**Purpose**: Verify CLI validate command works end-to-end

**What it tests**:
- `edgar-analyzer project validate weather_api_extractor` executes
- Validation passes
- Output format is correct

**Dependencies**: T8 (CLI refactoring)

**Execution time**: ~0.1 seconds

---

#### 3. test_weather_api_cli_list
**Purpose**: Verify CLI list command includes weather_api_extractor

**What it tests**:
- `edgar-analyzer project list` executes
- weather_api_extractor appears in list

**Dependencies**: T8 (CLI refactoring)

**Execution time**: ~0.1 seconds

---

#### 4. test_weather_api_smoke_test
**Purpose**: Fast validation (<1s) without file system changes

**What it tests**:
- Project directory exists
- Examples directory exists (7 JSON files)
- project.yaml is valid
- Quick validation passes

**Use case**: CI/CD fast path, pre-commit checks

**Execution time**: <1 second

---

### TestWeatherAPIExamples (2 tests)

#### 5. test_weather_api_examples_consistency
**Purpose**: Validate all 7 examples have consistent schema

**What it tests**:
- All 7 examples load successfully
- Input schema consistent (coord, main, weather fields)
- Output schema consistent (city, country, temperature_c, etc.)
- SchemaAnalyzer infers schemas correctly
- High-confidence patterns detected

**Dependencies**: T3 (SchemaAnalyzer)

**Execution time**: ~0.2 seconds

---

#### 6. test_weather_api_examples_valid_json
**Purpose**: Ensure all example files are valid JSON

**What it tests**:
- All JSON files in examples/ parse successfully
- No malformed JSON

**Execution time**: <0.1 seconds

---

### TestWeatherAPICodeGeneration (4 tests)

#### 7. test_weather_api_generation_with_missing_examples
**Purpose**: Verify graceful error handling for empty examples

**What it tests**:
- Attempt generation with empty examples list
- Appropriate error raised (ExampleParsingError, ValueError, CodeGenerationError)
- Error message mentions examples or empty

**Dependencies**: T12 (Error handling)

**Execution time**: <0.1 seconds

---

#### 8. test_weather_api_generation_with_malformed_examples
**Purpose**: Verify graceful error handling for invalid examples

**What it tests**:
- Create malformed example (empty output)
- Attempt code generation
- Appropriate error raised
- Error message is informative

**Dependencies**: T12 (Error handling)

**Execution time**: <0.1 seconds

---

#### 9. test_weather_api_generated_code_quality
**Purpose**: Validate quality of generated code

**What it tests**:
- Find generated Python files (extractor.py, models.py, test_extractor.py)
- AST validation (syntax check)
- Type hints present
- Docstrings present
- Code compiles

**Note**: Skips if no generated code exists (requires API keys)

**Execution time**: ~0.1 seconds

---

#### 10. test_weather_api_progress_tracking
**Purpose**: Verify T10 progress tracking integration

**What it tests**:
- `on_progress` parameter exists in generate()
- GenerationProgress model structure correct
- Progress percentage calculation works

**Dependencies**: T10 (Progress tracking)

**Execution time**: <0.1 seconds

---

## Test Fixtures

### Available Fixtures

```python
project_manager        # ProjectManager instance from DI container
code_generator         # CodeGeneratorService instance
schema_analyzer        # SchemaAnalyzer instance
example_parser         # ExampleParser with analyzer
weather_api_project_path  # Path to projects/weather_api/
weather_api_examples   # All 7 examples loaded from JSON
weather_api_config     # ProjectConfig from project.yaml
cli_runner             # Click CLI test runner
```

### Using Fixtures

```python
def test_my_feature(
    project_manager: ProjectManager,
    weather_api_examples: List[Dict[str, Any]]
) -> None:
    """Example test using fixtures."""
    project = await project_manager.get_project("weather_api_extractor")
    assert len(weather_api_examples) == 7
```

---

## Common Issues & Solutions

### Issue: Project not found
**Error**: `AssertionError: Project should exist`

**Solution**: Use full project name `weather_api_extractor` (from YAML), not directory name `weather_api`

```python
# ❌ Wrong
project = await project_manager.get_project("weather_api")

# ✅ Correct
project = await project_manager.get_project("weather_api_extractor")
```

---

### Issue: Example parsing AttributeError
**Error**: `AttributeError: 'dict' object has no attribute 'input'`

**Solution**: Convert dict examples to ExampleConfig objects

```python
from extract_transform_platform.models.project_config import ExampleConfig

# Convert dicts to ExampleConfig objects
example_configs = [
    ExampleConfig(
        input=ex["input"],
        output=ex["output"],
        description=ex.get("description", "")
    )
    for ex in weather_api_examples
]

parsed = example_parser.parse_examples(example_configs)
```

---

### Issue: CLI tests failing with 'Provide' object error
**Error**: `'Provide' object has no attribute 'validate_project'`

**Solution**: Wire the DI container before invoking CLI commands

```python
def test_cli_command(cli_runner: CliRunner) -> None:
    # Wire container first
    container = Container()
    container.wire(modules=[__name__])

    # Now run CLI command
    result = cli_runner.invoke(project, ["validate", "weather_api_extractor"])
```

---

### Issue: Generated code not found
**Error**: `AssertionError: Should have generated Python files`

**Solution**: Test skips gracefully if no code exists (requires API keys). This is expected behavior for E2E tests without API access.

The test validates existing generated code when present, but doesn't require fresh generation.

---

## Performance Guidelines

### Fast Tests (<0.1s)
- `test_weather_api_smoke_test`
- `test_weather_api_examples_valid_json`
- Error handling tests

### Medium Tests (0.1-0.3s)
- `test_weather_api_cli_commands`
- `test_weather_api_cli_list`
- `test_weather_api_examples_consistency`

### Comprehensive Tests (>0.3s)
- `test_weather_api_complete_lifecycle` (validates full workflow)

**Recommendation**: Run smoke test first in CI/CD for fast feedback, then full suite.

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Weather API E2E Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Run smoke test (fast)
      run: |
        pytest tests/integration/test_weather_api_e2e.py::TestWeatherAPILifecycle::test_weather_api_smoke_test -v

    - name: Run full E2E suite
      run: |
        pytest tests/integration/test_weather_api_e2e.py -v --tb=short

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: test-results/
```

---

## Test Maintenance

### When to Update Tests

1. **Project structure changes**: Update `weather_api_project_path` logic
2. **Example format changes**: Update ExampleConfig conversion logic
3. **New CLI commands**: Add new CLI test methods
4. **API changes**: Update fixture signatures

### Adding New Tests

```python
class TestWeatherAPINewFeature:
    """Test new feature."""

    @pytest.mark.asyncio
    async def test_new_feature(
        self,
        project_manager: ProjectManager,
        weather_api_config: ProjectConfig,
    ) -> None:
        """Test new feature description.

        Steps:
        1. Step 1 description
        2. Step 2 description
        3. Step 3 description

        Success Criteria:
        - Criterion 1
        - Criterion 2
        - Criterion 3
        """
        # Implementation
        pass
```

---

## Related Documentation

- **Test Report**: `T13_WEATHER_API_E2E_TEST_REPORT.md` - Comprehensive test documentation
- **Completion Summary**: `T13_COMPLETION_SUMMARY.md` - High-level overview
- **Platform Usage**: `docs/guides/PLATFORM_USAGE.md` - Platform API examples
- **CLI Usage**: `docs/guides/CLI_USAGE.md` - CLI command reference

---

## Contact & Support

**Questions?** Check the comprehensive documentation:
- `T13_WEATHER_API_E2E_TEST_REPORT.md` - Detailed test descriptions
- `T13_COMPLETION_SUMMARY.md` - Success criteria & learnings

**Found a bug?** Please include:
1. Test name that failed
2. Error message
3. Steps to reproduce
4. Expected vs actual behavior

---

**Last Updated**: 2025-12-03
**Test Suite Version**: 1.0.0
**Status**: ✅ All 10 tests passing (100%)
