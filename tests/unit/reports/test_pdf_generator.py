"""
Unit tests for PDFReportGenerator.

Tests cover:
- Basic PDF generation
- DataFrame, dict, and list input types
- Page orientation (portrait, landscape)
- Custom margins
- Table styles (grid, simple, fancy)
- Headers, footers, and page numbers
- Configuration validation
- Error handling

Phase 2: PDF Support (1M-360)
"""

from pathlib import Path

import pandas as pd
import pytest
from PyPDF2 import PdfReader

from extract_transform_platform.reports import (
    PDFReportConfig,
    PDFReportGenerator,
    ReportConfig,
)


class TestPDFReportGenerator:
    """Test suite for PDFReportGenerator."""

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "Product": ["Widget A", "Widget B", "Widget C"],
                "Quantity": [10, 25, 15],
                "Price": [15.99, 25.50, 10.00],
                "Total": [159.90, 637.50, 150.00],
            }
        )

    @pytest.fixture
    def large_data(self) -> pd.DataFrame:
        """Large DataFrame for multi-page testing."""
        return pd.DataFrame(
            {
                "ID": range(1, 101),
                "Name": [f"Item {i}" for i in range(1, 101)],
                "Value": [i * 10.5 for i in range(1, 101)],
            }
        )

    @pytest.fixture
    def output_path(self, tmp_path: Path) -> Path:
        """Temporary output path for PDF."""
        return tmp_path / "test_report.pdf"

    @pytest.fixture
    def generator(self) -> PDFReportGenerator:
        """PDFReportGenerator instance."""
        return PDFReportGenerator()

    # ============================================================================
    # Basic Generation Tests
    # ============================================================================

    def test_generate_basic_pdf(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test basic PDF generation from DataFrame."""
        config = PDFReportConfig(title="Test PDF Report")

        result_path = generator.generate(sample_data, output_path, config)

        # Verify file was created
        assert result_path.exists()
        assert result_path == output_path.resolve()

        # Verify file is valid PDF
        with open(result_path, "rb") as f:
            pdf_reader = PdfReader(f)
            assert len(pdf_reader.pages) >= 1

    def test_generate_from_dict(
        self, generator: PDFReportGenerator, output_path: Path
    ) -> None:
        """Test PDF generation from dictionary."""
        data = {"Product": "Widget A", "Quantity": 10, "Price": 15.99}
        config = PDFReportConfig(title="Dict Report")

        result_path = generator.generate(data, output_path, config)

        assert result_path.exists()
        with open(result_path, "rb") as f:
            pdf_reader = PdfReader(f)
            assert len(pdf_reader.pages) >= 1

    def test_generate_from_list_of_dicts(
        self, generator: PDFReportGenerator, output_path: Path
    ) -> None:
        """Test PDF generation from list of dictionaries."""
        data = [
            {"Product": "Widget A", "Quantity": 10},
            {"Product": "Widget B", "Quantity": 25},
        ]
        config = PDFReportConfig(title="List Report")

        result_path = generator.generate(data, output_path, config)

        assert result_path.exists()

    def test_generate_from_list_of_lists(
        self, generator: PDFReportGenerator, output_path: Path
    ) -> None:
        """Test PDF generation from list of lists."""
        data = [["Widget A", 10], ["Widget B", 25]]
        config = PDFReportConfig(title="List of Lists Report")

        result_path = generator.generate(data, output_path, config)

        assert result_path.exists()

    # ============================================================================
    # Page Orientation Tests
    # ============================================================================

    def test_portrait_orientation(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test portrait page orientation."""
        config = PDFReportConfig(title="Portrait Report", page_orientation="portrait")

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()
        # Note: Verifying actual orientation would require parsing PDF internals
        # This test confirms it doesn't raise an error

    def test_landscape_orientation(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test landscape page orientation."""
        config = PDFReportConfig(title="Landscape Report", page_orientation="landscape")

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    # ============================================================================
    # Custom Margins Tests
    # ============================================================================

    def test_custom_margins(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF with custom margins."""
        config = PDFReportConfig(
            title="Custom Margins Report",
            margin_top=1.5,
            margin_bottom=1.0,
            margin_left=1.0,
            margin_right=1.0,
        )

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    def test_minimal_margins(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF with minimal margins."""
        config = PDFReportConfig(
            title="Minimal Margins",
            margin_top=0.25,
            margin_bottom=0.25,
            margin_left=0.25,
            margin_right=0.25,
        )

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    # ============================================================================
    # Table Style Tests
    # ============================================================================

    def test_grid_table_style(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test grid table style (default)."""
        config = PDFReportConfig(title="Grid Style Report", table_style="grid")

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    def test_simple_table_style(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test simple table style."""
        config = PDFReportConfig(title="Simple Style Report", table_style="simple")

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    def test_fancy_table_style(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test fancy table style."""
        config = PDFReportConfig(title="Fancy Style Report", table_style="fancy")

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    def test_all_table_styles(
        self, generator: PDFReportGenerator, sample_data: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Test all table styles are generated without errors."""
        for style in ["grid", "simple", "fancy"]:
            config = PDFReportConfig(
                title=f"{style.capitalize()} Style Report", table_style=style
            )
            style_output = tmp_path / f"test_{style}.pdf"
            result_path = generator.generate(sample_data, style_output, config)
            assert result_path.exists()

    # ============================================================================
    # Header/Footer Tests
    # ============================================================================

    def test_header_text(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF with custom header text."""
        config = PDFReportConfig(
            title="Header Report", header_text="Confidential Report"
        )

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    def test_footer_text(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF with custom footer text."""
        config = PDFReportConfig(
            title="Footer Report", footer_text="Company XYZ - Internal Use Only"
        )

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    def test_header_and_footer(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF with both header and footer."""
        config = PDFReportConfig(
            title="Header/Footer Report",
            header_text="Confidential Report",
            footer_text="Company XYZ - Internal Use Only",
        )

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    def test_page_numbers(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF with page numbers."""
        config = PDFReportConfig(title="Page Numbers Report", include_page_numbers=True)

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    def test_no_page_numbers(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF without page numbers."""
        config = PDFReportConfig(
            title="No Page Numbers Report", include_page_numbers=False
        )

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    # ============================================================================
    # Multi-page Tests
    # ============================================================================

    def test_multi_page_report(
        self, generator: PDFReportGenerator, large_data: pd.DataFrame, output_path: Path
    ) -> None:
        """Test multi-page report generation."""
        config = PDFReportConfig(title="Multi-Page Report", include_page_numbers=True)

        result_path = generator.generate(large_data, output_path, config)

        assert result_path.exists()
        with open(result_path, "rb") as f:
            pdf_reader = PdfReader(f)
            # Large dataset should generate multiple pages
            assert len(pdf_reader.pages) >= 1

    # ============================================================================
    # Metadata Tests
    # ============================================================================

    def test_with_timestamp(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF with timestamp metadata."""
        config = PDFReportConfig(title="Timestamped Report", include_timestamp=True)

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    def test_without_timestamp(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF without timestamp metadata."""
        config = PDFReportConfig(title="No Timestamp Report", include_timestamp=False)

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    def test_custom_author(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF with custom author."""
        config = PDFReportConfig(
            title="Custom Author Report", author="John Doe", include_timestamp=True
        )

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    # ============================================================================
    # Page Size Tests
    # ============================================================================

    def test_letter_page_size(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF with letter page size."""
        config = PDFReportConfig(title="Letter Size Report", page_size="letter")

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    def test_a4_page_size(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF with A4 page size."""
        config = PDFReportConfig(title="A4 Size Report", page_size="a4")

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()

    # ============================================================================
    # Supported Features Tests
    # ============================================================================

    def test_get_supported_features(self, generator: PDFReportGenerator) -> None:
        """Test supported features list."""
        features = generator.get_supported_features()

        assert "tables" in features
        assert "headers" in features
        assert "footers" in features
        assert "page_numbers" in features
        assert "custom_fonts" in features
        assert "margins" in features
        assert "orientation" in features

    # ============================================================================
    # Error Handling Tests
    # ============================================================================

    def test_invalid_output_extension_raises(
        self, generator: PDFReportGenerator, sample_data: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Test that invalid extension raises ValueError."""
        config = PDFReportConfig(title="Test")
        invalid_path = tmp_path / "test.txt"

        with pytest.raises(ValueError, match="must have .pdf extension"):
            generator.generate(sample_data, invalid_path, config)

    def test_wrong_config_type_raises(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test that wrong config type raises TypeError."""
        # Use base ReportConfig instead of PDFReportConfig
        config = ReportConfig(title="Test")

        with pytest.raises(TypeError, match="requires PDFReportConfig"):
            generator.generate(sample_data, output_path, config)

    def test_none_data_raises(
        self, generator: PDFReportGenerator, output_path: Path
    ) -> None:
        """Test that None data raises ValueError."""
        config = PDFReportConfig(title="Test")

        with pytest.raises(ValueError, match="cannot be None"):
            generator.generate(None, output_path, config)

    def test_empty_dataframe_raises(
        self, generator: PDFReportGenerator, output_path: Path
    ) -> None:
        """Test that empty DataFrame raises ValueError."""
        config = PDFReportConfig(title="Test")
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="cannot be empty"):
            generator.generate(empty_df, output_path, config)

    def test_unsupported_data_type_raises(
        self, generator: PDFReportGenerator, output_path: Path
    ) -> None:
        """Test that unsupported data type raises TypeError."""
        config = PDFReportConfig(title="Test")
        invalid_data = "not a valid data type"

        with pytest.raises(TypeError, match="Unsupported data type"):
            generator.generate(invalid_data, output_path, config)

    # ============================================================================
    # Complex Configuration Tests
    # ============================================================================

    def test_full_configuration(
        self,
        generator: PDFReportGenerator,
        sample_data: pd.DataFrame,
        output_path: Path,
    ) -> None:
        """Test PDF with all configuration options."""
        config = PDFReportConfig(
            title="Comprehensive Report",
            author="Test Author",
            include_timestamp=True,
            page_size="letter",
            page_orientation="landscape",
            margin_top=1.0,
            margin_bottom=1.0,
            margin_left=1.0,
            margin_right=1.0,
            font_name="Helvetica",
            font_size=10,
            table_style="fancy",
            include_page_numbers=True,
            header_text="Confidential",
            footer_text="Company XYZ",
        )

        result_path = generator.generate(sample_data, output_path, config)

        assert result_path.exists()
        # Verify PDF is valid
        with open(result_path, "rb") as f:
            pdf_reader = PdfReader(f)
            assert len(pdf_reader.pages) >= 1

    # ============================================================================
    # Parent Directory Creation Tests
    # ============================================================================

    def test_creates_parent_directories(
        self, generator: PDFReportGenerator, sample_data: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Test that parent directories are created if they don't exist."""
        config = PDFReportConfig(title="Test")
        nested_path = tmp_path / "reports" / "2023" / "test.pdf"

        result_path = generator.generate(sample_data, nested_path, config)

        assert result_path.exists()
        assert result_path.parent.exists()
