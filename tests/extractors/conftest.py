"""Test fixtures for extractor tests."""

import pytest
from pathlib import Path
import tempfile

from edgar_analyzer.extractors.registry import ExtractorRegistry


@pytest.fixture
def temp_registry_path(tmp_path):
    """Create temporary registry path."""
    return tmp_path / "test_registry.json"


@pytest.fixture
def empty_registry(temp_registry_path):
    """Create empty registry for testing."""
    return ExtractorRegistry(registry_path=temp_registry_path)


@pytest.fixture
def populated_registry(temp_registry_path):
    """Create registry with sample extractors."""
    registry = ExtractorRegistry(registry_path=temp_registry_path)

    registry.register(
        name="sct_extractor",
        class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
        version="1.0.0",
        description="Extract Summary Compensation Tables from DEF 14A filings",
        domain="sct",
        confidence=0.95,
        examples_count=3,
        tags=["sec", "edgar", "def14a", "compensation"],
    )

    return registry
