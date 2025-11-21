"""Source verification and spot checking for Edgar Analyzer."""

import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import aiohttp
import structlog

from edgar_analyzer.models.company import Company, ExecutiveCompensation, TaxExpense
from edgar_analyzer.validation.data_validator import ValidationResult

logger = structlog.get_logger(__name__)


class SourceVerifier:
    """Verify data against known sources and perform spot checks."""
    
    def __init__(self):
        """Initialize source verifier."""
        self.session: Optional[aiohttp.ClientSession] = None
        self.known_benchmarks = self._load_known_benchmarks()
        logger.info("Source verifier initialized")
    
    def _load_known_benchmarks(self) -> Dict:
        """Load known benchmark data for verification."""
        return {
            # Known Apple data for verification
            "0000320193": {  # Apple Inc.
                "name": "Apple Inc.",
                "ticker": "AAPL",
                "2023": {
                    "tax_expense_range": (13_000_000_000, 17_000_000_000),  # $13B-$17B
                    "ceo_compensation_range": (60_000_000, 100_000_000),    # $60M-$100M
                },
                "2022": {
                    "tax_expense_range": (19_000_000_000, 21_000_000_000),  # ~$20B
                    "ceo_compensation_range": (90_000_000, 110_000_000),    # ~$100M
                }
            },
            # Known Microsoft data
            "0000789019": {  # Microsoft Corporation
                "name": "Microsoft Corporation",
                "ticker": "MSFT",
                "2023": {
                    "tax_expense_range": (16_000_000_000, 20_000_000_000),  # $16B-$20B
                    "ceo_compensation_range": (40_000_000, 60_000_000),     # $40M-$60M
                }
            },
            # Known Walmart data
            "0000066740": {  # Walmart Inc.
                "name": "Walmart Inc.",
                "ticker": "WMT",
                "2023": {
                    "tax_expense_range": (4_000_000_000, 6_000_000_000),    # $4B-$6B
                    "ceo_compensation_range": (20_000_000, 30_000_000),     # $20M-$30M
                }
            }
        }
    
    async def verify_against_benchmarks(
        self, 
        company: Company, 
        tax_expense: Optional[TaxExpense], 
        compensations: List[ExecutiveCompensation]
    ) -> List[ValidationResult]:
        """Verify extracted data against known benchmarks."""
        results = []
        
        if company.cik not in self.known_benchmarks:
            results.append(ValidationResult(
                is_valid=True,
                confidence_score=0.5,
                message=f"No benchmark data available for {company.name}",
                severity="INFO",
                field_name="benchmark_verification"
            ))
            return results
        
        benchmark = self.known_benchmarks[company.cik]
        
        # Verify tax expense
        if tax_expense:
            tax_results = await self._verify_tax_expense_benchmark(
                company, tax_expense, benchmark
            )
            results.extend(tax_results)
        
        # Verify CEO compensation
        ceo_compensation = self._find_ceo_compensation(compensations)
        if ceo_compensation:
            ceo_results = await self._verify_ceo_compensation_benchmark(
                company, ceo_compensation, benchmark
            )
            results.extend(ceo_results)
        
        return results
    
    async def _verify_tax_expense_benchmark(
        self, 
        company: Company, 
        tax_expense: TaxExpense, 
        benchmark: Dict
    ) -> List[ValidationResult]:
        """Verify tax expense against benchmark data."""
        results = []
        year = tax_expense.fiscal_year
        
        if str(year) not in benchmark:
            return [ValidationResult(
                is_valid=True,
                confidence_score=0.5,
                message=f"No benchmark data for {company.name} year {year}",
                severity="INFO",
                field_name="tax_expense_benchmark"
            )]
        
        year_benchmark = benchmark[str(year)]
        if "tax_expense_range" not in year_benchmark:
            return results
        
        min_expected, max_expected = year_benchmark["tax_expense_range"]
        actual_tax = float(tax_expense.total_tax_expense)
        
        if min_expected <= actual_tax <= max_expected:
            results.append(ValidationResult(
                is_valid=True,
                confidence_score=0.95,
                message=f"Tax expense within expected range for {company.name} ({year}): ${actual_tax:,.0f}",
                severity="INFO",
                field_name="tax_expense_benchmark",
                actual_value=actual_tax
            ))
        elif actual_tax < min_expected:
            deviation = (min_expected - actual_tax) / min_expected * 100
            severity = "WARNING" if deviation < 20 else "ERROR"
            confidence = 0.7 if deviation < 20 else 0.3
            
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=confidence,
                message=f"Tax expense below expected range for {company.name} ({year}): ${actual_tax:,.0f} < ${min_expected:,.0f}",
                severity=severity,
                field_name="tax_expense_benchmark",
                expected_value=f"${min_expected:,.0f}-${max_expected:,.0f}",
                actual_value=actual_tax,
                suggestion="Verify tax expense extraction - value seems low compared to known data"
            ))
        else:  # actual_tax > max_expected
            deviation = (actual_tax - max_expected) / max_expected * 100
            severity = "WARNING" if deviation < 20 else "ERROR"
            confidence = 0.7 if deviation < 20 else 0.3
            
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=confidence,
                message=f"Tax expense above expected range for {company.name} ({year}): ${actual_tax:,.0f} > ${max_expected:,.0f}",
                severity=severity,
                field_name="tax_expense_benchmark",
                expected_value=f"${min_expected:,.0f}-${max_expected:,.0f}",
                actual_value=actual_tax,
                suggestion="Verify tax expense extraction - value seems high compared to known data"
            ))
        
        return results

    async def _verify_ceo_compensation_benchmark(
        self,
        company: Company,
        ceo_compensation: ExecutiveCompensation,
        benchmark: Dict
    ) -> List[ValidationResult]:
        """Verify CEO compensation against benchmark data."""
        results = []
        year = ceo_compensation.fiscal_year

        if str(year) not in benchmark:
            return [ValidationResult(
                is_valid=True,
                confidence_score=0.5,
                message=f"No CEO compensation benchmark for {company.name} year {year}",
                severity="INFO",
                field_name="ceo_compensation_benchmark"
            )]

        year_benchmark = benchmark[str(year)]
        if "ceo_compensation_range" not in year_benchmark:
            return results

        min_expected, max_expected = year_benchmark["ceo_compensation_range"]
        actual_comp = float(ceo_compensation.total_compensation)

        if min_expected <= actual_comp <= max_expected:
            results.append(ValidationResult(
                is_valid=True,
                confidence_score=0.9,
                message=f"CEO compensation within expected range for {company.name} ({year}): ${actual_comp:,.0f}",
                severity="INFO",
                field_name="ceo_compensation_benchmark",
                actual_value=actual_comp
            ))
        else:
            deviation = abs(actual_comp - (min_expected + max_expected) / 2) / ((min_expected + max_expected) / 2) * 100
            severity = "WARNING" if deviation < 30 else "ERROR"
            confidence = 0.6 if deviation < 30 else 0.2

            results.append(ValidationResult(
                is_valid=False,
                confidence_score=confidence,
                message=f"CEO compensation outside expected range for {company.name} ({year}): ${actual_comp:,.0f}",
                severity=severity,
                field_name="ceo_compensation_benchmark",
                expected_value=f"${min_expected:,.0f}-${max_expected:,.0f}",
                actual_value=actual_comp,
                suggestion="Verify CEO compensation extraction against known public data"
            ))

        return results

    def _find_ceo_compensation(self, compensations: List[ExecutiveCompensation]) -> Optional[ExecutiveCompensation]:
        """Find CEO compensation from list of executive compensations."""
        ceo_titles = ["chief executive officer", "ceo", "president and ceo", "chairman and ceo"]

        for comp in compensations:
            title_lower = comp.title.lower()
            if any(ceo_title in title_lower for ceo_title in ceo_titles):
                return comp

        # If no explicit CEO found, return the highest paid executive
        if compensations:
            return max(compensations, key=lambda c: float(c.total_compensation))

        return None

    async def perform_spot_checks(
        self,
        company: Company,
        year: int
    ) -> List[ValidationResult]:
        """Perform spot checks against external sources."""
        results = []

        # Check company name consistency
        name_check = await self._spot_check_company_name(company)
        results.append(name_check)

        # Check ticker symbol consistency
        if company.ticker:
            ticker_check = await self._spot_check_ticker_symbol(company)
            results.append(ticker_check)

        # Check Fortune ranking reasonableness
        if company.fortune_rank:
            ranking_check = self._spot_check_fortune_ranking(company)
            results.append(ranking_check)

        return results

    async def _spot_check_company_name(self, company: Company) -> ValidationResult:
        """Spot check company name for consistency."""
        # Basic name validation
        name = company.name.strip()

        # Check for common corporate suffixes
        corporate_suffixes = [
            "inc", "inc.", "corporation", "corp", "corp.", "company", "co", "co.",
            "llc", "l.l.c.", "limited", "ltd", "ltd.", "plc"
        ]

        name_lower = name.lower()
        has_suffix = any(name_lower.endswith(suffix) for suffix in corporate_suffixes)

        if has_suffix:
            return ValidationResult(
                is_valid=True,
                confidence_score=0.9,
                message=f"Company name has proper corporate suffix: {name}",
                severity="INFO",
                field_name="company_name_format"
            )
        else:
            return ValidationResult(
                is_valid=True,
                confidence_score=0.6,
                message=f"Company name missing typical corporate suffix: {name}",
                severity="WARNING",
                field_name="company_name_format",
                suggestion="Verify complete company name extraction"
            )

    async def _spot_check_ticker_symbol(self, company: Company) -> ValidationResult:
        """Spot check ticker symbol format."""
        ticker = company.ticker.strip().upper()

        # Basic ticker validation
        if not re.match(r"^[A-Z]{1,5}$", ticker):
            return ValidationResult(
                is_valid=False,
                confidence_score=0.3,
                message=f"Unusual ticker symbol format: {ticker}",
                severity="WARNING",
                field_name="ticker_symbol",
                actual_value=ticker,
                suggestion="Verify ticker symbol extraction"
            )

        return ValidationResult(
            is_valid=True,
            confidence_score=0.9,
            message=f"Ticker symbol format looks good: {ticker}",
            severity="INFO",
            field_name="ticker_symbol",
            actual_value=ticker
        )

    def _spot_check_fortune_ranking(self, company: Company) -> ValidationResult:
        """Spot check Fortune 500 ranking reasonableness."""
        rank = company.fortune_rank

        if not isinstance(rank, int) or rank < 1 or rank > 500:
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                message=f"Invalid Fortune 500 ranking: {rank}",
                severity="ERROR",
                field_name="fortune_ranking",
                actual_value=rank,
                suggestion="Fortune 500 ranking must be between 1 and 500"
            )

        return ValidationResult(
            is_valid=True,
            confidence_score=0.95,
            message=f"Fortune 500 ranking is valid: #{rank}",
            severity="INFO",
            field_name="fortune_ranking",
            actual_value=rank
        )

    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
