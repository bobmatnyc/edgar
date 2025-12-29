"""
Pydantic models for Summary Compensation Table (SCT) data extraction.

These models define the structure for executive compensation data
extracted from SEC DEF 14A proxy filings.

Design Decisions:
- **Schema Validation**: Strict typing matches SEC disclosure requirements
- **Optional Fields**: Bonus, Option Awards, Pension often missing (default 0)
- **Nested Structure**: compensation_by_year allows multi-year tracking
- **Metadata**: Extraction tracking for quality assurance

Example:
    >>> exec_comp = ExecutiveCompensation(
    ...     name="Tim Cook",
    ...     position="Chief Executive Officer",
    ...     fiscal_year=2024,
    ...     salary=3000000,
    ...     stock_awards=58088946,
    ...     total=74609802
    ... )
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class CompensationYear(BaseModel):
    """Compensation data for a single fiscal year.

    Represents one row in the Summary Compensation Table for an executive.
    All monetary values are in USD (integer, no decimals).

    SEC Column Mapping:
    - Salary: Base salary
    - Bonus: Annual bonus (often blank/0)
    - Stock Awards: Fair value of stock grants
    - Option Awards: Fair value of option grants (often blank/0)
    - Non-Equity Incentive: Performance-based cash compensation
    - Change in Pension: Pension value changes (often blank/0)
    - All Other Compensation: Perks, benefits, 401k matching, etc.
    - Total: Sum of all components (must match sum)
    """

    year: int = Field(..., description="Fiscal year", ge=2000, le=2100)

    salary: int = Field(default=0, description="Base salary ($)", ge=0)

    bonus: int = Field(default=0, description="Annual bonus ($)", ge=0)

    stock_awards: int = Field(default=0, description="Stock awards ($)", ge=0)

    option_awards: int = Field(default=0, description="Option awards ($)", ge=0)

    non_equity_incentive: int = Field(
        default=0,
        description="Non-equity incentive plan compensation ($)",
        ge=0
    )

    change_in_pension: int = Field(
        default=0,
        description="Change in pension value ($)",
        ge=0
    )

    all_other_compensation: int = Field(
        default=0,
        description="All other compensation ($)",
        ge=0
    )

    total: int = Field(..., description="Total compensation ($)", ge=0)

    footnotes: List[str] = Field(
        default_factory=list,
        description="Footnote reference IDs (e.g., ['3', '4'])"
    )

    @field_validator('total')
    @classmethod
    def validate_total(cls, v: int, info) -> int:
        """Validate that total equals sum of components (±$1 tolerance).

        Note: We allow ±$1 tolerance for rounding differences in SEC filings.
        """
        if not info.data:
            return v

        calculated_total = (
            info.data.get('salary', 0) +
            info.data.get('bonus', 0) +
            info.data.get('stock_awards', 0) +
            info.data.get('option_awards', 0) +
            info.data.get('non_equity_incentive', 0) +
            info.data.get('change_in_pension', 0) +
            info.data.get('all_other_compensation', 0)
        )

        # Allow ±$1 tolerance for rounding
        if abs(v - calculated_total) > 1:
            raise ValueError(
                f"Total mismatch: expected {calculated_total}, got {v} "
                f"(difference: ${abs(v - calculated_total)})"
            )

        return v


class ExecutiveCompensation(BaseModel):
    """Named Executive Officer (NEO) with multi-year compensation data.

    Typically covers 3 fiscal years (most recent completed years).
    Each executive has 1-3 CompensationYear entries.

    CEO/CFO flags identify Principal Executive Officer (PEO) and
    Principal Financial Officer (PFO) as required by SEC.
    """

    name: str = Field(..., description="Executive full name")

    position: str = Field(..., description="Executive title/position")

    is_ceo: bool = Field(
        default=False,
        description="True if CEO or Principal Executive Officer"
    )

    is_cfo: bool = Field(
        default=False,
        description="True if CFO or Principal Financial Officer"
    )

    compensation_by_year: List[CompensationYear] = Field(
        ...,
        description="Compensation data for each fiscal year (1-3 years)",
        min_length=1,
        max_length=3
    )


class SCTData(BaseModel):
    """Complete Summary Compensation Table from DEF 14A proxy filing.

    Contains compensation data for all Named Executive Officers (NEOs)
    across 3 fiscal years (typically).

    Typical structure:
    - 5 NEOs (CEO, CFO, 3 most highly compensated officers)
    - 3 fiscal years per NEO
    - Total: 15 compensation records

    Validation:
    - All executives must have at least 1 year of data
    - Total compensation must match sum of components
    - Fiscal years must be in valid range (2000-2100)
    """

    company_name: str = Field(..., description="Company legal name")

    ticker: str = Field(
        ...,
        description="Stock ticker symbol",
        pattern=r"^[A-Z]{1,5}$"
    )

    cik: str = Field(
        ...,
        description="SEC Central Index Key (10 digits)",
        pattern=r"^[0-9]{10}$"
    )

    filing_date: str = Field(
        ...,
        description="DEF 14A filing date (YYYY-MM-DD)",
        pattern=r"^\d{4}-\d{2}-\d{2}$"
    )

    filing_url: Optional[str] = Field(
        default=None,
        description="SEC EDGAR URL for DEF 14A filing"
    )

    fiscal_years: List[int] = Field(
        ...,
        description="Fiscal years covered (e.g., [2024, 2023, 2022])",
        min_length=1,
        max_length=3
    )

    executives: List[ExecutiveCompensation] = Field(
        ...,
        description="Named Executive Officers (typically 5)",
        min_length=1,
        max_length=10
    )

    footnotes: dict[str, str] = Field(
        default_factory=dict,
        description="Footnote definitions (ID -> description)"
    )

    extraction_metadata: dict = Field(
        default_factory=dict,
        description="Extraction process metadata"
    )

    @field_validator('executives')
    @classmethod
    def validate_executives(cls, v: List[ExecutiveCompensation]) -> List[ExecutiveCompensation]:
        """Validate executive data consistency."""
        if not v:
            raise ValueError("Must have at least 1 executive")

        # Check for exactly 1 CEO and 1 CFO (typical)
        ceo_count = sum(1 for exec in v if exec.is_ceo)
        cfo_count = sum(1 for exec in v if exec.is_cfo)

        # Warn but don't fail (some filings may have variations)
        if ceo_count != 1:
            # This is informational, not a hard failure
            pass

        if cfo_count > 1:
            raise ValueError(f"Found {cfo_count} CFOs, expected 0-1")

        return v

    def get_ceo(self) -> Optional[ExecutiveCompensation]:
        """Get CEO/Principal Executive Officer."""
        for exec in self.executives:
            if exec.is_ceo:
                return exec
        return None

    def get_cfo(self) -> Optional[ExecutiveCompensation]:
        """Get CFO/Principal Financial Officer."""
        for exec in self.executives:
            if exec.is_cfo:
                return exec
        return None

    def get_total_compensation_for_year(self, year: int) -> int:
        """Calculate total compensation across all executives for a given year."""
        total = 0
        for exec in self.executives:
            for comp_year in exec.compensation_by_year:
                if comp_year.year == year:
                    total += comp_year.total
        return total


class SCTExtractionResult(BaseModel):
    """Result of SCT extraction operation.

    Wraps SCTData with success/error status and metadata.
    Used for API responses and error handling.
    """

    success: bool = Field(..., description="Whether extraction succeeded")

    data: Optional[SCTData] = Field(
        default=None,
        description="Extracted SCT data (if successful)"
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

    tokens_used: Optional[dict[str, int]] = Field(
        default=None,
        description="Token usage (input/output)"
    )
