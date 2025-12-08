"""
Extractor Registry for dynamic extractor management.

Provides:
- Registration of generated extractors with metadata
- Dynamic loading via importlib
- JSON persistence across sessions
- Filtering by tags, confidence, etc.

Design Decisions:
- **JSON Persistence**: Simple, human-readable, version-controllable
- **Atomic Writes**: Temp file + rename prevents corruption
- **Namespace Security**: Only allow imports from edgar_analyzer.extractors.*
- **Interface Validation**: Verify loaded class implements IDataExtractor
- **Singleton Registry**: One registry.json file per installation

Performance:
- Time Complexity: O(1) for get(), O(n) for list() where n = num extractors
- Space Complexity: O(n) metadata storage
- Dynamic import cached by Python's import system

Example:
    >>> registry = ExtractorRegistry()
    >>> registry.register(
    ...     name="sct_extractor",
    ...     class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
    ...     version="1.0.0",
    ...     description="Extract Summary Compensation Tables",
    ...     domain="sct"
    ... )
    >>> extractor_class = registry.get("sct_extractor")
    >>> extractor = extractor_class(openrouter_client)
"""

import importlib
import json
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import structlog

# Import the interface that all extractors must implement
from extract_transform_platform.core.base import IDataExtractor

logger = structlog.get_logger(__name__)


@dataclass
class ExtractorMetadata:
    """Metadata for a registered extractor.

    Attributes:
        name: Unique identifier (e.g., "sct_extractor")
        class_path: Importable path (e.g., "edgar_analyzer.extractors.sct.extractor.SCTExtractor")
        version: Semantic version (e.g., "1.0.0")
        description: Human-readable description
        domain: Domain slug (e.g., "sct", "10k", "news")
        confidence: Pattern analysis confidence (0.0-1.0)
        examples_count: Number of training examples
        tags: Searchable tags
        created_at: ISO timestamp of registration
        updated_at: ISO timestamp of last update
    """

    name: str
    class_path: str
    version: str
    description: str
    domain: str
    confidence: float = 0.0
    examples_count: int = 0
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractorMetadata":
        """Deserialize metadata from dictionary."""
        return cls(**data)


class ExtractorRegistry:
    """
    Registry for dynamically loading and managing extractors.

    The registry provides:
    - Centralized metadata for all extractors
    - Dynamic class loading with validation
    - JSON persistence across sessions
    - Filtering and search capabilities

    Thread Safety: Not thread-safe (file writes use atomic rename)
    Concurrency: Safe for single-threaded CLI usage

    Example:
        >>> registry = ExtractorRegistry()
        >>> registry.register(
        ...     name="sct_extractor",
        ...     class_path="edgar_analyzer.extractors.sct.extractor.SCTExtractor",
        ...     version="1.0.0",
        ...     description="Extract Summary Compensation Tables",
        ...     domain="sct"
        ... )
        >>> extractor_class = registry.get("sct_extractor")
        >>> extractor = extractor_class(openrouter_client)
    """

    # Security: Only allow imports from this namespace
    ALLOWED_NAMESPACE = "edgar_analyzer.extractors."

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize registry.

        Args:
            registry_path: Path to registry.json. Defaults to package location.
        """
        if registry_path is None:
            # Default to package location
            registry_path = (
                Path(__file__).parent / "registry.json"
            )

        self.registry_path = Path(registry_path)
        self._extractors: Dict[str, ExtractorMetadata] = {}

        # Load existing registry
        self._load_registry()

        logger.info(
            "ExtractorRegistry initialized",
            registry_path=str(self.registry_path),
            extractors_count=len(self._extractors),
        )

    def register(
        self,
        name: str,
        class_path: str,
        version: str,
        description: str,
        domain: str,
        confidence: float = 0.0,
        examples_count: int = 0,
        tags: Optional[List[str]] = None,
    ) -> ExtractorMetadata:
        """
        Register a new extractor.

        Args:
            name: Unique identifier for the extractor
            class_path: Full importable path to extractor class
            version: Semantic version string
            description: Human-readable description
            domain: Domain slug
            confidence: Pattern analysis confidence (0.0-1.0)
            examples_count: Number of training examples used
            tags: Searchable tags

        Returns:
            ExtractorMetadata for the registered extractor

        Raises:
            ValueError: If name already exists (use update() instead)
        """
        if name in self._extractors:
            raise ValueError(
                f"Extractor '{name}' already registered. Use update() to modify."
            )

        # Validate class can be imported before registering
        try:
            self._dynamic_import(class_path)
        except (ImportError, TypeError) as e:
            raise ValueError(f"Invalid class_path '{class_path}': {e}") from e

        metadata = ExtractorMetadata(
            name=name,
            class_path=class_path,
            version=version,
            description=description,
            domain=domain,
            confidence=confidence,
            examples_count=examples_count,
            tags=tags or [],
        )

        self._extractors[name] = metadata
        self._save_registry()

        logger.info(
            "Registered extractor",
            name=name,
            class_path=class_path,
            version=version,
        )

        return metadata

    def get(self, name: str) -> Type[IDataExtractor]:
        """
        Get extractor class by name.

        Args:
            name: Extractor identifier

        Returns:
            Extractor class (not instance)

        Raises:
            KeyError: If extractor not found
            ImportError: If class cannot be imported
        """
        if name not in self._extractors:
            raise KeyError(f"Extractor '{name}' not found in registry")

        metadata = self._extractors[name]

        logger.debug(
            "Loading extractor class",
            name=name,
            class_path=metadata.class_path,
        )

        return self._dynamic_import(metadata.class_path)

    def get_metadata(self, name: str) -> ExtractorMetadata:
        """Get metadata without loading class.

        Args:
            name: Extractor identifier

        Returns:
            ExtractorMetadata

        Raises:
            KeyError: If extractor not found
        """
        if name not in self._extractors:
            raise KeyError(f"Extractor '{name}' not found in registry")

        return self._extractors[name]

    def list(
        self,
        domain: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_confidence: float = 0.0,
    ) -> List[ExtractorMetadata]:
        """
        List registered extractors with optional filtering.

        Args:
            domain: Filter by domain
            tags: Filter by tags (any match)
            min_confidence: Minimum confidence threshold

        Returns:
            List of matching ExtractorMetadata
        """
        results = []

        for metadata in self._extractors.values():
            # Apply filters
            if domain and metadata.domain != domain:
                continue

            if tags and not any(tag in metadata.tags for tag in tags):
                continue

            if metadata.confidence < min_confidence:
                continue

            results.append(metadata)

        logger.debug(
            "Listed extractors",
            total=len(self._extractors),
            filtered=len(results),
            domain=domain,
            tags=tags,
            min_confidence=min_confidence,
        )

        return results

    def unregister(self, name: str) -> bool:
        """
        Remove extractor from registry.

        Args:
            name: Extractor identifier

        Returns:
            True if removed, False if not found
        """
        if name not in self._extractors:
            logger.warning("Extractor not found for removal", name=name)
            return False

        del self._extractors[name]
        self._save_registry()

        logger.info("Unregistered extractor", name=name)
        return True

    def update(self, name: str, **kwargs) -> ExtractorMetadata:
        """Update existing extractor metadata.

        Args:
            name: Extractor identifier
            **kwargs: Fields to update (version, description, confidence, etc.)

        Returns:
            Updated ExtractorMetadata

        Raises:
            KeyError: If extractor not found
        """
        if name not in self._extractors:
            raise KeyError(f"Extractor '{name}' not found in registry")

        metadata = self._extractors[name]

        # Update allowed fields
        allowed_fields = {
            "version",
            "description",
            "domain",
            "confidence",
            "examples_count",
            "tags",
            "class_path",
        }

        for key, value in kwargs.items():
            if key not in allowed_fields:
                logger.warning(f"Ignoring unknown field: {key}")
                continue

            setattr(metadata, key, value)

        # Update timestamp
        metadata.updated_at = datetime.now(timezone.utc).isoformat()

        self._save_registry()

        logger.info(
            "Updated extractor metadata",
            name=name,
            updated_fields=list(kwargs.keys()),
        )

        return metadata

    def _dynamic_import(self, class_path: str) -> Type[IDataExtractor]:
        """
        Dynamically import extractor class.

        Security: Only imports from edgar_analyzer.extractors namespace.

        Args:
            class_path: Full importable path (e.g., "edgar_analyzer.extractors.sct.extractor.SCTExtractor")

        Returns:
            Extractor class

        Raises:
            ImportError: If import fails or namespace invalid
            TypeError: If class doesn't implement IDataExtractor
        """
        # Validate namespace for security
        if not class_path.startswith(self.ALLOWED_NAMESPACE):
            raise ImportError(
                f"Invalid namespace: {class_path}. "
                f"Must be under {self.ALLOWED_NAMESPACE}"
            )

        # Split into module path and class name
        try:
            module_path, class_name = class_path.rsplit(".", 1)
        except ValueError as e:
            raise ImportError(f"Invalid class_path format: {class_path}") from e

        # Import module
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            raise ImportError(
                f"Could not import module '{module_path}': {e}"
            ) from e

        # Get class from module
        try:
            cls = getattr(module, class_name)
        except AttributeError as e:
            raise ImportError(
                f"Class '{class_name}' not found in module '{module_path}'"
            ) from e

        # Validate implements interface
        if not issubclass(cls, IDataExtractor):
            raise TypeError(
                f"{class_name} does not implement IDataExtractor interface"
            )

        logger.debug(
            "Successfully imported extractor class",
            class_path=class_path,
            class_name=class_name,
        )

        return cls

    def _load_registry(self) -> None:
        """Load registry from JSON file.

        If file doesn't exist, initializes empty registry.
        If file is corrupted, logs error and continues with empty registry.
        """
        if not self.registry_path.exists():
            logger.info(
                "Registry file not found, creating new registry",
                path=str(self.registry_path),
            )
            self._extractors = {}
            return

        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Load extractors from JSON
            extractors_data = data.get("extractors", {})
            self._extractors = {
                name: ExtractorMetadata.from_dict(metadata)
                for name, metadata in extractors_data.items()
            }

            logger.info(
                "Loaded registry from file",
                path=str(self.registry_path),
                extractors_count=len(self._extractors),
            )

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error(
                "Failed to load registry, starting with empty registry",
                path=str(self.registry_path),
                error=str(e),
            )
            self._extractors = {}

    def _save_registry(self) -> None:
        """Save registry to JSON file (atomic write).

        Uses temp file + atomic rename to prevent corruption.
        """
        # Ensure parent directory exists
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data structure
        data = {
            "version": "1.0.0",
            "extractors": {
                name: metadata.to_dict()
                for name, metadata in self._extractors.items()
            },
        }

        # Atomic write: temp file + rename
        try:
            # Write to temp file in same directory (ensures same filesystem)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.registry_path.parent,
                delete=False,
                suffix=".tmp",
            ) as f:
                json.dump(data, f, indent=2, sort_keys=True)
                temp_path = Path(f.name)

            # Atomic rename
            temp_path.replace(self.registry_path)

            logger.debug(
                "Saved registry to file",
                path=str(self.registry_path),
                extractors_count=len(self._extractors),
            )

        except Exception as e:
            logger.error(
                "Failed to save registry",
                path=str(self.registry_path),
                error=str(e),
            )
            # Clean up temp file if it exists
            if temp_path and temp_path.exists():
                temp_path.unlink()
            raise
