#!/usr/bin/env python3
"""Script to fix test issues in test_batch1_datasources.py"""

import re

def fix_tests():
    test_file = "tests/integration/test_batch1_datasources.py"

    with open(test_file, 'r') as f:
        content = f.read()

    # Fix URL source deprecation warning test
    content = re.sub(
        r'(class TestURLDataSourceMigration:.*?def test_edgar_wrapper_import_with_warning.*?from edgar_analyzer\.data_sources import URLDataSource\s+)(assert len\(w\) == 1\s+assert issubclass\(w\[0\]\.category, DeprecationWarning\)\s+assert "edgar_analyzer\.data_sources\.url_source is deprecated" in str\(\s+w\[0\]\.message\s+\))',
        r'\1# Multiple warnings expected due to __init__.py imports\n            assert len(w) >= 1\n            # Check that at least one warning is for url_source\n            url_source_warnings = [\n                warning for warning in w\n                if "edgar_analyzer.data_sources.url_source is deprecated" in str(warning.message)\n            ]\n            assert len(url_source_warnings) >= 1\n            assert issubclass(url_source_warnings[0].category, DeprecationWarning)',
        content,
        flags=re.DOTALL
    )

    # Fix Jina source deprecation warning test
    content = re.sub(
        r'(class TestJinaDataSourceMigration:.*?def test_edgar_wrapper_import_with_warning.*?from edgar_analyzer\.data_sources import JinaDataSource\s+)(assert len\(w\) == 1\s+assert issubclass\(w\[0\]\.category, DeprecationWarning\)\s+assert "edgar_analyzer\.data_sources\.jina_source is deprecated" in str\(\s+w\[0\]\.message\s+\))',
        r'\1# Multiple warnings expected due to __init__.py imports\n            assert len(w) >= 1\n            # Check that at least one warning is for jina_source\n            jina_source_warnings = [\n                warning for warning in w\n                if "edgar_analyzer.data_sources.jina_source is deprecated" in str(warning.message)\n            ]\n            assert len(jina_source_warnings) >= 1\n            assert issubclass(jina_source_warnings[0].category, DeprecationWarning)',
        content,
        flags=re.DOTALL
    )

    # Fix API source test methods mocks (replace remaining httpx.Client.get with httpx.AsyncClient.request)
    content = re.sub(
        r'@patch\("httpx\.Client\.get"\)',
        r'@patch("httpx.AsyncClient.request")',
        content
    )
    content = re.sub(
        r'async def test_\w+\(self, mock_get: MagicMock\)',
        lambda m: m.group(0).replace('mock_get', 'mock_request'),
        content
    )
    content = re.sub(
        r'\bmock_get\.return_value\b',
        'mock_request.return_value',
        content
    )

    with open(test_file, 'w') as f:
        f.write(content)

    print("Tests fixed successfully!")

if __name__ == "__main__":
    fix_tests()
