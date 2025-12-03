"""
Unit tests for extract_transform_platform.reports.factory module.

Tests:
- Factory creation of generators
- Format support checking
- Generator registration
- Error handling for unsupported formats
"""

import pytest

from extract_transform_platform.reports import (
    BaseReportGenerator,
    DOCXReportGenerator,
    ExcelReportGenerator,
    IReportGenerator,
    PDFReportGenerator,
    PPTXReportGenerator,
    ReportGeneratorFactory,
)


class TestReportGeneratorFactory:
    """Test ReportGeneratorFactory."""

    def test_create_excel_generator(self):
        """Test creating Excel generator."""
        generator = ReportGeneratorFactory.create("excel")

        assert isinstance(generator, ExcelReportGenerator)
        assert isinstance(generator, BaseReportGenerator)
        # Check protocol compliance
        assert hasattr(generator, "generate")
        assert hasattr(generator, "get_supported_features")

    def test_create_xlsx_generator(self):
        """Test creating generator with xlsx alias."""
        generator = ReportGeneratorFactory.create("xlsx")

        assert isinstance(generator, ExcelReportGenerator)

    def test_create_case_insensitive(self):
        """Test that format is case-insensitive."""
        gen1 = ReportGeneratorFactory.create("excel")
        gen2 = ReportGeneratorFactory.create("EXCEL")
        gen3 = ReportGeneratorFactory.create("Excel")

        # All should be same class
        assert type(gen1) == type(gen2) == type(gen3)

    def test_create_pdf_generator(self):
        """Test creating PDF generator."""
        generator = ReportGeneratorFactory.create("pdf")

        assert isinstance(generator, PDFReportGenerator)
        assert isinstance(generator, BaseReportGenerator)
        # Check protocol compliance
        assert hasattr(generator, "generate")
        assert hasattr(generator, "get_supported_features")

    def test_create_docx_generator(self):
        """Test creating DOCX generator."""
        generator = ReportGeneratorFactory.create("docx")

        assert isinstance(generator, DOCXReportGenerator)
        assert isinstance(generator, BaseReportGenerator)
        # Check protocol compliance
        assert hasattr(generator, "generate")
        assert hasattr(generator, "get_supported_features")

    def test_create_pptx_generator(self):
        """Test creating PPTX generator."""
        generator = ReportGeneratorFactory.create("pptx")

        assert isinstance(generator, PPTXReportGenerator)
        assert isinstance(generator, BaseReportGenerator)
        # Check protocol compliance
        assert hasattr(generator, "generate")
        assert hasattr(generator, "get_supported_features")

    def test_unsupported_format_raises(self):
        """Test that unsupported format raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported report format"):
            ReportGeneratorFactory.create("unsupported")

        with pytest.raises(ValueError, match="Unsupported report format"):
            ReportGeneratorFactory.create("invalid_format")

    def test_error_message_lists_supported_formats(self):
        """Test that error message lists supported formats."""
        try:
            ReportGeneratorFactory.create("invalid")
            pytest.fail("Should have raised ValueError")
        except ValueError as e:
            error_msg = str(e)
            assert "excel" in error_msg
            assert "xlsx" in error_msg
            assert "pdf" in error_msg
            assert "docx" in error_msg
            assert "pptx" in error_msg

    def test_get_supported_formats(self):
        """Test getting list of supported formats."""
        formats = ReportGeneratorFactory.get_supported_formats()

        assert isinstance(formats, list)
        assert "excel" in formats
        assert "xlsx" in formats
        assert "pdf" in formats
        assert "docx" in formats
        assert "pptx" in formats
        # Should be sorted
        assert formats == sorted(formats)
        # Should have 5 formats (excel, xlsx, pdf, docx, pptx)
        assert len(formats) == 5

    def test_is_format_supported_true(self):
        """Test checking if format is supported (positive case)."""
        assert ReportGeneratorFactory.is_format_supported("excel") is True
        assert ReportGeneratorFactory.is_format_supported("xlsx") is True
        assert ReportGeneratorFactory.is_format_supported("pdf") is True
        assert ReportGeneratorFactory.is_format_supported("docx") is True
        assert ReportGeneratorFactory.is_format_supported("pptx") is True
        assert (
            ReportGeneratorFactory.is_format_supported("EXCEL") is True
        )  # Case-insensitive

    def test_is_format_supported_false(self):
        """Test checking if format is supported (negative case)."""
        assert ReportGeneratorFactory.is_format_supported("invalid") is False
        assert ReportGeneratorFactory.is_format_supported("unknown") is False


class TestGeneratorRegistration:
    """Test registering custom generators."""

    def test_register_custom_generator(self):
        """Test registering a custom generator."""

        class CustomReportGenerator(BaseReportGenerator):
            def generate(self, data, output_path, config):
                return output_path

        # Register custom generator
        ReportGeneratorFactory.register("custom", CustomReportGenerator)

        # Should be in supported formats
        assert "custom" in ReportGeneratorFactory.get_supported_formats()

        # Should be able to create it
        generator = ReportGeneratorFactory.create("custom")
        assert isinstance(generator, CustomReportGenerator)

        # Clean up
        del ReportGeneratorFactory._generators["custom"]

    def test_register_non_generator_class_raises(self):
        """Test that registering non-generator class raises TypeError."""

        class NotAGenerator:
            pass

        with pytest.raises(TypeError, match="must inherit from BaseReportGenerator"):
            ReportGeneratorFactory.register("invalid", NotAGenerator)

    def test_register_case_insensitive(self):
        """Test that registration is case-insensitive."""

        class CustomGenerator(BaseReportGenerator):
            def generate(self, data, output_path, config):
                return output_path

        # Register with mixed case
        ReportGeneratorFactory.register("MyFormat", CustomGenerator)

        # Should be stored as lowercase
        assert "myformat" in ReportGeneratorFactory.get_supported_formats()

        # Should be retrievable with any case
        gen1 = ReportGeneratorFactory.create("myformat")
        gen2 = ReportGeneratorFactory.create("MYFORMAT")
        gen3 = ReportGeneratorFactory.create("MyFormat")

        assert type(gen1) == type(gen2) == type(gen3) == CustomGenerator

        # Clean up
        del ReportGeneratorFactory._generators["myformat"]

    def test_get_generator_class(self):
        """Test getting generator class without instantiating."""
        GeneratorClass = ReportGeneratorFactory.get_generator_class("excel")

        assert GeneratorClass == ExcelReportGenerator
        assert not isinstance(GeneratorClass, ExcelReportGenerator)  # Not an instance

    def test_get_generator_class_unsupported_raises(self):
        """Test that getting unsupported class raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported report format"):
            ReportGeneratorFactory.get_generator_class("unsupported")


class TestFactoryIntegration:
    """Test factory integration with generators."""

    def test_created_generator_has_features(self):
        """Test that created generator has features."""
        generator = ReportGeneratorFactory.create("excel")
        features = generator.get_supported_features()

        assert isinstance(features, list)
        assert len(features) > 0
        assert "tables" in features

    def test_multiple_create_calls_independent(self):
        """Test that multiple create calls return independent instances."""
        gen1 = ReportGeneratorFactory.create("excel")
        gen2 = ReportGeneratorFactory.create("excel")

        # Should be different instances
        assert gen1 is not gen2

        # But same class
        assert type(gen1) == type(gen2)
