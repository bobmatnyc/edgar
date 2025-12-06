"""
AI Integration Services

Provides AI-powered code generation using Sonnet 4.5 and OpenRouter.

Components:
- OpenRouterClient: OpenRouter API client with error handling and retry logic (MIGRATED ✅)
- Sonnet45Agent: Dual-mode agent (PM + Coder) for code generation (MIGRATED ✅)
- PromptTemplates: Prompt templates for pattern detection (MIGRATED ✅)
- AIConfig: Configuration management (MIGRATED ✅)

Migration Status: COMPLETE (T5 - Extract Sonnet 4.5 AI Integration)
- OpenRouterClient: 471 LOC (100% code reuse)
- Sonnet45Agent: 753 LOC (100% code reuse)
- Total: 1,224 LOC migrated
- Tests: 0 breaking changes

Usage:
    >>> from extract_transform_platform.ai import OpenRouterClient, Sonnet45Agent
    >>> # Direct client usage
    >>> client = OpenRouterClient(api_key="sk-or-v1-...")
    >>> response = await client.chat_completion(
    ...     messages=[{"role": "user", "content": "Analyze pattern"}],
    ...     temperature=0.3
    ... )
    >>> # Or dual-mode agent
    >>> agent = Sonnet45Agent(api_key="sk-or-v1-...")
    >>> code = await agent.plan_and_code(patterns, project_config)
"""

from extract_transform_platform.ai.config import (
    AIConfig,
    load_ai_config,
)
from extract_transform_platform.ai.openrouter_client import (
    ModelCapabilities,
    OpenRouterClient,
    OpenRouterConfig,
)
from extract_transform_platform.ai.prompt_templates import (
    EDGARPromptTemplates,
    PromptTemplates,
)
from extract_transform_platform.ai.sonnet45_agent import Sonnet45Agent

__all__ = [
    "OpenRouterClient",
    "OpenRouterConfig",
    "ModelCapabilities",
    "Sonnet45Agent",
    "PromptTemplates",
    "EDGARPromptTemplates",
    "AIConfig",
    "load_ai_config",
]
