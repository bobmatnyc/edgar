"""Demo script showing how to use the CompTaxAnalyzer.

This example demonstrates:
1. Analyzing a single company
2. Batch analysis with rankings
3. Generating summary statistics
"""

from edgar.analysis import CompTaxAnalyzer
from edgar.data.fortune100 import Company
from edgar.extractors.sct.models import (
    SCTData,
    ExecutiveCompensation,
    CompensationYear,
)
from edgar.extractors.tax.models import TaxData, TaxYear


def create_sample_data() -> tuple[Company, SCTData, TaxData]:
    """Create sample data for demonstration."""
    # Sample company
    company = Company(
        rank=1,
        name="Example Corp",
        ticker="EXMP",
        cik="0000012345",
        sector="Technology",
    )

    # Sample executive compensation data
    sct_data = SCTData(
        company="Example Corp",
        cik="0000012345",
        filing_date="2024-03-15",
        executives=[
            ExecutiveCompensation(
                name="Jane Doe",
                title="Chief Executive Officer",
                compensation=[
                    CompensationYear(
                        year=2023,
                        salary=1_200_000.0,
                        bonus=600_000.0,
                        stock_awards=4_000_000.0,
                        option_awards=2_000_000.0,
                        non_equity_incentive=1_000_000.0,
                        pension_change=300_000.0,
                        other_compensation=150_000.0,
                        total=9_250_000.0,
                    )
                ],
            ),
            ExecutiveCompensation(
                name="John Smith",
                title="Chief Financial Officer",
                compensation=[
                    CompensationYear(year=2023, total=5_500_000.0)
                ],
            ),
            ExecutiveCompensation(
                name="Alice Johnson",
                title="Chief Technology Officer",
                compensation=[
                    CompensationYear(year=2023, total=4_800_000.0)
                ],
            ),
        ],
    )

    # Sample corporate tax data
    tax_data = TaxData(
        company="Example Corp",
        cik="0000012345",
        filing_date="2024-02-15",
        fiscal_year_end="2023-12-31",
        tax_years=[
            TaxYear(
                year=2023,
                current_federal=900_000_000.0,
                current_state=180_000_000.0,
                current_foreign=70_000_000.0,
                deferred_federal=-120_000_000.0,
                deferred_state=-25_000_000.0,
                deferred_foreign=15_000_000.0,
                total_current=1_150_000_000.0,
                total_deferred=-130_000_000.0,
                total_tax_expense=1_020_000_000.0,
                pretax_income=4_500_000_000.0,
                effective_tax_rate=0.2267,
                cash_taxes_paid=1_100_000_000.0,
            )
        ],
    )

    return company, sct_data, tax_data


def demo_single_analysis() -> None:
    """Demonstrate single company analysis."""
    print("=" * 80)
    print("DEMO: Single Company Analysis")
    print("=" * 80)

    # Create analyzer
    analyzer = CompTaxAnalyzer()

    # Get sample data
    company, sct_data, tax_data = create_sample_data()

    # Analyze
    analysis = analyzer.analyze_single(company, sct_data, tax_data, fiscal_year=2023)

    # Print results
    print(f"\nCompany: {analysis.company} ({analysis.ticker})")
    print(f"Fiscal Year: {analysis.fiscal_year}")
    print("\nExecutive Compensation:")
    print(f"  Number of Executives: {analysis.num_executives}")
    print(f"  Total Compensation: ${analysis.total_exec_comp:,.0f}")
    print(f"  CEO: {analysis.ceo_name}")
    print(f"  CEO Compensation: ${analysis.ceo_comp:,.0f}")
    print(f"  Average Compensation: ${analysis.avg_exec_comp:,.0f}")
    print(f"  Median Compensation: ${analysis.median_exec_comp:,.0f}")

    print("\nCorporate Tax:")
    print(f"  Total Tax Expense: ${analysis.total_tax_expense:,.0f}")
    print(f"  Current Tax: ${analysis.current_tax:,.0f}")
    print(f"  Deferred Tax: ${analysis.deferred_tax:,.0f}")
    print(f"  Effective Tax Rate: {analysis.effective_tax_rate:.2%}")
    print(f"  Cash Taxes Paid: ${analysis.cash_taxes_paid:,.0f}")
    print(f"  Pre-tax Income: ${analysis.pretax_income:,.0f}")

    print("\nComparison Ratios:")
    print(f"  Exec Comp / Tax Expense: {analysis.comp_to_tax_ratio:.4f}")
    print(f"  CEO Comp / Tax Expense: {analysis.ceo_to_tax_ratio:.4f}")
    print(f"  Exec Comp / Pre-tax Income: {analysis.comp_to_pretax_ratio:.4f}")
    print(f"  Exec Comp / Cash Taxes: {analysis.comp_to_cash_tax_ratio:.4f}")


def demo_batch_analysis() -> None:
    """Demonstrate batch analysis with rankings."""
    print("\n" + "=" * 80)
    print("DEMO: Batch Analysis with Rankings")
    print("=" * 80)

    # Create analyzer
    analyzer = CompTaxAnalyzer()

    # Create multiple companies with different characteristics
    companies_data = [
        # Company 1: High compensation, moderate tax
        (
            Company(rank=1, name="High Comp Inc", ticker="HCI", cik="0000000001", sector="Tech"),
            SCTData(
                company="High Comp Inc",
                cik="0000000001",
                filing_date="2024-01-01",
                executives=[
                    ExecutiveCompensation(
                        name="CEO A",
                        title="Chief Executive Officer",
                        compensation=[CompensationYear(year=2023, total=12_000_000.0)],
                    )
                ],
            ),
            TaxData(
                company="High Comp Inc",
                cik="0000000001",
                filing_date="2024-01-01",
                fiscal_year_end="2023-12-31",
                tax_years=[
                    TaxYear(
                        year=2023,
                        total_tax_expense=600_000_000.0,
                        pretax_income=2_500_000_000.0,
                        effective_tax_rate=0.24,
                        cash_taxes_paid=650_000_000.0,
                    )
                ],
            ),
        ),
        # Company 2: Moderate compensation, high tax
        (
            Company(rank=2, name="High Tax Corp", ticker="HTC", cik="0000000002", sector="Finance"),
            SCTData(
                company="High Tax Corp",
                cik="0000000002",
                filing_date="2024-01-01",
                executives=[
                    ExecutiveCompensation(
                        name="CEO B",
                        title="CEO",
                        compensation=[CompensationYear(year=2023, total=7_000_000.0)],
                    )
                ],
            ),
            TaxData(
                company="High Tax Corp",
                cik="0000000002",
                filing_date="2024-01-01",
                fiscal_year_end="2023-12-31",
                tax_years=[
                    TaxYear(
                        year=2023,
                        total_tax_expense=1_200_000_000.0,
                        pretax_income=5_000_000_000.0,
                        effective_tax_rate=0.24,
                        cash_taxes_paid=1_250_000_000.0,
                    )
                ],
            ),
        ),
        # Company 3: Low compensation, low tax (high ratio)
        (
            Company(rank=3, name="Low Tax LLC", ticker="LTL", cik="0000000003", sector="Retail"),
            SCTData(
                company="Low Tax LLC",
                cik="0000000003",
                filing_date="2024-01-01",
                executives=[
                    ExecutiveCompensation(
                        name="CEO C",
                        title="CEO",
                        compensation=[CompensationYear(year=2023, total=5_000_000.0)],
                    )
                ],
            ),
            TaxData(
                company="Low Tax LLC",
                cik="0000000003",
                filing_date="2024-01-01",
                fiscal_year_end="2023-12-31",
                tax_years=[
                    TaxYear(
                        year=2023,
                        total_tax_expense=50_000_000.0,
                        pretax_income=250_000_000.0,
                        effective_tax_rate=0.20,
                        cash_taxes_paid=55_000_000.0,
                    )
                ],
            ),
        ),
    ]

    # Perform batch analysis
    analyses = analyzer.analyze_batch(companies_data, fiscal_year=2023)

    # Print results
    print("\nRanked Results:")
    print("-" * 80)

    for analysis in sorted(analyses, key=lambda a: a.rank):
        print(f"\n{analysis.company} ({analysis.ticker})")
        print(f"  Compensation: ${analysis.total_exec_comp:,.0f} (Rank #{analysis.comp_rank})")
        print(f"  Tax Expense: ${analysis.total_tax_expense:,.0f} (Rank #{analysis.tax_rank})")
        print(f"  Comp/Tax Ratio: {analysis.comp_to_tax_ratio:.4f} (Rank #{analysis.ratio_rank})")

    # Generate and display summary
    print("\n" + "=" * 80)
    print("DEMO: Batch Summary Statistics")
    print("=" * 80)

    summary = analyzer.generate_summary(analyses)

    print(f"\nAggregate Statistics for {summary.num_companies} companies (FY {summary.fiscal_year})")

    print("\nExecutive Compensation:")
    print(f"  Total (All Companies): ${summary.total_exec_comp_all:,.0f}")
    print(f"  Average per Company: ${summary.avg_exec_comp_per_company:,.0f}")
    print(f"  Median per Company: ${summary.median_exec_comp_per_company:,.0f}")
    print(f"  Highest: {summary.max_exec_comp_company} (${summary.max_exec_comp:,.0f})")

    print("\nCorporate Tax:")
    print(f"  Total (All Companies): ${summary.total_tax_all:,.0f}")
    print(f"  Average per Company: ${summary.avg_tax_per_company:,.0f}")
    print(f"  Median per Company: ${summary.median_tax_per_company:,.0f}")
    print(f"  Average Effective Rate: {summary.avg_effective_rate:.2%}")

    print("\nComparison Ratios:")
    print(f"  Average Comp/Tax Ratio: {summary.avg_comp_to_tax_ratio:.4f}")
    print(f"  Median Comp/Tax Ratio: {summary.median_comp_to_tax_ratio:.4f}")
    print(f"  Highest Ratio: {summary.max_ratio_company} ({summary.max_ratio:.4f})")


if __name__ == "__main__":
    # Run demos
    demo_single_analysis()
    demo_batch_analysis()

    print("\n" + "=" * 80)
    print("Demo completed!")
    print("=" * 80)
