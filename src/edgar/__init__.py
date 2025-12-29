"""EDGAR Platform - Example-Driven Generation with AI Reasoning.

AI-powered data extraction platform that generates production-ready Python code
from API response examples using Sonnet 4.5.
"""

from edgar.interfaces import IDataExtractor, IDataSource

__version__ = "0.1.0"

__all__ = ["IDataExtractor", "IDataSource", "__version__"]
