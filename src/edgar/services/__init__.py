"""Core AI services for EDGAR platform.

This module contains the main services for AI-powered code generation:
- Sonnet4_5Service: Main orchestrator for PM and Coder modes
- OpenRouterClient: API client for OpenRouter integration
- ContextManager: Conversation context management
"""

from edgar.services.sonnet_service import Sonnet4_5Service
from edgar.services.openrouter_client import OpenRouterClient
from edgar.services.context_manager import ContextManager

__all__ = [
    "Sonnet4_5Service",
    "OpenRouterClient",
    "ContextManager",
]
