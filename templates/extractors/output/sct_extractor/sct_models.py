"""
Pydantic models for sct data extraction.

These models define the structure for sct data
extracted from SEC filings.

Design Decisions:
- **Schema Validation**: Strict typing matches disclosure requirements
- **Optional Fields**: Some fields may be missing (defaults provided)
- **Nested Structure**: Supports hierarchical data
- **Metadata**: Extraction tracking for quality assurance

Example:
    >>> data = CompensationYear(
    ...     # Field values here
    ... )
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class CompensationYear(BaseModel):
    """Compensation data for a single fiscal year


    Notes:
    Represents one row in the Summary Compensation Table for an executive.
    All monetary values are in USD (integer, no decimals).

    """

    year: int = Field(..., description="Fiscal year", ge=2000, le=2100)

    salary: int = Field(default=0, description="Base salary ($)", ge=0)

    bonus: int = Field(default=0, description="Annual bonus ($)", ge=0)

    stock_awards: int = Field(default=0, description="Stock awards ($)", ge=0)

    total: int = Field(..., description="Total compensation ($)", ge=0)

    @field_validator("total")
    @classmethod
    def validate_total(cls, v: int, info) -> int:
        """Validate that total equals sum of components"""
        if not info.data:
            return v

        calculated_total = (
            info.data.get("salary", 0)
            + info.data.get("bonus", 0)
            + info.data.get("stock_awards", 0)
        )

        if abs(v - calculated_total) > 1:
            raise ValueError(f"Total mismatch: expected {calculated_total}, got {v}")

        return v
        return v


class ExecutiveCompensation(BaseModel):
    """Named Executive Officer with multi-year compensation data"""

    name: str = Field(..., description="Executive full name")

    position: str = Field(..., description="Executive title/position")

    is_ceo: bool = Field(
        default=False, description="True if CEO or Principal Executive Officer"
    )

    compensation_by_year: List[CompensationYear] = Field(
        ...,
        description="Compensation data for each fiscal year",
        min_length=1,
        max_length=3,
    )


class SCTData(BaseModel):
    """Complete Summary Compensation Table from DEF 14A proxy filing"""

    company_name: str = Field(..., description="Company legal name")

    ticker: str = Field(..., description="Stock ticker symbol", pattern=r"^[A-Z]{1,5}$")

    cik: str = Field(
        ..., description="SEC Central Index Key (10 digits)", pattern=r"^[0-9]{10}$"
    )

    executives: List[ExecutiveCompensation] = Field(
        ...,
        description="Named Executive Officers (typically 5)",
        min_length=1,
        max_length=10,
    )

    def get_ceo(self) -> Optional[ExecutiveCompensation]:
        """Get CEO/Principal Executive Officer."""
        for exec in self.executives:
            if exec.is_ceo:
                return exec
        return None


class SCTExtractionResult(BaseModel):
    """Result of sct extraction operation.

    Wraps data with success/error status and metadata.
    Used for API responses and error handling.
    """

    success: bool = Field(..., description="Whether extraction succeeded")

    data: Optional[SCTData] = Field(
        default=None, description="Extracted sct data (if successful)"
    )

    error_message: Optional[str] = Field(
        default=None, description="Error message (if failed)"
    )

    extraction_time_seconds: float = Field(
        default=0.0, description="Time taken for extraction"
    )

    model_used: str = Field(default="", description="LLM model identifier")

    tokens_used: Optional[dict[str, int]] = Field(
        default=None, description="Token usage (input/output)"
    )
