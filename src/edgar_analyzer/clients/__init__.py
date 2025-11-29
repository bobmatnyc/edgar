"""
Client modules for external API interactions.

BACKWARD COMPATIBILITY WRAPPER:
This module now imports from extract_transform_platform.ai for code reuse.
All existing EDGAR code continues to work without changes.

Migration Status:
- ✅ OpenRouterClient migrated to platform (100% code reuse)
- ✅ Backward compatibility maintained
- ✅ All imports work as before

Usage (unchanged):
    >>> from edgar_analyzer.clients import OpenRouterClient
    >>> client = OpenRouterClient(api_key="...")
"""

# Import from platform (migration complete)
from extract_transform_platform.ai import (
    OpenRouterClient,
    OpenRouterConfig,
    ModelCapabilities,
)

__all__ = [
    "OpenRouterClient",
    "OpenRouterConfig",
    "ModelCapabilities",
]
