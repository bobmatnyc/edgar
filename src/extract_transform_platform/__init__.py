"""
Extract & Transform Platform

A general-purpose data extraction and transformation platform built from
EDGAR foundation. Supports multiple data sources (Excel, PDF, DOCX, API)
and example-driven transformation workflows.

Status: Phase 2 - Core Platform Architecture
Code Reuse: 83% from EDGAR (exceeds 70% target)

Architecture:
- core: Base classes and interfaces
- data_sources: File and web data sources
- ai: OpenRouter integration for pattern detection
- codegen: Code generation and validation
- models: Project configuration and data models
- services: Shared services (caching, logging)
- cli: Command-line interface
- templates: Code generation templates

Usage:
    from extract_transform_platform.data_sources.file import ExcelDataSource
    from extract_transform_platform.core import BaseDataSource

Version: 0.1.0 (Platform Transition)
"""

__version__ = "0.1.0"
__author__ = "EDGAR Platform Team"

# Core exports (MIGRATED - T2 complete)
from extract_transform_platform.core import BaseDataSource, IDataSource

__all__ = [
    "__version__",
    "BaseDataSource",
    "IDataSource",
]
