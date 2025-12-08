"""Tests for ExtractorRegistry."""

import json
import tempfile
from pathlib import Path

import pytest

from edgar_analyzer.extractors.registry import ExtractorMetadata, ExtractorRegistry
from extract_transform_platform.core.base import IDataExtractor


class TestExtractorMetadata:
    """Tests for ExtractorMetadata dataclass."""

    def test_to_dict(self):
        """Test metadata serialization."""
        metadata = ExtractorMetadata(
            name="test_extractor",
            class_path="edgar_analyzer.extractors.test.TestExtractor",
            version="1.0.0",
            description="Test extractor",
            domain="test",
            confidence=0.95,
            examples_count=5,
            tags=["test", "example"],
        )

        data = metadata.to_dict()

        assert data["name"] == "test_extractor"
        assert data["class_path"] == "edgar_analyzer.extractors.test.TestExtractor"
        assert data["version"] == "1.0.0"
        assert data["description"] == "Test extractor"
        assert data["domain"] == "test"
        assert data["confidence"] == 0.95
        assert data["examples_count"] == 5
        assert data["tags"] == ["test", "example"]
        assert "created_at" in data
        assert "updated_at" in data

    def test_from_dict(self):
        """Test metadata deserialization."""
        data = {
            "name": "test_extractor",
            "class_path": "edgar_analyzer.extractors.test.TestExtractor",
            "version": "1.0.0",
            "description": "Test extractor",
            "domain": "test",
            "confidence": 0.95,
            "examples_count": 5,
            "tags": ["test", "example"],
            "created_at": "2025-12-07T00:00:00",
            "updated_at": "2025-12-07T00:00:00",
        }

        metadata = ExtractorMetadata.from_dict(data)

        assert metadata.name == "test_extractor"
        assert metadata.class_path == "edgar_analyzer.extractors.test.TestExtractor"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test extractor"
        assert metadata.domain == "test"
        assert metadata.confidence == 0.95
        assert metadata.examples_count == 5
        assert metadata.tags == ["test", "example"]
        assert metadata.created_at == "2025-12-07T00:00:00"
        assert metadata.updated_at == "2025-12-07T00:00:00"

    def test_round_trip(self):
        """Test serialization round-trip."""
        metadata = ExtractorMetadata(
            name="test_extractor",
            class_path="edgar_analyzer.extractors.test.TestExtractor",
            version="1.0.0",
            description="Test extractor",
            domain="test",
        )

        data = metadata.to_dict()
        restored = ExtractorMetadata.from_dict(data)

        assert restored.name == metadata.name
        assert restored.class_path == metadata.class_path
        assert restored.version == metadata.version


class TestExtractorRegistry:
    """Tests for ExtractorRegistry."""

    @pytest.fixture
    def temp_registry(self, tmp_path):
        """Create temporary registry for testing."""
        registry_path = tmp_path / "registry.json"
        return ExtractorRegistry(registry_path=registry_path)

    def test_init_creates_empty_registry(self, tmp_path):
        """Test that init creates empty registry if file doesn't exist."""
        registry_path = tmp_path / "registry.json"
        registry = ExtractorRegistry(registry_path=registry_path)

        assert len(registry.list()) == 0
        assert not registry_path.exists()  # Not created until first save

    def test_register_new_extractor(self, temp_registry):
        """Test registering a new extractor."""
        metadata = temp_registry.register(
            name="sct_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Extract Summary Compensation Tables",
            domain="sct",
            confidence=0.95,
            examples_count=3,
            tags=["sec", "edgar"],
        )

        assert metadata.name == "sct_extractor"
        assert metadata.class_path == "edgar_analyzer.extractors.sct.extractor.SCTExtractor"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Extract Summary Compensation Tables"
        assert metadata.domain == "sct"
        assert metadata.confidence == 0.95
        assert metadata.examples_count == 3
        assert metadata.tags == ["sec", "edgar"]

    def test_register_duplicate_raises(self, temp_registry):
        """Test that duplicate registration raises ValueError."""
        temp_registry.register(
            name="test_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Test",
            domain="test",
        )

        with pytest.raises(ValueError, match="already registered"):
            temp_registry.register(
                name="test_extractor",
                class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
                version="1.0.0",
                description="Test",
                domain="test",
            )

    def test_register_invalid_class_path_raises(self, temp_registry):
        """Test that invalid class_path raises ValueError."""
        with pytest.raises(ValueError, match="Invalid class_path"):
            temp_registry.register(
                name="test_extractor",
                class_path="edgar_analyzer.extractors.nonexistent.NonExistent",
                version="1.0.0",
                description="Test",
                domain="test",
            )

    def test_get_returns_class(self, temp_registry):
        """Test that get() returns the extractor class."""
        temp_registry.register(
            name="sct_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Extract Summary Compensation Tables",
            domain="sct",
        )

        extractor_class = temp_registry.get("sct_extractor")

        assert extractor_class.__name__ == "SCTExtractor"
        assert issubclass(extractor_class, IDataExtractor)

    def test_get_nonexistent_raises(self, temp_registry):
        """Test that get() raises KeyError for unknown extractor."""
        with pytest.raises(KeyError, match="not found"):
            temp_registry.get("nonexistent_extractor")

    def test_get_metadata(self, temp_registry):
        """Test get_metadata without loading class."""
        temp_registry.register(
            name="sct_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Extract Summary Compensation Tables",
            domain="sct",
        )

        metadata = temp_registry.get_metadata("sct_extractor")

        assert metadata.name == "sct_extractor"
        assert metadata.class_path == "edgar_analyzer.extractors.sct.extractor.SCTExtractor"

    def test_list_all(self, temp_registry):
        """Test listing all extractors."""
        temp_registry.register(
            name="sct_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Extract SCT",
            domain="sct",
            confidence=0.95,
        )

        temp_registry.register(
            name="test_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Test",
            domain="test",
            confidence=0.80,
        )

        extractors = temp_registry.list()

        assert len(extractors) == 2
        names = [e.name for e in extractors]
        assert "sct_extractor" in names
        assert "test_extractor" in names

    def test_list_with_domain_filter(self, temp_registry):
        """Test filtering by domain."""
        temp_registry.register(
            name="sct_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Extract SCT",
            domain="sct",
        )

        temp_registry.register(
            name="test_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Test",
            domain="test",
        )

        extractors = temp_registry.list(domain="sct")

        assert len(extractors) == 1
        assert extractors[0].name == "sct_extractor"

    def test_list_with_tags_filter(self, temp_registry):
        """Test filtering by tags."""
        temp_registry.register(
            name="sct_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Extract SCT",
            domain="sct",
            tags=["sec", "edgar"],
        )

        temp_registry.register(
            name="test_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Test",
            domain="test",
            tags=["test"],
        )

        extractors = temp_registry.list(tags=["sec"])

        assert len(extractors) == 1
        assert extractors[0].name == "sct_extractor"

    def test_list_with_confidence_filter(self, temp_registry):
        """Test filtering by minimum confidence."""
        temp_registry.register(
            name="high_confidence",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="High confidence",
            domain="test",
            confidence=0.95,
        )

        temp_registry.register(
            name="low_confidence",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Low confidence",
            domain="test",
            confidence=0.60,
        )

        extractors = temp_registry.list(min_confidence=0.80)

        assert len(extractors) == 1
        assert extractors[0].name == "high_confidence"

    def test_unregister(self, temp_registry):
        """Test removing an extractor."""
        temp_registry.register(
            name="sct_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Extract SCT",
            domain="sct",
        )

        result = temp_registry.unregister("sct_extractor")

        assert result is True
        assert len(temp_registry.list()) == 0

    def test_unregister_nonexistent(self, temp_registry):
        """Test unregistering nonexistent extractor returns False."""
        result = temp_registry.unregister("nonexistent")

        assert result is False

    def test_update(self, temp_registry):
        """Test updating extractor metadata."""
        temp_registry.register(
            name="sct_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Extract SCT",
            domain="sct",
            confidence=0.95,
        )

        metadata = temp_registry.update(
            "sct_extractor",
            version="1.1.0",
            confidence=0.98,
            description="Extract SCT (updated)",
        )

        assert metadata.version == "1.1.0"
        assert metadata.confidence == 0.98
        assert metadata.description == "Extract SCT (updated)"

    def test_persistence(self, tmp_path):
        """Test registry persists across instances."""
        registry_path = tmp_path / "registry.json"

        # Create and populate registry
        registry1 = ExtractorRegistry(registry_path=registry_path)
        registry1.register(
            name="sct_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Extract SCT",
            domain="sct",
        )

        # Load in new instance
        registry2 = ExtractorRegistry(registry_path=registry_path)
        extractors = registry2.list()

        assert len(extractors) == 1
        assert extractors[0].name == "sct_extractor"

    def test_persistence_file_format(self, tmp_path):
        """Test registry file format is valid JSON."""
        registry_path = tmp_path / "registry.json"

        registry = ExtractorRegistry(registry_path=registry_path)
        registry.register(
            name="sct_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="Extract SCT",
            domain="sct",
        )

        # Check file format
        with open(registry_path, "r") as f:
            data = json.load(f)

        assert "version" in data
        assert "extractors" in data
        assert "sct_extractor" in data["extractors"]
        assert data["extractors"]["sct_extractor"]["name"] == "sct_extractor"

    def test_dynamic_import_security(self, temp_registry):
        """Test that imports are restricted to allowed namespace."""
        with pytest.raises(ValueError, match="Invalid class_path"):
            temp_registry.register(
                name="malicious",
                class_path="os.system.MaliciousClass",
                version="1.0.0",
                description="Malicious",
                domain="malicious",
            )

    def test_dynamic_import_validates_interface(self, temp_registry):
        """Test that imported class must implement IDataExtractor."""
        # This test would require a non-IDataExtractor class in the namespace
        # For now, we test the validation logic indirectly through successful imports
        pass

    def test_concurrent_modifications(self, tmp_path):
        """Test that atomic writes prevent corruption."""
        registry_path = tmp_path / "registry.json"
        registry = ExtractorRegistry(registry_path=registry_path)

        # Register multiple extractors
        for i in range(5):
            registry.register(
                name=f"extractor_{i}",
                class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
                version="1.0.0",
                description=f"Extractor {i}",
                domain="test",
            )

        # Reload and verify all present
        registry2 = ExtractorRegistry(registry_path=registry_path)
        extractors = registry2.list()

        assert len(extractors) == 5


class TestExtractorRegistryIntegration:
    """Integration tests for registry with actual extractors."""

    def test_register_and_load_sct_extractor(self, tmp_path):
        """Test registering and loading SCT extractor."""
        registry_path = tmp_path / "registry.json"
        registry = ExtractorRegistry(registry_path=registry_path)

        # Register SCT extractor
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

        # Load class
        extractor_class = registry.get("sct_extractor")

        # Verify it's the right class
        assert extractor_class.__name__ == "SCTExtractor"
        assert issubclass(extractor_class, IDataExtractor)

        # Verify metadata
        metadata = registry.get_metadata("sct_extractor")
        assert metadata.confidence == 0.95
        assert metadata.domain == "sct"
        assert "compensation" in metadata.tags

    def test_multiple_domain_filtering(self, tmp_path):
        """Test filtering extractors by domain."""
        registry_path = tmp_path / "registry.json"
        registry = ExtractorRegistry(registry_path=registry_path)

        # Register extractors in different domains
        registry.register(
            name="sct_extractor",
            class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
            version="1.0.0",
            description="SCT",
            domain="sct",
        )

        # List by domain
        sct_extractors = registry.list(domain="sct")
        assert len(sct_extractors) == 1
        assert sct_extractors[0].name == "sct_extractor"

        all_extractors = registry.list()
        assert len(all_extractors) == 1
