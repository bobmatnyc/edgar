"""Demonstration of CSV export functionality.

This script shows how to use the CSVExporter to export executive compensation
and corporate tax data to CSV format.
"""

from pathlib import Path

from edgar.data.fortune100 import Company
from edgar.exporters import CSVExporter
from edgar.extractors.sct.models import (
    CompensationYear,
    ExecutiveCompensation,
    SCTData,
)
from edgar.extractors.tax.models import TaxData, TaxYear


def create_sample_data() -> tuple[
    list[tuple[Company, SCTData]], list[tuple[Company, TaxData]]
]:
    """Create sample data for demonstration."""
    # Sample company: Apple Inc.
    apple = Company(
        rank=3, name="Apple Inc.", ticker="AAPL", cik="0000320193", sector="Technology"
    )

    # Sample executive compensation data
    apple_sct = SCTData(
        company="Apple Inc.",
        cik="0000320193",
        filing_date="2024-10-31",
        executives=[
            ExecutiveCompensation(
                name="Timothy D. Cook",
                title="CEO",
                compensation=[
                    CompensationYear(
                        year=2024,
                        salary=3000000.0,
                        bonus=0.0,
                        stock_awards=58128634.0,
                        option_awards=0.0,
                        non_equity_incentive=12000000.0,
                        pension_change=0.0,
                        other_compensation=1523232.0,
                        total=74651866.0,
                    )
                ],
            ),
            ExecutiveCompensation(
                name="Luca Maestri",
                title="CFO",
                compensation=[
                    CompensationYear(
                        year=2024,
                        salary=1000000.0,
                        bonus=0.0,
                        stock_awards=20000000.0,
                        option_awards=0.0,
                        non_equity_incentive=5000000.0,
                        pension_change=0.0,
                        other_compensation=500000.0,
                        total=26500000.0,
                    )
                ],
            ),
        ],
    )

    # Sample corporate tax data
    apple_tax = TaxData(
        company="Apple Inc.",
        cik="0000320193",
        filing_date="2024-10-31",
        fiscal_year_end="2024-09-30",
        tax_years=[
            TaxYear(
                year=2024,
                current_federal=12500000000.0,
                current_state=1200000000.0,
                current_foreign=8000000000.0,
                total_current=21700000000.0,
                deferred_federal=-500000000.0,
                deferred_state=-50000000.0,
                deferred_foreign=200000000.0,
                total_deferred=-350000000.0,
                total_tax_expense=21350000000.0,
                pretax_income=100000000000.0,
                effective_tax_rate=0.2135,
                cash_taxes_paid=20000000000.0,
            )
        ],
    )

    comp_results = [(apple, apple_sct)]
    tax_results = [(apple, apple_tax)]

    return comp_results, tax_results


def main() -> None:
    """Run CSV export demonstration."""
    print("CSV Export Demonstration")
    print("=" * 60)

    # Create sample data
    comp_results, tax_results = create_sample_data()

    # Create exporter with custom output directory
    output_dir = Path("demo_output")
    exporter = CSVExporter(output_dir=output_dir)

    # Export executive compensation
    print("\n1. Exporting executive compensation data...")
    comp_path = exporter.export_compensation(comp_results)
    print(f"   ✓ Created: {comp_path}")
    print(f"   Size: {comp_path.stat().st_size} bytes")

    # Export corporate tax data
    print("\n2. Exporting corporate tax data...")
    tax_path = exporter.export_tax(tax_results)
    print(f"   ✓ Created: {tax_path}")
    print(f"   Size: {tax_path.stat().st_size} bytes")

    # Export combined analysis
    print("\n3. Exporting combined compensation vs tax analysis...")
    combined_path = exporter.export_combined(comp_results, tax_results)
    print(f"   ✓ Created: {combined_path}")
    print(f"   Size: {combined_path.stat().st_size} bytes")

    print("\n" + "=" * 60)
    print(f"All exports completed successfully!")
    print(f"Output directory: {output_dir.absolute()}")
    print("\nGenerated files:")
    print(f"  - {comp_path.name}")
    print(f"  - {tax_path.name}")
    print(f"  - {combined_path.name}")


if __name__ == "__main__":
    main()
