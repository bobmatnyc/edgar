"""Analyzer for comparing executive compensation to corporate tax payments."""

from dataclasses import dataclass
from statistics import median, mean

from edgar.analysis.models import BatchAnalysisSummary, CompTaxAnalysis
from edgar.data.fortune100 import Company
from edgar.extractors.sct.models import SCTData
from edgar.extractors.tax.models import TaxData, TaxYear


@dataclass(frozen=True)
class CompTaxAnalyzer:
    """Analyze relationship between executive compensation and corporate tax.

    Computes ratios and rankings to compare exec pay vs tax contributions.
    """

    def analyze_single(
        self,
        company: Company,
        sct_data: SCTData,
        tax_data: TaxData,
        fiscal_year: int | None = None,
    ) -> CompTaxAnalysis:
        """Analyze a single company's exec comp vs tax data.

        Args:
            company: Company info
            sct_data: Executive compensation data
            tax_data: Corporate tax data
            fiscal_year: Specific year to analyze (defaults to most recent)

        Returns:
            CompTaxAnalysis with all metrics
        """
        # Determine fiscal year
        if fiscal_year is None:
            # Use most recent year from either dataset
            sct_year = (
                sct_data.executives[0].compensation[0].year
                if sct_data.executives and sct_data.executives[0].compensation
                else 0
            )
            tax_year = tax_data.tax_years[0].year if tax_data.tax_years else 0
            fiscal_year = max(sct_year, tax_year)

        # Get compensation data for year
        comp_list = self._get_comp_for_year(sct_data, fiscal_year)
        total_exec_comp = sum(comp_list)
        num_executives = len(comp_list)
        avg_exec_comp = total_exec_comp / num_executives if num_executives > 0 else 0.0
        median_exec_comp = median(comp_list) if comp_list else 0.0

        # Find CEO
        ceo_name, ceo_comp = self._find_ceo(sct_data, fiscal_year)

        # Get tax data for year
        tax_year_data = self._get_tax_for_year(tax_data, fiscal_year)
        if tax_year_data:
            total_tax_expense = tax_year_data.total_tax_expense
            current_tax = tax_year_data.total_current
            deferred_tax = tax_year_data.total_deferred
            effective_tax_rate = tax_year_data.effective_tax_rate
            cash_taxes_paid = tax_year_data.cash_taxes_paid
            pretax_income = tax_year_data.pretax_income
        else:
            total_tax_expense = 0.0
            current_tax = 0.0
            deferred_tax = 0.0
            effective_tax_rate = 0.0
            cash_taxes_paid = 0.0
            pretax_income = 0.0

        # Compute ratios (avoid division by zero)
        # Note: Allow negative ratios when tax expense is negative (tax benefit)
        comp_to_tax_ratio = total_exec_comp / total_tax_expense if total_tax_expense != 0 else 0.0
        ceo_to_tax_ratio = ceo_comp / total_tax_expense if total_tax_expense != 0 else 0.0
        comp_to_pretax_ratio = total_exec_comp / pretax_income if pretax_income != 0 else 0.0
        comp_to_cash_tax_ratio = total_exec_comp / cash_taxes_paid if cash_taxes_paid != 0 else 0.0

        return CompTaxAnalysis(
            company=company.name,
            ticker=company.ticker,
            cik=company.cik,
            rank=company.rank,
            fiscal_year=fiscal_year,
            num_executives=num_executives,
            total_exec_comp=total_exec_comp,
            ceo_name=ceo_name,
            ceo_comp=ceo_comp,
            median_exec_comp=median_exec_comp,
            avg_exec_comp=avg_exec_comp,
            total_tax_expense=total_tax_expense,
            current_tax=current_tax,
            deferred_tax=deferred_tax,
            effective_tax_rate=effective_tax_rate,
            cash_taxes_paid=cash_taxes_paid,
            pretax_income=pretax_income,
            comp_to_tax_ratio=comp_to_tax_ratio,
            ceo_to_tax_ratio=ceo_to_tax_ratio,
            comp_to_pretax_ratio=comp_to_pretax_ratio,
            comp_to_cash_tax_ratio=comp_to_cash_tax_ratio,
        )

    def analyze_batch(
        self,
        results: list[tuple[Company, SCTData, TaxData]],
        fiscal_year: int | None = None,
    ) -> list[CompTaxAnalysis]:
        """Analyze all companies and compute rankings.

        Args:
            results: List of (Company, SCTData, TaxData) tuples
            fiscal_year: Specific year to analyze

        Returns:
            List of analyses with rankings populated
        """
        # Analyze each company
        analyses = [
            self.analyze_single(company, sct_data, tax_data, fiscal_year)
            for company, sct_data, tax_data in results
        ]

        # Compute rankings
        return self._compute_rankings(analyses)

    def generate_summary(
        self,
        analyses: list[CompTaxAnalysis],
    ) -> BatchAnalysisSummary:
        """Generate aggregate statistics across all companies.

        Args:
            analyses: List of individual company analyses

        Returns:
            BatchAnalysisSummary with aggregate metrics
        """
        if not analyses:
            # Return empty summary for fiscal year 0
            return BatchAnalysisSummary(num_companies=0, fiscal_year=0)

        num_companies = len(analyses)
        fiscal_year = analyses[0].fiscal_year

        # Aggregate compensation stats
        comp_values = [a.total_exec_comp for a in analyses]
        total_exec_comp_all = sum(comp_values)
        avg_exec_comp_per_company = mean(comp_values) if comp_values else 0.0
        median_exec_comp_per_company = median(comp_values) if comp_values else 0.0

        max_comp_analysis = max(analyses, key=lambda a: a.total_exec_comp)
        max_exec_comp_company = max_comp_analysis.company
        max_exec_comp = max_comp_analysis.total_exec_comp

        # Aggregate tax stats
        tax_values = [a.total_tax_expense for a in analyses]
        total_tax_all = sum(tax_values)
        avg_tax_per_company = mean(tax_values) if tax_values else 0.0
        median_tax_per_company = median(tax_values) if tax_values else 0.0

        effective_rates = [a.effective_tax_rate for a in analyses if a.effective_tax_rate > 0]
        avg_effective_rate = mean(effective_rates) if effective_rates else 0.0

        # Ratio stats
        ratio_values = [a.comp_to_tax_ratio for a in analyses if a.comp_to_tax_ratio > 0]
        avg_comp_to_tax_ratio = mean(ratio_values) if ratio_values else 0.0
        median_comp_to_tax_ratio = median(ratio_values) if ratio_values else 0.0

        max_ratio_analysis = max(analyses, key=lambda a: a.comp_to_tax_ratio)
        max_ratio_company = max_ratio_analysis.company
        max_ratio = max_ratio_analysis.comp_to_tax_ratio

        return BatchAnalysisSummary(
            num_companies=num_companies,
            fiscal_year=fiscal_year,
            total_exec_comp_all=total_exec_comp_all,
            avg_exec_comp_per_company=avg_exec_comp_per_company,
            median_exec_comp_per_company=median_exec_comp_per_company,
            max_exec_comp_company=max_exec_comp_company,
            max_exec_comp=max_exec_comp,
            total_tax_all=total_tax_all,
            avg_tax_per_company=avg_tax_per_company,
            median_tax_per_company=median_tax_per_company,
            avg_effective_rate=avg_effective_rate,
            avg_comp_to_tax_ratio=avg_comp_to_tax_ratio,
            median_comp_to_tax_ratio=median_comp_to_tax_ratio,
            max_ratio_company=max_ratio_company,
            max_ratio=max_ratio,
        )

    def _find_ceo(self, sct_data: SCTData, fiscal_year: int) -> tuple[str, float]:
        """Find CEO name and compensation from SCT data.

        Args:
            sct_data: Executive compensation data
            fiscal_year: Fiscal year to search

        Returns:
            Tuple of (CEO name, CEO compensation) or ("", 0.0) if not found
        """
        # Common CEO title patterns
        ceo_patterns = [
            "chief executive officer",
            "ceo",
            "president and chief executive",
            "president & ceo",
            "chairman and ceo",
        ]

        for exec_data in sct_data.executives:
            title_lower = exec_data.title.lower()

            # Check if title matches CEO patterns
            if any(pattern in title_lower for pattern in ceo_patterns):
                # Find compensation for specific year
                for comp_year in exec_data.compensation:
                    if comp_year.year == fiscal_year:
                        return (exec_data.name, comp_year.total)

                # If no exact year match, return most recent (first) compensation
                if exec_data.compensation:
                    return (exec_data.name, exec_data.compensation[0].total)

        return ("", 0.0)

    def _get_comp_for_year(self, sct_data: SCTData, year: int) -> list[float]:
        """Get all executive compensations for a specific year.

        Args:
            sct_data: Executive compensation data
            year: Fiscal year to extract

        Returns:
            List of total compensation values for all executives in that year
        """
        comp_list = []

        for exec_data in sct_data.executives:
            for comp_year in exec_data.compensation:
                if comp_year.year == year:
                    comp_list.append(comp_year.total)
                    break

        return comp_list

    def _get_tax_for_year(self, tax_data: TaxData, year: int) -> TaxYear | None:
        """Get tax data for a specific year.

        Args:
            tax_data: Corporate tax data
            year: Fiscal year to extract

        Returns:
            TaxYear for specified year, or None if not found
        """
        for tax_year in tax_data.tax_years:
            if tax_year.year == year:
                return tax_year

        return None

    def _compute_rankings(
        self,
        analyses: list[CompTaxAnalysis],
    ) -> list[CompTaxAnalysis]:
        """Compute and assign rankings to all analyses.

        Args:
            analyses: List of analyses without rankings

        Returns:
            New list of analyses with rankings populated
        """
        # Sort by total exec compensation (descending)
        sorted_by_comp = sorted(analyses, key=lambda a: a.total_exec_comp, reverse=True)

        # Sort by total tax expense (descending)
        sorted_by_tax = sorted(analyses, key=lambda a: a.total_tax_expense, reverse=True)

        # Sort by comp/tax ratio (descending)
        sorted_by_ratio = sorted(analyses, key=lambda a: a.comp_to_tax_ratio, reverse=True)

        # Create ranking maps
        comp_ranks = {a.cik: rank + 1 for rank, a in enumerate(sorted_by_comp)}
        tax_ranks = {a.cik: rank + 1 for rank, a in enumerate(sorted_by_tax)}
        ratio_ranks = {a.cik: rank + 1 for rank, a in enumerate(sorted_by_ratio)}

        # Create new analyses with rankings
        ranked_analyses = []
        for analysis in analyses:
            # Create new analysis with rankings populated
            ranked_analysis = analysis.model_copy(
                update={
                    "comp_rank": comp_ranks[analysis.cik],
                    "tax_rank": tax_ranks[analysis.cik],
                    "ratio_rank": ratio_ranks[analysis.cik],
                }
            )
            ranked_analyses.append(ranked_analysis)

        return ranked_analyses
