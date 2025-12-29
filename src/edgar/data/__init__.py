"""Fortune 100 Company Registry data module.

This module provides access to Fortune 100 company data with SEC EDGAR CIKs,
enabling efficient lookup and filtering operations for regulatory filings.
"""

from edgar.data.fortune100 import Company, Fortune100Registry

__all__ = [
    "Company",
    "Fortune100Registry",
]
