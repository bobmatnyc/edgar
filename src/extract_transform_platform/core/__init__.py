"""
Core Module - Base Classes and Interfaces

Provides foundational abstractions for the extract & transform platform.

Key Components:
- BaseDataSource: Abstract base class for all data sources
- IDataSource: Protocol defining data source interface

Status: MIGRATED from edgar_analyzer.data_sources.base (100% generic)
"""

from extract_transform_platform.core.base import BaseDataSource, IDataSource

__all__ = [
    "BaseDataSource",
    "IDataSource",
]
