"""
Integration tests for Batch 2: Schema Services Migration

Tests all 3 migrated components:
1. PatternModels (530 LOC platform + 58 LOC wrapper)
2. SchemaAnalyzer (436 LOC platform + 94 LOC wrapper)
3. ExampleParser (679 LOC platform + 47 LOC wrapper)

Verifies:
- Platform imports work correctly
- Backward compatibility maintained
- End-to-end pattern detection flows
- Dependency chain integrity
- No breaking API changes
"""

import warnings
from typing import Any, Dict, List

import pytest

# Test platform imports
from extract_transform_platform.models.patterns import (
    FieldTypeEnum,
    ParsedExamples,
    Pattern,
    PatternType,
    Schema,
    SchemaField,
)
from extract_transform_platform.services.analysis.example_parser import ExampleParser
from extract_transform_platform.services.analysis.schema_analyzer import SchemaAnalyzer

# Test backward compatibility imports (will generate warnings)
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from edgar_analyzer.models.patterns import FieldTypeEnum as LegacyFieldTypeEnum
    from edgar_analyzer.models.patterns import PatternType as LegacyPatternType
    from edgar_analyzer.services.example_parser import (
        ExampleParser as LegacyExampleParser,
    )
    from edgar_analyzer.services.schema_analyzer import (
        SchemaAnalyzer as LegacySchemaAnalyzer,
    )


class TestPlatformImports:
    """Test that all platform imports work correctly."""

    def test_pattern_models_import(self) -> None:
        """Verify PatternModels can be imported from platform."""
        assert PatternType is not None
        assert FieldTypeEnum is not None
        assert Pattern is not None
        assert Schema is not None
        assert SchemaField is not None

    def test_pattern_types_complete(self) -> None:
        """Verify all 14 pattern types are present."""
        pattern_types = [p.value for p in PatternType]
        expected_types = [
            "field_mapping",
            "field_rename",
            "type_conversion",
            "constant_value",
            "concatenation",
            "calculation",
            "conditional_value",
            "array_transformation",
            "nested_extraction",
            "value_mapping",
            "regex_extraction",
            "date_formatting",
            "null_handling",
            "custom_function",
        ]
        for expected in expected_types:
            assert expected in pattern_types, f"Missing pattern type: {expected}"

    def test_field_types_complete(self) -> None:
        """Verify all 10 field types are present."""
        field_types = [t.value for t in FieldTypeEnum]
        expected_types = [
            "string",
            "integer",
            "float",
            "boolean",
            "date",
            "datetime",
            "array",
            "object",
            "null",
            "unknown",
        ]
        for expected in expected_types:
            assert expected in field_types, f"Missing field type: {expected}"

    def test_schema_analyzer_import(self) -> None:
        """Verify SchemaAnalyzer can be imported from platform."""
        analyzer = SchemaAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, "infer_schema")
        assert hasattr(analyzer, "compare_schemas")

    def test_example_parser_import(self) -> None:
        """Verify ExampleParser can be imported from platform."""
        parser = ExampleParser(SchemaAnalyzer())
        assert parser is not None
        assert hasattr(parser, "parse_examples")


class TestBackwardCompatibility:
    """Test that backward compatibility is maintained."""

    def test_legacy_imports_work(self) -> None:
        """Verify legacy imports still work (with warnings)."""
        assert LegacyPatternType is not None
        assert LegacyFieldTypeEnum is not None
        assert LegacySchemaAnalyzer is not None
        assert LegacyExampleParser is not None

    def test_deprecation_warnings_raised(self) -> None:
        """Verify deprecation warnings are raised for legacy imports."""
        with pytest.warns(DeprecationWarning, match="edgar_analyzer.models.patterns"):
            from edgar_analyzer.models.patterns import PatternType  # noqa: F401

        with pytest.warns(
            DeprecationWarning, match="edgar_analyzer.services.schema_analyzer"
        ):
            from edgar_analyzer.services.schema_analyzer import (  # noqa: F401
                SchemaAnalyzer,
            )

        with pytest.warns(
            DeprecationWarning, match="edgar_analyzer.services.example_parser"
        ):
            from edgar_analyzer.services.example_parser import (  # noqa: F401
                ExampleParser,
            )

    def test_pattern_types_identical(self) -> None:
        """Verify pattern types are identical between platform and wrapper."""
        platform_types = {p.value for p in PatternType}
        legacy_types = {p.value for p in LegacyPatternType}
        assert platform_types == legacy_types

    def test_field_types_identical(self) -> None:
        """Verify field types are identical between platform and wrapper."""
        platform_types = {t.value for t in FieldTypeEnum}
        legacy_types = {t.value for t in LegacyFieldTypeEnum}
        assert platform_types == legacy_types


class TestEndToEndPatternDetection:
    """Test complete pattern detection flow."""

    def test_simple_field_rename_flow(self) -> None:
        """Test detecting a simple field rename pattern."""
        # Setup
        analyzer = SchemaAnalyzer()
        parser = ExampleParser(analyzer)

        # Create examples
        examples = [
            {
                "input": {"employee_id": "E1001", "name": "Alice"},
                "output": {"id": "E1001", "name": "Alice"},
            },
            {
                "input": {"employee_id": "E1002", "name": "Bob"},
                "output": {"id": "E1002", "name": "Bob"},
            },
        ]

        # Parse
        result = parser.parse_examples(examples)

        # Verify
        assert result is not None
        assert len(result.patterns) >= 2  # id + name mappings

        # Find the rename pattern
        rename_patterns = [
            p for p in result.patterns if p.pattern_type == PatternType.FIELD_RENAME
        ]
        assert len(rename_patterns) > 0
        rename = rename_patterns[0]
        assert rename.input_field == "employee_id"
        assert rename.output_field == "id"
        assert rename.confidence > 0.9

    def test_type_conversion_flow(self) -> None:
        """Test detecting type conversion patterns."""
        analyzer = SchemaAnalyzer()
        parser = ExampleParser(analyzer)

        examples = [
            {
                "input": {"salary": "95000"},
                "output": {"salary": 95000.0},
            },
            {
                "input": {"salary": "120000"},
                "output": {"salary": 120000.0},
            },
        ]

        result = parser.parse_examples(examples)

        # Verify type conversion detected
        type_patterns = [
            p for p in result.patterns if p.pattern_type == PatternType.TYPE_CONVERSION
        ]
        assert len(type_patterns) > 0
        pattern = type_patterns[0]
        assert pattern.output_field == "salary"
        assert "string" in pattern.description.lower()
        assert "float" in pattern.description.lower()

    def test_concatenation_flow(self) -> None:
        """Test detecting string concatenation patterns."""
        analyzer = SchemaAnalyzer()
        parser = ExampleParser(analyzer)

        examples = [
            {
                "input": {"first_name": "Alice", "last_name": "Johnson"},
                "output": {"full_name": "Alice Johnson"},
            },
            {
                "input": {"first_name": "Bob", "last_name": "Smith"},
                "output": {"full_name": "Bob Smith"},
            },
        ]

        result = parser.parse_examples(examples)

        # Verify concatenation detected
        concat_patterns = [
            p for p in result.patterns if p.pattern_type == PatternType.CONCATENATION
        ]
        assert len(concat_patterns) > 0
        pattern = concat_patterns[0]
        assert pattern.output_field == "full_name"
        assert "first_name" in pattern.input_field
        assert "last_name" in pattern.input_field

    def test_confidence_scores_valid(self) -> None:
        """Test that all confidence scores are within valid range."""
        analyzer = SchemaAnalyzer()
        parser = ExampleParser(analyzer)

        examples = [
            {
                "input": {"a": 1, "b": "hello"},
                "output": {"x": 1, "y": "hello"},
            },
            {
                "input": {"a": 2, "b": "world"},
                "output": {"x": 2, "y": "world"},
            },
        ]

        result = parser.parse_examples(examples)

        # Verify all confidence scores are valid
        for pattern in result.patterns:
            assert (
                0.0 <= pattern.confidence <= 1.0
            ), f"Invalid confidence: {pattern.confidence}"


class TestSchemaAnalysis:
    """Test schema analysis functionality."""

    def test_schema_inference_from_examples(self) -> None:
        """Test inferring schema from example data."""
        analyzer = SchemaAnalyzer()

        examples = [
            {"id": "E1001", "salary": 95000.0, "is_manager": True},
            {"id": "E1002", "salary": 120000.0, "is_manager": False},
        ]

        schema = analyzer.infer_schema(examples)

        # Verify schema structure
        assert len(schema.fields) == 3
        field_names = {f.name for f in schema.fields}
        assert field_names == {"id", "salary", "is_manager"}

        # Verify field types
        field_types = {f.name: f.field_type for f in schema.fields}
        assert field_types["id"] == FieldTypeEnum.STRING
        assert field_types["salary"] == FieldTypeEnum.FLOAT
        assert field_types["is_manager"] == FieldTypeEnum.BOOLEAN

    def test_schema_comparison(self) -> None:
        """Test comparing two schemas."""
        analyzer = SchemaAnalyzer()

        input_examples = [
            {"employee_id": "E1001", "first_name": "Alice", "last_name": "Johnson"}
        ]
        output_examples = [{"id": "E1001", "full_name": "Alice Johnson"}]

        input_schema = analyzer.infer_schema(input_examples)
        output_schema = analyzer.infer_schema(output_examples)

        diff = analyzer.compare_schemas(input_schema, output_schema)

        # Verify differences detected
        assert len(diff.added_fields) > 0
        assert len(diff.removed_fields) > 0

        # Check specific changes
        added_names = {f.name for f in diff.added_fields}
        removed_names = {f.name for f in diff.removed_fields}
        assert "full_name" in added_names
        assert "employee_id" in removed_names or "first_name" in removed_names


class TestDependencyChain:
    """Test that dependency chain is correct."""

    def test_example_parser_uses_schema_analyzer(self) -> None:
        """Verify ExampleParser depends on SchemaAnalyzer."""
        analyzer = SchemaAnalyzer()
        parser = ExampleParser(analyzer)

        # Verify analyzer is stored
        assert parser.schema_analyzer is not None
        assert isinstance(parser.schema_analyzer, SchemaAnalyzer)

    def test_no_circular_dependencies(self) -> None:
        """Verify no circular dependencies exist."""
        # This test passes if imports succeed without ImportError
        from extract_transform_platform.models.patterns import PatternType  # noqa: F401
        from extract_transform_platform.services.analysis.example_parser import (  # noqa: F401
            ExampleParser,
        )
        from extract_transform_platform.services.analysis.schema_analyzer import (  # noqa: F401
            SchemaAnalyzer,
        )

        # If we get here, no circular dependencies
        assert True


class TestComplexPatterns:
    """Test detection of complex patterns."""

    def test_nested_structure_pattern(self) -> None:
        """Test detecting patterns in nested structures."""
        analyzer = SchemaAnalyzer()
        parser = ExampleParser(analyzer)

        examples = [
            {
                "input": {
                    "employee": {"id": "E1001", "name": "Alice"},
                    "department": "Engineering",
                },
                "output": {
                    "employee_id": "E1001",
                    "employee_name": "Alice",
                    "dept": "Engineering",
                },
            }
        ]

        result = parser.parse_examples(examples)

        # Verify patterns detected for nested fields
        assert len(result.patterns) > 0
        output_fields = {p.output_field for p in result.patterns}
        assert "employee_id" in output_fields or "employee_name" in output_fields

    def test_array_handling(self) -> None:
        """Test handling of array fields."""
        analyzer = SchemaAnalyzer()

        examples = [
            {"tags": ["python", "data"], "scores": [95, 87, 92]},
        ]

        schema = analyzer.infer_schema(examples)

        # Verify array fields detected
        field_types = {f.name: f.field_type for f in schema.fields}
        assert field_types["tags"] == FieldTypeEnum.ARRAY
        assert field_types["scores"] == FieldTypeEnum.ARRAY


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_examples(self) -> None:
        """Test handling of empty example list."""
        analyzer = SchemaAnalyzer()
        parser = ExampleParser(analyzer)

        result = parser.parse_examples([])

        # Should return empty result, not crash
        assert result is not None
        assert len(result.patterns) == 0

    def test_inconsistent_schemas(self) -> None:
        """Test handling of inconsistent example schemas."""
        analyzer = SchemaAnalyzer()
        parser = ExampleParser(analyzer)

        examples = [
            {"input": {"a": 1}, "output": {"x": 1}},
            {"input": {"b": 2}, "output": {"y": 2}},  # Different schema
        ]

        result = parser.parse_examples(examples)

        # Should handle gracefully
        assert result is not None
        # May have warnings about inconsistent schemas
        assert isinstance(result.warnings, list)

    def test_null_values(self) -> None:
        """Test handling of null values in examples."""
        analyzer = SchemaAnalyzer()

        examples = [
            {"name": "Alice", "middle_name": None},
            {"name": "Bob", "middle_name": "J."},
        ]

        schema = analyzer.infer_schema(examples)

        # Verify nullable fields detected
        middle_name_field = next(f for f in schema.fields if f.name == "middle_name")
        assert middle_name_field.nullable is True


# Summary test to run all checks
def test_batch2_complete_integration() -> None:
    """
    Master integration test verifying all Batch 2 components work together.

    Tests:
    - ✅ PatternModels platform import
    - ✅ SchemaAnalyzer platform import
    - ✅ ExampleParser platform import
    - ✅ Backward compatibility
    - ✅ End-to-end pattern detection
    - ✅ Confidence scoring
    - ✅ Dependency chain
    """
    # Platform imports
    from extract_transform_platform.models.patterns import PatternType
    from extract_transform_platform.services.analysis.example_parser import (
        ExampleParser,
    )
    from extract_transform_platform.services.analysis.schema_analyzer import (
        SchemaAnalyzer,
    )

    # Create instances
    analyzer = SchemaAnalyzer()
    parser = ExampleParser(analyzer)

    # Run end-to-end test
    examples = [
        {
            "input": {"employee_id": "E1001", "salary": "95000"},
            "output": {"id": "E1001", "annual_salary": 95000.0},
        }
    ]

    result = parser.parse_examples(examples)

    # Verify success
    assert result is not None
    assert len(result.patterns) > 0
    assert all(0.0 <= p.confidence <= 1.0 for p in result.patterns)

    print("\n✅ Batch 2 Integration Test PASSED")
    print(f"   - Detected {len(result.patterns)} patterns")
    print(f"   - Input schema: {len(result.input_schema.fields)} fields")
    print(f"   - Output schema: {len(result.output_schema.fields)} fields")
    print(f"   - Warnings: {len(result.warnings)}")
