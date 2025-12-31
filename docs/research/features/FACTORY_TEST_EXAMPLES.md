# Factory.py Test Examples - Code Snippets

**Purpose**: Reference examples of test patterns used in test_factory.py
**Use Case**: Template for testing other factory pattern implementations

---

## Example 1: Testing Generator Creation

```python
def test_create_excel_generator(self):
    """Test creating Excel generator."""
    generator = ReportGeneratorFactory.create("excel")
    
    # Verify specific type
    assert isinstance(generator, ExcelReportGenerator)
    
    # Verify base class
    assert isinstance(generator, BaseReportGenerator)
    
    # Verify protocol compliance
    assert hasattr(generator, "generate")
    assert hasattr(generator, "get_supported_features")
```

**Pattern**: Create → Verify Type → Verify Interface
**Coverage**: Happy path for format creation

---

## Example 2: Testing Case Insensitivity

```python
def test_create_case_insensitive(self):
    """Test that format is case-insensitive."""
    gen1 = ReportGeneratorFactory.create("excel")
    gen2 = ReportGeneratorFactory.create("EXCEL")
    gen3 = ReportGeneratorFactory.create("Excel")
    
    # All should be same class
    assert type(gen1) == type(gen2) == type(gen3)
```

**Pattern**: Create Multiple Variants → Verify Same Type
**Coverage**: Edge case for case-insensitive matching

---

## Example 3: Testing Error Handling

```python
def test_unsupported_format_raises(self):
    """Test that unsupported format raises ValueError."""
    with pytest.raises(ValueError, match="Unsupported report format"):
        ReportGeneratorFactory.create("unsupported")
    
    with pytest.raises(ValueError, match="Unsupported report format"):
        ReportGeneratorFactory.create("invalid_format")
```

**Pattern**: pytest.raises → Verify Exception Type → Verify Error Message
**Coverage**: Error path for invalid format

---

## Example 4: Testing Error Message Quality

```python
def test_error_message_lists_supported_formats(self):
    """Test that error message lists supported formats."""
    try:
        ReportGeneratorFactory.create("invalid")
        pytest.fail("Should have raised ValueError")
    except ValueError as e:
        error_msg = str(e)
        assert "excel" in error_msg
        assert "xlsx" in error_msg
        assert "pdf" in error_msg
        assert "docx" in error_msg
        assert "pptx" in error_msg
```

**Pattern**: Try-Except → Inspect Error Message → Verify Content
**Coverage**: Error message helpfulness

---

## Example 5: Testing List Retrieval

```python
def test_get_supported_formats(self):
    """Test getting list of supported formats."""
    formats = ReportGeneratorFactory.get_supported_formats()
    
    # Verify type
    assert isinstance(formats, list)
    
    # Verify contents
    assert "excel" in formats
    assert "xlsx" in formats
    assert "pdf" in formats
    assert "docx" in formats
    assert "pptx" in formats
    
    # Verify sorting
    assert formats == sorted(formats)
    
    # Verify count
    assert len(formats) == 5
```

**Pattern**: Call Method → Verify Return Type → Verify Contents → Verify Ordering
**Coverage**: Format listing functionality

---

## Example 6: Testing Boolean Checks

```python
def test_is_format_supported_true(self):
    """Test checking if format is supported (positive case)."""
    assert ReportGeneratorFactory.is_format_supported("excel") is True
    assert ReportGeneratorFactory.is_format_supported("xlsx") is True
    assert ReportGeneratorFactory.is_format_supported("pdf") is True
    assert ReportGeneratorFactory.is_format_supported("docx") is True
    assert ReportGeneratorFactory.is_format_supported("pptx") is True
    assert ReportGeneratorFactory.is_format_supported("EXCEL") is True  # Case-insensitive

def test_is_format_supported_false(self):
    """Test checking if format is supported (negative case)."""
    assert ReportGeneratorFactory.is_format_supported("invalid") is False
    assert ReportGeneratorFactory.is_format_supported("unknown") is False
```

**Pattern**: Call Method → Verify Boolean Result (True/False)
**Coverage**: Format validation helper

---

## Example 7: Testing Custom Registration

```python
def test_register_custom_generator(self):
    """Test registering a custom generator."""
    
    # Define custom generator
    class CustomReportGenerator(BaseReportGenerator):
        def generate(self, data, output_path, config):
            return output_path
    
    # Register custom generator
    ReportGeneratorFactory.register("custom", CustomReportGenerator)
    
    # Verify registration
    assert "custom" in ReportGeneratorFactory.get_supported_formats()
    
    # Verify creation
    generator = ReportGeneratorFactory.create("custom")
    assert isinstance(generator, CustomReportGenerator)
    
    # Clean up (important!)
    del ReportGeneratorFactory._generators["custom"]
```

**Pattern**: Define Custom Class → Register → Verify → Cleanup
**Coverage**: Extensibility testing

---

## Example 8: Testing Type Validation

```python
def test_register_non_generator_class_raises(self):
    """Test that registering non-generator class raises TypeError."""
    
    # Define non-generator class
    class NotAGenerator:
        pass
    
    # Attempt registration
    with pytest.raises(TypeError, match="must inherit from BaseReportGenerator"):
        ReportGeneratorFactory.register("invalid", NotAGenerator)
```

**Pattern**: Define Invalid Class → pytest.raises → Verify TypeError
**Coverage**: Type safety enforcement

---

## Example 9: Testing Class Retrieval

```python
def test_get_generator_class(self):
    """Test getting generator class without instantiating."""
    GeneratorClass = ReportGeneratorFactory.get_generator_class("excel")
    
    # Verify correct class
    assert GeneratorClass == ExcelReportGenerator
    
    # Verify it's the class, not an instance
    assert not isinstance(GeneratorClass, ExcelReportGenerator)
```

**Pattern**: Get Class → Verify Type Equality → Verify Not Instance
**Coverage**: Class introspection

---

## Example 10: Testing Instance Independence

```python
def test_multiple_create_calls_independent(self):
    """Test that multiple create calls return independent instances."""
    gen1 = ReportGeneratorFactory.create("excel")
    gen2 = ReportGeneratorFactory.create("excel")
    
    # Should be different instances
    assert gen1 is not gen2
    
    # But same class
    assert type(gen1) == type(gen2)
```

**Pattern**: Create Multiple → Verify Identity Difference → Verify Type Same
**Coverage**: Factory behavior validation

---

## Example 11: Testing Integration

```python
def test_created_generator_has_features(self):
    """Test that created generator has features."""
    generator = ReportGeneratorFactory.create("excel")
    features = generator.get_supported_features()
    
    # Verify features list
    assert isinstance(features, list)
    assert len(features) > 0
    assert "tables" in features
```

**Pattern**: Create → Call Instance Method → Verify Results
**Coverage**: Integration between factory and instances

---

## Test Organization Pattern

```python
class TestReportGeneratorFactory:
    """Test suite for ReportGeneratorFactory."""
    
    def test_create_excel_generator(self):
        """Test Excel generator creation."""
        # Test code here
    
    def test_create_pdf_generator(self):
        """Test PDF generator creation."""
        # Test code here
    
    # ... more tests


class TestGeneratorRegistration:
    """Test registering custom generators."""
    
    def test_register_custom_generator(self):
        """Test custom generator registration."""
        # Test code here
    
    # ... more tests


class TestFactoryIntegration:
    """Test factory integration with generators."""
    
    def test_created_generator_has_features(self):
        """Test generator features."""
        # Test code here
    
    # ... more tests
```

**Pattern**: Group Related Tests in Classes
**Benefits**: Better organization, easier to navigate

---

## Common Assertion Patterns

### Type Checking
```python
assert isinstance(generator, ExcelReportGenerator)
assert isinstance(generator, BaseReportGenerator)
assert isinstance(generator, IReportGenerator)
```

### Equality Checking
```python
assert GeneratorClass == ExcelReportGenerator
assert type(gen1) == type(gen2)
```

### Containment Checking
```python
assert "excel" in formats
assert "tables" in features
```

### Boolean Checking
```python
assert is_supported is True
assert is_supported is False
```

### Attribute Checking
```python
assert hasattr(generator, "generate")
assert hasattr(generator, "get_supported_features")
assert callable(generator.generate)
```

### Identity Checking
```python
assert gen1 is not gen2  # Different instances
```

### Exception Checking
```python
with pytest.raises(ValueError, match="pattern"):
    factory.create("invalid")
```

---

## Cleanup Pattern for Tests with Side Effects

```python
def test_register_custom_generator(self):
    """Test registering a custom generator."""
    
    class CustomReportGenerator(BaseReportGenerator):
        def generate(self, data, output_path, config):
            return output_path
    
    # Register
    ReportGeneratorFactory.register("custom", CustomReportGenerator)
    
    # Test
    assert "custom" in ReportGeneratorFactory.get_supported_formats()
    
    # IMPORTANT: Clean up to avoid affecting other tests
    del ReportGeneratorFactory._generators["custom"]
```

**Key Point**: Always clean up modifications to class-level state

---

## Error Message Testing Pattern

```python
def test_error_message_quality(self):
    """Test that error messages are helpful."""
    try:
        factory.create("invalid")
        pytest.fail("Should have raised ValueError")
    except ValueError as e:
        error_msg = str(e)
        # Verify error message includes helpful info
        assert "invalid" in error_msg
        assert "Supported formats" in error_msg
        assert "excel" in error_msg
```

**Pattern**: Try-Except → Capture Exception → Inspect Message
**Purpose**: Ensure error messages help users debug issues

---

## Testing Best Practices Demonstrated

1. **Clear Test Names**: `test_create_excel_generator` is self-explanatory
2. **One Assertion Focus**: Each test focuses on one behavior
3. **AAA Pattern**: Arrange → Act → Assert
4. **Cleanup**: Clean up side effects (registered generators)
5. **Documentation**: Docstrings explain what's being tested
6. **Independence**: Tests don't depend on execution order
7. **Coverage**: Test both happy paths and error paths
8. **Edge Cases**: Test case-insensitivity, aliases, etc.

---

## Reusable Test Template

```python
def test_<feature>_<scenario>(self):
    """Test <what is being tested>."""
    # ARRANGE: Set up test data
    input_data = "test_input"
    
    # ACT: Execute the code under test
    result = factory.method(input_data)
    
    # ASSERT: Verify the results
    assert result == expected_value
    assert isinstance(result, ExpectedType)
    
    # CLEANUP: Clean up any side effects (if needed)
    # del factory._state["test_key"]
```

---

**Date**: 2025-12-03
**Source**: tests/unit/reports/test_factory.py
**Total Examples**: 11 test patterns
**Use Case**: Reference for implementing similar test suites
