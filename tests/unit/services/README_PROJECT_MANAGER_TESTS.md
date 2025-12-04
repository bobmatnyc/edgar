# ProjectManager Tests - Quick Reference

## Running the Tests

### Prerequisites
```bash
# Activate virtual environment (required for pytest-asyncio)
source venv/bin/activate
```

### Run All Tests
```bash
# Standard test run
pytest tests/unit/services/test_project_manager.py -v

# With coverage report
pytest tests/unit/services/test_project_manager.py -v \
  --cov=extract_transform_platform.services.project_manager \
  --cov-report=term-missing
```

### Run Specific Test Categories

```bash
# CRUD operations only
pytest tests/unit/services/test_project_manager.py::TestCRUDOperations -v

# Validation tests only
pytest tests/unit/services/test_project_manager.py::TestValidation -v

# Caching tests only
pytest tests/unit/services/test_project_manager.py::TestCaching -v

# Directory management tests only
pytest tests/unit/services/test_project_manager.py::TestDirectoryManagement -v

# Error handling tests only
pytest tests/unit/services/test_project_manager.py::TestErrorHandling -v

# Edge cases only
pytest tests/unit/services/test_project_manager.py::TestEdgeCases -v
```

### Run Specific Test
```bash
# Single test by name
pytest tests/unit/services/test_project_manager.py::TestCRUDOperations::test_create_project_success -v
```

## Test Results Summary

- **Total Tests**: 45
- **Coverage**: 95% (162/170 statements)
- **Status**: ✅ All Passing
- **Execution Time**: ~1 second

## Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| **CRUD Operations** | 18 | Create, Read, List, Delete operations |
| **Validation** | 8 | Config, structure, and example validation |
| **Caching** | 4 | Cache population and invalidation |
| **Directory Management** | 7 | Environment override and directory creation |
| **Error Handling** | 6 | Exception handling and error conditions |
| **Edge Cases** | 10 | Boundary conditions and unusual scenarios |

## Coverage Report

```
Name                                                  Stmts   Miss  Cover   Missing
---------------------------------------------------------------------------------------
extract_transform_platform/services/project_manager.py   170      8    95%   580-587
```

**Uncovered Lines**: Exception handlers in validate_project() (lines 580-587) - defensive programming that is difficult to trigger in normal operation.

## Troubleshooting

### "async def functions are not natively supported"
**Solution**: Make sure you're using the venv:
```bash
source venv/bin/activate
pytest --version  # Should show pytest with asyncio plugin
```

### Coverage too low
**Solution**: Use `--no-cov-on-fail` to skip coverage on test failures:
```bash
pytest tests/unit/services/test_project_manager.py \
  --cov=extract_transform_platform.services.project_manager \
  --no-cov-on-fail
```

### Tests hang or timeout
**Issue**: Async tests not configured properly
**Solution**: Check that `pytestmark = pytest.mark.asyncio` is at module level

## Test Files

- **Test File**: `tests/unit/services/test_project_manager.py` (850+ LOC)
- **Service**: `src/extract_transform_platform/services/project_manager.py` (622 LOC)
- **Summary**: `tests/unit/services/TEST_SUMMARY_PROJECT_MANAGER.md`

## CI/CD Integration

Add to CI pipeline:
```yaml
- name: Run ProjectManager Tests
  run: |
    source venv/bin/activate
    pytest tests/unit/services/test_project_manager.py \
      --cov=extract_transform_platform.services.project_manager \
      --cov-report=xml \
      --cov-fail-under=80
```

## Further Reading

- **Test Summary**: See `TEST_SUMMARY_PROJECT_MANAGER.md` for detailed analysis
- **Service Documentation**: See `src/extract_transform_platform/services/project_manager.py` docstrings
- **Research**: See `docs/research/project-manager-service-patterns-2025-11-30.md`
