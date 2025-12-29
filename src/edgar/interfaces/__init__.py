"""Interface definitions for EDGAR platform.

This package contains Protocol interfaces that define contracts
for data sources and extractors.
"""

from edgar.interfaces.data_extractor import IDataExtractor, IDataSource

__all__ = ["IDataExtractor", "IDataSource"]
