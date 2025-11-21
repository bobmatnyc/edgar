"""Sanity testing framework for logical consistency checks."""

from decimal import Decimal
from typing import Dict, List, Optional

import structlog

from edgar_analyzer.models.company import Company, CompanyAnalysis, ExecutiveCompensation, TaxExpense
from edgar_analyzer.validation.data_validator import ValidationResult

logger = structlog.get_logger(__name__)


class SanityChecker:
    """Perform sanity checks for logical consistency and reasonableness."""
    
    def __init__(self):
        """Initialize sanity checker."""
        self.industry_benchmarks = self._load_industry_benchmarks()
        logger.info("Sanity checker initialized")
    
    def _load_industry_benchmarks(self) -> Dict:
        """Load industry-specific benchmarks for sanity checking."""
        return {
            "Technology": {
                "typical_tax_rate_range": (0.15, 0.25),  # 15%-25%
                "typical_ceo_comp_range": (10_000_000, 200_000_000),  # $10M-$200M
                "revenue_multiplier_range": (0.001, 0.01),  # CEO comp as % of revenue
            },
            "Healthcare": {
                "typical_tax_rate_range": (0.18, 0.28),  # 18%-28%
                "typical_ceo_comp_range": (5_000_000, 50_000_000),   # $5M-$50M
                "revenue_multiplier_range": (0.0005, 0.005),
            },
            "Financial Services": {
                "typical_tax_rate_range": (0.20, 0.30),  # 20%-30%
                "typical_ceo_comp_range": (15_000_000, 100_000_000), # $15M-$100M
                "revenue_multiplier_range": (0.001, 0.008),
            },
            "Energy": {
                "typical_tax_rate_range": (0.25, 0.35),  # 25%-35%
                "typical_ceo_comp_range": (10_000_000, 80_000_000),  # $10M-$80M
                "revenue_multiplier_range": (0.0002, 0.002),
            },
            "Consumer Staples": {
                "typical_tax_rate_range": (0.22, 0.32),  # 22%-32%
                "typical_ceo_comp_range": (8_000_000, 60_000_000),   # $8M-$60M
                "revenue_multiplier_range": (0.0003, 0.003),
            }
        }
    
    def perform_comprehensive_sanity_check(self, analysis: CompanyAnalysis) -> List[ValidationResult]:
        """Perform comprehensive sanity checks on company analysis."""
        results = []
        
        # Basic data consistency checks
        results.extend(self._check_data_consistency(analysis))
        
        # Cross-year consistency checks
        results.extend(self._check_cross_year_consistency(analysis))
        
        # Industry benchmark checks
        results.extend(self._check_industry_benchmarks(analysis))
        
        # Logical relationship checks
        results.extend(self._check_logical_relationships(analysis))
        
        # Outlier detection
        results.extend(self._detect_outliers(analysis))
        
        return results
    
    def _check_data_consistency(self, analysis: CompanyAnalysis) -> List[ValidationResult]:
        """Check basic data consistency within the analysis."""
        results = []
        
        # Check if we have data for the target years
        expected_years = 5  # Assuming 5-year analysis
        actual_tax_years = len(analysis.tax_expenses)
        actual_comp_years = len(set(comp.fiscal_year for comp in analysis.executive_compensations))
        
        if actual_tax_years < expected_years * 0.6:  # Less than 60% of expected data
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=0.4,
                message=f"Insufficient tax data: {actual_tax_years} years (expected ~{expected_years})",
                severity="WARNING",
                field_name="data_completeness",
                suggestion="Verify tax expense extraction for all target years"
            ))
        
        if actual_comp_years < expected_years * 0.6:
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=0.4,
                message=f"Insufficient compensation data: {actual_comp_years} years (expected ~{expected_years})",
                severity="WARNING",
                field_name="data_completeness",
                suggestion="Verify executive compensation extraction for all target years"
            ))
        
        # Check for duplicate years
        tax_years = [tax.fiscal_year for tax in analysis.tax_expenses]
        if len(tax_years) != len(set(tax_years)):
            results.append(ValidationResult(
                is_valid=False,
                confidence_score=0.2,
                message="Duplicate tax expense years detected",
                severity="ERROR",
                field_name="data_consistency",
                suggestion="Check for duplicate data extraction"
            ))
        
        return results
    
    def _check_cross_year_consistency(self, analysis: CompanyAnalysis) -> List[ValidationResult]:
        """Check consistency across multiple years."""
        results = []
        
        if len(analysis.tax_expenses) < 2:
            return results  # Need at least 2 years for comparison
        
        # Sort by year
        sorted_taxes = sorted(analysis.tax_expenses, key=lambda x: x.fiscal_year)
        
        # Check for extreme year-over-year changes
        for i in range(1, len(sorted_taxes)):
            current = float(sorted_taxes[i].total_tax_expense)
            previous = float(sorted_taxes[i-1].total_tax_expense)
            
            if previous > 0:  # Avoid division by zero
                change_pct = abs(current - previous) / previous * 100
                
                if change_pct > 200:  # More than 200% change
                    results.append(ValidationResult(
                        is_valid=False,
                        confidence_score=0.3,
                        message=f"Extreme tax expense change: {change_pct:.1f}% from {sorted_taxes[i-1].fiscal_year} to {sorted_taxes[i].fiscal_year}",
                        severity="WARNING",
                        field_name="year_over_year_consistency",
                        actual_value=change_pct,
                        suggestion="Verify tax expense extraction - unusual year-over-year change"
                    ))
                elif change_pct > 100:  # More than 100% change
                    results.append(ValidationResult(
                        is_valid=True,
                        confidence_score=0.6,
                        message=f"Large tax expense change: {change_pct:.1f}% from {sorted_taxes[i-1].fiscal_year} to {sorted_taxes[i].fiscal_year}",
                        severity="INFO",
                        field_name="year_over_year_consistency",
                        actual_value=change_pct,
                        suggestion="Review for potential business changes or extraction issues"
                    ))
        
        return results

    def _check_industry_benchmarks(self, analysis: CompanyAnalysis) -> List[ValidationResult]:
        """Check against industry-specific benchmarks."""
        results = []

        company_sector = analysis.company.sector
        if not company_sector or company_sector not in self.industry_benchmarks:
            results.append(ValidationResult(
                is_valid=True,
                confidence_score=0.5,
                message=f"No industry benchmarks available for sector: {company_sector}",
                severity="INFO",
                field_name="industry_benchmark"
            ))
            return results

        benchmarks = self.industry_benchmarks[company_sector]

        # Note: Effective tax rate validation would require calculating ETR from available data
        # For now, we skip this validation as the field doesn't exist in TaxExpense model

        return results

    def _check_logical_relationships(self, analysis: CompanyAnalysis) -> List[ValidationResult]:
        """Check logical relationships between different data points."""
        results = []

        # Check compensation vs tax ratios for reasonableness
        ratios = analysis.compensation_vs_tax_ratio

        for year, ratio in ratios.items():
            if ratio is not None:
                if ratio > 10:  # Compensation more than 10x tax expense
                    results.append(ValidationResult(
                        is_valid=False,
                        confidence_score=0.2,
                        message=f"Extremely high compensation/tax ratio in {year}: {ratio:.2f}x",
                        severity="ERROR",
                        field_name="compensation_tax_ratio",
                        actual_value=ratio,
                        suggestion="Verify both compensation and tax expense extraction"
                    ))
                elif ratio > 5:  # Compensation more than 5x tax expense
                    results.append(ValidationResult(
                        is_valid=False,
                        confidence_score=0.4,
                        message=f"High compensation/tax ratio in {year}: {ratio:.2f}x",
                        severity="WARNING",
                        field_name="compensation_tax_ratio",
                        actual_value=ratio,
                        suggestion="Review compensation and tax data for accuracy"
                    ))
                elif ratio > 1:  # Compensation exceeds tax expense
                    results.append(ValidationResult(
                        is_valid=True,
                        confidence_score=0.7,
                        message=f"Compensation exceeds tax expense in {year}: {ratio:.2f}x",
                        severity="INFO",
                        field_name="compensation_tax_ratio",
                        actual_value=ratio
                    ))

        return results

    def _detect_outliers(self, analysis: CompanyAnalysis) -> List[ValidationResult]:
        """Detect statistical outliers in the data."""
        results = []

        # Detect outliers in tax expenses
        if len(analysis.tax_expenses) >= 3:
            tax_values = [float(tax.total_tax_expense) for tax in analysis.tax_expenses if tax.total_tax_expense is not None]
            if len(tax_values) >= 3:
                tax_outliers = self._find_statistical_outliers(tax_values)

                for i, is_outlier in enumerate(tax_outliers):
                    if is_outlier and i < len(analysis.tax_expenses):
                        year = analysis.tax_expenses[i].fiscal_year
                        value = tax_values[i]
                        results.append(ValidationResult(
                            is_valid=False,
                            confidence_score=0.5,
                            message=f"Statistical outlier detected in tax expense for {year}: ${value:,.0f}",
                            severity="WARNING",
                            field_name="statistical_outlier",
                            actual_value=value,
                            suggestion="Review tax expense data for this year"
                        ))

        # Detect outliers in executive compensation
        comp_by_year = {}
        for comp in analysis.executive_compensations:
            year = comp.fiscal_year
            if year not in comp_by_year:
                comp_by_year[year] = []
            if comp.total_compensation is not None:
                comp_by_year[year].append(float(comp.total_compensation))

        # Calculate total compensation per year
        total_comp_by_year = {year: sum(comps) for year, comps in comp_by_year.items()}

        if len(total_comp_by_year) >= 3:
            comp_values = list(total_comp_by_year.values())
            comp_outliers = self._find_statistical_outliers(comp_values)

            for i, (year, value) in enumerate(total_comp_by_year.items()):
                if i < len(comp_outliers) and comp_outliers[i]:
                    results.append(ValidationResult(
                        is_valid=False,
                        confidence_score=0.5,
                        message=f"Statistical outlier detected in executive compensation for {year}: ${value:,.0f}",
                        severity="WARNING",
                        field_name="statistical_outlier",
                        actual_value=value,
                        suggestion="Review executive compensation data for this year"
                    ))

        return results

    def _find_statistical_outliers(self, values: List[float]) -> List[bool]:
        """Find statistical outliers using IQR method."""
        if len(values) < 3:
            return [False] * len(values)

        sorted_values = sorted(values)
        n = len(sorted_values)

        # Calculate quartiles
        q1_idx = n // 4
        q3_idx = 3 * n // 4
        q1 = sorted_values[q1_idx]
        q3 = sorted_values[q3_idx]

        # Calculate IQR and outlier bounds
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # Identify outliers
        return [value < lower_bound or value > upper_bound for value in values]
