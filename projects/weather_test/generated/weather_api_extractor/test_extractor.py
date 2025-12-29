"""
Unit tests for WeatherExtractor
Tests validate extraction and transformation against provided examples.
"""
import pytest
from unittest.mock import AsyncMock, patch, Mock, MagicMock
import asyncio
import time
from extractor import WeatherExtractor
from models import WeatherInputSchema, WeatherOutputSchema
@pytest.fixture
def mock_config() -> dict:
    """Create mock configuration for testing.
    Returns:
        Configuration dictionary with test settings
    """
    return {
        'data_sources': [
            {
                'auth': {
                    'key': 'OPENWEATHER_API_KEY'
                }
            }
        ]
    }
@pytest.fixture
def mock_logger() -> Mock:
    """Create mock logger for testing.
    Returns:
        Mock logger instance
    """
    logger = Mock()
    logger.bind = Mock(return_value=logger)
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    return logger
@pytest.fixture
def extractor(mock_config: dict, mock_logger: Mock) -> WeatherExtractor:
    """Create extractor instance for testing.
    Args:
        mock_config: Mock configuration
        mock_logger: Mock logger
    Returns:
        WeatherExtractor instance
    """
    with patch.dict('os.environ', {'OPENWEATHER_API_KEY': 'test_api_key'}):
        return WeatherExtractor(config=mock_config, logger=mock_logger)
@pytest.fixture
def london_api_response() -> dict:
    """Mock API response for London (rainy weather).
    Returns:
        API response dictionary matching example 1
    """
    return {
        "coord": {"lon": -0.1257, "lat": 51.5085},
        "weather": [
            {"id": 500, "main": "Rain", "description": "light rain", "icon": "10d"}
        ],
        "base": "stations",
        "main": {
            "temp": 15.5,
            "feels_like": 14.2,
            "temp_min": 14.0,
            "temp_max": 17.0,
            "pressure": 1012,
            "humidity": 72
        },
        "visibility": 10000,
        "wind": {"speed": 4.1, "deg": 230},
        "clouds": {"all": 75},
        "dt": 1701360000,
        "sys": {
            "type": 2,
            "id": 2019646,
            "country": "GB",
            "sunrise": 1701331200,
            "sunset": 1701362400
        },
        "timezone": 0,
        "id": 2643743,
        "name": "London",
        "cod": 200
    }
@pytest.mark.asyncio
async def test_extract_london_rainy(
    extractor: WeatherExtractor,
    london_api_response: dict
) -> None:
    """Test extraction matches London rainy weather example.
    This test validates that the extractor correctly transforms
    the input from example 1 to the expected output.
    Args:
        extractor: WeatherExtractor instance
        london_api_response: Mock API response
    """
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=london_api_response)
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    extractor.session = mock_session
    result = await extractor.extract(city="London")
    assert result is not None
    assert result["city"] == "London"
    assert result["country"] == "GB"
    assert result["temperature_c"] == 15.5
    assert result["feels_like_c"] == 14.2
    assert result["humidity_percent"] == 72
    assert result["pressure_hpa"] == 1012
    assert result["wind_speed_ms"] == 4.1
    assert result["conditions"] == "light rain"
    assert result["cloudiness_percent"] == 75
    assert result["visibility_m"] == 10000
@pytest.mark.asyncio
async def test_extract_tokyo_clear(extractor: WeatherExtractor) -> None:
    """Test extraction matches Tokyo clear weather example.
    Args:
        extractor: WeatherExtractor instance
    """
    tokyo_response = {
        "coord": {"lon": 139.6917, "lat": 35.6895},
        "weather": [
            {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}
        ],
        "base": "stations",
        "main": {
            "temp": 18.2,
            "feels_like": 17.5,
            "temp_min": 16.0,
            "temp_max": 20.0,
            "pressure": 1015,
            "humidity": 55
        },
        "visibility": 10000,
        "wind": {"speed": 2.5, "deg": 180},
        "clouds": {"all": 0},
        "dt": 1701360000,
        "sys": {
            "type": 1,
            "id": 8074,
            "country": "JP",
            "sunrise": 1701295200,
            "sunset": 1701331200
        },
        "timezone": 32400,
        "id": 1850144,
        "name": "Tokyo",
        "cod": 200
    }
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=tokyo_response)
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    extractor.session = mock_session
    result = await extractor.extract(city="Tokyo")
    assert result is not None
    assert result["city"] == "Tokyo"
    assert result["country"] == "JP"
    assert result["temperature_c"] == 18.2
    assert result["feels_like_c"] == 17.5
    assert result["humidity_percent"] == 55
    assert result["pressure_hpa"] == 1015
    assert result["wind_speed_ms"] == 2.5
    assert result["conditions"] == "clear sky"
    assert result["cloudiness_percent"] == 0
    assert result["visibility_m"] == 10000
@pytest.mark.asyncio
async def test_extract_moscow_snow(extractor: WeatherExtractor) -> None:
    """Test extraction matches Moscow snowy weather example.
    Args:
        extractor: WeatherExtractor instance
    """
    moscow_response = {
        "coord": {"lon": 37.6156, "lat": 55.7522},
        "weather": [
            {"id": 601, "main": "Snow", "description": "snow", "icon": "13d"}
        ],
        "base": "stations",
        "main": {
            "temp": -8.0,
            "feels_like": -12.5,
            "temp_min": -10.0,
            "temp_max": -6.0,
            "pressure": 1020,
            "humidity": 85
        },
        "visibility": 5000,
        "wind": {"speed": 5.5, "deg": 320},
        "clouds": {"all": 90},
        "dt": 1701360000,
        "sys": {
            "type": 1,
            "id": 9029,
            "country": "RU",
            "sunrise": 1701323400,
            "sunset": 1701349800
        },
        "timezone": 10800,
        "id": 524901,
        "name": "Moscow",
        "cod": 200
    }
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=moscow_response)
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_response)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    extractor.session = mock_session
    result = await extractor.extract(city="Moscow")
    assert result is not None
    assert result["city"] == "Moscow"
    assert result["country"] == "RU"
    assert result["temperature_c"] == -8.0
    assert result["feels_like_c"] == -12.5
    assert result["humidity_percent"] == 85
    assert result["pressure_hpa"] == 1020
    assert result["wind_speed_ms"] == 5.5
    assert result["conditions"] == "snow"
    assert result["cloudiness_percent"] == 90
    assert result["visibility_m"] == 5000
@pytest.mark.asyncio
async def test_extract_dubai_hot(extractor: WeatherExtractor) -> None:
    """Test extraction matches Dubai hot weather example.
    Args:
        extractor: WeatherExtractor instance
    """
    dubai_response = {
        "coord": {"lon": 55.3047, "lat": 25.2582},
        "weather": [
            {"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}
        ],
        "base": "stations",
        "main": {
            "temp": 35.0,
            "feels_like": 38.5,
            "temp_min": 33.0,
            "temp_max": 37.0,
            "pressure": 1010,
            "humidity": 25
        },
        "visibility": 10000,
        "wind": {"speed": 3.5, "deg": 90},
        "clouds": {"all": 0},
        "dt": 1701360000,
        "sys": {
            "type": 1,
            "id": 7537,
            "country": "AE",
            "sunrise": 1701314400,
            "sunset": 1701350400
        },
        "timezone": 14400,
        "id": 292223,
        "name": "Dubai",
        "cod": 200
    }
    mock_response = AsyncMock()
    mock_response.status = 200
    mock