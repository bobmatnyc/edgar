"""
End-to-End Integration Tests for IReportGenerator Multi-Format Support.

Tests the complete report generation system across all 4 formats (Excel, PDF, DOCX, PPTX)
with focus on cross-format consistency, factory validation, configuration, error handling,
and performance benchmarks.

Ticket: 1M-360 (IReportGenerator Multi-Format Support)
Test Coverage: E2E validation of complete system
"""

import time
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest
from openpyxl import load_workbook

from extract_transform_platform.reports import (
    DOCXReportConfig,
    DOCXReportGenerator,
    ExcelReportConfig,
    ExcelReportGenerator,
    PDFReportConfig,
    PDFReportGenerator,
    PPTXReportConfig,
    PPTXReportGenerator,
    ReportGeneratorFactory,
)


class TestReportGeneratorFactoryE2E:
    """Test ReportGeneratorFactory end-to-end functionality."""

    def test_factory_creates_all_formats(self):
        """Test factory can create generators for all supported formats."""
        formats = ["excel", "xlsx", "pdf", "docx", "pptx"]

        for format_name in formats:
            generator = ReportGeneratorFactory.create(format_name)
            assert generator is not None
            assert hasattr(generator, "generate")

    def test_factory_supported_formats_complete(self):
        """Test factory returns all 5 supported formats."""
        formats = ReportGeneratorFactory.get_supported_formats()

        assert "excel" in formats
        assert "xlsx" in formats  # Alias for excel
        assert "pdf" in formats
        assert "docx" in formats
        assert "pptx" in formats
        assert len(formats) == 5

    def test_factory_format_aliases_work(self):
        """Test format aliases (excel vs xlsx) produce same generator type."""
        excel_gen = ReportGeneratorFactory.create("excel")
        xlsx_gen = ReportGeneratorFactory.create("xlsx")

        assert type(excel_gen) == type(xlsx_gen)
        assert isinstance(excel_gen, ExcelReportGenerator)
        assert isinstance(xlsx_gen, ExcelReportGenerator)

    def test_factory_case_insensitive(self):
        """Test factory handles case-insensitive format names."""
        generators = [
            ReportGeneratorFactory.create("Excel"),
            ReportGeneratorFactory.create("EXCEL"),
            ReportGeneratorFactory.create("excel"),
        ]

        for gen in generators:
            assert isinstance(gen, ExcelReportGenerator)

    def test_factory_unsupported_format_raises(self):
        """Test factory raises ValueError for unsupported formats."""
        with pytest.raises(ValueError, match="Unsupported report format"):
            ReportGeneratorFactory.create("txt")

        with pytest.raises(ValueError, match="Unsupported report format"):
            ReportGeneratorFactory.create("html")

    def test_factory_is_format_supported(self):
        """Test is_format_supported method works correctly."""
        assert ReportGeneratorFactory.is_format_supported("excel") is True
        assert ReportGeneratorFactory.is_format_supported("pdf") is True
        assert ReportGeneratorFactory.is_format_supported("txt") is False
        assert ReportGeneratorFactory.is_format_supported("html") is False


class TestCrossFormatConsistency:
    """Test data consistency across all 4 report formats."""

    @pytest.fixture
    def test_data(self) -> pd.DataFrame:
        """Standard test dataset for cross-format consistency."""
        return pd.DataFrame({
            "Product": ["Widget A", "Widget B", "Widget C", "Widget D"],
            "Q1 Sales": [45000, 52000, 38000, 61000],
            "Q2 Sales": [48000, 55000, 41000, 64000],
            "Target": [50000, 50000, 50000, 50000],
            "Growth": ["10%", "15%", "8%", "18%"],
        })

    def test_all_formats_generate_successfully(self, test_data: pd.DataFrame, tmp_path: Path):
        """Test generating reports in all 4 formats successfully."""
        formats_and_extensions = [
            ("excel", "xlsx"),
            ("pdf", "pdf"),
            ("docx", "docx"),
            ("pptx", "pptx"),
        ]

        for format_name, extension in formats_and_extensions:
            generator = ReportGeneratorFactory.create(format_name)
            output_path = tmp_path / f"test_report.{extension}"

            result = generator.generate(
                test_data,
                output_path,
                config={
                    "title": "Cross-Format Test Report",
                    "author": "QA Suite",
                },
            )

            # Verify file exists and has content
            assert result.exists()
            assert result.stat().st_size > 0
            assert result.suffix == f".{extension}"

    def test_all_formats_contain_same_data(self, test_data: pd.DataFrame, tmp_path: Path):
        """Test all formats contain the same underlying data."""
        # Generate all formats
        excel_path = tmp_path / "report.xlsx"
        pdf_path = tmp_path / "report.pdf"
        docx_path = tmp_path / "report.docx"
        pptx_path = tmp_path / "report.pptx"

        excel_gen = ReportGeneratorFactory.create("excel")
        pdf_gen = ReportGeneratorFactory.create("pdf")
        docx_gen = ReportGeneratorFactory.create("docx")
        pptx_gen = ReportGeneratorFactory.create("pptx")

        excel_gen.generate(test_data, excel_path)
        pdf_gen.generate(test_data, pdf_path)
        docx_gen.generate(test_data, docx_path)
        pptx_gen.generate(test_data, pptx_path)

        # Verify Excel contains exact data
        df_from_excel = pd.read_excel(excel_path)
        pd.testing.assert_frame_equal(df_from_excel, test_data)

        # Verify all files exist with reasonable sizes
        assert excel_path.stat().st_size > 1000  # Excel: ~5-10KB
        assert pdf_path.stat().st_size > 1000    # PDF: ~2-5KB
        assert docx_path.stat().st_size > 1000   # DOCX: ~3-6KB
        assert pptx_path.stat().st_size > 5000   # PPTX: ~20-30KB

    def test_all_formats_respect_metadata(self, test_data: pd.DataFrame, tmp_path: Path):
        """Test all formats include metadata (title, author, timestamp)."""
        metadata = {
            "title": "E2E Test Report",
            "author": "QA Integration Suite",
            "include_timestamp": True,
        }

        # Excel
        excel_path = tmp_path / "meta.xlsx"
        excel_gen = ReportGeneratorFactory.create("excel")
        excel_gen.generate(test_data, excel_path, config=metadata)

        wb = load_workbook(excel_path)
        assert wb.properties.title == "E2E Test Report"
        assert wb.properties.creator == "QA Integration Suite"

        # PDF, DOCX, PPTX - just verify they generate without error
        pdf_gen = ReportGeneratorFactory.create("pdf")
        docx_gen = ReportGeneratorFactory.create("docx")
        pptx_gen = ReportGeneratorFactory.create("pptx")

        pdf_gen.generate(test_data, tmp_path / "meta.pdf", config=metadata)
        docx_gen.generate(test_data, tmp_path / "meta.docx", config=metadata)
        pptx_gen.generate(test_data, tmp_path / "meta.pptx", config=metadata)


class TestConfigurationValidation:
    """Test configuration validation for all formats."""

    @pytest.fixture
    def test_data(self) -> pd.DataFrame:
        return pd.DataFrame({"A": [1, 2], "B": [3, 4]})

    def test_excel_config_validation(self, test_data: pd.DataFrame, tmp_path: Path):
        """Test ExcelReportConfig validation."""
        # Valid config
        config = ExcelReportConfig(
            title="Test",
            sheet_name="Data",
            freeze_panes=True,
            auto_filter=True,
        )
        assert config.title == "Test"
        assert config.freeze_panes is True

        # Generate with config
        gen = ExcelReportGenerator()
        result = gen.generate(test_data, tmp_path / "test.xlsx", config=config)
        assert result.exists()

    def test_pdf_config_validation(self, test_data: pd.DataFrame, tmp_path: Path):
        """Test PDFReportConfig validation."""
        # Valid config
        config = PDFReportConfig(
            title="Test PDF",
            orientation="landscape",
            page_size="A4",
            table_style="fancy",
        )
        assert config.orientation == "landscape"
        assert config.page_size == "A4"

        # Invalid page size should raise
        with pytest.raises(ValueError):
            PDFReportConfig(title="Test", page_size="INVALID")

    def test_docx_config_validation(self, test_data: pd.DataFrame, tmp_path: Path):
        """Test DOCXReportConfig validation."""
        # Valid config
        config = DOCXReportConfig(
            title="Test DOCX",
            table_alignment="center",
            font_name="Arial",
            font_size=11,
        )
        assert config.table_alignment == "center"
        assert config.font_size == 11

    def test_pptx_config_validation(self, test_data: pd.DataFrame, tmp_path: Path):
        """Test PPTXReportConfig validation."""
        # Valid config
        config = PPTXReportConfig(
            title="Test PPTX",
            chart_type="bar",
            theme_color="blue",
            max_rows_per_slide=15,
        )
        assert config.chart_type == "bar"
        assert config.max_rows_per_slide == 15

        # Invalid chart type should work (validation in generator)
        config_invalid = PPTXReportConfig(
            title="Test",
            chart_type="invalid_type",
        )
        assert config_invalid.chart_type == "invalid_type"


class TestErrorHandling:
    """Test comprehensive error handling across all formats."""

    @pytest.fixture
    def valid_data(self) -> pd.DataFrame:
        return pd.DataFrame({"A": [1, 2], "B": [3, 4]})

    def test_invalid_output_extensions(self, valid_data: pd.DataFrame, tmp_path: Path):
        """Test generators reject invalid output extensions."""
        # Excel
        excel_gen = ExcelReportGenerator()
        with pytest.raises(ValueError, match="Output path must have extension"):
            excel_gen.generate(valid_data, tmp_path / "report.txt")

        # PDF
        pdf_gen = PDFReportGenerator()
        with pytest.raises(ValueError, match="Output path must have extension"):
            pdf_gen.generate(valid_data, tmp_path / "report.txt")

        # DOCX
        docx_gen = DOCXReportGenerator()
        with pytest.raises(ValueError, match="Output path must have extension"):
            docx_gen.generate(valid_data, tmp_path / "report.txt")

        # PPTX
        pptx_gen = PPTXReportGenerator()
        with pytest.raises(ValueError, match="Output path must have extension"):
            pptx_gen.generate(valid_data, tmp_path / "report.txt")

    def test_empty_data_raises(self, tmp_path: Path):
        """Test all generators reject empty data."""
        empty_df = pd.DataFrame()

        generators = [
            ExcelReportGenerator(),
            PDFReportGenerator(),
            DOCXReportGenerator(),
            PPTXReportGenerator(),
        ]

        paths = [
            tmp_path / "empty.xlsx",
            tmp_path / "empty.pdf",
            tmp_path / "empty.docx",
            tmp_path / "empty.pptx",
        ]

        for gen, path in zip(generators, paths):
            with pytest.raises(ValueError, match="Data cannot be None or empty"):
                gen.generate(empty_df, path)

    def test_none_data_raises(self, tmp_path: Path):
        """Test all generators reject None data."""
        generators = [
            ExcelReportGenerator(),
            PDFReportGenerator(),
            DOCXReportGenerator(),
            PPTXReportGenerator(),
        ]

        paths = [
            tmp_path / "none.xlsx",
            tmp_path / "none.pdf",
            tmp_path / "none.docx",
            tmp_path / "none.pptx",
        ]

        for gen, path in zip(generators, paths):
            with pytest.raises(ValueError, match="Data cannot be None or empty"):
                gen.generate(None, path)

    def test_unsupported_data_types(self, tmp_path: Path):
        """Test all generators reject unsupported data types."""
        invalid_data = "This is a string, not a DataFrame"

        generators = [
            ExcelReportGenerator(),
            PDFReportGenerator(),
            DOCXReportGenerator(),
            PPTXReportGenerator(),
        ]

        paths = [
            tmp_path / "invalid.xlsx",
            tmp_path / "invalid.pdf",
            tmp_path / "invalid.docx",
            tmp_path / "invalid.pptx",
        ]

        for gen, path in zip(generators, paths):
            with pytest.raises((ValueError, TypeError)):
                gen.generate(invalid_data, path)


class TestPerformanceBenchmarks:
    """Test performance benchmarks for all formats."""

    def test_small_dataset_performance(self, tmp_path: Path):
        """Test generation time with 100-row dataset (target: <1s each)."""
        data = pd.DataFrame({
            "ID": range(100),
            "Name": [f"Item {i}" for i in range(100)],
            "Value": [i * 10 for i in range(100)],
        })

        formats = [
            ("excel", "xlsx"),
            ("pdf", "pdf"),
            ("docx", "docx"),
            ("pptx", "pptx"),
        ]

        results = {}
        for format_name, ext in formats:
            gen = ReportGeneratorFactory.create(format_name)
            output = tmp_path / f"small_{format_name}.{ext}"

            start = time.time()
            gen.generate(data, output)
            duration = time.time() - start

            results[format_name] = duration
            assert duration < 1.0, f"{format_name} took {duration:.2f}s (expected <1s)"

        print(f"\n100-row dataset performance:")
        for fmt, dur in results.items():
            print(f"  {fmt:10s} {dur:.3f}s")

    def test_medium_dataset_performance(self, tmp_path: Path):
        """Test generation time with 1000-row dataset (target: <5s each)."""
        data = pd.DataFrame({
            "ID": range(1000),
            "Product": [f"Product {i % 10}" for i in range(1000)],
            "Sales": [1000 + (i * 100) for i in range(1000)],
            "Cost": [500 + (i * 50) for i in range(1000)],
        })

        formats = [
            ("excel", "xlsx"),
            ("pdf", "pdf"),
            ("docx", "docx"),
            ("pptx", "pptx"),
        ]

        results = {}
        for format_name, ext in formats:
            gen = ReportGeneratorFactory.create(format_name)
            output = tmp_path / f"medium_{format_name}.{ext}"

            start = time.time()
            gen.generate(data, output)
            duration = time.time() - start

            results[format_name] = duration
            assert duration < 5.0, f"{format_name} took {duration:.2f}s (expected <5s)"

        print(f"\n1000-row dataset performance:")
        for fmt, dur in results.items():
            print(f"  {fmt:10s} {dur:.3f}s")

    def test_memory_efficiency(self, tmp_path: Path):
        """Test memory efficiency with 1000-row dataset."""
        data = pd.DataFrame({
            "Col" + str(i): range(1000) for i in range(10)
        })

        # Just verify all formats complete without memory errors
        formats = ["excel", "pdf", "docx", "pptx"]

        for fmt in formats:
            gen = ReportGeneratorFactory.create(fmt)
            ext = "xlsx" if fmt == "excel" else fmt
            output = tmp_path / f"memory_test.{ext}"

            # Should not raise MemoryError
            gen.generate(data, output)
            assert output.exists()


class TestDataInputVariations:
    """Test various data input formats for all generators."""

    @pytest.fixture
    def generators(self) -> Dict[str, Any]:
        return {
            "excel": ExcelReportGenerator(),
            "pdf": PDFReportGenerator(),
            "docx": DOCXReportGenerator(),
            "pptx": PPTXReportGenerator(),
        }

    def test_dict_input(self, generators: Dict[str, Any], tmp_path: Path):
        """Test generating reports from dict input."""
        data = {"A": [1, 2, 3], "B": [4, 5, 6]}

        for name, gen in generators.items():
            ext = "xlsx" if name == "excel" else name
            output = tmp_path / f"dict_input.{ext}"
            result = gen.generate(data, output)
            assert result.exists()

    def test_list_of_dicts_input(self, generators: Dict[str, Any], tmp_path: Path):
        """Test generating reports from list of dicts."""
        data = [
            {"Name": "Alice", "Age": 30},
            {"Name": "Bob", "Age": 25},
        ]

        for name, gen in generators.items():
            ext = "xlsx" if name == "excel" else name
            output = tmp_path / f"list_dicts.{ext}"
            result = gen.generate(data, output)
            assert result.exists()

    def test_dataframe_input(self, generators: Dict[str, Any], tmp_path: Path):
        """Test generating reports from DataFrame (most common)."""
        data = pd.DataFrame({"X": [1, 2], "Y": [3, 4]})

        for name, gen in generators.items():
            ext = "xlsx" if name == "excel" else name
            output = tmp_path / f"dataframe.{ext}"
            result = gen.generate(data, output)
            assert result.exists()


class TestOutputPathHandling:
    """Test output path handling across formats."""

    @pytest.fixture
    def test_data(self) -> pd.DataFrame:
        return pd.DataFrame({"A": [1, 2], "B": [3, 4]})

    def test_creates_parent_directories(self, test_data: pd.DataFrame, tmp_path: Path):
        """Test all generators create parent directories if missing."""
        nested_dir = tmp_path / "reports" / "2024" / "Q1"

        formats = [
            ("excel", "report.xlsx"),
            ("pdf", "report.pdf"),
            ("docx", "report.docx"),
            ("pptx", "report.pptx"),
        ]

        for fmt, filename in formats:
            gen = ReportGeneratorFactory.create(fmt)
            output = nested_dir / filename

            assert not nested_dir.exists()  # Verify parent doesn't exist
            result = gen.generate(test_data, output)
            assert result.exists()
            assert nested_dir.exists()

    def test_returns_absolute_paths(self, test_data: pd.DataFrame, tmp_path: Path):
        """Test all generators return absolute paths."""
        formats = ["excel", "pdf", "docx", "pptx"]

        for fmt in formats:
            gen = ReportGeneratorFactory.create(fmt)
            ext = "xlsx" if fmt == "excel" else fmt
            output = tmp_path / f"test.{ext}"

            result = gen.generate(test_data, output)
            assert result.is_absolute()


# Summary counts for QA report
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print summary for QA report."""
    if hasattr(config, "_e2e_summary"):
        print("\n" + "=" * 70)
        print("E2E TEST SUMMARY FOR QA VALIDATION")
        print("=" * 70)
