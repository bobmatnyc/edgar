"""Historical analysis service for multi-year data extraction."""

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import structlog

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


class HistoricalAnalysisService:
    """Service for multi-year historical analysis."""

    def __init__(
        self,
        edgar_api_service: IEdgarApiService,
        data_extraction_service: IDataExtractionService,
        company_service: ICompanyService,
        cache_service: Optional[ICacheService] = None
    ):
        """Initialize historical analysis service."""
        self._edgar_api = edgar_api_service
        self._data_extraction = data_extraction_service
        self._company_service = company_service
        self._cache = cache_service

        logger.info("Historical analysis service initialized")

    async def extract_multi_year_analysis(
        self, cik: str, years: List[int]
    ) -> Optional[CompanyAnalysis]:
        """Extract multi-year analysis for a company."""
        cik_formatted = str(cik).zfill(10)

        try:
            # Get company information
            company = await self._company_service.get_company_by_cik(cik_formatted)
            if not company:
                logger.warning("Company not found", cik=cik_formatted)
                return None

            # Extract data for each year
            all_tax_expenses = []
            all_executive_compensations = []

            for year in years:
                logger.info("Extracting data for year", cik=cik_formatted, year=year)

                # Extract tax expense
                tax_expense = await self._data_extraction.extract_tax_expense(cik_formatted, year)
                if tax_expense:
                    all_tax_expenses.append(tax_expense)

                # Extract executive compensation
                exec_compensations = await self._data_extraction.extract_executive_compensation(cik_formatted, year)
                all_executive_compensations.extend(exec_compensations)

                # Small delay to respect rate limits
                await asyncio.sleep(0.1)

            # Create comprehensive analysis
            analysis = CompanyAnalysis(
                company=company,
                tax_expenses=all_tax_expenses,
                executive_compensations=all_executive_compensations,
                analysis_date=datetime.now()
            )

            logger.info(
                "Multi-year analysis completed",
                cik=cik_formatted,
                company=company.name,
                years=len(years),
                tax_expenses=len(all_tax_expenses),
                executives=len(all_executive_compensations)
            )

            return analysis

        except Exception as e:
            logger.error(
                "Failed to extract multi-year analysis",
                cik=cik_formatted,
                years=years,
                error=str(e)
            )
            return None

    async def extract_historical_tax_trends(
        self, cik: str, years: List[int]
    ) -> Dict[int, Optional[Decimal]]:
        """Extract historical tax expense trends."""
        cik_formatted = str(cik).zfill(10)
        tax_trends = {}

        for year in years:
            try:
                tax_expense = await self._data_extraction.extract_tax_expense(cik_formatted, year)
                tax_trends[year] = tax_expense.total_tax_expense if tax_expense else None
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.warning("Failed to extract tax for year", cik=cik_formatted, year=year, error=str(e))
                tax_trends[year] = None

        return tax_trends

    async def extract_historical_compensation_trends(
        self, cik: str, years: List[int]
    ) -> Dict[int, Decimal]:
        """Extract historical executive compensation trends."""
        cik_formatted = str(cik).zfill(10)
        compensation_trends = {}

        for year in years:
            try:
                compensations = await self._data_extraction.extract_executive_compensation(cik_formatted, year)
                total_compensation = sum(comp.total_compensation for comp in compensations)
                compensation_trends[year] = total_compensation
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                logger.warning("Failed to extract compensation for year", cik=cik_formatted, year=year, error=str(e))
                compensation_trends[year] = Decimal('0')

        return compensation_trends

    def calculate_growth_rates(self, values: Dict[int, Optional[Decimal]]) -> Dict[int, Optional[float]]:
        """Calculate year-over-year growth rates."""
        growth_rates = {}
        sorted_years = sorted(values.keys())

        for i in range(1, len(sorted_years)):
            current_year = sorted_years[i]
            previous_year = sorted_years[i-1]

            current_value = values.get(current_year)
            previous_value = values.get(previous_year)

            if current_value is not None and previous_value is not None and previous_value > 0:
                growth_rate = float((current_value - previous_value) / previous_value * 100)
                growth_rates[current_year] = growth_rate
            else:
                growth_rates[current_year] = None

        return growth_rates

    def calculate_average_ratios(self, analysis: CompanyAnalysis, years: List[int]) -> Dict[str, float]:
        """Calculate average ratios over multiple years."""
        ratios = analysis.compensation_vs_tax_ratio

        valid_ratios = [
            float(ratios[year]) for year in years
            if year in ratios and ratios[year] is not None
        ]

        if not valid_ratios:
            return {"average_ratio": 0.0, "years_with_data": 0}

        return {
            "average_ratio": sum(valid_ratios) / len(valid_ratios),
            "max_ratio": max(valid_ratios),
            "min_ratio": min(valid_ratios),
            "years_with_data": len(valid_ratios)
        }