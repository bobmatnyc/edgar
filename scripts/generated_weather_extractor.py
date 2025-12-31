# Standard library imports
from dataclasses import dataclass
from typing import Any, Optional

# Third-party imports
import httpx
from pydantic import BaseModel, Field, field_validator


# Custom exception hierarchy
class DataSourceError(Exception):
    """Base exception for data source errors."""

    pass


class HTTPError(DataSourceError):
    """HTTP request failed."""

    pass


class ExtractionError(DataSourceError):
    """Data extraction failed."""

    pass


class ValidationError(DataSourceError):
    """Data validation failed."""

    pass


class MissingFieldError(ExtractionError):
    """Required field is missing from source data."""

    pass


class InvalidTypeError(ExtractionError):
    """Field has invalid type."""

    pass


# Pydantic models
class WeatherData(BaseModel):
    """Validated weather data model.

    This model represents extracted and validated weather data with temperature
    converted from Kelvin to Celsius and humidity as a percentage.

    Attributes:
        temperature: Temperature in Celsius, must be between -50 and 50
        humidity: Relative humidity percentage, must be between 0 and 100
    """

    temperature: float = Field(
        ..., description="Temperature in Celsius", ge=-50.0, le=50.0
    )
    humidity: int = Field(..., description="Humidity percentage", ge=0, le=100)

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within acceptable range.

        Args:
            v: Temperature value in Celsius

        Returns:
            Validated temperature value

        Raises:
            ValueError: If temperature is outside valid range
        """
        if v < -50.0 or v > 50.0:
            raise ValueError(f"Temperature {v}°C is outside valid range [-50, 50]")
        return v

    @field_validator("humidity")
    @classmethod
    def validate_humidity(cls, v: int) -> int:
        """Validate humidity is within acceptable range.

        Args:
            v: Humidity percentage value

        Returns:
            Validated humidity value

        Raises:
            ValueError: If humidity is outside valid range
        """
        if v < 0 or v > 100:
            raise ValueError(f"Humidity {v}% is outside valid range [0, 100]")
        return v


# Data source implementation
@dataclass(frozen=True)
class WeatherDataSource:
    """Fetches weather data from REST API.

    This class implements the IDataSource interface to fetch raw weather data
    from an external REST API endpoint. It handles HTTP communication and
    returns the raw JSON response.

    Attributes:
        http_client: Async HTTP client for making requests
        api_url: Full URL of the weather API endpoint
        timeout: Request timeout in seconds

    Example:
        >>> async with httpx.AsyncClient() as client:
        ...     source = WeatherDataSource(
        ...         http_client=client,
        ...         api_url="https://api.openweathermap.org/data/2.5/weather",
        ...         timeout=30.0
        ...     )
        ...     data = await source.fetch()
    """

    http_client: httpx.AsyncClient
    api_url: str
    timeout: float = 30.0

    async def fetch(self) -> dict[str, Any]:
        """Fetch raw data from the weather API.

        Makes an HTTP GET request to the configured API endpoint and returns
        the JSON response as a dictionary.

        Returns:
            Raw data dictionary from the API response

        Raises:
            HTTPError: If the HTTP request fails or returns non-200 status
            DataSourceError: If response cannot be parsed as JSON
        """
        try:
            response = await self.http_client.get(self.api_url, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPError(
                f"HTTP request failed with status {e.response.status_code}: "
                f"{e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise HTTPError(f"HTTP request failed: {str(e)}") from e

        try:
            return response.json()
        except ValueError as e:
            raise DataSourceError(f"Failed to parse JSON response: {str(e)}") from e


# Data extractor implementation
@dataclass(frozen=True)
class WeatherDataExtractor:
    """Extracts structured weather data from API responses.

    This class implements the IDataExtractor interface to extract, transform,
    and validate weather data from raw API responses. It applies JSONPath
    extraction patterns, performs unit conversions, and validates the results
    against defined constraints.

    The extractor handles:
    - Extracting temperature from $.main.temp (Kelvin)
    - Extracting humidity from $.main.humidity (percentage)
    - Converting temperature from Kelvin to Celsius
    - Validating all fields against defined constraints

    Example:
        >>> extractor = WeatherDataExtractor()
        >>> raw_data = {
        ...     "main": {
        ...         "temp": 293.15,
        ...         "humidity": 65
        ...     }
        ... }
        >>> weather = extractor.extract(raw_data)
        >>> weather.temperature
        20.0
    """

    def extract(self, raw_data: dict[str, Any]) -> WeatherData:
        """Extract and validate weather data from raw API response.

        Extracts temperature and humidity from the raw data using JSONPath
        patterns, applies transformations (Kelvin to Celsius conversion),
        and validates the results.

        Args:
            raw_data: Raw data dictionary from the API response

        Returns:
            Validated WeatherData model instance

        Raises:
            MissingFieldError: If required fields are missing
            InvalidTypeError: If field types are invalid
            ValidationError: If validation constraints are violated
        """
        # Extract main section
        main_data = self._extract_field(raw_data, ["main"], "main", required=True)

        if not isinstance(main_data, dict):
            raise InvalidTypeError(
                f"Expected 'main' to be dict, got {type(main_data).__name__}"
            )

        # Extract temperature (in Kelvin)
        temperature_kelvin = self._extract_field(
            main_data, ["temp"], "temperature", required=True
        )

        # Validate temperature type
        if not isinstance(temperature_kelvin, (int, float)):
            raise InvalidTypeError(
                f"Expected temperature to be numeric, "
                f"got {type(temperature_kelvin).__name__}"
            )

        # Extract humidity
        humidity = self._extract_field(
            main_data, ["humidity"], "humidity", required=True
        )

        # Validate humidity type
        if not isinstance(humidity, (int, float)):
            raise InvalidTypeError(
                f"Expected humidity to be numeric, " f"got {type(humidity).__name__}"
            )

        # Transform temperature from Kelvin to Celsius
        temperature_celsius = self._convert_kelvin_to_celsius(temperature_kelvin)

        # Convert humidity to int
        humidity_int = int(humidity)

        # Validate and create model
        try:
            return WeatherData(temperature=temperature_celsius, humidity=humidity_int)
        except ValueError as e:
            raise ValidationError(f"Data validation failed: {str(e)}") from e

    def _extract_field(
        self,
        data: dict[str, Any],
        path: list[str],
        field_name: str,
        required: bool = True,
        default_value: Optional[Any] = None,
    ) -> Any:
        """Extract a field from nested dictionary using path.

        Args:
            data: Dictionary to extract from
            path: List of keys representing the path to the field
            field_name: Name of the field for error messages
            required: Whether the field is required
            default_value: Default value if field is missing and not required

        Returns:
            Extracted field value

        Raises:
            MissingFieldError: If required field is missing
        """
        current = data

        for key in path:
            if not isinstance(current, dict):
                if required:
                    raise MissingFieldError(
                        f"Cannot navigate to '{field_name}': "
                        f"'{key}' not found in non-dict value"
                    )
                return default_value

            if key not in current:
                if required:
                    raise MissingFieldError(
                        f"Required field '{field_name}' not found at path: "
                        f"{'.'.join(path)}"
                    )
                return default_value

            current = current[key]

        return current

    def _convert_kelvin_to_celsius(self, kelvin: float) -> float:
        """Convert temperature from Kelvin to Celsius.

        Applies the formula: celsius = kelvin - 273.15

        Args:
            kelvin: Temperature in Kelvin

        Returns:
            Temperature in Celsius
        """
        return float(kelvin) - 273.15
