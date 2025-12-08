# Meta-Extractor Troubleshooting Guide

This guide covers common issues when creating and using extractors with the Meta-Extractor system.

## Table of Contents

- [Creation Issues](#creation-issues)
- [Low Confidence Scores](#low-confidence-scores)
- [Validation Failures](#validation-failures)
- [Runtime Errors](#runtime-errors)
- [Registry Issues](#registry-issues)
- [Performance Problems](#performance-problems)
- [Debugging Tips](#debugging-tips)
- [Best Practices](#best-practices)

---

## Creation Issues

### Issue: "No examples found in directory"

**Symptom**:
```
❌ Creation failed: error
   Error: No valid examples found in examples/my_domain/
   Stage: loading_examples
```

**Causes**:
1. Directory is empty
2. No `*.json` files present
3. JSON files don't contain `input`/`output` keys

**Solutions**:

✅ **Verify directory contents**:
```bash
ls -la examples/my_domain/
# Should show .json files
```

✅ **Check JSON structure**:
```bash
cat examples/my_domain/example1.json
# Should have: {"input": {...}, "output": {...}}
```

✅ **Create valid example**:
```json
{
  "input": {
    "html": "<html>...</html>",
    "url": "https://example.com"
  },
  "output": {
    "records": [],
    "count": 0
  }
}
```

---

### Issue: "Invalid JSON in example file"

**Symptom**:
```
❌ Creation failed: error
   Error: Invalid JSON in examples/my_domain/example1.json
   Stage: loading_examples
```

**Causes**:
- Syntax errors in JSON (trailing commas, missing quotes, etc.)
- File encoding issues
- Comments in JSON (not allowed in standard JSON)

**Solutions**:

✅ **Validate JSON syntax**:
```bash
# Use jq to validate
cat examples/my_domain/example1.json | jq .

# Or use Python
python -m json.tool examples/my_domain/example1.json
```

✅ **Common JSON mistakes**:
```json
// ❌ BAD - trailing comma
{
  "input": {},
  "output": {},  // <-- Remove this comma
}

// ❌ BAD - comments not allowed
{
  // This is a comment
  "input": {}
}

// ✅ GOOD
{
  "input": {},
  "output": {}
}
```

✅ **Fix encoding**:
```bash
# Convert to UTF-8
iconv -f ISO-8859-1 -t UTF-8 example1.json > example1_fixed.json
```

---

### Issue: "Inconsistent example structures"

**Symptom**:
```
❌ Creation failed: validation_failed
   Error: Examples have inconsistent structures
   Stage: analyzing_patterns
```

**Causes**:
- Different input schemas across examples
- Different output schemas across examples
- Missing keys in some examples

**Solutions**:

✅ **Ensure consistent input structure**:
```json
// ❌ BAD - Inconsistent
// example1.json
{"input": {"html": "..."}, "output": {...}}

// example2.json - missing "html" key!
{"input": {"url": "..."}, "output": {...}}

// ✅ GOOD - Consistent
// All examples have same input keys
{"input": {"html": "...", "url": "..."}, "output": {...}}
```

✅ **Use optional fields for variations**:
```json
// If some examples don't have a field, use null
{
  "input": {
    "html": "<html>...</html>",
    "url": "https://example.com",
    "metadata": null  // Optional field
  }
}
```

---

## Low Confidence Scores

### Issue: Confidence score below 0.85

**Symptom**:
```
✅ Extractor created successfully!
   ...
   Confidence: 67.3%  ⚠️ Low confidence
```

**Interpretation**:

| Score | Meaning | Action |
|-------|---------|--------|
| 0.95-1.00 | Excellent | ✅ Ready for production |
| 0.85-0.94 | Good | ✅ Safe to use |
| 0.70-0.84 | Fair | ⚠️ Review generated code |
| 0.50-0.69 | Poor | ❌ Add more/better examples |
| <0.50 | Failed | ❌ Redesign examples |

**Root Causes and Solutions**:

#### Cause 1: Too Few Examples

❌ **Problem**: Only 1-2 examples provided

✅ **Solution**: Add more diverse examples (2-3 minimum, 3-5 ideal)
```bash
# Before: 2 examples
examples/
├── example1.json
└── example2.json

# After: 4 examples covering edge cases
examples/
├── example1.json  # Typical case
├── example2.json  # Multiple records
├── example3.json  # Empty data
└── example4.json  # Edge case
```

#### Cause 2: Lack of Diversity

❌ **Problem**: All examples are too similar

✅ **Solution**: Cover different scenarios
```json
// Example 1: Typical case
{
  "input": {"html": "<table><tr><td>A</td><td>100</td></tr></table>"},
  "output": {"records": [{"name": "A", "value": 100}], "count": 1}
}

// Example 2: Empty data (edge case)
{
  "input": {"html": "<table></table>"},
  "output": {"records": [], "count": 0}
}

// Example 3: Multiple records
{
  "input": {"html": "<table><tr><td>A</td><td>100</td></tr><tr><td>B</td><td>200</td></tr></table>"},
  "output": {"records": [{"name": "A", "value": 100}, {"name": "B", "value": 200}], "count": 2}
}
```

#### Cause 3: Complex Transformations

❌ **Problem**: Unclear pattern between input and output

✅ **Solution**: Simplify or make patterns explicit
```json
// ❌ BAD - Unclear transformation
{
  "input": {"text": "John Doe - Senior VP - $250K"},
  "output": {"name": "John Doe", "title": "Senior VP", "salary": 250000}
}
// System can't detect the parsing rules!

// ✅ GOOD - Use structured input
{
  "input": {
    "name": "John Doe",
    "title": "Senior VP",
    "salary_text": "$250,000"
  },
  "output": {
    "name": "John Doe",
    "title": "Senior VP",
    "salary": 250000.0
  }
}
// Clear pattern: remove $ and commas, convert to float
```

#### Cause 4: Schema Ambiguity

❌ **Problem**: Output schema not clear from examples

✅ **Solution**: Use consistent field names and types
```json
// ❌ BAD - Inconsistent types
// example1.json
{"output": {"amount": 100}}  // Integer

// example2.json
{"output": {"amount": "100.50"}}  // String!

// ✅ GOOD - Consistent types
// All examples use float
{"output": {"amount": 100.0}}
{"output": {"amount": 100.5}}
```

---

## Validation Failures

### Issue: "Syntax error in generated code"

**Symptom**:
```
❌ Creation failed: validation_failed
   Error: Syntax error in generated extractor.py: invalid syntax (line 42)
   Stage: validating_code
```

**Causes**:
- Template rendering bug
- Special characters in example data not escaped
- Complex nested structures

**Solutions**:

✅ **Check example data for special characters**:
```json
// ❌ BAD - Unescaped quotes in data
{
  "input": {
    "text": "He said "hello""  // Breaks template rendering
  }
}

// ✅ GOOD - Properly escaped
{
  "input": {
    "text": "He said \"hello\""
  }
}
```

✅ **Simplify nested structures**:
```json
// If you have deeply nested data, flatten it:
// ❌ Complex nesting
{
  "output": {
    "data": {
      "records": {
        "items": [{"nested": {"value": 1}}]
      }
    }
  }
}

// ✅ Flattened
{
  "output": {
    "records": [{"value": 1}]
  }
}
```

✅ **Report template bug** (if persistent):
```bash
# Save generated code for inspection
edgar extractors create test_extractor \
  --examples examples/test/ \
  --skip-validation  # Bypass validation

# Inspect generated code
cat src/edgar_analyzer/extractors/test/extractor.py
```

---

### Issue: "Missing IDataExtractor interface"

**Symptom**:
```
❌ Validation failed
   Error: Generated class doesn't implement IDataExtractor
```

**Causes**:
- Template corruption
- Invalid class structure in templates

**Solutions**:

✅ **Reinstall platform**:
```bash
pip install -e ".[dev]" --force-reinstall
```

✅ **Check template integrity**:
```bash
ls -la src/edgar_analyzer/extractors/templates/
# Should contain: extractor.py.j2, models.py.j2, etc.
```

---

## Runtime Errors

### Issue: "Extractor not found in registry"

**Symptom**:
```python
>>> ExtractorClass = registry.get("my_extractor")
KeyError: 'my_extractor not found in registry'
```

**Causes**:
- Extractor created with `--no-register` flag
- Registry file corrupted
- Extractor name mismatch

**Solutions**:

✅ **List registered extractors**:
```bash
edgar extractors list
# Verify your extractor appears in the list
```

✅ **Manually register**:
```python
from edgar_analyzer.extractors.registry import ExtractorRegistry

registry = ExtractorRegistry()
registry.register(
    name="my_extractor",
    class_path="edgar_analyzer.extractors.my_domain.extractor.MyExtractor",
    version="1.0.0",
    description="My extractor",
    domain="my_domain"
)
```

✅ **Check registry file**:
```bash
cat data/extractors/registry.json
# Verify JSON is valid and contains your extractor
```

---

### Issue: "Import failed: ModuleNotFoundError"

**Symptom**:
```python
>>> ExtractorClass = registry.get("my_extractor")
ImportError: No module named 'edgar_analyzer.extractors.my_domain'
```

**Causes**:
- Extractor files not in Python path
- Missing `__init__.py`
- Package not installed

**Solutions**:

✅ **Verify files exist**:
```bash
ls -la src/edgar_analyzer/extractors/my_domain/
# Should contain: __init__.py, extractor.py, models.py, prompts.py
```

✅ **Reinstall package**:
```bash
pip install -e ".[dev]"
```

✅ **Check `__init__.py`**:
```python
# src/edgar_analyzer/extractors/my_domain/__init__.py should contain:
from .extractor import MyExtractor

__all__ = ["MyExtractor"]
```

---

### Issue: "Extraction returns empty results"

**Symptom**:
```python
>>> result = extractor.extract(input_data)
>>> print(result)
{"records": [], "count": 0}  # Expected non-empty!
```

**Causes**:
- Input data format doesn't match training examples
- Heading patterns don't match actual HTML
- LLM failing to extract data

**Solutions**:

✅ **Enable debug logging**:
```python
import structlog
import logging

logging.basicConfig(level=logging.DEBUG)
logger = structlog.get_logger(__name__)

# Run extraction again - will show detailed logs
result = extractor.extract(input_data)
```

✅ **Verify input format matches examples**:
```python
# Check what your extractor expects
from edgar_analyzer.extractors.registry import ExtractorRegistry

registry = ExtractorRegistry()
metadata = registry.get_metadata("my_extractor")
print(f"Training examples: {metadata.examples_count}")

# Compare with your actual input
print(f"Your input keys: {list(input_data.keys())}")
```

✅ **Test with training example**:
```python
# Load one of your training examples
import json
with open("examples/my_domain/example1.json") as f:
    example = json.load(f)

# Should work perfectly since it's training data
result = extractor.extract(example["input"])
print(result)  # Should match example["output"]
```

---

## Registry Issues

### Issue: "Registry file corrupted"

**Symptom**:
```
Error: Failed to load registry.json: JSONDecodeError
```

**Solutions**:

✅ **Backup and recreate**:
```bash
# Backup corrupted file
cp data/extractors/registry.json data/extractors/registry.json.bak

# Create fresh registry
echo '{"version": "1.0.0", "extractors": {}}' > data/extractors/registry.json

# Re-register extractors manually
edgar extractors create ... --auto-register
```

✅ **Restore from git**:
```bash
git checkout data/extractors/registry.json
```

---

### Issue: "Duplicate extractor registration"

**Symptom**:
```
Warning: Extractor 'my_extractor' already registered. Updating.
```

**Solutions**:

✅ **This is normal behavior** - Registry automatically updates existing entries

✅ **To prevent updates, unregister first**:
```python
from edgar_analyzer.extractors.registry import ExtractorRegistry

registry = ExtractorRegistry()
registry.unregister("my_extractor")  # Remove old entry
# Then re-register with new version
```

---

## Performance Problems

### Issue: "Creation takes > 10 seconds"

**Expected**: 2-5 seconds for 3 examples
**Actual**: > 10 seconds

**Causes**:
- Too many examples (> 10)
- Large example files (> 100KB each)
- Complex schemas (> 100 fields)
- Slow LLM response (OpenRouter)

**Solutions**:

✅ **Reduce examples**:
```bash
# Keep only best 3-5 examples
mv examples/my_domain/example{6..10}.json examples/archive/
```

✅ **Simplify examples**:
```json
// ❌ Large example (50KB+)
{
  "input": {
    "html": "<html>... 10,000 lines ...</html>"
  }
}

// ✅ Minimal example (5KB)
{
  "input": {
    "html": "<table>... only relevant table ...</table>"
  }
}
```

✅ **Profile bottlenecks**:
```python
import time
from edgar_analyzer.extractors.meta_extractor import MetaExtractor

meta = MetaExtractor()

start = time.time()
result = meta.create(...)
print(f"Total time: {result.total_time_seconds:.2f}s")

# Check individual stages:
# - Analysis: Should be < 1s
# - Generation: Should be < 500ms
# - Validation: Should be < 200ms
```

---

### Issue: "Extraction is slow (> 5 seconds per input)"

**Expected**: < 1 second per extraction
**Actual**: > 5 seconds

**Causes**:
- Large HTML input (> 1MB)
- LLM timeout or slow response
- Inefficient table parsing

**Solutions**:

✅ **Reduce HTML size before extraction**:
```python
from bs4 import BeautifulSoup

# Strip unnecessary HTML before extraction
soup = BeautifulSoup(html, "html.parser")

# Remove scripts, styles, etc.
for tag in soup(["script", "style", "nav", "footer"]):
    tag.decompose()

# Extract only relevant section
relevant_section = soup.find("div", class_="data-section")
clean_html = str(relevant_section)

# Now extract
result = extractor.extract({"html": clean_html})
```

✅ **Use caching for repeated inputs**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_extract(html_hash: str, extractor_name: str):
    # Extract and cache results
    pass
```

---

## Debugging Tips

### Enable Detailed Logging

```python
import structlog
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Now all operations will log details
from edgar_analyzer.extractors.meta_extractor import MetaExtractor
meta = MetaExtractor()
result = meta.create(...)  # Will show detailed logs
```

### Inspect Generated Code

```bash
# After creation, review generated files
cat src/edgar_analyzer/extractors/my_domain/extractor.py
cat src/edgar_analyzer/extractors/my_domain/models.py
cat src/edgar_analyzer/extractors/my_domain/prompts.py

# Check for obvious issues:
# - Missing imports
# - Incorrect field types
# - Malformed prompts
```

### Test Generated Extractor

```python
# Test with training data (should always work)
import json
from edgar_analyzer.extractors.registry import ExtractorRegistry
from edgar_analyzer.services.openrouter_client import OpenRouterClient

# Load training example
with open("examples/my_domain/example1.json") as f:
    example = json.load(f)

# Get extractor
registry = ExtractorRegistry()
ExtractorClass = registry.get("my_extractor")
extractor = ExtractorClass(openrouter_client=OpenRouterClient())

# Should match training output exactly
result = extractor.extract(example["input"])
expected = example["output"]

print("Result:", result)
print("Expected:", expected)
print("Match:", result == expected)
```

### Run Unit Tests

```bash
# Generated extractors include unit tests
pytest src/edgar_analyzer/extractors/my_domain/test_my_extractor.py -v

# Should show:
# test_extraction_basic PASSED
# test_extraction_empty PASSED
# test_extraction_multiple PASSED
```

### Profile Performance

```python
import time
import cProfile
import pstats

# Profile creation
profiler = cProfile.Profile()
profiler.enable()

result = meta.create(name="test", examples_dir=Path("examples/test/"))

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats("cumulative")
stats.print_stats(20)  # Top 20 slowest functions
```

---

## Best Practices

### 1. Start Simple, Iterate

✅ **Good workflow**:
1. Create with 2 minimal examples
2. Check confidence score
3. Add edge cases one by one
4. Monitor confidence improvement

❌ **Bad workflow**:
- Start with 10 complex examples
- Low confidence, unclear why
- Hard to debug

### 2. Version Your Examples

```bash
examples/
├── v1/  # Initial examples
│   ├── example1.json
│   └── example2.json
├── v2/  # Added edge cases
│   ├── example1.json
│   ├── example2.json
│   └── example3.json  # New!
└── current -> v2/  # Symlink to active version
```

### 3. Test Before Production

```python
# Always test with unseen data before production
test_cases = load_test_data()  # Different from training examples

for test_case in test_cases:
    result = extractor.extract(test_case["input"])
    assert result == test_case["expected_output"]
```

### 4. Monitor Confidence Over Time

```bash
# Track confidence scores
echo "$(date),my_extractor,0.94" >> data/confidence_log.csv

# Review trends
cat data/confidence_log.csv
# 2025-12-07,my_extractor,0.72  # Initial
# 2025-12-07,my_extractor,0.89  # After adding edge cases
# 2025-12-07,my_extractor,0.94  # After simplifying schema
```

### 5. Document Your Examples

```json
// Add comments to example files (in separate .md)
// example1.md:
// This example covers the typical case with 5 executives and complete data.
// Known issues: None
// Last updated: 2025-12-07
```

---

## Getting Help

### Check Documentation

- **[User Guide](META_EXTRACTOR_USER_GUIDE.md)** - Complete usage guide
- **[API Reference](../developer/api/META_EXTRACTOR_API.md)** - Detailed API docs
- **[Architecture](../developer/architecture/META_EXTRACTOR_ARCHITECTURE.md)** - System design

### Enable Debug Mode

```bash
export LOG_LEVEL=DEBUG
edgar extractors create ... 2>&1 | tee debug.log
```

### File Bug Report

Include:
1. Complete error message
2. Example files (anonymized if needed)
3. Debug logs
4. Platform version (`pip show edgar-analyzer`)
5. Python version (`python --version`)

---

**Built with the EDGAR Platform: From SEC filings to general-purpose data extraction.**
