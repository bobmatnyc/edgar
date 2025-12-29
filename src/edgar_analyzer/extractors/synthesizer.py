"""
Extractor Synthesizer for generating extractors from examples.

Analyzes input/output examples to detect patterns, then renders
Jinja2 templates to produce complete extractor code.

Pipeline:
1. analyze() - Extract patterns from examples using SchemaAnalyzer + ExampleParser
2. synthesize() - Render templates with detected patterns
3. write() - Write generated files to disk

Design Decisions:
- **Reuse Platform Components**: Leverage SchemaAnalyzer and ExampleParser for pattern detection
- **Template-Based Generation**: Use Jinja2 templates for maintainability and consistency
- **Metadata-Driven**: Build comprehensive context from pattern analysis
- **Type Safety**: Infer Pydantic field types from schema analysis
- **Error Recovery**: Graceful degradation when analysis confidence is low

Performance:
- Time Complexity: O(n * m) where n=examples, m=fields per example
- Space Complexity: O(f + p) where f=fields, p=patterns
- Expected: <1s for 3 examples with 50 fields

Usage:
    >>> synthesizer = ExtractorSynthesizer()
    >>> analysis = synthesizer.analyze(
    ...     name="sct_extractor",
    ...     examples=[{"input": {...}, "output": {...}}, ...],
    ...     description="Extract Summary Compensation Tables"
    ... )
    >>> extractor = synthesizer.synthesize(analysis)
    >>> synthesizer.write(extractor, output_dir=Path("src/edgar_analyzer/extractors/sct"))
"""

import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog
from jinja2 import Environment, FileSystemLoader

# Import existing platform components for reuse
from extract_transform_platform.models.patterns import (
    FieldTypeEnum,
    ParsedExamples,
    Pattern,
    PatternType,
)
from extract_transform_platform.services.analysis.example_parser import ExampleParser
from extract_transform_platform.services.analysis.schema_analyzer import SchemaAnalyzer

# Import EDGAR ExampleConfig (temporary until migrated to platform)
from edgar_analyzer.models.project_config import ExampleConfig

logger = structlog.get_logger(__name__)


@dataclass
class PatternAnalysis:
    """Results from analyzing examples.

    Contains all metadata needed to render extractor templates.

    Attributes:
        name: Extractor name (e.g., "sct_extractor")
        domain: Domain slug (e.g., "sct")
        description: Human-readable description
        input_schema: Detected input structure
        output_schema: Detected output structure
        patterns: List of transformation patterns
        confidence: Overall confidence (0.0-1.0)
        examples_count: Number of examples analyzed
        heading_patterns: HTML heading patterns for table detection
        table_validation_rules: Table validation rules
        system_prompt: LLM system prompt
        parsing_rules: LLM parsing instructions
    """

    name: str
    domain: str
    description: str

    # Schemas (as dicts for JSON serialization)
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]

    # Patterns detected
    patterns: List[Dict[str, Any]]

    # Metrics
    confidence: float
    examples_count: int

    # Extraction config
    heading_patterns: List[str] = field(default_factory=list)
    table_validation_rules: Dict[str, Any] = field(default_factory=dict)

    # LLM config
    system_prompt: str = ""
    parsing_rules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)


@dataclass
class GeneratedExtractor:
    """Container for generated extractor code.

    Contains all generated files and metadata.

    Attributes:
        name: Extractor name
        domain: Domain slug
        extractor_code: Main extractor class
        models_code: Pydantic models
        prompts_code: LLM prompts
        tests_code: pytest tests
        init_code: __init__.py
        analysis: PatternAnalysis used for generation
        generated_at: ISO timestamp
    """

    name: str
    domain: str

    # Generated code strings
    extractor_code: str
    models_code: str
    prompts_code: str
    tests_code: str
    init_code: str

    # Metadata
    analysis: PatternAnalysis
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ExtractorSynthesizer:
    """
    Synthesizes extractors from examples using pattern analysis and templates.

    This is the orchestrator for the Meta-Extractor POC Phase 3.
    It coordinates SchemaAnalyzer, ExampleParser, and Jinja2 templates
    to generate complete extractor implementations.

    Code Reuse: 90%+ from platform components
    - SchemaAnalyzer: Schema inference and comparison
    - ExampleParser: Pattern detection
    - Jinja2 templates: Code generation

    Example:
        >>> synthesizer = ExtractorSynthesizer()
        >>> analysis = synthesizer.analyze(
        ...     name="sct_extractor",
        ...     examples=[{"input": {...}, "output": {...}}, ...],
        ...     description="Extract Summary Compensation Tables"
        ... )
        >>> extractor = synthesizer.synthesize(analysis)
        >>> synthesizer.write(extractor, output_dir=Path("src/edgar_analyzer/extractors/sct"))
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize synthesizer with template directory.

        Args:
            templates_dir: Path to Jinja2 templates. Defaults to templates/extractors/
        """
        self.templates_dir = templates_dir or (
            Path(__file__).parent.parent.parent.parent / "templates" / "extractors"
        )

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Initialize platform components for pattern detection
        self.schema_analyzer = SchemaAnalyzer()
        self.example_parser = ExampleParser(self.schema_analyzer)

        logger.info(
            "ExtractorSynthesizer initialized",
            templates_dir=str(self.templates_dir),
        )

    def analyze(
        self,
        name: str,
        examples: List[Dict[str, Any]],
        description: str = "",
        domain: Optional[str] = None,
        heading_patterns: Optional[List[str]] = None,
        table_validation_rules: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        parsing_rules: Optional[List[str]] = None,
    ) -> PatternAnalysis:
        """
        Analyze examples to detect patterns and build extraction config.

        Args:
            name: Extractor name (e.g., "sct_extractor")
            examples: List of {"input": {...}, "output": {...}} dicts
            description: Human-readable description
            domain: Domain slug (defaults to name without "_extractor")
            heading_patterns: HTML heading patterns for table detection
            table_validation_rules: Table validation rules
            system_prompt: Custom LLM system prompt
            parsing_rules: Custom LLM parsing instructions

        Returns:
            PatternAnalysis with detected patterns and schemas

        Raises:
            ValueError: If examples is empty or invalid
        """
        if not examples:
            raise ValueError("examples list cannot be empty")

        domain = domain or name.replace("_extractor", "")

        logger.info(
            "Analyzing examples",
            name=name,
            examples_count=len(examples),
        )

        # Convert examples to ExampleConfig format
        example_configs = []
        for ex in examples:
            if "input" not in ex or "output" not in ex:
                logger.warning("Skipping example missing input/output", example=ex)
                continue

            example_configs.append(
                ExampleConfig(
                    input=ex["input"],
                    output=ex["output"],
                )
            )

        if not example_configs:
            raise ValueError("No valid examples with input/output found")

        # Use platform components for pattern detection (CODE REUSE!)
        parsed: ParsedExamples = self.example_parser.parse_examples(example_configs)

        # Calculate overall confidence
        confidence = self._calculate_confidence(parsed.patterns, len(example_configs))

        # Extract metadata from examples if provided
        heading_patterns = heading_patterns or self._extract_heading_patterns(examples)
        table_validation_rules = table_validation_rules or self._extract_validation_rules(examples)
        system_prompt = system_prompt or self._build_system_prompt(domain, description)
        parsing_rules = parsing_rules or self._extract_parsing_rules(examples)

        # Convert schemas and patterns to serializable dicts
        input_schema_dict = self._schema_to_dict(parsed.input_schema)
        output_schema_dict = self._schema_to_dict(parsed.output_schema)
        patterns_dicts = [self._pattern_to_dict(p) for p in parsed.patterns]

        analysis = PatternAnalysis(
            name=name,
            domain=domain,
            description=description or f"Extract {domain} data",
            input_schema=input_schema_dict,
            output_schema=output_schema_dict,
            patterns=patterns_dicts,
            confidence=confidence,
            examples_count=len(example_configs),
            heading_patterns=heading_patterns,
            table_validation_rules=table_validation_rules,
            system_prompt=system_prompt,
            parsing_rules=parsing_rules,
        )

        logger.info(
            "Analysis complete",
            name=name,
            patterns_count=len(patterns_dicts),
            confidence=confidence,
        )

        return analysis

    def synthesize(self, analysis: PatternAnalysis) -> GeneratedExtractor:
        """
        Generate extractor code from pattern analysis.

        Args:
            analysis: PatternAnalysis from analyze()

        Returns:
            GeneratedExtractor with all code strings
        """
        logger.info("Synthesizing extractor", name=analysis.name)

        # Build template context
        context = self._build_template_context(analysis)

        # Render all templates
        extractor_code = self._render_template("base_extractor.py.j2", context)
        models_code = self._render_template("data_models.py.j2", context)
        prompts_code = self._render_template("prompt_template.j2", context)
        tests_code = self._render_template("test_extractor.py.j2", context)
        init_code = self._render_template("__init__.py.j2", context)

        extractor = GeneratedExtractor(
            name=analysis.name,
            domain=analysis.domain,
            extractor_code=extractor_code,
            models_code=models_code,
            prompts_code=prompts_code,
            tests_code=tests_code,
            init_code=init_code,
            analysis=analysis,
        )

        total_loc = sum(
            len(code.splitlines())
            for code in [extractor_code, models_code, prompts_code, tests_code, init_code]
        )

        logger.info(
            "Synthesis complete",
            name=analysis.name,
            total_loc=total_loc,
        )

        return extractor

    def write(self, extractor: GeneratedExtractor, output_dir: Path) -> List[Path]:
        """
        Write generated extractor to disk.

        Args:
            extractor: GeneratedExtractor from synthesize()
            output_dir: Directory to write files

        Returns:
            List of paths to written files
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        files = [
            (output_dir / "extractor.py", extractor.extractor_code),
            (output_dir / "models.py", extractor.models_code),
            (output_dir / "prompts.py", extractor.prompts_code),
            (output_dir / f"test_{extractor.domain}_extractor.py", extractor.tests_code),
            (output_dir / "__init__.py", extractor.init_code),
        ]

        written_paths = []
        for path, content in files:
            path.write_text(content, encoding="utf-8")
            written_paths.append(path)
            logger.debug("Wrote file", path=str(path), lines=len(content.splitlines()))

        # Format with black and isort if available
        self._format_code(output_dir)

        logger.info(
            "Files written",
            output_dir=str(output_dir),
            file_count=len(written_paths),
        )

        return written_paths

    # ========== Private Methods ==========

    def _schema_to_dict(self, schema) -> Dict[str, Any]:
        """Convert Schema to serializable dict."""
        return {
            "fields": [
                {
                    "path": f.path,
                    "type": f.field_type.value,
                    "required": f.required,
                    "nullable": f.nullable,
                    "nested_level": f.nested_level,
                    "is_array": f.is_array,
                }
                for f in schema.fields
            ],
            "is_nested": schema.is_nested,
            "has_arrays": schema.has_arrays,
        }

    def _pattern_to_dict(self, pattern: Pattern) -> Dict[str, Any]:
        """Convert Pattern to serializable dict."""
        return {
            "type": pattern.type.value,
            "confidence": pattern.confidence,
            "source_path": pattern.source_path,
            "target_path": pattern.target_path,
            "transformation": pattern.transformation,
            "source_type": pattern.source_type.value if pattern.source_type else None,
            "target_type": pattern.target_type.value if pattern.target_type else None,
        }

    def _calculate_confidence(self, patterns: List[Pattern], examples_count: int) -> float:
        """Calculate overall confidence score.

        Args:
            patterns: Detected patterns
            examples_count: Number of examples analyzed

        Returns:
            Overall confidence (0.0-1.0)
        """
        if not patterns:
            return 0.0

        # Average confidence across all patterns
        total_confidence = sum(p.confidence for p in patterns)
        avg_confidence = total_confidence / len(patterns)

        # Penalize if few examples
        example_penalty = 1.0 if examples_count >= 3 else 0.8

        return min(1.0, avg_confidence * example_penalty)

    def _extract_heading_patterns(self, examples: List[Dict[str, Any]]) -> List[str]:
        """Extract HTML heading patterns from examples.

        Args:
            examples: List of examples

        Returns:
            List of regex patterns for heading detection
        """
        patterns = []

        for ex in examples:
            # Check for heading_pattern in metadata
            metadata = ex.get("metadata", {})
            if "heading_pattern" in metadata:
                patterns.append(metadata["heading_pattern"])

        # Return unique patterns or defaults
        unique_patterns = list(set(patterns)) if patterns else []

        return unique_patterns or [
            # Default heading patterns
            "Summary.*Table",
            "Executive Compensation",
        ]

    def _extract_validation_rules(self, examples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract table validation rules from examples.

        Args:
            examples: List of examples

        Returns:
            Validation rules dict
        """
        rules = {
            "required_columns": [],
            "reject_patterns": [],
        }

        for ex in examples:
            metadata = ex.get("metadata", {})
            if "validation_rules" in metadata:
                ex_rules = metadata["validation_rules"]
                if "required_columns" in ex_rules:
                    rules["required_columns"].extend(ex_rules["required_columns"])
                if "reject_patterns" in ex_rules:
                    rules["reject_patterns"].extend(ex_rules["reject_patterns"])

        # Deduplicate
        rules["required_columns"] = list(set(rules["required_columns"]))
        rules["reject_patterns"] = list(set(rules["reject_patterns"]))

        return rules

    def _build_system_prompt(self, domain: str, description: str) -> str:
        """Build LLM system prompt for the domain.

        Args:
            domain: Domain slug
            description: Description

        Returns:
            System prompt string
        """
        return (
            f"You are an expert at extracting structured data from SEC filings. "
            f"{description}. Extract data following the provided schema exactly."
        )

    def _extract_parsing_rules(self, examples: List[Dict[str, Any]]) -> List[str]:
        """Extract parsing rules from example metadata.

        Args:
            examples: List of examples

        Returns:
            List of parsing rule strings
        """
        rules = []

        for ex in examples:
            metadata = ex.get("metadata", {})
            if "parsing_rules" in metadata:
                rules.extend(metadata["parsing_rules"])

        return list(set(rules))  # Deduplicate

    def _build_template_context(self, analysis: PatternAnalysis) -> Dict[str, Any]:
        """Build Jinja2 template context from analysis.

        Args:
            analysis: PatternAnalysis

        Returns:
            Template context dict
        """
        # Infer Pydantic models from output schema
        models = self._infer_pydantic_models(analysis.output_schema)

        # Find main model (first model with is_main_model or first model)
        main_model = next((m for m in models if m.get("is_main_model")), models[0] if models else None)

        # Build context matching template expectations
        context = {
            # Core identifiers
            "extractor_name": self._to_pascal_case(analysis.name),
            "domain": analysis.domain,
            "extractor_description": analysis.description,

            # Data models
            "data_model_import": f"from .models import {main_model['name']}, {main_model['name']}ExtractionResult" if main_model else "",
            "data_model_class": main_model["name"] if main_model else "UnknownData",
            "result_class": f"{main_model['name']}ExtractionResult" if main_model else "UnknownResult",

            # Configuration
            "rate_limit_delay": 0.15,
            "context_chars": 1000,
            "max_html_size": 100000,

            # Pattern analysis results
            "heading_patterns": analysis.heading_patterns,
            "table_validation_rules": analysis.table_validation_rules,

            # LLM configuration
            "llm_temperature": 0.1,
            "llm_max_tokens": 8000,
            "system_prompt": analysis.system_prompt,

            # Models for data_models.py.j2
            "models": models,

            # Tests
            "test_fixtures": self._build_test_fixtures(analysis),
            "test_cases": self._build_test_cases(analysis),

            # Prompt template
            "task_description": analysis.description,
            "task_instructions": f"Extract {analysis.domain} data from the provided HTML.",
            "parsing_rules": self._format_parsing_rules(analysis.parsing_rules),
            "example_input": "<html>...</html>",
            "example_output": self._build_example_output(analysis),
            "example_explanation": "See patterns detected during analysis.",
            "json_schema": self._build_json_schema(models),
            "output_requirements": [
                "Return ONLY valid JSON (no markdown code fences)",
                "Extract ALL relevant data from the input",
                "Use proper JSON syntax: double quotes, lowercase booleans",
            ],
        }

        return context

    def _infer_pydantic_models(self, output_schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Infer Pydantic models from output schema.

        Args:
            output_schema: Output schema dict

        Returns:
            List of model definitions
        """
        models = []
        fields = output_schema.get("fields", [])

        if not fields:
            return []

        # Create main model from top-level fields
        main_model_fields = []
        for field in fields:
            if field["nested_level"] == 0:
                pydantic_field = {
                    "name": field["path"],
                    "type": self._field_type_to_pydantic(field["type"]),
                    "description": f"{field['path']} field",
                    "required": field["required"],
                }
                main_model_fields.append(pydantic_field)

        if main_model_fields:
            models.append({
                "name": "ExtractedData",
                "description": "Main data model",
                "fields": main_model_fields,
                "is_main_model": True,
            })

        return models

    def _field_type_to_pydantic(self, field_type: str) -> str:
        """Convert FieldTypeEnum to Pydantic type hint.

        Args:
            field_type: FieldTypeEnum value

        Returns:
            Pydantic type hint string
        """
        type_mapping = {
            "str": "str",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "date": "date",
            "datetime": "datetime",
            "list": "List[Any]",
            "dict": "Dict[str, Any]",
        }

        return type_mapping.get(field_type, "Any")

    def _to_pascal_case(self, name: str) -> str:
        """Convert snake_case to PascalCase.

        Args:
            name: snake_case name

        Returns:
            PascalCase name
        """
        return "".join(word.capitalize() for word in name.split("_"))

    def _format_parsing_rules(self, rules: List[str]) -> List[Dict[str, str]]:
        """Format parsing rules for template.

        Args:
            rules: List of rule strings

        Returns:
            List of rule dicts
        """
        return [
            {
                "title": f"Rule {i+1}",
                "description": rule,
            }
            for i, rule in enumerate(rules)
        ]

    def _build_example_output(self, analysis: PatternAnalysis) -> Dict[str, Any]:
        """Build example output from patterns.

        Args:
            analysis: PatternAnalysis

        Returns:
            Example output dict
        """
        # Simple example based on output schema
        output = {}
        for field in analysis.output_schema.get("fields", []):
            if field["nested_level"] == 0:
                output[field["path"]] = "example_value"

        return output

    def _build_json_schema(self, models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build JSON schema from models.

        Args:
            models: List of model definitions

        Returns:
            JSON schema dict
        """
        if not models:
            return {}

        main_model = models[0]
        schema = {}

        for field in main_model.get("fields", []):
            schema[field["name"]] = field["type"]

        return schema

    def _build_test_fixtures(self, analysis: PatternAnalysis) -> List[Dict[str, Any]]:
        """Build test fixtures from analysis.

        Args:
            analysis: PatternAnalysis

        Returns:
            List of test fixtures
        """
        return [
            {
                "name": "sample_html",
                "description": "Sample HTML for testing",
                "data": {"html": "<html>...</html>"},
            }
        ]

    def _build_test_cases(self, analysis: PatternAnalysis) -> List[Dict[str, Any]]:
        """Build test cases from analysis.

        Args:
            analysis: PatternAnalysis

        Returns:
            List of test cases
        """
        return [
            {
                "name": "extraction_success",
                "description": "Test successful extraction",
                "fixtures": ["extractor", "mock_openrouter"],
                "expected_success": True,
            }
        ]

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render a single Jinja2 template.

        Args:
            template_name: Template filename
            context: Template context

        Returns:
            Rendered template string
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(
                "Template rendering failed",
                template=template_name,
                error=str(e),
            )
            raise

    def _format_code(self, output_dir: Path) -> None:
        """Format generated code with black and isort.

        Args:
            output_dir: Directory containing generated code
        """
        try:
            subprocess.run(
                ["black", str(output_dir)],
                check=True,
                capture_output=True,
                timeout=30,
            )
            logger.debug("Formatted code with black", output_dir=str(output_dir))
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning("black formatting failed or unavailable", error=str(e))

        try:
            subprocess.run(
                ["isort", str(output_dir)],
                check=True,
                capture_output=True,
                timeout=30,
            )
            logger.debug("Sorted imports with isort", output_dir=str(output_dir))
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning("isort failed or unavailable", error=str(e))
