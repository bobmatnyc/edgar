"""
Data Source Abstraction Layer

Provides generic interfaces and implementations for various data sources:
- API sources (REST APIs)
- Jina.ai web content extraction
- File-based sources (JSON, YAML, CSV)
- Generic URL sources
- EDGAR-specific sources

All sources implement common interface with built-in:
- Caching
- Rate limiting
- Retry logic with exponential backoff
- Configuration validation
"""

from .base import IDataSource, BaseDataSource
from .api_source import APIDataSource
from .jina_source import JinaDataSource
from .file_source import FileDataSource
from .url_source import URLDataSource

__all__ = [
    "IDataSource",
    "BaseDataSource",
    "APIDataSource",
    "JinaDataSource",
    "FileDataSource",
    "URLDataSource",
]
