"""Edgar Analyzer data module."""

from edgar_analyzer.data.fortune100_loader import (
    Company,
    Fortune100Registry,
    load_fortune100_registry,
)

__all__ = [
    "Company",
    "Fortune100Registry",
    "load_fortune100_registry",
]
