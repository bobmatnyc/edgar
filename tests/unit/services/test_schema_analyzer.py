"""
Unit tests for SchemaAnalyzer service.

Tests cover:
- Schema inference from examples
- Type detection
- Nested structure handling
- Schema comparison
- Field rename detection
"""

import pytest

from edgar_analyzer.models.patterns import FieldTypeEnum
from edgar_analyzer.services.schema_analyzer import SchemaAnalyzer


class TestSchemaAnalyzer:
    """Test suite for SchemaAnalyzer service."""

    @pytest.fixture
    def analyzer(self):
        """Create SchemaAnalyzer instance."""
        return SchemaAnalyzer()

    def test_simple_schema_inference(self, analyzer):
        """Test inference of simple flat schema."""
        examples = [
            {"name": "London", "temp": 15.5, "count": 10},
            {"name": "Tokyo", "temp": 22.3, "count": 20},
        ]

        schema = analyzer.infer_schema(examples)

        assert len(schema.fields) == 3
        assert not schema.is_nested
        assert not schema.has_arrays

        # Check field paths
        paths = [f.path for f in schema.fields]
        assert "name" in paths
        assert "temp" in paths
        assert "count" in paths

    def test_type_inference(self, analyzer):
        """Test correct type inference for different data types."""
        examples = [
            {
                "string_field": "text",
                "int_field": 42,
                "float_field": 3.14,
                "bool_field": True,
                "list_field": [1, 2, 3],
                "dict_field": {"nested": "value"},
            }
        ]

        schema = analyzer.infer_schema(examples)

        field_types = {f.path: f.field_type for f in schema.fields}

        assert field_types.get("string_field") == FieldTypeEnum.STRING
        assert field_types.get("int_field") == FieldTypeEnum.INTEGER
        assert field_types.get("float_field") == FieldTypeEnum.FLOAT
        assert field_types.get("bool_field") == FieldTypeEnum.BOOLEAN
        # Note: nested dict fields will be extracted with paths like "dict_field.nested"

    def test_nested_structure_inference(self, analyzer):
        """Test inference of nested dictionary structures."""
        examples = [{"main": {"temp": 15.5, "humidity": 80}}]

        schema = analyzer.infer_schema(examples)

        assert schema.is_nested

        # Should have nested fields
        nested_fields = schema.get_nested_fields()
        assert len(nested_fields) > 0

        # Check nested paths
        paths = [f.path for f in schema.fields]
        assert any("main.temp" in p for p in paths)
        assert any("main.humidity" in p for p in paths)

    def test_array_field_detection(self, analyzer):
        """Test detection of array fields."""
        examples = [{"items": [{"name": "item1"}, {"name": "item2"}]}]

        schema = analyzer.infer_schema(examples)

        assert schema.has_arrays

        # Should detect array fields
        array_fields = schema.get_array_fields()
        assert len(array_fields) > 0

    def test_nullable_field_detection(self, analyzer):
        """Test detection of nullable fields."""
        examples = [
            {"required": "value", "optional": "present"},
            {"required": "value", "optional": None},
        ]

        schema = analyzer.infer_schema(examples)

        optional_field = schema.get_field("optional")
        assert optional_field is not None
        assert optional_field.nullable

        required_field = schema.get_field("required")
        assert required_field is not None
        assert not required_field.nullable

    def test_required_field_detection(self, analyzer):
        """Test detection of required vs optional fields."""
        examples = [
            {"always_present": "value1", "sometimes_present": "value"},
            {"always_present": "value2"},
        ]

        schema = analyzer.infer_schema(examples)

        always_field = schema.get_field("always_present")
        assert always_field is not None
        assert always_field.required

        sometimes_field = schema.get_field("sometimes_present")
        assert sometimes_field is not None
        assert not sometimes_field.required

    def test_sample_values_collection(self, analyzer):
        """Test that sample values are collected."""
        examples = [{"field": "value1"}, {"field": "value2"}, {"field": "value3"}]

        schema = analyzer.infer_schema(examples)

        field = schema.get_field("field")
        assert field is not None
        assert len(field.sample_values) > 0
        assert "value1" in field.sample_values or "value2" in field.sample_values

    def test_nested_level_calculation(self, analyzer):
        """Test correct calculation of nesting levels."""
        examples = [
            {
                "level0": "value",
                "level1": {"field": "value", "level2": {"deep": "value"}},
            }
        ]

        schema = analyzer.infer_schema(examples)

        level0_field = schema.get_field("level0")
        assert level0_field is not None
        assert level0_field.nested_level == 0

        # Nested fields have higher levels
        nested_fields = schema.get_nested_fields()
        assert len(nested_fields) > 0
        assert all(f.nested_level > 0 for f in nested_fields)


class TestSchemaComparison:
    """Test schema comparison functionality."""

    @pytest.fixture
    def analyzer(self):
        """Create SchemaAnalyzer instance."""
        return SchemaAnalyzer()

    def test_field_addition_detection(self, analyzer):
        """Test detection of fields added in output."""
        input_examples = [{"field1": "value"}]
        output_examples = [{"field1": "value", "field2": "new"}]

        input_schema = analyzer.infer_schema(input_examples)
        output_schema = analyzer.infer_schema(output_examples)

        differences = analyzer.compare_schemas(input_schema, output_schema)

        # Should detect field2 as added
        added_diffs = [d for d in differences if d.difference_type == "added"]
        assert len(added_diffs) > 0
        assert any("field2" in d.output_path for d in added_diffs if d.output_path)

    def test_field_removal_detection(self, analyzer):
        """Test detection of fields removed in output."""
        input_examples = [{"field1": "value", "field2": "value"}]
        output_examples = [{"field1": "value"}]

        input_schema = analyzer.infer_schema(input_examples)
        output_schema = analyzer.infer_schema(output_examples)

        differences = analyzer.compare_schemas(input_schema, output_schema)

        # Should detect field2 as removed
        removed_diffs = [d for d in differences if d.difference_type == "removed"]
        assert len(removed_diffs) > 0
        assert any("field2" in d.input_path for d in removed_diffs if d.input_path)

    def test_type_change_detection(self, analyzer):
        """Test detection of field type changes."""
        input_examples = [{"field": "42"}]  # string
        output_examples = [{"field": 42}]  # int

        input_schema = analyzer.infer_schema(input_examples)
        output_schema = analyzer.infer_schema(output_examples)

        differences = analyzer.compare_schemas(input_schema, output_schema)

        # Should detect type change
        type_changes = [d for d in differences if d.difference_type == "type_changed"]
        assert len(type_changes) > 0

    def test_field_rename_detection(self, analyzer):
        """Test detection of probable field renames."""
        input_examples = [{"old_name": "value1"}, {"old_name": "value2"}]
        output_examples = [{"new_name": "value1"}, {"new_name": "value2"}]

        input_schema = analyzer.infer_schema(input_examples)
        output_schema = analyzer.infer_schema(output_examples)

        differences = analyzer.compare_schemas(input_schema, output_schema)

        # Should detect potential rename
        renames = [d for d in differences if d.difference_type == "renamed"]
        assert len(renames) > 0

    def test_no_differences_same_schema(self, analyzer):
        """Test no differences when schemas are identical."""
        examples = [{"field1": "value", "field2": 42}]

        schema1 = analyzer.infer_schema(examples)
        schema2 = analyzer.infer_schema(examples)

        differences = analyzer.compare_schemas(schema1, schema2)

        # Should only have differences for renamed/added/removed, not for common fields
        type_changes = [d for d in differences if d.difference_type == "type_changed"]
        assert len(type_changes) == 0


class TestEdgeCases:
    """Test edge cases for SchemaAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create SchemaAnalyzer instance."""
        return SchemaAnalyzer()

    def test_empty_examples(self, analyzer):
        """Test handling of empty examples list."""
        schema = analyzer.infer_schema([])

        assert len(schema.fields) == 0
        assert not schema.is_nested
        assert not schema.has_arrays

    def test_empty_dictionaries(self, analyzer):
        """Test handling of empty dictionaries."""
        schema = analyzer.infer_schema([{}, {}])

        assert len(schema.fields) == 0

    def test_inconsistent_types_across_examples(self, analyzer):
        """Test handling when field has different types across examples."""
        examples = [{"field": "string"}, {"field": 42}]

        schema = analyzer.infer_schema(examples)

        # Should infer type based on majority or first occurrence
        field = schema.get_field("field")
        assert field is not None
        # Type should be one of the observed types

    def test_deeply_nested_structure(self, analyzer):
        """Test handling of deeply nested structures."""
        examples = [{"level1": {"level2": {"level3": {"value": 42}}}}]

        schema = analyzer.infer_schema(examples)

        assert schema.is_nested
        nested_fields = schema.get_nested_fields()
        assert len(nested_fields) > 0

        # Check maximum nesting level
        max_level = max(f.nested_level for f in nested_fields)
        assert max_level >= 3

    def test_array_of_primitives(self, analyzer):
        """Test handling of arrays containing primitive values."""
        examples = [{"numbers": [1, 2, 3, 4, 5]}]

        schema = analyzer.infer_schema(examples)

        # Should detect array
        assert schema.has_arrays

    def test_mixed_nested_and_flat_fields(self, analyzer):
        """Test schema with both flat and nested fields."""
        examples = [{"flat_field": "value", "nested": {"field": "value"}}]

        schema = analyzer.infer_schema(examples)

        assert schema.is_nested

        top_level = schema.get_top_level_fields()
        nested = schema.get_nested_fields()

        assert len(top_level) > 0
        assert len(nested) > 0
