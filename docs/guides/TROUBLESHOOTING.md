# Troubleshooting Guide

Common errors and how to fix them when using the EDGAR Extract & Transform Platform.

## Code Generation Errors

### ❌ Code Validation Failed

**Error**: `Generated code for 'project_name' failed quality validation after 3 attempts`

**Causes**:
- Examples have inconsistent structure
- Missing required fields in examples
- Type mismatches between examples
- Invalid transformation patterns detected

**Solutions**:
1. **Review validation issues** listed in the error message
2. **Check examples for consistency** - all examples should have same field names
3. **Verify required fields** - ensure all examples have complete data
4. **Use `--skip-validation` flag** to generate anyway and inspect code manually:
   ```bash
   edgar-analyzer project generate my_project --skip-validation
   ```
5. **Start simple** - Begin with 2-3 simple examples to validate approach:
   ```bash
   # Remove complex examples temporarily
   mv examples/complex_example.json examples/complex_example.json.bak

   # Generate with simple examples only
   edgar-analyzer project generate my_project
   ```

**Example**:
```bash
# Generate with validation skipped
edgar-analyzer project generate weather_api --skip-validation

# Then review generated code manually
cat projects/weather_api/output/extractor.py
```

**Related Documentation**:
- [Pattern Detection Guide](PATTERN_DETECTION.md)
- [Example-Driven Transformation](PROJECT_MANAGEMENT.md#examples)

---

### 🔑 OpenRouter API Authentication Failed

**Error**: `OpenRouter API authentication failed`

**Causes**:
- `OPENROUTER_API_KEY` environment variable not set
- Invalid or expired API key
- `.env.local` file not in correct location
- `.env.local` file not loaded by shell

**Solutions**:

1. **Create `.env.local` in project root**:
   ```bash
   # Navigate to project root
   cd /path/to/edgar/

   # Create .env.local with your API key
   echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env.local

   # Verify file exists
   cat .env.local
   ```

2. **Get valid API key** from OpenRouter:
   - Visit: https://openrouter.ai/keys
   - Create new key or copy existing key
   - Key format: `sk-or-v1-...`

3. **Verify environment variable is loaded**:
   ```bash
   # Check if variable is set
   echo $OPENROUTER_API_KEY

   # If empty, load .env.local manually
   export $(cat .env.local | xargs)
   ```

4. **Test connection**:
   ```bash
   # Test OpenRouter connection (future feature)
   edgar-analyzer setup --test openrouter
   ```

**Troubleshooting Steps**:
```bash
# 1. Check if .env.local exists
ls -la .env.local

# 2. Check file contents (verify key format)
cat .env.local

# 3. Check if variable is loaded
echo $OPENROUTER_API_KEY

# 4. Try loading manually
source .env.local  # or export $(cat .env.local | xargs)

# 5. Test again
edgar-analyzer project generate my_project
```

---

### ⏱️ OpenRouter Rate Limit Exceeded

**Error**: `OpenRouter API rate limit exceeded`

**Causes**:
- Too many API requests in short time period
- Free tier rate limits exceeded
- Multiple projects generating simultaneously

**Solutions**:

1. **Wait 60 seconds and retry**:
   ```bash
   # Wait for rate limit window to reset
   sleep 60

   # Retry generation
   edgar-analyzer project generate my_project
   ```

2. **Check rate limits** at OpenRouter dashboard:
   - Visit: https://openrouter.ai/activity
   - View current usage and limits
   - Check remaining quota

3. **Use `--skip-validation` to reduce API calls**:
   ```bash
   # Skip validation step (fewer API calls)
   edgar-analyzer project generate my_project --skip-validation
   ```

4. **Consider upgrading OpenRouter plan**:
   - Visit: https://openrouter.ai/settings/billing
   - Free tier: 10 requests/minute
   - Paid tiers: Higher limits

**Rate Limit Details**:
- **Free Tier**: 10 requests/minute, 200 requests/day
- **Code Generation**: 2-4 API calls per generation (PM mode + Coder mode + validation)
- **Retry Logic**: Automatic exponential backoff (1s, 2s, 4s)

---

### 📋 Project Not Found

**Error**: `Project 'project_name' not found`

**Causes**:
- Project name misspelled
- Project in different directory than expected
- Project not yet created
- `EDGAR_ARTIFACTS_DIR` pointing to wrong location

**Solutions**:

1. **List available projects**:
   ```bash
   edgar-analyzer project list
   ```

2. **Create new project if needed**:
   ```bash
   edgar-analyzer project create my_project --template weather
   ```

3. **Verify project name spelling**:
   ```bash
   # List with tree format for full directory structure
   edgar-analyzer project list --format tree
   ```

4. **Check artifacts directory**:
   ```bash
   # Check where projects are stored
   echo $EDGAR_ARTIFACTS_DIR

   # List projects directory
   ls -la ${EDGAR_ARTIFACTS_DIR:-./projects}
   ```

5. **Use correct output directory**:
   ```bash
   # If project is in custom location
   edgar-analyzer project generate my_project --output-dir /custom/path
   ```

**Example**:
```bash
# List all projects
edgar-analyzer project list

# Output:
# Projects (3)
# ┌─────────────┬─────────┬──────────┬─────────────────┐
# │ Name        │ Version │ Template │ Description     │
# ├─────────────┼─────────┼──────────┼─────────────────┤
# │ weather_api │ 0.1.0   │ weather  │ Weather data    │
# │ news_scrape │ 0.1.0   │ minimal  │ News scraper    │
# │ invoice_ext │ 0.1.0   │ minimal  │ Invoice extract │
# └─────────────┴─────────┴──────────┴─────────────────┘

# Create project if not listed
edgar-analyzer project create my_api --template weather
```

---

### 📄 Examples Directory Not Found

**Error**: `Examples directory not found: projects/my_project/examples/`

**Causes**:
- Examples directory not created
- Examples in wrong location
- Project created without template
- Directory deleted accidentally

**Solutions**:

1. **Create examples directory**:
   ```bash
   mkdir -p projects/my_project/examples
   ```

2. **Add 2-3 example JSON files**:
   ```bash
   # Copy from weather_api template
   cp examples/weather_api/example1.json projects/my_project/examples/
   cp examples/weather_api/example2.json projects/my_project/examples/

   # Or create manually
   cat > projects/my_project/examples/example1.json <<'EOF'
   {
     "input": {
       "temp": 15.5,
       "city": "London"
     },
     "output": {
       "temperature_c": 15.5,
       "location": "London"
     }
   }
   EOF
   ```

3. **Review example format**:
   ```bash
   # Check weather_api examples for reference
   cat examples/weather_api/example1.json
   ```

4. **Verify directory structure**:
   ```bash
   # Expected structure
   projects/my_project/
   ├── project.yaml
   ├── examples/          # Must exist
   │   ├── example1.json  # At least 2 examples
   │   └── example2.json
   ├── input/             # Optional: source data files
   └── output/            # Created during generation
   ```

**Example Format**:
```json
{
  "input": {
    "field1": "value1",
    "field2": 42
  },
  "output": {
    "transformed_field": "value1",
    "count": 42
  }
}
```

**See**: [Project Management Guide](PROJECT_MANAGEMENT.md) for full setup instructions.

---

### 📝 Invalid project.yaml Configuration

**Error**: `Invalid project.yaml configuration: <validation error>`

**Causes**:
- Syntax errors in YAML file
- Missing required fields
- Invalid data types
- Schema validation failure

**Solutions**:

1. **Validate YAML syntax**:
   ```bash
   # Check for syntax errors
   python -c "import yaml; yaml.safe_load(open('projects/my_project/project.yaml'))"
   ```

2. **Review required fields**:
   ```yaml
   # Minimal valid project.yaml
   project:
     name: my_project
     version: "0.1.0"
     description: "My project description"

   data_sources:
     - name: main
       type: api
       config:
         url: "https://api.example.com"

   examples:
     - examples/example1.json

   output:
     - format: json
   ```

3. **Use template as reference**:
   ```bash
   # Copy working template
   cp templates/minimal_project.yaml projects/my_project/project.yaml

   # Customize as needed
   vim projects/my_project/project.yaml
   ```

4. **Validate project configuration**:
   ```bash
   # Run validation command
   edgar-analyzer project validate my_project --verbose
   ```

**Common Issues**:
- **Missing quotes**: `version: 0.1.0` should be `version: "0.1.0"`
- **Invalid indentation**: Use 2 spaces, not tabs
- **Missing required fields**: Check error message for field name
- **Wrong data type**: String vs. integer vs. boolean

---

## Setup and Configuration

### Validate API Connections (T14) 🆕

Before generating code, test your API connections:

```bash
edgar-cli setup test
```

**Common Issues**:

#### OpenRouter Authentication Failed
**Error**: `❌ OPENROUTER_API_KEY not set`

**Solution**:
1. Create `.env.local` in project root
2. Add: `OPENROUTER_API_KEY=sk-or-v1-...`
3. Get key from: https://openrouter.ai/keys
4. Test: `edgar-cli setup test --service openrouter`

**Example**:
```bash
# 1. Check if .env.local exists
ls -la .env.local

# 2. Create if missing
cat > .env.local <<EOF
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
EOF

# 3. Test connection
edgar-cli setup test --service openrouter

# Expected output:
# Testing OpenRouter API...
#   ✓ API key found (sk-or-v1-1234...)
#   ✓ API connection successful
#   ✓ Model: anthropic/claude-3.5-sonnet
```

#### Jina.ai Connection Failed
**Error**: `⚠️ JINA_API_KEY not set (optional)`

**Note**: Jina.ai is optional (used for web scraping features)

**Solution** (if needed):
1. Get key from: https://jina.ai
2. Add to `.env.local`: `JINA_API_KEY=jina_...`
3. Test: `edgar-cli setup test --service jina`

**Example**:
```bash
# Add to .env.local
echo "JINA_API_KEY=jina_YOUR_KEY_HERE" >> .env.local

# Test connection
edgar-cli setup test --service jina

# Expected output:
# Testing Jina.ai API...
#   ✓ API key found (jina_ab12...)
#   ✓ Jina.ai connection successful
```

#### All Services Test
```bash
# Test all services at once
edgar-cli setup test

# Example output:
# EDGAR Platform Connection Test
#
# Testing OpenRouter API...
#   ✓ API key found (sk-or-v1-1234...)
#   ✓ API connection successful
#   ✓ Model: anthropic/claude-3.5-sonnet
#
# Testing Jina.ai API...
#   ✓ API key found (jina_ab12...)
#   ✓ Jina.ai connection successful
#
# Test Summary:
#   openrouter: ✅ PASS
#   jina: ✅ PASS
#
# All services operational
```

**Troubleshooting**:
- **OpenRouter fails**: Check API key format (should start with `sk-or-v1-`)
- **Jina.ai fails**: Web scraping features won't work (optional service)
- **All fail**: Check internet connection and firewall settings
- **Permission errors**: Verify `.env.local` file permissions

---

## Installation & Setup Errors

### 🐍 Python Version Mismatch

**Error**: `Python 3.11+ required`

**Solution**:
```bash
# Check Python version
python --version

# Install Python 3.11+ using pyenv
pyenv install 3.11
pyenv global 3.11

# Or using conda
conda create -n edgar python=3.11
conda activate edgar
```

---

### 📦 Dependency Installation Failed

**Error**: `pip install failed` or `ImportError`

**Solutions**:

1. **Use development install**:
   ```bash
   pip install -e ".[dev]"
   ```

2. **Upgrade pip**:
   ```bash
   pip install --upgrade pip
   ```

3. **Clear pip cache**:
   ```bash
   pip cache purge
   pip install -e ".[dev]"
   ```

---

## Runtime Errors

### 🔄 Async Event Loop Errors

**Error**: `Event loop is closed` or `RuntimeError: This event loop is already running`

**Solutions**:

1. **Use async context manager**:
   ```python
   import asyncio

   async def main():
       result = await service.generate(...)

   asyncio.run(main())
   ```

2. **Check for existing event loop**:
   ```python
   try:
       loop = asyncio.get_running_loop()
   except RuntimeError:
       loop = asyncio.new_event_loop()
       asyncio.set_event_loop(loop)
   ```

---

## General Troubleshooting Tips

### Enable Debug Logging

```bash
# Set debug log level
export LOG_LEVEL=DEBUG

# Run command with verbose output
edgar-analyzer project generate my_project --verbose
```

### Check Logs

```bash
# View recent logs
tail -f logs/edgar_analyzer.log

# Search for errors
grep -i error logs/edgar_analyzer.log
```

### Clean Generated Files

```bash
# Remove generated code and start fresh
rm -rf projects/my_project/output/

# Regenerate
edgar-analyzer project generate my_project
```

### Verify Installation

```bash
# Check package version
pip show edgar-analyzer

# Run tests
pytest tests/

# Verify dependencies
pip check
```

---

## Getting Help

### Report Issues

If you encounter a bug or unexpected behavior:

1. **Collect error information**:
   - Full error message and stack trace
   - Command that triggered the error
   - Python version: `python --version`
   - Package version: `pip show edgar-analyzer`
   - Operating system

2. **Check existing issues**:
   - Search GitHub issues: https://github.com/your-org/edgar/issues

3. **Report new issue**:
   - Include all error information above
   - Provide minimal reproducible example
   - Attach relevant configuration files (project.yaml, examples)

### Community Support

- **Documentation**: [docs/README.md](../README.md)
- **User Guide**: [QUICK_START.md](QUICK_START.md)
- **API Reference**: [docs/api/](../api/)
- **GitHub Issues**: https://github.com/your-org/edgar/issues

---

## Related Documentation

- [Quick Start Guide](QUICK_START.md) - Initial setup
- [Project Management](PROJECT_MANAGEMENT.md) - Project structure and configuration
- [Pattern Detection](PATTERN_DETECTION.md) - Transformation pattern reference
- [Platform Usage](PLATFORM_USAGE.md) - Complete usage examples
- [CLI Reference](CLI_USAGE.md) - Command-line interface documentation
