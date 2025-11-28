#!/usr/bin/env python3
"""
Example Parser Demo - Weather API Example

This script demonstrates the Example Parser system for analyzing input/output
pairs and generating transformation patterns for Sonnet 4.5.

Usage:
    python examples/example_parser_demo.py
"""

from edgar_analyzer.models.project_config import ExampleConfig
from edgar_analyzer.services.example_parser import ExampleParser
from edgar_analyzer.services.prompt_generator import PromptGenerator
from edgar_analyzer.services.schema_analyzer import SchemaAnalyzer


def main():
    """Run Example Parser demo."""
    print("=" * 80)
    print("Example Parser Demo - Weather API Transformation")
    print("=" * 80)
    print()

    # Step 1: Define example input/output pairs
    print("Step 1: Defining example input/output pairs...")
    examples = [
        ExampleConfig(
            input={
                "coord": {"lon": -0.13, "lat": 51.51},
                "weather": [
                    {
                        "id": 300,
                        "main": "Drizzle",
                        "description": "light intensity drizzle",
                        "icon": "09d"
                    }
                ],
                "main": {
                    "temp": 15.5,
                    "feels_like": 14.2,
                    "temp_min": 14,
                    "temp_max": 17,
                    "pressure": 1012,
                    "humidity": 82
                },
                "name": "London"
            },
            output={
                "city": "London",
                "temperature_c": 15.5,
                "humidity_percent": 82,
                "conditions": "light intensity drizzle"
            },
            description="London weather with drizzle"
        ),
        ExampleConfig(
            input={
                "coord": {"lon": 139.69, "lat": 35.69},
                "weather": [
                    {
                        "id": 800,
                        "main": "Clear",
                        "description": "clear sky",
                        "icon": "01d"
                    }
                ],
                "main": {
                    "temp": 22.3,
                    "feels_like": 21.8,
                    "temp_min": 21,
                    "temp_max": 24,
                    "pressure": 1015,
                    "humidity": 65
                },
                "name": "Tokyo"
            },
            output={
                "city": "Tokyo",
                "temperature_c": 22.3,
                "humidity_percent": 65,
                "conditions": "clear sky"
            },
            description="Tokyo weather with clear skies"
        ),
        ExampleConfig(
            input={
                "coord": {"lon": -74.01, "lat": 40.71},
                "weather": [
                    {
                        "id": 500,
                        "main": "Rain",
                        "description": "light rain",
                        "icon": "10d"
                    }
                ],
                "main": {
                    "temp": 18.0,
                    "feels_like": 17.5,
                    "temp_min": 16,
                    "temp_max": 20,
                    "pressure": 1010,
                    "humidity": 75
                },
                "name": "New York"
            },
            output={
                "city": "New York",
                "temperature_c": 18.0,
                "humidity_percent": 75,
                "conditions": "light rain"
            },
            description="New York weather with light rain"
        )
    ]
    print(f"✓ Defined {len(examples)} example pairs")
    print()

    # Step 2: Parse examples and identify patterns
    print("Step 2: Parsing examples and identifying transformation patterns...")
    schema_analyzer = SchemaAnalyzer()
    parser = ExampleParser(schema_analyzer)
    parsed = parser.parse_examples(examples)

    print(f"✓ Analyzed {parsed.num_examples} examples")
    print(f"✓ Identified {len(parsed.patterns)} transformation patterns")
    print(f"  - High confidence patterns: {len(parsed.high_confidence_patterns)}")
    print(f"  - Medium confidence patterns: {len(parsed.medium_confidence_patterns)}")
    print(f"  - Low confidence patterns: {len(parsed.low_confidence_patterns)}")
    print()

    # Step 3: Display schema information
    print("Step 3: Schema Analysis")
    print("-" * 80)
    print("Input Schema:")
    print(f"  - Total fields: {len(parsed.input_schema.fields)}")
    print(f"  - Nested structure: {parsed.input_schema.is_nested}")
    print(f"  - Contains arrays: {parsed.input_schema.has_arrays}")
    print()
    print("Output Schema:")
    print(f"  - Total fields: {len(parsed.output_schema.fields)}")
    print(f"  - Nested structure: {parsed.output_schema.is_nested}")
    print(f"  - Contains arrays: {parsed.output_schema.has_arrays}")
    print()

    # Step 4: Display identified patterns
    print("Step 4: Identified Transformation Patterns")
    print("-" * 80)
    for i, pattern in enumerate(parsed.high_confidence_patterns, 1):
        print(f"\nPattern {i}: {pattern.target_path}")
        print(f"  Type: {pattern.type.value}")
        print(f"  Confidence: {pattern.confidence * 100:.0f}%")
        print(f"  Source: {pattern.source_path}")
        print(f"  Transformation: {pattern.transformation}")
        if pattern.examples:
            print(f"  Examples:")
            for inp, out in pattern.examples[:2]:  # Show first 2
                print(f"    {inp} → {out}")
    print()

    # Step 5: Generate Sonnet 4.5 prompt
    print("Step 5: Generating Sonnet 4.5 Prompt...")
    generator = PromptGenerator()
    prompt = generator.generate_prompt(parsed, project_name="weather_api")

    print(f"✓ Generated prompt with {len(prompt.sections)} sections")
    print()

    # Step 6: Save prompt to file
    output_file = "examples/weather_api_prompt.md"
    with open(output_file, "w") as f:
        f.write(prompt.to_markdown())

    print(f"✓ Prompt saved to: {output_file}")
    print()

    # Step 7: Display prompt preview
    print("Step 7: Prompt Preview (first 1500 characters)")
    print("=" * 80)
    markdown = prompt.to_markdown()
    print(markdown[:1500])
    if len(markdown) > 1500:
        print("\n... (truncated)")
    print()
    print("=" * 80)

    # Summary
    print("\nSummary:")
    print(f"  ✓ Parsed {parsed.num_examples} examples successfully")
    print(f"  ✓ Identified {len(parsed.patterns)} transformation patterns")
    print(f"  ✓ Generated comprehensive prompt for Sonnet 4.5")
    print(f"  ✓ Prompt saved to {output_file}")
    print()
    print("Next steps:")
    print("  1. Review the generated prompt in weather_api_prompt.md")
    print("  2. Send prompt to Sonnet 4.5 for code generation")
    print("  3. Test generated transformation code with examples")
    print()


if __name__ == "__main__":
    main()
