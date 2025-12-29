"""Analysis models for executive compensation vs. corporate tax comparison."""

from pydantic import BaseModel, Field


class CompTaxAnalysis(BaseModel):
    """Comparison analysis between executive compensation and corporate tax."""

    # Company info
    company: str = Field(..., description="Company name")
    ticker: str = Field(default="", description="Stock ticker")
    cik: str = Field(..., description="SEC CIK")
    rank: int = Field(default=0, description="Fortune 100 rank")
    fiscal_year: int = Field(..., description="Fiscal year analyzed")

    # Executive Compensation Metrics
    num_executives: int = Field(default=0, description="Number of named executives")
    total_exec_comp: float = Field(default=0.0, description="Sum of all NEO compensation")
    ceo_name: str = Field(default="", description="CEO name")
    ceo_comp: float = Field(default=0.0, description="CEO total compensation")
    median_exec_comp: float = Field(default=0.0, description="Median executive compensation")
    avg_exec_comp: float = Field(default=0.0, description="Average executive compensation")

    # Corporate Tax Metrics
    total_tax_expense: float = Field(default=0.0, description="Total income tax expense")
    current_tax: float = Field(default=0.0, description="Current tax expense")
    deferred_tax: float = Field(default=0.0, description="Deferred tax expense")
    effective_tax_rate: float = Field(default=0.0, description="Effective tax rate (0-1)")
    cash_taxes_paid: float = Field(default=0.0, description="Actual cash taxes paid")
    pretax_income: float = Field(default=0.0, description="Pre-tax income")

    # Comparison Ratios
    comp_to_tax_ratio: float = Field(default=0.0, description="total_exec_comp / total_tax_expense")
    ceo_to_tax_ratio: float = Field(default=0.0, description="ceo_comp / total_tax_expense")
    comp_to_pretax_ratio: float = Field(default=0.0, description="total_exec_comp / pretax_income")
    comp_to_cash_tax_ratio: float = Field(
        default=0.0, description="total_exec_comp / cash_taxes_paid"
    )

    # Rankings (populated when analyzing multiple companies)
    comp_rank: int | None = Field(default=None, description="Rank by total exec compensation")
    tax_rank: int | None = Field(default=None, description="Rank by total tax expense")
    ratio_rank: int | None = Field(default=None, description="Rank by comp/tax ratio")


class BatchAnalysisSummary(BaseModel):
    """Summary statistics across all analyzed companies."""

    num_companies: int = Field(..., description="Number of companies analyzed")
    fiscal_year: int = Field(..., description="Fiscal year of analysis")

    # Aggregate Compensation Stats
    total_exec_comp_all: float = Field(default=0.0, description="Sum across all companies")
    avg_exec_comp_per_company: float = Field(default=0.0)
    median_exec_comp_per_company: float = Field(default=0.0)
    max_exec_comp_company: str = Field(default="")
    max_exec_comp: float = Field(default=0.0)

    # Aggregate Tax Stats
    total_tax_all: float = Field(default=0.0, description="Sum across all companies")
    avg_tax_per_company: float = Field(default=0.0)
    median_tax_per_company: float = Field(default=0.0)
    avg_effective_rate: float = Field(default=0.0)

    # Ratio Stats
    avg_comp_to_tax_ratio: float = Field(default=0.0)
    median_comp_to_tax_ratio: float = Field(default=0.0)
    max_ratio_company: str = Field(default="")
    max_ratio: float = Field(default=0.0)
