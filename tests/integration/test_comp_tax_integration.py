"""Integration tests for CompTaxAnalyzer with realistic data scenarios."""

import pytest

from edgar.analysis import CompTaxAnalyzer
from edgar.data.fortune100 import Company
from edgar.extractors.sct.models import (
    SCTData,
    ExecutiveCompensation,
    CompensationYear,
)
from edgar.extractors.tax.models import TaxData, TaxYear


class TestCompTaxIntegration:
    """Integration tests simulating real-world usage."""

    def test_fortune100_top10_analysis(self) -> None:
        """Test analysis of top 10 Fortune 100 companies with realistic data."""
        analyzer = CompTaxAnalyzer()

        # Simulate realistic top 10 Fortune 100 data
        companies_data = []

        # Walmart (#1) - Retail
        companies_data.append(
            (
                Company(
                    rank=1,
                    name="Walmart Inc.",
                    ticker="WMT",
                    cik="0000104169",
                    sector="Retail",
                ),
                SCTData(
                    company="Walmart Inc.",
                    cik="0000104169",
                    filing_date="2024-04-15",
                    executives=[
                        ExecutiveCompensation(
                            name="Doug McMillon",
                            title="President and Chief Executive Officer",
                            compensation=[
                                CompensationYear(
                                    year=2024,
                                    salary=1_400_000.0,
                                    stock_awards=18_000_000.0,
                                    non_equity_incentive=6_000_000.0,
                                    total=25_700_000.0,
                                )
                            ],
                        ),
                        ExecutiveCompensation(
                            name="John David Rainey",
                            title="Executive VP and CFO",
                            compensation=[CompensationYear(year=2024, total=11_500_000.0)],
                        ),
                        ExecutiveCompensation(
                            name="Donna Morris",
                            title="Executive VP, Chief People Officer",
                            compensation=[CompensationYear(year=2024, total=9_200_000.0)],
                        ),
                    ],
                ),
                TaxData(
                    company="Walmart Inc.",
                    cik="0000104169",
                    filing_date="2024-03-28",
                    fiscal_year_end="2024-01-31",
                    tax_years=[
                        TaxYear(
                            year=2024,
                            current_federal=4_500_000_000.0,
                            current_state=800_000_000.0,
                            current_foreign=200_000_000.0,
                            deferred_federal=-300_000_000.0,
                            deferred_state=-50_000_000.0,
                            total_current=5_500_000_000.0,
                            total_deferred=-350_000_000.0,
                            total_tax_expense=5_150_000_000.0,
                            pretax_income=20_000_000_000.0,
                            effective_tax_rate=0.2575,
                            cash_taxes_paid=5_300_000_000.0,
                        )
                    ],
                ),
            )
        )

        # Amazon (#2) - Technology/Retail
        companies_data.append(
            (
                Company(
                    rank=2,
                    name="Amazon.com Inc.",
                    ticker="AMZN",
                    cik="0001018724",
                    sector="Technology",
                ),
                SCTData(
                    company="Amazon.com Inc.",
                    cik="0001018724",
                    filing_date="2024-04-10",
                    executives=[
                        ExecutiveCompensation(
                            name="Andrew R. Jassy",
                            title="President and CEO",
                            compensation=[
                                CompensationYear(year=2024, total=1_300_000.0)
                            ],  # Mostly stock vesting
                        ),
                        ExecutiveCompensation(
                            name="Brian T. Olsavsky",
                            title="Senior VP and CFO",
                            compensation=[CompensationYear(year=2024, total=18_000_000.0)],
                        ),
                    ],
                ),
                TaxData(
                    company="Amazon.com Inc.",
                    cik="0001018724",
                    filing_date="2024-02-02",
                    fiscal_year_end="2024-12-31",
                    tax_years=[
                        TaxYear(
                            year=2024,
                            current_federal=3_200_000_000.0,
                            current_state=500_000_000.0,
                            current_foreign=1_800_000_000.0,
                            deferred_federal=-800_000_000.0,
                            deferred_state=-100_000_000.0,
                            total_current=5_500_000_000.0,
                            total_deferred=-900_000_000.0,
                            total_tax_expense=4_600_000_000.0,
                            pretax_income=30_000_000_000.0,
                            effective_tax_rate=0.1533,
                            cash_taxes_paid=4_800_000_000.0,
                        )
                    ],
                ),
            )
        )

        # Apple (#3) - Technology
        companies_data.append(
            (
                Company(
                    rank=3,
                    name="Apple Inc.",
                    ticker="AAPL",
                    cik="0000320193",
                    sector="Technology",
                ),
                SCTData(
                    company="Apple Inc.",
                    cik="0000320193",
                    filing_date="2024-01-12",
                    executives=[
                        ExecutiveCompensation(
                            name="Timothy D. Cook",
                            title="Chief Executive Officer",
                            compensation=[
                                CompensationYear(year=2024, total=63_200_000.0)
                            ],
                        ),
                        ExecutiveCompensation(
                            name="Luca Maestri",
                            title="Senior VP and CFO",
                            compensation=[CompensationYear(year=2024, total=27_000_000.0)],
                        ),
                        ExecutiveCompensation(
                            name="Kate Adams",
                            title="Senior VP and General Counsel",
                            compensation=[CompensationYear(year=2024, total=27_000_000.0)],
                        ),
                    ],
                ),
                TaxData(
                    company="Apple Inc.",
                    cik="0000320193",
                    filing_date="2023-11-03",
                    fiscal_year_end="2024-09-30",
                    tax_years=[
                        TaxYear(
                            year=2024,
                            current_federal=8_000_000_000.0,
                            current_state=1_200_000_000.0,
                            current_foreign=5_800_000_000.0,
                            deferred_federal=-500_000_000.0,
                            deferred_state=-100_000_000.0,
                            total_current=15_000_000_000.0,
                            total_deferred=-600_000_000.0,
                            total_tax_expense=14_400_000_000.0,
                            pretax_income=120_000_000_000.0,
                            effective_tax_rate=0.1200,
                            cash_taxes_paid=15_200_000_000.0,
                        )
                    ],
                ),
            )
        )

        # Perform batch analysis
        analyses = analyzer.analyze_batch(companies_data, fiscal_year=2024)

        # Verify we got all companies
        assert len(analyses) == 3

        # Find specific companies
        walmart = next(a for a in analyses if a.ticker == "WMT")
        amazon = next(a for a in analyses if a.ticker == "AMZN")
        apple = next(a for a in analyses if a.ticker == "AAPL")

        # Verify Walmart analysis
        assert walmart.company == "Walmart Inc."
        assert walmart.num_executives == 3
        assert walmart.ceo_name == "Doug McMillon"
        assert walmart.ceo_comp == 25_700_000.0
        assert walmart.total_tax_expense == 5_150_000_000.0

        # Verify Amazon analysis
        assert amazon.company == "Amazon.com Inc."
        assert amazon.ceo_name == "Andrew R. Jassy"
        assert amazon.total_tax_expense == 4_600_000_000.0

        # Verify Apple analysis
        assert apple.company == "Apple Inc."
        assert apple.ceo_name == "Timothy D. Cook"
        assert apple.ceo_comp == 63_200_000.0
        assert apple.total_tax_expense == 14_400_000_000.0

        # Verify rankings make sense
        # Apple should have highest exec comp
        assert apple.comp_rank == 1
        # Apple should have highest tax
        assert apple.tax_rank == 1

        # Generate and verify summary
        summary = analyzer.generate_summary(analyses)

        assert summary.num_companies == 3
        assert summary.fiscal_year == 2024
        assert summary.total_exec_comp_all > 0
        assert summary.total_tax_all > 0
        assert summary.avg_effective_rate > 0
        assert summary.max_exec_comp_company == "Apple Inc."

    def test_multi_year_analysis(self) -> None:
        """Test analyzing different fiscal years for same company."""
        analyzer = CompTaxAnalyzer()

        company = Company(
            rank=1, name="Test Corp", ticker="TEST", cik="0000000001", sector="Tech"
        )

        # Multi-year compensation data
        sct_data = SCTData(
            company="Test Corp",
            cik="0000000001",
            filing_date="2024-04-01",
            executives=[
                ExecutiveCompensation(
                    name="CEO Name",
                    title="Chief Executive Officer",
                    compensation=[
                        CompensationYear(year=2024, total=10_000_000.0),
                        CompensationYear(year=2023, total=8_000_000.0),
                        CompensationYear(year=2022, total=7_000_000.0),
                    ],
                ),
            ],
        )

        # Multi-year tax data
        tax_data = TaxData(
            company="Test Corp",
            cik="0000000001",
            filing_date="2024-03-01",
            fiscal_year_end="2023-12-31",
            tax_years=[
                TaxYear(year=2024, total_tax_expense=500_000_000.0, pretax_income=2_000_000_000.0),
                TaxYear(year=2023, total_tax_expense=450_000_000.0, pretax_income=1_800_000_000.0),
                TaxYear(year=2022, total_tax_expense=400_000_000.0, pretax_income=1_600_000_000.0),
            ],
        )

        # Analyze different years
        analysis_2024 = analyzer.analyze_single(company, sct_data, tax_data, fiscal_year=2024)
        analysis_2023 = analyzer.analyze_single(company, sct_data, tax_data, fiscal_year=2023)
        analysis_2022 = analyzer.analyze_single(company, sct_data, tax_data, fiscal_year=2022)

        # Verify year-specific data
        assert analysis_2024.fiscal_year == 2024
        assert analysis_2024.ceo_comp == 10_000_000.0
        assert analysis_2024.total_tax_expense == 500_000_000.0

        assert analysis_2023.fiscal_year == 2023
        assert analysis_2023.ceo_comp == 8_000_000.0
        assert analysis_2023.total_tax_expense == 450_000_000.0

        assert analysis_2022.fiscal_year == 2022
        assert analysis_2022.ceo_comp == 7_000_000.0
        assert analysis_2022.total_tax_expense == 400_000_000.0

        # Verify ratios are calculated for each year
        assert analysis_2024.comp_to_tax_ratio == pytest.approx(0.02, rel=1e-2)
        assert analysis_2023.comp_to_tax_ratio == pytest.approx(0.0178, rel=1e-2)
        assert analysis_2022.comp_to_tax_ratio == pytest.approx(0.0175, rel=1e-2)

    def test_sector_comparison(self) -> None:
        """Test analyzing companies across different sectors."""
        analyzer = CompTaxAnalyzer()

        # Tech company - high comp, moderate tax
        tech_company = (
            Company(
                rank=10, name="Tech Giant", ticker="TECH", cik="0000000010", sector="Technology"
            ),
            SCTData(
                company="Tech Giant",
                cik="0000000010",
                filing_date="2024-01-01",
                executives=[
                    ExecutiveCompensation(
                        name="Tech CEO",
                        title="CEO",
                        compensation=[CompensationYear(year=2024, total=50_000_000.0)],
                    )
                ],
            ),
            TaxData(
                company="Tech Giant",
                cik="0000000010",
                filing_date="2024-01-01",
                fiscal_year_end="2023-12-31",
                tax_years=[
                    TaxYear(
                        year=2024,
                        total_tax_expense=3_000_000_000.0,
                        pretax_income=20_000_000_000.0,
                        effective_tax_rate=0.15,
                    )
                ],
            ),
        )

        # Retail company - moderate comp, high tax
        retail_company = (
            Company(
                rank=20, name="Retail Giant", ticker="RTL", cik="0000000020", sector="Retail"
            ),
            SCTData(
                company="Retail Giant",
                cik="0000000020",
                filing_date="2024-01-01",
                executives=[
                    ExecutiveCompensation(
                        name="Retail CEO",
                        title="CEO",
                        compensation=[CompensationYear(year=2024, total=20_000_000.0)],
                    )
                ],
            ),
            TaxData(
                company="Retail Giant",
                cik="0000000020",
                filing_date="2024-01-01",
                fiscal_year_end="2023-12-31",
                tax_years=[
                    TaxYear(
                        year=2024,
                        total_tax_expense=5_000_000_000.0,
                        pretax_income=20_000_000_000.0,
                        effective_tax_rate=0.25,
                    )
                ],
            ),
        )

        # Financial company - high comp, high tax
        finance_company = (
            Company(
                rank=30, name="Finance Corp", ticker="FIN", cik="0000000030", sector="Finance"
            ),
            SCTData(
                company="Finance Corp",
                cik="0000000030",
                filing_date="2024-01-01",
                executives=[
                    ExecutiveCompensation(
                        name="Finance CEO",
                        title="CEO",
                        compensation=[CompensationYear(year=2024, total=40_000_000.0)],
                    )
                ],
            ),
            TaxData(
                company="Finance Corp",
                cik="0000000030",
                filing_date="2024-01-01",
                fiscal_year_end="2023-12-31",
                tax_years=[
                    TaxYear(
                        year=2024,
                        total_tax_expense=4_000_000_000.0,
                        pretax_income=15_000_000_000.0,
                        effective_tax_rate=0.2667,
                    )
                ],
            ),
        )

        analyses = analyzer.analyze_batch(
            [tech_company, retail_company, finance_company], fiscal_year=2024
        )

        # Verify sector-specific patterns
        tech = next(a for a in analyses if a.ticker == "TECH")
        retail = next(a for a in analyses if a.ticker == "RTL")
        finance = next(a for a in analyses if a.ticker == "FIN")

        # Tech should have highest comp/tax ratio
        assert tech.comp_to_tax_ratio > retail.comp_to_tax_ratio
        assert tech.comp_to_tax_ratio > finance.comp_to_tax_ratio

        # Retail should have lowest comp/tax ratio
        assert retail.comp_to_tax_ratio < tech.comp_to_tax_ratio
        assert retail.comp_to_tax_ratio < finance.comp_to_tax_ratio

        # Verify effective tax rates vary by sector
        assert tech.effective_tax_rate == 0.15
        assert retail.effective_tax_rate == 0.25
        assert finance.effective_tax_rate == pytest.approx(0.2667, rel=1e-3)
