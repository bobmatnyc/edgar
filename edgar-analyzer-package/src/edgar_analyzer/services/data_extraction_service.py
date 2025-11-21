"""Data extraction service implementation."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import structlog
from bs4 import BeautifulSoup

from edgar_analyzer.models.company import (
    Company,
    CompanyAnalysis,
    ExecutiveCompensation,
    TaxExpense,
)
from edgar_analyzer.services.interfaces import (
    ICacheService,
    ICompanyService,
    IDataExtractionService,
    IEdgarApiService,
)

logger = structlog.get_logger(__name__)


class DataExtractionService(IDataExtractionService):
    """Data extraction service implementation."""

    def __init__(
        self,
        edgar_api_service: IEdgarApiService,
        company_service: ICompanyService,
        cache_service: Optional[ICacheService] = None
    ):
        """Initialize data extraction service."""
        self._edgar_api = edgar_api_service
        self._company_service = company_service
        self._cache = cache_service

        # XBRL tags for tax expense data
        self._tax_expense_tags = [
            'IncomeTaxExpenseBenefit',
            'CurrentIncomeTaxExpenseBenefit',
            'DeferredIncomeTaxExpenseBenefit',
            'IncomeTaxesPaid',
            'FederalIncomeTaxExpenseBenefit',
            'StateAndLocalIncomeTaxExpenseBenefit'
        ]

        logger.info("Data extraction service initialized")

    async def extract_tax_expense(self, cik: str, year: int) -> Optional[TaxExpense]:
        """Extract tax expense data for a company and year."""
        cik_formatted = str(cik).zfill(10)

        try:
            # Get company facts from EDGAR API
            facts_data = await self._edgar_api.get_company_facts(cik_formatted)

            if not facts_data:
                logger.warning("No facts data found", cik=cik_formatted, year=year)
                return None

            us_gaap = facts_data.get('facts', {}).get('us-gaap', {})

            # Try to extract tax expense using different tags
            for tag in self._tax_expense_tags:
                tax_expense = await self._extract_tax_from_tag(
                    us_gaap, tag, cik_formatted, year
                )
                if tax_expense:
                    logger.info(
                        "Tax expense extracted",
                        cik=cik_formatted,
                        year=year,
                        tag=tag,
                        amount=tax_expense.total_tax_expense
                    )
                    return tax_expense

            logger.warning("No tax expense data found", cik=cik_formatted, year=year)
            return None

        except Exception as e:
            logger.error(
                "Failed to extract tax expense",
                cik=cik_formatted,
                year=year,
                error=str(e)
            )
            return None

    async def _extract_tax_from_tag(
        self, us_gaap: Dict, tag: str, cik: str, year: int
    ) -> Optional[TaxExpense]:
        """Extract tax expense from specific XBRL tag."""
        if tag not in us_gaap:
            return None

        tag_data = us_gaap[tag]
        units = tag_data.get('units', {})

        if 'USD' not in units:
            return None

        usd_facts = units['USD']

        # Look for annual data (10-K filings) for the specified year
        for fact in usd_facts:
            if (fact.get('fy') == year and
                fact.get('form') in ['10-K', '10-K/A'] and
                fact.get('val') is not None):

                return TaxExpense(
                    company_cik=cik,
                    fiscal_year=year,
                    period='annual',
                    total_tax_expense=Decimal(str(fact['val'])),
                    filing_date=datetime.fromisoformat(fact.get('filed', '').replace('Z', '+00:00')) if fact.get('filed') else None,
                    source_filing=fact.get('accn'),
                    form_type=fact.get('form')
                )

        return None

    async def extract_executive_compensation(
        self, cik: str, year: int
    ) -> List[ExecutiveCompensation]:
        """Extract executive compensation data for a company and year."""
        cik_formatted = str(cik).zfill(10)

        try:
            # Get company submissions to find proxy filings
            submissions_data = await self._edgar_api.get_company_submissions(cik_formatted)

            if not submissions_data:
                logger.warning("No submissions data found", cik=cik_formatted, year=year)
                return []

            # Find DEF 14A (proxy statement) filings for the year
            proxy_filings = self._find_proxy_filings(submissions_data, year)

            if not proxy_filings:
                logger.warning("No proxy filings found", cik=cik_formatted, year=year)
                return []

            # For now, return placeholder data since proxy parsing is complex
            # This would need to be implemented with actual HTML/XML parsing
            compensations = await self._create_placeholder_compensation(cik_formatted, year)

            logger.info(
                "Executive compensation extracted (placeholder)",
                cik=cik_formatted,
                year=year,
                executives=len(compensations)
            )
            return compensations

        except Exception as e:
            logger.error(
                "Failed to extract executive compensation",
                cik=cik_formatted,
                year=year,
                error=str(e)
            )
            return []

    def _find_proxy_filings(self, submissions_data: Dict, year: int) -> List[Dict]:
        """Find proxy statement filings for a specific year."""
        filings = []
        recent_filings = submissions_data.get('filings', {}).get('recent', {})

        if not recent_filings:
            return filings

        forms = recent_filings.get('form', [])
        filing_dates = recent_filings.get('filingDate', [])
        accession_numbers = recent_filings.get('accessionNumber', [])

        for i, form in enumerate(forms):
            if form == 'DEF 14A':
                filing_date = filing_dates[i]
                if filing_date.startswith(str(year)):
                    filings.append({
                        'form': form,
                        'filingDate': filing_date,
                        'accessionNumber': accession_numbers[i]
                    })

        return filings

    async def _create_placeholder_compensation(
        self, cik: str, year: int
    ) -> List[ExecutiveCompensation]:
        """Create placeholder compensation data for demonstration."""
        # This is placeholder data - real implementation would parse proxy statements
        placeholder_executives = [
            {"name": "Chief Executive Officer", "title": "CEO", "compensation": 15000000},
            {"name": "Chief Financial Officer", "title": "CFO", "compensation": 8000000},
            {"name": "Chief Operating Officer", "title": "COO", "compensation": 7000000},
        ]

        compensations = []
        for exec_data in placeholder_executives:
            compensation = ExecutiveCompensation(
                company_cik=cik,
                fiscal_year=year,
                executive_name=exec_data["name"],
                title=exec_data["title"],
                total_compensation=Decimal(str(exec_data["compensation"])),
                salary=Decimal(str(exec_data["compensation"] * 0.3)),
                bonus=Decimal(str(exec_data["compensation"] * 0.2)),
                stock_awards=Decimal(str(exec_data["compensation"] * 0.4)),
                option_awards=Decimal(str(exec_data["compensation"] * 0.1)),
            )
            compensations.append(compensation)

        return compensations

    async def extract_company_analysis(
        self, cik: str, year: int
    ) -> Optional[CompanyAnalysis]:
        """Extract complete analysis for a company and year."""
        cik_formatted = str(cik).zfill(10)

        try:
            # Get company information
            company = await self._company_service.get_company_by_cik(cik_formatted)
            if not company:
                logger.warning("Company not found", cik=cik_formatted)
                return None

            # Extract tax expense data
            tax_expense = await self.extract_tax_expense(cik_formatted, year)
            tax_expenses = [tax_expense] if tax_expense else []

            # Extract executive compensation data
            executive_compensations = await self.extract_executive_compensation(cik_formatted, year)

            # Create company analysis
            analysis = CompanyAnalysis(
                company=company,
                tax_expenses=tax_expenses,
                executive_compensations=executive_compensations,
                analysis_date=datetime.now()
            )

            logger.info(
                "Company analysis completed",
                cik=cik_formatted,
                company=company.name,
                tax_expenses=len(tax_expenses),
                executives=len(executive_compensations)
            )

            return analysis

        except Exception as e:
            logger.error(
                "Failed to extract company analysis",
                cik=cik_formatted,
                year=year,
                error=str(e)
            )
            return None