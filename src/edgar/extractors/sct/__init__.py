"""Summary Compensation Table extractor."""

from edgar.extractors.sct.extractor import SCTExtractor
from edgar.extractors.sct.models import ExecutiveCompensation, SCTData

__all__ = ["SCTExtractor", "ExecutiveCompensation", "SCTData"]
