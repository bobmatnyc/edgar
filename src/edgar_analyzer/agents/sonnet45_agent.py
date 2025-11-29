"""
Sonnet 4.5 Agent - Dual-Mode AI Code Generation

This module implements a dual-agent system using Anthropic's Claude Sonnet 4.5
for AI-powered code generation with two distinct modes:
- PM (Planning Manager) Mode: Analyzes patterns and creates implementation plans
- Coder Mode: Generates production-ready code from plans

Design Decisions:
- **Dual-Mode Architecture**: Separation of planning from implementation
- **Structured Outputs**: JSON for plans, structured Python for code
- **Template-Based Prompts**: Consistent, high-quality prompts
- **Error Recovery**: Retry logic for API failures and malformed outputs
- **Validation**: All outputs validated before returning

Usage:
    >>> agent = Sonnet45Agent(api_key="sk-or-v1-...")
    >>> plan = await agent.plan(patterns, project_config)
    >>> code = await agent.code(plan, patterns)
    >>> # Or end-to-end:
    >>> code = await agent.plan_and_code(patterns, project_config)
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

import structlog
from pydantic import ValidationError

from edgar_analyzer.clients.openrouter_client import OpenRouterClient
from edgar_analyzer.models.patterns import Pattern, ParsedExamples
from edgar_analyzer.models.project_config import ProjectConfig
from edgar_analyzer.models.plan import (
    PlanSpec,
    GeneratedCode,
    GenerationContext,
    MethodSpec,
    ClassSpec,
)

logger = structlog.get_logger(__name__)


# ============================================================================
# PROMPT TEMPLATE LOADER
# ============================================================================


class PromptLoader:
    """Load and prepare prompt templates for Sonnet 4.5.

    Design Decision: File-based templates for easy iteration
    without code changes.
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize prompt loader.

        Args:
            prompts_dir: Directory containing prompt templates
        """
        if prompts_dir is None:
            # Default to prompts directory next to this file
            prompts_dir = Path(__file__).parent / "prompts"

        self.prompts_dir = prompts_dir

        logger.debug("PromptLoader initialized", prompts_dir=str(self.prompts_dir))

    def load_template(self, template_name: str) -> str:
        """
        Load a prompt template file.

        Args:
            template_name: Template filename (e.g., "pm_mode_prompt.md")

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template doesn't exist
        """
        template_path = self.prompts_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")

        with open(template_path, 'r') as f:
            content = f.read()

        logger.debug("Loaded prompt template", template=template_name, size=len(content))

        return content

    def render_pm_prompt(
        self,
        patterns: List[Pattern],
        project_config: ProjectConfig
    ) -> str:
        """
        Render PM mode prompt with patterns and configuration.

        Args:
            patterns: Identified transformation patterns
            project_config: Project configuration

        Returns:
            Rendered prompt ready for API call
        """
        template = self.load_template("pm_mode_prompt.md")

        # Serialize patterns to JSON
        patterns_data = [p.model_dump() for p in patterns]
        patterns_json = json.dumps(patterns_data, indent=2)

        # Serialize project config to JSON (use mode='json' to handle datetimes)
        config_json = json.dumps(project_config.model_dump(mode='json'), indent=2)

        # Replace placeholders
        prompt = template.replace("{{patterns_json}}", patterns_json)
        prompt = prompt.replace("{{project_config_json}}", config_json)

        logger.debug(
            "Rendered PM prompt",
            pattern_count=len(patterns),
            prompt_length=len(prompt)
        )

        return prompt

    def render_coder_prompt(
        self,
        plan: PlanSpec,
        patterns: List[Pattern],
        examples: List[Dict[str, Any]]
    ) -> str:
        """
        Render Coder mode prompt with plan and examples.

        Args:
            plan: PM-generated implementation plan
            patterns: Transformation patterns
            examples: Input/output example pairs

        Returns:
            Rendered prompt ready for API call
        """
        template = self.load_template("coder_mode_prompt.md")

        # Serialize plan to JSON
        plan_json = json.dumps(plan.model_dump(), indent=2)

        # Combine patterns and examples
        # Convert examples to dicts if they're ExampleConfig objects
        examples_dicts = []
        for ex in examples:
            if hasattr(ex, 'model_dump'):
                examples_dicts.append(ex.model_dump())
            elif hasattr(ex, 'dict'):
                examples_dicts.append(ex.dict())
            else:
                examples_dicts.append(ex)

        patterns_and_examples = {
            "patterns": [p.model_dump() for p in patterns],
            "examples": examples_dicts
        }
        patterns_examples_json = json.dumps(patterns_and_examples, indent=2)

        # Replace placeholders
        prompt = template.replace("{{plan_spec_json}}", plan_json)
        prompt = prompt.replace("{{patterns_and_examples_json}}", patterns_examples_json)

        logger.debug(
            "Rendered Coder prompt",
            pattern_count=len(patterns),
            example_count=len(examples),
            prompt_length=len(prompt)
        )

        return prompt

    def render_coder_retry_prompt(
        self,
        plan: PlanSpec,
        patterns: List[Pattern],
        examples: List[Dict[str, Any]],
        validation_errors: Any
    ) -> str:
        """
        Render Coder mode retry prompt with validation errors.

        Args:
            plan: PM-generated implementation plan
            patterns: Transformation patterns
            examples: Input/output example pairs
            validation_errors: Validation result from previous attempt

        Returns:
            Rendered retry prompt with validation feedback
        """
        template = self.load_template("coder_mode_retry.md")

        # Serialize plan to JSON
        plan_json = json.dumps(plan.model_dump(), indent=2)

        # Combine patterns and examples
        # Convert examples to dicts if they're ExampleConfig objects
        examples_dicts = []
        for ex in examples:
            if hasattr(ex, 'model_dump'):
                examples_dicts.append(ex.model_dump())
            elif hasattr(ex, 'dict'):
                examples_dicts.append(ex.dict())
            else:
                examples_dicts.append(ex)

        patterns_and_examples = {
            "patterns": [p.model_dump() for p in patterns],
            "examples": examples_dicts
        }
        patterns_examples_json = json.dumps(patterns_and_examples, indent=2)

        # Format validation errors
        validation_errors_text = self._format_validation_errors(validation_errors)

        # Replace placeholders
        prompt = template.replace("{{plan_spec_json}}", plan_json)
        prompt = prompt.replace("{{patterns_and_examples_json}}", patterns_examples_json)
        prompt = prompt.replace("{{validation_errors}}", validation_errors_text)

        logger.debug(
            "Rendered Coder retry prompt",
            pattern_count=len(patterns),
            example_count=len(examples),
            validation_issues=len(validation_errors.issues) if hasattr(validation_errors, 'issues') else 0,
            prompt_length=len(prompt)
        )

        return prompt

    def _format_validation_errors(self, validation_result: Any) -> str:
        """
        Format validation errors for LLM context.

        Args:
            validation_result: CodeValidationResult object

        Returns:
            Formatted error text
        """
        if not hasattr(validation_result, 'issues'):
            return str(validation_result)

        formatted = []
        formatted.append("## Validation Issues")
        formatted.append("")

        if not validation_result.is_valid:
            formatted.append(f"**Overall Status**: INVALID (Quality Score: {validation_result.quality_score})")
            formatted.append("")

        if validation_result.issues:
            formatted.append("### Critical Issues (Must Fix)")
            for i, issue in enumerate(validation_result.issues, 1):
                formatted.append(f"{i}. {issue}")
            formatted.append("")

        if hasattr(validation_result, 'recommendations') and validation_result.recommendations:
            formatted.append("### Recommendations (Should Fix)")
            for i, rec in enumerate(validation_result.recommendations, 1):
                formatted.append(f"{i}. {rec}")
            formatted.append("")

        # Add quality metrics
        formatted.append("### Quality Metrics")
        formatted.append(f"- Syntax Valid: {'✅' if validation_result.syntax_valid else '❌'}")
        formatted.append(f"- Has Type Hints: {'✅' if validation_result.has_type_hints else '❌'}")
        formatted.append(f"- Has Docstrings: {'✅' if validation_result.has_docstrings else '❌'}")
        formatted.append(f"- Has Tests: {'✅' if validation_result.has_tests else '❌'}")
        formatted.append(f"- Implements Interface: {'✅' if validation_result.implements_interface else '❌'}")

        return "\n".join(formatted)


# ============================================================================
# SONNET 4.5 AGENT
# ============================================================================


class Sonnet45Agent:
    """
    Dual-mode AI agent using Sonnet 4.5 for code generation.

    This agent orchestrates two distinct AI modes:
    1. PM Mode: Analyzes patterns → creates implementation plan
    2. Coder Mode: Takes plan → generates production code

    Design Philosophy:
    - **Separation of Concerns**: Planning and coding are distinct skills
    - **Structured Outputs**: JSON plans, structured Python code
    - **Validation**: All outputs validated before use
    - **Error Recovery**: Graceful handling of API failures

    Example:
        >>> agent = Sonnet45Agent(api_key="sk-or-v1-...")
        >>> code = await agent.plan_and_code(patterns, project_config)
        >>> print(f"Generated {code.total_lines} lines of code")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "anthropic/claude-sonnet-4.5",
        pm_temperature: float = 0.3,
        coder_temperature: float = 0.2,
        max_retries: int = 3
    ):
        """
        Initialize Sonnet 4.5 agent.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            model: Model identifier
            pm_temperature: Temperature for PM mode (lower = more focused)
            coder_temperature: Temperature for Coder mode (lower = more deterministic)
            max_retries: Maximum retry attempts for failed API calls

        Design Decision: Lower temperatures for code generation to ensure
        consistent, deterministic output. PM mode slightly higher for creativity
        in design decisions.
        """
        self.model = model
        self.pm_temperature = pm_temperature
        self.coder_temperature = coder_temperature
        self.max_retries = max_retries

        # Initialize OpenRouter client
        self.client = OpenRouterClient(
            api_key=api_key,
            model=model,
            max_retries=max_retries
        )

        # Initialize prompt loader
        self.prompt_loader = PromptLoader()

        logger.info(
            "Sonnet45Agent initialized",
            model=self.model,
            pm_temperature=self.pm_temperature,
            coder_temperature=self.coder_temperature
        )

    async def plan(
        self,
        patterns: List[Pattern],
        project: ProjectConfig
    ) -> PlanSpec:
        """
        PM Mode: Analyze patterns and create implementation plan.

        This method uses Sonnet 4.5 to act as a Planning Manager,
        analyzing transformation patterns and designing an optimal
        extraction architecture.

        Args:
            patterns: Identified transformation patterns
            project: Project configuration

        Returns:
            Detailed implementation specification

        Raises:
            ValidationError: If plan JSON is invalid
            Exception: If API call fails after retries

        Example:
            >>> plan = await agent.plan(patterns, project_config)
            >>> print(f"Plan includes {len(plan.classes)} classes")
            >>> print(f"Strategy: {plan.strategy}")
        """
        logger.info("Starting PM mode planning", pattern_count=len(patterns))

        # Render PM prompt
        prompt = self.prompt_loader.render_pm_prompt(patterns, project)

        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": "You are an expert software architect. Respond with ONLY valid JSON following the exact schema provided."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Call API
        try:
            response = await self.client.chat_completion_json(
                messages=messages,
                temperature=self.pm_temperature,
                max_tokens=8000
            )

            logger.debug("PM mode API response received", response_length=len(response))

        except Exception as e:
            logger.error("PM mode API call failed", error=str(e))
            raise

        # Parse JSON response
        try:
            # Strip markdown code blocks if present
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]  # Remove ```json
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]  # Remove ```
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]  # Remove trailing ```
            response_clean = response_clean.strip()

            plan_data = json.loads(response_clean)

            # Convert to PlanSpec (validates structure)
            plan = PlanSpec(**plan_data)

            logger.info(
                "PM mode planning completed",
                classes=len(plan.classes),
                dependencies=len(plan.dependencies),
                strategy_length=len(plan.strategy)
            )

            return plan

        except json.JSONDecodeError as e:
            logger.error("PM mode response is not valid JSON", error=str(e), response=response[:500])
            raise ValueError(f"PM mode returned invalid JSON: {e}")

        except ValidationError as e:
            logger.error("PM mode response failed validation", error=str(e))
            raise ValueError(f"PM mode response invalid: {e}")

    async def code(
        self,
        plan: PlanSpec,
        patterns: List[Pattern],
        examples: Optional[List[Dict[str, Any]]] = None,
        validation_errors: Optional[Any] = None
    ) -> GeneratedCode:
        """
        Coder Mode: Generate production code from plan with optional validation feedback.

        This method uses Sonnet 4.5 to act as a Python developer,
        implementing the architecture specified in the PM plan.
        If validation_errors are provided, it will retry generation
        with feedback to fix the issues.

        Args:
            plan: Implementation plan from PM mode
            patterns: Transformation patterns
            examples: Input/output example pairs (extracted from patterns if None)
            validation_errors: Validation result from previous attempt (for retry)

        Returns:
            Generated code artifacts (extractor, models, tests)

        Raises:
            ValueError: If code cannot be parsed or validated
            Exception: If API call fails after retries

        Example:
            >>> # First attempt
            >>> code = await agent.code(plan, patterns, examples)
            >>> # Retry with validation errors
            >>> code = await agent.code(plan, patterns, examples, validation_errors=result)
        """
        logger.info(
            "Starting Coder mode generation",
            classes=len(plan.classes),
            is_retry=validation_errors is not None
        )

        # Extract examples from patterns if not provided
        if examples is None:
            examples = []
            for pattern in patterns:
                for input_val, output_val in pattern.examples:
                    examples.append({
                        "input": input_val,
                        "output": output_val,
                        "pattern": pattern.type
                    })

        # Render Coder prompt (with or without validation errors)
        if validation_errors is not None:
            # Retry prompt with validation errors
            prompt = self.prompt_loader.render_coder_retry_prompt(
                plan,
                patterns,
                examples,
                validation_errors
            )
        else:
            # First attempt prompt
            prompt = self.prompt_loader.render_coder_prompt(plan, patterns, examples)

        # Prepare messages
        messages = [
            {
                "role": "system",
                "content": "You are an expert Python developer. Generate production-ready code following the specification exactly."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Call API
        try:
            response = await self.client.chat_completion(
                messages=messages,
                temperature=self.coder_temperature,
                max_tokens=8000
            )

            logger.debug("Coder mode API response received", response_length=len(response))

        except Exception as e:
            logger.error("Coder mode API call failed", error=str(e))
            raise

        # Parse code response
        try:
            code = self._parse_generated_code(response)

            # Add generation metadata
            code.add_metadata("model", self.model)
            code.add_metadata("plan_classes", len(plan.classes))
            code.add_metadata("pattern_count", len(patterns))
            code.add_metadata("example_count", len(examples))

            logger.info(
                "Coder mode generation completed",
                total_lines=code.total_lines,
                extractor_lines=len(code.extractor_code.splitlines()),
                models_lines=len(code.models_code.splitlines()),
                tests_lines=len(code.tests_code.splitlines())
            )

            return code

        except Exception as e:
            logger.error("Coder mode response parsing failed", error=str(e))
            raise ValueError(f"Coder mode response invalid: {e}")

    async def plan_and_code(
        self,
        patterns: List[Pattern],
        project: ProjectConfig,
        examples: Optional[List[Dict[str, Any]]] = None
    ) -> GeneratedCode:
        """
        End-to-end: PM planning + Coder implementation.

        This method orchestrates the complete dual-agent pipeline:
        1. PM mode analyzes patterns → creates plan
        2. Coder mode takes plan → generates code

        Args:
            patterns: Identified transformation patterns
            project: Project configuration
            examples: Input/output example pairs (optional)

        Returns:
            Generated code artifacts

        Raises:
            Exception: If either PM or Coder mode fails

        Example:
            >>> code = await agent.plan_and_code(patterns, project_config)
            >>> with open("generated/extractor.py", "w") as f:
            ...     f.write(code.extractor_code)
        """
        logger.info(
            "Starting end-to-end code generation",
            pattern_count=len(patterns),
            project=project.project.name
        )

        # Step 1: PM planning
        logger.info("Step 1: PM mode planning")
        plan = await self.plan(patterns, project)

        # Step 2: Coder implementation
        logger.info("Step 2: Coder mode implementation")
        code = await self.code(plan, patterns, examples)

        # Add plan reference to metadata
        code.add_metadata("plan_strategy", plan.strategy)

        logger.info(
            "End-to-end generation completed",
            total_lines=code.total_lines
        )

        return code

    def _parse_generated_code(self, response: str) -> GeneratedCode:
        """
        Parse Coder mode response into structured code artifacts.

        Args:
            response: Raw API response with code blocks

        Returns:
            Structured GeneratedCode object

        Raises:
            ValueError: If code cannot be parsed

        Design Decision: Expect structured response with file markers.
        Falls back to heuristic parsing if markers not found.
        """
        # Look for file markers
        extractor_marker = "# FILE: extractor.py"
        models_marker = "# FILE: models.py"
        tests_marker = "# FILE: test_extractor.py"

        if all(marker in response for marker in [extractor_marker, models_marker, tests_marker]):
            # Structured response - parse by markers
            logger.debug("Parsing structured code response")

            # Find code for each file by looking between markers
            extractor_code = self._extract_between_markers(
                response,
                extractor_marker,
                models_marker
            )
            models_code = self._extract_between_markers(
                response,
                models_marker,
                tests_marker
            )
            tests_code = self._extract_after_marker(response, tests_marker)

        else:
            # Fallback: Try to extract from code blocks
            logger.warning("File markers not found, attempting fallback parsing")

            code_blocks = self._extract_all_code_blocks(response)

            if len(code_blocks) >= 3:
                extractor_code = code_blocks[0]
                models_code = code_blocks[1]
                tests_code = code_blocks[2]
            else:
                raise ValueError(
                    f"Could not parse generated code. Expected 3 code blocks, found {len(code_blocks)}"
                )

        # Validate non-empty
        if not extractor_code or not models_code or not tests_code:
            raise ValueError("One or more code sections are empty")

        return GeneratedCode(
            extractor_code=extractor_code,
            models_code=models_code,
            tests_code=tests_code,
            metadata={}
        )

    def _extract_between_markers(self, response: str, start_marker: str, end_marker: str) -> str:
        """Extract code between two markers."""
        try:
            start_idx = response.index(start_marker) + len(start_marker)
            end_idx = response.index(end_marker)
            section = response[start_idx:end_idx]
            return self._extract_code_block(section)
        except ValueError:
            return ""

    def _extract_after_marker(self, response: str, marker: str) -> str:
        """Extract code after a marker."""
        try:
            start_idx = response.index(marker) + len(marker)
            section = response[start_idx:]
            return self._extract_code_block(section)
        except ValueError:
            return ""

    def _extract_code_block(self, section: str) -> str:
        """Extract Python code from a section."""
        # Remove file marker line and section separators
        lines = section.split('\n')
        code_lines = [
            line for line in lines
            if not line.startswith('# FILE:') and not line.startswith('# ===')
        ]

        # Find code block boundaries
        in_code = False
        code = []

        for line in code_lines:
            if line.strip().startswith('```python'):
                in_code = True
                continue
            elif line.strip().startswith('```'):
                in_code = False
                continue

            # Include line if we're in a code block
            if in_code:
                code.append(line)
            # Or if it looks like Python code (not a comment-only line)
            elif line.strip() and not line.strip().startswith('#'):
                code.append(line)

        return '\n'.join(code).strip()

    def _extract_all_code_blocks(self, response: str) -> List[str]:
        """Extract all Python code blocks from response."""
        blocks = []
        in_block = False
        current_block = []

        for line in response.split('\n'):
            if line.strip().startswith('```python'):
                in_block = True
                current_block = []
                continue
            elif line.strip().startswith('```'):
                if in_block and current_block:
                    blocks.append('\n'.join(current_block).strip())
                in_block = False
                current_block = []
                continue

            if in_block:
                current_block.append(line)

        return blocks
