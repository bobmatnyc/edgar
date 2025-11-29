"""Integration tests for Coder Mode with Weather API extraction strategy.

This test demonstrates the full Coder Mode workflow:
1. PM Mode generates extraction strategy from Weather API examples
2. Coder Mode generates Python code from that strategy
3. Validate generated code structure and syntax
"""

import ast
import os
import pytest

from edgar.services import Sonnet4_5Service, OpenRouterClient, ContextManager


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="No API key")
async def test_generate_weather_extractor_code():
    """Test Coder Mode generates valid Python code from Weather API strategy.

    This integration test demonstrates:
    - Loading a pre-defined extraction strategy (from PM Mode)
    - Calling Coder Mode to generate Python code
    - Validating the generated code structure
    - Ensuring code compiles and has expected components
    """
    # Pre-generated extraction strategy from PM Mode
    # (This would normally come from analyze_examples, but using fixed
    # strategy for deterministic testing)
    weather_strategy = {
        "data_source_type": "REST_API",
        "response_format": "JSON",
        "extraction_patterns": {
            "temperature": {
                "source_path": "$.main.temp",
                "description": "Temperature in Kelvin",
                "optional": False,
                "default_value": None,
            },
            "humidity": {
                "source_path": "$.main.humidity",
                "description": "Humidity percentage",
                "optional": False,
                "default_value": None,
            },
            "location": {
                "source_path": "$.name",
                "description": "City name",
                "optional": False,
                "default_value": None,
            },
        },
        "transformations": [
            {
                "field": "temperature",
                "operation": "unit_conversion",
                "formula": "value - 273.15",
                "description": "Convert Kelvin to Celsius",
            }
        ],
        "validation_rules": {
            "temperature": {
                "type": "float",
                "constraints": {"required": True, "min": -50, "max": 50},
                "error_handling": "fail",
                "default_value": None,
            },
            "humidity": {
                "type": "int",
                "constraints": {"required": True, "min": 0, "max": 100},
                "error_handling": "fail",
                "default_value": None,
            },
            "location": {
                "type": "str",
                "constraints": {"required": True, "min_length": 1},
                "error_handling": "fail",
                "default_value": None,
            },
        },
        "cross_field_validations": [],
        "error_handling": {
            "missing_fields": "fail",
            "invalid_types": "fail",
            "validation_failures": "fail",
        },
        "assumptions": [
            "Temperature is provided in Kelvin",
            "Humidity is percentage (0-100)",
            "Location is city name string",
        ],
    }

    # Initialize service with real API client
    api_key = os.getenv("OPENROUTER_API_KEY")
    assert api_key, "OPENROUTER_API_KEY environment variable required"

    client = OpenRouterClient(api_key=api_key)
    context = ContextManager()
    service = Sonnet4_5Service(client=client, context=context)

    # Generate code using Coder Mode
    print("\n🔧 Generating Python code from strategy...")
    code = await service.generate_code(strategy=weather_strategy)

    # Validate code was generated
    assert code is not None, "No code generated"
    assert len(code) > 0, "Generated code is empty"

    print(f"\n✅ Generated {len(code)} characters of code")

    # Validate code structure
    print("\n📋 Validating code structure...")

    # Should contain class definitions
    assert "class" in code, "No classes found in generated code"

    # Should implement required interfaces (directly or via implementation)
    # Note: Code might not literally have "IDataSource" string, but should have
    # data source and extractor classes
    has_data_source = any(
        keyword in code.lower()
        for keyword in ["datasource", "data_source", "source", "fetch"]
    )
    assert has_data_source, "No data source implementation found"

    has_extractor = any(
        keyword in code.lower() for keyword in ["extractor", "extract", "parse"]
    )
    assert has_extractor, "No extractor implementation found"

    # Should have async methods (for data fetching)
    assert "async def" in code, "No async methods found"

    # Should use Pydantic or BaseModel
    has_pydantic = "BaseModel" in code or "pydantic" in code.lower()
    assert has_pydantic, "No Pydantic models found"

    # Should reference the temperature conversion (273.15 or kelvin)
    has_temp_conversion = "273.15" in code or "kelvin" in code.lower()
    assert has_temp_conversion, "Temperature conversion not implemented"

    # Should have weather-related fields
    assert "temperature" in code.lower(), "Temperature field not found"
    assert "humidity" in code.lower(), "Humidity field not found"

    print("✅ Code structure validation passed")

    # Validate syntax using Python AST parser
    print("\n🔍 Validating Python syntax...")
    try:
        ast.parse(code)
        print("✅ Code syntax is valid")
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax errors: {e}")

    # Print sample of generated code for inspection
    print("\n📝 Generated Code Sample (first 500 chars):")
    print("-" * 60)
    print(code[:500] + "..." if len(code) > 500 else code)
    print("-" * 60)

    # Validate type hints are present
    has_type_hints = "->" in code or ": " in code
    assert has_type_hints, "No type hints found in generated code"

    print("\n✅ Integration test passed!")
    print(f"   - Generated {len(code)} chars of valid Python code")
    print(f"   - Contains data source and extractor classes")
    print(f"   - Uses async/await patterns")
    print(f"   - Has Pydantic models for validation")
    print(f"   - Implements temperature conversion (Kelvin -> Celsius)")


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="No API key")
async def test_coder_mode_with_custom_constraints():
    """Test Coder Mode respects custom architecture constraints."""
    # Simple strategy for testing constraints
    simple_strategy = {
        "data_source_type": "REST_API",
        "response_format": "JSON",
        "extraction_patterns": {
            "value": {
                "source_path": "$.data.value",
                "description": "Test value",
                "optional": False,
                "default_value": None,
            }
        },
        "transformations": [],
        "validation_rules": {
            "value": {
                "type": "str",
                "constraints": {"required": True},
                "error_handling": "fail",
                "default_value": None,
            }
        },
        "cross_field_validations": [],
        "error_handling": {
            "missing_fields": "fail",
            "invalid_types": "fail",
            "validation_failures": "fail",
        },
        "assumptions": ["Value is string"],
    }

    # Custom constraints
    custom_constraints = {
        "interfaces": ["IDataSource", "IDataExtractor"],
        "use_dependency_injection": True,
        "use_pydantic_models": True,
        "type_hints_required": True,
        "docstrings_required": True,
        "pep8_compliance": True,
        "max_line_length": 100,
        "use_dataclasses": True,
    }

    # Initialize service
    api_key = os.getenv("OPENROUTER_API_KEY")
    client = OpenRouterClient(api_key=api_key)
    context = ContextManager()
    service = Sonnet4_5Service(client=client, context=context)

    # Generate code with custom constraints
    print("\n🔧 Generating code with custom constraints...")
    code = await service.generate_code(
        strategy=simple_strategy, architecture_constraints=custom_constraints
    )

    # Validate constraints were applied
    assert code is not None
    assert len(code) > 0

    # Should use dataclasses (frozen=True pattern)
    assert "dataclass" in code.lower(), "Dataclass decorator not found"

    # Validate syntax
    ast.parse(code)

    print("✅ Custom constraints test passed!")
