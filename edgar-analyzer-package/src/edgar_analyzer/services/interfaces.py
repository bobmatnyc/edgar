"""Service interfaces for dependency injection."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from edgar_analyzer.models.company import (
    AnalysisReport,
    Company,
    CompanyAnalysis,
    ExecutiveCompensation,
    TaxExpense,
)


class IEdgarApiService(ABC):
    """Interface for SEC EDGAR API service."""

    @abstractmethod
    async def get_company_submissions(self, cik: str) -> Dict:
        """Get company submission history."""
        pass

    @abstractmethod
    async def get_company_facts(self, cik: str) -> Dict:
        """Get company XBRL facts."""
        pass

    @abstractmethod
    async def get_filing_content(self, accession_number: str, cik: str) -> str:
        """Get filing content by accession number."""
        pass


class ICompanyService(ABC):
    """Interface for company data service."""

    @abstractmethod
    async def get_company_by_cik(self, cik: str) -> Optional[Company]:
        """Get company information by CIK."""
        pass

    @abstractmethod
    async def get_fortune_500_companies(self) -> List[Company]:
        """Get Fortune 500 companies list."""
        pass

    @abstractmethod
    async def search_companies(self, query: str) -> List[Company]:
        """Search companies by name or ticker."""
        pass

    @abstractmethod
    async def update_company(self, company: Company) -> Company:
        """Update company information."""
        pass


class IDataExtractionService(ABC):
    """Interface for data extraction service."""

    @abstractmethod
    async def extract_tax_expense(self, cik: str, year: int) -> Optional[TaxExpense]:
        """Extract tax expense data for a company and year."""
        pass

    @abstractmethod
    async def extract_executive_compensation(
        self, cik: str, year: int
    ) -> List[ExecutiveCompensation]:
        """Extract executive compensation data for a company and year."""
        pass

    @abstractmethod
    async def extract_company_analysis(
        self, cik: str, year: int
    ) -> Optional[CompanyAnalysis]:
        """Extract complete analysis for a company and year."""
        pass


class IReportService(ABC):
    """Interface for report generation service."""

    @abstractmethod
    async def generate_analysis_report(
        self, companies: List[str], year: int
    ) -> AnalysisReport:
        """Generate analysis report for multiple companies."""
        pass

    @abstractmethod
    async def export_to_excel(self, report: AnalysisReport, filepath: str) -> None:
        """Export report to Excel file."""
        pass

    @abstractmethod
    async def export_to_json(self, report: AnalysisReport, filepath: str) -> None:
        """Export report to JSON file."""
        pass


class ICacheService(ABC):
    """Interface for caching service."""

    @abstractmethod
    async def get(self, key: str) -> Optional[any]:
        """Get cached value by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: any, ttl: Optional[int] = None) -> None:
        """Set cached value with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete cached value."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cached values."""
        pass


class IConfigService(ABC):
    """Interface for configuration service."""

    @abstractmethod
    def get(self, key: str, default: any = None) -> any:
        """Get configuration value."""
        pass

    @abstractmethod
    def get_edgar_config(self) -> Dict[str, any]:
        """Get EDGAR API configuration."""
        pass

    @abstractmethod
    def get_cache_config(self) -> Dict[str, any]:
        """Get cache configuration."""
        pass

    @abstractmethod
    def get_logging_config(self) -> Dict[str, any]:
        """Get logging configuration."""
        pass