"""Data models for Summary Compensation Table extraction."""

from pydantic import BaseModel, Field


class CompensationYear(BaseModel):
    """Compensation data for a single fiscal year."""

    year: int = Field(..., description="Fiscal year")
    salary: float = Field(default=0.0, description="Base salary in USD")
    bonus: float = Field(default=0.0, description="Discretionary bonus in USD")
    stock_awards: float = Field(default=0.0, description="Stock awards grant date value in USD")
    option_awards: float = Field(default=0.0, description="Option awards value in USD")
    non_equity_incentive: float = Field(
        default=0.0, description="Non-equity incentive compensation in USD"
    )
    pension_change: float = Field(default=0.0, description="Change in pension value in USD")
    other_compensation: float = Field(default=0.0, description="All other compensation in USD")
    total: float = Field(default=0.0, description="Total compensation in USD")


class ExecutiveCompensation(BaseModel):
    """Executive compensation data."""

    name: str = Field(..., description="Executive name")
    title: str = Field(default="", description="Executive title/position")
    compensation: list[CompensationYear] = Field(
        default_factory=list, description="Yearly compensation data"
    )


class SCTData(BaseModel):
    """Summary Compensation Table extracted data."""

    company: str = Field(default="", description="Company name")
    cik: str = Field(default="", description="SEC CIK number")
    filing_date: str = Field(default="", description="Filing date")
    executives: list[ExecutiveCompensation] = Field(
        default_factory=list, description="List of executives"
    )

    @property
    def total_compensation(self) -> float:
        """Calculate total compensation across all executives for latest year."""
        total = 0.0
        for exec_data in self.executives:
            if exec_data.compensation:
                total += exec_data.compensation[0].total
        return total
