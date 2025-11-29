"""
Prompt Templates for Extract Transform Platform

This module provides generic prompt templates for AI-powered pattern detection
and code generation. Templates are designed to work across different data sources
(Excel, PDF, DOCX, APIs, etc.).

Design Decisions:
- **Generic Templates**: No domain-specific assumptions (works for any data)
- **Few-Shot Examples**: Include examples to guide pattern detection
- **Confidence Scoring**: Templates request confidence scores for patterns
- **Structured Output**: Request JSON responses for easy parsing

Migration Notes:
- Migrated from edgar_analyzer.services.prompt_generator
- Removed EDGAR-specific compensation analysis prompts
- Generalized for any data transformation use case
- 90% code reuse from proven templates

Usage:
    >>> from extract_transform_platform.ai.prompt_templates import PromptTemplates
    >>> templates = PromptTemplates()
    >>> prompt = templates.render_pattern_detection(
    ...     input_schema=input_schema,
    ...     output_schema=output_schema,
    ...     examples=examples
    ... )
"""

from typing import List, Dict, Any, Optional
import json


class PromptTemplates:
    """
    Generic prompt templates for pattern detection and code generation.

    This class provides reusable prompts for:
    - Pattern detection (field mappings, type conversions, etc.)
    - Code generation (Python extractor functions)
    - Schema analysis (input/output structure understanding)

    Example:
        >>> templates = PromptTemplates()
        >>> prompt = templates.render_pattern_detection(input_schema, output_schema, examples)
    """

    # ========================================================================
    # PATTERN DETECTION TEMPLATES
    # ========================================================================

    PATTERN_DETECTION_TEMPLATE = """
You are an expert data transformation analyst. Analyze the provided schemas and examples
to identify transformation patterns.

## Input Schema

{input_schema}

## Output Schema

{output_schema}

## Transformation Examples

{examples}

## Your Task

Identify ALL transformation patterns between input and output. For each pattern, provide:

1. **Pattern Type**: One of:
   - field_mapping: Direct field rename (employee_id → id)
   - concatenation: Multiple fields combined (first_name + last_name → full_name)
   - type_conversion: Type change (int → float, string → date)
   - boolean_mapping: Boolean normalization ("Yes" → true, "No" → false)
   - value_mapping: Discrete value transformations ("A" → "Active")
   - field_extraction: Substring extraction (email → domain)
   - array_first: Extract first element from array
   - constant: Always same value
   - complex: Requires custom logic

2. **Confidence Score**: 0.0-1.0 indicating confidence in pattern detection
   - 0.9-1.0: Very confident (consistent across all examples)
   - 0.7-0.89: Confident (mostly consistent)
   - 0.5-0.69: Moderate (some inconsistencies)
   - <0.5: Low confidence (unclear pattern)

3. **Source Path**: Input field path (e.g., "employee_id", "address.city")

4. **Target Path**: Output field path (e.g., "id", "location.city_name")

5. **Transformation**: Description of the transformation logic

6. **Examples**: List of (input_value, output_value) pairs showing the transformation

## Output Format (JSON)

Respond with ONLY valid JSON in this exact format:

```json
{{
  "patterns": [
    {{
      "type": "field_mapping",
      "confidence": 0.95,
      "source_path": "employee_id",
      "target_path": "id",
      "transformation": "Direct field rename",
      "examples": [
        ["E1001", "E1001"],
        ["E1002", "E1002"]
      ]
    }},
    {{
      "type": "concatenation",
      "confidence": 0.98,
      "source_path": "first_name,last_name",
      "target_path": "full_name",
      "transformation": "Concatenate first_name and last_name with space",
      "examples": [
        [["Alice", "Johnson"], "Alice Johnson"],
        [["Bob", "Smith"], "Bob Smith"]
      ]
    }},
    {{
      "type": "boolean_mapping",
      "confidence": 0.92,
      "source_path": "is_manager",
      "target_path": "manager",
      "transformation": "Map 'Yes'/'No' to true/false",
      "examples": [
        ["Yes", true],
        ["No", false]
      ]
    }}
  ],
  "warnings": [
    "Field 'middle_name' in input has no corresponding output field",
    "Output field 'created_date' appears to be a constant value"
  ]
}}
```

## Important Guidelines

- Analyze ALL fields in both schemas
- Provide concrete examples from the provided data
- Be conservative with confidence scores (prefer lower if uncertain)
- Note any missing mappings or unusual patterns in warnings
- Focus on identifying the transformation logic, not implementing it
"""

    # ========================================================================
    # CODE GENERATION TEMPLATES
    # ========================================================================

    CODE_GENERATION_TEMPLATE = """
You are an expert Python developer. Generate a production-ready transformation function
based on the identified patterns.

## Identified Patterns

{patterns_json}

## Examples to Validate

{examples_json}

## Your Task

Generate a complete Python transformation function that implements ALL identified patterns.

## Requirements

1. **Function Signature**:
   ```python
   def transform(input_data: Dict[str, Any]) -> Dict[str, Any]:
       \"\"\"Transform input data to output format.\"\"\"
       # Your implementation
   ```

2. **Implementation Guidelines**:
   - Use type hints for all function parameters and return values
   - Handle missing fields gracefully (use `.get()` with sensible defaults)
   - Preserve data types (int, float, str, bool, date)
   - Add logging for traceability (use `logger.debug()`)
   - Include comprehensive docstring
   - Handle errors without crashing (log and continue)

3. **Error Handling**:
   - Log warnings for missing critical fields
   - Use `Optional` types for nullable fields
   - Provide sensible defaults where appropriate
   - Never raise exceptions for missing optional fields

4. **Testing**:
   - Function MUST pass all provided examples
   - Verify output structure matches expected schema
   - Handle edge cases (None, empty strings, empty arrays)

## Output Format

Respond with ONLY the Python function code (no explanations):

```python
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def transform(input_data: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"
    Transform input data to output format.

    Transformations:
    - Field mappings: employee_id → id, ...
    - Type conversions: salary (int) → (float), ...
    - Concatenations: first_name + last_name → full_name
    - Boolean mappings: "Yes"/"No" → true/false

    Args:
        input_data: Input dictionary matching input schema

    Returns:
        Transformed dictionary matching output schema
    \"\"\"
    output = {{}}

    # Your implementation here

    return output
```
"""

    # ========================================================================
    # SCHEMA ANALYSIS TEMPLATE
    # ========================================================================

    SCHEMA_ANALYSIS_TEMPLATE = """
You are a data schema expert. Analyze the provided data and infer its structure.

## Sample Data

{sample_data}

## Your Task

Analyze the data and provide a structured schema description.

For each field, identify:
1. **Path**: Field name or nested path (e.g., "name", "address.city")
2. **Type**: Data type (str, int, float, bool, date, datetime, list, dict)
3. **Nullable**: Whether the field can be null/None
4. **Required**: Whether the field is always present
5. **Sample Values**: 2-3 example values
6. **Description**: Brief description of what the field represents

## Output Format (JSON)

```json
{{
  "fields": [
    {{
      "path": "employee_id",
      "type": "str",
      "nullable": false,
      "required": true,
      "sample_values": ["E1001", "E1002", "E1003"],
      "description": "Unique employee identifier"
    }},
    {{
      "path": "salary",
      "type": "float",
      "nullable": false,
      "required": true,
      "sample_values": [95000.0, 87000.0, 105000.0],
      "description": "Annual salary in USD"
    }},
    {{
      "path": "middle_name",
      "type": "str",
      "nullable": true,
      "required": false,
      "sample_values": ["Marie", null, "Lee"],
      "description": "Employee middle name (optional)"
    }}
  ]
}}
```
"""

    # ========================================================================
    # TEMPLATE RENDERING METHODS
    # ========================================================================

    def render_pattern_detection(
        self,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        examples: List[Dict[str, Any]],
        confidence_threshold: Optional[float] = None
    ) -> str:
        """
        Render pattern detection prompt.

        Args:
            input_schema: Input data schema
            output_schema: Output data schema
            examples: List of input/output example pairs
            confidence_threshold: Optional minimum confidence (0.0-1.0)

        Returns:
            Rendered prompt ready for LLM

        Example:
            >>> prompt = templates.render_pattern_detection(
            ...     input_schema={"fields": [...]},
            ...     output_schema={"fields": [...]},
            ...     examples=[{"input": {...}, "output": {...}}]
            ... )
        """
        # Format schemas
        input_schema_str = self._format_schema(input_schema)
        output_schema_str = self._format_schema(output_schema)

        # Format examples
        examples_str = self._format_examples(examples)

        # Render template
        prompt = self.PATTERN_DETECTION_TEMPLATE.format(
            input_schema=input_schema_str,
            output_schema=output_schema_str,
            examples=examples_str
        )

        # Add confidence threshold note if specified
        if confidence_threshold is not None:
            prompt += f"\n\n**Minimum Confidence Threshold**: {confidence_threshold}\n"
            prompt += "Only include patterns with confidence >= this threshold.\n"

        return prompt

    def render_code_generation(
        self,
        patterns: List[Dict[str, Any]],
        examples: List[Dict[str, Any]]
    ) -> str:
        """
        Render code generation prompt.

        Args:
            patterns: Identified transformation patterns
            examples: Input/output example pairs for validation

        Returns:
            Rendered prompt ready for LLM

        Example:
            >>> prompt = templates.render_code_generation(
            ...     patterns=[{"type": "field_mapping", ...}],
            ...     examples=[{"input": {...}, "output": {...}}]
            ... )
        """
        patterns_json = json.dumps(patterns, indent=2)
        examples_json = json.dumps(examples, indent=2)

        return self.CODE_GENERATION_TEMPLATE.format(
            patterns_json=patterns_json,
            examples_json=examples_json
        )

    def render_schema_analysis(
        self,
        sample_data: List[Dict[str, Any]]
    ) -> str:
        """
        Render schema analysis prompt.

        Args:
            sample_data: Sample data records to analyze

        Returns:
            Rendered prompt ready for LLM

        Example:
            >>> prompt = templates.render_schema_analysis(
            ...     sample_data=[{...}, {...}, {...}]
            ... )
        """
        sample_data_str = json.dumps(sample_data, indent=2)

        return self.SCHEMA_ANALYSIS_TEMPLATE.format(
            sample_data=sample_data_str
        )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """
        Format schema as readable text.

        Args:
            schema: Schema dictionary

        Returns:
            Formatted schema text
        """
        if "fields" in schema:
            # Structured schema
            lines = ["```json"]
            lines.append(json.dumps(schema, indent=2))
            lines.append("```")
            return "\n".join(lines)
        else:
            # Simple schema
            return json.dumps(schema, indent=2)

    def _format_examples(self, examples: List[Dict[str, Any]]) -> str:
        """
        Format examples as readable text.

        Args:
            examples: List of example pairs

        Returns:
            Formatted examples text
        """
        lines = []

        for i, example in enumerate(examples, 1):
            lines.append(f"### Example {i}\n")

            if "input" in example and "output" in example:
                lines.append("**Input**:")
                lines.append("```json")
                lines.append(json.dumps(example["input"], indent=2))
                lines.append("```\n")

                lines.append("**Output**:")
                lines.append("```json")
                lines.append(json.dumps(example["output"], indent=2))
                lines.append("```\n")
            else:
                # Fallback format
                lines.append("```json")
                lines.append(json.dumps(example, indent=2))
                lines.append("```\n")

        return "\n".join(lines)


# ============================================================================
# DOMAIN-SPECIFIC TEMPLATE EXTENSIONS
# ============================================================================


class EDGARPromptTemplates(PromptTemplates):
    """
    EDGAR-specific prompt template extensions.

    Adds executive compensation analysis prompts on top of generic templates.
    This demonstrates how domain-specific applications can extend the base templates.

    Example:
        >>> edgar_templates = EDGARPromptTemplates()
        >>> # Use generic templates
        >>> pattern_prompt = edgar_templates.render_pattern_detection(...)
        >>> # Use EDGAR-specific templates
        >>> compensation_prompt = edgar_templates.render_compensation_analysis(...)
    """

    # EDGAR-specific prompts would go here
    # (Kept separate from generic platform templates)
    pass
