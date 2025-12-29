"""
Pydantic models for patent data extraction.

These models define the structure for patent data
extracted from SEC filings.

Design Decisions:
- **Schema Validation**: Strict typing matches disclosure requirements
- **Optional Fields**: Some fields may be missing (defaults provided)
- **Nested Structure**: Supports hierarchical data
- **Metadata**: Extraction tracking for quality assurance

Example:
    >>> data = ExtractedData(
    ...     # Field values here
    ... )
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ExtractedData(BaseModel):
    """Main data model for patent filing information"""

    patent_number: str = Field(..., description="Patent number (e.g., US11234567B2)")
    title: str = Field(..., description="Patent title")
    inventors: List[str] = Field(..., description="List of inventor names")
    assignee: str = Field(..., description="Assignee/company name")
    filing_date: str = Field(..., description="Filing date (YYYY-MM-DD)")
    grant_date: str = Field(..., description="Grant date (YYYY-MM-DD)")
    claims_count: int = Field(..., description="Total number of claims", ge=0)
    abstract: str = Field(..., description="Patent abstract text")
    status: str = Field(..., description="Legal status (e.g., Active, Expired)")
    classifications: List[str] = Field(
        default_factory=list,
        description="CPC/IPC classification codes"
    )


class ExtractedDataExtractionResult(BaseModel):
    """Result of patent extraction operation.

    Wraps data with success/error status and metadata.
    Used for API responses and error handling.
    """

    success: bool = Field(..., description="Whether extraction succeeded")

    data: Optional[ExtractedData] = Field(
        default=None,
        description="Extracted patent data (if successful)"
    )

    error_message: Optional[str] = Field(
        default=None,
        description="Error message (if failed)"
    )

    extraction_time_seconds: float = Field(
        default=0.0,
        description="Time taken for extraction"
    )

    model_used: str = Field(
        default="",
        description="LLM model identifier"
    )

    tokens_used: Optional[dict] = Field(
        default=None,
        description="Token usage (input/output)"
    )
