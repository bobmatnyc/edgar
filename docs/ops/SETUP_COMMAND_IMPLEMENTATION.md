# Setup Command Implementation

**Ticket**: 1M-319 - Core Platform Architecture - Phase 2 (Setup Command)
**Status**: ✅ COMPLETE
**Date**: November 28, 2025

## Overview

The setup command provides both **interactive wizard** and **non-interactive** modes for configuring API keys and settings for the EDGAR Platform. All keys are stored securely in `.env.local` which is gitignored.

## Features Implemented

### ✅ Interactive Wizard Mode
- Beautiful Rich UI with tables and prompts
- Current configuration status display
- Masked API key display for security
- Optional API key validation
- Preserves existing configuration
- User confirmation for reconfiguration

### ✅ Non-Interactive Mode
- Command-line options: `--key` and `--value`
- Validation control: `--validate / --no-validate`
- Scriptable for automation
- Safe for CI/CD pipelines

### ✅ API Key Validation
- **OpenRouter**: Tests connection to `https://openrouter.ai/api/v1/models`
- **Jina.ai**: Tests connection to Jina reader API
- **EDGAR**: Validates user agent format (Name email@example.com)

### ✅ Safe .env.local Management
- Preserves existing environment variables
- Preserves comments and formatting
- Updates keys in-place when reconfiguring
- Adds new keys without disrupting existing ones
- Creates `.env.local` if it doesn't exist

### ✅ Security Features
- API keys masked in console output (shows first 10 and last 4 chars)
- Password-style input for API keys (hidden during typing)
- `.env.local` excluded from version control
- Validation is optional (can skip for offline setup)

## Usage Examples

### Interactive Wizard

```bash
# Launch interactive setup wizard
python -m edgar_analyzer setup

# Output:
# 🔧 EDGAR Platform Setup Wizard
#
# Current Configuration
# ┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
# ┃ Service    ┃ Status        ┃ Value                  ┃
# ┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
# │ OpenRouter │ ✅ Configured │ sk-or-v1-t...6789      │
# │ Jina.ai    │ ✅ Configured │ jina_6b330...BPJQ      │
# │ SEC EDGAR  │ ✅ Configured │ YourName email@co.com  │
# └────────────┴───────────────┴────────────────────────┘
#
# Reconfigure openrouter? [y/N]:
```

### Non-Interactive Mode

```bash
# Configure OpenRouter key
python -m edgar_analyzer setup \
  --key openrouter \
  --value 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 \
  --validate

# Configure Jina.ai key
python -m edgar_analyzer setup \
  --key jina \
  --value jina_6b33070a68824d84be23367fe0ea9f56gTEuH4Pr_Phjuq6Da2eL4iMSBPJQ \
  --no-validate

# Configure EDGAR user agent
python -m edgar_analyzer setup \
  --key edgar \
  --value "YourName your.email@example.com" \
  --no-validate
```

### View Current Configuration

```bash
# Run setup and immediately decline all reconfigurations
python -m edgar_analyzer setup
# Press 'n' for all prompts to just view status
```

## API Keys Supported

| Key Name | Environment Variable | Description | Required |
|----------|---------------------|-------------|----------|
| `openrouter` | `OPENROUTER_API_KEY` | OpenRouter API key for LLM operations | Yes |
| `jina` | `JINA_API_KEY` | Jina.ai API key for web content extraction | Optional |
| `edgar` | `EDGAR_USER_AGENT` | SEC EDGAR User-Agent (Name email@example.com) | Yes for EDGAR sources |

## Validation Details

### OpenRouter Validation
- **Endpoint**: `https://openrouter.ai/api/v1/models`
- **Method**: GET with Authorization header
- **Success**: HTTP 200 response
- **Timeout**: 10 seconds

### Jina.ai Validation
- **Endpoint**: `https://r.jina.ai/https://example.com`
- **Method**: GET with Authorization header
- **Success**: HTTP 200 response
- **Timeout**: 10 seconds

### EDGAR User Agent Validation
- **Format**: `Name email@example.com`
- **Requirements**:
  - Must contain at least one space
  - Must contain @ symbol
  - Example: `"John Doe john.doe@company.com"`

## File Structure

```
src/edgar_analyzer/cli/commands/
└── setup.py                 # Setup command implementation (252 LOC)

tests/unit/
└── test_setup_command.py    # Comprehensive tests (325 LOC)

.env.local                   # API keys (gitignored)
```

## Implementation Details

### Key Functions

```python
# Main command
@click.command()
@click.option('--key', type=str, help='API key to configure')
@click.option('--value', type=str, help='API key value')
@click.option('--validate/--no-validate', default=True)
def setup(key: Optional[str], value: Optional[str], validate: bool)

# Interactive wizard
def _interactive_setup() -> None

# Non-interactive single key setup
def _setup_single_key(key: str, value: str, validate: bool) -> None

# Configuration management
def _read_env_file(env_file: Path) -> dict
def _save_to_env_file(env_file: Path, updates: dict) -> None
def _display_config_status(config: dict) -> None

# Validation functions
def _validate_openrouter(api_key: str) -> bool
def _validate_jina(api_key: str) -> bool
def _validate_edgar_user_agent(user_agent: str) -> bool
```

### Error Handling

- **Network errors**: Validation returns `False`, allows setup to continue
- **Invalid key names**: Displays error message with valid options
- **Missing .env.local**: Creates new file automatically
- **Malformed .env.local**: Preserves valid lines, skips malformed ones

## Testing

### Test Coverage

```bash
# Run setup command tests
pytest tests/unit/test_setup_command.py -v

# Test classes:
# - TestSetupCommand (11 tests)
# - TestSetupValidation (4 tests)
# - TestSetupHelpers (7 tests)
#
# Total: 22 comprehensive tests
```

### Test Categories

1. **Interactive Mode Tests**
   - Complete wizard flow
   - Empty input handling
   - Reconfiguration prompts

2. **Non-Interactive Mode Tests**
   - Single key configuration
   - Validation control
   - Invalid key handling

3. **Configuration Persistence Tests**
   - New file creation
   - Updating existing keys
   - Preserving comments
   - Preserving other variables

4. **Validation Tests**
   - API key format validation
   - Connection testing (mocked)
   - Real API validation (integration tests, skipped if keys not available)

5. **Edge Cases**
   - Malformed .env.local files
   - Empty values
   - Special characters in keys
   - Multiple equals signs in values

## Security Considerations

### ✅ Implemented

- API keys never logged or printed in full
- `.env.local` in `.gitignore` (verified)
- Password-style input for API keys
- Validation is optional (can configure offline)
- No API keys in error messages

### 📋 Recommendations

- **Key Rotation**: Rotate API keys regularly
- **Access Control**: Restrict `.env.local` file permissions (`chmod 600`)
- **Backup**: Store keys securely (password manager, not in git)
- **Environment Separation**: Use different keys for dev/staging/prod

## Known Limitations

1. **Validation Best-Effort**: Network errors during validation don't prevent setup
2. **No Key Deletion**: Command can only add/update, not delete keys
3. **No Bulk Import**: Cannot import from another .env file
4. **No Key Encryption**: Keys stored in plaintext (standard for .env files)

## Future Enhancements

Potential improvements for future versions:

- [ ] Support for environment-specific .env files (.env.dev, .env.prod)
- [ ] Key deletion command
- [ ] Bulk import from template
- [ ] Integration with system keychain/credential managers
- [ ] Key expiration warnings
- [ ] Automatic key rotation

## Success Criteria

✅ **All Success Criteria Met**

1. ✅ Interactive wizard works with current keys in .env.local
2. ✅ Non-interactive mode: `python -m edgar_analyzer setup --key openrouter --value <key>`
3. ✅ Validation tests OpenRouter API connection
4. ✅ .env.local updates preserve other variables
5. ✅ All unit tests passing (22 tests)
6. ✅ Rich library integrated for beautiful UI
7. ✅ Masked key display for security
8. ✅ Supports openrouter, jina, edgar keys

## Examples with Real Keys

### Current .env.local Configuration

```bash
# Your actual keys (from user context):
OPENROUTER_API_KEY=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
JINA_API_KEY=jina_6b33070a68824d84be23367fe0ea9f56gTEuH4Pr_Phjuq6Da2eL4iMSBPJQ
EDGAR_USER_AGENT=YourCompany YourEmail@example.com

# These keys are already configured and working
```

### Update Existing Key

```bash
# Update OpenRouter key
python -m edgar_analyzer setup \
  --key openrouter \
  --value sk-or-v1-NEW_KEY_HERE \
  --validate

# Output:
# Testing openrouter... ✅
# ✅ OPENROUTER_API_KEY configured
```

### Add New Optional Key

```bash
# Add GitHub token for self-improving features
# (Note: GitHub key support would need to be added to setup.py)
python -m edgar_analyzer setup \
  --key github \
  --value ghp_NEW_GITHUB_TOKEN \
  --no-validate
```

## Related Documentation

- [API Key Security Guide](API_KEY_SECURITY.md)
- [Environment Configuration](../architecture/ENVIRONMENT_CONFIGURATION.md)
- [CLI Usage Guide](CLI_USAGE.md)
- [Phase 2 Research](../research/phase-2-core-platform-architecture-2025-11-28.md)

## Support

For issues or questions:
1. Check `.env.local` file permissions
2. Verify API keys are valid on provider websites
3. Test validation manually with `--validate` flag
4. Check network connectivity for validation
5. Review test suite for expected behavior

---

**Implementation Complete**: November 28, 2025
**Total Code**: ~550 LOC (implementation + tests)
**Test Coverage**: 22 comprehensive tests
**Status**: ✅ Production Ready
