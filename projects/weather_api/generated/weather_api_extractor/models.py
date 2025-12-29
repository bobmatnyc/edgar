"""
Data models for WeatherExtractor
Defines input and output schemas inferred from OpenWeatherMap API examples.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
class WeatherInputSchema(BaseModel):
    """Input data schema for OpenWeatherMap API response.
    This model represents the raw data structure from the OpenWeatherMap
    current weather API endpoint.
    Example:
        >>> data = WeatherInputSchema(
        ...     name="London",
        ...     sys={"country": "GB"},
        ...     main={"temp": 15.5, "humidity": 72},
        ...     wind={"speed": 4.1},
        ...     clouds={"all": 75},
        ...     weather=[{"description": "light rain"}],
        ...     visibility=10000,
        ...     cod=200
        ... )
    """
    name: str = Field(..., description="City name")
    sys: Dict[str, Any] = Field(..., description="System data including country")
    main: Dict[str, Any] = Field(
        ...,
        description="Main weather parameters (temp, pressure, humidity)"
    )
    wind: Dict[str, Any] = Field(..., description="Wind data")
    clouds: Dict[str, Any] = Field(..., description="Cloudiness data")
    weather: List[Dict[str, Any]] = Field(
        ...,
        description="Weather condition array",
        min_length=1
    )
    visibility: int = Field(..., description="Visibility in meters")
    cod: int = Field(..., description="API response code")
    class Config:
        """Pydantic model configuration."""
        extra = "allow"  # Allow extra fields from API
    @field_validator('weather')
    @classmethod
    def validate_weather_array(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate weather array has at least one element.
        Args:
            v: Weather array to validate
        Returns:
            Validated weather array
        Raises:
            ValueError: If weather array is empty
        """
        if not v or len(v) == 0:
            raise ValueError("Weather array must contain at least one element")
        return v
class WeatherOutputSchema(BaseModel):
    """Output data schema for WeatherExtractor.
    This model represents the transformed and validated weather data structure.
    Example:
        >>> output = WeatherOutputSchema(
        ...     city="London",
        ...     country="GB",
        ...     temperature_c=15.5,
        ...     feels_like_c=14.2,
        ...     humidity_percent=72,
        ...     pressure_hpa=1012,
        ...     wind_speed_ms=4.1,
        ...     conditions="light rain",
        ...     cloudiness_percent=75,
        ...     visibility_m=10000
        ... )
    """
    city: str = Field(..., description="City name")
    country: str = Field(..., description="Country code (ISO 3166-1 alpha-2)")
    temperature_c: float = Field(
        ...,
        description="Temperature in Celsius",
        ge=-60,
        le=60
    )
    feels_like_c: float = Field(
        ...,
        description="Feels like temperature in Celsius",
        ge=-60,
        le=60
    )
    humidity_percent: int = Field(
        ...,
        description="Humidity percentage",
        ge=0,
        le=100
    )
    pressure_hpa: int = Field(
        ...,
        description="Atmospheric pressure in hPa",
        ge=870,
        le=1085
    )
    wind_speed_ms: float = Field(
        ...,
        description="Wind speed in meters per second",
        ge=0,
        le=113
    )
    conditions: str = Field(..., description="Weather condition description")
    cloudiness_percent: int = Field(
        ...,
        description="Cloudiness percentage",
        ge=0,
        le=100
    )
    visibility_m: int = Field(
        ...,
        description="Visibility in meters",
        ge=0,
        le=100000
    )
    @field_validator('city', 'country', 'conditions')
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        """Validate string fields are not empty.
        Args:
            v: String value to validate
        Returns:
            Validated string
        Raises:
            ValueError: If string is empty
        """
        if not v or not v.strip():
            raise ValueError("String field cannot be empty")
        return v