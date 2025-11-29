"""Integration test for PM Mode with Weather API examples.

This test verifies the end-to-end PM Mode analysis flow with real OpenRouter API calls.
Requires OPENROUTER_API_KEY environment variable to be set.
"""

import json
import os
from pathlib import Path

import pytest

from edgar.services import Sonnet4_5Service, OpenRouterClient, ContextManager


# Load weather examples and schema
EXAMPLES_PATH = Path(__file__).parent.parent.parent / "examples" / "weather_api" / "examples.json"


def load_weather_examples() -> list[dict]:
    """Load weather API examples from JSON file."""
    with open(EXAMPLES_PATH) as f:
        return json.load(f)


def load_weather_schema() -> type:
    """Load WeatherData schema dynamically."""
    # Import from examples.weather_api.target_schema
    import sys
    schema_module_path = Path(__file__).parent.parent.parent / "examples" / "weather_api"
    sys.path.insert(0, str(schema_module_path))

    from target_schema import WeatherData

    sys.path.pop(0)
    return WeatherData


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY environment variable not set"
)
class TestPMModeWeatherAnalysis:
    """Integration tests for PM Mode with Weather API."""

    @pytest.fixture
    def client(self) -> OpenRouterClient:
        """Create OpenRouter client with real API key."""
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        return OpenRouterClient(api_key=api_key)

    @pytest.fixture
    def context_manager(self) -> ContextManager:
        """Create context manager."""
        return ContextManager(max_messages=20)

    @pytest.fixture
    def service(
        self,
        client: OpenRouterClient,
        context_manager: ContextManager,
    ) -> Sonnet4_5Service:
        """Create Sonnet4_5Service with real dependencies."""
        return Sonnet4_5Service(client=client, context=context_manager)

    @pytest.mark.asyncio
    async def test_analyze_weather_examples(
        self,
        service: Sonnet4_5Service,
    ) -> None:
        """Test PM Mode analysis with real Weather API examples.

        This test:
        1. Loads real weather API response examples
        2. Uses WeatherData Pydantic schema as target
        3. Calls OpenRouter API to analyze examples
        4. Validates the returned extraction strategy structure
        5. Verifies specific patterns were identified
        """
        # Load examples and schema
        examples = load_weather_examples()
        weather_schema = load_weather_schema()

        # Analyze examples with PM Mode
        strategy = await service.analyze_examples(examples, weather_schema)

        # Validate strategy structure (all required fields present)
        assert "data_source_type" in strategy, "Missing data_source_type"
        assert "response_format" in strategy, "Missing response_format"
        assert "extraction_patterns" in strategy, "Missing extraction_patterns"
        assert "transformations" in strategy, "Missing transformations"
        assert "validation_rules" in strategy, "Missing validation_rules"

        # Verify data source identification
        assert strategy["data_source_type"] in [
            "REST_API", "REST API", "API", "HTTP_API"
        ], f"Unexpected data source type: {strategy['data_source_type']}"

        # Verify response format identification
        assert strategy["response_format"] in [
            "JSON", "json"
        ], f"Unexpected response format: {strategy['response_format']}"

        # Verify extraction patterns were identified
        extraction_patterns = strategy["extraction_patterns"]
        assert isinstance(extraction_patterns, dict), "extraction_patterns should be dict"

        # Check for key weather fields in extraction patterns
        expected_fields = [
            "city_name",
            "temperature_celsius",
            "humidity",
            "weather_condition",
        ]

        for field in expected_fields:
            assert field in extraction_patterns, \
                f"Missing extraction pattern for {field}. Found patterns: {list(extraction_patterns.keys())}"

            # Verify pattern structure
            pattern = extraction_patterns[field]
            assert "source_path" in pattern, f"Missing source_path for {field}"
            assert "description" in pattern, f"Missing description for {field}"

        # Verify temperature conversion transformation was identified
        # (Kelvin to Celsius is a key transformation for weather data)
        transformations = strategy["transformations"]
        assert isinstance(transformations, list), "transformations should be list"

        temp_conversions = [
            t for t in transformations
            if "temperature" in t.get("field", "").lower()
        ]
        assert len(temp_conversions) > 0, \
            "Expected temperature conversion transformation. " \
            f"Found transformations: {transformations}"

        # Verify validation rules were defined
        validation_rules = strategy["validation_rules"]
        assert isinstance(validation_rules, dict), "validation_rules should be dict"

        # Temperature validation should include range constraints
        if "temperature_celsius" in validation_rules:
            temp_rule = validation_rules["temperature_celsius"]
            assert "type" in temp_rule, "Missing type in temperature validation"
            assert temp_rule["type"] in ["float", "number"], \
                f"Unexpected temperature type: {temp_rule['type']}"

        # Print strategy for debugging (useful for development)
        print("\n" + "=" * 80)
        print("GENERATED EXTRACTION STRATEGY:")
        print("=" * 80)
        print(json.dumps(strategy, indent=2))
        print("=" * 80)

    @pytest.mark.asyncio
    async def test_analyze_weather_examples_context_management(
        self,
        service: Sonnet4_5Service,
    ) -> None:
        """Test that conversation context is properly maintained."""
        # Load examples and schema
        examples = load_weather_examples()
        weather_schema = load_weather_schema()

        # Analyze examples
        await service.analyze_examples(examples, weather_schema)

        # Verify context was updated
        messages = service.context.get_messages()

        # Should have at least: system message, user message, assistant response
        assert len(messages) >= 3, \
            f"Expected at least 3 messages in context, got {len(messages)}"

        # Verify message types
        roles = [m["role"] for m in messages]
        assert "system" in roles, "Missing system message in context"
        assert "user" in roles, "Missing user message in context"
        assert "assistant" in roles, "Missing assistant message in context"

        # Verify system message contains prompt template content
        system_messages = [m for m in messages if m["role"] == "system"]
        assert len(system_messages) > 0, "No system messages found"

        system_content = system_messages[0]["content"]
        assert "data engineer" in system_content.lower(), \
            "System message should contain PM Mode prompt"
        assert "extraction strategy" in system_content.lower(), \
            "System message should mention extraction strategy"
