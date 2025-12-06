"""Custom exceptions for code generation pipeline with user-friendly error messages."""


class CodeGenerationError(Exception):
    """Base exception for code generation failures with actionable guidance."""

    def __init__(
        self, message: str, suggestions: list[str] = None, context: dict = None
    ):
        self.suggestions = suggestions or []
        self.context = context or {}

        full_message = f"{message}\n"
        if self.suggestions:
            full_message += "\n💡 Troubleshooting:\n"
            for i, suggestion in enumerate(self.suggestions, 1):
                full_message += f"  {i}. {suggestion}\n"

        super().__init__(full_message)


class CodeValidationError(CodeGenerationError):
    """Code validation failed after generation."""

    def __init__(self, issues: list[str], attempts: int, project_name: str):
        message = f"❌ Generated code for '{project_name}' failed quality validation after {attempts} attempts"

        suggestions = [
            f"Review the following validation issues: {', '.join(issues)}",
            "Check your examples for inconsistencies or missing required fields",
            "Try using --skip-validation flag to generate code anyway",
            "Review project.yaml configuration for accuracy",
            f"See docs/guides/TROUBLESHOOTING.md for common validation issues",
        ]

        super().__init__(message, suggestions, {"issues": issues, "attempts": attempts})


class OpenRouterAPIError(CodeGenerationError):
    """OpenRouter API request failed."""

    def __init__(
        self, status_code: int = None, error_message: str = "", endpoint: str = ""
    ):
        if status_code == 401:
            message = "🔑 OpenRouter API authentication failed"
            suggestions = [
                "Check that OPENROUTER_API_KEY is set in .env.local",
                "Verify your API key is valid at https://openrouter.ai/keys",
                "Ensure .env.local is in the project root directory",
                "Run: edgar-cli setup --test openrouter",
            ]
        elif status_code == 429:
            message = "⏱️  OpenRouter API rate limit exceeded"
            suggestions = [
                "Wait 60 seconds and try again",
                "Check your rate limits at https://openrouter.ai/activity",
                "Consider upgrading your OpenRouter plan",
                "Use --skip-validation to reduce API calls",
            ]
        elif status_code and 500 <= status_code < 600:
            message = f"🔧 OpenRouter API server error ({status_code})"
            suggestions = [
                "OpenRouter service may be experiencing issues",
                "Check status at https://status.openrouter.ai",
                "Wait a few minutes and try again",
                "Save your work and retry later",
            ]
        else:
            message = f"🌐 OpenRouter API request failed: {error_message}"
            suggestions = [
                "Check your internet connection",
                "Verify firewall isn't blocking openrouter.ai",
                "Try again in a few moments",
                "Check OpenRouter status: https://status.openrouter.ai",
            ]

        super().__init__(
            message, suggestions, {"status_code": status_code, "endpoint": endpoint}
        )


class PlanGenerationError(CodeGenerationError):
    """PM mode planning failed."""

    def __init__(self, reason: str, examples_count: int):
        message = f"📋 Implementation plan generation failed: {reason}"

        suggestions = [
            f"Verify your {examples_count} examples have consistent structure",
            "Ensure all required fields are present in examples",
            "Check that input/output pairs are valid JSON",
            "Try with 2-3 simple examples first to validate approach",
            "See examples/weather_api/ for working example format",
        ]

        super().__init__(
            message, suggestions, {"reason": reason, "examples_count": examples_count}
        )


class ExampleParsingError(CodeGenerationError):
    """Example file parsing failed."""

    def __init__(self, file_path: str, parse_error: str):
        message = f"📄 Failed to parse example file: {file_path}"

        suggestions = [
            f"Error details: {parse_error}",
            "Validate JSON syntax using: python -m json.tool your_file.json",
            "Check for missing commas, unmatched brackets, or quotes",
            "Ensure file encoding is UTF-8",
            "See examples/weather_api/ for correct format",
        ]

        super().__init__(
            message, suggestions, {"file_path": file_path, "parse_error": parse_error}
        )


class FileWriteError(CodeGenerationError):
    """File write operation failed."""

    def __init__(self, file_path: str, error: str):
        message = f"💾 Failed to write file: {file_path}"

        suggestions = [
            f"Error: {error}",
            "Check write permissions for the output directory",
            "Ensure parent directory exists",
            "Verify disk space is available",
            f"Try writing to a different location using --output-dir",
        ]

        super().__init__(message, suggestions, {"file_path": file_path, "error": error})
