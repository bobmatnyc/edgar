# Weather API Extractor

**MVP Proof-of-Concept for Example-Driven Extraction Platform**

Extract current weather data from OpenWeatherMap API using example-driven transformation. This project demonstrates the platform's capability to generate data extractors from input/output examples without manual coding.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Example Diversity](#example-diversity)
- [Generated Code](#generated-code)
- [Usage](#usage)
- [Output](#output)
- [Configuration](#configuration)
- [Validation](#validation)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

---

## 🎯 Overview

### What This Does

This project extracts current weather data from the **OpenWeatherMap API** and transforms it into a clean, structured format suitable for analysis and reporting.

**Key Capabilities:**
- ✅ Extract weather data for any city worldwide
- ✅ Transform nested JSON into flat, analysis-ready format
- ✅ Validate data quality with comprehensive rules
- ✅ Output to multiple formats (CSV, JSON)
- ✅ Cache responses to respect API rate limits
- ✅ Handle diverse weather conditions (rain, snow, heat, cold, etc.)

### How It Works

1. **Example-Based Learning**: Provide input/output example pairs
2. **AI Code Generation**: Sonnet 4.5 analyzes examples and generates extractor
3. **Automatic Validation**: Generated code includes data quality checks
4. **Production Ready**: Includes error handling, caching, rate limiting

### Transformation Patterns Demonstrated

This project showcases all key transformation patterns:

| Pattern | Example | Input Path | Output Field |
|---------|---------|------------|--------------|
| **Nested Field Access** | `main.temp` → `temperature_c` | `input.main.temp` | `temperature_c` |
| **Array Element Extraction** | `weather[0].description` → `conditions` | `input.weather[0].description` | `conditions` |
| **Field Renaming** | `name` → `city` | `input.name` | `city` |
| **Type Preservation** | Float, Int, String | Various | Validated types |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- OpenWeatherMap API key (free tier available)

### Setup Steps

#### 1. Get API Key

Sign up for a free API key at: https://openweathermap.org/api

The free tier provides:
- 60 calls/minute
- 1,000,000 calls/month
- Current weather data

#### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API key
# OPENWEATHER_API_KEY=your_api_key_here
```

#### 3. Generate Extractor

```bash
# Using platform CLI (when implemented)
platform generate weather_api

# This will create:
# - generated/weather_extractor.py
# - generated/weather_models.py
# - generated/test_weather_extractor.py
```

#### 4. Run Extractor

```bash
# Extract weather for specific cities
python generated/weather_extractor.py --cities "London,Tokyo,Moscow"

# Extract for all example cities
python generated/weather_extractor.py --use-examples

# View output
cat output/weather_data.csv
```

---

## 🌍 Example Diversity

This project includes **7 diverse weather examples** covering different climatic conditions:

### 1. London, UK 🌧️
**Condition:** Rainy, temperate
**Demonstrates:** Nested field extraction, array handling
- Temperature: 15.5°C (feels like 14.2°C)
- Humidity: 72%
- Conditions: Light rain
- Use Case: Baseline temperate climate with precipitation

### 2. Tokyo, Japan ☀️
**Condition:** Clear sky, moderate
**Demonstrates:** Clean baseline case
- Temperature: 18.2°C (feels like 17.5°C)
- Humidity: 55%
- Conditions: Clear sky
- Use Case: Ideal weather conditions reference

### 3. Moscow, Russia ❄️
**Condition:** Snowy, cold
**Demonstrates:** Negative temperatures, reduced visibility
- Temperature: -8.0°C (feels like -12.5°C)
- Humidity: 85%
- Conditions: Snow
- Visibility: 5,000m (reduced)
- Use Case: Extreme cold, winter conditions

### 4. Dubai, UAE 🏜️
**Condition:** Hot, dry
**Demonstrates:** High temperatures, low humidity
- Temperature: 35.0°C (feels like 38.5°C)
- Humidity: 25%
- Conditions: Clear sky
- Use Case: Desert climate, extreme heat

### 5. Oslo, Norway 🌬️
**Condition:** Cold, windy
**Demonstrates:** Wind chill effect (feels_like < actual)
- Temperature: 2.0°C (feels like -3.0°C)
- Humidity: 78%
- Wind: 7.5 m/s
- Conditions: Broken clouds
- Use Case: Wind chill demonstration

### 6. Singapore 🌴
**Condition:** Humid tropical
**Demonstrates:** High humidity, heat index effect
- Temperature: 28.0°C (feels like 32.5°C)
- Humidity: 88%
- Conditions: Moderate rain
- Use Case: Tropical climate, humidity effects

### 7. New York, USA 🌫️
**Condition:** Misty
**Demonstrates:** Reduced visibility edge case
- Temperature: 12.0°C (feels like 10.5°C)
- Humidity: 68%
- Conditions: Mist
- Visibility: 6,000m
- Use Case: Variable urban weather

### Coverage Analysis

| Weather Aspect | Coverage |
|----------------|----------|
| **Temperature Range** | -8°C to 35°C (extreme cold to extreme heat) |
| **Humidity Range** | 25% to 88% (arid to tropical) |
| **Conditions** | Clear, rain, snow, clouds, mist |
| **Visibility** | 5,000m to 10,000m |
| **Wind Speed** | 1.5 m/s to 7.5 m/s |

---

## 🤖 Generated Code

When you run `platform generate weather_api`, the following files are created in the `generated/` directory:

### `weather_extractor.py`
Main extraction logic with:
- API client with authentication
- Response caching (30-minute TTL)
- Rate limiting (0.5 requests/second)
- Error handling and retries
- Data transformation based on examples
- Multi-city batch processing

### `weather_models.py`
Pydantic data models for:
- Input validation (API response structure)
- Output validation (transformed data structure)
- Field constraints (temperature ranges, humidity bounds)
- Type safety (float, int, str)

### `test_weather_extractor.py`
Comprehensive test suite:
- Unit tests for each transformation pattern
- Integration tests against all 7 examples
- Validation tests for constraints
- Edge case handling (negative temps, high humidity)
- Mock API responses for offline testing

---

## 💻 Usage

### Command-Line Interface

```bash
# Basic usage - extract for specific cities
python generated/weather_extractor.py --cities "London,Paris,Berlin"

# Use cities from examples
python generated/weather_extractor.py --use-examples

# Specify output format
python generated/weather_extractor.py \
  --cities "Tokyo,Seoul" \
  --format json \
  --output custom_output.json

# Enable debug logging
python generated/weather_extractor.py \
  --cities "Moscow" \
  --log-level DEBUG

# Disable caching (always fetch fresh data)
python generated/weather_extractor.py \
  --cities "Singapore" \
  --no-cache
```

### Python API

```python
from generated.weather_extractor import WeatherExtractor
from generated.weather_models import WeatherData

# Initialize extractor
extractor = WeatherExtractor(api_key="your_api_key_here")

# Extract single city
data: WeatherData = extractor.extract_city("London")
print(f"{data.city}: {data.temperature_c}°C, {data.conditions}")

# Extract multiple cities
cities = ["London", "Tokyo", "Moscow"]
results = extractor.extract_batch(cities)

# Access data
for weather in results:
    print(f"{weather.city}: {weather.temperature_c}°C")

# Save to file
extractor.save_csv(results, "output/weather.csv")
extractor.save_json(results, "output/weather.json")
```

---

## 📊 Output

### CSV Format (`output/weather_data.csv`)

```csv
city,country,temperature_c,feels_like_c,humidity_percent,pressure_hpa,wind_speed_ms,conditions,cloudiness_percent,visibility_m
London,GB,15.5,14.2,72,1012,4.1,light rain,75,10000
Tokyo,JP,18.2,17.5,55,1015,2.5,clear sky,0,10000
Moscow,RU,-8.0,-12.5,85,1020,5.5,snow,90,5000
```

**Use Cases:**
- Excel/Google Sheets import
- Data analysis with pandas
- Database bulk import
- Tableau/Power BI visualization

### JSON Format (`output/weather_data.json`)

```json
[
  {
    "city": "London",
    "country": "GB",
    "temperature_c": 15.5,
    "feels_like_c": 14.2,
    "humidity_percent": 72,
    "pressure_hpa": 1012,
    "wind_speed_ms": 4.1,
    "conditions": "light rain",
    "cloudiness_percent": 75,
    "visibility_m": 10000
  }
]
```

**Use Cases:**
- API integration
- NoSQL database import
- JavaScript/web applications
- Configuration files

### Output Fields

| Field | Type | Description | Range/Constraints |
|-------|------|-------------|-------------------|
| `city` | string | City name | Required |
| `country` | string | Country code (ISO 3166) | 2-character code |
| `temperature_c` | float | Temperature in Celsius | -60.0 to 60.0 |
| `feels_like_c` | float | Perceived temperature | -60.0 to 60.0 |
| `humidity_percent` | int | Relative humidity | 0 to 100 |
| `pressure_hpa` | int | Atmospheric pressure | 870 to 1085 |
| `wind_speed_ms` | float | Wind speed (m/s) | 0.0 to 113.0 |
| `conditions` | string | Weather description | Required |
| `cloudiness_percent` | int | Cloud cover | 0 to 100 |
| `visibility_m` | int | Visibility distance (meters) | 0 to 100000 |

---

## ⚙️ Configuration

### project.yaml Structure

The `project.yaml` file contains all configuration:

```yaml
project:
  name: weather_api_extractor
  description: Extract weather data
  version: 1.0.0

data_sources:
  - type: api
    name: openweathermap
    endpoint: https://api.openweathermap.org/data/2.5/weather
    auth:
      type: api_key
      key: ${OPENWEATHER_API_KEY}
    cache:
      enabled: true
      ttl: 1800  # 30 minutes
    rate_limit:
      requests_per_second: 0.5

examples: [...]  # 7 example pairs

validation: [...]  # Data quality rules

output:
  formats:
    - type: csv
      path: output/weather_data.csv
    - type: json
      path: output/weather_data.json

runtime:
  log_level: INFO
  error_strategy: continue
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENWEATHER_API_KEY` | ✅ Yes | - | OpenWeatherMap API key |
| `WEATHER_API_BASE_URL` | ❌ No | `https://api.openweathermap.org/data/2.5` | API base URL |
| `WEATHER_API_UNITS` | ❌ No | `metric` | Units (metric/imperial) |
| `WEATHER_API_TIMEOUT` | ❌ No | `10` | Request timeout (seconds) |
| `WEATHER_CACHE_DIR` | ❌ No | `data/cache/weather` | Cache directory |
| `WEATHER_OUTPUT_DIR` | ❌ No | `output` | Output directory |

---

## ✅ Validation

### Automatic Validation

Generated code includes comprehensive validation:

#### 1. Required Fields
All outputs must contain:
- `city`, `country`, `temperature_c`, `humidity_percent`, `conditions`

#### 2. Type Validation
- `temperature_c`: float
- `humidity_percent`: int (0-100)
- `pressure_hpa`: int (870-1085)
- `city`: non-empty string

#### 3. Value Constraints

| Field | Constraint | Rationale |
|-------|------------|-----------|
| `temperature_c` | -60.0 to 60.0 | Extreme weather records (Oymyakon to Death Valley) |
| `humidity_percent` | 0 to 100 | Physical limit |
| `pressure_hpa` | 870 to 1085 | Historical weather records (Typhoon Tip to Siberian High) |
| `wind_speed_ms` | 0.0 to 113.0 | Category 5 hurricane limit |
| `visibility_m` | 0 to 100000 | Maximum useful visibility |

#### 4. Data Quality Checks
- ✅ All required fields present
- ✅ Values within valid ranges
- ✅ Correct data types
- ✅ No null/undefined values
- ✅ API response structure matches examples

---

## 🔧 Troubleshooting

### Common Issues

#### API Key Not Working
```
Error: 401 Unauthorized
```
**Solution:**
1. Verify API key is correct in `.env`
2. Check that environment variable syntax is `${OPENWEATHER_API_KEY}`
3. Ensure API key is activated (may take a few hours after signup)

#### Rate Limit Exceeded
```
Error: 429 Too Many Requests
```
**Solution:**
1. Check `rate_limit` configuration in `project.yaml`
2. Increase cache TTL to reduce API calls
3. Upgrade to paid tier for higher limits

#### City Not Found
```
Error: 404 Not Found
```
**Solution:**
1. Verify city name spelling
2. Try adding country code: `"London,GB"`
3. Check OpenWeatherMap city list: https://openweathermap.org/find

#### Invalid Temperature Range
```
ValidationError: temperature_c must be between -60.0 and 60.0
```
**Solution:**
1. This indicates data quality issue or API error
2. Check raw API response in logs (DEBUG level)
3. May indicate API returned corrupt data

#### Cache Issues
```
Error: Cannot write to cache directory
```
**Solution:**
1. Create cache directory: `mkdir -p data/cache/weather`
2. Check write permissions
3. Disable cache: `--no-cache` flag

---

## 📚 API Reference

### OpenWeatherMap API

**Endpoint:** `https://api.openweathermap.org/data/2.5/weather`

**Parameters:**
- `q`: City name (e.g., `London` or `London,GB`)
- `appid`: API key (authentication)
- `units`: `metric` (Celsius) or `imperial` (Fahrenheit)

**Rate Limits (Free Tier):**
- 60 calls/minute
- 1,000,000 calls/month

**Response Structure:**
```json
{
  "coord": {"lon": -0.1257, "lat": 51.5085},
  "weather": [{"id": 500, "main": "Rain", "description": "light rain"}],
  "main": {"temp": 15.5, "humidity": 72, "pressure": 1012},
  "wind": {"speed": 4.1, "deg": 230},
  "clouds": {"all": 75},
  "visibility": 10000,
  "name": "London",
  "cod": 200
}
```

**Documentation:** https://openweathermap.org/current

---

## 🎓 Learning Resources

### Understanding the Examples

Each example demonstrates specific transformation patterns:

1. **london.json**: Baseline with nested fields + array access
2. **tokyo.json**: Simple clear weather (edge case: minimal data)
3. **moscow.json**: Negative temperatures + reduced visibility
4. **dubai.json**: Extreme heat + low humidity
5. **oslo.json**: Wind chill demonstration
6. **singapore.json**: Heat index (high humidity effect)
7. **new_york.json**: Visibility edge cases

### Extending the Project

To add new cities or customize:

1. **Add Examples**: Create new JSON files in `examples/`
2. **Update Validation**: Modify constraints in `project.yaml`
3. **Regenerate Code**: Run `platform generate weather_api`
4. **Test**: Run test suite against new examples

---

## 📝 Success Criteria

This project is considered successful when:

- ✅ Valid `project.yaml` (passes schema validation)
- ✅ 7 diverse example pairs covering all weather conditions
- ✅ All example files present and properly formatted
- ✅ Complete documentation (this README)
- ✅ Environment template (`.env.example`)
- ✅ Validation script functional
- ✅ Integration test passing
- ✅ Ready for code generation

---

## 📄 License

This project is part of the Example-Driven Extraction Platform MVP.

---

## 🤝 Contributing

This is a proof-of-concept template. To contribute:

1. Test with your own OpenWeatherMap API key
2. Suggest additional weather examples
3. Report issues with transformation patterns
4. Improve documentation clarity

---

## 📞 Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section
- Review OpenWeatherMap API docs
- Examine example files for transformation patterns

---

**Built with ❤️ as part of the Example-Driven Extraction Platform MVP**
