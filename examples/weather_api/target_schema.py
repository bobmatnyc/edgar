"""Target schema for Weather API data extraction.

This defines the desired output structure for weather data extraction.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class WeatherData(BaseModel):
    """Extracted weather data model.

    Attributes:
        city_name: Name of the city
        temperature_celsius: Temperature in Celsius
        feels_like_celsius: Feels like temperature in Celsius
        humidity: Relative humidity percentage
        pressure: Atmospheric pressure in hPa
        wind_speed_mps: Wind speed in meters per second
        weather_condition: Main weather condition (Clear, Clouds, Rain, etc.)
        weather_description: Detailed weather description
        timestamp: Observation timestamp
    """

    city_name: str = Field(..., description="City name")
    temperature_celsius: float = Field(
        ...,
        description="Temperature in Celsius",
        ge=-100,
        le=60,
    )
    feels_like_celsius: float = Field(
        ...,
        description="Feels like temperature in Celsius",
        ge=-100,
        le=60,
    )
    humidity: int = Field(
        ...,
        description="Relative humidity percentage",
        ge=0,
        le=100,
    )
    pressure: int = Field(
        ...,
        description="Atmospheric pressure in hPa",
        ge=800,
        le=1100,
    )
    wind_speed_mps: float = Field(
        ...,
        description="Wind speed in meters per second",
        ge=0,
    )
    weather_condition: str = Field(
        ...,
        description="Main weather condition",
    )
    weather_description: str = Field(
        ...,
        description="Detailed weather description",
    )
    timestamp: datetime = Field(
        ...,
        description="Observation timestamp",
    )
