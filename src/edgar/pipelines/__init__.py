"""Pipeline modules for EDGAR data extraction and analysis.

This package contains the core pipeline logic that can be invoked via:
- CLI: `edgar fortune100 --companies 1-100`
- Notebooks: Interactive exploration and visualization
- Streamlit: (future) Interactive dashboard
"""

from edgar.pipelines.fortune100 import (
    Fortune100Pipeline,
    PipelineConfig,
    PipelineResult,
)

__all__ = [
    "Fortune100Pipeline",
    "PipelineConfig",
    "PipelineResult",
]
