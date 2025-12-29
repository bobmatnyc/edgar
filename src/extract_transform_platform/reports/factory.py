"""
Module: extract_transform_platform.reports.factory

Purpose: Factory for creating report generators by format.

Features:
- Format-based generator selection
- Format registration (extensible)
- Supported format listing

Design Pattern: Factory Method Pattern
- Centralizes generator creation logic
- Decouples format selection from generator implementation
- Easy to add new formats without modifying existing code

Status: Phase 1 - Excel Support (1M-360)

Code Reuse: Pattern from BaseDataSource factory usage

Performance:
- Time: O(1) for format lookup
- Space: O(k) where k = number of registered formats
"""

import logging
from typing import Dict, List, Type

from .base import BaseReportGenerator, IReportGenerator
from .docx_generator import DOCXReportGenerator
from .excel_generator import ExcelReportGenerator
from .pdf_generator import PDFReportGenerator
from .pptx_generator import PPTXReportGenerator

logger = logging.getLogger(__name__)


class ReportGeneratorFactory:
    """Factory for creating report generators.

    Provides centralized creation of report generators by format.
    Supports registration of new formats for extensibility.

    Design Decisions:
    - Class-level registry: Shared across all instances
    - String-based format keys: User-friendly, case-insensitive
    - Type safety: Returns IReportGenerator protocol type
    - Extensible: Can register new formats at runtime

    Usage Example:
        >>> # Create generator
        >>> generator = ReportGeneratorFactory.create("excel")
        >>>
        >>> # List supported formats
        >>> formats = ReportGeneratorFactory.get_supported_formats()
        >>> print(formats)  # ["excel", "xlsx", "pdf", "docx"]
        >>>
        >>> # Register custom generator
        >>> ReportGeneratorFactory.register("custom", CustomGenerator)

    Thread Safety: Not thread-safe. If using in multi-threaded context,
    wrap registration in locks or register all formats at startup.
    """

    # Class-level registry of format -> generator class mappings
    _generators: Dict[str, Type[BaseReportGenerator]] = {
        "excel": ExcelReportGenerator,
        "xlsx": ExcelReportGenerator,  # Alias for convenience
        "pdf": PDFReportGenerator,
        "docx": DOCXReportGenerator,
        "pptx": PPTXReportGenerator,
    }

    @classmethod
    def create(cls, format: str) -> IReportGenerator:
        """Create report generator for specified format.

        Args:
            format: Report format (excel, xlsx, pdf, docx, pptx)
                Case-insensitive (excel = Excel = EXCEL)

        Returns:
            Report generator instance implementing IReportGenerator

        Raises:
            ValueError: If format not supported

        Performance:
        - Time: O(1) for format lookup + O(1) for instantiation
        - Space: O(1) for single generator instance

        Design Decision: Fail fast on unsupported formats
        - Better to raise exception than return None
        - Clear error message lists supported formats
        - Helps catch configuration errors early
        """
        format_lower = format.lower()

        if format_lower not in cls._generators:
            supported = ", ".join(sorted(cls._generators.keys()))
            raise ValueError(
                f"Unsupported report format: '{format}'. "
                f"Supported formats: {supported}"
            )

        generator_class = cls._generators[format_lower]
        generator = generator_class()

        logger.info(f"Created {generator_class.__name__} for format '{format}'")

        return generator

    @classmethod
    def register(cls, format: str, generator_class: Type[BaseReportGenerator]) -> None:
        """Register a new report generator.

        Allows external code to add support for new formats without
        modifying this module. Useful for plugins and extensions.

        Args:
            format: Format identifier (e.g., "pdf", "docx")
                Case-insensitive, will be stored as lowercase
            generator_class: Generator class (must inherit from BaseReportGenerator)

        Raises:
            TypeError: If generator_class doesn't inherit from BaseReportGenerator

        Design Decision: Validate generator class
        - Ensures registered classes meet interface contract
        - Prevents runtime errors from invalid generators
        - Clear error message if validation fails

        Example:
            >>> class CustomReportGenerator(BaseReportGenerator):
            ...     def generate(self, data, output_path, config):
            ...         # Implementation here
            ...         pass
            >>>
            >>> ReportGeneratorFactory.register("custom", CustomReportGenerator)
            >>> generator = ReportGeneratorFactory.create("custom")
        """
        # Validate generator class inherits from BaseReportGenerator
        if not issubclass(generator_class, BaseReportGenerator):
            raise TypeError(
                f"Generator class must inherit from BaseReportGenerator, "
                f"got {generator_class.__name__}"
            )

        format_lower = format.lower()
        cls._generators[format_lower] = generator_class

        logger.info(
            f"Registered {generator_class.__name__} for format '{format_lower}'"
        )

    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """Get list of supported formats.

        Returns:
            Sorted list of format identifiers

        Design Decision: Return sorted list
        - Consistent ordering for display
        - Easy to scan for users
        - Minimal performance cost (small list)
        """
        return sorted(cls._generators.keys())

    @classmethod
    def is_format_supported(cls, format: str) -> bool:
        """Check if format is supported.

        Convenience method for checking format support without
        catching exceptions.

        Args:
            format: Format identifier (case-insensitive)

        Returns:
            True if format is supported, False otherwise

        Example:
            >>> if ReportGeneratorFactory.is_format_supported("excel"):
            ...     generator = ReportGeneratorFactory.create("excel")
            ... else:
            ...     print("Excel format not supported")
        """
        return format.lower() in cls._generators

    @classmethod
    def get_generator_class(cls, format: str) -> Type[BaseReportGenerator]:
        """Get generator class for format without instantiating.

        Useful for introspection or when you need the class itself
        rather than an instance.

        Args:
            format: Format identifier (case-insensitive)

        Returns:
            Generator class

        Raises:
            ValueError: If format not supported

        Example:
            >>> GeneratorClass = ReportGeneratorFactory.get_generator_class("excel")
            >>> print(GeneratorClass.__name__)  # "ExcelReportGenerator"
            >>> features = GeneratorClass().get_supported_features()
        """
        format_lower = format.lower()

        if format_lower not in cls._generators:
            supported = ", ".join(sorted(cls._generators.keys()))
            raise ValueError(
                f"Unsupported report format: '{format}'. "
                f"Supported formats: {supported}"
            )

        return cls._generators[format_lower]
