"""Tests for custom code generation exceptions."""

import pytest

from extract_transform_platform.services.codegen.exceptions import (
    CodeValidationError,
    ExampleParsingError,
    FileWriteError,
    OpenRouterAPIError,
    PlanGenerationError,
)


class TestCodeValidationError:
    def test_includes_project_name_and_attempts(self):
        error = CodeValidationError(
            issues=["syntax error", "type error"],
            attempts=3,
            project_name="test_project",
        )

        error_str = str(error)
        assert "test_project" in error_str
        assert "3 attempts" in error_str
        assert "syntax error" in error_str

    def test_includes_troubleshooting_suggestions(self):
        error = CodeValidationError(issues=["error1"], attempts=1, project_name="test")

        assert "💡 Troubleshooting:" in str(error)
        assert "Review the following validation issues" in str(error)

    def test_context_stored(self):
        error = CodeValidationError(
            issues=["issue1", "issue2"], attempts=2, project_name="test_proj"
        )

        assert error.context["issues"] == ["issue1", "issue2"]
        assert error.context["attempts"] == 2

    def test_multiple_issues_joined(self):
        error = CodeValidationError(
            issues=["issue1", "issue2", "issue3"], attempts=3, project_name="test"
        )

        error_str = str(error)
        assert "issue1" in error_str
        assert "issue2" in error_str
        assert "issue3" in error_str


class TestOpenRouterAPIError:
    def test_auth_failure_401(self):
        error = OpenRouterAPIError(status_code=401, error_message="Unauthorized")
        error_str = str(error)

        assert "authentication failed" in error_str.lower()
        assert "OPENROUTER_API_KEY" in error_str
        assert ".env.local" in error_str

    def test_rate_limit_429(self):
        error = OpenRouterAPIError(status_code=429)
        error_str = str(error)

        assert "rate limit" in error_str.lower()
        assert "Wait 60 seconds" in error_str

    def test_server_error_500(self):
        error = OpenRouterAPIError(status_code=500)
        error_str = str(error)

        assert "server error" in error_str.lower()
        assert "status.openrouter.ai" in error_str

    def test_server_error_503(self):
        error = OpenRouterAPIError(status_code=503)
        error_str = str(error)

        assert "server error" in error_str.lower()
        assert "503" in error_str

    def test_generic_error(self):
        error = OpenRouterAPIError(error_message="Connection timeout")
        error_str = str(error)

        assert "Connection timeout" in error_str
        assert "internet connection" in error_str

    def test_context_includes_status_code(self):
        error = OpenRouterAPIError(status_code=401, endpoint="/v1/chat/completions")

        assert error.context["status_code"] == 401
        assert error.context["endpoint"] == "/v1/chat/completions"


class TestPlanGenerationError:
    def test_includes_reason_and_examples_count(self):
        error = PlanGenerationError(reason="Invalid schema", examples_count=3)
        error_str = str(error)

        assert "Invalid schema" in error_str
        assert "3 examples" in error_str
        assert "consistent structure" in error_str

    def test_includes_troubleshooting_suggestions(self):
        error = PlanGenerationError(reason="Parse error", examples_count=2)
        error_str = str(error)

        assert "💡 Troubleshooting:" in error_str
        assert "Verify your 2 examples" in error_str

    def test_context_stored(self):
        error = PlanGenerationError(reason="Schema mismatch", examples_count=5)

        assert error.context["reason"] == "Schema mismatch"
        assert error.context["examples_count"] == 5


class TestExampleParsingError:
    def test_includes_file_path_and_parse_error(self):
        error = ExampleParsingError(
            file_path="/path/to/file.json",
            parse_error="Expecting ',' delimiter: line 5 column 10",
        )
        error_str = str(error)

        assert "/path/to/file.json" in error_str
        assert "line 5 column 10" in error_str
        assert "json.tool" in error_str  # Suggests validation tool

    def test_includes_troubleshooting_suggestions(self):
        error = ExampleParsingError(
            file_path="example1.json", parse_error="Invalid JSON"
        )
        error_str = str(error)

        assert "💡 Troubleshooting:" in error_str
        assert "json.tool" in error_str
        assert "UTF-8" in error_str

    def test_context_stored(self):
        error = ExampleParsingError(file_path="test.json", parse_error="Parse error")

        assert error.context["file_path"] == "test.json"
        assert error.context["parse_error"] == "Parse error"


class TestFileWriteError:
    def test_includes_file_path_and_error(self):
        error = FileWriteError(
            file_path="/output/extractor.py", error="Permission denied"
        )
        error_str = str(error)

        assert "/output/extractor.py" in error_str
        assert "Permission denied" in error_str
        assert "write permissions" in error_str

    def test_includes_troubleshooting_suggestions(self):
        error = FileWriteError(file_path="output.py", error="No space left on device")
        error_str = str(error)

        assert "💡 Troubleshooting:" in error_str
        assert "disk space" in error_str
        assert "--output-dir" in error_str

    def test_context_stored(self):
        error = FileWriteError(file_path="/tmp/file.py", error="I/O error")

        assert error.context["file_path"] == "/tmp/file.py"
        assert error.context["error"] == "I/O error"


class TestCodeGenerationErrorBase:
    def test_suggestions_optional(self):
        from extract_transform_platform.services.codegen.exceptions import (
            CodeGenerationError,
        )

        error = CodeGenerationError("Test error")
        assert error.suggestions == []
        assert "💡 Troubleshooting:" not in str(error)

    def test_context_optional(self):
        from extract_transform_platform.services.codegen.exceptions import (
            CodeGenerationError,
        )

        error = CodeGenerationError("Test error")
        assert error.context == {}

    def test_suggestions_displayed(self):
        from extract_transform_platform.services.codegen.exceptions import (
            CodeGenerationError,
        )

        error = CodeGenerationError(
            "Test error", suggestions=["Suggestion 1", "Suggestion 2"]
        )
        error_str = str(error)

        assert "💡 Troubleshooting:" in error_str
        assert "1. Suggestion 1" in error_str
        assert "2. Suggestion 2" in error_str

    def test_context_stored(self):
        from extract_transform_platform.services.codegen.exceptions import (
            CodeGenerationError,
        )

        error = CodeGenerationError("Test error", context={"key": "value"})

        assert error.context["key"] == "value"
