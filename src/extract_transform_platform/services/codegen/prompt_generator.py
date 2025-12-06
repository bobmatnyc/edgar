"""
Prompt generation service for Sonnet 4.5 code generation.

This service converts parsed examples and identified patterns into structured
prompts optimized for Sonnet 4.5 LLM code generation.

Design Decisions:
- **Structured Format**: Clear sections for schemas, patterns, requirements
- **Example-Rich**: Include concrete examples for each pattern
- **Confidence Transparency**: Show confidence scores to guide LLM
- **Implementation Guidance**: Provide specific requirements and constraints

Usage:
    >>> generator = PromptGenerator()
    >>> parsed = parser.parse_examples(examples)
    >>> prompt = generator.generate_prompt(parsed)
    >>> print(prompt.to_markdown())

Migration Status: MIGRATED from EDGAR (1M-379, T4)
- Origin: edgar_analyzer.services.prompt_generator
- Platform: extract_transform_platform.services.codegen.prompt_generator
- Code reuse: 100% (436 LOC preserved)
- Tests: 0 breaking changes
"""

import logging
from typing import List

from extract_transform_platform.models.patterns import (
    GeneratedPrompt,
    ParsedExamples,
    Pattern,
    PatternType,
    PromptSection,
    SchemaField,
)

logger = logging.getLogger(__name__)


class PromptGenerator:
    """Generate Sonnet 4.5 prompts from parsed examples and patterns.

    Converts pattern analysis results into structured prompts that guide
    the LLM to generate accurate transformation code.

    Example:
        >>> generator = PromptGenerator()
        >>> prompt = generator.generate_prompt(parsed_examples)
        >>> with open("prompt.md", "w") as f:
        ...     f.write(prompt.to_markdown())
    """

    def __init__(self) -> None:
        """Initialize PromptGenerator."""
        self.logger = logger

    def generate_prompt(
        self, parsed: ParsedExamples, project_name: str = "transformation"
    ) -> GeneratedPrompt:
        """Generate Sonnet 4.5 prompt from parsed examples.

        Creates a comprehensive prompt with:
        - Input/output schemas
        - Identified transformation patterns
        - Concrete examples
        - Implementation requirements
        - Type safety guidelines

        Args:
            parsed: ParsedExamples from ExampleParser
            project_name: Name of the project/transformation

        Returns:
            GeneratedPrompt ready for Sonnet 4.5

        Example:
            >>> prompt = generator.generate_prompt(parsed)
            >>> print(prompt.to_text())
        """
        sections: List[PromptSection] = []

        # Section 1: Overview
        sections.append(self._create_overview_section(parsed, project_name))

        # Section 2: Input Schema
        sections.append(self._create_input_schema_section(parsed.input_schema))

        # Section 3: Output Schema
        sections.append(self._create_output_schema_section(parsed.output_schema))

        # Section 4: Transformation Patterns
        sections.append(self._create_patterns_section(parsed.patterns))

        # Section 5: Pattern Details
        sections.extend(self._create_pattern_detail_sections(parsed.patterns))

        # Section 6: Implementation Requirements
        sections.append(self._create_requirements_section(parsed))

        # Section 7: Edge Cases and Warnings
        if parsed.warnings:
            sections.append(self._create_warnings_section(parsed.warnings))

        metadata = {
            "num_patterns": len(parsed.patterns),
            "num_examples": parsed.num_examples,
            "high_confidence_patterns": len(parsed.high_confidence_patterns),
            "project_name": project_name,
        }

        self.logger.info(
            f"Generated prompt for '{project_name}': "
            f"{len(sections)} sections, {len(parsed.patterns)} patterns"
        )

        return GeneratedPrompt(sections=sections, metadata=metadata)

    def _create_overview_section(
        self, parsed: ParsedExamples, project_name: str
    ) -> PromptSection:
        """Create overview section."""
        content = f"""**Project**: {project_name}
**Task**: Generate Python transformation function based on identified patterns

**Analysis Summary**:
- Examples Analyzed: {parsed.num_examples}
- Patterns Identified: {len(parsed.patterns)}
- High Confidence Patterns: {len(parsed.high_confidence_patterns)} ({len(parsed.high_confidence_patterns)/max(len(parsed.patterns), 1)*100:.0f}%)
- Input Fields: {len(parsed.input_schema.fields)}
- Output Fields: {len(parsed.output_schema.fields)}
"""

        return PromptSection(
            title="Example Parser Output for Sonnet 4.5", content=content, order=1
        )

    def _create_input_schema_section(self, schema) -> PromptSection:
        """Create input schema section."""
        content = self._format_schema(schema, "Input")

        return PromptSection(title="Input Schema", content=content, order=2)

    def _create_output_schema_section(self, schema) -> PromptSection:
        """Create output schema section."""
        content = self._format_schema(schema, "Output")

        return PromptSection(title="Output Schema", content=content, order=3)

    def _format_schema(self, schema, schema_type: str) -> str:
        """Format schema as readable text.

        Args:
            schema: Schema object
            schema_type: "Input" or "Output"

        Returns:
            Formatted schema text
        """
        lines = [f"**{schema_type} Data Structure**:\n"]

        # Group fields by nesting level
        top_level = schema.get_top_level_fields()
        nested = schema.get_nested_fields()

        lines.append("```python")
        lines.append("{")

        for field in top_level:
            type_str = self._field_type_to_python(field)
            required = "" if field.required else "  # Optional"
            lines.append(f'  "{field.path}": {type_str},{required}')

        if nested:
            lines.append("  # Nested fields:")
            for field in nested[:5]:  # Show first 5 nested fields
                type_str = self._field_type_to_python(field)
                lines.append(f'  # "{field.path}": {type_str}')

            if len(nested) > 5:
                lines.append(f"  # ... and {len(nested) - 5} more nested fields")

        lines.append("}")
        lines.append("```\n")

        # Add field details
        if top_level:
            lines.append("\n**Field Details**:")
            for field in top_level:
                nullable = " (nullable)" if field.nullable else ""
                samples = ", ".join(str(s) for s in field.sample_values[:2])
                lines.append(f"- `{field.path}`: {field.field_type.value}{nullable}")
                if samples:
                    lines.append(f"  - Examples: {samples}")

        return "\n".join(lines)

    def _field_type_to_python(self, field: SchemaField) -> str:
        """Convert FieldTypeEnum to Python type hint.

        Args:
            field: SchemaField

        Returns:
            Python type hint string
        """
        type_map = {
            "str": "str",
            "int": "int",
            "float": "float",
            "decimal": "Decimal",
            "bool": "bool",
            "date": "date",
            "datetime": "datetime",
            "list": "List",
            "dict": "Dict",
            "null": "None",
            "unknown": "Any",
        }

        base_type = type_map.get(field.field_type.value, "Any")

        if field.is_array and field.array_item_type:
            item_type = type_map.get(field.array_item_type.value, "Any")
            return f"List[{item_type}]"

        if field.nullable:
            return f"Optional[{base_type}]"

        return base_type

    def _create_patterns_section(self, patterns: List[Pattern]) -> PromptSection:
        """Create patterns overview section."""
        lines = ["**Pattern Summary**:\n"]

        # Group by type
        pattern_types = {}
        for pattern in patterns:
            if pattern.type not in pattern_types:
                pattern_types[pattern.type] = []
            pattern_types[pattern.type].append(pattern)

        for pattern_type, type_patterns in sorted(pattern_types.items()):
            avg_confidence = sum(p.confidence for p in type_patterns) / len(
                type_patterns
            )
            lines.append(
                f"- **{pattern_type.value.replace('_', ' ').title()}**: "
                f"{len(type_patterns)} patterns (avg confidence: {avg_confidence:.0%})"
            )

        return PromptSection(
            title="Identified Patterns", content="\n".join(lines), order=4
        )

    def _create_pattern_detail_sections(
        self, patterns: List[Pattern]
    ) -> List[PromptSection]:
        """Create detailed sections for each pattern.

        Args:
            patterns: List of patterns

        Returns:
            List of PromptSections, one per pattern
        """
        sections: List[PromptSection] = []

        # Sort by confidence (high to low)
        sorted_patterns = sorted(patterns, key=lambda p: p.confidence, reverse=True)

        for i, pattern in enumerate(sorted_patterns, 1):
            section = self._create_pattern_detail(pattern, i)
            sections.append(section)

        return sections

    def _create_pattern_detail(self, pattern: Pattern, index: int) -> PromptSection:
        """Create detailed section for a single pattern.

        Args:
            pattern: Pattern object
            index: Pattern number

        Returns:
            PromptSection with pattern details
        """
        confidence_pct = f"{pattern.confidence * 100:.0f}%"
        confidence_label = pattern.confidence_level

        lines = [
            f"**Type**: {pattern.type.value.replace('_', ' ').title()}",
            f"**Confidence**: {confidence_pct} ({confidence_label})",
            f"**Source**: `{pattern.source_path}`",
            f"**Target**: `{pattern.target_path}`",
            f"**Transformation**: {pattern.transformation}\n",
        ]

        # Add type information
        if pattern.source_type and pattern.target_type:
            lines.append(
                f"**Type Conversion**: {pattern.source_type.value} → {pattern.target_type.value}"
            )
            if pattern.is_type_safe:
                lines.append("**Type Safety**: ✓ Safe conversion")
            else:
                lines.append("**Type Safety**: ⚠ Requires careful handling")

        # Add examples
        if pattern.examples:
            lines.append("\n**Examples**:")
            for inp, out in pattern.examples[:3]:  # Show first 3
                lines.append(f"- Input: `{inp}` → Output: `{out}`")

            if len(pattern.examples) > 3:
                lines.append(f"- ... and {len(pattern.examples) - 3} more examples")

        # Add implementation guidance
        lines.append("\n**Implementation Guidance**:")
        lines.extend(self._get_implementation_guidance(pattern))

        # Add notes if present
        if pattern.notes:
            lines.append(f"\n**Notes**: {pattern.notes}")

        return PromptSection(
            title=f"Pattern {index}: {pattern.target_path}",
            content="\n".join(lines),
            order=5 + index,
        )

    def _get_implementation_guidance(self, pattern: Pattern) -> List[str]:
        """Get implementation guidance for a pattern type.

        Args:
            pattern: Pattern object

        Returns:
            List of guidance strings
        """
        guidance = {
            PatternType.FIELD_MAPPING: [
                "- Use direct dictionary access",
                "- Handle missing keys with `.get()` method",
                f"- Extract: `input_data['{pattern.source_path}']`",
            ],
            PatternType.FIELD_EXTRACTION: [
                "- Navigate nested structure carefully",
                "- Check for None at each level",
                f"- Path: {pattern.source_path}",
            ],
            PatternType.ARRAY_FIRST: [
                "- Check if array is non-empty",
                "- Access first element: `array[0]`",
                "- Handle empty array case",
            ],
            PatternType.TYPE_CONVERSION: [
                f"- Convert {pattern.source_type} to {pattern.target_type}",
                "- Handle conversion errors gracefully",
                "- Validate converted value",
            ],
            PatternType.CONSTANT: [
                f"- Set constant value: `{pattern.examples[0][1]}`",
                "- No input dependency",
                "- Always returns same value",
            ],
            PatternType.COMPLEX: [
                "- ⚠ Complex transformation detected",
                "- Review examples carefully",
                "- May require custom logic or calculation",
                "- Test thoroughly with all examples",
            ],
        }

        return guidance.get(pattern.type, ["- Implement based on examples"])

    def _create_requirements_section(self, parsed: ParsedExamples) -> PromptSection:
        """Create implementation requirements section."""
        lines = [
            "**Function Signature**:",
            "```python",
            "def transform(input_data: Dict[str, Any]) -> Dict[str, Any]:",
            '    """Transform input data to output format."""',
            "    # Your implementation here",
            "    pass",
            "```\n",
            "**Requirements**:",
            "- Use dependency injection for services",
            "- Handle nested dictionaries and arrays",
            "- Preserve types (float, int, str, bool)",
            "- Add logging for traceability",
            "- Include type hints",
            "- Handle missing fields gracefully (use `.get()` with defaults)",
            "- Validate output structure matches schema",
            "- Add docstring with transformation description\n",
            "**Error Handling**:",
            "- Log errors but don't crash on missing fields",
            "- Use Optional types for nullable fields",
            "- Provide sensible defaults where appropriate",
            "- Validate critical fields are present\n",
            "**Testing**:",
            "- Function must pass all provided examples",
            f"- Verify output matches expected structure for all {parsed.num_examples} examples",
            "- Test edge cases (null values, empty arrays, missing fields)",
        ]

        return PromptSection(
            title="Implementation Requirements", content="\n".join(lines), order=100
        )

    def _create_warnings_section(self, warnings: List[str]) -> PromptSection:
        """Create warnings section.

        Args:
            warnings: List of warning messages

        Returns:
            PromptSection with warnings
        """
        lines = ["**⚠ Warnings and Considerations**:\n"]
        for warning in warnings:
            lines.append(f"- {warning}")

        return PromptSection(title="Warnings", content="\n".join(lines), order=101)
