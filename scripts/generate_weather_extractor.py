#!/usr/bin/env python3
"""
Weather API Extractor Generation Demo Script

This script demonstrates the complete end-to-end code generation pipeline
for the Weather API extractor project. It serves as both a demo and a
standalone utility for generating production-ready extractors from examples.

Usage:
    python scripts/generate_weather_extractor.py
    python scripts/generate_weather_extractor.py --no-validate
    python scripts/generate_weather_extractor.py --output-dir custom/path

Features:
- Loads Weather API project configuration
- Parses 7 diverse weather examples
- Generates implementation plan with Sonnet 4.5
- Creates production-ready Python code
- Validates code quality
- Writes files to disk
- Reports generation metrics

Success Criteria:
- Generation completes in < 2 minutes
- All constraint checks pass
- Generated code has 0 syntax errors
- Generated tests cover all 7 examples
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from edgar_analyzer.models.project_config import ProjectConfig
from edgar_analyzer.services.code_generator import CodeGeneratorService
from edgar_analyzer.services.example_parser import ExampleParser

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)

logger = structlog.get_logger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================


DEFAULT_PROJECT_PATH = project_root / "projects" / "weather_api"
DEFAULT_OUTPUT_DIR = DEFAULT_PROJECT_PATH / "generated"


# ============================================================================
# GENERATION ORCHESTRATOR
# ============================================================================


class WeatherExtractorGenerator:
    """Orchestrate Weather API extractor generation."""

    def __init__(
        self,
        project_path: Path = DEFAULT_PROJECT_PATH,
        output_dir: Optional[Path] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize generator.

        Args:
            project_path: Path to Weather API project directory
            output_dir: Output directory for generated code
            api_key: OpenRouter API key
        """
        self.project_path = project_path
        self.output_dir = output_dir or (project_path / "generated")
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable not set. "
                "Please set it or pass api_key parameter."
            )

        logger.info(
            "Generator initialized",
            project_path=str(self.project_path),
            output_dir=str(self.output_dir)
        )

    def load_project(self) -> ProjectConfig:
        """Load Weather API project configuration."""
        logger.info("Loading project configuration")

        config_path = self.project_path / "project.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Project configuration not found: {config_path}")

        config = ProjectConfig.from_yaml(config_path)

        logger.info(
            "Project loaded",
            name=config.project.name,
            version=config.project.version,
            examples=len(config.examples),
            data_sources=len(config.data_sources)
        )

        return config

    async def generate(
        self,
        validate: bool = True,
        write_files: bool = True
    ):
        """
        Generate Weather API extractor.

        Args:
            validate: Whether to validate generated code
            write_files: Whether to write files to disk

        Returns:
            Generation context with results
        """
        start_time = datetime.now()

        logger.info("=" * 80)
        logger.info("WEATHER API EXTRACTOR GENERATION")
        logger.info("=" * 80)

        # Step 1: Load project
        logger.info("\n[STEP 1] Loading Weather API project configuration...")
        config = self.load_project()

        # Step 2: Create code generator service
        logger.info("\n[STEP 2] Initializing Code Generator Service...")
        code_generator = CodeGeneratorService(
            api_key=self.api_key,
            output_dir=self.output_dir,
            model="anthropic/claude-sonnet-4.5"
        )

        # Step 3: Generate code
        logger.info("\n[STEP 3] Starting code generation pipeline...")
        logger.info(f"  - Parsing {len(config.examples)} examples")
        logger.info(f"  - PM mode: Creating implementation plan")
        logger.info(f"  - Coder mode: Generating Python code")
        logger.info(f"  - Validation: {'Enabled' if validate else 'Disabled'}")
        logger.info(f"  - Write files: {'Enabled' if write_files else 'Disabled'}")

        try:
            context = await code_generator.generate(
                examples=config.examples,
                project_config=config,
                validate=validate,
                write_files=write_files
            )

            # Calculate metrics
            duration = (datetime.now() - start_time).total_seconds()

            logger.info("\n" + "=" * 80)
            logger.info("GENERATION COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)

            # Report results
            self._report_results(context, duration)

            return context

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            logger.error("\n" + "=" * 80)
            logger.error("GENERATION FAILED")
            logger.error("=" * 80)
            logger.error(f"Error: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Duration: {duration:.2f}s")

            raise

    def _report_results(self, context, duration: float):
        """Report generation results."""
        logger.info(f"\nGeneration Metrics:")
        logger.info(f"  Duration: {duration:.2f}s")
        logger.info(f"  Examples Processed: {context.num_examples}")
        logger.info(f"  Patterns Identified: {context.num_patterns}")

        if context.plan:
            logger.info(f"  Classes Planned: {len(context.plan.classes)}")
            logger.info(f"  Dependencies: {len(context.plan.dependencies)}")

        if context.generated_code:
            logger.info(f"  Total Lines Generated: {context.generated_code.total_lines}")
            logger.info(f"  Extractor Lines: {len(context.generated_code.extractor_code.split(chr(10)))}")
            logger.info(f"  Models Lines: {len(context.generated_code.models_code.split(chr(10)))}")
            logger.info(f"  Tests Lines: {len(context.generated_code.tests_code.split(chr(10)))}")

            # Show file paths
            output_paths = context.generated_code.metadata.get("output_paths", {})
            if output_paths:
                logger.info(f"\nGenerated Files:")
                for file_type, path in output_paths.items():
                    logger.info(f"  {file_type}: {path}")

        logger.info(f"\nNext Steps:")
        logger.info(f"  1. Review generated code in: {self.output_dir}")
        logger.info(f"  2. Run generated tests: pytest {self.output_dir}/test_extractor.py")
        logger.info(f"  3. Integrate with your project")


# ============================================================================
# CLI INTERFACE
# ============================================================================


def main():
    """Main entry point for CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Weather API Extractor from examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with default settings
  python scripts/generate_weather_extractor.py

  # Generate without validation
  python scripts/generate_weather_extractor.py --no-validate

  # Custom output directory
  python scripts/generate_weather_extractor.py --output-dir /tmp/weather

  # Skip file writing (dry run)
  python scripts/generate_weather_extractor.py --no-write

Environment Variables:
  OPENROUTER_API_KEY    OpenRouter API key (required)
        """
    )

    parser.add_argument(
        "--project-path",
        type=Path,
        default=DEFAULT_PROJECT_PATH,
        help="Path to Weather API project directory"
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        help=f"Output directory for generated code (default: {DEFAULT_OUTPUT_DIR})"
    )

    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip code validation"
    )

    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing files (dry run)"
    )

    parser.add_argument(
        "--api-key",
        help="OpenRouter API key (overrides OPENROUTER_API_KEY env var)"
    )

    args = parser.parse_args()

    # Create generator
    try:
        generator = WeatherExtractorGenerator(
            project_path=args.project_path,
            output_dir=args.output_dir,
            api_key=args.api_key
        )

        # Run generation
        asyncio.run(generator.generate(
            validate=not args.no_validate,
            write_files=not args.no_write
        ))

        logger.info("\n✅ Generation completed successfully!")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Generation interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"\n❌ Generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
