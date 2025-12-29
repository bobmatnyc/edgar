# Quick Reference - Extract & Transform Platform

**Version**: 1.0 Alpha
**For**: Alpha Testers
**Quick Access**: Common commands and troubleshooting

---

## Essential Commands

### Project Management

```bash
# Create new project
edgar_analyzer project create <name>
edgar_analyzer project create <name> --template weather

# List all projects
edgar_analyzer project list

# Validate project
edgar_analyzer project validate <name>

# Delete project
edgar_analyzer project delete <name> --force
```

### Workflow Commands

```bash
# Full workflow (from project directory)
cd projects/my_project/

# 1. Analyze patterns
edgar_analyzer analyze-project .

# 2. Generate code
edgar_analyzer generate-code .

# 3. Run extraction
edgar_analyzer run-extraction .

# 4. Generate reports
edgar_analyzer report generate --format excel --output reports/output.xlsx
```

### Setup and Validation

```bash
# Test OpenRouter connection
edgar_analyzer setup test

# Validate all API keys
edgar_analyzer setup validate-keys

# Show current configuration
edgar_analyzer setup show-config
```

---

## File Structure

### Project Directory Structure

```
projects/my_project/
├── project.yaml        # Configuration
├── input/              # Source data files
│   └── data.xlsx
├── examples/           # Transformation examples
│   ├── row1.json
│   ├── row2.json
│   └── row3.json
├── output/             # Generated code and results
│   ├── extractor.py
│   └── extracted_data.json
└── reports/            # Generated reports (optional)
    ├── report.xlsx
    ├── report.pdf
    ├── report.docx
    └── report.pptx
```

### Example JSON Format

```json
{
  "input": {
    "source_field1": "value1",
    "source_field2": "value2"
  },
  "output": {
    "target_field1": "transformed_value1",
    "target_field2": "transformed_value2"
  }
}
```

---

## Configuration Files

### project.yaml Structure

```yaml
name: My Project
description: Project description
version: 1.0.0

data_source:
  type: excel  # or pdf, api, url
  config:
    file_path: input/data.xlsx
    sheet_name: 0
    header_row: 0

examples:
  - examples/row1.json
  - examples/row2.json

output:
  format: json
  directory: output/

validation:
  required_fields:
    - field1
    - field2
  field_types:
    field1: string
    field2: float
```

### .env.local Configuration

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional
OPENWEATHERMAP_API_KEY=your-key-here
JINA_API_KEY=your-key-here

# Platform settings
LOG_LEVEL=INFO
EDGAR_RATE_LIMIT_DELAY=0.1
```

---

## Data Source Types

### Excel

```yaml
data_source:
  type: excel
  config:
    file_path: input/data.xlsx
    sheet_name: 0           # Sheet index (0-based) or name
    header_row: 0           # Header row index
```

### PDF

```yaml
data_source:
  type: pdf
  config:
    file_path: input/document.pdf
    page_number: 0          # Page to extract (0-based)
    table_strategy: lines   # lines, text, or mixed
```

### API

```yaml
data_source:
  type: api
  config:
    base_url: https://api.example.com
    endpoint: /data
    method: GET             # GET or POST
    headers:
      Authorization: Bearer ${API_KEY}
    params:
      limit: 100
```

### URL (Web Scraping)

```yaml
data_source:
  type: url
  config:
    url: https://example.com/data
    use_jina: true          # Use Jina.ai for JS-heavy sites
```

---

## Common Patterns

### Transformation Patterns

| Pattern | Example | Config |
|---------|---------|--------|
| **Field Rename** | `employee_id` → `id` | Just change name in output |
| **Concatenation** | `first + last` → `full_name` | Show concatenated value |
| **Type Convert** | `"100"` (str) → `100` (int) | Change type in output |
| **Boolean** | `"Yes"` → `true` | Show boolean in output |
| **Currency** | `"$15.00"` → `15.00` | Remove currency symbol |
| **Date Parse** | `"2024-01-01"` → date object | Parse date string |

### Example Transformations

**Field Rename**:
```json
{
  "input": {"old_name": "value"},
  "output": {"new_name": "value"}
}
```

**Concatenation**:
```json
{
  "input": {
    "first_name": "Alice",
    "last_name": "Johnson"
  },
  "output": {
    "full_name": "Alice Johnson"
  }
}
```

**Type Conversion**:
```json
{
  "input": {"salary": 95000},
  "output": {"annual_salary_usd": 95000.0}
}
```

**Boolean Conversion**:
```json
{
  "input": {"is_manager": "Yes"},
  "output": {"manager": true}
}
```

---

## Troubleshooting

### Quick Diagnostics

```bash
# View logs
tail -50 logs/edgar_analyzer.log

# Follow logs in real-time
tail -f logs/edgar_analyzer.log

# Search for errors
grep -i error logs/edgar_analyzer.log

# Check Python version
python --version  # Should be 3.11+

# Check package installation
pip list | grep edgar

# Verify working directory
pwd
ls -la
```

### Common Errors

**Error: "API key not found"**
```bash
# Solution
ls -la .env.local  # Check file exists
cat .env.local | grep OPENROUTER  # Check key present
python -m edgar_analyzer setup test  # Verify connection
```

**Error: "Pattern detection failed"**
```bash
# Solution: Add 3rd example
cp examples/row1.json examples/row3.json
# Edit row3.json with different data
edgar_analyzer analyze-project .
```

**Error: "Table not detected"**
```yaml
# Solution: Try different strategy
data_source:
  config:
    table_strategy: text  # or mixed instead of lines
```

**Error: "Permission denied"**
```bash
# Solution: Fix permissions
chmod -R u+w projects/my_project/output/
```

**Error: "Module not found"**
```bash
# Solution: Reinstall
pip install -e ".[dev]"
```

---

## Keyboard Shortcuts

### Terminal

- `Ctrl+C` - Cancel current command
- `Ctrl+Z` - Suspend current command
- `Ctrl+R` - Search command history
- `↑ / ↓` - Navigate command history
- `Tab` - Auto-complete command/path

### Nano Editor

- `Ctrl+O` - Save file
- `Ctrl+X` - Exit editor
- `Ctrl+K` - Cut line
- `Ctrl+U` - Paste line
- `Ctrl+W` - Search in file

---

## File Locations

### Platform Files

```
edgar/
├── .env.local                      # API keys (gitignored)
├── projects/                       # User projects
├── test_data/                      # Sample data for testing
├── logs/                           # Application logs
├── docs/                           # Documentation
└── src/edgar_analyzer/             # Platform code
```

### Log Files

```
logs/
├── edgar_analyzer.log              # Main application log
└── tests/                          # Test logs
```

### Sample Data

```
test_data/
├── employee_roster_sample.xlsx     # Excel sample
├── invoice_sample.pdf              # PDF sample
├── examples/                       # Pre-built examples
│   ├── employee_roster/
│   └── invoice/
└── instructions/
    ├── api_setup.md                # API key setup
    └── quick_reference.md          # This file
```

---

## Cheat Sheet

### Typical Workflow

```bash
# 1. Setup (once)
git clone <repo>
cd edgar
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.template .env.local
# Edit .env.local with API keys

# 2. Create project
cd projects/
mkdir my_project
cd my_project
mkdir input examples output

# 3. Add data and examples
cp ../../test_data/sample.xlsx input/
cp ../../test_data/examples/row1.json examples/

# 4. Configure
nano project.yaml

# 5. Run workflow
cd ../..
edgar_analyzer analyze-project projects/my_project/
edgar_analyzer generate-code projects/my_project/
edgar_analyzer run-extraction projects/my_project/

# 6. Check results
cat projects/my_project/output/extracted_data.json
```

### One-Liner Commands

```bash
# Quick test extraction
edgar_analyzer run-extraction projects/my_project/ && cat projects/my_project/output/extracted_data.json | head -20

# Generate all report formats
for fmt in excel pdf docx pptx; do
  edgar_analyzer report generate --project projects/my_project/ --format $fmt --output reports/report.$fmt
done

# Check logs for errors
tail -100 logs/edgar_analyzer.log | grep -i error

# Validate all projects
edgar_analyzer project list --format json | jq -r '.[].name' | while read proj; do
  echo "Validating $proj..."
  edgar_analyzer project validate $proj
done
```

---

## Getting Help

### Documentation

- **User Testing Guide**: `docs/guides/USER_TESTING_GUIDE.md`
- **Platform Usage**: `docs/guides/PLATFORM_USAGE.md`
- **Troubleshooting**: `docs/guides/TROUBLESHOOTING.md`
- **API Reference**: `docs/api/`

### Support Channels

- **Slack**: #edgar-alpha-testing (fastest)
- **Email**: edgar-support@example.com
- **GitHub**: https://github.com/yourorg/edgar/issues

### Useful Links

- **OpenRouter**: https://openrouter.ai/
- **OpenWeatherMap**: https://openweathermap.org/api
- **Platform Docs**: `open docs/README.md`

---

## Tips and Tricks

### Speed Up Testing

- Use provided sample data instead of your own
- Start with 2 examples (add 3rd if needed)
- Use template projects: `--template weather`
- Keep examples simple initially

### Improve Pattern Detection

- Provide 3 examples instead of 2
- Show edge cases (nulls, special chars)
- Be consistent with field names
- Use clear transformation patterns

### Debug Faster

- Check logs first: `tail -f logs/edgar_analyzer.log`
- Test API keys: `edgar_analyzer setup test`
- Validate config: `edgar_analyzer project validate .`
- Use verbose mode: `edgar_analyzer -v run-extraction .`

### Report Issues Effectively

Include:
1. Command you ran
2. Complete error message
3. Relevant config files (project.yaml, examples)
4. Logs (sanitize sensitive data!)
5. OS and Python version

---

**Document Version**: 1.0
**Last Updated**: 2025-12-04
**Maintained By**: Platform Development Team

**Questions?** See User Testing Guide or ask in #edgar-alpha-testing Slack channel!
