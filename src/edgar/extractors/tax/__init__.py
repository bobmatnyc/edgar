"""Income tax extractor."""

from edgar.extractors.tax.extractor import TaxExtractor
from edgar.extractors.tax.models import TaxData, TaxYear

__all__ = ["TaxExtractor", "TaxData", "TaxYear"]
