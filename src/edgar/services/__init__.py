"""Core AI services for EDGAR platform.

This module contains the main services for AI-powered code generation:
- Sonnet4_5Service: Main orchestrator for PM and Coder modes
- OpenRouterClient: API client for OpenRouter integration
- ContextManager: Conversation context management
- SecEdgarClient: SEC EDGAR API client for fetching filings
- PatternAnalyzer: Detects transformation patterns from examples
"""

from edgar.services.sonnet_service import Sonnet4_5Service
from edgar.services.openrouter_client import OpenRouterClient
from edgar.services.context_manager import ContextManager
from edgar.services.sec_edgar_client import (
    SecEdgarClient,
    parse_summary_compensation_table,
)
from edgar.services.pattern_analyzer import PatternAnalyzer

__all__ = [
    "Sonnet4_5Service",
    "OpenRouterClient",
    "ContextManager",
    "SecEdgarClient",
    "parse_summary_compensation_table",
    "PatternAnalyzer",
]
