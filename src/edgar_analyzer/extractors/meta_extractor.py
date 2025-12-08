"""
MetaExtractor - End-to-end orchestrator for extractor generation.

Coordinates the full pipeline:
1. Load and validate examples
2. Analyze patterns with Synthesizer
3. Generate code from templates
4. Validate generated code
5. Deploy and register extractor

Example:
    >>> meta = MetaExtractor()
    >>> result = meta.create(
    ...     name="sct_extractor",
    ...     examples_dir=Path("examples/sct/"),
    ...     description="Extract Summary Compensation Tables"
    ... )
    >>> print(result.status)  # "success"
    >>> print(result.extractor_path)  # Path to deployed extractor
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import ast
import json
import time

import structlog

from edgar_analyzer.extractors.synthesizer import (
    ExtractorSynthesizer,
    PatternAnalysis,
    GeneratedExtractor,
)
from edgar_analyzer.extractors.registry import ExtractorRegistry

logger = structlog.get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of code validation."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Validation details
    syntax_valid: bool = False
    interface_valid: bool = False
    imports_valid: bool = False
    tests_valid: bool = False


@dataclass
class DeploymentResult:
    """Result of extractor deployment."""

    success: bool
    extractor_path: Path
    registered: bool = False
    registry_name: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class CreateResult:
    """Full result of extractor creation."""

    status: str  # "success", "validation_failed", "deployment_failed", "error"
    name: str
    domain: str

    # Results from each stage
    analysis: Optional[PatternAnalysis] = None
    extractor: Optional[GeneratedExtractor] = None
    validation: Optional[ValidationResult] = None
    deployment: Optional[DeploymentResult] = None

    # Metrics
    total_time_seconds: float = 0.0
    files_created: List[Path] = field(default_factory=list)

    # Error info
    error_message: Optional[str] = None
    error_stage: Optional[str] = None


class MetaExtractor:
    """
    End-to-end orchestrator for generating extractors from examples.

    Coordinates: Synthesizer → Validation → Deployment → Registration

    Example:
        >>> meta = MetaExtractor()
        >>> result = meta.create(
        ...     name="sct_extractor",
        ...     examples_dir=Path("examples/sct/"),
        ...     description="Extract Summary Compensation Tables"
        ... )
        >>> if result.status == "success":
        ...     print(f"Created extractor at {result.deployment.extractor_path}")
        ...     print(f"Registered as: {result.deployment.registry_name}")
    """

    def __init__(
        self,
        synthesizer: Optional[ExtractorSynthesizer] = None,
        registry: Optional[ExtractorRegistry] = None,
        output_base: Optional[Path] = None,
    ):
        """
        Initialize MetaExtractor.

        Args:
            synthesizer: ExtractorSynthesizer instance (creates default if None)
            registry: ExtractorRegistry instance (creates default if None)
            output_base: Base directory for generated extractors.
                        Defaults to src/edgar_analyzer/extractors/
        """
        self.synthesizer = synthesizer or ExtractorSynthesizer()
        self.registry = registry or ExtractorRegistry()
        self.output_base = output_base or Path(__file__).parent

        logger.info(
            "MetaExtractor initialized",
            output_base=str(self.output_base),
        )

    def create(
        self,
        name: str,
        examples: Optional[List[Dict[str, Any]]] = None,
        examples_dir: Optional[Path] = None,
        description: str = "",
        domain: Optional[str] = None,
        auto_register: bool = True,
        skip_validation: bool = False,
    ) -> CreateResult:
        """
        Create a new extractor from examples (end-to-end pipeline).

        Args:
            name: Extractor name (e.g., "sct_extractor")
            examples: List of example dicts OR
            examples_dir: Path to directory with example JSON files
            description: Human-readable description
            domain: Domain slug (defaults to name without "_extractor")
            auto_register: Register with ExtractorRegistry after deployment
            skip_validation: Skip validation step (not recommended)

        Returns:
            CreateResult with status and all stage results

        Raises:
            ValueError: If neither examples nor examples_dir provided
        """
        start_time = time.time()

        domain = domain or name.replace("_extractor", "")

        logger.info(
            "Starting extractor creation",
            name=name,
            domain=domain,
        )

        try:
            # Step 1: Load examples
            if examples is None and examples_dir is None:
                raise ValueError("Must provide either 'examples' or 'examples_dir'")

            if examples is None:
                examples = self._load_examples(examples_dir)

            if not examples:
                raise ValueError("No examples provided or found")

            logger.info(
                "Examples loaded",
                count=len(examples),
                source="provided" if examples_dir is None else str(examples_dir),
            )

            # Step 2: Analyze
            logger.info("Starting pattern analysis", name=name)
            analysis = self.synthesizer.analyze(
                name=name,
                examples=examples,
                description=description,
                domain=domain,
            )

            logger.info(
                "Pattern analysis complete",
                patterns_detected=len(analysis.patterns),
                confidence=analysis.confidence,
            )

            # Step 3: Synthesize
            logger.info("Starting code synthesis", name=name)
            extractor = self.synthesizer.synthesize(analysis)

            logger.info(
                "Code synthesis complete",
                extractor_lines=len(extractor.extractor_code.split("\n")),
                tests_lines=len(extractor.tests_code.split("\n")),
            )

            # Step 4: Validate (unless skipped)
            validation = None
            if not skip_validation:
                logger.info("Starting validation", name=name)
                validation = self.validate(extractor)

                if not validation.valid:
                    logger.warning(
                        "Validation failed",
                        errors=validation.errors,
                        warnings=validation.warnings,
                    )

                    return CreateResult(
                        status="validation_failed",
                        name=name,
                        domain=domain,
                        analysis=analysis,
                        extractor=extractor,
                        validation=validation,
                        total_time_seconds=time.time() - start_time,
                        error_message=f"Validation errors: {'; '.join(validation.errors)}",
                        error_stage="validation",
                    )

                logger.info(
                    "Validation passed",
                    warnings_count=len(validation.warnings),
                )
            else:
                logger.warning("Validation skipped (not recommended)")

            # Step 5: Deploy
            logger.info("Starting deployment", name=name)
            deployment = self.deploy(extractor, auto_register=auto_register)

            if not deployment.success:
                logger.error(
                    "Deployment failed",
                    error=deployment.error_message,
                )

                return CreateResult(
                    status="deployment_failed",
                    name=name,
                    domain=domain,
                    analysis=analysis,
                    extractor=extractor,
                    validation=validation,
                    deployment=deployment,
                    total_time_seconds=time.time() - start_time,
                    error_message=deployment.error_message,
                    error_stage="deployment",
                )

            # Success!
            total_time = time.time() - start_time

            files_created = []
            if deployment.extractor_path.is_dir():
                files_created = list(deployment.extractor_path.glob("*.py"))
            elif deployment.extractor_path.exists():
                files_created = [deployment.extractor_path]

            logger.info(
                "Extractor creation successful",
                name=name,
                domain=domain,
                total_time_seconds=total_time,
                files_created=len(files_created),
                registered=deployment.registered,
            )

            return CreateResult(
                status="success",
                name=name,
                domain=domain,
                analysis=analysis,
                extractor=extractor,
                validation=validation,
                deployment=deployment,
                total_time_seconds=total_time,
                files_created=files_created,
            )

        except Exception as e:
            logger.error(
                "Extractor creation failed",
                name=name,
                error=str(e),
                error_type=type(e).__name__,
            )

            return CreateResult(
                status="error",
                name=name,
                domain=domain,
                total_time_seconds=time.time() - start_time,
                error_message=str(e),
                error_stage="exception",
            )

    def validate(self, extractor: GeneratedExtractor) -> ValidationResult:
        """
        Validate generated extractor code.

        Checks:
        1. Syntax (AST parse)
        2. Interface (IDataExtractor inheritance)
        3. Imports (all imports resolve)
        4. Tests (test file is valid)

        Args:
            extractor: GeneratedExtractor from synthesizer

        Returns:
            ValidationResult with details
        """
        errors = []
        warnings = []

        logger.debug("Starting validation", extractor=extractor.name)

        # 1. Syntax validation
        syntax_valid = self._validate_syntax(extractor.extractor_code, errors)

        # 2. Interface validation
        interface_valid = self._validate_interface(
            extractor.extractor_code, errors, warnings
        )

        # 3. Import validation
        imports_valid = self._validate_imports(
            extractor.extractor_code, errors, warnings
        )

        # 4. Tests validation
        tests_valid = self._validate_syntax(extractor.tests_code, errors)

        valid = syntax_valid and interface_valid and len(errors) == 0

        logger.debug(
            "Validation complete",
            valid=valid,
            errors_count=len(errors),
            warnings_count=len(warnings),
        )

        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            syntax_valid=syntax_valid,
            interface_valid=interface_valid,
            imports_valid=imports_valid,
            tests_valid=tests_valid,
        )

    def deploy(
        self,
        extractor: GeneratedExtractor,
        output_dir: Optional[Path] = None,
        auto_register: bool = True,
    ) -> DeploymentResult:
        """
        Deploy generated extractor to filesystem and registry.

        Args:
            extractor: GeneratedExtractor from synthesizer
            output_dir: Target directory (defaults to output_base/domain/)
            auto_register: Register with ExtractorRegistry

        Returns:
            DeploymentResult with paths and registration status
        """
        output_dir = output_dir or self.output_base / extractor.domain

        logger.debug(
            "Starting deployment",
            extractor=extractor.name,
            output_dir=str(output_dir),
            auto_register=auto_register,
        )

        try:
            # Write files
            written_paths = self.synthesizer.write(extractor, output_dir)

            logger.info(
                "Files written",
                count=len(written_paths),
                paths=[str(p) for p in written_paths],
            )

            # Register if requested
            registered = False
            registry_name = None

            if auto_register:
                # Convert name to class name: sct_extractor → SctExtractor
                class_name = (
                    "".join(word.capitalize() for word in extractor.name.split("_"))
                    + "Extractor"
                )

                class_path = f"edgar_analyzer.extractors.{extractor.domain}.extractor.{class_name}"

                logger.debug(
                    "Registering extractor",
                    name=extractor.name,
                    class_path=class_path,
                )

                self.registry.register(
                    name=extractor.name,
                    class_path=class_path,
                    version="1.0.0",
                    description=extractor.analysis.description,
                    domain=extractor.domain,
                    confidence=extractor.analysis.confidence,
                    examples_count=extractor.analysis.examples_count,
                    tags=[extractor.domain, "generated", "meta-extractor"],
                )

                registered = True
                registry_name = extractor.name

                # Verify dynamic import works
                try:
                    self.registry.get(extractor.name)
                    logger.info(
                        "Verified dynamic import successful",
                        name=extractor.name,
                    )
                except ImportError as e:
                    logger.warning(
                        "Dynamic import verification failed",
                        name=extractor.name,
                        error=str(e),
                    )
                    # Don't fail deployment, just warn

            return DeploymentResult(
                success=True,
                extractor_path=output_dir,
                registered=registered,
                registry_name=registry_name,
            )

        except Exception as e:
            logger.error(
                "Deployment failed",
                extractor=extractor.name,
                error=str(e),
                error_type=type(e).__name__,
            )

            return DeploymentResult(
                success=False,
                extractor_path=output_dir,
                error_message=f"{type(e).__name__}: {str(e)}",
            )

    # ========== Private Methods ==========

    def _load_examples(self, examples_dir: Path) -> List[Dict[str, Any]]:
        """
        Load examples from directory.

        Args:
            examples_dir: Directory containing JSON example files

        Returns:
            List of example dictionaries

        Raises:
            ValueError: If directory doesn't exist or contains invalid JSON
        """
        if not examples_dir.exists():
            raise ValueError(f"Examples directory does not exist: {examples_dir}")

        if not examples_dir.is_dir():
            raise ValueError(f"Examples path is not a directory: {examples_dir}")

        examples = []
        json_files = sorted(examples_dir.glob("*.json"))

        if not json_files:
            raise ValueError(f"No JSON files found in {examples_dir}")

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    example = json.load(f)
                    examples.append(example)

                logger.debug(
                    "Loaded example",
                    file=json_file.name,
                    keys=list(example.keys()) if isinstance(example, dict) else None,
                )

            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {json_file}: {e}")
            except Exception as e:
                raise ValueError(f"Error reading {json_file}: {e}")

        logger.info(
            "Examples loaded successfully",
            count=len(examples),
            directory=str(examples_dir),
        )

        return examples

    def _validate_syntax(self, code: str, errors: List[str]) -> bool:
        """
        Validate Python syntax using AST.

        Args:
            code: Python source code
            errors: List to append errors to

        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            ast.parse(code)
            logger.debug("Syntax validation passed")
            return True
        except SyntaxError as e:
            error_msg: str = f"Syntax error at line {e.lineno}: {e.msg}"
            errors.append(error_msg)
            logger.warning("Syntax validation failed", error=error_msg)
            return False
        except Exception as e:
            error_msg: str = f"Syntax validation error: {type(e).__name__}: {str(e)}"
            errors.append(error_msg)
            logger.warning("Syntax validation failed", error=error_msg)
            return False

    def _validate_interface(
        self, code: str, errors: List[str], warnings: List[str]
    ) -> bool:
        """
        Check for IDataExtractor interface compliance.

        Args:
            code: Python source code
            errors: List to append errors to
            warnings: List to append warnings to

        Returns:
            True if interface is valid, False otherwise
        """
        # Check for IDataExtractor inheritance
        if "IDataExtractor" not in code:
            warnings.append("Class does not inherit from IDataExtractor")

        # Check for required extract method
        if "async def extract" not in code and "def extract" not in code:
            errors.append("Missing required 'extract' method")
            logger.warning("Interface validation failed: missing extract method")
            return False

        # Warn if extract is not async (best practice)
        if "async def extract" not in code:
            warnings.append("Extract method should be async (best practice)")

        logger.debug("Interface validation passed")
        return True

    def _validate_imports(
        self, code: str, errors: List[str], warnings: List[str]
    ) -> bool:
        """
        Validate imports are reasonable and safe.

        Args:
            code: Python source code
            errors: List to append errors to
            warnings: List to append warnings to

        Returns:
            True if imports are valid, False otherwise
        """
        # Potentially unsafe imports to warn about
        unsafe_modules: set[str] = {"os", "subprocess", "sys", "eval", "exec", "__import__"}

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Check for unsafe imports
                        module_base = alias.name.split(".")[0]
                        if module_base in unsafe_modules:
                            warnings.append(
                                f"Potentially unsafe import: {alias.name}"
                            )

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_base = node.module.split(".")[0]
                        if module_base in unsafe_modules:
                            warnings.append(
                                f"Potentially unsafe import from: {node.module}"
                            )

            logger.debug("Import validation passed")
            return True

        except Exception as e:
            error_msg = f"Import validation failed: {type(e).__name__}: {str(e)}"
            errors.append(error_msg)
            logger.warning("Import validation failed", error=error_msg)
            return False
