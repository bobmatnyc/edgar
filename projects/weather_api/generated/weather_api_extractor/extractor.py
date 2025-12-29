"""
WeatherExtractor - OpenWeatherMap API Data Extractor
Extracts current weather data from OpenWeatherMap API and transforms it to a
standardized output format. Implements async HTTP requests with retry logic,
rate limiting, and caching for efficient API usage.
"""
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import time
import os
from collections import OrderedDict
import aiohttp
import structlog
from dependency_injector.wiring import inject, Provide
from edgar_analyzer.config.container import Container
logger = structlog.get_logger(__name__)
class WeatherExtractor:
    """Extract and transform current weather data from OpenWeatherMap API.
    This implementation follows the design specified by the Planning Manager.
    It provides async extraction with caching, rate limiting, and robust error
    handling.
    Design Decisions:
    - Uses aiohttp for async HTTP requests with connection pooling
    - Implements token bucket rate limiting (0.5 req/s, burst 3)
    - In-memory LRU cache with 30-minute TTL
    - Exponential backoff retry strategy (1s, 2s, 4s)
    - Graceful degradation on validation errors
    Example:
        >>> extractor = WeatherExtractor(config=config, logger=logger)
        >>> result = await extractor.extract(city="London")
        >>> print(result["temperature_c"])
        15.5
    """
    @inject
    def __init__(
        self,
        config: Dict[str, Any],
        logger: structlog.BoundLogger = Provide[Container.logger]
    ) -> None:
        """Initialize WeatherExtractor with configuration and dependencies.
        Args:
            config: Configuration dictionary containing data source settings
            logger: Structured logger instance for logging operations
        Raises:
            KeyError: If required configuration keys are missing
            ValueError: If API key is not found in environment
        """
        self.config = config
        self.logger = logger
        api_key_env = config['data_sources'][0]['auth']['key']
        self.api_key = os.getenv(api_key_env)
        if not self.api_key:
            raise ValueError(f"API key not found in environment: {api_key_env}")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.timeout = 30
        self.max_retries = 3
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: OrderedDict[str, Tuple[float, Dict[str, Any]]] = OrderedDict()
        self.cache_ttl = 1800  # 30 minutes
        self.cache_max_size = 100
        self.rate_limit_tokens = 3.0  # Burst size
        self.rate_limit_max_tokens = 3.0
        self.rate_limit_refill_rate = 0.5  # tokens per second
        self.last_request_time = time.time()
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session.
        Returns:
            Active aiohttp ClientSession instance
        """
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    async def extract(self, **kwargs) -> Optional[Dict[str, Any]]:
        """Extract and transform weather data for a given city.
        Main extraction method implementing IDataExtractor interface.
        Orchestrates the fetch, transform, and validate pipeline.
        Args:
            **kwargs: Must contain 'city' key with city name string
        Returns:
            Transformed weather data dictionary matching output schema,
            or None if extraction fails
        Example:
            >>> result = await extractor.extract(city="Tokyo")
            >>> print(result["conditions"])
            'clear sky'
        """
        city = kwargs.get('city')
        if not city:
            self.logger.error("extract_missing_city", error="City parameter required")
            return None
        bound_logger = self.logger.bind(city=city, operation="extract")
        try:
            bound_logger.info("extract_started")
            raw_data = await self._fetch_weather_data(city)
            transformed_data = self._transform_data(raw_data)
            if not self._validate_output(transformed_data):
                bound_logger.error("extract_validation_failed")
                return None
            bound_logger.info("extract_completed", fields=len(transformed_data))
            return transformed_data
        except Exception as e:
            bound_logger.error("extract_failed", error=str(e), exc_info=True)
            return None
    async def _fetch_weather_data(self, city: str) -> Dict[str, Any]:
        """Fetch raw weather data from API with caching and retry logic.
        Args:
            city: City name to fetch weather for
        Returns:
            Raw API response as dictionary
        Raises:
            aiohttp.ClientError: On persistent network failures
            asyncio.TimeoutError: On request timeout
        """
        bound_logger = self.logger.bind(city=city, operation="fetch")
        cached_data = self._cache_get(city)
        if cached_data is not None:
            bound_logger.info("cache_hit")
            return cached_data
        await self._check_rate_limit()
        session = await self._get_session()
        retry_delays = [1, 2, 4]
        for attempt in range(self.max_retries):
            try:
                params = {
                    'q': city,
                    'appid': self.api_key,
                    'units': 'metric'
                }
                async with session.get(
                    self.base_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 429:
                        bound_logger.warning("rate_limited_by_api", retry_after=60)
                        await asyncio.sleep(60)
                        continue
                    if response.status >= 400:
                        error_text = await response.text()
                        bound_logger.error(
                            "api_error",
                            status=response.status,
                            error=error_text
                        )
                        raise aiohttp.ClientError(
                            f"API error {response.status}: {error_text}"
                        )
                    data = await response.json()
                    self._cache_set(city, data)
                    bound_logger.info("fetch_success", status=response.status)
                    return data
            except asyncio.TimeoutError:
                bound_logger.warning(
                    "fetch_timeout",
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(retry_delays[attempt])
                else:
                    raise
            except aiohttp.ClientError as e:
                bound_logger.warning(
                    "fetch_error",
                    attempt=attempt + 1,
                    error=str(e)
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(retry_delays[attempt])
                else:
                    raise
        raise aiohttp.ClientError("Max retries exceeded")
    def _transform_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw API response to output schema using pattern mappings.
        Args:
            raw_data: Raw API response dictionary
        Returns:
            Transformed data matching output schema
        Example:
            >>> raw = {"name": "London", "main": {"temp": 15.5}}
            >>> result = extractor._transform_data(raw)
            >>> result["city"]
            'London'
        """
        transformed = {
            'city': self._get_nested_value(raw_data, 'name'),
            'country': self._get_nested_value(raw_data, 'sys.country'),
            'temperature_c': self._get_nested_value(raw_data, 'main.temp'),
            'feels_like_c': self._get_nested_value(raw_data, 'main.feels_like'),
            'humidity_percent': self._get_nested_value(raw_data, 'main.humidity'),
            'pressure_hpa': self._get_nested_value(raw_data, 'main.pressure'),
            'wind_speed_ms': self._get_nested_value(raw_data, 'wind.speed'),
            'conditions': self._get_nested_value(raw_data, 'weather[0].description'),
            'cloudiness_percent': self._get_nested_value(raw_data, 'clouds.all'),
            'visibility_m': self._get_nested_value(raw_data, 'visibility')
        }
        for key, value in transformed.items():
            if value is None:
                self.logger.warning("missing_field", field=key)
        return transformed
    def _validate_output(self, data: Dict[str, Any]) -> bool:
        """Validate transformed data against schema and constraints.
        Args:
            data: Transformed data dictionary to validate
        Returns:
            True if validation passes, False otherwise
        """
        bound_logger = self.logger.bind(operation="validate")
        required_fields = [
            'city', 'country', 'temperature_c', 'feels_like_c',
            'humidity_percent', 'pressure_hpa', 'wind_speed_ms',
            'conditions', 'cloudiness_percent', 'visibility_m'
        ]
        for field in required_fields:
            if field not in data or data[field] is None:
                bound_logger.error("validation_missing_field", field=field)
                return False
        type_checks = {
            'city': str,
            'country': str,
            'temperature_c': (int, float),
            'feels_like_c': (int, float),
            'humidity_percent': int,
            'pressure_hpa': int,
            'wind_speed_ms': (int, float),
            'conditions': str,
            'cloudiness_percent': int,
            'visibility_m': int
        }
        for field, expected_type in type_checks.items():
            if not isinstance(data[field], expected_type):
                bound_logger.error(
                    "validation_type_error",
                    field=field,
                    expected=str(expected_type),
                    actual=type(data[field]).__name__
                )
                return False
        constraints = {
            'temperature_c': (-60, 60),
            'feels_like_c': (-60, 60),
            'humidity_percent': (0, 100),
            'pressure_hpa': (870, 1085),
            'wind_speed_ms': (0, 113),
            'cloudiness_percent': (0, 100),
            'visibility_m': (0, 100000)
        }
        for field, (min_val, max_val) in constraints.items():
            value = data[field]
            if not (min_val <= value <= max_val):
                bound_logger.error(
                    "validation_constraint_violation",
                    field=field,
                    value=value,
                    min=min_val,
                    max=max_val
                )
                return False
        return True
    def _get_nested_value(
        self,
        data: Dict[str, Any],
        path: str,
        default: Any = None
    ) -> Any:
        """Safely extract nested dictionary values with dot notation.
        Args:
            data: Dictionary to extract from
            path: Dot-notation path (e.g., 'main.temp', 'weather[0].description')
            default: Default value if path not found
        Returns:
            Extracted value or default if path doesn't exist
        Example:
            >>> data = {"main": {"temp": 15.5}}
            >>> extractor._get_nested_value(data, "main.temp")
            15.5
        """
        try:
            value = data
            parts = path.replace('[', '.').replace(']', '').split('.')
            for part in parts:
                if part.isdigit():
                    value = value[int(part)]
                else:
                    value = value[part]
            return value
        except (KeyError, IndexError, TypeError):
            return default
    async def _check_rate_limit(self) -> None:
        """Enforce rate limiting before API calls using token bucket algorithm.
        Implements 0.5 requests/second with burst size of 3.
        Sleeps if rate limit would be exceeded.
        """
        current_time = time.time()
        time_passed = current_time - self.last_request_time
        self.rate_limit_tokens = min(
            self.rate_limit_max_tokens,
            self.rate_limit_tokens + time_passed * self.rate_limit_refill_rate
        )
        if self.rate_limit_tokens < 1.0:
            sleep_time = (1.0 - self.rate_limit_tokens) / self.rate_limit_refill_rate
            self.logger.info("rate_limit_sleep", sleep_seconds=sleep_time)
            await asyncio.sleep(sleep_time)
            self.rate_limit_tokens = 1.0
        self.rate_limit_tokens -= 1.0
        self.last_request_time = time.time()
    def _cache_get(self, city: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached weather data if not expired.
        Args:
            city: City name to retrieve from cache
        Returns:
            Cached data if valid, None if expired or not found
        """
        if city not in self.cache:
            return None
        timestamp, data = self.cache[city]
        age = time.time() - timestamp
        if age < self.cache_ttl:
            self.cache.move_to_end(city)
            return data
        else:
            del self.cache[city]
            return None
    def _cache_set(self, city: str, data: Dict[str, Any]) -> None:
        """Store weather data in cache with timestamp.
        Args:
            city: City name as cache key
            data: Weather data to cache
        """
        if city in self.cache:
            del self.cache[city]
        self.cache[city] = (time.time(), data)
        if len(self.cache) > self.cache_max_size:
            self.cache.popitem(last=False)
        self.logger.info("cache_set", city=city, cache_size=len(self.cache))
    async def close(self) -> None:
        """Close aiohttp session and cleanup resources."""
        if self.session and not self.session.closed:
            await self.session.close()