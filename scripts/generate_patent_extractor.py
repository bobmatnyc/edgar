#!/usr/bin/env python3
"""
Generate Patent Filing Extractor using MetaExtractor.

This script demonstrates the end-to-end meta-extractor pipeline:
1. Load patent filing examples
2. Analyze patterns with Synthesizer
3. Generate extractor code
4. Validate and deploy
5. Register with ExtractorRegistry

Usage:
    python scripts/generate_patent_extractor.py
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import structlog
from edgar_analyzer.extractors.meta_extractor import MetaExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger(__name__)


def main():
    """Generate patent extractor from examples."""
    logger.info("Starting patent extractor generation")

    # Initialize MetaExtractor
    meta = MetaExtractor()

    # Examples directory
    examples_dir = Path(__file__).parent.parent / "examples" / "patent_filings"

    if not examples_dir.exists():
        logger.error("Examples directory does not exist", path=str(examples_dir))
        sys.exit(1)

    # Verify examples exist
    example_files = list(examples_dir.glob("*.json"))
    logger.info(
        "Found example files",
        count=len(example_files),
        files=[f.name for f in example_files],
    )

    if len(example_files) < 3:
        logger.error("Need at least 3 examples", found=len(example_files))
        sys.exit(1)

    # Create extractor
    logger.info("Creating patent extractor", examples_dir=str(examples_dir))

    result = meta.create(
        name="patent_extractor",
        examples_dir=examples_dir,
        description="Extract patent filing information from Google Patents API responses",
        domain="patent",
        auto_register=True,
        skip_validation=False,
    )

    # Report results
    logger.info(
        "Extractor creation complete",
        status=result.status,
        total_time=f"{result.total_time_seconds:.2f}s",
    )

    if result.status == "success":
        logger.info(
            "✅ SUCCESS - Patent extractor created!",
            extractor_path=str(result.deployment.extractor_path),
            registered=result.deployment.registered,
            registry_name=result.deployment.registry_name,
            files_created=len(result.files_created),
        )

        print("\n" + "=" * 70)
        print("✅ PATENT EXTRACTOR GENERATED SUCCESSFULLY")
        print("=" * 70)
        print(f"\nExtractor Path: {result.deployment.extractor_path}")
        print(f"Registry Name: {result.deployment.registry_name}")
        print(f"Files Created: {len(result.files_created)}")
        print(f"Total Time: {result.total_time_seconds:.2f}s")

        if result.analysis:
            print(f"\nAnalysis:")
            print(f"  - Confidence: {result.analysis.confidence:.1%}")
            print(f"  - Patterns: {len(result.analysis.patterns)}")
            print(f"  - Examples: {result.analysis.examples_count}")

        if result.validation and result.validation.warnings:
            print(f"\nValidation Warnings ({len(result.validation.warnings)}):")
            for warning in result.validation.warnings:
                print(f"  - {warning}")

        print("\n" + "=" * 70)

    elif result.status == "validation_failed":
        logger.error(
            "❌ VALIDATION FAILED",
            errors=result.validation.errors if result.validation else [],
            warnings=result.validation.warnings if result.validation else [],
        )

        print("\n" + "=" * 70)
        print("❌ VALIDATION FAILED")
        print("=" * 70)

        if result.validation:
            print(f"\nErrors ({len(result.validation.errors)}):")
            for error in result.validation.errors:
                print(f"  - {error}")

            if result.validation.warnings:
                print(f"\nWarnings ({len(result.validation.warnings)}):")
                for warning in result.validation.warnings:
                    print(f"  - {warning}")

        sys.exit(1)

    elif result.status == "deployment_failed":
        logger.error(
            "❌ DEPLOYMENT FAILED",
            error=result.deployment.error_message if result.deployment else None,
        )

        print("\n" + "=" * 70)
        print("❌ DEPLOYMENT FAILED")
        print("=" * 70)
        print(f"\nError: {result.deployment.error_message}")
        sys.exit(1)

    else:
        logger.error(
            "❌ CREATION FAILED",
            status=result.status,
            error=result.error_message,
            stage=result.error_stage,
        )

        print("\n" + "=" * 70)
        print("❌ EXTRACTOR CREATION FAILED")
        print("=" * 70)
        print(f"\nStatus: {result.status}")
        print(f"Stage: {result.error_stage}")
        print(f"Error: {result.error_message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
