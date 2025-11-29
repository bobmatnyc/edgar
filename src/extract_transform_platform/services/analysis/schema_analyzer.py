"""
Schema analysis service for Example Parser.

This service infers data schemas from example input/output pairs and identifies
structural differences that indicate transformation patterns.

Design Decisions:
- **Type Inference**: Analyze actual values to determine types (not declarations)
- **Null Handling**: Track nullability separately from type
- **Nested Structure Support**: Handle arbitrarily nested dicts and lists
- **Path-Based Addressing**: Use dot notation for nested fields (e.g., "main.temp")

Performance:
- Time Complexity: O(n * m) where n=examples, m=fields per example
- Space Complexity: O(f) where f=total unique fields across examples
- Typical Performance: <100ms for 10 examples with 50 fields each

Usage:
    >>> analyzer = SchemaAnalyzer()
    >>> input_schema = analyzer.infer_input_schema(examples)
    >>> output_schema = analyzer.infer_output_schema(examples)
    >>> differences = analyzer.compare_schemas(input_schema, output_schema)

Migration Note:
    Migrated from edgar_analyzer.services.schema_analyzer (T3 - Extract Schema Analyzer)
    No EDGAR-specific code - generic schema analysis for all data sources.
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

from extract_transform_platform.models.patterns import (
    FieldTypeEnum,
    Schema,
    SchemaField,
    SchemaDifference,
)

logger = logging.getLogger(__name__)


class SchemaAnalyzer:
    """Analyze and infer schemas from example data.

    Provides schema inference, type detection, and schema comparison
    functionality for the Example Parser system.

    Example:
        >>> analyzer = SchemaAnalyzer()
        >>> examples = [
        ...     {"name": "London", "temp": 15.5},
        ...     {"name": "Tokyo", "temp": 22.3}
        ... ]
        >>> schema = analyzer.infer_schema(examples, is_input=True)
        >>> print(schema.fields)
    """

    def __init__(self) -> None:
        """Initialize SchemaAnalyzer."""
        self.logger = logger

    def infer_input_schema(self, examples: List[Dict[str, Any]]) -> Schema:
        """Infer input data schema from examples.

        Args:
            examples: List of example input dictionaries

        Returns:
            Inferred Schema object for inputs

        Example:
            >>> examples = [
            ...     {"main": {"temp": 15.5}, "name": "London"},
            ...     {"main": {"temp": 22.3}, "name": "Tokyo"}
            ... ]
            >>> schema = analyzer.infer_input_schema(examples)
        """
        return self.infer_schema(examples, is_input=True)

    def infer_output_schema(self, examples: List[Dict[str, Any]]) -> Schema:
        """Infer output data schema from examples.

        Args:
            examples: List of example output dictionaries

        Returns:
            Inferred Schema object for outputs

        Example:
            >>> examples = [
            ...     {"city": "London", "temperature_c": 15.5},
            ...     {"city": "Tokyo", "temperature_c": 22.3}
            ... ]
            >>> schema = analyzer.infer_output_schema(examples)
        """
        return self.infer_schema(examples, is_input=False)

    def infer_schema(
        self, examples: List[Dict[str, Any]], is_input: bool = True
    ) -> Schema:
        """Infer schema from a list of example dictionaries.

        Args:
            examples: List of example dictionaries
            is_input: Whether analyzing input schema (affects logging)

        Returns:
            Inferred Schema object

        Error Handling:
        - Empty examples: Returns empty schema with warning
        - Null values: Tracked in nullable field
        - Type conflicts: Uses most common type across examples
        """
        if not examples:
            self.logger.warning("No examples provided for schema inference")
            return Schema(fields=[])

        # Extract all fields from all examples
        all_fields: Dict[str, List[Any]] = {}
        for example in examples:
            self._extract_fields(example, "", all_fields)

        # Build schema fields
        fields: List[SchemaField] = []
        for path, values in all_fields.items():
            field = self._analyze_field(path, values, len(examples))
            fields.append(field)

        # Determine schema characteristics
        is_nested = any(f.nested_level > 0 for f in fields)
        has_arrays = any(f.is_array for f in fields)

        schema_type = "input" if is_input else "output"
        self.logger.debug(
            f"Inferred {schema_type} schema: {len(fields)} fields, "
            f"nested={is_nested}, arrays={has_arrays}"
        )

        return Schema(fields=fields, is_nested=is_nested, has_arrays=has_arrays)

    def compare_schemas(
        self, input_schema: Schema, output_schema: Schema
    ) -> List[SchemaDifference]:
        """Compare input and output schemas to identify differences.

        Identifies transformation patterns by comparing schema structures:
        - Fields added in output (new constants or calculated fields)
        - Fields removed from input (dropped fields)
        - Fields renamed (same data, different name)
        - Type changes (type conversions)
        - Nesting changes (extraction or wrapping)

        Args:
            input_schema: Input data schema
            output_schema: Output data schema

        Returns:
            List of schema differences

        Example:
            >>> differences = analyzer.compare_schemas(input_schema, output_schema)
            >>> for diff in differences:
            ...     print(f"{diff.difference_type}: {diff.description}")
        """
        differences: List[SchemaDifference] = []

        # Build path → field mappings
        input_fields = {f.path: f for f in input_schema.fields}
        output_fields = {f.path: f for f in output_schema.fields}

        input_paths = set(input_fields.keys())
        output_paths = set(output_fields.keys())

        # Find fields only in output (added/calculated)
        added_paths = output_paths - input_paths
        for path in added_paths:
            output_field = output_fields[path]
            differences.append(
                SchemaDifference(
                    input_path=None,
                    output_path=path,
                    difference_type="added",
                    description=f"Field '{path}' added in output (may be calculated or constant)",
                    output_type=output_field.field_type,
                )
            )

        # Find fields only in input (removed/dropped)
        removed_paths = input_paths - output_paths
        for path in removed_paths:
            input_field = input_fields[path]
            differences.append(
                SchemaDifference(
                    input_path=path,
                    output_path=None,
                    difference_type="removed",
                    description=f"Field '{path}' removed in output (dropped)",
                    input_type=input_field.field_type,
                )
            )

        # Find fields in both (check for type changes)
        common_paths = input_paths & output_paths
        for path in common_paths:
            input_field = input_fields[path]
            output_field = output_fields[path]

            if input_field.field_type != output_field.field_type:
                differences.append(
                    SchemaDifference(
                        input_path=path,
                        output_path=path,
                        difference_type="type_changed",
                        description=f"Field '{path}' type changed: {input_field.field_type} → {output_field.field_type}",
                        input_type=input_field.field_type,
                        output_type=output_field.field_type,
                    )
                )

        # Detect potential field renames (same type, similar values, different path)
        differences.extend(self._detect_field_renames(input_schema, output_schema))

        self.logger.debug(f"Found {len(differences)} schema differences")

        return differences

    def _extract_fields(
        self,
        data: Any,
        prefix: str,
        all_fields: Dict[str, List[Any]],
        nested_level: int = 0,
    ) -> None:
        """Recursively extract all fields from nested data structure.

        Args:
            data: Data to extract fields from
            prefix: Current path prefix (e.g., "main.temp")
            all_fields: Accumulator for field values
            nested_level: Current nesting depth
        """
        if isinstance(data, dict):
            for key, value in data.items():
                path = f"{prefix}.{key}" if prefix else key
                self._extract_fields(value, path, all_fields, nested_level)
        elif isinstance(data, list) and data:
            # Handle arrays - extract from first element for now
            # Future enhancement: analyze all array elements
            array_path = f"{prefix}[0]" if prefix else "[0]"
            if data:
                self._extract_fields(data[0], array_path, all_fields, nested_level)
        else:
            # Leaf value
            if prefix not in all_fields:
                all_fields[prefix] = []
            all_fields[prefix].append(data)

    def _analyze_field(
        self, path: str, values: List[Any], total_examples: int
    ) -> SchemaField:
        """Analyze a single field across all examples.

        Args:
            path: Field path (e.g., "main.temp")
            values: All observed values for this field
            total_examples: Total number of examples

        Returns:
            SchemaField with inferred metadata
        """
        # Determine type
        field_type = self._infer_type(values)

        # Check if required (present in all examples)
        required = len(values) == total_examples

        # Check if nullable (contains None)
        nullable = None in values

        # Calculate nested level
        nested_level = path.count(".")
        if "[" in path:
            nested_level += path.count("[")

        # Check if array
        is_array = "[" in path
        array_item_type = None
        if is_array:
            # Infer array item type from non-None values
            non_none_values = [v for v in values if v is not None]
            if non_none_values:
                array_item_type = self._infer_type(non_none_values)

        # Sample values (up to 3)
        sample_values = list(set(values))[:3]

        return SchemaField(
            path=path,
            field_type=field_type,
            required=required,
            nullable=nullable,
            nested_level=nested_level,
            is_array=is_array,
            array_item_type=array_item_type,
            sample_values=sample_values,
        )

    def _infer_type(self, values: List[Any]) -> FieldTypeEnum:
        """Infer field type from observed values.

        Uses majority voting when types conflict across examples.

        Args:
            values: List of observed values

        Returns:
            Inferred FieldTypeEnum
        """
        if not values:
            return FieldTypeEnum.UNKNOWN

        # Count type occurrences
        type_counts: Dict[FieldTypeEnum, int] = {}
        for value in values:
            value_type = self._get_value_type(value)
            type_counts[value_type] = type_counts.get(value_type, 0) + 1

        # Remove null from consideration if other types exist
        if len(type_counts) > 1 and FieldTypeEnum.NULL in type_counts:
            del type_counts[FieldTypeEnum.NULL]

        # Return most common type
        if type_counts:
            return max(type_counts, key=type_counts.get)  # type: ignore

        return FieldTypeEnum.UNKNOWN

    def _get_value_type(self, value: Any) -> FieldTypeEnum:
        """Get FieldTypeEnum for a single value.

        Args:
            value: Value to type-check

        Returns:
            Corresponding FieldTypeEnum
        """
        if value is None:
            return FieldTypeEnum.NULL
        elif isinstance(value, bool):
            return FieldTypeEnum.BOOLEAN
        elif isinstance(value, int):
            return FieldTypeEnum.INTEGER
        elif isinstance(value, float):
            return FieldTypeEnum.FLOAT
        elif isinstance(value, Decimal):
            return FieldTypeEnum.DECIMAL
        elif isinstance(value, datetime):
            return FieldTypeEnum.DATETIME
        elif isinstance(value, date):
            return FieldTypeEnum.DATE
        elif isinstance(value, str):
            return FieldTypeEnum.STRING
        elif isinstance(value, list):
            return FieldTypeEnum.LIST
        elif isinstance(value, dict):
            return FieldTypeEnum.DICT
        else:
            return FieldTypeEnum.UNKNOWN

    def _detect_field_renames(
        self, input_schema: Schema, output_schema: Schema
    ) -> List[SchemaDifference]:
        """Detect potential field renames between schemas.

        Uses heuristics:
        - Same type
        - Similar sample values
        - One input field removed, one output field added

        Args:
            input_schema: Input schema
            output_schema: Output schema

        Returns:
            List of potential rename differences
        """
        renames: List[SchemaDifference] = []

        # Get fields that appear only in one schema
        input_only = {
            f.path: f
            for f in input_schema.fields
            if not output_schema.get_field(f.path)
        }
        output_only = {
            f.path: f
            for f in output_schema.fields
            if not input_schema.get_field(f.path)
        }

        # Try to match by type and sample values
        for input_path, input_field in input_only.items():
            for output_path, output_field in output_only.items():
                # Must have same type
                if input_field.field_type != output_field.field_type:
                    continue

                # Check sample value overlap
                input_samples = set(str(v) for v in input_field.sample_values)
                output_samples = set(str(v) for v in output_field.sample_values)

                if not input_samples or not output_samples:
                    continue

                # Calculate Jaccard similarity
                intersection = len(input_samples & output_samples)
                union = len(input_samples | output_samples)
                similarity = intersection / union if union > 0 else 0

                # High similarity suggests rename
                if similarity >= 0.5:
                    renames.append(
                        SchemaDifference(
                            input_path=input_path,
                            output_path=output_path,
                            difference_type="renamed",
                            description=f"Field '{input_path}' likely renamed to '{output_path}' (similarity: {similarity:.0%})",
                            input_type=input_field.field_type,
                            output_type=output_field.field_type,
                        )
                    )

        return renames
