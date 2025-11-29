"""
AI Module - OpenRouter Integration

Provides AI-powered pattern detection and code generation via OpenRouter.

Components:
- OpenRouterClient: OpenRouter API client with error handling and retry logic
- PromptTemplates: Prompt templates for pattern detection (TODO)

Migration Status:
- ✅ OpenRouterClient migrated from edgar_analyzer (100% code reuse)
- 🔄 PromptTemplates in progress (Week 1, Phase 1)

Usage:
    >>> from extract_transform_platform.ai import OpenRouterClient
    >>> client = OpenRouterClient(api_key="sk-or-v1-...")
    >>> response = await client.chat_completion(
    ...     messages=[{"role": "user", "content": "Analyze pattern"}],
    ...     temperature=0.3
    ... )
"""

from extract_transform_platform.ai.openrouter_client import (
    OpenRouterClient,
    OpenRouterConfig,
    ModelCapabilities,
)
from extract_transform_platform.ai.prompt_templates import (
    PromptTemplates,
    EDGARPromptTemplates,
)
from extract_transform_platform.ai.config import (
    AIConfig,
    load_ai_config,
)

__all__ = [
    "OpenRouterClient",
    "OpenRouterConfig",
    "ModelCapabilities",
    "PromptTemplates",
    "EDGARPromptTemplates",
    "AIConfig",
    "load_ai_config",
]
