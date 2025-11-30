"""
Core Module - Base Classes and Interfaces

Provides foundational abstractions for the extract & transform platform.

Key Components:
- BaseDataSource: Abstract base class for all data sources
- IDataSource: Protocol defining data source interface
- IDataExtractor: Abstract interface for generated extractors (T6)

Status: MIGRATED from edgar_analyzer.data_sources.base (100% generic)

Migration Status: T6 (1M-381 - IDataExtractor Interface Definition)
- Added IDataExtractor export for code generation consistency
"""

from extract_transform_platform.core.base import BaseDataSource, IDataSource, IDataExtractor

__all__ = [
    "BaseDataSource",
    "IDataSource",
    "IDataExtractor",
]
