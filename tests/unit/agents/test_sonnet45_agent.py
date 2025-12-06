"""
Unit tests for Sonnet45Agent.

Tests cover both PM and Coder modes, error handling, and integration.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, mock_open, patch

import pytest

from edgar_analyzer.agents.sonnet45_agent import PromptLoader, Sonnet45Agent
from edgar_analyzer.models.patterns import (
    FieldTypeEnum,
    Pattern,
    PatternType,
)
from edgar_analyzer.models.plan import ClassSpec, GeneratedCode, MethodSpec, PlanSpec
from edgar_analyzer.models.project_config import (
    DataSourceConfig,
    DataSourceType,
    OutputConfig,
    OutputDestinationConfig,
    OutputFormat,
    ProjectConfig,
    ProjectMetadata,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_patterns():
    """Sample transformation patterns for testing."""
    return [
        Pattern(
            type=PatternType.FIELD_MAPPING,
            confidence=1.0,
            source_path="main.temp",
            target_path="temperature_c",
            transformation="Extract temperature from main object",
            examples=[({"temp": 15.5}, 15.5), ({"temp": 20.0}, 20.0)],
            source_type=FieldTypeEnum.FLOAT,
            target_type=FieldTypeEnum.FLOAT,
        ),
        Pattern(
            type=PatternType.ARRAY_FIRST,
            confidence=1.0,
            source_path="weather[0].description",
            target_path="conditions",
            transformation="Extract first weather description",
            examples=[([{"description": "rain"}], "rain")],
            source_type=FieldTypeEnum.STRING,
            target_type=FieldTypeEnum.STRING,
        ),
    ]


@pytest.fixture
def sample_project_config():
    """Sample project configuration for testing."""
    return ProjectConfig(
        project=ProjectMetadata(
            name="test_weather_extractor", description="Test weather extractor"
        ),
        data_sources=[
            DataSourceConfig(
                type=DataSourceType.API,
                name="weather_api",
                endpoint="https://api.openweathermap.org/data/2.5/weather",
            )
        ],
        output=OutputConfig(
            formats=[
                OutputDestinationConfig(
                    type=OutputFormat.JSON, path="output/weather.json"
                )
            ]
        ),
    )


@pytest.fixture
def sample_plan_response():
    """Sample PM mode API response."""
    return json.dumps(
        {
            "strategy": "Fetch weather data from API, parse JSON, transform to output schema",
            "classes": [
                {
                    "name": "WeatherExtractor",
                    "purpose": "Extract weather data",
                    "base_classes": ["IDataExtractor"],
                    "methods": [
                        {
                            "name": "extract",
                            "purpose": "Main extraction method",
                            "parameters": ["self", "city: str"],
                            "return_type": "Optional[Dict[str, Any]]",
                        }
                    ],
                    "attributes": ["api_key: str", "base_url: str"],
                }
            ],
            "dependencies": ["requests", "pydantic"],
            "error_handling": "Retry with exponential backoff",
            "testing_strategy": "Pytest with mocked HTTP responses",
        }
    )


@pytest.fixture
def sample_code_response():
    """Sample Coder mode API response."""
    return """
# ============================================================================
# FILE: extractor.py
# ============================================================================

```python
from typing import Dict, Optional, Any

class WeatherExtractor:
    async def extract(self, city: str) -> Optional[Dict[str, Any]]:
        return {"city": city}
```

# ============================================================================
# FILE: models.py
# ============================================================================

```python
from pydantic import BaseModel

class WeatherData(BaseModel):
    city: str
```

# ============================================================================
# FILE: test_extractor.py
# ============================================================================

```python
import pytest

def test_weather_extraction():
    assert True
```
"""


# ============================================================================
# PROMPT LOADER TESTS
# ============================================================================


class TestPromptLoader:
    """Tests for PromptLoader."""

    def test_init_default_prompts_dir(self):
        """Test initialization with default prompts directory."""
        loader = PromptLoader()
        assert loader.prompts_dir.name == "prompts"
        assert loader.prompts_dir.parent.name == "agents"

    def test_init_custom_prompts_dir(self):
        """Test initialization with custom prompts directory."""
        custom_dir = Path("/tmp/custom_prompts")
        loader = PromptLoader(prompts_dir=custom_dir)
        assert loader.prompts_dir == custom_dir

    def test_load_template_success(self):
        """Test loading an existing template."""
        loader = PromptLoader()
        # Load actual PM template
        content = loader.load_template("pm_mode_prompt.md")
        assert "PM Mode: Implementation Planning" in content
        assert "{{patterns_json}}" in content
        assert "{{project_config_json}}" in content

    def test_load_template_not_found(self):
        """Test loading non-existent template raises error."""
        loader = PromptLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_template("nonexistent.md")

    def test_render_pm_prompt(self, sample_patterns, sample_project_config):
        """Test rendering PM mode prompt with data."""
        loader = PromptLoader()
        prompt = loader.render_pm_prompt(sample_patterns, sample_project_config)

        # Check placeholders replaced
        assert "{{patterns_json}}" not in prompt
        assert "{{project_config_json}}" not in prompt

        # Check data present
        assert "main.temp" in prompt
        assert "temperature_c" in prompt
        assert "test_weather_extractor" in prompt

    def test_render_coder_prompt(self, sample_patterns):
        """Test rendering Coder mode prompt with data."""
        loader = PromptLoader()

        # Create minimal plan
        plan = PlanSpec(
            strategy="Test strategy",
            classes=[
                ClassSpec(
                    name="TestExtractor",
                    purpose="Test",
                    methods=[
                        MethodSpec(
                            name="extract", purpose="Extract", return_type="Dict"
                        )
                    ],
                )
            ],
            dependencies=["requests"],
            error_handling="Retry",
            testing_strategy="Pytest",
        )

        examples = [{"input": {"a": 1}, "output": {"b": 2}}]

        prompt = loader.render_coder_prompt(plan, sample_patterns, examples)

        # Check placeholders replaced
        assert "{{plan_spec_json}}" not in prompt
        assert "{{patterns_and_examples_json}}" not in prompt

        # Check data present
        assert "TestExtractor" in prompt
        assert "field_mapping" in prompt


# ============================================================================
# SONNET45AGENT TESTS
# ============================================================================


class TestSonnet45Agent:
    """Tests for Sonnet45Agent."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        agent = Sonnet45Agent(api_key="test_key")
        assert agent.client.api_key == "test_key"
        assert agent.model == "anthropic/claude-sonnet-4.5"

    def test_init_from_env(self, monkeypatch):
        """Test initialization from environment variable."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "env_key")
        agent = Sonnet45Agent()
        assert agent.client.api_key == "env_key"

    def test_init_custom_model(self):
        """Test initialization with custom model."""
        agent = Sonnet45Agent(api_key="test_key", model="anthropic/claude-3.5-sonnet")
        assert agent.model == "anthropic/claude-3.5-sonnet"

    def test_init_custom_temperatures(self):
        """Test initialization with custom temperatures."""
        agent = Sonnet45Agent(
            api_key="test_key", pm_temperature=0.5, coder_temperature=0.1
        )
        assert agent.pm_temperature == 0.5
        assert agent.coder_temperature == 0.1

    @pytest.mark.asyncio
    async def test_plan_success(
        self, sample_patterns, sample_project_config, sample_plan_response
    ):
        """Test PM mode planning with successful response."""
        agent = Sonnet45Agent(api_key="test_key")

        # Mock API call
        with patch.object(
            agent.client, "chat_completion_json", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = sample_plan_response

            # Execute plan
            plan = await agent.plan(sample_patterns, sample_project_config)

            # Verify API called
            assert mock_api.called
            call_args = mock_api.call_args
            assert call_args.kwargs["temperature"] == agent.pm_temperature

            # Verify plan structure
            assert isinstance(plan, PlanSpec)
            assert len(plan.classes) == 1
            assert plan.classes[0].name == "WeatherExtractor"
            assert len(plan.dependencies) == 2

    @pytest.mark.asyncio
    async def test_plan_invalid_json(self, sample_patterns, sample_project_config):
        """Test PM mode with invalid JSON response."""
        agent = Sonnet45Agent(api_key="test_key")

        with patch.object(
            agent.client, "chat_completion_json", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = "not valid json {"

            with pytest.raises(ValueError, match="invalid JSON"):
                await agent.plan(sample_patterns, sample_project_config)

    @pytest.mark.asyncio
    async def test_plan_missing_required_fields(
        self, sample_patterns, sample_project_config
    ):
        """Test PM mode with missing required fields."""
        agent = Sonnet45Agent(api_key="test_key")

        # Response missing required 'strategy' field
        invalid_response = json.dumps({"classes": [], "dependencies": []})

        with patch.object(
            agent.client, "chat_completion_json", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = invalid_response

            with pytest.raises(ValueError, match="invalid"):
                await agent.plan(sample_patterns, sample_project_config)

    @pytest.mark.asyncio
    async def test_code_success(self, sample_patterns, sample_code_response):
        """Test Coder mode with successful response."""
        agent = Sonnet45Agent(api_key="test_key")

        # Create minimal plan
        plan = PlanSpec(
            strategy="Test",
            classes=[ClassSpec(name="TestExtractor", purpose="Test")],
            dependencies=[],
            error_handling="Test",
            testing_strategy="Test",
        )

        with patch.object(
            agent.client, "chat_completion", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = sample_code_response

            # Execute code generation
            code = await agent.code(plan, sample_patterns)

            # Verify API called
            assert mock_api.called
            call_args = mock_api.call_args
            assert call_args.kwargs["temperature"] == agent.coder_temperature

            # Verify code structure
            assert isinstance(code, GeneratedCode)
            assert "WeatherExtractor" in code.extractor_code
            assert "WeatherData" in code.models_code
            assert "test_weather_extraction" in code.tests_code

    @pytest.mark.asyncio
    async def test_code_with_examples(self, sample_patterns):
        """Test Coder mode with explicit examples."""
        agent = Sonnet45Agent(api_key="test_key")

        plan = PlanSpec(
            strategy="Test",
            classes=[ClassSpec(name="TestExtractor", purpose="Test")],
            dependencies=[],
            error_handling="Test",
            testing_strategy="Test",
        )

        examples = [
            {"input": {"temp": 15}, "output": {"temperature_c": 15}},
            {"input": {"temp": 20}, "output": {"temperature_c": 20}},
        ]

        with patch.object(
            agent.client, "chat_completion", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = """
# FILE: extractor.py
```python
class Test:
    pass
```
# FILE: models.py
```python
class Model:
    pass
```
# FILE: test_extractor.py
```python
def test():
    pass
```
"""

            code = await agent.code(plan, sample_patterns, examples)

            # Verify examples passed to API
            call_args = mock_api.call_args
            messages = call_args.kwargs["messages"]
            prompt_content = messages[1]["content"]

            # Examples should be in prompt
            assert "15" in prompt_content or "20" in prompt_content

    @pytest.mark.asyncio
    async def test_code_parsing_fallback(self, sample_patterns):
        """Test Coder mode code parsing fallback."""
        agent = Sonnet45Agent(api_key="test_key")

        plan = PlanSpec(
            strategy="Test",
            classes=[ClassSpec(name="TestExtractor", purpose="Test")],
            dependencies=[],
            error_handling="Test",
            testing_strategy="Test",
        )

        # Response without file markers (fallback mode)
        response_without_markers = """
```python
class Extractor:
    pass
```

```python
class Model:
    pass
```

```python
def test():
    pass
```
"""

        with patch.object(
            agent.client, "chat_completion", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = response_without_markers

            code = await agent.code(plan, sample_patterns)

            assert "Extractor" in code.extractor_code
            assert "Model" in code.models_code
            assert "test" in code.tests_code

    @pytest.mark.asyncio
    async def test_code_insufficient_blocks(self, sample_patterns):
        """Test Coder mode with insufficient code blocks."""
        agent = Sonnet45Agent(api_key="test_key")

        plan = PlanSpec(
            strategy="Test",
            classes=[ClassSpec(name="TestExtractor", purpose="Test")],
            dependencies=[],
            error_handling="Test",
            testing_strategy="Test",
        )

        # Only one code block
        insufficient_response = """
```python
class OnlyOne:
    pass
```
"""

        with patch.object(
            agent.client, "chat_completion", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = insufficient_response

            with pytest.raises(ValueError, match="Expected 3 code blocks"):
                await agent.code(plan, sample_patterns)

    @pytest.mark.asyncio
    async def test_plan_and_code_success(
        self,
        sample_patterns,
        sample_project_config,
        sample_plan_response,
        sample_code_response,
    ):
        """Test end-to-end plan_and_code pipeline."""
        agent = Sonnet45Agent(api_key="test_key")

        with patch.object(
            agent.client, "chat_completion_json", new_callable=AsyncMock
        ) as mock_plan:
            with patch.object(
                agent.client, "chat_completion", new_callable=AsyncMock
            ) as mock_code:
                mock_plan.return_value = sample_plan_response
                mock_code.return_value = sample_code_response

                # Execute end-to-end
                code = await agent.plan_and_code(sample_patterns, sample_project_config)

                # Verify both API calls made
                assert mock_plan.called
                assert mock_code.called

                # Verify output
                assert isinstance(code, GeneratedCode)
                assert code.metadata.get("plan_strategy")

    @pytest.mark.asyncio
    async def test_plan_and_code_pm_failure(
        self, sample_patterns, sample_project_config
    ):
        """Test plan_and_code when PM mode fails."""
        agent = Sonnet45Agent(api_key="test_key")

        with patch.object(
            agent.client, "chat_completion_json", new_callable=AsyncMock
        ) as mock_plan:
            mock_plan.side_effect = Exception("API Error")

            with pytest.raises(Exception, match="API Error"):
                await agent.plan_and_code(sample_patterns, sample_project_config)

    @pytest.mark.asyncio
    async def test_plan_and_code_coder_failure(
        self, sample_patterns, sample_project_config, sample_plan_response
    ):
        """Test plan_and_code when Coder mode fails."""
        agent = Sonnet45Agent(api_key="test_key")

        with patch.object(
            agent.client, "chat_completion_json", new_callable=AsyncMock
        ) as mock_plan:
            with patch.object(
                agent.client, "chat_completion", new_callable=AsyncMock
            ) as mock_code:
                mock_plan.return_value = sample_plan_response
                mock_code.side_effect = Exception("Coder Error")

                with pytest.raises(Exception, match="Coder Error"):
                    await agent.plan_and_code(sample_patterns, sample_project_config)
