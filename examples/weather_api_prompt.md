## Example Parser Output for Sonnet 4.5

**Project**: weather_api
**Task**: Generate Python transformation function based on identified patterns

**Analysis Summary**:
- Examples Analyzed: 3
- Patterns Identified: 4
- High Confidence Patterns: 4 (100%)
- Input Fields: 13
- Output Fields: 4


## Input Schema

**Input Data Structure**:

```python
{
  "name": str,
  # Nested fields:
  # "coord.lon": float
  # "coord.lat": float
  # "weather[0].id": List[int]
  # "weather[0].main": List[str]
  # "weather[0].description": List[str]
  # ... and 7 more nested fields
}
```


**Field Details**:
- `name`: str
  - Examples: New York, Tokyo

## Output Schema

**Output Data Structure**:

```python
{
  "city": str,
  "temperature_c": float,
  "humidity_percent": int,
  "conditions": str,
}
```


**Field Details**:
- `city`: str
  - Examples: New York, Tokyo
- `temperature_c`: float
  - Examples: 18.0, 22.3
- `humidity_percent`: int
  - Examples: 65, 82
- `conditions`: str
  - Examples: light intensity drizzle, light rain

## Identified Patterns

**Pattern Summary**:

- **Field Mapping**: 4 patterns (avg confidence: 100%)

## Pattern 1: city

**Type**: Field Mapping
**Confidence**: 100% (high)
**Source**: `city`
**Target**: `city`
**Transformation**: Direct copy

**Type Conversion**: str → str
**Type Safety**: ✓ Safe conversion

**Examples**:
- Input: `London` → Output: `London`
- Input: `Tokyo` → Output: `Tokyo`
- Input: `New York` → Output: `New York`

**Implementation Guidance**:
- Use direct dictionary access
- Handle missing keys with `.get()` method
- Extract: `input_data['city']`

## Pattern 2: temperature_c

**Type**: Field Mapping
**Confidence**: 100% (high)
**Source**: `temperature_c`
**Target**: `temperature_c`
**Transformation**: Direct copy

**Type Conversion**: float → float
**Type Safety**: ✓ Safe conversion

**Examples**:
- Input: `15.5` → Output: `15.5`
- Input: `22.3` → Output: `22.3`
- Input: `18.0` → Output: `18.0`

**Implementation Guidance**:
- Use direct dictionary access
- Handle missing keys with `.get()` method
- Extract: `input_data['temperature_c']`

## Pattern 3: humidity_percent

**Type**: Field Mapping
**Confidence**: 100% (high)
**Source**: `humidity_percent`
**Target**: `humidity_percent`
**Transformation**: Direct copy

**Type Conversion**: int → int
**Type Safety**: ✓ Safe conversion

**Examples**:
- Input: `82` → Output: `82`
- Input: `65` → Output: `65`
- Input: `75` → Output: `75`

**Implementation Guidance**:
- Use direct dictionary access
- Handle missing keys with `.get()` method
- Extract: `input_data['humidity_percent']`

## Pattern 4: conditions

**Type**: Field Mapping
**Confidence**: 100% (high)
**Source**: `conditions`
**Target**: `conditions`
**Transformation**: Direct copy

**Type Conversion**: str → str
**Type Safety**: ✓ Safe conversion

**Examples**:
- Input: `light intensity drizzle` → Output: `light intensity drizzle`
- Input: `clear sky` → Output: `clear sky`
- Input: `light rain` → Output: `light rain`

**Implementation Guidance**:
- Use direct dictionary access
- Handle missing keys with `.get()` method
- Extract: `input_data['conditions']`

## Implementation Requirements

**Function Signature**:
```python
def transform(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform input data to output format."""
    # Your implementation here
    pass
```

**Requirements**:
- Use dependency injection for services
- Handle nested dictionaries and arrays
- Preserve types (float, int, str, bool)
- Add logging for traceability
- Include type hints
- Handle missing fields gracefully (use `.get()` with defaults)
- Validate output structure matches schema
- Add docstring with transformation description

**Error Handling**:
- Log errors but don't crash on missing fields
- Use Optional types for nullable fields
- Provide sensible defaults where appropriate
- Validate critical fields are present

**Testing**:
- Function must pass all provided examples
- Verify output matches expected structure for all 3 examples
- Test edge cases (null values, empty arrays, missing fields)