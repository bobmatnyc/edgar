"""Unit tests for Sonnet4_5Service."""

import json
import pytest
from unittest.mock import Mock, AsyncMock
from pydantic import BaseModel, Field, ValidationError as PydanticValidationError

from edgar.services import Sonnet4_5Service, OpenRouterClient, ContextManager
from edgar.services.openrouter_client import OpenRouterAuthError, OpenRouterRateLimitError


class SampleSchema(BaseModel):
    """Sample Pydantic schema for testing."""

    temperature: float = Field(..., description="Temperature in Celsius")
    humidity: int = Field(..., ge=0, le=100)


class TestSonnet4_5Service:
    """Test suite for Sonnet4_5Service."""

    @pytest.fixture
    def mock_client(self) -> Mock:
        """Create mock OpenRouter client."""
        client = Mock(spec=OpenRouterClient)
        client.chat_completion = AsyncMock()
        return client

    @pytest.fixture
    def context_manager(self) -> ContextManager:
        """Create context manager."""
        return ContextManager(max_messages=10)

    @pytest.fixture
    def service(
        self,
        mock_client: Mock,
        context_manager: ContextManager,
    ) -> Sonnet4_5Service:
        """Create Sonnet4_5Service instance."""
        return Sonnet4_5Service(
            client=mock_client,
            context=context_manager,
        )

    @pytest.fixture
    def valid_strategy_json(self) -> dict:
        """Valid extraction strategy JSON for testing."""
        return {
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
            },
            "cross_field_validations": [],
            "error_handling": {
                "missing_fields": "fail",
                "invalid_types": "fail",
                "validation_failures": "fail",
            },
            "assumptions": ["Temperature is provided in Kelvin", "Humidity is percentage"],
        }

    @pytest.mark.asyncio
    async def test_analyze_examples_success(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
        valid_strategy_json: dict,
    ) -> None:
        """Test successful example analysis with valid LLM response."""
        # Setup mock response
        mock_client.chat_completion.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(valid_strategy_json, indent=2)
                    }
                }
            ]
        }

        # Test examples
        examples = [
            {"main": {"temp": 295.15, "humidity": 65}},
            {"main": {"temp": 300.15, "humidity": 70}},
        ]

        # Execute
        result = await service.analyze_examples(examples, SampleSchema)

        # Verify
        assert result["data_source_type"] == "REST_API"
        assert result["response_format"] == "JSON"
        assert "temperature" in result["extraction_patterns"]
        assert "humidity" in result["extraction_patterns"]
        assert len(result["transformations"]) == 1
        assert result["transformations"][0]["field"] == "temperature"

        # Verify API was called with correct params
        mock_client.chat_completion.assert_called_once()
        call_args = mock_client.chat_completion.call_args
        assert call_args[1]["temperature"] == 0.3
        assert call_args[1]["max_tokens"] == 4096

        # Verify context was updated
        messages = service.context.get_messages()
        assert any(m["role"] == "system" for m in messages)
        assert any(m["role"] == "user" for m in messages)
        assert any(m["role"] == "assistant" for m in messages)

    @pytest.mark.asyncio
    async def test_analyze_examples_with_markdown_wrapped_json(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
        valid_strategy_json: dict,
    ) -> None:
        """Test JSON extraction from markdown code blocks."""
        # Setup mock response with markdown wrapper
        json_content = json.dumps(valid_strategy_json, indent=2)
        markdown_wrapped = f"```json\n{json_content}\n```"

        mock_client.chat_completion.return_value = {
            "choices": [{"message": {"content": markdown_wrapped}}]
        }

        # Execute
        examples = [{"main": {"temp": 295.15, "humidity": 65}}]
        result = await service.analyze_examples(examples, SampleSchema)

        # Verify extraction worked
        assert result["data_source_type"] == "REST_API"
        assert "temperature" in result["extraction_patterns"]

    @pytest.mark.asyncio
    async def test_analyze_examples_empty_examples_raises_error(
        self,
        service: Sonnet4_5Service,
    ) -> None:
        """Test that empty examples list raises ValueError."""
        with pytest.raises(ValueError, match="Examples list cannot be empty"):
            await service.analyze_examples([], SampleSchema)

    @pytest.mark.asyncio
    async def test_analyze_examples_invalid_json_raises_error(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
    ) -> None:
        """Test that invalid JSON in LLM response raises ValueError."""
        # Setup mock with invalid JSON
        mock_client.chat_completion.return_value = {
            "choices": [{"message": {"content": "Not valid JSON at all"}}]
        }

        examples = [{"temp": 72}]
        with pytest.raises(ValueError, match="Failed to parse JSON from LLM response"):
            await service.analyze_examples(examples, SampleSchema)

    @pytest.mark.asyncio
    async def test_analyze_examples_pydantic_validation_error(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
    ) -> None:
        """Test that LLM response missing required fields raises validation error."""
        # Setup mock with incomplete strategy (missing required fields)
        incomplete_strategy = {
            "data_source_type": "REST_API",
            # Missing response_format and extraction_patterns (required)
        }

        mock_client.chat_completion.return_value = {
            "choices": [{"message": {"content": json.dumps(incomplete_strategy)}}]
        }

        examples = [{"temp": 72}]
        with pytest.raises(ValueError, match="doesn't match ExtractionStrategy schema"):
            await service.analyze_examples(examples, SampleSchema)

    @pytest.mark.asyncio
    async def test_analyze_examples_auth_error_propagation(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
    ) -> None:
        """Test that authentication errors are properly propagated."""
        # Setup mock to raise auth error
        mock_client.chat_completion.side_effect = OpenRouterAuthError(
            "Invalid API key"
        )

        examples = [{"temp": 72}]
        with pytest.raises(OpenRouterAuthError, match="authentication failed"):
            await service.analyze_examples(examples, SampleSchema)

    @pytest.mark.asyncio
    async def test_analyze_examples_rate_limit_error_propagation(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
    ) -> None:
        """Test that rate limit errors are properly propagated."""
        # Setup mock to raise rate limit error
        mock_client.chat_completion.side_effect = OpenRouterRateLimitError(
            "Rate limit exceeded"
        )

        examples = [{"temp": 72}]
        with pytest.raises(OpenRouterRateLimitError, match="rate limit exceeded"):
            await service.analyze_examples(examples, SampleSchema)

    @pytest.mark.asyncio
    async def test_generate_code_success(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
        valid_strategy_json: dict,
    ) -> None:
        """Test successful code generation from strategy."""
        # Setup mock to return valid Python code
        python_code = """
from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel, Field

class WeatherData(BaseModel):
    temperature: float = Field(..., ge=-50, le=50)
    humidity: int = Field(..., ge=0, le=100)

@dataclass(frozen=True)
class WeatherDataSource:
    api_key: str

    async def fetch(self) -> dict[str, Any]:
        return {}

@dataclass(frozen=True)
class WeatherDataExtractor:
    def extract(self, raw_data: dict[str, Any]) -> WeatherData:
        return WeatherData(
            temperature=raw_data["main"]["temp"] - 273.15,
            humidity=raw_data["main"]["humidity"]
        )
"""
        mock_client.chat_completion.return_value = {
            "choices": [{"message": {"content": python_code}}]
        }

        # Call generate_code
        code = await service.generate_code(strategy=valid_strategy_json)

        # Verify code was returned
        assert code is not None
        assert len(code) > 0
        assert "class WeatherData" in code
        assert "WeatherDataSource" in code
        assert "WeatherDataExtractor" in code

        # Verify API call was made with correct params
        mock_client.chat_completion.assert_called_once()
        call_args = mock_client.chat_completion.call_args
        assert call_args.kwargs["temperature"] == 0.2  # Lower temp for code
        assert call_args.kwargs["max_tokens"] == 8192  # More tokens

    @pytest.mark.asyncio
    async def test_generate_code_extracts_from_markdown(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
        valid_strategy_json: dict,
    ) -> None:
        """Test code extraction from markdown-wrapped response."""
        # Setup mock to return code wrapped in markdown
        markdown_response = """```python
class WeatherData:
    pass
```"""
        mock_client.chat_completion.return_value = {
            "choices": [{"message": {"content": markdown_response}}]
        }

        # Call generate_code
        code = await service.generate_code(strategy=valid_strategy_json)

        # Verify markdown was stripped
        assert "```python" not in code
        assert "```" not in code
        assert "class WeatherData:" in code

    @pytest.mark.asyncio
    async def test_generate_code_validates_syntax(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
        valid_strategy_json: dict,
    ) -> None:
        """Test that invalid Python syntax raises ValueError."""
        # Setup mock to return invalid Python code
        invalid_code = "def broken_function(\nprint('missing closing paren')"
        mock_client.chat_completion.return_value = {
            "choices": [{"message": {"content": invalid_code}}]
        }

        # Call generate_code and expect ValueError
        with pytest.raises(ValueError, match="syntax errors at line"):
            await service.generate_code(strategy=valid_strategy_json)

    @pytest.mark.asyncio
    async def test_generate_code_empty_response_raises_error(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
        valid_strategy_json: dict,
    ) -> None:
        """Test that empty code response raises ValueError."""
        # Setup mock to return empty content
        mock_client.chat_completion.return_value = {
            "choices": [{"message": {"content": ""}}]
        }

        # Call generate_code and expect ValueError
        with pytest.raises(ValueError, match="Generated code is empty"):
            await service.generate_code(strategy=valid_strategy_json)

    @pytest.mark.asyncio
    async def test_generate_code_uses_default_constraints(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
        valid_strategy_json: dict,
    ) -> None:
        """Test that default constraints are used when none provided."""
        # Setup mock to return valid code
        mock_client.chat_completion.return_value = {
            "choices": [{"message": {"content": "class Test:\n    pass"}}]
        }

        # Call generate_code without constraints
        await service.generate_code(strategy=valid_strategy_json)

        # Verify system message contains default constraints
        messages = service.context.get_messages()
        system_msg = messages[0]["content"]

        # Check that default constraints are present in prompt
        assert "IDataSource" in system_msg
        assert "IDataExtractor" in system_msg
        assert "use_dependency_injection" in system_msg
        assert "use_pydantic_models" in system_msg

    @pytest.mark.asyncio
    async def test_generate_code_empty_strategy_raises_error(
        self,
        service: Sonnet4_5Service,
    ) -> None:
        """Test that empty strategy raises ValueError."""
        with pytest.raises(ValueError, match="Strategy dictionary cannot be empty"):
            await service.generate_code(strategy={})

    @pytest.mark.asyncio
    async def test_generate_code_auth_error_propagation(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
        valid_strategy_json: dict,
    ) -> None:
        """Test that authentication errors are properly propagated."""
        # Setup mock to raise auth error
        mock_client.chat_completion.side_effect = OpenRouterAuthError(
            "Invalid API key"
        )

        # Call generate_code and expect auth error
        with pytest.raises(OpenRouterAuthError, match="authentication failed"):
            await service.generate_code(strategy=valid_strategy_json)

    @pytest.mark.asyncio
    async def test_generate_code_rate_limit_error_propagation(
        self,
        service: Sonnet4_5Service,
        mock_client: Mock,
        valid_strategy_json: dict,
    ) -> None:
        """Test that rate limit errors are properly propagated."""
        # Setup mock to raise rate limit error
        mock_client.chat_completion.side_effect = OpenRouterRateLimitError(
            "Rate limit exceeded"
        )

        # Call generate_code and expect rate limit error
        with pytest.raises(OpenRouterRateLimitError, match="rate limit exceeded"):
            await service.generate_code(strategy=valid_strategy_json)


class TestExtractJsonHelper:
    """Test suite for _extract_json helper method."""

    @pytest.fixture
    def service(self) -> Sonnet4_5Service:
        """Create service with mock dependencies."""
        mock_client = Mock(spec=OpenRouterClient)
        context = ContextManager()
        return Sonnet4_5Service(client=mock_client, context=context)

    def test_extract_json_plain_json(self, service: Sonnet4_5Service) -> None:
        """Test extracting plain JSON without markdown."""
        content = '{"key": "value", "number": 42}'
        result = service._extract_json(content)
        assert result == {"key": "value", "number": 42}

    def test_extract_json_with_markdown_json_block(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test extracting JSON from ```json code block."""
        content = '```json\n{"key": "value"}\n```'
        result = service._extract_json(content)
        assert result == {"key": "value"}

    def test_extract_json_with_generic_code_block(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test extracting JSON from generic ``` code block."""
        content = '```\n{"key": "value"}\n```'
        result = service._extract_json(content)
        assert result == {"key": "value"}

    def test_extract_json_with_whitespace(self, service: Sonnet4_5Service) -> None:
        """Test extracting JSON with leading/trailing whitespace."""
        content = '\n\n  {"key": "value"}  \n\n'
        result = service._extract_json(content)
        assert result == {"key": "value"}

    def test_extract_json_invalid_json_raises_error(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test that invalid JSON raises JSONDecodeError."""
        content = "Not valid JSON"
        with pytest.raises(json.JSONDecodeError):
            service._extract_json(content)

    def test_extract_json_non_dict_raises_error(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test that non-dict JSON (like array) raises ValueError."""
        content = '["array", "not", "dict"]'
        with pytest.raises(ValueError, match="Expected JSON object"):
            service._extract_json(content)

    def test_extract_json_empty_code_block_raises_error(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test that empty code block raises ValueError."""
        content = "```\n```"
        with pytest.raises(ValueError, match="no JSON found inside"):
            service._extract_json(content)


class TestFormatHelpers:
    """Test suite for formatting helper methods."""

    @pytest.fixture
    def service(self) -> Sonnet4_5Service:
        """Create service with mock dependencies."""
        mock_client = Mock(spec=OpenRouterClient)
        context = ContextManager()
        return Sonnet4_5Service(client=mock_client, context=context)

    def test_format_examples_single_example(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test formatting single example."""
        examples = [{"temp": 72, "humidity": 45}]
        result = service._format_examples(examples)

        assert "Example 1:" in result
        assert "```json" in result
        assert '"temp": 72' in result
        assert '"humidity": 45' in result

    def test_format_examples_multiple_examples(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test formatting multiple examples."""
        examples = [{"temp": 72}, {"temp": 75}]
        result = service._format_examples(examples)

        assert "Example 1:" in result
        assert "Example 2:" in result
        assert result.count("```json") == 2

    def test_format_schema_pydantic_model(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test formatting Pydantic model schema."""
        result = service._format_schema(SampleSchema)

        # Should be JSON schema
        schema_dict = json.loads(result)
        assert "properties" in schema_dict
        assert "temperature" in schema_dict["properties"]
        assert "humidity" in schema_dict["properties"]

    def test_format_schema_non_pydantic_fallback(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test formatting non-Pydantic type falls back to str()."""
        result = service._format_schema(dict)
        assert "dict" in result.lower()


class TestExtractPythonCodeHelper:
    """Test suite for _extract_python_code helper method."""

    @pytest.fixture
    def service(self) -> Sonnet4_5Service:
        """Create service with mock dependencies."""
        mock_client = Mock(spec=OpenRouterClient)
        context = ContextManager()
        return Sonnet4_5Service(client=mock_client, context=context)

    def test_extract_python_code_plain_code(self, service: Sonnet4_5Service) -> None:
        """Test extracting plain Python code without markdown."""
        code = "print('hello')\nclass Test:\n    pass"
        result = service._extract_python_code(code)
        assert result == code

    def test_extract_python_code_with_markdown_python_block(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test extracting code from ```python block."""
        content = "```python\nprint('hello')\nclass Test:\n    pass\n```"
        result = service._extract_python_code(content)
        assert result == "print('hello')\nclass Test:\n    pass"
        assert "```python" not in result
        assert "```" not in result

    def test_extract_python_code_with_generic_code_block(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test extracting code from generic ``` block."""
        content = "```\nprint('hello')\n```"
        result = service._extract_python_code(content)
        assert result == "print('hello')"
        assert "```" not in result

    def test_extract_python_code_with_whitespace(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test extracting code with leading/trailing whitespace."""
        content = "\n\n  print('hello')  \n\n"
        result = service._extract_python_code(content)
        assert "print('hello')" in result

    def test_extract_python_code_multiline_in_markdown(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test extracting multi-line code from markdown."""
        content = """```python
from typing import Any

class MyClass:
    def method(self) -> None:
        pass
```"""
        result = service._extract_python_code(content)
        assert "from typing import Any" in result
        assert "class MyClass:" in result
        assert "def method(self) -> None:" in result
        assert "```python" not in result


class TestValidateCodeSyntaxHelper:
    """Test suite for _validate_code_syntax helper method."""

    @pytest.fixture
    def service(self) -> Sonnet4_5Service:
        """Create service with mock dependencies."""
        mock_client = Mock(spec=OpenRouterClient)
        context = ContextManager()
        return Sonnet4_5Service(client=mock_client, context=context)

    def test_validate_code_syntax_valid_code(self, service: Sonnet4_5Service) -> None:
        """Test validation passes for valid Python code."""
        code = "print('hello')\nclass Test:\n    pass"
        # Should not raise any exception
        service._validate_code_syntax(code)

    def test_validate_code_syntax_valid_complex_code(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test validation passes for complex valid code."""
        code = """
from typing import Any
from dataclasses import dataclass

@dataclass(frozen=True)
class MyClass:
    value: int

    async def method(self) -> dict[str, Any]:
        return {"key": self.value}
"""
        # Should not raise any exception
        service._validate_code_syntax(code)

    def test_validate_code_syntax_missing_colon(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test validation fails for missing colon."""
        code = "if True\n    pass"
        with pytest.raises(ValueError, match="syntax errors at line"):
            service._validate_code_syntax(code)

    def test_validate_code_syntax_unclosed_string(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test validation fails for unclosed string."""
        code = "print('unterminated string"
        with pytest.raises(ValueError, match="syntax errors"):
            service._validate_code_syntax(code)

    def test_validate_code_syntax_invalid_indentation(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test validation fails for invalid indentation."""
        code = "def func():\npass"  # Missing indentation
        with pytest.raises(ValueError, match="syntax errors"):
            service._validate_code_syntax(code)

    def test_validate_code_syntax_error_includes_line_number(
        self, service: Sonnet4_5Service
    ) -> None:
        """Test error message includes line number."""
        code = "valid_line = 1\nif True\n    pass"
        with pytest.raises(ValueError) as exc_info:
            service._validate_code_syntax(code)
        # Check that error message contains line number
        assert "line" in str(exc_info.value).lower()
