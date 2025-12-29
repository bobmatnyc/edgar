"""Cache service implementation."""

import json
import time
from pathlib import Path
from typing import Any, Optional

import structlog

from edgar_analyzer.config.settings import ConfigService
from edgar_analyzer.services.interfaces import ICacheService

logger = structlog.get_logger(__name__)


class CacheService(ICacheService):
    """File-based cache service implementation."""

    def __init__(self, config: ConfigService):
        """Initialize cache service."""
        self._config = config
        self._cache_config = config.get_cache_config()
        self._cache_dir = Path(self._cache_config["cache_dir"])
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Cache service initialized", cache_dir=str(self._cache_dir))

    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for key."""
        # Replace invalid filename characters
        safe_key = key.replace("/", "_").replace(":", "_").replace("?", "_")
        return self._cache_dir / f"{safe_key}.json"

    def _is_expired(self, cache_data: dict, ttl: Optional[int] = None) -> bool:
        """Check if cache entry is expired."""
        if not self._cache_config["enabled"]:
            return True

        if ttl is None:
            ttl = self._cache_config["ttl_default"]

        if ttl <= 0:  # No expiration
            return False

        timestamp = cache_data.get("timestamp", 0)
        return time.time() - timestamp > ttl

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value by key."""
        if not self._cache_config["enabled"]:
            return None

        cache_file = self._get_cache_file(key)

        try:
            if not cache_file.exists():
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Check expiration
            if self._is_expired(cache_data):
                await self.delete(key)
                logger.debug("Cache entry expired", key=key)
                return None

            logger.debug("Cache hit", key=key)
            return cache_data.get("data")

        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Cache read error", key=key, error=str(e))
            await self.delete(key)
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value with optional TTL."""
        if not self._cache_config["enabled"]:
            return

        cache_file = self._get_cache_file(key)

        cache_data = {
            "data": value,
            "timestamp": time.time(),
            "ttl": ttl or self._cache_config["ttl_default"]
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, default=str)

            logger.debug("Cache set", key=key, ttl=cache_data["ttl"])

        except (IOError, TypeError) as e:
            logger.warning("Cache write error", key=key, error=str(e))

    async def delete(self, key: str) -> None:
        """Delete cached value."""
        cache_file = self._get_cache_file(key)

        try:
            if cache_file.exists():
                cache_file.unlink()
                logger.debug("Cache entry deleted", key=key)
        except IOError as e:
            logger.warning("Cache delete error", key=key, error=str(e))

    async def clear(self) -> None:
        """Clear all cached values."""
        try:
            for cache_file in self._cache_dir.glob("*.json"):
                cache_file.unlink()

            logger.info("Cache cleared")

        except IOError as e:
            logger.warning("Cache clear error", error=str(e))

    async def cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        if not self._cache_config["enabled"]:
            return

        removed_count = 0

        try:
            for cache_file in self._cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)

                    if self._is_expired(cache_data):
                        cache_file.unlink()
                        removed_count += 1

                except (json.JSONDecodeError, IOError):
                    # Remove corrupted cache files
                    cache_file.unlink()
                    removed_count += 1

            if removed_count > 0:
                logger.info("Expired cache entries removed", count=removed_count)

        except Exception as e:
            logger.warning("Cache cleanup error", error=str(e))