#!/usr/bin/env python3
"""
Project YAML Schema Usage Examples

Demonstrates how to use the ProjectConfig schema for:
1. Loading and validating existing configurations
2. Creating new configurations programmatically
3. Running comprehensive validation
4. Serializing to/from YAML

Related to ticket 1M-323: Project YAML Schema
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from edgar_analyzer.models.project_config import (
    AuthConfig,
    AuthType,
    CacheConfig,
    DataSourceConfig,
    DataSourceType,
    ExampleConfig,
    FieldConstraint,
    FieldType,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
    ProjectConfig,
    ProjectMetadata,
    RateLimitConfig,
    RuntimeConfig,
    ValidationConfig,
)


def example_1_load_existing():
    """Example 1: Load and validate existing project.yaml"""
    print("=" * 70)
    print("Example 1: Load Existing Configuration")
    print("=" * 70)

    project_path = Path(__file__).parent.parent / "projects/weather_api/project.yaml"

    try:
        config = ProjectConfig.from_yaml(project_path)

        print(f"✅ Successfully loaded: {project_path}")
        print(f"\nProject Info:")
        print(f"  Name: {config.project.name}")
        print(f"  Version: {config.project.version}")
        print(f"  Description: {config.project.description[:50]}...")
        print(f"\nConfiguration:")
        print(f"  Data Sources: {len(config.data_sources)}")
        print(f"  Examples: {len(config.examples)}")
        print(f"  Output Formats: {len(config.output.formats)}")
        print(f"  Required Fields: {len(config.validation.required_fields)}")

        # Run comprehensive validation
        results = config.validate_comprehensive()
        print(f"\nValidation Results:")
        print(f"  Errors: {len(results['errors'])}")
        print(f"  Warnings: {len(results['warnings'])}")
        print(f"  Recommendations: {len(results['recommendations'])}")

        if results['warnings']:
            print("\n⚠️  Warnings:")
            for warning in results['warnings']:
                print(f"  - {warning}")

    except Exception as e:
        print(f"❌ Failed to load: {e}")
        return False

    print("\n✅ Example 1 Complete\n")
    return True


def example_2_create_minimal():
    """Example 2: Create minimal valid configuration"""
    print("=" * 70)
    print("Example 2: Create Minimal Configuration")
    print("=" * 70)

    config = ProjectConfig(
        project=ProjectMetadata(name="minimal_project"),
        data_sources=[
            DataSourceConfig(
                type=DataSourceType.API,
                name="example_api",
                endpoint="https://api.example.com/data",
            )
        ],
        output=OutputConfig(
            formats=[OutputDestinationConfig(type=OutputFormat.JSON, path="output.json")]
        ),
    )

    print("✅ Created minimal configuration")
    print(f"\nProject: {config.project.name}")
    print(f"Data Source: {config.data_sources[0].name} ({config.data_sources[0].type.value})")
    print(f"Output: {config.output.formats[0].path} ({config.output.formats[0].type.value})")

    # Save to YAML
    output_path = Path("/tmp/minimal_project.yaml")
    config.to_yaml(output_path)
    print(f"\n💾 Saved to: {output_path}")

    # Verify it can be loaded back
    loaded = ProjectConfig.from_yaml(output_path)
    print(f"✅ Successfully loaded back from YAML")
    print(f"   Project name matches: {loaded.project.name == config.project.name}")

    print("\n✅ Example 2 Complete\n")
    return True


def example_3_create_full():
    """Example 3: Create full configuration with all features"""
    print("=" * 70)
    print("Example 3: Create Full Configuration")
    print("=" * 70)

    config = ProjectConfig(
        # Project metadata
        project=ProjectMetadata(
            name="full_featured_project",
            description="Demonstrates all schema features",
            version="1.0.0",
            author="Schema Example",
            tags=["example", "demo", "complete"],
        ),
        # Data source with authentication and caching
        data_sources=[
            DataSourceConfig(
                type=DataSourceType.API,
                name="weather_api",
                endpoint="https://api.openweathermap.org/data/2.5/weather",
                auth=AuthConfig(
                    type=AuthType.API_KEY, key="${OPENWEATHER_API_KEY}", param_name="appid"
                ),
                parameters={"units": "metric"},
                headers={"User-Agent": "SchemaExample/1.0"},
                cache=CacheConfig(enabled=True, ttl=1800, cache_dir="data/cache/example"),
                rate_limit=RateLimitConfig(requests_per_second=0.5, burst_size=3),
                timeout=10,
                max_retries=3,
            )
        ],
        # Examples for transformation learning
        examples=[
            ExampleConfig(
                input={"temp": 15.5, "weather": [{"desc": "rain"}], "name": "London"},
                output={"temperature_c": 15.5, "conditions": "rain", "city": "London"},
                description="Example demonstrating nested field extraction",
            ),
            ExampleConfig(
                input={"temp": 28.0, "weather": [{"desc": "clear"}], "name": "Dubai"},
                output={"temperature_c": 28.0, "conditions": "clear", "city": "Dubai"},
                description="Example demonstrating high temperature",
            ),
        ],
        # Validation rules
        validation=ValidationConfig(
            required_fields=["city", "temperature_c", "conditions"],
            field_types={
                "city": FieldType.STRING,
                "temperature_c": FieldType.FLOAT,
                "conditions": FieldType.STRING,
            },
            constraints={
                "temperature_c": FieldConstraint(min=-60.0, max=60.0),
                "city": FieldConstraint(min_length=2, max_length=100),
            },
            allow_extra_fields=True,
        ),
        # Multiple output formats
        output=OutputConfig(
            formats=[
                OutputDestinationConfig(
                    type=OutputFormat.CSV,
                    path="output/data.csv",
                    include_timestamp=False,
                    options={"delimiter": ",", "quoting": "minimal"},
                ),
                OutputDestinationConfig(
                    type=OutputFormat.JSON,
                    path="output/data.json",
                    pretty_print=True,
                    include_timestamp=False,
                ),
            ]
        ),
        # Runtime configuration
        runtime=RuntimeConfig(
            log_level="INFO",
            parallel=False,
            max_workers=1,
            error_strategy="continue",
            checkpoint_enabled=False,
        ),
    )

    print("✅ Created full configuration")
    print(f"\nProject: {config.project.name} v{config.project.version}")
    print(f"Tags: {', '.join(config.project.tags)}")
    print(f"\nData Sources: {len(config.data_sources)}")
    for source in config.data_sources:
        print(f"  - {source.name} ({source.type.value})")
        print(f"    Auth: {source.auth.type.value}")
        print(f"    Cache: TTL={source.cache.ttl}s")
        if source.rate_limit:
            print(f"    Rate Limit: {source.rate_limit.requests_per_second} req/s")

    print(f"\nExamples: {len(config.examples)}")
    for i, example in enumerate(config.examples, 1):
        print(f"  {i}. {example.description}")

    print(f"\nValidation:")
    print(f"  Required Fields: {', '.join(config.validation.required_fields)}")
    print(f"  Field Types: {len(config.validation.field_types)}")
    print(f"  Constraints: {len(config.validation.constraints)}")

    print(f"\nOutput Formats: {len(config.output.formats)}")
    for fmt in config.output.formats:
        print(f"  - {fmt.type.value}: {fmt.path}")

    # Validate
    results = config.validate_comprehensive()
    print(f"\nValidation: ✅ {len(results['errors'])} errors, {len(results['warnings'])} warnings")

    # Save to YAML
    output_path = Path("/tmp/full_project.yaml")
    config.to_yaml(output_path)
    print(f"\n💾 Saved to: {output_path}")

    print("\n✅ Example 3 Complete\n")
    return True


def example_4_validation():
    """Example 4: Demonstrate validation errors"""
    print("=" * 70)
    print("Example 4: Validation Examples")
    print("=" * 70)

    # Example 4a: Invalid project name
    print("\n4a. Testing invalid project name (with spaces)...")
    try:
        config = ProjectConfig(
            project=ProjectMetadata(name="invalid project name"),  # Spaces not allowed
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API, name="api", endpoint="https://api.example.com"
                )
            ],
            output=OutputConfig(
                formats=[OutputDestinationConfig(type=OutputFormat.JSON, path="output.json")]
            ),
        )
        print("❌ Should have raised ValidationError")
    except Exception as e:
        print(f"✅ Caught expected error: {type(e).__name__}")
        print(f"   Message: {str(e)[:100]}...")

    # Example 4b: Missing endpoint for API source
    print("\n4b. Testing API source without endpoint...")
    try:
        config = ProjectConfig(
            project=ProjectMetadata(name="test"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API,
                    name="api",
                    # Missing endpoint
                )
            ],
            output=OutputConfig(
                formats=[OutputDestinationConfig(type=OutputFormat.JSON, path="output.json")]
            ),
        )
        print("❌ Should have raised ValidationError")
    except Exception as e:
        print(f"✅ Caught expected error: {type(e).__name__}")
        print(f"   Message: {str(e)[:100]}...")

    # Example 4c: No output formats
    print("\n4c. Testing empty output formats...")
    try:
        config = ProjectConfig(
            project=ProjectMetadata(name="test"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API, name="api", endpoint="https://api.example.com"
                )
            ],
            output=OutputConfig(formats=[]),  # Empty list not allowed
        )
        print("❌ Should have raised ValidationError")
    except Exception as e:
        print(f"✅ Caught expected error: {type(e).__name__}")
        print(f"   Message: {str(e)[:100]}...")

    # Example 4d: Duplicate source names
    print("\n4d. Testing duplicate source names...")
    try:
        config = ProjectConfig(
            project=ProjectMetadata(name="test"),
            data_sources=[
                DataSourceConfig(
                    type=DataSourceType.API, name="api1", endpoint="https://api1.example.com"
                ),
                DataSourceConfig(
                    type=DataSourceType.API, name="api1", endpoint="https://api2.example.com"
                ),  # Duplicate name
            ],
            output=OutputConfig(
                formats=[OutputDestinationConfig(type=OutputFormat.JSON, path="output.json")]
            ),
        )
        print("❌ Should have raised ValidationError")
    except Exception as e:
        print(f"✅ Caught expected error: {type(e).__name__}")
        print(f"   Message: {str(e)[:100]}...")

    print("\n✅ Example 4 Complete\n")
    return True


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("PROJECT YAML SCHEMA USAGE EXAMPLES")
    print("=" * 70 + "\n")

    examples = [
        example_1_load_existing,
        example_2_create_minimal,
        example_3_create_full,
        example_4_validation,
    ]

    success_count = 0
    for example_func in examples:
        try:
            if example_func():
                success_count += 1
        except Exception as e:
            print(f"❌ Example failed: {e}")
            import traceback

            traceback.print_exc()

    print("=" * 70)
    print(f"SUMMARY: {success_count}/{len(examples)} examples completed successfully")
    print("=" * 70)

    return success_count == len(examples)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
