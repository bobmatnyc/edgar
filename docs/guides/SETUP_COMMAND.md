# Setup Command Guide

The `setup` command provides an interactive wizard and CLI interface for configuring API keys and platform settings.

## Features

- 🔧 **Interactive Wizard**: User-friendly terminal UI for configuration
- 🤖 **Non-Interactive Mode**: Script-friendly CLI mode for automation
- ✅ **API Key Validation**: Test connections before saving
- 🔒 **Secure Input**: Masked password entry for API keys
- 📝 **Safe Updates**: Preserves existing configuration and comments
- 📊 **Status Display**: Shows current configuration state

## Quick Start

### Interactive Mode

Run the wizard to configure all API keys:

```bash
edgar-analyzer setup
```

The wizard will:
1. Display current configuration status
2. Prompt for each API key (with defaults)
3. Optionally validate keys by testing connections
4. Save configuration to `.env.local`

### Non-Interactive Mode

Configure a single key without prompts:

```bash
# OpenRouter API key
edgar-analyzer setup --key openrouter --value "sk-or-v1-..."

# Jina.ai API key
edgar-analyzer setup --key jina --value "jina_..."

# SEC EDGAR User Agent
edgar-analyzer setup --key edgar --value "YourName email@example.com"
```

## Configuration Options

### API Keys

#### OpenRouter (Required)
- **Purpose**: Primary LLM provider for data extraction
- **Get Key**: https://openrouter.ai/keys
- **Format**: `sk-or-v1-...`
- **Example**: `sk-or-v1-1234567890abcdef...`

#### Jina.ai (Optional)
- **Purpose**: Web content extraction and reading
- **Get Key**: https://jina.ai
- **Format**: `jina_...`
- **Example**: `jina_abc123def456...`

#### SEC EDGAR User Agent (Required for EDGAR)
- **Purpose**: Identifies your application to SEC servers
- **Format**: `Name email@example.com`
- **Example**: `John Doe john.doe@company.com`
- **Note**: SEC requires valid contact information

## Command Options

```bash
edgar-analyzer setup [OPTIONS]
```

### Options

- `--key TEXT`: API key to configure (`openrouter`, `jina`, `edgar`)
- `--value TEXT`: API key value (for non-interactive mode)
- `--validate / --no-validate`: Validate API key (default: validate)
- `--help`: Show help message

## Usage Examples

### Interactive Setup (Recommended)

```bash
# Start interactive wizard
edgar-analyzer setup
```

Output:
```
🔧 EDGAR Platform Setup Wizard

Current Configuration
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Service    ┃ Status          ┃ Value                          ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ OpenRouter │ ❌ Not configured │ Required                       │
│ Jina.ai    │ ❌ Not configured │ Optional                       │
│ SEC EDGAR  │ ❌ Not configured │ Required for EDGAR sources     │
└────────────┴─────────────────┴────────────────────────────────┘

OpenRouter API Key
Get your key from https://openrouter.ai/keys
Enter OpenRouter API Key: ●●●●●●●●●●●●●●●●

Jina.ai API Key (optional)
Get your key from https://jina.ai
Enter Jina.ai API Key (optional):

SEC EDGAR User Agent
Format: YourName email@example.com
Enter SEC EDGAR User Agent: John Doe john@example.com

Validate API keys? [Y/n]: y

Validating API keys...
Testing openrouter... ✅
Testing edgar... ✅

✅ Configuration saved to .env.local
```

### Non-Interactive Setup

```bash
# Configure OpenRouter without validation
edgar-analyzer setup --key openrouter --value "sk-or-v1-test123" --no-validate

# Configure and validate
edgar-analyzer setup --key openrouter --value "sk-or-v1-real-key"
```

### Update Existing Configuration

```bash
# Update OpenRouter key
edgar-analyzer setup --key openrouter --value "sk-or-v1-new-key"

# Update EDGAR user agent
edgar-analyzer setup --key edgar --value "Jane Smith jane@newcompany.com"
```

## Validation

The `--validate` option (enabled by default) tests API key validity:

### OpenRouter Validation
- Tests connection to `https://openrouter.ai/api/v1/models`
- Verifies API key format and authorization
- Returns ✅ if key is valid

### Jina.ai Validation
- Tests Jina Reader API endpoint
- Verifies API key authorization
- Returns ✅ if key is valid

### EDGAR User Agent Validation
- Checks format: `Name email@example.com`
- Requires both name and email with `@` symbol
- Returns ✅ if format is valid

## Configuration File

The setup command manages `.env.local` in the project root:

### File Structure

```bash
# EDGAR CLI Environment Configuration

# OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-v1-1234567890abcdef...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Jina.ai API Configuration (optional)
JINA_API_KEY=jina_abc123def456...
JINA_BASE_URL=https://r.jina.ai

# SEC EDGAR API Configuration
EDGAR_USER_AGENT=John Doe john@example.com
EDGAR_API_BASE_URL=https://data.sec.gov
```

### Safety Features

1. **Preserves Comments**: Keeps all comment lines
2. **Preserves Other Variables**: Doesn't touch unrelated configuration
3. **Updates Only Changed Keys**: Replaces only specified keys
4. **Atomic Updates**: Writes entire file at once (no partial writes)

## Troubleshooting

### Validation Fails

```bash
# Skip validation if offline or testing
edgar-analyzer setup --key openrouter --value "test-key" --no-validate
```

### Update Isn't Applied

Check file permissions:
```bash
ls -la .env.local
# Should be writable: -rw-r--r--
```

### API Key Not Recognized

Verify the key is in the correct format:
- **OpenRouter**: Must start with `sk-or-v1-`
- **Jina**: Must start with `jina_`
- **EDGAR**: Must contain both name and email with `@`

### Configuration Not Loaded

Ensure `.env.local` is in the project root directory where you run the command:

```bash
pwd
# Should show: /path/to/edgar

ls -la .env.local
# Should exist in current directory
```

## Security Best Practices

1. **Never Commit `.env.local`**: It's gitignored by default
2. **Use Different Keys for Dev/Prod**: Separate keys for different environments
3. **Rotate Keys Regularly**: Update API keys periodically
4. **Limit Key Permissions**: Use API keys with minimal required permissions
5. **Monitor Key Usage**: Check API provider dashboards for unusual activity

## Integration with Other Commands

After setup, all EDGAR analyzer commands will use these API keys:

```bash
# Run analysis with configured keys
edgar-analyzer analyze --cik 0000320193 --year 2023

# Generate Fortune 500 report
edgar-analyzer fortune500 --year 2023 --limit 50

# All commands automatically load .env.local
```

## Advanced Usage

### Environment Variables

You can override `.env.local` with environment variables:

```bash
# Override OpenRouter key for single command
OPENROUTER_API_KEY="sk-or-v1-override" edgar-analyzer analyze --cik 0000320193

# Use different configuration file
cp .env.local .env.production
# Edit .env.production
# Load it: source .env.production (shell-specific)
```

### Scripting

Use non-interactive mode in scripts:

```bash
#!/bin/bash
# setup_edgar.sh

# Configure EDGAR analyzer
edgar-analyzer setup --key openrouter --value "$OPENROUTER_KEY" --no-validate
edgar-analyzer setup --key jina --value "$JINA_KEY" --no-validate
edgar-analyzer setup --key edgar --value "ScriptBot script@company.com" --no-validate

echo "Setup complete!"
```

### CI/CD Integration

```yaml
# .github/workflows/analysis.yml
- name: Configure EDGAR Analyzer
  run: |
    edgar-analyzer setup --key openrouter --value "${{ secrets.OPENROUTER_API_KEY }}" --no-validate
    edgar-analyzer setup --key edgar --value "CI Bot ci@company.com" --no-validate
```

## Testing

The setup command includes comprehensive test coverage:

```bash
# Run setup command tests
pytest tests/unit/test_setup_command.py -v

# Run integration tests
python tests/test_setup_integration.py
```

## See Also

- [Quick Start Guide](QUICK_START.md) - Get started with EDGAR Analyzer
- [CLI Usage Guide](CLI_USAGE.md) - Complete CLI reference
- [API Key Security](API_KEY_SECURITY.md) - Security best practices
- [Configuration Reference](../architecture/CONFIGURATION.md) - All configuration options
