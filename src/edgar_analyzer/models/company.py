"""Company data models."""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class Company(BaseModel):
    """Company information model."""

    cik: str = Field(..., description="SEC Central Index Key (10 digits)")
    name: str = Field(..., description="Company name")
    ticker: Optional[str] = Field(None, description="Stock ticker symbol")
    exchange: Optional[str] = Field(None, description="Stock exchange")
    sic: Optional[str] = Field(None, description="Standard Industrial Classification")
    industry: Optional[str] = Field(None, description="Industry description")
    sector: Optional[str] = Field(None, description="Business sector")
    market_cap: Optional[Decimal] = Field(None, description="Market capitalization")
    fortune_rank: Optional[int] = Field(None, description="Fortune 500 ranking")

    @validator('cik')
    def validate_cik(cls, v: str) -> str:
        """Ensure CIK is 10 digits with leading zeros."""
        return str(v).zfill(10)

    @validator('ticker')
    def validate_ticker(cls, v: Optional[str]) -> Optional[str]:
        """Normalize ticker symbol."""
        return v.upper() if v else None


class ExecutiveCompensation(BaseModel):
    """Executive compensation data model."""

    company_cik: str = Field(..., description="Company CIK")
    fiscal_year: int = Field(..., description="Fiscal year")
    executive_name: str = Field(..., description="Executive name")
    title: str = Field(..., description="Executive title")
    total_compensation: Decimal = Field(..., description="Total compensation")
    salary: Optional[Decimal] = Field(None, description="Base salary")
    bonus: Optional[Decimal] = Field(None, description="Bonus")
    stock_awards: Optional[Decimal] = Field(None, description="Stock awards")
    option_awards: Optional[Decimal] = Field(None, description="Option awards")
    other_compensation: Optional[Decimal] = Field(None, description="Other compensation")
    filing_date: Optional[datetime] = Field(None, description="Filing date")
    source_filing: Optional[str] = Field(None, description="Source filing accession number")


class TaxExpense(BaseModel):
    """Tax expense data model."""

    company_cik: str = Field(..., description="Company CIK")
    fiscal_year: int = Field(..., description="Fiscal year")
    period: str = Field(..., description="Reporting period (annual/quarterly)")
    total_tax_expense: Decimal = Field(..., description="Total income tax expense")
    current_tax_expense: Optional[Decimal] = Field(None, description="Current tax expense")
    deferred_tax_expense: Optional[Decimal] = Field(None, description="Deferred tax expense")
    federal_tax_expense: Optional[Decimal] = Field(None, description="Federal tax expense")
    state_local_tax_expense: Optional[Decimal] = Field(None, description="State/local tax expense")
    filing_date: Optional[datetime] = Field(None, description="Filing date")
    source_filing: Optional[str] = Field(None, description="Source filing accession number")
    form_type: Optional[str] = Field(None, description="Form type (10-K, 10-Q)")


class CompanyAnalysis(BaseModel):
    """Combined analysis data for a company."""

    company: Company
    tax_expenses: List[TaxExpense] = Field(default_factory=list)
    executive_compensations: List[ExecutiveCompensation] = Field(default_factory=list)
    analysis_date: datetime = Field(default_factory=datetime.now)

    @property
    def latest_tax_expense(self) -> Optional[TaxExpense]:
        """Get the most recent tax expense data."""
        if not self.tax_expenses:
            return None
        return max(self.tax_expenses, key=lambda x: x.fiscal_year)

    @property
    def total_executive_compensation(self) -> Dict[int, Decimal]:
        """Get total executive compensation by fiscal year."""
        compensation_by_year: Dict[int, Decimal] = {}
        for comp in self.executive_compensations:
            year = comp.fiscal_year
            if year not in compensation_by_year:
                compensation_by_year[year] = Decimal('0')
            compensation_by_year[year] += comp.total_compensation
        return compensation_by_year

    @property
    def compensation_vs_tax_ratio(self) -> Dict[int, Optional[Decimal]]:
        """Calculate compensation to tax expense ratio by year."""
        ratios: Dict[int, Optional[Decimal]] = {}
        total_comp = self.total_executive_compensation

        for tax_exp in self.tax_expenses:
            year = tax_exp.fiscal_year
            if year in total_comp and tax_exp.total_tax_expense > 0:
                ratios[year] = total_comp[year] / tax_exp.total_tax_expense
            else:
                ratios[year] = None

        return ratios


class AnalysisReport(BaseModel):
    """Analysis report containing multiple companies."""

    companies: List[CompanyAnalysis] = Field(default_factory=list)
    report_date: datetime = Field(default_factory=datetime.now)
    target_year: int = Field(..., description="Target analysis year")
    total_companies: int = Field(default=0, description="Total companies analyzed")

    def add_company_analysis(self, analysis: CompanyAnalysis) -> None:
        """Add a company analysis to the report."""
        self.companies.append(analysis)
        self.total_companies = len(self.companies)

    @property
    def companies_with_higher_compensation(self) -> List[CompanyAnalysis]:
        """Get companies where exec compensation exceeds tax expense."""
        result = []
        for company in self.companies:
            ratios = company.compensation_vs_tax_ratio
            if self.target_year in ratios and ratios[self.target_year]:
                if ratios[self.target_year] > 1:
                    result.append(company)
        return result

    @property
    def summary_statistics(self) -> Dict[str, any]:
        """Generate summary statistics for the report."""
        total = len(self.companies)
        higher_comp = len(self.companies_with_higher_compensation)

        return {
            "total_companies": total,
            "companies_with_higher_compensation": higher_comp,
            "percentage_higher_compensation": (higher_comp / total * 100) if total > 0 else 0,
            "target_year": self.target_year,
            "report_date": self.report_date,
        }