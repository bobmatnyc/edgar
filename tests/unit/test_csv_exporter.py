"""Unit tests for CSV exporter module."""

import csv
from pathlib import Path

import pytest

from edgar.data.fortune100 import Company
from edgar.exporters import CSVExporter
from edgar.extractors.sct.models import (
    CompensationYear,
    ExecutiveCompensation,
    SCTData,
)
from edgar.extractors.tax.models import TaxData, TaxYear


@pytest.fixture
def sample_company() -> Company:
    """Create sample Fortune 100 company."""
    return Company(
        rank=3,
        name="Apple Inc.",
        ticker="AAPL",
        cik="0000320193",
        sector="Technology",
    )


@pytest.fixture
def sample_sct_data() -> SCTData:
    """Create sample executive compensation data."""
    return SCTData(
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
                    ),
                    CompensationYear(
                        year=2023,
                        salary=3000000.0,
                        bonus=0.0,
                        stock_awards=47000000.0,
                        option_awards=0.0,
                        non_equity_incentive=10500000.0,
                        pension_change=0.0,
                        other_compensation=1400000.0,
                        total=61900000.0,
                    ),
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


@pytest.fixture
def sample_tax_data() -> TaxData:
    """Create sample corporate tax data."""
    return TaxData(
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
            ),
            TaxYear(
                year=2023,
                current_federal=11000000000.0,
                current_state=1100000000.0,
                current_foreign=7500000000.0,
                total_current=19600000000.0,
                deferred_federal=-400000000.0,
                deferred_state=-40000000.0,
                deferred_foreign=150000000.0,
                total_deferred=-290000000.0,
                total_tax_expense=19310000000.0,
                pretax_income=95000000000.0,
                effective_tax_rate=0.2033,
                cash_taxes_paid=18500000000.0,
            ),
        ],
    )


class TestCSVExporter:
    """Test suite for CSVExporter class."""

    def test_init_default_output_dir(self) -> None:
        """Test CSVExporter initialization with default output directory."""
        exporter = CSVExporter()
        assert exporter.output_dir == Path("output")

    def test_init_custom_output_dir(self) -> None:
        """Test CSVExporter initialization with custom output directory."""
        custom_dir = Path("/tmp/custom_output")
        exporter = CSVExporter(output_dir=custom_dir)
        assert exporter.output_dir == custom_dir

    def test_ensure_output_dir_creates_directory(self, tmp_path: Path) -> None:
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "new_dir"
        exporter = CSVExporter(output_dir=output_dir)

        assert not output_dir.exists()
        exporter._ensure_output_dir()
        assert output_dir.exists()

    def test_format_currency(self) -> None:
        """Test currency formatting."""
        exporter = CSVExporter()

        assert exporter._format_currency(1234567.89) == "1,234,567.89"
        assert exporter._format_currency(0.0) == "0.00"
        assert exporter._format_currency(1000.0) == "1,000.00"
        assert exporter._format_currency(-500.50) == "-500.50"

    def test_format_percent(self) -> None:
        """Test percentage formatting."""
        exporter = CSVExporter()

        assert exporter._format_percent(0.2135) == "21.35%"
        assert exporter._format_percent(0.0) == "0.00%"
        assert exporter._format_percent(1.0) == "100.00%"
        assert exporter._format_percent(0.5) == "50.00%"

    def test_export_compensation(
        self,
        tmp_path: Path,
        sample_company: Company,
        sample_sct_data: SCTData,
    ) -> None:
        """Test executive compensation CSV export."""
        exporter = CSVExporter(output_dir=tmp_path)
        results = [(sample_company, sample_sct_data)]

        output_path = exporter.export_compensation(results, "test_comp.csv")

        assert output_path.exists()
        assert output_path == tmp_path / "test_comp.csv"

        # Read and validate CSV content
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have 3 rows: Tim Cook 2024, Tim Cook 2023, Luca Maestri 2024
        assert len(rows) == 3

        # Validate Tim Cook 2024 row
        cook_2024 = rows[0]
        assert cook_2024["rank"] == "3"
        assert cook_2024["company"] == "Apple Inc."
        assert cook_2024["ticker"] == "AAPL"
        assert cook_2024["cik"] == "0000320193"
        assert cook_2024["fiscal_year"] == "2024"
        assert cook_2024["executive_name"] == "Timothy D. Cook"
        assert cook_2024["title"] == "CEO"
        assert cook_2024["salary"] == "3,000,000.00"
        assert cook_2024["total_comp"] == "74,651,866.00"

        # Validate Luca Maestri 2024 row
        maestri_2024 = rows[2]
        assert maestri_2024["executive_name"] == "Luca Maestri"
        assert maestri_2024["title"] == "CFO"
        assert maestri_2024["total_comp"] == "26,500,000.00"

    def test_export_tax(
        self,
        tmp_path: Path,
        sample_company: Company,
        sample_tax_data: TaxData,
    ) -> None:
        """Test corporate tax CSV export."""
        exporter = CSVExporter(output_dir=tmp_path)
        results = [(sample_company, sample_tax_data)]

        output_path = exporter.export_tax(results, "test_tax.csv")

        assert output_path.exists()
        assert output_path == tmp_path / "test_tax.csv"

        # Read and validate CSV content
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have 2 rows: 2024 and 2023
        assert len(rows) == 2

        # Validate 2024 row
        tax_2024 = rows[0]
        assert tax_2024["rank"] == "3"
        assert tax_2024["company"] == "Apple Inc."
        assert tax_2024["ticker"] == "AAPL"
        assert tax_2024["cik"] == "0000320193"
        assert tax_2024["fiscal_year"] == "2024"
        assert tax_2024["current_federal"] == "12,500,000,000.00"
        assert tax_2024["total_tax_expense"] == "21,350,000,000.00"
        assert tax_2024["effective_tax_rate"] == "21.35%"
        assert tax_2024["cash_taxes_paid"] == "20,000,000,000.00"

        # Validate 2023 row
        tax_2023 = rows[1]
        assert tax_2023["fiscal_year"] == "2023"
        assert tax_2023["effective_tax_rate"] == "20.33%"

    def test_export_combined(
        self,
        tmp_path: Path,
        sample_company: Company,
        sample_sct_data: SCTData,
        sample_tax_data: TaxData,
    ) -> None:
        """Test combined compensation vs tax CSV export."""
        exporter = CSVExporter(output_dir=tmp_path)
        comp_results = [(sample_company, sample_sct_data)]
        tax_results = [(sample_company, sample_tax_data)]

        output_path = exporter.export_combined(
            comp_results, tax_results, "test_combined.csv"
        )

        assert output_path.exists()
        assert output_path == tmp_path / "test_combined.csv"

        # Read and validate CSV content
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have 2 rows: 2024 and 2023 (matching years)
        assert len(rows) == 2

        # Validate 2024 row
        combined_2024 = rows[0]
        assert combined_2024["rank"] == "3"
        assert combined_2024["company"] == "Apple Inc."
        assert combined_2024["ticker"] == "AAPL"
        assert combined_2024["cik"] == "0000320193"
        assert combined_2024["fiscal_year"] == "2024"
        assert combined_2024["num_executives"] == "2"
        assert combined_2024["ceo_name"] == "Timothy D. Cook"
        assert combined_2024["ceo_comp"] == "74,651,866.00"
        assert combined_2024["total_tax_expense"] == "21,350,000,000.00"
        assert combined_2024["effective_tax_rate"] == "21.35%"

        # Validate ratio calculations (comp to tax ratio)
        # Ratios are formatted to 6 decimal places in CSV
        total_comp = 74651866.0 + 26500000.0  # Cook + Maestri
        expected_ratio = total_comp / 21350000000.0
        assert combined_2024["comp_to_tax_ratio"] == f"{expected_ratio:.6f}"

        # Validate CEO to tax ratio
        ceo_ratio = 74651866.0 / 21350000000.0
        assert combined_2024["ceo_to_tax_ratio"] == f"{ceo_ratio:.6f}"

    def test_export_combined_median_calculation_odd(self, tmp_path: Path) -> None:
        """Test median calculation with odd number of executives."""
        exporter = CSVExporter(output_dir=tmp_path)

        company = Company(
            rank=1, name="Test Corp", ticker="TEST", cik="0000000001", sector="Tech"
        )

        # 3 executives with different compensation
        sct_data = SCTData(
            company="Test Corp",
            cik="0000000001",
            filing_date="2024-10-31",
            executives=[
                ExecutiveCompensation(
                    name="Exec A",
                    title="CEO",
                    compensation=[
                        CompensationYear(year=2024, total=3000000.0, salary=3000000.0)
                    ],
                ),
                ExecutiveCompensation(
                    name="Exec B",
                    title="CFO",
                    compensation=[
                        CompensationYear(year=2024, total=1000000.0, salary=1000000.0)
                    ],
                ),
                ExecutiveCompensation(
                    name="Exec C",
                    title="COO",
                    compensation=[
                        CompensationYear(year=2024, total=2000000.0, salary=2000000.0)
                    ],
                ),
            ],
        )

        tax_data = TaxData(
            company="Test Corp",
            cik="0000000001",
            filing_date="2024-10-31",
            fiscal_year_end="2024-09-30",
            tax_years=[
                TaxYear(
                    year=2024,
                    total_tax_expense=1000000000.0,
                    effective_tax_rate=0.21,
                    cash_taxes_paid=950000000.0,
                )
            ],
        )

        output_path = exporter.export_combined(
            [(company, sct_data)], [(company, tax_data)], "test_median_odd.csv"
        )

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        # Median of [1M, 2M, 3M] should be 2M
        assert row["median_exec_comp"] == "2,000,000.00"

    def test_export_combined_median_calculation_even(self, tmp_path: Path) -> None:
        """Test median calculation with even number of executives."""
        exporter = CSVExporter(output_dir=tmp_path)

        company = Company(
            rank=1, name="Test Corp", ticker="TEST", cik="0000000001", sector="Tech"
        )

        # 4 executives with different compensation
        sct_data = SCTData(
            company="Test Corp",
            cik="0000000001",
            filing_date="2024-10-31",
            executives=[
                ExecutiveCompensation(
                    name="Exec A",
                    title="CEO",
                    compensation=[
                        CompensationYear(year=2024, total=4000000.0, salary=4000000.0)
                    ],
                ),
                ExecutiveCompensation(
                    name="Exec B",
                    title="CFO",
                    compensation=[
                        CompensationYear(year=2024, total=1000000.0, salary=1000000.0)
                    ],
                ),
                ExecutiveCompensation(
                    name="Exec C",
                    title="COO",
                    compensation=[
                        CompensationYear(year=2024, total=2000000.0, salary=2000000.0)
                    ],
                ),
                ExecutiveCompensation(
                    name="Exec D",
                    title="CTO",
                    compensation=[
                        CompensationYear(year=2024, total=3000000.0, salary=3000000.0)
                    ],
                ),
            ],
        )

        tax_data = TaxData(
            company="Test Corp",
            cik="0000000001",
            filing_date="2024-10-31",
            fiscal_year_end="2024-09-30",
            tax_years=[
                TaxYear(
                    year=2024,
                    total_tax_expense=1000000000.0,
                    effective_tax_rate=0.21,
                    cash_taxes_paid=950000000.0,
                )
            ],
        )

        output_path = exporter.export_combined(
            [(company, sct_data)], [(company, tax_data)], "test_median_even.csv"
        )

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)

        # Median of [1M, 2M, 3M, 4M] should be (2M + 3M) / 2 = 2.5M
        assert row["median_exec_comp"] == "2,500,000.00"

    def test_export_combined_skips_mismatched_years(
        self, tmp_path: Path, sample_company: Company
    ) -> None:
        """Test that combined export skips years without matching data."""
        exporter = CSVExporter(output_dir=tmp_path)

        # Compensation data for 2024
        sct_data = SCTData(
            company="Apple Inc.",
            cik="0000320193",
            filing_date="2024-10-31",
            executives=[
                ExecutiveCompensation(
                    name="CEO",
                    title="Chief Executive Officer",
                    compensation=[
                        CompensationYear(year=2024, total=10000000.0, salary=10000000.0)
                    ],
                )
            ],
        )

        # Tax data for 2023 (different year)
        tax_data = TaxData(
            company="Apple Inc.",
            cik="0000320193",
            filing_date="2023-10-31",
            fiscal_year_end="2023-09-30",
            tax_years=[
                TaxYear(
                    year=2023,
                    total_tax_expense=1000000000.0,
                    effective_tax_rate=0.21,
                    cash_taxes_paid=950000000.0,
                )
            ],
        )

        output_path = exporter.export_combined(
            [(sample_company, sct_data)],
            [(sample_company, tax_data)],
            "test_mismatched.csv",
        )

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have 0 rows since years don't match
        assert len(rows) == 0

    def test_export_multiple_companies(self, tmp_path: Path) -> None:
        """Test exporting data for multiple companies."""
        exporter = CSVExporter(output_dir=tmp_path)

        company1 = Company(
            rank=1, name="Company A", ticker="CMPA", cik="0000000001", sector="Tech"
        )
        company2 = Company(
            rank=2, name="Company B", ticker="CMPB", cik="0000000002", sector="Finance"
        )

        sct_data1 = SCTData(
            company="Company A",
            cik="0000000001",
            filing_date="2024-10-31",
            executives=[
                ExecutiveCompensation(
                    name="CEO A",
                    title="CEO",
                    compensation=[
                        CompensationYear(year=2024, total=5000000.0, salary=5000000.0)
                    ],
                )
            ],
        )

        sct_data2 = SCTData(
            company="Company B",
            cik="0000000002",
            filing_date="2024-10-31",
            executives=[
                ExecutiveCompensation(
                    name="CEO B",
                    title="CEO",
                    compensation=[
                        CompensationYear(year=2024, total=7000000.0, salary=7000000.0)
                    ],
                )
            ],
        )

        results = [(company1, sct_data1), (company2, sct_data2)]
        output_path = exporter.export_compensation(results, "test_multi.csv")

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["company"] == "Company A"
        assert rows[1]["company"] == "Company B"

    def test_export_empty_results(self, tmp_path: Path) -> None:
        """Test exporting empty results creates file with header only."""
        exporter = CSVExporter(output_dir=tmp_path)
        results: list[tuple[Company, SCTData]] = []

        output_path = exporter.export_compensation(results, "test_empty.csv")

        assert output_path.exists()

        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Should have header row only
        assert len(rows) == 1
        assert rows[0][0] == "rank"
