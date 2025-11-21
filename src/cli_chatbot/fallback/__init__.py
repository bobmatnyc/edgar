"""Fallback CLI interface using Click when LLM is unavailable."""

from .traditional_cli import TraditionalCLI, create_fallback_cli

__all__ = ["TraditionalCLI", "create_fallback_cli"]
