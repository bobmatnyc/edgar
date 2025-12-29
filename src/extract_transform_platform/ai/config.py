"""
AI Configuration for Extract Transform Platform

Handles API keys, model selection, and other AI-related configuration.

Design Decisions:
- **Environment-First**: API keys from environment variables
- **Sensible Defaults**: Works out-of-the-box with minimal config
- **Validation**: Validates configuration before use
- **Type Safety**: Full type hints and Pydantic models

Usage:
    >>> from extract_transform_platform.ai.config import AIConfig
    >>> config = AIConfig.from_env()
    >>> print(config.model)
    'anthropic/claude-sonnet-4.5'
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


class AIConfig(BaseModel):
    """
    Configuration for AI integration.

    Handles API keys, model selection, and other AI-related settings.

    Example:
        >>> config = AIConfig.from_env()
        >>> config = AIConfig(api_key="sk-or-v1-...", model="anthropic/claude-sonnet-4.5")
    """

    api_key: str = Field(..., description="OpenRouter API key")

    model: str = Field(
        default="anthropic/claude-sonnet-4.5", description="Default model identifier"
    )

    base_url: str = Field(
        default="https://openrouter.ai/api/v1", description="OpenRouter API base URL"
    )

    timeout: int = Field(
        default=120, description="Request timeout in seconds", ge=1, le=600
    )

    max_retries: int = Field(
        default=3, description="Maximum retry attempts", ge=0, le=10
    )

    temperature: float = Field(
        default=0.3,
        description="Default sampling temperature for pattern detection",
        ge=0.0,
        le=2.0,
    )

    confidence_threshold: Optional[float] = Field(
        default=None,
        description="Minimum confidence threshold for pattern detection (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key format."""
        if not v or len(v) < 10:
            raise ValueError("API key must be at least 10 characters")
        return v

    @classmethod
    def from_env(
        cls, env_file: Optional[Path] = None, require_api_key: bool = True
    ) -> "AIConfig":
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional .env file to load (defaults to .env.local)
            require_api_key: Whether to require API key (default: True)

        Returns:
            AIConfig instance

        Raises:
            ValueError: If API key is required but not found

        Environment Variables:
            - OPENROUTER_API_KEY: OpenRouter API key (required)
            - OPENROUTER_MODEL: Default model (optional)
            - OPENROUTER_BASE_URL: API base URL (optional)
            - OPENROUTER_TIMEOUT: Request timeout (optional)
            - OPENROUTER_MAX_RETRIES: Max retry attempts (optional)
            - AI_TEMPERATURE: Default temperature (optional)
            - AI_CONFIDENCE_THRESHOLD: Min confidence threshold (optional)

        Example:
            >>> config = AIConfig.from_env()
            >>> # Or with custom .env file
            >>> config = AIConfig.from_env(env_file=Path(".env.production"))
        """
        # Load .env file if specified or default
        if env_file:
            load_dotenv(env_file)
        elif Path(".env.local").exists():
            load_dotenv(".env.local")
        elif Path(".env").exists():
            load_dotenv(".env")

        # Get API key
        api_key = os.getenv("OPENROUTER_API_KEY", "")

        if require_api_key and not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY environment variable is required. "
                "Set it in your environment or .env.local file."
            )

        # Get optional settings with defaults
        return cls(
            api_key=api_key or "not-set",  # Allow empty for optional usage
            model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5"),
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            timeout=int(os.getenv("OPENROUTER_TIMEOUT", "120")),
            max_retries=int(os.getenv("OPENROUTER_MAX_RETRIES", "3")),
            temperature=float(os.getenv("AI_TEMPERATURE", "0.3")),
            confidence_threshold=(
                float(os.getenv("AI_CONFIDENCE_THRESHOLD"))
                if os.getenv("AI_CONFIDENCE_THRESHOLD")
                else None
            ),
        )

    def to_client_kwargs(self) -> dict:
        """
        Convert config to kwargs for OpenRouterClient.

        Returns:
            Dictionary of kwargs for OpenRouterClient initialization

        Example:
            >>> config = AIConfig.from_env()
            >>> client = OpenRouterClient(**config.to_client_kwargs())
        """
        return {
            "api_key": self.api_key,
            "model": self.model,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }


# Convenience function for quick setup
def load_ai_config(env_file: Optional[Path] = None) -> AIConfig:
    """
    Load AI configuration from environment.

    This is a convenience function for quick setup.

    Args:
        env_file: Optional .env file path

    Returns:
        AIConfig instance

    Example:
        >>> from extract_transform_platform.ai.config import load_ai_config
        >>> config = load_ai_config()
    """
    return AIConfig.from_env(env_file=env_file)
