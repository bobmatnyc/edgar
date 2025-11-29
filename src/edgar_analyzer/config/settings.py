"""Configuration settings and service."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class EdgarSettings(BaseModel):
    """EDGAR API settings."""

    base_url: str = Field(default="https://data.sec.gov")
    user_agent: str = Field(
        default="Edgar Analyzer Tool contact@example.com"
    )
    rate_limit_delay: float = Field(default=0.1)
    max_retries: int = Field(default=3)
    timeout: int = Field(default=30)


class CacheSettings(BaseModel):
    """Cache settings."""

    enabled: bool = Field(default=True)
    ttl_default: int = Field(default=3600)  # 1 hour
    ttl_company_facts: int = Field(default=86400)  # 24 hours
    ttl_submissions: int = Field(default=3600)  # 1 hour
    cache_dir: str = Field(default="data/cache")


class LoggingSettings(BaseModel):
    """Logging settings."""

    level: str = Field(default="INFO")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_enabled: bool = Field(default=True)
    file_path: str = Field(default="logs/edgar_analyzer.log")
    console_enabled: bool = Field(default=True)


class DatabaseSettings(BaseModel):
    """Database settings for company data."""

    companies_file: str = Field(default="data/companies/fortune_500_complete.json")
    backup_enabled: bool = Field(default=True)
    backup_dir: str = Field(default="data/backups")


class AppSettings(BaseModel):
    """Main application settings."""

    app_name: str = Field(default="Edgar Analyzer")
    version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)

    # Base directory for all artifacts (from EDGAR_ARTIFACTS_DIR env var)
    artifacts_base_dir: Optional[Path] = Field(
        default=None,
        description="Base directory for artifacts (env: EDGAR_ARTIFACTS_DIR)"
    )

    # Relative paths (resolved relative to artifacts_base_dir if set)
    data_dir: str = Field(default="data")
    output_dir: str = Field(default="output")
    projects_dir: str = Field(default="projects")

    # Sub-settings
    edgar: EdgarSettings = Field(default_factory=EdgarSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    @classmethod
    def from_environment(cls) -> "AppSettings":
        """Load settings from environment variables.

        Returns:
            AppSettings instance with environment-based configuration
        """
        artifacts_base = os.getenv("EDGAR_ARTIFACTS_DIR")

        # Convert to Path if set and not empty
        artifacts_path = None
        if artifacts_base and artifacts_base.strip():
            artifacts_path = Path(artifacts_base).expanduser().resolve()

        return cls(artifacts_base_dir=artifacts_path)

    def get_absolute_path(self, relative_path: str) -> Path:
        """Get absolute path for an artifact directory.

        Args:
            relative_path: Relative path from artifacts base or current directory

        Returns:
            Absolute Path object
        """
        if self.artifacts_base_dir:
            return (self.artifacts_base_dir / relative_path).resolve()
        return Path(relative_path).resolve()


class ConfigService:
    """Configuration service implementation."""

    def __init__(self, settings: Optional[AppSettings] = None):
        """Initialize configuration service."""
        # Use environment-aware settings by default
        self._settings = settings or AppSettings.from_environment()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        # Check if using external artifacts directory
        if self._settings.artifacts_base_dir:
            base_path = self._settings.artifacts_base_dir
            if not base_path.exists():
                logger.warning(
                    f"Creating external artifacts directory: {base_path}"
                )
                try:
                    base_path.mkdir(parents=True, exist_ok=True)
                except (PermissionError, OSError) as e:
                    raise RuntimeError(
                        f"Cannot create artifacts directory at {base_path}: {e}"
                    ) from e

        # Resolve directories using get_absolute_path
        directories = [
            self._settings.get_absolute_path(self._settings.data_dir),
            self._settings.get_absolute_path(self._settings.output_dir),
            self._settings.get_absolute_path(self._settings.projects_dir),
            self._settings.get_absolute_path(self._settings.cache.cache_dir),
            self._settings.get_absolute_path(self._settings.database.backup_dir),
            self._settings.get_absolute_path(self._settings.logging.file_path).parent,
        ]

        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except (PermissionError, OSError) as e:
                raise RuntimeError(
                    f"Cannot create directory {directory}: {e}"
                ) from e

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self._settings

        try:
            for k in keys:
                value = getattr(value, k)
            return value
        except AttributeError:
            return default

    def get_edgar_config(self) -> Dict[str, Any]:
        """Get EDGAR API configuration."""
        return {
            "base_url": self._settings.edgar.base_url,
            "user_agent": self._settings.edgar.user_agent,
            "rate_limit_delay": self._settings.edgar.rate_limit_delay,
            "max_retries": self._settings.edgar.max_retries,
            "timeout": self._settings.edgar.timeout,
        }

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration."""
        return {
            "enabled": self._settings.cache.enabled,
            "ttl_default": self._settings.cache.ttl_default,
            "ttl_company_facts": self._settings.cache.ttl_company_facts,
            "ttl_submissions": self._settings.cache.ttl_submissions,
            "cache_dir": self._settings.cache.cache_dir,
        }

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            "level": self._settings.logging.level,
            "format": self._settings.logging.format,
            "file_enabled": self._settings.logging.file_enabled,
            "file_path": self._settings.logging.file_path,
            "console_enabled": self._settings.logging.console_enabled,
        }

    @property
    def settings(self) -> AppSettings:
        """Get application settings."""
        return self._settings


# Helper functions for testing and CLI usage

def get_artifacts_dir() -> Path:
    """Get the base artifacts directory.

    Returns:
        Path to artifacts directory (external if EDGAR_ARTIFACTS_DIR set, else in-repo)
    """
    settings = AppSettings.from_environment()
    if settings.artifacts_base_dir:
        return settings.artifacts_base_dir
    return Path.cwd()


def ensure_artifacts_structure() -> None:
    """Ensure artifacts directory structure exists.

    Creates:
        - {artifacts_dir}/projects/
        - {artifacts_dir}/output/
        - {artifacts_dir}/data/
        - {artifacts_dir}/data/cache/
    """
    config_service = ConfigService()
    # Directory creation happens in __init__ via _ensure_directories
    logger.info(f"Artifacts structure ensured at: {get_artifacts_dir()}")