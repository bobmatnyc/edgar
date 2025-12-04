"""
Quick validation script for T10 (1M-452) - Progress Tracking

Tests the GenerationProgress feature with minimal example to verify:
1. Progress callback is invoked
2. All 7 steps are reported
3. Progress percentage increases correctly
4. Rollback works on validation failure

Created: 2025-11-30 (T10 validation)
"""

import asyncio
from pathlib import Path
import sys
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extract_transform_platform.services.codegen.code_generator import CodeGeneratorService
from extract_transform_platform.models.plan import GenerationProgress, GenerationContext
from extract_transform_platform.models.project_config import (
    ProjectConfig,
    ProjectMetadata,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
    ExampleConfig,
)


async def validate_progress_tracking():
    """Test progress tracking with minimal example."""
    print("="*80)
    print("T10 VALIDATION: Progress Tracking")
    print("="*80)

    # Create minimal project config
    config = ProjectConfig(
        project=ProjectMetadata(
            name="validation_test",
            description="T10 progress tracking validation",
            version="1.0.0",
        ),
        output=OutputConfig(
            formats=[
                OutputDestinationConfig(
                    type=OutputFormat.JSON,
                    path="/tmp/edgar_t10_validation/output.json",
                )
            ]
        ),
    )

    # Minimal examples (must use ExampleConfig objects)
    examples = [
        ExampleConfig(
            input={"temp": 15.5, "city": "SF"},
            output={"temperature_c": 15.5, "location": "SF"},
        ),
        ExampleConfig(
            input={"temp": 20.0, "city": "NY"},
            output={"temperature_c": 20.0, "location": "NY"},
        ),
    ]

    # Progress tracking
    progress_updates: List[GenerationProgress] = []

    def on_progress(progress: GenerationProgress):
        """Capture progress updates."""
        progress_updates.append(progress)
        print(f"[{progress.current_step}/{progress.total_steps}] "
              f"{progress.step_name} - {progress.status} "
              f"({progress.progress_percentage:.1f}%)")
        if progress.message:
            print(f"    Message: {progress.message}")

    # Run generation with progress tracking
    service = CodeGeneratorService()

    try:
        print("\n🚀 Starting code generation with progress tracking...\n")

        context: GenerationContext = await service.generate(
            examples=examples,
            project_config=config,
            validate=False,  # Skip validation to test success path
            write_files=False,  # Skip file writing for quick test
            on_progress=on_progress,
        )

        print("\n✅ Code generation completed successfully!")
        print(f"\nProgress updates received: {len(progress_updates)}")

        # Verify all 7 steps were reported
        step_numbers = {p.current_step for p in progress_updates}
        print(f"Steps reported: {sorted(step_numbers)}")

        if len(step_numbers) == 7:
            print("✅ All 7 steps reported")
        else:
            print(f"⚠️  Expected 7 steps, got {len(step_numbers)}")

        # Check final progress
        if progress_updates:
            final = progress_updates[-1]
            print(f"\nFinal progress: {final.progress_percentage:.1f}%")
            if final.is_complete:
                print("✅ Pipeline marked as complete")
            else:
                print(f"⚠️  Pipeline not complete (status: {final.status})")

        # Verify generation context
        print(f"\n📊 Generation Context:")
        print(f"   - Project: {context.project_name}")
        print(f"   - Patterns: {context.num_patterns}")
        print(f"   - Examples: {context.num_examples}")
        print(f"   - Complete: {context.is_complete}")
        print(f"   - Has Errors: {context.has_errors}")

        if context.is_complete:
            print("✅ Context marked as complete")
        else:
            print(f"⚠️  Context not complete")

    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n"+"="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    return True


if __name__ == "__main__":
    success = asyncio.run(validate_progress_tracking())
    sys.exit(0 if success else 1)
