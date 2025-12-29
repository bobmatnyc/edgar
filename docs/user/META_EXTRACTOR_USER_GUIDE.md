# Meta-Extractor User Guide

The **Meta-Extractor** is a powerful system that **automatically generates custom data extractors from examples**. Just provide 2-3 examples of input/output pairs, and the system creates a complete, production-ready extractor for you.

## Quick Start: Create Your First Extractor in 5 Minutes

### Prerequisites

- EDGAR Platform installed (`pip install -e ".[dev]"`)
- OpenRouter API key configured in `.env.local`
- 2-3 example JSON files showing input → output transformations

### Step 1: Prepare Your Examples

Create a directory with example files:

```bash
mkdir -p examples/my_domain/
```

Each example file should contain an input/output pair:

```json
{
  "input": {
    "html": "<html><table><tr><th>Name</th><th>Amount</th></tr>...</table></html>",
    "url": "https://example.com/data.html"
  },
  "output": {
    "records": [
      {
        "name": "John Doe",
        "amount": 50000.0
      }
    ],
    "total_count": 1
  }
}
```

**Best Practice**: Provide 2-3 diverse examples covering edge cases (empty data, multiple records, etc.)

### Step 2: Generate the Extractor

Run a single command:

```bash
edgar extractors create my_extractor \
  --examples examples/my_domain/ \
  --description "Extract data from HTML tables"
```

**Expected Output**:
```
🔧 Creating extractor: my_extractor
   Examples: examples/my_domain/

✅ Extractor created successfully!
   Domain: my_domain
   Confidence: 92.5%
   Files: 4
   Time: 3.42s
   Registered as: my_extractor

📁 Output: src/edgar_analyzer/extractors/my_domain/
```

### Step 3: Use Your New Extractor

```python
from edgar_analyzer.extractors.registry import ExtractorRegistry
from edgar_analyzer.services.openrouter_client import OpenRouterClient

# Load the extractor
registry = ExtractorRegistry()
ExtractorClass = registry.get("my_extractor")

# Initialize with OpenRouter client
openrouter = OpenRouterClient()
extractor = ExtractorClass(openrouter_client=openrouter)

# Extract data
input_data = {
    "html": "<html>...</html>",
    "url": "https://example.com/data.html"
}
result = extractor.extract(input_data)
print(result)
```

**That's it!** You now have a working, registered extractor.

---

## Complete Workflow Example

Let's walk through creating an extractor for **Summary Compensation Tables (SCT)** from SEC proxy filings.

### 1. Understand Your Data

**Input**: HTML proxy filing with embedded compensation tables
**Output**: Structured JSON with executive compensation data

### 2. Create Example Files

Create `examples/sct/example1.json`:

```json
{
  "input": {
    "html": "<html><body><p><b>Summary Compensation Table</b></p><table><tr><th>Name</th><th>Year</th><th>Salary</th><th>Bonus</th><th>Total</th></tr><tr><td>Jane Smith</td><td>2023</td><td>$750,000</td><td>$200,000</td><td>$950,000</td></tr></table></body></html>",
    "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000010/aapl-20231230.htm",
    "filing_type": "DEF 14A",
    "cik": "0000320193"
  },
  "output": {
    "table_found": true,
    "records": [
      {
        "name": "Jane Smith",
        "year": 2023,
        "salary": 750000.0,
        "bonus": 200000.0,
        "total_compensation": 950000.0
      }
    ],
    "record_count": 1
  }
}
```

Create `examples/sct/example2.json` and `example3.json` with variations (multiple executives, different years, edge cases).

### 3. Generate the Extractor

```bash
edgar extractors create sct_extractor \
  --examples examples/sct/ \
  --description "Extract Summary Compensation Table from SEC proxy filings" \
  --domain sct
```

**Generated Files**:
```
src/edgar_analyzer/extractors/sct/
├── __init__.py            # Package initialization
├── extractor.py           # Main SCTExtractor class
├── models.py              # Pydantic models for validation
├── prompts.py             # LLM system prompts
└── test_sct_extractor.py  # Unit tests
```

### 4. Validate the Extractor

```bash
edgar extractors validate sct_extractor
```

**Output**:
```
🔍 Validating extractor: sct_extractor
✅ Dynamic import successful
   Class: SCTExtractor
✅ Has 'extract' method

✅ Extractor validation passed!
```

### 5. Inspect Extractor Details

```bash
edgar extractors info sct_extractor
```

**Output**:
```
📦 sct_extractor
   Description: Extract Summary Compensation Table from SEC proxy filings
   Domain: sct
   Version: 1.0.0
   Confidence: 94.2%
   Examples: 3
   Tags: sct, compensation, sec, proxy
   Class: edgar_analyzer.extractors.sct.extractor.SCTExtractor
   Created: 2025-12-07T22:45:00Z
   Updated: 2025-12-07T22:45:00Z
```

### 6. Use in Production

```python
from edgar_analyzer.extractors.registry import ExtractorRegistry
from edgar_analyzer.services.openrouter_client import OpenRouterClient

# Load extractor
registry = ExtractorRegistry()
SCTExtractor = registry.get("sct_extractor")

# Initialize
openrouter = OpenRouterClient()
extractor = SCTExtractor(openrouter_client=openrouter)

# Extract from real proxy filing
input_data = {
    "html": "<html>... proxy filing HTML ...</html>",
    "url": "https://www.sec.gov/...",
    "filing_type": "DEF 14A",
    "cik": "0000320193"
}

result = extractor.extract(input_data)

# Result is validated against Pydantic schema
print(f"Found {result['record_count']} executives")
for record in result['records']:
    print(f"{record['name']}: ${record['total_compensation']:,.0f}")
```

---

## Best Practices for Writing Examples

### 1. Quality Over Quantity

**Good**: 2-3 high-quality, diverse examples
**Bad**: 10 nearly-identical examples

### 2. Cover Edge Cases

Include examples with:
- ✅ Typical cases (most common scenario)
- ✅ Empty data (no records found)
- ✅ Multiple records (array handling)
- ✅ Missing fields (optional data)
- ✅ Different formats (variations in input structure)

**Example Set**:
```
example1.json - Typical case: 5 executives, complete data
example2.json - Edge case: No table found (table_found=false)
example3.json - Multiple years: 3 executives × 3 years
```

### 3. Use Consistent Structure

All examples should follow the same schema:

```json
{
  "input": { ... },   // Always same keys
  "output": { ... }   // Always same structure
}
```

### 4. Include Domain Context

Add contextual fields that help the extractor:

```json
{
  "input": {
    "html": "<html>...</html>",
    "url": "https://...",           // Helps with context
    "filing_type": "DEF 14A",       // Domain-specific info
    "cik": "0000320193",            // Additional metadata
    "fiscal_year": 2023
  }
}
```

### 5. Annotate Complex Transformations

Use comments in your examples (for documentation, not in actual JSON):

```json
{
  "input": {
    "raw_amount": "$1,500,000"
  },
  "output": {
    "amount": 1500000.0   // Stripped $, commas, converted to float
  }
}
```

---

## CLI Command Reference

### Create Extractor

```bash
edgar extractors create <name> --examples <dir> [OPTIONS]
```

**Arguments**:
- `<name>` - Extractor name (e.g., `sct_extractor`)

**Options**:
- `--examples`, `-e` - Directory with example JSON files (required)
- `--description`, `-d` - Human-readable description
- `--domain` - Domain slug (defaults to name without `_extractor`)
- `--no-register` - Skip registry registration
- `--skip-validation` - Skip code validation (not recommended)

**Example**:
```bash
edgar extractors create patent_extractor \
  -e examples/patents/ \
  -d "Extract patent data from USPTO filings" \
  --domain patent
```

### List Extractors

```bash
edgar extractors list [OPTIONS]
```

**Options**:
- `--domain`, `-d` - Filter by domain
- `--min-confidence`, `-c` - Minimum confidence threshold (0.0-1.0)
- `--format`, `-f` - Output format: `table` or `json`

**Examples**:
```bash
# List all extractors
edgar extractors list

# Filter by domain
edgar extractors list --domain sct

# Filter by confidence
edgar extractors list --min-confidence 0.9

# JSON output
edgar extractors list --format json
```

### Show Extractor Info

```bash
edgar extractors info <name>
```

**Example**:
```bash
edgar extractors info sct_extractor
```

### Validate Extractor

```bash
edgar extractors validate <name>
```

**Example**:
```bash
edgar extractors validate sct_extractor
```

---

## Understanding Confidence Scores

The Meta-Extractor analyzes your examples and assigns a **confidence score** (0.0-1.0) indicating how well it understands the transformation pattern.

### Confidence Ranges

| Score | Meaning | Recommendation |
|-------|---------|----------------|
| **0.95-1.00** | Excellent - High pattern clarity | ✅ Ready for production |
| **0.85-0.94** | Good - Clear patterns detected | ✅ Safe to use |
| **0.70-0.84** | Fair - Some ambiguity | ⚠️ Review generated code |
| **0.50-0.69** | Poor - Unclear patterns | ❌ Add more/better examples |
| **<0.50** | Failed - Insufficient pattern detection | ❌ Revisit example design |

### Improving Low Confidence

**If confidence < 0.85**:

1. **Add more diverse examples** - Cover more edge cases
2. **Simplify output structure** - Remove unnecessary nesting
3. **Make patterns explicit** - Use consistent field names
4. **Check input consistency** - Ensure all examples have same structure
5. **Review schema complexity** - Break into smaller extractors if needed

**Example**: Confidence jumped from 0.72 → 0.94 by adding one edge case example with empty data.

---

## Advanced Usage

### Custom Domain Naming

```bash
edgar extractors create my_custom_extractor \
  --examples examples/custom/ \
  --domain custom_domain  # Override default domain
```

### Skip Auto-Registration

Generate extractor without registering (for testing):

```bash
edgar extractors create test_extractor \
  --examples examples/test/ \
  --no-register
```

Manually register later:

```python
from edgar_analyzer.extractors.registry import ExtractorRegistry

registry = ExtractorRegistry()
registry.register(
    name="test_extractor",
    class_path="edgar_analyzer.extractors.test.extractor.TestExtractor",
    version="1.0.0",
    description="Test extractor",
    domain="test"
)
```

### Skip Validation (Not Recommended)

```bash
edgar extractors create risky_extractor \
  --examples examples/risky/ \
  --skip-validation  # Bypasses code quality checks
```

**Warning**: Only use `--skip-validation` for rapid prototyping. Always validate before production use.

---

## Troubleshooting

See [META_EXTRACTOR_TROUBLESHOOTING.md](META_EXTRACTOR_TROUBLESHOOTING.md) for detailed troubleshooting guide.

### Quick Fixes

**Issue**: "No patterns detected" (confidence < 0.5)
- ✅ **Fix**: Add more diverse examples with clear input→output mapping

**Issue**: "Validation failed - syntax error"
- ✅ **Fix**: Check example JSON syntax, ensure valid JSON

**Issue**: "Extractor not found in registry"
- ✅ **Fix**: Run `edgar extractors list` to verify registration

**Issue**: "Import failed: ModuleNotFoundError"
- ✅ **Fix**: Reinstall platform: `pip install -e ".[dev]"`

---

## Next Steps

- **[API Reference](../developer/api/META_EXTRACTOR_API.md)** - Detailed API documentation
- **[Architecture Guide](../developer/architecture/META_EXTRACTOR_ARCHITECTURE.md)** - System design and internals
- **[Troubleshooting](META_EXTRACTOR_TROUBLESHOOTING.md)** - Debugging and optimization
- **[Platform API](../developer/api/PLATFORM_API.md)** - Core platform components

---

**Built with the EDGAR Platform: From SEC filings to general-purpose data extraction.**
