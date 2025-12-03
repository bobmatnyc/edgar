"""
Unit tests for extract_transform_platform.reports.base module.

Tests:
- ReportConfig validation
- ExcelReportConfig validation
- IReportGenerator protocol compliance
- BaseReportGenerator abstract methods
- Helper method validation
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from extract_transform_platform.reports.base import (
    BaseReportGenerator,
    ExcelReportConfig,
    IReportGenerator,
    ReportConfig,
)


class TestReportConfig:
    """Test ReportConfig Pydantic model."""

    def test_create_with_required_fields(self):
        """Test creating config with only required fields."""
        config = ReportConfig(title="Test Report")

        assert config.title == "Test Report"
        assert config.author == "EDGAR Platform"  # Default value
        assert config.include_timestamp is True  # Default value
        assert config.page_size == "letter"  # Default value

    def test_create_with_all_fields(self):
        """Test creating config with all fields specified."""
        config = ReportConfig(
            title="Custom Report",
            author="Jane Doe",
            include_timestamp=False,
            page_size="a4",
        )

        assert config.title == "Custom Report"
        assert config.author == "Jane Doe"
        assert config.include_timestamp is False
        assert config.page_size == "a4"

    def test_missing_required_field_raises(self):
        """Test that missing required field raises ValidationError."""
        with pytest.raises(ValidationError, match="title"):
            ReportConfig()

    def test_invalid_page_size_raises(self):
        """Test that invalid page size raises ValidationError."""
        with pytest.raises(ValidationError, match="page_size"):
            ReportConfig(title="Test", page_size="invalid")

    def test_validate_assignment(self):
        """Test that assignment validation works."""
        config = ReportConfig(title="Test Report")

        # Valid assignment
        config.page_size = "a4"
        assert config.page_size == "a4"

        # Invalid assignment should raise
        with pytest.raises(ValidationError):
            config.page_size = "invalid"


class TestExcelReportConfig:
    """Test ExcelReportConfig Pydantic model."""

    def test_create_with_defaults(self):
        """Test creating Excel config with default values."""
        config = ExcelReportConfig(title="Test Report")

        # Parent class defaults
        assert config.title == "Test Report"
        assert config.author == "EDGAR Platform"

        # Excel-specific defaults
        assert config.sheet_name == "Report"
        assert config.freeze_header is True
        assert config.auto_filter is True
        assert config.column_widths == {}
        assert config.include_summary is False

    def test_create_with_custom_values(self):
        """Test creating Excel config with custom values."""
        config = ExcelReportConfig(
            title="Sales Report",
            author="Sales Team",
            sheet_name="Q4 Sales",
            freeze_header=False,
            auto_filter=False,
            column_widths={"name": 20, "amount": 15},
            include_summary=True,
        )

        assert config.title == "Sales Report"
        assert config.author == "Sales Team"
        assert config.sheet_name == "Q4 Sales"
        assert config.freeze_header is False
        assert config.auto_filter is False
        assert config.column_widths == {"name": 20, "amount": 15}
        assert config.include_summary is True


class TestIReportGenerator:
    """Test IReportGenerator protocol."""

    def test_protocol_methods_defined(self):
        """Test that protocol defines required methods."""
        # Check that IReportGenerator has required methods
        assert hasattr(IReportGenerator, "generate")
        assert hasattr(IReportGenerator, "get_supported_features")

    def test_runtime_checkable(self):
        """Test that protocol is runtime checkable."""
        # Test that isinstance() works with protocol (requires @runtime_checkable)
        from extract_transform_platform.reports import ExcelReportGenerator

        generator = ExcelReportGenerator()
        # This would raise TypeError if not @runtime_checkable
        assert isinstance(generator, IReportGenerator)


class MockReportGenerator(BaseReportGenerator):
    """Mock generator for testing abstract base class."""

    def generate(self, data, output_path, config):
        """Mock implementation."""
        self._validate_output_path(output_path, ".mock")
        self._validate_data_not_empty(data)
        return output_path


class TestBaseReportGenerator:
    """Test BaseReportGenerator abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract class cannot be instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseReportGenerator()

    def test_subclass_must_implement_generate(self):
        """Test that subclass must implement generate method."""

        class IncompleteGenerator(BaseReportGenerator):
            pass  # Missing generate implementation

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteGenerator()

    def test_get_supported_features_returns_copy(self):
        """Test that get_supported_features returns a copy."""
        generator = MockReportGenerator()
        generator._supported_features = ["feature1", "feature2"]

        features1 = generator.get_supported_features()
        features2 = generator.get_supported_features()

        # Should be equal
        assert features1 == features2

        # But not the same object
        assert features1 is not features2

        # Modifying returned list shouldn't affect internal state
        features1.append("feature3")
        assert len(generator.get_supported_features()) == 2

    def test_validate_output_path_correct_extension(self, tmp_path):
        """Test that valid output path passes validation."""
        generator = MockReportGenerator()
        output_path = tmp_path / "report.mock"

        # Should not raise
        generator._validate_output_path(output_path, ".mock")

        # Should create parent directory
        assert output_path.parent.exists()

    def test_validate_output_path_wrong_extension(self, tmp_path):
        """Test that wrong extension raises ValueError."""
        generator = MockReportGenerator()
        output_path = tmp_path / "report.txt"

        with pytest.raises(ValueError, match="must have .mock extension"):
            generator._validate_output_path(output_path, ".mock")

    def test_validate_output_path_creates_parent_directory(self, tmp_path):
        """Test that validation creates parent directories."""
        generator = MockReportGenerator()
        nested_path = tmp_path / "nested" / "dir" / "report.mock"

        # Parent directory shouldn't exist yet
        assert not nested_path.parent.exists()

        # Validation should create it
        generator._validate_output_path(nested_path, ".mock")
        assert nested_path.parent.exists()

    def test_validate_data_not_empty_with_valid_data(self):
        """Test that validation passes for non-empty data."""
        generator = MockReportGenerator()

        # Should not raise
        generator._validate_data_not_empty([1, 2, 3])
        generator._validate_data_not_empty({"key": "value"})
        generator._validate_data_not_empty("non-empty string")

    def test_validate_data_not_empty_with_none(self):
        """Test that None data raises ValueError."""
        generator = MockReportGenerator()

        with pytest.raises(ValueError, match="cannot be None"):
            generator._validate_data_not_empty(None)

    def test_validate_data_not_empty_with_empty_container(self):
        """Test that empty container raises ValueError."""
        generator = MockReportGenerator()

        with pytest.raises(ValueError, match="cannot be empty"):
            generator._validate_data_not_empty([])

        with pytest.raises(ValueError, match="cannot be empty"):
            generator._validate_data_not_empty({})

        with pytest.raises(ValueError, match="cannot be empty"):
            generator._validate_data_not_empty("")
