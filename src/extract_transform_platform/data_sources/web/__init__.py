"""
Web Data Sources

Data source implementations for web-based data.

Supported Protocols:
- Simple URL (public HTTP/HTTPS endpoints)
- REST API (generic HTTP/JSON)
- Jina.ai (JS-heavy web scraping)

Status: Week 2, Phase 1 - Migration in progress
"""

from extract_transform_platform.data_sources.web.api_source import APIDataSource
from extract_transform_platform.data_sources.web.jina_source import JinaDataSource
from extract_transform_platform.data_sources.web.url_source import URLDataSource

__all__ = [
    "URLDataSource",
    "APIDataSource",
    "JinaDataSource",
]
