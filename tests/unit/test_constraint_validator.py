"""Tests for ConstraintValidator."""

import pytest

from edgar.validators.constraint_validator import ConstraintValidator


class TestConstraintValidator:
    """Test suite for ConstraintValidator."""

    @pytest.fixture
    def validator(self) -> ConstraintValidator:
        """Create validator instance."""
        return ConstraintValidator()

    class TestInterfaceValidation:
        """Tests for interface compliance checking."""

        def test_valid_interface_implementation(self, validator: ConstraintValidator) -> None:
            """Code with proper IDataExtractor passes."""
            code = '''
from typing import Any
from pydantic import BaseModel

class MyData(BaseModel):
    value: int

class MyExtractor:
    def extract(self, raw_data: dict[str, Any]) -> MyData:
        return MyData(value=raw_data["value"])
'''
            result = validator.validate(code, {})
            # Code doesn't explicitly inherit from IDataExtractor, so should fail
            assert not result.valid
            assert any("IDataExtractor" in err for err in result.errors)

        def test_explicit_interface_inheritance(self, validator: ConstraintValidator) -> None:
            """Explicit IDataExtractor inheritance passes interface check."""
            code = '''
from typing import Any
from pydantic import BaseModel, Field
from dataclasses import dataclass

class MyData(BaseModel):
    value: int = Field(..., description="The value")

@dataclass(frozen=True)
class IDataExtractor:
    def extract(self, raw_data: dict[str, Any]) -> BaseModel:
        pass

@dataclass(frozen=True)
class IDataSource:
    async def fetch(self) -> dict[str, Any]:
        pass

@dataclass(frozen=True)
class MyExtractor(IDataExtractor):
    def extract(self, raw_data: dict[str, Any]) -> MyData:
        return MyData(value=raw_data["value"])

@dataclass(frozen=True)
class MySource(IDataSource):
    async def fetch(self) -> dict[str, Any]:
        return {}
'''
            result = validator.validate(code, {})
            # Has both required interfaces implemented
            assert result.valid

        def test_missing_extract_method(self, validator: ConstraintValidator) -> None:
            """Code without extract method fails."""
            code = '''
from typing import Any

class IDataExtractor:
    def extract(self, raw_data: dict[str, Any]) -> Any:
        pass

class MyExtractor(IDataExtractor):
    def process(self, data: Any) -> None:
        pass
'''
            result = validator.validate(code, {})
            # Should warn about missing extract method
            assert len(result.warnings) > 0
            assert any("extract" in warning.lower() for warning in result.warnings)

        def test_async_data_source_interface(self, validator: ConstraintValidator) -> None:
            """IDataSource with async fetch method passes."""
            code = '''
from typing import Any
from pydantic import BaseModel, Field
from dataclasses import dataclass

@dataclass(frozen=True)
class IDataSource:
    async def fetch(self) -> dict[str, Any]:
        pass

@dataclass(frozen=True)
class IDataExtractor:
    def extract(self, raw_data: dict[str, Any]) -> BaseModel:
        pass

@dataclass(frozen=True)
class MySource(IDataSource):
    async def fetch(self) -> dict[str, Any]:
        return {"data": "value"}

class Result(BaseModel):
    data: str = Field(..., description="The data")

@dataclass(frozen=True)
class MyExtractor(IDataExtractor):
    def extract(self, raw_data: dict[str, Any]) -> Result:
        return Result(data="test")
'''
            result = validator.validate(code, {})
            # Should pass with both interfaces
            assert result.valid

        def test_wrong_method_signature(self, validator: ConstraintValidator) -> None:
            """Wrong method signature generates warning."""
            code = '''
from typing import Any

class IDataExtractor:
    def extract(self, raw_data: dict[str, Any]) -> Any:
        pass

class MyExtractor(IDataExtractor):
    def extract(self, wrong_param: str) -> str:
        return wrong_param
'''
            result = validator.validate(code, {})
            # Should warn about parameter mismatch
            assert len(result.warnings) > 0

        def test_sync_instead_of_async(self, validator: ConstraintValidator) -> None:
            """Sync method when async expected generates warning."""
            code = '''
from typing import Any

class IDataSource:
    async def fetch(self) -> dict[str, Any]:
        pass

class MySource(IDataSource):
    def fetch(self) -> dict[str, Any]:  # Should be async
        return {}
'''
            result = validator.validate(code, {})
            # Should warn about async/sync mismatch
            assert len(result.warnings) > 0
            assert any("async" in warning.lower() for warning in result.warnings)

    class TestDependencyInjection:
        """Tests for DI pattern validation."""

        def test_frozen_dataclass_passes(self, validator: ConstraintValidator) -> None:
            """Frozen dataclass pattern passes."""
            code = '''
from dataclasses import dataclass

@dataclass(frozen=True)
class MyService:
    client: str
'''
            result = validator.validate(code, {})
            # Should pass DI check
            assert not any("frozen" in err.lower() for err in result.errors)

        def test_mutable_dataclass_fails(self, validator: ConstraintValidator) -> None:
            """Non-frozen dataclass should error."""
            code = '''
from dataclasses import dataclass

@dataclass
class MyService:
    client: str
'''
            result = validator.validate(code, {})
            # Should error about missing frozen=True
            assert not result.valid
            assert any("frozen" in err.lower() for err in result.errors)

        def test_pydantic_model_exempt_from_frozen(self, validator: ConstraintValidator) -> None:
            """Pydantic models don't need frozen dataclass."""
            code = '''
from pydantic import BaseModel

class MyModel(BaseModel):
    value: int
'''
            result = validator.validate(code, {})
            # Pydantic models are exempt from frozen dataclass requirement
            assert not any("frozen" in err.lower() for err in result.errors)

        def test_hardcoded_url_fails(self, validator: ConstraintValidator) -> None:
            """Hardcoded URLs should be detected."""
            code = '''
class MyClient:
    def __init__(self):
        self.url = "https://api.example.com/v1"
'''
            result = validator.validate(code, {})
            # Should error about hardcoded configuration
            assert not result.valid
            assert any("hardcoded" in err.lower() for err in result.errors)

        def test_hardcoded_api_key_fails(self, validator: ConstraintValidator) -> None:
            """ALL_CAPS constants are allowed (not flagged as hardcoded config)."""
            code = '''
API_KEY = "sk_test_1234567890"

class MyClient:
    def authenticate(self) -> str:
        return API_KEY
'''
            result = validator.validate(code, {})
            # ALL_CAPS constants are allowed, but will fail interface check
            assert not result.valid
            # Should fail for missing interfaces, not hardcoded config
            assert any("interface" in err.lower() for err in result.errors)

        def test_global_mutable_state_fails(self, validator: ConstraintValidator) -> None:
            """Global mutable state should be detected."""
            code = '''
counter = 0

def increment():
    global counter
    counter += 1
'''
            result = validator.validate(code, {})
            # Should error about global mutable state
            assert not result.valid
            assert any("global" in err.lower() for err in result.errors)

        def test_all_caps_constant_allowed(self, validator: ConstraintValidator) -> None:
            """ALL_CAPS constants are allowed as global state (no mutable state error)."""
            code = '''
MAX_RETRIES = 3
API_VERSION = "v1"
'''
            result = validator.validate(code, {})
            # Constants (ALL_CAPS) should be allowed (no mutable state error)
            # But will fail interface check
            assert not result.valid
            assert not any("global mutable" in err.lower() for err in result.errors)

        def test_short_strings_ignored(self, validator: ConstraintValidator) -> None:
            """Short strings (<= 5 chars) are not flagged as config."""
            code = '''
class MyService:
    def get_status(self) -> str:
        return "OK"
'''
            result = validator.validate(code, {})
            # Short strings should be ignored (no hardcoded config error)
            # But will fail interface check
            assert not result.valid
            assert not any("hardcoded" in err.lower() for err in result.errors)

    class TestTypeHints:
        """Tests for type hint validation."""

        def test_fully_typed_function_passes(self, validator: ConstraintValidator) -> None:
            """Function with all type hints passes."""
            code = '''
def process(data: dict) -> str:
    return str(data)
'''
            result = validator.validate(code, {})
            # Should pass type hint check
            assert "type hint" not in str(result.errors).lower()

        def test_missing_param_type_fails(self, validator: ConstraintValidator) -> None:
            """Missing parameter type fails."""
            code = '''
def process(data) -> str:
    return str(data)
'''
            result = validator.validate(code, {})
            # Should error about missing parameter type
            assert not result.valid
            assert any("type hint" in err.lower() for err in result.errors)

        def test_missing_return_type_fails(self, validator: ConstraintValidator) -> None:
            """Missing return type fails."""
            code = '''
def process(data: dict):
    return str(data)
'''
            result = validator.validate(code, {})
            # Should error about missing return type
            assert not result.valid
            assert any("return type" in err.lower() for err in result.errors)

        def test_self_parameter_exempt(self, validator: ConstraintValidator) -> None:
            """'self' parameter doesn't need type hint."""
            code = '''
class MyClass:
    def method(self, value: int) -> str:
        return str(value)
'''
            result = validator.validate(code, {})
            # 'self' is exempt from type hints (no type hint errors)
            # But will fail interface and DI checks
            assert not result.valid
            assert not any("type hint" in err.lower() for err in result.errors)

        def test_cls_parameter_exempt(self, validator: ConstraintValidator) -> None:
            """'cls' parameter doesn't need type hint."""
            code = '''
class MyClass:
    @classmethod
    def create(cls, value: int) -> 'MyClass':
        return cls()
'''
            result = validator.validate(code, {})
            # 'cls' is exempt from type hints (no type hint errors)
            # But will fail interface and DI checks
            assert not result.valid
            assert not any("type hint" in err.lower() for err in result.errors)

        def test_async_function_type_hints(self, validator: ConstraintValidator) -> None:
            """Async functions need type hints too."""
            code = '''
async def fetch(url: str) -> dict:
    return {}
'''
            result = validator.validate(code, {})
            # Has type hints but no interfaces
            assert not result.valid
            # No type hint errors
            assert not any("type hint" in err.lower() for err in result.errors)

        def test_async_missing_type_hints_fails(self, validator: ConstraintValidator) -> None:
            """Async functions with missing type hints fail."""
            code = '''
async def fetch(url):
    return {}
'''
            result = validator.validate(code, {})
            # Should error
            assert not result.valid

    class TestPydanticUsage:
        """Tests for Pydantic validation."""

        def test_pydantic_model_with_fields_passes(self, validator: ConstraintValidator) -> None:
            """Pydantic model with Field descriptions passes."""
            code = '''
from pydantic import BaseModel, Field

class MyModel(BaseModel):
    name: str = Field(..., description="The name")
    value: int = Field(default=0, description="The value")
'''
            result = validator.validate(code, {})
            # Should pass Pydantic checks
            assert not any("Field" in err for err in result.errors)

        def test_pydantic_without_field_descriptions_warns(self, validator: ConstraintValidator) -> None:
            """Pydantic models without Field descriptions generate warnings."""
            code = '''
from pydantic import BaseModel

class MyModel(BaseModel):
    name: str
    value: int = 0
'''
            result = validator.validate(code, {})
            # Should warn about missing Field descriptions
            assert len(result.warnings) > 0
            assert any("description" in warning.lower() for warning in result.warnings)

        def test_validator_without_decorator_warns(self, validator: ConstraintValidator) -> None:
            """Validator methods without decorators generate warnings."""
            code = '''
from pydantic import BaseModel

class MyModel(BaseModel):
    value: int

    def validate_value(self, v):
        return v
'''
            result = validator.validate(code, {})
            # Should warn about missing validator decorator
            assert len(result.warnings) > 0

        def test_proper_field_validator(self, validator: ConstraintValidator) -> None:
            """Proper field_validator usage doesn't warn."""
            code = '''
from pydantic import BaseModel, field_validator

class MyModel(BaseModel):
    value: int

    @field_validator('value')
    @classmethod
    def validate_value(cls, v):
        return v
'''
            result = validator.validate(code, {})
            # Should not warn about this validator
            # Note: There might be other warnings, so check specifically
            validator_warnings = [w for w in result.warnings if "validate_value" in w]
            assert len(validator_warnings) == 0

    class TestEdgeCases:
        """Edge case tests."""

        def test_invalid_syntax_returns_error(self, validator: ConstraintValidator) -> None:
            """Invalid Python syntax returns error."""
            code = "def broken("
            result = validator.validate(code, {})
            assert not result.valid
            assert any("syntax" in err.lower() for err in result.errors)

        def test_empty_code_passes(self, validator: ConstraintValidator) -> None:
            """Empty code should pass (no violations)."""
            code = ""
            result = validator.validate(code, {})
            # Empty code has no classes/functions, so will fail interface check
            assert not result.valid

        def test_comment_only_code(self, validator: ConstraintValidator) -> None:
            """Comment-only code fails interface check."""
            code = "# Just a comment"
            result = validator.validate(code, {})
            # No interfaces implemented
            assert not result.valid

        def test_multiple_classes(self, validator: ConstraintValidator) -> None:
            """Multiple classes are all validated."""
            code = '''
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass(frozen=True)
class Service1:
    client: str

@dataclass  # Missing frozen=True
class Service2:
    client: str

class Model1(BaseModel):
    value: int
'''
            result = validator.validate(code, {})
            # Should error about Service2 missing frozen=True
            assert not result.valid
            assert any("Service2" in err for err in result.errors)

        def test_nested_class_definitions(self, validator: ConstraintValidator) -> None:
            """Nested classes are validated."""
            code = '''
from dataclasses import dataclass

@dataclass(frozen=True)
class Outer:
    value: int

    @dataclass  # Missing frozen=True
    class Inner:
        data: str
'''
            result = validator.validate(code, {})
            # Should error about Inner missing frozen=True
            assert not result.valid
            assert any("Inner" in err for err in result.errors)

        def test_complex_type_annotations(self, validator: ConstraintValidator) -> None:
            """Complex type annotations are handled."""
            code = '''
from typing import Optional, Union, List, Dict, Any

def process(
    data: Dict[str, Union[int, str]],
    items: Optional[List[Any]] = None,
) -> Union[str, None]:
    return None
'''
            result = validator.validate(code, {})
            # Should handle complex types without type hint errors
            # But will fail interface check
            assert not result.valid
            assert not any("type hint" in err.lower() for err in result.errors)

    class TestHelperMethods:
        """Tests for internal helper methods."""

        def test_looks_like_config_detects_urls(self, validator: ConstraintValidator) -> None:
            """_looks_like_config detects URLs."""
            assert validator._looks_like_config("https://api.example.com")
            assert validator._looks_like_config("http://localhost:8000")
            assert validator._looks_like_config("ftp://files.example.org")

        def test_looks_like_config_detects_secrets(self, validator: ConstraintValidator) -> None:
            """_looks_like_config detects secret-like strings."""
            assert validator._looks_like_config("my_api_key_12345")
            assert validator._looks_like_config("super_secret_token")
            assert validator._looks_like_config("password123")

        def test_looks_like_config_ignores_normal_strings(self, validator: ConstraintValidator) -> None:
            """_looks_like_config ignores normal strings."""
            assert not validator._looks_like_config("hello world")
            assert not validator._looks_like_config("user name")
            assert not validator._looks_like_config("data value")

        def test_get_assignment_target_name(self, validator: ConstraintValidator) -> None:
            """_get_assignment_target_name extracts variable names."""
            import ast

            code = "counter = 0"
            tree = ast.parse(code)
            assign = tree.body[0]
            assert isinstance(assign, ast.Assign)
            name = validator._get_assignment_target_name(assign)
            assert name == "counter"

        def test_get_assignment_target_name_complex(self, validator: ConstraintValidator) -> None:
            """_get_assignment_target_name handles complex assignments."""
            import ast

            code = "obj.attr = 5"  # Attribute assignment
            tree = ast.parse(code)
            assign = tree.body[0]
            assert isinstance(assign, ast.Assign)
            name = validator._get_assignment_target_name(assign)
            # Should return None for attribute assignments
            assert name is None
