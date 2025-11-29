"""Main orchestrator service for Sonnet 4.5 integration.

This module provides the Sonnet4_5Service class which coordinates:
- PM Mode: Example analysis and extraction strategy design
- Coder Mode: Production code generation from strategy
- Conversation context management
- Validation pipeline integration
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from edgar.models.extraction_strategy import ExtractionStrategy
from edgar.services.context_manager import ContextManager
from edgar.services.openrouter_client import (
    OpenRouterAuthError,
    OpenRouterClient,
    OpenRouterRateLimitError,
)


@dataclass(frozen=True)
class Sonnet4_5Service:
    """Main service for AI-powered code generation using Sonnet 4.5.

    This service orchestrates the two-phase code generation process:
    1. PM Mode: Analyzes API examples and designs extraction strategy
    2. Coder Mode: Generates production-ready Python code from strategy

    Attributes:
        client: OpenRouter API client for Sonnet 4.5
        context: Conversation context manager
    """

    client: OpenRouterClient
    context: ContextManager

    async def analyze_examples(
        self,
        examples: list[dict[str, Any]],
        target_schema: type,
    ) -> dict[str, Any]:
        """Analyze API examples and generate extraction strategy (PM Mode).

        This method implements PM Mode by:
        1. Loading PM Mode prompt template
        2. Formatting examples and target schema for analysis
        3. Calling OpenRouter API with formatted prompt
        4. Parsing and validating the extraction strategy response
        5. Updating conversation context

        Args:
            examples: List of API response examples (minimum 1 required)
            target_schema: Target Pydantic model class with schema

        Returns:
            Extraction strategy as structured dictionary with fields:
            - data_source_type: Type of data source (REST_API, GraphQL, etc.)
            - response_format: Format of response (JSON, XML, etc.)
            - extraction_patterns: Field extraction patterns
            - transformations: Data transformations
            - validation_rules: Field validation rules
            - cross_field_validations: Cross-field validation rules
            - error_handling: Error handling strategy
            - assumptions: List of assumptions made

        Raises:
            ValueError: If examples are empty, JSON parsing fails, or LLM response invalid
            OpenRouterAuthError: If API authentication fails
            OpenRouterRateLimitError: If rate limit exceeded (after retries)
            PydanticValidationError: If strategy doesn't match ExtractionStrategy schema

        Example:
            >>> service = Sonnet4_5Service(client, context)
            >>> examples = [{"temp": 72, "humidity": 45}]
            >>> strategy = await service.analyze_examples(examples, WeatherData)
            >>> print(strategy["data_source_type"])
            "REST_API"
        """
        # Validate inputs
        if not examples:
            raise ValueError("Examples list cannot be empty")

        # 1. Load PM Mode prompt template
        template = self._load_pm_template()

        # 2. Format examples for prompt
        examples_text = self._format_examples(examples)

        # 3. Format target schema
        schema_text = self._format_schema(target_schema)

        # 4. Build system message from template
        system_message = template.format(
            examples=examples_text,
            target_schema=schema_text,
        )

        # 5. Add to context manager
        self.context.add_system_message(system_message)
        self.context.add_user_message(
            "Analyze these examples and design the extraction strategy."
        )

        # 6. Call OpenRouter API
        messages = self.context.get_messages()
        try:
            response = await self.client.chat_completion(
                messages=messages,
                temperature=0.3,  # Lower temp for structured output
                max_tokens=4096,
            )
        except OpenRouterAuthError as e:
            raise OpenRouterAuthError(
                f"OpenRouter authentication failed. Please check your API key: {e}"
            ) from e
        except OpenRouterRateLimitError as e:
            raise OpenRouterRateLimitError(
                f"OpenRouter rate limit exceeded. Please retry later: {e}"
            ) from e

        # 7. Parse response content
        content = response["choices"][0]["message"]["content"]

        # 8. Update context with assistant response
        self.context.add_assistant_message(content)

        # 9. Extract JSON from content (handles markdown code blocks)
        try:
            strategy_dict = self._extract_json(content)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(
                f"Failed to parse JSON from LLM response. "
                f"Response may not be valid JSON: {e}"
            ) from e

        # 10. Validate against ExtractionStrategy model
        try:
            strategy = ExtractionStrategy(**strategy_dict)
        except PydanticValidationError as e:
            # Re-raise with additional context
            raise ValueError(
                f"LLM response doesn't match ExtractionStrategy schema. "
                f"Validation errors: {e}"
            ) from e

        # 11. Return as dictionary
        return strategy.model_dump()

    async def generate_code(
        self,
        strategy: dict[str, Any],
        architecture_constraints: dict[str, Any] | None = None,
    ) -> str:
        """Generate production-ready Python code from strategy (Coder Mode).

        This method implements Coder Mode by:
        1. Loading Coder Mode prompt template
        2. Formatting strategy and architecture constraints
        3. Calling OpenRouter API with formatted prompt
        4. Extracting Python code from response (handling markdown)
        5. Validating code syntax using AST
        6. Updating conversation context

        Args:
            strategy: Extraction strategy from PM Mode (required)
            architecture_constraints: Optional architecture constraints. If None, uses defaults:
                - interfaces: ["IDataSource", "IDataExtractor"]
                - use_dependency_injection: True
                - use_pydantic_models: True
                - type_hints_required: True
                - docstrings_required: True
                - pep8_compliance: True

        Returns:
            Complete Python module as string with:
            - Exception classes
            - Pydantic models
            - Data source implementation (IDataSource)
            - Data extractor implementation (IDataExtractor)

        Raises:
            ValueError: If strategy is empty, code has syntax errors, or no code generated
            OpenRouterAuthError: If API authentication fails
            OpenRouterRateLimitError: If rate limit exceeded (after retries)

        Example:
            >>> strategy = {"data_source_type": "REST_API", ...}
            >>> code = await service.generate_code(strategy)
            >>> assert "class" in code
            >>> assert "IDataSource" in code or "IDataExtractor" in code
        """
        # Validate inputs
        if not strategy:
            raise ValueError("Strategy dictionary cannot be empty")

        # 1. Use default constraints if none provided
        if architecture_constraints is None:
            architecture_constraints = {
                "interfaces": ["IDataSource", "IDataExtractor"],
                "use_dependency_injection": True,
                "use_pydantic_models": True,
                "type_hints_required": True,
                "docstrings_required": True,
                "pep8_compliance": True,
            }

        # 2. Load Coder Mode prompt template
        template = self._load_coder_template()

        # 3. Format strategy and constraints for prompt
        strategy_text = json.dumps(strategy, indent=2, ensure_ascii=False)
        constraints_text = json.dumps(architecture_constraints, indent=2, ensure_ascii=False)

        # 4. Build system message from template
        system_message = template.format(
            extraction_strategy=strategy_text,
            architecture_constraints=constraints_text,
        )

        # 5. Add to context manager
        self.context.add_system_message(system_message)
        self.context.add_user_message(
            "Generate the complete Python code implementing this extraction strategy."
        )

        # 6. Call OpenRouter API
        messages = self.context.get_messages()
        try:
            response = await self.client.chat_completion(
                messages=messages,
                temperature=0.2,  # Lower temperature for code generation
                max_tokens=8192,  # More tokens for complete code
            )
        except OpenRouterAuthError as e:
            raise OpenRouterAuthError(
                f"OpenRouter authentication failed. Please check your API key: {e}"
            ) from e
        except OpenRouterRateLimitError as e:
            raise OpenRouterRateLimitError(
                f"OpenRouter rate limit exceeded. Please retry later: {e}"
            ) from e

        # 7. Extract content from response
        content = response["choices"][0]["message"]["content"]

        # 8. Update context with assistant response
        self.context.add_assistant_message(content)

        # 9. Extract Python code from response (handles markdown wrapping)
        code = self._extract_python_code(content)

        # 10. Validate code has content
        if not code or not code.strip():
            raise ValueError(
                "Generated code is empty. LLM may have failed to generate valid code."
            )

        # 11. Validate code syntax using AST
        self._validate_code_syntax(code)

        # 12. Return generated code
        return code

    async def validate_and_refine(
        self,
        code: str,
        examples: list[dict[str, Any]],
    ) -> str:
        """Validate generated code and refine through conversation.

        Args:
            code: Generated Python code to validate
            examples: Original API examples for accuracy testing

        Returns:
            Refined and validated Python code

        Raises:
            ValidationError: If code fails validation
        """
        # TODO: Implement validation and refinement loop
        raise NotImplementedError("Validation not yet implemented")

    def _load_pm_template(self) -> str:
        """Load PM Mode prompt template from file.

        Returns:
            PM Mode prompt template as string

        Raises:
            FileNotFoundError: If template file doesn't exist
            IOError: If template file cannot be read
        """
        # Get template path relative to this file
        template_path = Path(__file__).parent.parent / "prompts" / "pm_mode.txt"

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"PM Mode template not found at {template_path}. "
                f"Please ensure prompts/pm_mode.txt exists."
            ) from e
        except IOError as e:
            raise IOError(
                f"Failed to read PM Mode template from {template_path}: {e}"
            ) from e

    def _format_examples(self, examples: list[dict[str, Any]]) -> str:
        """Format API response examples for prompt.

        Args:
            examples: List of API response dictionaries

        Returns:
            Formatted examples string with numbered JSON blocks
        """
        formatted_examples = []
        for i, example in enumerate(examples, start=1):
            json_str = json.dumps(example, indent=2, ensure_ascii=False)
            formatted_examples.append(f"Example {i}:\n```json\n{json_str}\n```")

        return "\n\n".join(formatted_examples)

    def _format_schema(self, target_schema: type) -> str:
        """Format target schema for prompt.

        Args:
            target_schema: Pydantic model class or type with schema

        Returns:
            Formatted schema string (JSON schema or string representation)
        """
        # Try to get Pydantic model JSON schema
        if hasattr(target_schema, "model_json_schema"):
            schema_dict = target_schema.model_json_schema()
            return json.dumps(schema_dict, indent=2, ensure_ascii=False)

        # Fallback to string representation
        return str(target_schema)

    def _extract_json(self, content: str) -> dict[str, Any]:
        """Extract JSON from LLM response, handling markdown code blocks.

        This method handles cases where the LLM wraps JSON in markdown code blocks:
        - ```json ... ```
        - ``` ... ```
        - Or returns raw JSON

        Args:
            content: LLM response content (may contain markdown)

        Returns:
            Parsed JSON dictionary

        Raises:
            ValueError: If content doesn't contain valid JSON
            json.JSONDecodeError: If JSON parsing fails

        Example:
            >>> content = '```json\\n{"key": "value"}\\n```'
            >>> result = service._extract_json(content)
            >>> print(result)
            {"key": "value"}
        """
        # Remove leading/trailing whitespace
        content = content.strip()

        # Check if content is wrapped in markdown code blocks
        if content.startswith("```"):
            # Extract JSON between ``` markers
            lines = content.split("\n")
            json_lines = []
            in_code_block = False

            for line in lines:
                # Toggle code block state on ``` markers
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue

                # Collect lines inside code block
                if in_code_block:
                    json_lines.append(line)

            # If no content extracted, content may be malformed
            if not json_lines:
                raise ValueError(
                    "Content appears to have markdown code blocks but no JSON found inside"
                )

            content = "\n".join(json_lines)

        # Parse JSON
        try:
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Expected JSON object (dict), got {type(parsed).__name__}"
                )
            return parsed
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Failed to parse JSON from content: {e.msg}",
                e.doc,
                e.pos,
            ) from e

    def _load_coder_template(self) -> str:
        """Load Coder Mode prompt template from file.

        Returns:
            Coder Mode prompt template as string

        Raises:
            FileNotFoundError: If template file doesn't exist
            IOError: If template file cannot be read
        """
        # Get template path relative to this file
        template_path = Path(__file__).parent.parent / "prompts" / "coder_mode.txt"

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Coder Mode template not found at {template_path}. "
                f"Please ensure prompts/coder_mode.txt exists."
            ) from e
        except IOError as e:
            raise IOError(
                f"Failed to read Coder Mode template from {template_path}: {e}"
            ) from e

    def _extract_python_code(self, content: str) -> str:
        """Extract Python code from LLM response, handling markdown code blocks.

        This method handles cases where the LLM wraps Python code in markdown:
        - ```python ... ```
        - ``` ... ```
        - Or returns raw Python code

        Args:
            content: LLM response content (may contain markdown)

        Returns:
            Extracted Python code as string

        Example:
            >>> content = '```python\\nprint("hello")\\n```'
            >>> code = service._extract_python_code(content)
            >>> print(code)
            print("hello")
        """
        # Remove leading/trailing whitespace
        content = content.strip()

        # Check if wrapped in markdown code blocks
        if "```python" in content or "```" in content:
            # Extract code between ``` markers
            lines = content.split("\n")
            code_lines = []
            in_code_block = False

            for line in lines:
                # Check for code block start/end markers
                if line.strip().startswith("```"):
                    if not in_code_block:
                        # Entering code block
                        in_code_block = True
                        continue
                    else:
                        # Exiting code block - we found the end
                        break

                # Collect lines inside code block
                if in_code_block:
                    code_lines.append(line)

            # If we extracted code from markdown, return it
            if code_lines:
                return "\n".join(code_lines)

        # If no markdown detected or extraction failed, return content as-is
        # (assume entire content is code)
        return content

    def _validate_code_syntax(self, code: str) -> None:
        """Validate Python code syntax using AST parser.

        This method compiles the code to check for syntax errors without
        executing it. Uses Python's built-in AST parser.

        Args:
            code: Python code string to validate

        Raises:
            ValueError: If code has syntax errors (includes line number and message)

        Example:
            >>> code = "print('hello')"
            >>> service._validate_code_syntax(code)  # No error
            >>> bad_code = "print('unterminated"
            >>> service._validate_code_syntax(bad_code)  # Raises ValueError
        """
        import ast

        try:
            ast.parse(code)
        except SyntaxError as e:
            # Format error message with line number and details
            raise ValueError(
                f"Generated code has syntax errors at line {e.lineno}: {e.msg}\n"
                f"Problematic text: {e.text}"
            ) from e
