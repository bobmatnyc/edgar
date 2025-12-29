# Weather API Extractor - Code Generation Guide

This guide explains how to generate the Weather API data extractor using the Example-Driven Extraction Platform.

---

## Quick Start

### Prerequisites

1. **Python Environment**
   ```bash
   source venv/bin/activate  # Activate virtual environment
   ```

2. **API Key** (for AI generation)
   ```bash
   export OPENROUTER_API_KEY=your_key_here
   ```

### Generate Extractor

#### Option 1: Demo Script (Recommended)

```bash
# Generate with all defaults
python scripts/generate_weather_extractor.py

# Custom options
python scripts/generate_weather_extractor.py \
    --output-dir projects/weather_api/generated \
    --no-validate  # Skip validation (faster)
```

**Output**: Generated files in `projects/weather_api/generated/`

#### Option 2: Run Tests

```bash
# Run complete test suite
pytest tests/integration/test_weather_api_generation.py -v

# Run specific test stage
pytest tests/integration/test_weather_api_generation.py::TestEndToEndGeneration -v
```

**Output**: Test results + generated files

---

## Pipeline Stages

### 1. Example Parsing (No API Key)

```bash
pytest tests/integration/test_weather_api_generation.py::TestExampleParsing -v
```

**What it does**:
- Parses 7 weather examples from `project.yaml`
- Identifies transformation patterns
- Infers input/output schemas

**Duration**: <1 second

### 2. PM Mode Planning (Requires API Key)

```bash
pytest tests/integration/test_weather_api_generation.py::TestPMModePlanning -v
```

**What it does**:
- Sends patterns to Sonnet 4.5
- Creates implementation plan
- Defines classes, methods, dependencies

**Duration**: ~10-20 seconds

### 3. Coder Mode Generation (Requires API Key)

```bash
pytest tests/integration/test_weather_api_generation.py::TestCoderModeGeneration -v
```

**What it does**:
- Sends plan to Sonnet 4.5
- Generates Python code (extractor, models, tests)
- Returns structured code artifacts

**Duration**: ~30-60 seconds

### 4. Validation

```bash
pytest tests/integration/test_weather_api_generation.py::TestConstraintValidation -v
```

**What it does**:
- Validates syntax (AST parsing)
- Checks type hints
- Verifies interface implementation
- Scores code quality

**Duration**: <1 second

### 5. Complete Pipeline

```bash
pytest tests/integration/test_weather_api_generation.py::TestEndToEndGeneration -v
```

**What it does**:
- Runs all stages sequentially
- Writes files to disk
- Reports comprehensive metrics

**Duration**: ~1-2 minutes total

---

## Generated Files

After successful generation:

```
projects/weather_api/generated/
├── extractor.py          # WeatherExtractor class
├── models.py             # Pydantic data models
├── test_extractor.py     # Pytest test suite
└── __init__.py           # Package initialization
```

### Verify Generated Code

```bash
# 1. Check syntax
python -m py_compile projects/weather_api/generated/*.py

# 2. Run generated tests
pytest projects/weather_api/generated/test_extractor.py -v

# 3. Try the extractor
python -c "
from projects.weather_api.generated.extractor import WeatherExtractor
from projects.weather_api.generated.models import WeatherData

extractor = WeatherExtractor()
print('Extractor loaded successfully!')
"
```

---

## Configuration

### Project Configuration

**File**: `projects/weather_api/project.yaml`

**Key Sections**:
- `project`: Metadata (name, version, tags)
- `data_sources`: OpenWeatherMap API config
- `examples`: 7 diverse weather examples
- `validation`: Data quality rules
- `output`: Report formats

### Modify Examples

Add/modify examples in `project.yaml`:

```yaml
examples:
  - input:
      coord: {lon: -122.4194, lat: 37.7749}
      weather: [{main: "Fog", description: "fog"}]
      main: {temp: 13.5, humidity: 89}
      # ... full API response
    output:
      city: San Francisco
      temperature_c: 13.5
      conditions: fog
      humidity_percent: 89
    description: "Foggy coastal weather"
```

Re-run generation to incorporate new patterns.

---

## Troubleshooting

### Import Errors

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -e ".[dev]"
```

### API Key Issues

```bash
# Check API key is set
echo $OPENROUTER_API_KEY

# Set if missing
export OPENROUTER_API_KEY=your_key_here

# Or use .env.local
echo "OPENROUTER_API_KEY=your_key" >> .env.local
```

### Generation Fails

```bash
# Run with verbose logging
python scripts/generate_weather_extractor.py --verbose

# Check logs
tail -f logs/generation.log
```

### Test Failures

```bash
# Run with detailed output
pytest tests/integration/test_weather_api_generation.py -vv -s

# Run specific failing test
pytest tests/integration/test_weather_api_generation.py::TestClass::test_name -vv
```

---

## Advanced Usage

### Custom Output Directory

```bash
python scripts/generate_weather_extractor.py \
    --output-dir /custom/path/output
```

### Skip Validation (Faster)

```bash
python scripts/generate_weather_extractor.py --no-validate
```

### Dry Run (No File Writing)

```bash
python scripts/generate_weather_extractor.py --no-write
```

### Custom API Key

```bash
python scripts/generate_weather_extractor.py \
    --api-key sk-or-v1-...
```

---

## Metrics and Reporting

### View Generation Metrics

After generation, check:

```bash
# View generation report
cat projects/weather_api/GENERATION_REPORT.md

# Key metrics
grep "Total Duration" projects/weather_api/GENERATION_REPORT.md
grep "Total Lines" projects/weather_api/GENERATION_REPORT.md
grep "Quality Score" projects/weather_api/GENERATION_REPORT.md
```

### Success Criteria

✅ Generation completes in <2 minutes
✅ All constraint checks pass
✅ Generated code has 0 syntax errors
✅ Generated tests cover all 7 examples
✅ No manual code editing required

---

## Next Steps After Generation

1. **Review Generated Code**
   - Read through `extractor.py`
   - Understand transformation logic
   - Check error handling

2. **Run Generated Tests**
   ```bash
   pytest projects/weather_api/generated/test_extractor.py -v
   ```

3. **Integrate with Project**
   ```python
   from weather_api.generated import WeatherExtractor

   extractor = WeatherExtractor()
   data = extractor.extract(api_response)
   ```

4. **Customize as Needed**
   - Add custom validation rules
   - Enhance error messages
   - Add logging/monitoring

5. **Deploy to Production**
   - Package as wheel
   - Deploy to environment
   - Monitor extraction performance

---

## Resources

- **Implementation Summary**: `WEATHER_API_GENERATION_IMPLEMENTATION.md`
- **Test Suite**: `tests/integration/test_weather_api_generation.py`
- **Demo Script**: `scripts/generate_weather_extractor.py`
- **Project Config**: `projects/weather_api/project.yaml`
- **Generation Report**: `projects/weather_api/GENERATION_REPORT.md`

---

**Questions?** Check the main project README or implementation summary.
