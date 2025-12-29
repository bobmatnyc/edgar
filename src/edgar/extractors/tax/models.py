"""Data models for income tax extraction from 10-K filings."""

from pydantic import BaseModel, Field


class TaxYear(BaseModel):
    """Corporate tax data for a single fiscal year."""

    year: int = Field(..., description="Fiscal year")

    # Income Tax Expense breakdown
    current_federal: float = Field(default=0.0, description="Current federal income tax")
    current_state: float = Field(default=0.0, description="Current state income tax")
    current_foreign: float = Field(default=0.0, description="Current foreign income tax")
    deferred_federal: float = Field(default=0.0, description="Deferred federal income tax")
    deferred_state: float = Field(default=0.0, description="Deferred state income tax")
    deferred_foreign: float = Field(default=0.0, description="Deferred foreign income tax")

    total_current: float = Field(default=0.0, description="Total current tax expense")
    total_deferred: float = Field(default=0.0, description="Total deferred tax expense")
    total_tax_expense: float = Field(default=0.0, description="Total income tax expense")

    # For ratio calculations
    pretax_income: float = Field(default=0.0, description="Pre-tax income")
    effective_tax_rate: float = Field(default=0.0, description="Effective tax rate (0-1)")

    # Cash taxes (from cash flow statement)
    cash_taxes_paid: float = Field(default=0.0, description="Actual cash taxes paid")


class TaxData(BaseModel):
    """Corporate tax data extracted from 10-K filing."""

    company: str = Field(default="", description="Company name")
    cik: str = Field(default="", description="SEC CIK number")
    filing_date: str = Field(default="", description="10-K filing date")
    fiscal_year_end: str = Field(default="", description="Fiscal year end date")

    tax_years: list[TaxYear] = Field(default_factory=list, description="Multi-year tax data")

    @property
    def latest_tax_expense(self) -> float:
        """Get most recent year's total tax expense."""
        if self.tax_years:
            return self.tax_years[0].total_tax_expense
        return 0.0

    @property
    def latest_effective_rate(self) -> float:
        """Get most recent year's effective tax rate."""
        if self.tax_years:
            return self.tax_years[0].effective_tax_rate
        return 0.0
