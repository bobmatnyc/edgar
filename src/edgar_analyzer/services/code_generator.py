"""
Code Generator Service - End-to-End Code Generation Pipeline

This service orchestrates the complete code generation pipeline:
1. Example Parser → Parse examples and extract patterns
2. PM Mode → Analyze patterns and create plan
3. Coder Mode → Generate production code
4. Validator → Validate generated code
5. Writer → Save code to files

Design Decisions:
- **Pipeline Architecture**: Each step is independent and testable
- **Progress Tracking**: Logs and events for monitoring
- **Error Recovery**: Graceful failure handling at each stage
- **File Management**: Safe writes with backup and validation

Usage:
    >>> service = CodeGeneratorService()
    >>> result = await service.generate(
    ...     examples=[{"input": {...}, "output": {...}}],
    ...     project_config=config
    ... )
    >>> print(f"Generated code saved to: {result.output_dir}")
"""

import ast
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from edgar_analyzer.agents.sonnet45_agent import Sonnet45Agent
from edgar_analyzer.models.patterns import ParsedExamples, Pattern
from edgar_analyzer.models.plan import (
    CodeValidationResult,
    GeneratedCode,
    GenerationContext,
)
from edgar_analyzer.models.project_config import ProjectConfig
from edgar_analyzer.services.example_parser import ExampleParser

logger = structlog.get_logger(__name__)


# ============================================================================
# CODE VALIDATION
# ============================================================================


class CodeValidator:
    """
    Validate generated code for quality and correctness.

    Checks:
    - Syntax validity (can it be parsed?)
    - Type hints present
    - Docstrings present
    - Interface implementation
    - Test coverage
    """

    def validate(self, code: GeneratedCode) -> CodeValidationResult:
        """
        Validate all generated code artifacts.

        Args:
            code: Generated code to validate

        Returns:
            Validation result with issues and recommendations
        """
        logger.debug("Validating generated code")

        result = CodeValidationResult(is_valid=True, syntax_valid=True)

        # Check syntax validity
        for name, code_str in [
            ("extractor", code.extractor_code),
            ("models", code.models_code),
            ("tests", code.tests_code),
        ]:
            if not self._check_syntax(code_str):
                result.syntax_valid = False
                result.is_valid = False
                result.add_issue(f"{name}.py has syntax errors")
            else:
                logger.debug(f"{name}.py syntax is valid")

        # Check for type hints
        result.has_type_hints = self._check_type_hints(code.extractor_code)
        if not result.has_type_hints:
            result.add_recommendation("Add type hints to all methods")

        # Check for docstrings
        result.has_docstrings = self._check_docstrings(code.extractor_code)
        if not result.has_docstrings:
            result.add_recommendation("Add docstrings to all public methods")

        # Check for tests
        result.has_tests = "def test_" in code.tests_code
        if not result.has_tests:
            result.add_issue("No test functions found")
            result.is_valid = False

        # Check interface implementation
        result.implements_interface = (
            "IDataExtractor" in code.extractor_code
            and "async def extract" in code.extractor_code
        )
        if not result.implements_interface:
            result.add_issue("Extractor does not implement IDataExtractor interface")
            result.is_valid = False

        logger.info(
            "Code validation completed",
            is_valid=result.is_valid,
            quality_score=result.quality_score,
            issues=len(result.issues),
            recommendations=len(result.recommendations),
        )

        return result

    def _check_syntax(self, code: str) -> bool:
        """Check if code has valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _check_type_hints(self, code: str) -> bool:
        """Check if code includes type hints."""
        try:
            tree = ast.parse(code)
            # Check functions have type annotations
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if at least one function has return annotation
                    if node.returns is not None:
                        return True
            return False
        except:
            return False

    def _check_docstrings(self, code: str) -> bool:
        """Check if code includes docstrings."""
        return '"""' in code or "'''" in code


# ============================================================================
# CODE WRITER
# ============================================================================


class CodeWriter:
    """
    Write generated code to files with safety checks.

    Features:
    - Backup existing files before overwriting
    - Create directory structure
    - Validate before writing
    - Return file paths for reference
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize code writer.

        Args:
            base_dir: Base directory for generated code (default: ./generated)
        """
        self.base_dir = base_dir or Path("./generated")

    def write(
        self, code: GeneratedCode, project_name: str, backup: bool = True
    ) -> Dict[str, Path]:
        """
        Write generated code to files.

        Args:
            code: Generated code artifacts
            project_name: Project name (used for directory)
            backup: Whether to backup existing files

        Returns:
            Dictionary mapping file type to path

        Example:
            >>> paths = writer.write(code, "weather_extractor")
            >>> print(paths["extractor"])  # Path to extractor.py
        """
        # Create project directory
        project_dir = self.base_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Writing generated code", project_dir=str(project_dir))

        paths = {}

        # Write each file
        for name, content in [
            ("extractor", code.extractor_code),
            ("models", code.models_code),
            ("test_extractor", code.tests_code),
        ]:
            file_path = project_dir / f"{name}.py"

            # Backup existing file
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(
                    f".py.bak.{int(datetime.now().timestamp())}"
                )
                file_path.rename(backup_path)
                logger.debug(f"Backed up existing {name}.py", backup=str(backup_path))

            # Write new file
            with open(file_path, "w") as f:
                f.write(content)

            paths[name] = file_path
            logger.debug(f"Wrote {name}.py", path=str(file_path), size=len(content))

        # Write __init__.py
        init_path = project_dir / "__init__.py"
        with open(init_path, "w") as f:
            f.write(f'"""Generated extractor for {project_name}"""\n')
        paths["init"] = init_path

        logger.info(
            "Code writing completed", project_dir=str(project_dir), files=len(paths)
        )

        return paths


# ============================================================================
# CODE GENERATOR SERVICE
# ============================================================================


class CodeGeneratorService:
    """
    End-to-end code generation pipeline orchestrator.

    This service coordinates all steps of the code generation process:
    1. Parse examples → extract patterns
    2. PM mode → create implementation plan
    3. Coder mode → generate code
    4. Validate code → ensure quality
    5. Write files → save to disk

    Example:
        >>> service = CodeGeneratorService()
        >>> result = await service.generate(
        ...     examples=[
        ...         {"input": {"temp": 15.5}, "output": {"temperature_c": 15.5}}
        ...     ],
        ...     project_config=config
        ... )
        >>> print(f"Generated {result.code.total_lines} lines of code")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        output_dir: Optional[Path] = None,
        model: str = "anthropic/claude-sonnet-4.5",
    ):
        """
        Initialize code generator service.

        Args:
            api_key: OpenRouter API key
            output_dir: Output directory for generated code
            model: Model to use for generation
        """
        self.agent = Sonnet45Agent(api_key=api_key, model=model)
        self.parser = ExampleParser()
        self.validator = CodeValidator()
        self.writer = CodeWriter(base_dir=output_dir)

        logger.info(
            "CodeGeneratorService initialized",
            model=model,
            output_dir=str(output_dir or "./generated"),
        )

    async def generate(
        self,
        examples: List[Dict[str, Any]],
        project_config: ProjectConfig,
        validate: bool = True,
        write_files: bool = True,
        max_retries: int = 3,
    ) -> GenerationContext:
        """
        Generate code from examples and configuration with iterative refinement.

        This is the main entry point for the code generation pipeline.
        If validation fails, the system will retry with validation feedback
        to iteratively improve the generated code.

        Args:
            examples: List of input/output example pairs
            project_config: Project configuration
            validate: Whether to validate generated code
            write_files: Whether to write files to disk
            max_retries: Maximum retry attempts for validation failures (default: 3)

        Returns:
            Generation context with plan, code, and metadata

        Raises:
            ValueError: If validation fails after max retries
            Exception: If generation fails

        Example:
            >>> context = await service.generate(
            ...     examples=[{"input": {...}, "output": {...}}],
            ...     project_config=config,
            ...     max_retries=3
            ... )
            >>> if context.is_complete:
            ...     print("Success!")
        """
        start_time = datetime.now()

        logger.info(
            "Starting code generation",
            project=project_config.project.name,
            examples=len(examples),
            max_retries=max_retries,
        )

        # Create generation context
        context = GenerationContext(
            project_name=project_config.project.name,
            num_patterns=0,
            num_examples=len(examples),
        )

        try:
            # Step 1: Parse examples and extract patterns
            logger.info("Step 1: Parsing examples")
            # parse_examples is synchronous, not async
            parsed = self.parser.parse_examples(examples)

            context.num_patterns = len(parsed.patterns)

            logger.info(
                "Examples parsed",
                patterns=len(parsed.patterns),
                input_fields=len(parsed.input_schema.fields),
                output_fields=len(parsed.output_schema.fields),
            )

            # Step 2: PM mode planning
            logger.info("Step 2: PM mode planning")
            plan = await self.agent.plan(parsed.patterns, project_config)

            context.plan = plan

            logger.info(
                "Plan created",
                classes=len(plan.classes),
                dependencies=len(plan.dependencies),
            )

            # Step 3: Coder mode implementation with iterative refinement
            logger.info("Step 3: Coder mode code generation with iterative refinement")

            validation_result = None
            code = None

            for attempt in range(max_retries):
                logger.info(
                    "Code generation attempt",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                )

                # Generate code (passing validation errors from previous attempt if any)
                if attempt == 0:
                    # First attempt - no validation errors yet
                    code = await self.agent.code(plan, parsed.patterns, examples)
                else:
                    # Retry with validation errors from previous attempt
                    code = await self.agent.code(
                        plan,
                        parsed.patterns,
                        examples,
                        validation_errors=validation_result,
                    )

                logger.info(
                    "Code generated", attempt=attempt + 1, total_lines=code.total_lines
                )

                # Validate if enabled
                if validate:
                    logger.info("Validating generated code", attempt=attempt + 1)
                    validation_result = self.validator.validate(code)

                    if validation_result.is_valid:
                        # Success! Code is valid
                        logger.info(
                            "Code generation successful",
                            attempt=attempt + 1,
                            quality_score=validation_result.quality_score,
                        )
                        code.add_metadata("generation_attempts", attempt + 1)
                        code.validation_notes = f"Quality score: {validation_result.quality_score} (attempt {attempt + 1})"
                        break
                    else:
                        # Validation failed
                        logger.warning(
                            "Validation failed",
                            attempt=attempt + 1,
                            issues=len(validation_result.issues),
                            max_retries=max_retries,
                        )

                        if attempt == max_retries - 1:
                            # Final attempt failed
                            error_msg = f"Code validation failed after {max_retries} attempts: {validation_result.issues}"
                            context.add_error(error_msg)
                            logger.error(
                                "Code generation failed after max retries",
                                max_retries=max_retries,
                                final_issues=validation_result.issues,
                            )
                            raise ValueError(error_msg)
                        else:
                            logger.info(
                                "Retrying code generation with validation feedback",
                                attempt=attempt + 1,
                                next_attempt=attempt + 2,
                            )
                else:
                    # Validation disabled, accept code on first attempt
                    logger.info("Validation disabled, accepting generated code")
                    code.add_metadata("generation_attempts", 1)
                    break

            context.generated_code = code

            logger.info(
                "Code validated",
                quality_score=(
                    validation_result.quality_score if validation_result else None
                ),
                issues=len(validation_result.issues) if validation_result else 0,
                recommendations=(
                    len(validation_result.recommendations) if validation_result else 0
                ),
            )

            # Step 5: Write files (if enabled)
            if write_files:
                logger.info("Step 5: Writing files")
                paths = self.writer.write(
                    code, project_config.project.name, backup=True
                )

                code.add_metadata("output_paths", {k: str(v) for k, v in paths.items()})

                logger.info(
                    "Files written",
                    files=len(paths),
                    directory=str(self.writer.base_dir / project_config.project.name),
                )

            # Record completion time
            duration = (datetime.now() - start_time).total_seconds()
            context.generation_duration_seconds = duration

            logger.info(
                "Code generation completed successfully",
                duration_seconds=duration,
                total_lines=code.total_lines,
            )

            return context

        except Exception as e:
            # Record error in context
            context.add_error(str(e))

            # Calculate duration even on failure
            duration = (datetime.now() - start_time).total_seconds()
            context.generation_duration_seconds = duration

            logger.error(
                "Code generation failed",
                error=str(e),
                error_type=type(e).__name__,
                duration_seconds=duration,
            )

            raise

    async def generate_from_parsed(
        self,
        parsed: ParsedExamples,
        project_config: ProjectConfig,
        validate: bool = True,
        write_files: bool = True,
    ) -> GenerationContext:
        """
        Generate code from pre-parsed examples.

        Use this when you already have parsed patterns and want to
        skip the example parsing step.

        Args:
            parsed: Pre-parsed examples and patterns
            project_config: Project configuration
            validate: Whether to validate generated code
            write_files: Whether to write files to disk

        Returns:
            Generation context

        Example:
            >>> parsed = parser.parse_examples(examples)  # Synchronous
            >>> context = await service.generate_from_parsed(parsed, config)
        """
        start_time = datetime.now()

        logger.info(
            "Starting code generation from parsed patterns",
            project=project_config.project.name,
            patterns=len(parsed.patterns),
        )

        context = GenerationContext(
            project_name=project_config.project.name,
            num_patterns=len(parsed.patterns),
            num_examples=parsed.num_examples,
        )

        try:
            # PM mode planning
            plan = await self.agent.plan(parsed.patterns, project_config)
            context.plan = plan

            # Coder mode implementation
            # Pass empty list for examples if not provided
            code = await self.agent.code(plan, parsed.patterns, examples=[])
            context.generated_code = code

            # Validation
            if validate:
                validation_result = self.validator.validate(code)
                if not validation_result.is_valid:
                    raise ValueError(f"Validation failed: {validation_result.issues}")

            # Write files
            if write_files:
                paths = self.writer.write(code, project_config.project.name)
                code.add_metadata("output_paths", {k: str(v) for k, v in paths.items()})

            # Record completion
            duration = (datetime.now() - start_time).total_seconds()
            context.generation_duration_seconds = duration

            logger.info("Generation completed", duration_seconds=duration)

            return context

        except Exception as e:
            context.add_error(str(e))
            duration = (datetime.now() - start_time).total_seconds()
            context.generation_duration_seconds = duration
            logger.error("Generation failed", error=str(e), duration_seconds=duration)
            raise
