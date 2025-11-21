"""Configuration settings and service."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


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
    data_dir: str = Field(default="data")
    output_dir: str = Field(default="output")

    # Sub-settings
    edgar: EdgarSettings = Field(default_factory=EdgarSettings)
    cache: CacheSettings = Field(default_factory=CacheSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)


class ConfigService:
    """Configuration service implementation."""

    def __init__(self, settings: Optional[AppSettings] = None):
        """Initialize configuration service."""
        self._settings = settings or AppSettings()
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        directories = [
            self._settings.data_dir,
            self._settings.output_dir,
            self._settings.cache.cache_dir,
            self._settings.database.backup_dir,
            Path(self._settings.logging.file_path).parent,
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

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