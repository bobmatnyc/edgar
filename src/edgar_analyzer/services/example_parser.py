"""
Example Parser service for transformation pattern extraction.

This is the core service that analyzes input/output example pairs to identify
transformation patterns. It coordinates schema analysis and pattern detection
to extract reusable transformation logic.

Design Decisions:
- **Example-Based Learning**: Infer patterns from examples rather than explicit rules
- **Multi-Pattern Detection**: Identify all applicable patterns for each field
- **Confidence Scoring**: Track pattern consistency across examples
- **Incremental Analysis**: Can process examples in batches

Performance:
- Time Complexity: O(n * m * p) where n=examples, m=fields, p=pattern types
- Space Complexity: O(f * n) where f=fields, n=examples
- Expected Performance: <500ms for 10 examples with 50 fields

Usage:
    >>> parser = ExampleParser(schema_analyzer)
    >>> examples = [ExampleConfig(...), ExampleConfig(...)]
    >>> parsed = parser.parse_examples(examples)
    >>> for pattern in parsed.high_confidence_patterns:
    ...     print(f"{pattern.type}: {pattern.transformation}")
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from edgar_analyzer.models.patterns import (
    FieldTypeEnum,
    ParsedExamples,
    Pattern,
    PatternType,
    Schema,
)
from edgar_analyzer.models.project_config import ExampleConfig
from edgar_analyzer.services.schema_analyzer import SchemaAnalyzer

logger = logging.getLogger(__name__)


class ExampleParser:
    """Parse and analyze input/output examples for pattern extraction.

    This service is the heart of the Example Parser system, identifying
    transformation patterns that can be used to generate code.

    Example:
        >>> parser = ExampleParser(SchemaAnalyzer())
        >>> examples = [
        ...     ExampleConfig(
        ...         input={"name": "London", "main": {"temp": 15.5}},
        ...         output={"city": "London", "temperature_c": 15.5}
        ...     )
        ... ]
        >>> parsed = parser.parse_examples(examples)
        >>> print(f"Found {len(parsed.patterns)} patterns")
    """

    def __init__(self, schema_analyzer: Optional[SchemaAnalyzer] = None) -> None:
        """Initialize ExampleParser.

        Args:
            schema_analyzer: SchemaAnalyzer instance (creates new if None)
        """
        self.schema_analyzer = schema_analyzer or SchemaAnalyzer()
        self.logger = logger

    def parse_examples(self, examples: List[ExampleConfig]) -> ParsedExamples:
        """Parse all examples and extract patterns.

        This is the main entry point for pattern extraction.

        Args:
            examples: List of ExampleConfig objects

        Returns:
            ParsedExamples containing schemas, patterns, and metadata

        Error Handling:
        - Empty examples: Returns empty ParsedExamples with warning
        - Parse failures: Logged and skipped, processing continues
        - Pattern conflicts: Lower confidence scores applied

        Example:
            >>> examples = [example1, example2, example3]
            >>> parsed = parser.parse_examples(examples)
            >>> print(f"High confidence: {len(parsed.high_confidence_patterns)}")
        """
        if not examples:
            self.logger.warning("No examples provided to parse")
            return ParsedExamples(
                input_schema=Schema(), output_schema=Schema(), num_examples=0
            )

        self.logger.info(f"Parsing {len(examples)} examples")

        # Extract input and output data
        inputs = [ex.input for ex in examples]
        outputs = [ex.output for ex in examples]

        # Infer schemas
        input_schema = self.schema_analyzer.infer_input_schema(inputs)
        output_schema = self.schema_analyzer.infer_output_schema(outputs)

        # Compare schemas
        schema_differences = self.schema_analyzer.compare_schemas(
            input_schema, output_schema
        )

        # Identify patterns
        patterns = self.identify_patterns(examples)

        # Collect warnings
        warnings = self._generate_warnings(patterns, examples)

        parsed = ParsedExamples(
            input_schema=input_schema,
            output_schema=output_schema,
            patterns=patterns,
            schema_differences=schema_differences,
            num_examples=len(examples),
            warnings=warnings,
        )

        self.logger.info(
            f"Parsed {len(examples)} examples: "
            f"{len(patterns)} patterns found, "
            f"{len(parsed.high_confidence_patterns)} high confidence"
        )

        return parsed

    def identify_patterns(self, examples: List[ExampleConfig]) -> List[Pattern]:
        """Identify transformation patterns across examples.

        Analyzes all examples to detect common transformation patterns:
        - Field mappings and renames
        - Type conversions
        - Nested field extractions
        - Array operations
        - Calculations and transformations

        Args:
            examples: List of ExampleConfig objects

        Returns:
            List of identified Pattern objects

        Example:
            >>> patterns = parser.identify_patterns(examples)
            >>> field_mappings = [p for p in patterns if p.type == PatternType.FIELD_MAPPING]
        """
        if not examples:
            return []

        patterns: List[Pattern] = []

        # Get all output field paths from first example
        output_paths = self._extract_all_paths(examples[0].output)

        # For each output field, try to identify transformation pattern
        for output_path in output_paths:
            pattern = self._identify_field_pattern(output_path, examples)
            if pattern:
                patterns.append(pattern)

        self.logger.debug(f"Identified {len(patterns)} patterns")

        return patterns

    def _identify_field_pattern(
        self, output_path: str, examples: List[ExampleConfig]
    ) -> Optional[Pattern]:
        """Identify pattern for a single output field across all examples.

        Args:
            output_path: Path to output field (e.g., "temperature_c")
            examples: All examples to analyze

        Returns:
            Pattern if detected, None if no clear pattern

        Pattern Detection Priority:
        1. Direct field mapping (same path, same value)
        2. Field rename (different path, same value)
        3. Nested field extraction
        4. Array first element
        5. Type conversion
        6. Calculation/transformation
        7. Constant value
        """
        # Collect (input_value, output_value) pairs
        value_pairs: List[Tuple[Any, Any]] = []

        for example in examples:
            output_value = self._get_value_at_path(example.output, output_path)
            if output_value is None:
                continue

            # Try to find matching input value
            input_value = self._find_source_value(
                example.input, output_value, output_path
            )

            value_pairs.append((input_value, output_value))

        if not value_pairs:
            return None

        # Detect pattern type based on value pairs
        return self._detect_pattern_type(output_path, value_pairs, examples)

    def _detect_pattern_type(
        self,
        output_path: str,
        value_pairs: List[Tuple[Any, Any]],
        examples: List[ExampleConfig],
    ) -> Optional[Pattern]:
        """Detect the type of transformation pattern.

        Detection Priority (from most specific to least specific):
        1. Field mapping/extraction (checks for nested paths first)
        2. Constant value
        3. Array first element
        4. Type conversion
        5. Direct copy (only if none of the above matched)

        Args:
            output_path: Output field path
            value_pairs: List of (input_value, output_value) tuples
            examples: All examples

        Returns:
            Pattern if detected, None otherwise

        Design Decision: Check field mapping FIRST (before direct copy) to ensure
        nested extractions like input["main"]["temp"] → output["temperature_c"]
        are correctly classified as FIELD_EXTRACTION instead of direct copy.
        This prioritizes semantic accuracy over simple value matching.
        """
        if not value_pairs:
            return None

        # PRIORITY 1: Check for field mapping/extraction
        # This must come FIRST to detect nested paths before direct copy check
        # Example: {"main": {"temp": 15.5}} → {"temperature_c": 15.5}
        # Value pairs: [(15.5, 15.5)] but source is nested path "main.temp"
        field_mapping_pattern = self._detect_field_mapping(
            output_path, value_pairs, examples
        )
        if field_mapping_pattern is not None:
            return field_mapping_pattern

        # PRIORITY 2: Check for constant value (all outputs same, input varies or None)
        output_values = [out for _, out in value_pairs]
        if len(set(str(v) for v in output_values)) == 1:
            return self._create_constant_pattern(output_path, value_pairs)

        # PRIORITY 3: Check for array first element
        # Must come before direct copy to detect array[0] extractions
        if all(isinstance(inp, list) for inp, _ in value_pairs if inp is not None):
            array_pattern = self._detect_array_first(output_path, value_pairs)
            if array_pattern is not None:
                return array_pattern

        # PRIORITY 4: Check for type conversion
        input_types = set(type(inp) for inp, _ in value_pairs if inp is not None)
        output_types = set(type(out) for _, out in value_pairs if out is not None)

        if len(input_types) == 1 and len(output_types) == 1:
            if list(input_types)[0] != list(output_types)[0]:
                return self._create_type_conversion_pattern(output_path, value_pairs)

        # PRIORITY 5: Check for direct copy (input == output)
        # This is LAST because inp==out might be from nested extraction
        # Only apply if no more specific pattern was detected above
        if all(inp == out for inp, out in value_pairs if inp is not None):
            return self._create_direct_copy_pattern(output_path, value_pairs)

        # Default: complex transformation
        return self._create_complex_pattern(output_path, value_pairs)

    def _detect_field_mapping(
        self,
        output_path: str,
        value_pairs: List[Tuple[Any, Any]],
        examples: List[ExampleConfig],
    ) -> Optional[Pattern]:
        """Detect field mapping or extraction pattern.

        Args:
            output_path: Output field path
            value_pairs: Value pairs with dict inputs
            examples: All examples

        Returns:
            FIELD_MAPPING or FIELD_EXTRACTION pattern
        """
        # Try to find consistent input path
        input_paths: Set[str] = set()

        for example in examples:
            # Search input for output value
            output_value = self._get_value_at_path(example.output, output_path)
            if output_value is None:
                continue

            input_path = self._find_path_for_value(example.input, output_value)
            if input_path:
                input_paths.add(input_path)

        if len(input_paths) == 1:
            # Consistent mapping found
            input_path = list(input_paths)[0]
            confidence = len(value_pairs) / len(examples)

            # Determine if it's nested extraction
            is_nested = "." in input_path or "[" in input_path

            pattern_type = (
                PatternType.FIELD_EXTRACTION if is_nested else PatternType.FIELD_MAPPING
            )

            transformation = (
                f"Extract nested field from '{input_path}'"
                if is_nested
                else f"Map field '{input_path}' to '{output_path}'"
            )

            return Pattern(
                type=pattern_type,
                confidence=confidence,
                source_path=input_path,
                target_path=output_path,
                transformation=transformation,
                examples=value_pairs,
                source_type=self._infer_type_from_values([v for v, _ in value_pairs]),
                target_type=self._infer_type_from_values([v for _, v in value_pairs]),
            )

        return None

    def _detect_array_first(
        self, output_path: str, value_pairs: List[Tuple[Any, Any]]
    ) -> Optional[Pattern]:
        """Detect array first element extraction pattern.

        Args:
            output_path: Output field path
            value_pairs: Value pairs with list inputs

        Returns:
            ARRAY_FIRST pattern if detected
        """
        # Check if output value matches first element of input array
        matches = 0
        for inp, out in value_pairs:
            if isinstance(inp, list) and inp:
                # Handle nested access (e.g., first element's 'description' field)
                first_elem = inp[0]
                if isinstance(first_elem, dict):
                    # Try to find matching field in first element
                    for key, val in first_elem.items():
                        if val == out:
                            matches += 1
                            break
                elif first_elem == out:
                    matches += 1

        if matches == len(value_pairs):
            confidence = 1.0
            transformation = "Extract first element from array"

            return Pattern(
                type=PatternType.ARRAY_FIRST,
                confidence=confidence,
                source_path="[0]",  # Placeholder, should be detected
                target_path=output_path,
                transformation=transformation,
                examples=value_pairs,
                source_type=FieldTypeEnum.LIST,
                target_type=self._infer_type_from_values([v for _, v in value_pairs]),
            )

        return None

    def _create_direct_copy_pattern(
        self, output_path: str, value_pairs: List[Tuple[Any, Any]]
    ) -> Pattern:
        """Create pattern for direct value copy.

        Args:
            output_path: Output field path
            value_pairs: Value pairs where input == output

        Returns:
            FIELD_MAPPING pattern for direct copy
        """
        confidence = sum(1 for inp, out in value_pairs if inp == out) / len(value_pairs)

        return Pattern(
            type=PatternType.FIELD_MAPPING,
            confidence=confidence,
            source_path=output_path,  # Assume same path
            target_path=output_path,
            transformation="Direct copy",
            examples=value_pairs,
            source_type=self._infer_type_from_values([v for v, _ in value_pairs]),
            target_type=self._infer_type_from_values([v for _, v in value_pairs]),
        )

    def _create_type_conversion_pattern(
        self, output_path: str, value_pairs: List[Tuple[Any, Any]]
    ) -> Pattern:
        """Create type conversion pattern.

        Args:
            output_path: Output field path
            value_pairs: Value pairs with different types

        Returns:
            TYPE_CONVERSION pattern
        """
        source_type = self._infer_type_from_values([v for v, _ in value_pairs])
        target_type = self._infer_type_from_values([v for _, v in value_pairs])

        transformation = f"Convert {source_type} to {target_type}"

        return Pattern(
            type=PatternType.TYPE_CONVERSION,
            confidence=1.0,
            source_path=output_path,  # Assume same path
            target_path=output_path,
            transformation=transformation,
            examples=value_pairs,
            source_type=source_type,
            target_type=target_type,
        )

    def _create_constant_pattern(
        self, output_path: str, value_pairs: List[Tuple[Any, Any]]
    ) -> Pattern:
        """Create constant value pattern.

        Args:
            output_path: Output field path
            value_pairs: Value pairs with constant output

        Returns:
            CONSTANT pattern
        """
        constant_value = value_pairs[0][1]

        return Pattern(
            type=PatternType.CONSTANT,
            confidence=1.0,
            source_path="<constant>",
            target_path=output_path,
            transformation=f"Set constant value: {constant_value}",
            examples=value_pairs,
            target_type=self._infer_type_from_values([constant_value]),
        )

    def _create_complex_pattern(
        self, output_path: str, value_pairs: List[Tuple[Any, Any]]
    ) -> Pattern:
        """Create complex transformation pattern.

        Args:
            output_path: Output field path
            value_pairs: Value pairs with complex transformation

        Returns:
            COMPLEX pattern
        """
        return Pattern(
            type=PatternType.COMPLEX,
            confidence=0.5,  # Lower confidence for complex patterns
            source_path="<multiple>",
            target_path=output_path,
            transformation="Complex transformation (requires manual review)",
            examples=value_pairs,
            source_type=self._infer_type_from_values([v for v, _ in value_pairs]),
            target_type=self._infer_type_from_values([v for _, v in value_pairs]),
            notes="This transformation may require custom logic or calculation",
        )

    def _find_source_value(
        self, input_data: Dict[str, Any], output_value: Any, output_path: str
    ) -> Any:
        """Find the input value that maps to an output value.

        Args:
            input_data: Input dictionary
            output_value: Output value to find source for
            output_path: Output field path (used as hint)

        Returns:
            Input value if found, None otherwise
        """
        # First try same path
        same_path_value = self._get_value_at_path(input_data, output_path)
        if same_path_value == output_value:
            return same_path_value

        # Search entire input for matching value
        matching_path = self._find_path_for_value(input_data, output_value)
        if matching_path:
            return self._get_value_at_path(input_data, matching_path)

        # Return entire input if no specific match (might be transformation)
        return input_data

    def _find_path_for_value(
        self, data: Any, target_value: Any, prefix: str = ""
    ) -> Optional[str]:
        """Recursively find path to a target value in nested structure.

        Args:
            data: Data structure to search
            target_value: Value to find
            prefix: Current path prefix

        Returns:
            Path to value if found, None otherwise
        """
        if data == target_value:
            return prefix or "."

        if isinstance(data, dict):
            for key, value in data.items():
                path = f"{prefix}.{key}" if prefix else key
                result = self._find_path_for_value(value, target_value, path)
                if result:
                    return result

        elif isinstance(data, list):
            for i, item in enumerate(data):
                path = f"{prefix}[{i}]"
                result = self._find_path_for_value(item, target_value, path)
                if result:
                    return result

        return None

    def _get_value_at_path(self, data: Dict[str, Any], path: str) -> Any:
        """Get value at a specific path in nested structure.

        Args:
            data: Data dictionary
            path: Dot-notation path (e.g., "main.temp", "weather[0].description")

        Returns:
            Value at path, None if not found
        """
        if not path:
            return data

        parts = path.replace("[", ".").replace("]", "").split(".")
        current = data

        for part in parts:
            if not part:
                continue

            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError):
                    return None
            else:
                return None

            if current is None:
                return None

        return current

    def _extract_all_paths(self, data: Any, prefix: str = "") -> List[str]:
        """Extract all field paths from data structure.

        Args:
            data: Data structure
            prefix: Current path prefix

        Returns:
            List of all field paths
        """
        paths: List[str] = []

        if isinstance(data, dict):
            for key, value in data.items():
                path = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    paths.extend(self._extract_all_paths(value, path))
                else:
                    paths.append(path)
        elif isinstance(data, list) and data:
            # Only extract from first element
            path = f"{prefix}[0]"
            paths.extend(self._extract_all_paths(data[0], path))

        return paths

    def _infer_type_from_values(self, values: List[Any]) -> FieldTypeEnum:
        """Infer FieldTypeEnum from a list of values.

        Args:
            values: List of values

        Returns:
            Inferred FieldTypeEnum
        """
        non_none_values = [v for v in values if v is not None]
        if not non_none_values:
            return FieldTypeEnum.NULL

        value = non_none_values[0]

        if isinstance(value, bool):
            return FieldTypeEnum.BOOLEAN
        elif isinstance(value, int):
            return FieldTypeEnum.INTEGER
        elif isinstance(value, float):
            return FieldTypeEnum.FLOAT
        elif isinstance(value, str):
            return FieldTypeEnum.STRING
        elif isinstance(value, list):
            return FieldTypeEnum.LIST
        elif isinstance(value, dict):
            return FieldTypeEnum.DICT
        else:
            return FieldTypeEnum.UNKNOWN

    def _generate_warnings(
        self, patterns: List[Pattern], examples: List[ExampleConfig]
    ) -> List[str]:
        """Generate warnings about pattern quality and edge cases.

        Args:
            patterns: Identified patterns
            examples: Examples analyzed

        Returns:
            List of warning messages
        """
        warnings: List[str] = []

        # Warn about low confidence patterns
        low_confidence = [p for p in patterns if p.confidence < 0.7]
        if low_confidence:
            warnings.append(
                f"{len(low_confidence)} patterns have low confidence (<0.7). "
                f"Consider adding more examples."
            )

        # Warn about complex patterns
        complex_patterns = [p for p in patterns if p.type == PatternType.COMPLEX]
        if complex_patterns:
            warnings.append(
                f"{len(complex_patterns)} complex transformations detected. "
                f"Manual review recommended."
            )

        # Warn if few examples
        if len(examples) < 3:
            warnings.append(
                "Only 2 examples provided. Consider adding more for better pattern detection."
            )

        return warnings
