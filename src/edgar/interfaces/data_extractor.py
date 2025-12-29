"""Interface definitions for data extraction.

This module defines the Protocol interfaces that generated extractors
must implement. Using Protocol enables structural subtyping (duck typing
with type checking).
"""

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


@runtime_checkable
class IDataSource(Protocol):
    """Interface for fetching raw data from external sources.

    Implementations should handle:
    - HTTP requests to APIs
    - Authentication/authorization
    - Rate limiting and retries
    - Error handling

    Example:
        >>> class WeatherApiSource:
        ...     async def fetch(self) -> dict[str, Any]:
        ...         response = await httpx.get("https://api.weather.com/...")
        ...         return response.json()
    """

    async def fetch(self) -> dict[str, Any]:
        """Fetch raw data from external source.

        Returns:
            Raw data dictionary from the source

        Raises:
            ConnectionError: If source is unreachable
            AuthenticationError: If credentials are invalid
        """
        ...


@runtime_checkable
class IDataExtractor(Protocol):
    """Interface for extracting structured data from raw responses.

    Implementations should handle:
    - Field mapping from raw to structured
    - Type conversion and validation
    - Error handling for missing/invalid data

    Example:
        >>> class WeatherExtractor:
        ...     def extract(self, raw_data: dict[str, Any]) -> WeatherData:
        ...         return WeatherData(
        ...             temperature=raw_data["temp"],
        ...             condition=raw_data["weather"]["description"]
        ...         )
    """

    def extract(self, raw_data: dict[str, Any]) -> BaseModel:
        """Extract structured data from raw response.

        Args:
            raw_data: Raw API response dictionary

        Returns:
            Pydantic model with extracted data

        Raises:
            ValidationError: If extraction fails validation
            KeyError: If required fields are missing
        """
        ...
