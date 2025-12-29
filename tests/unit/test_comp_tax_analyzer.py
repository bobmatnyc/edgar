"""Unit tests for executive compensation vs. tax analyzer."""

import pytest

from edgar.analysis import CompTaxAnalyzer, CompTaxAnalysis
from edgar.data.fortune100 import Company
from edgar.extractors.sct.models import (
    SCTData,
    ExecutiveCompensation,
    CompensationYear,
)
from edgar.extractors.tax.models import TaxData, TaxYear


# Test fixtures
@pytest.fixture
def sample_company() -> Company:
    """Create sample Fortune 100 company."""
    return Company(
        rank=1,
        name="Test Corp",
        ticker="TEST",
        cik="0000012345",
        sector="Technology",
    )


@pytest.fixture
def sample_sct_data() -> SCTData:
    """Create sample executive compensation data."""
    return SCTData(
        company="Test Corp",
        cik="0000012345",
        filing_date="2024-03-15",
        executives=[
            ExecutiveCompensation(
                name="John CEO",
                title="Chief Executive Officer",
                compensation=[
                    CompensationYear(
                        year=2023,
                        salary=1_000_000.0,
                        bonus=500_000.0,
                        stock_awards=3_000_000.0,
                        option_awards=1_500_000.0,
                        non_equity_incentive=800_000.0,
                        pension_change=200_000.0,
                        other_compensation=100_000.0,
                        total=7_100_000.0,
                    ),
                    CompensationYear(
                        year=2022,
                        total=6_500_000.0,
                    ),
                ],
            ),
            ExecutiveCompensation(
                name="Jane CFO",
                title="Chief Financial Officer",
                compensation=[
                    CompensationYear(
                        year=2023,
                        total=4_200_000.0,
                    ),
                ],
            ),
            ExecutiveCompensation(
                name="Bob CTO",
                title="Chief Technology Officer",
                compensation=[
                    CompensationYear(
                        year=2023,
                        total=3_800_000.0,
                    ),
                ],
            ),
        ],
    )


@pytest.fixture
def sample_tax_data() -> TaxData:
    """Create sample corporate tax data."""
    return TaxData(
        company="Test Corp",
        cik="0000012345",
        filing_date="2024-02-15",
        fiscal_year_end="2023-12-31",
        tax_years=[
            TaxYear(
                year=2023,
                current_federal=800_000_000.0,
                current_state=150_000_000.0,
                current_foreign=50_000_000.0,
                deferred_federal=-100_000_000.0,
                deferred_state=-20_000_000.0,
                deferred_foreign=10_000_000.0,
                total_current=1_000_000_000.0,
                total_deferred=-110_000_000.0,
                total_tax_expense=890_000_000.0,
                pretax_income=4_000_000_000.0,
                effective_tax_rate=0.2225,
                cash_taxes_paid=950_000_000.0,
            ),
            TaxYear(
                year=2022,
                total_tax_expense=850_000_000.0,
                pretax_income=3_800_000_000.0,
                effective_tax_rate=0.2237,
            ),
        ],
    )


@pytest.fixture
def analyzer() -> CompTaxAnalyzer:
    """Create analyzer instance."""
    return CompTaxAnalyzer()


class TestCompTaxAnalyzerSingle:
    """Tests for single company analysis."""

    def test_analyze_single_basic(
        self,
        analyzer: CompTaxAnalyzer,
        sample_company: Company,
        sample_sct_data: SCTData,
        sample_tax_data: TaxData,
    ) -> None:
        """Test basic single company analysis."""
        analysis = analyzer.analyze_single(
            sample_company, sample_sct_data, sample_tax_data, fiscal_year=2023
        )

        # Company info
        assert analysis.company == "Test Corp"
        assert analysis.ticker == "TEST"
        assert analysis.cik == "0000012345"
        assert analysis.rank == 1
        assert analysis.fiscal_year == 2023

        # Executive compensation metrics
        assert analysis.num_executives == 3
        assert analysis.total_exec_comp == 15_100_000.0  # 7.1M + 4.2M + 3.8M
        assert analysis.ceo_name == "John CEO"
        assert analysis.ceo_comp == 7_100_000.0
        assert analysis.avg_exec_comp == pytest.approx(5_033_333.33, rel=1e-2)
        assert analysis.median_exec_comp == 4_200_000.0

        # Tax metrics
        assert analysis.total_tax_expense == 890_000_000.0
        assert analysis.current_tax == 1_000_000_000.0
        assert analysis.deferred_tax == -110_000_000.0
        assert analysis.effective_tax_rate == 0.2225
        assert analysis.cash_taxes_paid == 950_000_000.0
        assert analysis.pretax_income == 4_000_000_000.0

        # Ratios
        assert analysis.comp_to_tax_ratio == pytest.approx(0.01697, rel=1e-3)
        assert analysis.ceo_to_tax_ratio == pytest.approx(0.00798, rel=1e-3)
        assert analysis.comp_to_pretax_ratio == pytest.approx(0.003775, rel=1e-3)
        assert analysis.comp_to_cash_tax_ratio == pytest.approx(0.01589, rel=1e-3)

        # Rankings not populated in single analysis
        assert analysis.comp_rank is None
        assert analysis.tax_rank is None
        assert analysis.ratio_rank is None

    def test_analyze_single_auto_fiscal_year(
        self,
        analyzer: CompTaxAnalyzer,
        sample_company: Company,
        sample_sct_data: SCTData,
        sample_tax_data: TaxData,
    ) -> None:
        """Test analysis with automatic fiscal year detection."""
        analysis = analyzer.analyze_single(
            sample_company, sample_sct_data, sample_tax_data
        )

        # Should auto-detect 2023 as most recent year
        assert analysis.fiscal_year == 2023
        assert analysis.total_exec_comp == 15_100_000.0

    def test_analyze_single_zero_tax(
        self,
        analyzer: CompTaxAnalyzer,
        sample_company: Company,
        sample_sct_data: SCTData,
    ) -> None:
        """Test analysis with zero tax expense (avoid division by zero)."""
        # Tax data with zero tax
        tax_data = TaxData(
            company="Test Corp",
            cik="0000012345",
            filing_date="2024-02-15",
            fiscal_year_end="2023-12-31",
            tax_years=[
                TaxYear(
                    year=2023,
                    total_tax_expense=0.0,
                    pretax_income=0.0,
                    cash_taxes_paid=0.0,
                )
            ],
        )

        analysis = analyzer.analyze_single(
            sample_company, sample_sct_data, tax_data, fiscal_year=2023
        )

        # Ratios should be 0.0, not raise division by zero
        assert analysis.comp_to_tax_ratio == 0.0
        assert analysis.ceo_to_tax_ratio == 0.0
        assert analysis.comp_to_pretax_ratio == 0.0
        assert analysis.comp_to_cash_tax_ratio == 0.0

    def test_analyze_single_missing_year(
        self,
        analyzer: CompTaxAnalyzer,
        sample_company: Company,
        sample_sct_data: SCTData,
        sample_tax_data: TaxData,
    ) -> None:
        """Test analysis when requested year not in data."""
        analysis = analyzer.analyze_single(
            sample_company, sample_sct_data, sample_tax_data, fiscal_year=2020
        )

        # Should return analysis with zero values for missing year
        assert analysis.fiscal_year == 2020
        assert analysis.num_executives == 0
        assert analysis.total_exec_comp == 0.0
        assert analysis.total_tax_expense == 0.0

    def test_find_ceo_variations(self, analyzer: CompTaxAnalyzer) -> None:
        """Test CEO detection with various title formats."""
        test_cases = [
            ("Chief Executive Officer", True),
            ("CEO", True),
            ("President and CEO", True),
            ("Chairman and Chief Executive Officer", True),
            ("President & CEO", True),
            ("Chief Financial Officer", False),
            ("Executive Vice President", False),
        ]

        for title, should_find in test_cases:
            sct_data = SCTData(
                company="Test",
                cik="0000012345",
                filing_date="2024-01-01",
                executives=[
                    ExecutiveCompensation(
                        name="Test Exec",
                        title=title,
                        compensation=[
                            CompensationYear(year=2023, total=5_000_000.0)
                        ],
                    )
                ],
            )

            ceo_name, ceo_comp = analyzer._find_ceo(sct_data, 2023)

            if should_find:
                assert ceo_name == "Test Exec"
                assert ceo_comp == 5_000_000.0
            else:
                assert ceo_name == ""
                assert ceo_comp == 0.0

    def test_find_ceo_no_ceo(self, analyzer: CompTaxAnalyzer) -> None:
        """Test CEO detection when no CEO in data."""
        sct_data = SCTData(
            company="Test",
            cik="0000012345",
            filing_date="2024-01-01",
            executives=[
                ExecutiveCompensation(
                    name="Test CFO",
                    title="Chief Financial Officer",
                    compensation=[CompensationYear(year=2023, total=3_000_000.0)],
                )
            ],
        )

        ceo_name, ceo_comp = analyzer._find_ceo(sct_data, 2023)
        assert ceo_name == ""
        assert ceo_comp == 0.0


class TestCompTaxAnalyzerBatch:
    """Tests for batch analysis with rankings."""

    def test_analyze_batch_rankings(self, analyzer: CompTaxAnalyzer) -> None:
        """Test batch analysis computes correct rankings."""
        # Create three companies with different metrics
        companies = [
            Company(
                rank=1, name="High Comp Corp", ticker="HCC", cik="0000000001", sector="Tech"
            ),
            Company(
                rank=2, name="High Tax Corp", ticker="HTC", cik="0000000002", sector="Finance"
            ),
            Company(
                rank=3, name="High Ratio Corp", ticker="HRC", cik="0000000003", sector="Retail"
            ),
        ]

        # High Comp: High exec comp, moderate tax
        sct_data_1 = SCTData(
            company="High Comp Corp",
            cik="0000000001",
            filing_date="2024-01-01",
            executives=[
                ExecutiveCompensation(
                    name="CEO1",
                    title="CEO",
                    compensation=[CompensationYear(year=2023, total=10_000_000.0)],
                ),
            ],
        )
        tax_data_1 = TaxData(
            company="High Comp Corp",
            cik="0000000001",
            filing_date="2024-01-01",
            fiscal_year_end="2023-12-31",
            tax_years=[
                TaxYear(year=2023, total_tax_expense=500_000_000.0, pretax_income=2_000_000_000.0)
            ],
        )

        # High Tax: Moderate comp, high tax
        sct_data_2 = SCTData(
            company="High Tax Corp",
            cik="0000000002",
            filing_date="2024-01-01",
            executives=[
                ExecutiveCompensation(
                    name="CEO2",
                    title="CEO",
                    compensation=[CompensationYear(year=2023, total=5_000_000.0)],
                ),
            ],
        )
        tax_data_2 = TaxData(
            company="High Tax Corp",
            cik="0000000002",
            filing_date="2024-01-01",
            fiscal_year_end="2023-12-31",
            tax_years=[
                TaxYear(year=2023, total_tax_expense=1_000_000_000.0, pretax_income=4_000_000_000.0)
            ],
        )

        # High Ratio: Low comp, very low tax
        sct_data_3 = SCTData(
            company="High Ratio Corp",
            cik="0000000003",
            filing_date="2024-01-01",
            executives=[
                ExecutiveCompensation(
                    name="CEO3",
                    title="CEO",
                    compensation=[CompensationYear(year=2023, total=3_000_000.0)],
                ),
            ],
        )
        tax_data_3 = TaxData(
            company="High Ratio Corp",
            cik="0000000003",
            filing_date="2024-01-01",
            fiscal_year_end="2023-12-31",
            tax_years=[
                TaxYear(year=2023, total_tax_expense=10_000_000.0, pretax_income=50_000_000.0)
            ],
        )

        results = [
            (companies[0], sct_data_1, tax_data_1),
            (companies[1], sct_data_2, tax_data_2),
            (companies[2], sct_data_3, tax_data_3),
        ]

        analyses = analyzer.analyze_batch(results, fiscal_year=2023)

        # Verify rankings
        assert len(analyses) == 3

        # Find each analysis by company name
        hcc = next(a for a in analyses if a.company == "High Comp Corp")
        htc = next(a for a in analyses if a.company == "High Tax Corp")
        hrc = next(a for a in analyses if a.company == "High Ratio Corp")

        # Comp rankings (HCC > HTC > HRC)
        assert hcc.comp_rank == 1
        assert htc.comp_rank == 2
        assert hrc.comp_rank == 3

        # Tax rankings (HTC > HCC > HRC)
        assert htc.tax_rank == 1
        assert hcc.tax_rank == 2
        assert hrc.tax_rank == 3

        # Ratio rankings (HRC > HCC > HTC)
        # HRC: 3M / 10M = 0.3
        # HCC: 10M / 500M = 0.02
        # HTC: 5M / 1000M = 0.005
        assert hrc.ratio_rank == 1
        assert hcc.ratio_rank == 2
        assert htc.ratio_rank == 3

    def test_analyze_batch_empty(self, analyzer: CompTaxAnalyzer) -> None:
        """Test batch analysis with empty input."""
        analyses = analyzer.analyze_batch([])
        assert analyses == []


class TestBatchAnalysisSummary:
    """Tests for batch summary statistics."""

    def test_generate_summary(self, analyzer: CompTaxAnalyzer) -> None:
        """Test summary generation from analyses."""
        # Create sample analyses
        analyses = [
            CompTaxAnalysis(
                company="Company A",
                ticker="AAA",
                cik="0000000001",
                rank=1,
                fiscal_year=2023,
                num_executives=5,
                total_exec_comp=20_000_000.0,
                ceo_name="CEO A",
                ceo_comp=8_000_000.0,
                median_exec_comp=3_000_000.0,
                avg_exec_comp=4_000_000.0,
                total_tax_expense=800_000_000.0,
                current_tax=900_000_000.0,
                deferred_tax=-100_000_000.0,
                effective_tax_rate=0.22,
                cash_taxes_paid=850_000_000.0,
                pretax_income=3_600_000_000.0,
                comp_to_tax_ratio=0.025,
                ceo_to_tax_ratio=0.01,
                comp_to_pretax_ratio=0.0056,
                comp_to_cash_tax_ratio=0.0235,
            ),
            CompTaxAnalysis(
                company="Company B",
                ticker="BBB",
                cik="0000000002",
                rank=2,
                fiscal_year=2023,
                num_executives=4,
                total_exec_comp=15_000_000.0,
                ceo_name="CEO B",
                ceo_comp=6_000_000.0,
                median_exec_comp=3_500_000.0,
                avg_exec_comp=3_750_000.0,
                total_tax_expense=600_000_000.0,
                current_tax=650_000_000.0,
                deferred_tax=-50_000_000.0,
                effective_tax_rate=0.20,
                cash_taxes_paid=625_000_000.0,
                pretax_income=3_000_000_000.0,
                comp_to_tax_ratio=0.025,
                ceo_to_tax_ratio=0.01,
                comp_to_pretax_ratio=0.005,
                comp_to_cash_tax_ratio=0.024,
            ),
            CompTaxAnalysis(
                company="Company C",
                ticker="CCC",
                cik="0000000003",
                rank=3,
                fiscal_year=2023,
                num_executives=6,
                total_exec_comp=25_000_000.0,
                ceo_name="CEO C",
                ceo_comp=10_000_000.0,
                median_exec_comp=4_000_000.0,
                avg_exec_comp=4_166_667.0,
                total_tax_expense=1_000_000_000.0,
                current_tax=1_100_000_000.0,
                deferred_tax=-100_000_000.0,
                effective_tax_rate=0.24,
                cash_taxes_paid=1_050_000_000.0,
                pretax_income=4_200_000_000.0,
                comp_to_tax_ratio=0.025,
                ceo_to_tax_ratio=0.01,
                comp_to_pretax_ratio=0.006,
                comp_to_cash_tax_ratio=0.0238,
            ),
        ]

        summary = analyzer.generate_summary(analyses)

        # Basic info
        assert summary.num_companies == 3
        assert summary.fiscal_year == 2023

        # Compensation stats
        assert summary.total_exec_comp_all == 60_000_000.0
        assert summary.avg_exec_comp_per_company == 20_000_000.0
        assert summary.median_exec_comp_per_company == 20_000_000.0
        assert summary.max_exec_comp_company == "Company C"
        assert summary.max_exec_comp == 25_000_000.0

        # Tax stats
        assert summary.total_tax_all == 2_400_000_000.0
        assert summary.avg_tax_per_company == 800_000_000.0
        assert summary.median_tax_per_company == 800_000_000.0
        assert summary.avg_effective_rate == pytest.approx(0.22, rel=1e-2)

        # Ratio stats
        assert summary.avg_comp_to_tax_ratio == 0.025
        assert summary.median_comp_to_tax_ratio == 0.025
        assert summary.max_ratio_company == "Company A"  # First with max ratio
        assert summary.max_ratio == 0.025

    def test_generate_summary_empty(self, analyzer: CompTaxAnalyzer) -> None:
        """Test summary generation with empty analyses list."""
        summary = analyzer.generate_summary([])

        assert summary.num_companies == 0
        assert summary.fiscal_year == 0
        assert summary.total_exec_comp_all == 0.0
        assert summary.total_tax_all == 0.0


class TestHelperMethods:
    """Tests for internal helper methods."""

    def test_get_comp_for_year(
        self, analyzer: CompTaxAnalyzer, sample_sct_data: SCTData
    ) -> None:
        """Test extracting compensation for specific year."""
        comp_list = analyzer._get_comp_for_year(sample_sct_data, 2023)

        assert len(comp_list) == 3
        assert 7_100_000.0 in comp_list
        assert 4_200_000.0 in comp_list
        assert 3_800_000.0 in comp_list

    def test_get_comp_for_year_missing(
        self, analyzer: CompTaxAnalyzer, sample_sct_data: SCTData
    ) -> None:
        """Test extracting compensation for year not in data."""
        comp_list = analyzer._get_comp_for_year(sample_sct_data, 2020)
        assert comp_list == []

    def test_get_tax_for_year(
        self, analyzer: CompTaxAnalyzer, sample_tax_data: TaxData
    ) -> None:
        """Test extracting tax data for specific year."""
        tax_year = analyzer._get_tax_for_year(sample_tax_data, 2023)

        assert tax_year is not None
        assert tax_year.year == 2023
        assert tax_year.total_tax_expense == 890_000_000.0

    def test_get_tax_for_year_missing(
        self, analyzer: CompTaxAnalyzer, sample_tax_data: TaxData
    ) -> None:
        """Test extracting tax data for year not in data."""
        tax_year = analyzer._get_tax_for_year(sample_tax_data, 2020)
        assert tax_year is None


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_empty_executives_list(self, analyzer: CompTaxAnalyzer) -> None:
        """Test analysis with no executives."""
        company = Company(
            rank=1, name="Test", ticker="TST", cik="0000000001", sector="Tech"
        )
        sct_data = SCTData(
            company="Test", cik="0000000001", filing_date="2024-01-01", executives=[]
        )
        tax_data = TaxData(
            company="Test",
            cik="0000000001",
            filing_date="2024-01-01",
            fiscal_year_end="2023-12-31",
            tax_years=[
                TaxYear(year=2023, total_tax_expense=100_000_000.0, pretax_income=500_000_000.0)
            ],
        )

        analysis = analyzer.analyze_single(company, sct_data, tax_data, fiscal_year=2023)

        assert analysis.num_executives == 0
        assert analysis.total_exec_comp == 0.0
        assert analysis.ceo_name == ""
        assert analysis.ceo_comp == 0.0
        assert analysis.median_exec_comp == 0.0
        assert analysis.avg_exec_comp == 0.0

    def test_empty_tax_years_list(self, analyzer: CompTaxAnalyzer) -> None:
        """Test analysis with no tax years."""
        company = Company(
            rank=1, name="Test", ticker="TST", cik="0000000001", sector="Tech"
        )
        sct_data = SCTData(
            company="Test",
            cik="0000000001",
            filing_date="2024-01-01",
            executives=[
                ExecutiveCompensation(
                    name="CEO",
                    title="Chief Executive Officer",
                    compensation=[CompensationYear(year=2023, total=5_000_000.0)],
                )
            ],
        )
        tax_data = TaxData(
            company="Test",
            cik="0000000001",
            filing_date="2024-01-01",
            fiscal_year_end="2023-12-31",
            tax_years=[],
        )

        analysis = analyzer.analyze_single(company, sct_data, tax_data, fiscal_year=2023)

        assert analysis.total_tax_expense == 0.0
        assert analysis.current_tax == 0.0
        assert analysis.deferred_tax == 0.0
        assert analysis.effective_tax_rate == 0.0

    def test_negative_tax_expense(self, analyzer: CompTaxAnalyzer) -> None:
        """Test analysis with negative tax expense (tax benefit)."""
        company = Company(
            rank=1, name="Test", ticker="TST", cik="0000000001", sector="Tech"
        )
        sct_data = SCTData(
            company="Test",
            cik="0000000001",
            filing_date="2024-01-01",
            executives=[
                ExecutiveCompensation(
                    name="CEO",
                    title="CEO",
                    compensation=[CompensationYear(year=2023, total=5_000_000.0)],
                )
            ],
        )
        tax_data = TaxData(
            company="Test",
            cik="0000000001",
            filing_date="2024-01-01",
            fiscal_year_end="2023-12-31",
            tax_years=[
                TaxYear(
                    year=2023,
                    total_tax_expense=-50_000_000.0,  # Tax benefit
                    pretax_income=-200_000_000.0,  # Loss
                )
            ],
        )

        analysis = analyzer.analyze_single(company, sct_data, tax_data, fiscal_year=2023)

        # Should handle negative tax gracefully
        assert analysis.total_tax_expense == -50_000_000.0
        # Ratio calculation with negative tax should still work
        assert analysis.comp_to_tax_ratio == pytest.approx(-0.1, rel=1e-2)
