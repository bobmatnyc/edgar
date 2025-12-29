"""CSV export functionality for extraction results."""

import csv
from dataclasses import dataclass
from pathlib import Path

from edgar.data.fortune100 import Company
from edgar.extractors.sct.models import SCTData
from edgar.extractors.tax.models import TaxData


@dataclass(frozen=True)
class CSVExporter:
    """Export extraction results to CSV format.

    Generates three types of CSV files:
    1. Executive Compensation - one row per executive per year
    2. Corporate Tax - one row per company per year
    3. Combined Analysis - comparison of exec comp vs tax
    """

    output_dir: Path = Path("output")

    def export_compensation(
        self,
        results: list[tuple[Company, SCTData]],
        filename: str = "executive_compensation.csv",
    ) -> Path:
        """Export executive compensation data to CSV.

        CSV Schema:
        rank, company, ticker, cik, fiscal_year, executive_name, title,
        salary, bonus, stock_awards, option_awards, non_equity_incentive,
        pension_change, other_comp, total_comp

        Args:
            results: List of (Company, SCTData) tuples
            filename: Output filename

        Returns:
            Path to created CSV file
        """
        self._ensure_output_dir()
        output_path = self.output_dir / filename

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "rank",
                    "company",
                    "ticker",
                    "cik",
                    "fiscal_year",
                    "executive_name",
                    "title",
                    "salary",
                    "bonus",
                    "stock_awards",
                    "option_awards",
                    "non_equity_incentive",
                    "pension_change",
                    "other_comp",
                    "total_comp",
                ]
            )

            # Write data rows
            for company, sct_data in results:
                for executive in sct_data.executives:
                    for comp_year in executive.compensation:
                        writer.writerow(
                            [
                                company.rank,
                                company.name,
                                company.ticker,
                                company.cik,
                                comp_year.year,
                                executive.name,
                                executive.title,
                                self._format_currency(comp_year.salary),
                                self._format_currency(comp_year.bonus),
                                self._format_currency(comp_year.stock_awards),
                                self._format_currency(comp_year.option_awards),
                                self._format_currency(comp_year.non_equity_incentive),
                                self._format_currency(comp_year.pension_change),
                                self._format_currency(comp_year.other_compensation),
                                self._format_currency(comp_year.total),
                            ]
                        )

        return output_path

    def export_tax(
        self,
        results: list[tuple[Company, TaxData]],
        filename: str = "corporate_tax.csv",
    ) -> Path:
        """Export corporate tax data to CSV.

        CSV Schema:
        rank, company, ticker, cik, fiscal_year, current_federal, current_state,
        current_foreign, total_current, deferred_federal, deferred_state,
        deferred_foreign, total_deferred, total_tax_expense, pretax_income,
        effective_tax_rate, cash_taxes_paid

        Args:
            results: List of (Company, TaxData) tuples
            filename: Output filename

        Returns:
            Path to created CSV file
        """
        self._ensure_output_dir()
        output_path = self.output_dir / filename

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "rank",
                    "company",
                    "ticker",
                    "cik",
                    "fiscal_year",
                    "current_federal",
                    "current_state",
                    "current_foreign",
                    "total_current",
                    "deferred_federal",
                    "deferred_state",
                    "deferred_foreign",
                    "total_deferred",
                    "total_tax_expense",
                    "pretax_income",
                    "effective_tax_rate",
                    "cash_taxes_paid",
                ]
            )

            # Write data rows
            for company, tax_data in results:
                for tax_year in tax_data.tax_years:
                    writer.writerow(
                        [
                            company.rank,
                            company.name,
                            company.ticker,
                            company.cik,
                            tax_year.year,
                            self._format_currency(tax_year.current_federal),
                            self._format_currency(tax_year.current_state),
                            self._format_currency(tax_year.current_foreign),
                            self._format_currency(tax_year.total_current),
                            self._format_currency(tax_year.deferred_federal),
                            self._format_currency(tax_year.deferred_state),
                            self._format_currency(tax_year.deferred_foreign),
                            self._format_currency(tax_year.total_deferred),
                            self._format_currency(tax_year.total_tax_expense),
                            self._format_currency(tax_year.pretax_income),
                            self._format_percent(tax_year.effective_tax_rate),
                            self._format_currency(tax_year.cash_taxes_paid),
                        ]
                    )

        return output_path

    def export_combined(
        self,
        comp_results: list[tuple[Company, SCTData]],
        tax_results: list[tuple[Company, TaxData]],
        filename: str = "compensation_vs_tax.csv",
    ) -> Path:
        """Export combined analysis comparing exec comp to corporate tax.

        CSV Schema:
        rank, company, ticker, cik, fiscal_year, num_executives, total_exec_comp,
        ceo_name, ceo_comp, median_exec_comp, total_tax_expense, effective_tax_rate,
        cash_taxes_paid, comp_to_tax_ratio, ceo_to_tax_ratio

        Args:
            comp_results: List of (Company, SCTData) tuples
            tax_results: List of (Company, TaxData) tuples
            filename: Output filename

        Returns:
            Path to created CSV file
        """
        self._ensure_output_dir()
        output_path = self.output_dir / filename

        # Build lookup tables by (CIK, year)
        comp_by_cik_year: dict[tuple[str, int], tuple[Company, SCTData]] = {}
        for company, sct_data in comp_results:
            # Group compensation data by year
            years_in_data: set[int] = set()
            for executive in sct_data.executives:
                for comp_year in executive.compensation:
                    years_in_data.add(comp_year.year)

            # Create entries for each year
            for year in years_in_data:
                comp_by_cik_year[(company.cik, year)] = (company, sct_data)

        tax_by_cik_year: dict[tuple[str, int], tuple[Company, TaxData]] = {}
        for company, tax_data in tax_results:
            for tax_year in tax_data.tax_years:
                tax_by_cik_year[(company.cik, tax_year.year)] = (company, tax_data)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "rank",
                    "company",
                    "ticker",
                    "cik",
                    "fiscal_year",
                    "num_executives",
                    "total_exec_comp",
                    "ceo_name",
                    "ceo_comp",
                    "median_exec_comp",
                    "total_tax_expense",
                    "effective_tax_rate",
                    "cash_taxes_paid",
                    "comp_to_tax_ratio",
                    "ceo_to_tax_ratio",
                ]
            )

            # Iterate over all unique (CIK, year) combinations
            # Sort by CIK ascending, then year descending (latest first)
            all_keys = set(comp_by_cik_year.keys()) | set(tax_by_cik_year.keys())

            for cik, year in sorted(all_keys, key=lambda x: (x[0], -x[1])):
                # Get compensation data for this year
                comp_entry = comp_by_cik_year.get((cik, year))
                tax_entry = tax_by_cik_year.get((cik, year))

                if not comp_entry or not tax_entry:
                    continue  # Skip if missing either dataset

                company, sct_data = comp_entry
                _, tax_data = tax_entry

                # Calculate compensation metrics for this year
                year_compensations: list[float] = []
                ceo_name = ""
                ceo_comp = 0.0

                for executive in sct_data.executives:
                    for comp_year in executive.compensation:
                        if comp_year.year == year:
                            year_compensations.append(comp_year.total)

                            # Identify CEO
                            if "CEO" in executive.title.upper() or "Chief Executive" in executive.title:
                                ceo_name = executive.name
                                ceo_comp = comp_year.total

                if not year_compensations:
                    continue  # Skip if no compensation data for this year

                num_executives = len(year_compensations)
                total_exec_comp = sum(year_compensations)

                # Calculate median compensation
                sorted_comps = sorted(year_compensations)
                if num_executives % 2 == 0:
                    median_exec_comp = (
                        sorted_comps[num_executives // 2 - 1]
                        + sorted_comps[num_executives // 2]
                    ) / 2
                else:
                    median_exec_comp = sorted_comps[num_executives // 2]

                # Get tax data for this year
                tax_year_data = next(
                    (ty for ty in tax_data.tax_years if ty.year == year), None
                )
                if not tax_year_data:
                    continue

                total_tax_expense = tax_year_data.total_tax_expense
                effective_tax_rate = tax_year_data.effective_tax_rate
                cash_taxes_paid = tax_year_data.cash_taxes_paid

                # Calculate ratios
                comp_to_tax_ratio = (
                    total_exec_comp / total_tax_expense if total_tax_expense > 0 else 0.0
                )
                ceo_to_tax_ratio = (
                    ceo_comp / total_tax_expense if total_tax_expense > 0 else 0.0
                )

                writer.writerow(
                    [
                        company.rank,
                        company.name,
                        company.ticker,
                        company.cik,
                        year,
                        num_executives,
                        self._format_currency(total_exec_comp),
                        ceo_name,
                        self._format_currency(ceo_comp),
                        self._format_currency(median_exec_comp),
                        self._format_currency(total_tax_expense),
                        self._format_percent(effective_tax_rate),
                        self._format_currency(cash_taxes_paid),
                        f"{comp_to_tax_ratio:.6f}",
                        f"{ceo_to_tax_ratio:.6f}",
                    ]
                )

        return output_path

    def _ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _format_currency(self, value: float) -> str:
        """Format number as currency string.

        Args:
            value: Numeric value to format

        Returns:
            Formatted currency string with two decimal places
        """
        return f"{value:,.2f}"

    def _format_percent(self, value: float) -> str:
        """Format decimal as percentage.

        Args:
            value: Decimal value (0-1) to format as percentage

        Returns:
            Formatted percentage string
        """
        return f"{value * 100:.2f}%"
