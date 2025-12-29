"""
Pattern models for Example Parser system.

This module defines data models for transformation patterns identified by
analyzing input/output example pairs. These patterns are used to generate
prompts for Sonnet 4.5 code generation.

Design Decisions:
- **Pattern-Based Approach**: Extract reusable patterns from examples rather
  than hardcoded transformations
- **Confidence Scoring**: Track pattern reliability across multiple examples
- **Type Preservation**: Maintain type information for validation
- **Source Tracking**: Record which examples support each pattern

Usage:
    >>> pattern = Pattern(
    ...     type=PatternType.FIELD_MAPPING,
    ...     confidence=1.0,
    ...     source_path="name",
    ...     target_path="city",
    ...     transformation="Direct copy",
    ...     examples=[("London", "London"), ("Tokyo", "Tokyo")]
    ... )

Migration Note:
    Migrated from edgar_analyzer.models.patterns (T3 - Extract Schema Analyzer)
    No EDGAR-specific code - generic pattern detection for all data sources.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# ENUMERATIONS
# ============================================================================


class PatternType(str, Enum):
    """Types of transformation patterns that can be identified.

    Each pattern type represents a different class of data transformation
    commonly found in API response → structured output conversions.
    """

    FIELD_MAPPING = "field_mapping"
    """Direct field mapping: input.field → output.field"""

    FIELD_RENAME = "field_rename"
    """Field rename with same data: input.old_name → output.new_name"""

    TYPE_CONVERSION = "type_conversion"
    """Type transformation: string → int, string → datetime, etc."""

    FIELD_EXTRACTION = "field_extraction"
    """Extract nested field to flat structure: input.a.b.c → output.c"""

    CALCULATION = "calculation"
    """Mathematical calculation: (temp_f - 32) * 5/9 → temp_c"""

    ARRAY_FIRST = "array_first"
    """Extract first element from array: input.array[0] → output.field"""

    ARRAY_MAP = "array_map"
    """Map array elements: [a, b, c] → [transform(a), transform(b), ...]"""

    ARRAY_FILTER = "array_filter"
    """Filter array elements: [a, b, c] → [a, c] (where predicate)"""

    CONDITIONAL = "conditional"
    """Conditional logic: if input.x then output.y else output.z"""

    STRING_MANIPULATION = "string_manipulation"
    """String operations: split, join, regex, formatting"""

    CONSTANT = "constant"
    """Constant value: output.field = constant"""

    AGGREGATION = "aggregation"
    """Aggregate values: sum, avg, min, max, count"""

    DEFAULT_VALUE = "default_value"
    """Provide default when field missing: output.field = input.field || default"""

    COMPLEX = "complex"
    """Complex transformation requiring multiple steps"""


class FieldTypeEnum(str, Enum):
    """Field data types for schema inference."""

    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "bool"
    DATE = "date"
    DATETIME = "datetime"
    LIST = "list"
    DICT = "dict"
    NULL = "null"
    UNKNOWN = "unknown"


# ============================================================================
# PATTERN MODELS
# ============================================================================


class Pattern(BaseModel):
    """Represents an identified transformation pattern.

    A pattern describes how data transforms from input to output, along with
    confidence metrics based on consistency across examples.

    Confidence Scoring:
    - 1.0: Pattern applies to ALL examples (100% confidence)
    - 0.9-0.99: Pattern applies to most examples (high confidence)
    - 0.7-0.89: Pattern applies to majority (medium confidence)
    - <0.7: Pattern inconsistent (low confidence, may need review)

    Example:
        >>> pattern = Pattern(
        ...     type=PatternType.FIELD_MAPPING,
        ...     confidence=1.0,
        ...     source_path="main.temp",
        ...     target_path="temperature_c",
        ...     transformation="Extract nested field 'temp' from 'main' object",
        ...     examples=[({"temp": 15.5}, 15.5), ({"temp": 22.3}, 22.3)],
        ...     source_type=FieldTypeEnum.FLOAT,
        ...     target_type=FieldTypeEnum.FLOAT
        ... )
    """

    type: PatternType = Field(..., description="Type of transformation pattern")

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) based on example consistency",
    )

    source_path: str = Field(
        ...,
        description="Path to source field in input (e.g., 'main.temp', 'weather[0].description')",
    )

    target_path: str = Field(
        ..., description="Path to target field in output (e.g., 'temperature_c')"
    )

    transformation: str = Field(
        ..., description="Human-readable description of the transformation"
    )

    examples: List[Tuple[Any, Any]] = Field(
        default_factory=list,
        description="List of (input_value, output_value) pairs demonstrating this pattern",
    )

    source_type: Optional[FieldTypeEnum] = Field(
        None, description="Inferred data type of source field"
    )

    target_type: Optional[FieldTypeEnum] = Field(
        None, description="Inferred data type of target field"
    )

    code_snippet: Optional[str] = Field(
        None,
        description="Optional Python code snippet implementing this transformation",
    )

    notes: Optional[str] = Field(
        None, description="Additional notes or edge cases for this pattern"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float) -> float:
        """Ensure confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v

    @property
    def confidence_level(self) -> str:
        """Get human-readable confidence level."""
        if self.confidence >= 0.9:
            return "high"
        elif self.confidence >= 0.7:
            return "medium"
        else:
            return "low"

    @property
    def is_type_safe(self) -> bool:
        """Check if transformation preserves or safely converts types."""
        if not self.source_type or not self.target_type:
            return False

        # Same type is always safe
        if self.source_type == self.target_type:
            return True

        # Define safe conversions
        safe_conversions = {
            (FieldTypeEnum.INTEGER, FieldTypeEnum.FLOAT),
            (FieldTypeEnum.INTEGER, FieldTypeEnum.STRING),
            (FieldTypeEnum.FLOAT, FieldTypeEnum.STRING),
            (FieldTypeEnum.BOOLEAN, FieldTypeEnum.STRING),
            (FieldTypeEnum.DATE, FieldTypeEnum.STRING),
            (FieldTypeEnum.DATETIME, FieldTypeEnum.STRING),
        }

        return (self.source_type, self.target_type) in safe_conversions


class SchemaField(BaseModel):
    """Represents a field in input or output schema.

    Tracks field metadata including type, nesting, and nullability.

    Example:
        >>> field = SchemaField(
        ...     path="main.temp",
        ...     field_type=FieldTypeEnum.FLOAT,
        ...     required=True,
        ...     nullable=False,
        ...     nested_level=1
        ... )
    """

    path: str = Field(
        ..., description="Field path (e.g., 'main.temp', 'weather[0].description')"
    )

    field_type: FieldTypeEnum = Field(..., description="Inferred data type")

    required: bool = Field(
        default=True, description="Whether field is present in all examples"
    )

    nullable: bool = Field(default=False, description="Whether field can be null/None")

    nested_level: int = Field(
        default=0,
        description="Depth of nesting (0 = top level, 1 = one level deep, etc.)",
    )

    is_array: bool = Field(default=False, description="Whether field is an array")

    array_item_type: Optional[FieldTypeEnum] = Field(
        None, description="Type of array items (if is_array=True)"
    )

    sample_values: List[Any] = Field(
        default_factory=list, description="Sample values from examples"
    )


class Schema(BaseModel):
    """Represents input or output data schema.

    A schema describes the structure, types, and constraints of data.
    Inferred from analyzing example input/output pairs.

    Example:
        >>> schema = Schema(
        ...     fields=[
        ...         SchemaField(path="name", field_type=FieldTypeEnum.STRING),
        ...         SchemaField(path="main.temp", field_type=FieldTypeEnum.FLOAT, nested_level=1)
        ...     ]
        ... )
    """

    fields: List[SchemaField] = Field(
        default_factory=list, description="List of fields in schema"
    )

    is_nested: bool = Field(
        default=False, description="Whether schema contains nested structures"
    )

    has_arrays: bool = Field(
        default=False, description="Whether schema contains array fields"
    )

    def get_field(self, path: str) -> Optional[SchemaField]:
        """Get field by path."""
        for field in self.fields:
            if field.path == path:
                return field
        return None

    def get_top_level_fields(self) -> List[SchemaField]:
        """Get only top-level fields (nested_level=0)."""
        return [f for f in self.fields if f.nested_level == 0]

    def get_nested_fields(self) -> List[SchemaField]:
        """Get only nested fields (nested_level>0)."""
        return [f for f in self.fields if f.nested_level > 0]

    def get_array_fields(self) -> List[SchemaField]:
        """Get only array fields."""
        return [f for f in self.fields if f.is_array]


class SchemaDifference(BaseModel):
    """Represents a difference between input and output schemas.

    Used to identify potential transformation patterns by comparing
    what changes between input and output.

    Example:
        >>> diff = SchemaDifference(
        ...     input_path="main.temp",
        ...     output_path="temperature_c",
        ...     difference_type="field_rename",
        ...     description="Field 'main.temp' renamed to 'temperature_c'"
        ... )
    """

    input_path: Optional[str] = Field(
        None, description="Path in input schema (None if field only in output)"
    )

    output_path: Optional[str] = Field(
        None, description="Path in output schema (None if field only in input)"
    )

    difference_type: str = Field(
        ...,
        description="Type of difference (added, removed, renamed, type_changed, etc.)",
    )

    description: str = Field(
        ..., description="Human-readable description of the difference"
    )

    input_type: Optional[FieldTypeEnum] = Field(
        None, description="Input field type (if applicable)"
    )

    output_type: Optional[FieldTypeEnum] = Field(
        None, description="Output field type (if applicable)"
    )


class ParsedExamples(BaseModel):
    """Result of parsing and analyzing example input/output pairs.

    Contains extracted schemas, identified patterns, and analysis metadata.

    Example:
        >>> parsed = ParsedExamples(
        ...     input_schema=input_schema,
        ...     output_schema=output_schema,
        ...     patterns=[pattern1, pattern2],
        ...     num_examples=3
        ... )
    """

    input_schema: Schema = Field(..., description="Inferred input data schema")

    output_schema: Schema = Field(..., description="Inferred output data schema")

    patterns: List[Pattern] = Field(
        default_factory=list, description="Identified transformation patterns"
    )

    schema_differences: List[SchemaDifference] = Field(
        default_factory=list, description="Differences between input and output schemas"
    )

    num_examples: int = Field(..., ge=0, description="Number of examples analyzed")

    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings about pattern inconsistencies or edge cases",
    )

    @property
    def all_patterns(self) -> List[Pattern]:
        """Get all patterns (alias for patterns field for consistency with FilteredParsedExamples)."""
        return self.patterns

    @property
    def high_confidence_patterns(self) -> List[Pattern]:
        """Get patterns with confidence >= 0.9."""
        return [p for p in self.patterns if p.confidence >= 0.9]

    @property
    def medium_confidence_patterns(self) -> List[Pattern]:
        """Get patterns with 0.7 <= confidence < 0.9."""
        return [p for p in self.patterns if 0.7 <= p.confidence < 0.9]

    @property
    def low_confidence_patterns(self) -> List[Pattern]:
        """Get patterns with confidence < 0.7."""
        return [p for p in self.patterns if p.confidence < 0.7]

    def get_patterns_by_type(self, pattern_type: PatternType) -> List[Pattern]:
        """Get all patterns of a specific type."""
        return [p for p in self.patterns if p.type == pattern_type]

    def get_pattern_for_field(self, target_path: str) -> Optional[Pattern]:
        """Get pattern that produces a specific output field."""
        for pattern in self.patterns:
            if pattern.target_path == target_path:
                return pattern
        return None


class FilteredParsedExamples(BaseModel):
    """Filtered ParsedExamples with patterns split by confidence threshold.

    This model extends ParsedExamples concept by separating patterns into
    included (meeting threshold) and excluded (below threshold) groups.
    Used by PatternFilterService for interactive confidence threshold selection.

    Design Rationale:
    - **Separation of Concerns**: Keeps original patterns intact while providing
      filtered views for code generation
    - **Explicit Filtering**: Makes threshold-based decisions transparent
    - **Warning Integration**: Captures filtering impact for user feedback

    Example:
        >>> filtered = FilteredParsedExamples(
        ...     input_schema=input_schema,
        ...     output_schema=output_schema,
        ...     all_patterns=[p1, p2, p3],
        ...     included_patterns=[p1, p2],  # confidence >= 0.7
        ...     excluded_patterns=[p3],       # confidence < 0.7
        ...     confidence_threshold=0.7,
        ...     num_examples=3
        ... )
        >>> assert len(filtered.included_patterns) == 2
        >>> assert all(p.confidence >= 0.7 for p in filtered.included_patterns)

    Related to: 1M-362 (Interactive Confidence Threshold UX)
    """

    input_schema: Schema = Field(..., description="Inferred input data schema")

    output_schema: Schema = Field(..., description="Inferred output data schema")

    all_patterns: List[Pattern] = Field(
        default_factory=list, description="All detected patterns before filtering"
    )

    included_patterns: List[Pattern] = Field(
        default_factory=list,
        description="Patterns meeting confidence threshold (will be used for code generation)",
    )

    excluded_patterns: List[Pattern] = Field(
        default_factory=list,
        description="Patterns below confidence threshold (excluded from code generation)",
    )

    confidence_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence threshold used for filtering (0.0 to 1.0)",
    )

    schema_differences: List[SchemaDifference] = Field(
        default_factory=list, description="Differences between input and output schemas"
    )

    num_examples: int = Field(..., ge=0, description="Number of examples analyzed")

    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings about filtering impact and excluded patterns",
    )

    @property
    def patterns(self) -> List[Pattern]:
        """Get included patterns (alias for compatibility with ParsedExamples interface)."""
        return self.included_patterns

    @property
    def high_confidence_patterns(self) -> List[Pattern]:
        """Get included patterns with confidence >= 0.9."""
        return [p for p in self.included_patterns if p.confidence >= 0.9]

    @property
    def medium_confidence_patterns(self) -> List[Pattern]:
        """Get included patterns with 0.7 <= confidence < 0.9."""
        return [p for p in self.included_patterns if 0.7 <= p.confidence < 0.9]

    @property
    def low_confidence_patterns(self) -> List[Pattern]:
        """Get included patterns with confidence < 0.7."""
        return [p for p in self.included_patterns if p.confidence < 0.7]

    def get_patterns_by_type(self, pattern_type: PatternType) -> List[Pattern]:
        """Get included patterns of a specific type."""
        return [p for p in self.included_patterns if p.type == pattern_type]

    def get_pattern_for_field(self, target_path: str) -> Optional[Pattern]:
        """Get included pattern that produces a specific output field."""
        for pattern in self.included_patterns:
            if pattern.target_path == target_path:
                return pattern
        return None


# ============================================================================
# PROMPT GENERATION MODELS
# ============================================================================


class PromptSection(BaseModel):
    """A section in the generated Sonnet 4.5 prompt.

    Example:
        >>> section = PromptSection(
        ...     title="Input Schema",
        ...     content="{ 'name': str, 'main': {'temp': float} }",
        ...     order=1
        ... )
    """

    title: str = Field(..., description="Section title")

    content: str = Field(..., description="Section content")

    order: int = Field(default=0, description="Display order (lower = earlier)")


class GeneratedPrompt(BaseModel):
    """Complete generated prompt for Sonnet 4.5.

    Contains all information needed for the LLM to generate transformation code.

    Example:
        >>> prompt = GeneratedPrompt(
        ...     sections=[section1, section2, section3],
        ...     metadata={"num_patterns": 5, "confidence": "high"}
        ... )
    """

    sections: List[PromptSection] = Field(
        default_factory=list, description="Ordered list of prompt sections"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Metadata about prompt generation"
    )

    def to_text(self) -> str:
        """Convert prompt to plain text format."""
        sorted_sections = sorted(self.sections, key=lambda s: s.order)
        parts = []

        for section in sorted_sections:
            parts.append(f"# {section.title}\n")
            parts.append(section.content)
            parts.append("\n\n")

        return "".join(parts).strip()

    def to_markdown(self) -> str:
        """Convert prompt to Markdown format."""
        sorted_sections = sorted(self.sections, key=lambda s: s.order)
        parts = []

        for section in sorted_sections:
            parts.append(f"## {section.title}\n\n")
            parts.append(section.content)
            parts.append("\n\n")

        return "".join(parts).strip()
