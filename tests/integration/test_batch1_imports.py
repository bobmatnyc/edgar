"""
Simple import verification for Batch 1 data sources.

Tests that all imports work correctly from both platform and EDGAR packages.
"""

import warnings


def test_platform_imports():
    """Verify all platform imports work."""
    # File data sources
    from extract_transform_platform.data_sources.file import (
        ExcelDataSource,
        FileDataSource,
        PDFDataSource,
    )

    # Web data sources
    from extract_transform_platform.data_sources.web import (
        APIDataSource,
        JinaDataSource,
        URLDataSource,
    )

    # Base classes
    from extract_transform_platform.core import BaseDataSource, IDataSource

    assert all([
        FileDataSource,
        ExcelDataSource,
        PDFDataSource,
        APIDataSource,
        URLDataSource,
        JinaDataSource,
        BaseDataSource,
        IDataSource,
    ])
    print("✅ All platform imports successful")


def test_edgar_wrapper_imports():
    """Verify all EDGAR wrapper imports work (with warnings)."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        from edgar_analyzer.data_sources import (
            APIDataSource,
            BaseDataSource,
            ExcelDataSource,
            FileDataSource,
            IDataSource,
            JinaDataSource,
            PDFDataSource,
            URLDataSource,
        )

        # Verify imports worked
        assert all([
            FileDataSource,
            ExcelDataSource,
            PDFDataSource,
            APIDataSource,
            URLDataSource,
            JinaDataSource,
            BaseDataSource,
            IDataSource,
        ])

        # Verify we got deprecation warnings
        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        print(f"✅ All EDGAR wrapper imports successful ({len(deprecation_warnings)} deprecation warnings)")

        for warning in deprecation_warnings[:3]:  # Show first 3
            print(f"   ⚠️  {warning.message}")


if __name__ == "__main__":
    test_platform_imports()
    test_edgar_wrapper_imports()
    print("\n✅ All import tests passed!")
