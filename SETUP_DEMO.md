# Setup Command - Visual Demo

## What You'll See

### 1. Interactive Wizard Mode

```bash
$ edgar-analyzer setup
```

**Output:**

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
Enter OpenRouter API Key: ●●●●●●●●●●●●●●●●●●●●●●●●

Jina.ai API Key (optional)
Get your key from https://jina.ai
Enter Jina.ai API Key (optional): ●●●●●●●●●●●●●●●●

SEC EDGAR User Agent
Format: YourName email@example.com
Enter SEC EDGAR User Agent: John Doe john.doe@company.com

Validate API keys? [Y/n]: y

Validating API keys...
Testing openrouter... ✅
Testing jina... ✅
Testing edgar... ✅

✅ Configuration saved to .env.local
```

### 2. Non-Interactive Mode

```bash
$ edgar-analyzer setup --key openrouter --value "sk-or-v1-abc123..."
```

**Output:**

```
✅ OPENROUTER_API_KEY configured
```

### 3. With Validation

```bash
$ edgar-analyzer setup --key openrouter --value "sk-or-v1-real-key"
```

**Output:**

```
Testing openrouter... ✅
✅ OPENROUTER_API_KEY configured
```

### 4. Update Existing Configuration

```bash
$ edgar-analyzer setup
```

**Output (when keys already configured):**

```
🔧 EDGAR Platform Setup Wizard

Current Configuration
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Service    ┃ Status          ┃ Value                          ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ OpenRouter │ ✅ Configured    │ sk-or-v1-1...f55b5             │
│ Jina.ai    │ ✅ Configured    │ jina_6b330...BPJQ              │
│ SEC EDGAR  │ ✅ Configured    │ John Doe john@company.com      │
└────────────┴─────────────────┴────────────────────────────────┘

Reconfigure openrouter? [y/N]: n
Reconfigure jina? [y/N]: n
Reconfigure edgar? [y/N]: n

No changes made
```

### 5. Error Handling

```bash
$ edgar-analyzer setup --key invalid_key --value "test"
```

**Output:**

```
❌ Unknown key: invalid_key
Valid keys: openrouter, jina, edgar
```

## File Created

After running setup, `.env.local` is created/updated:

```bash
$ cat .env.local
```

**Content:**

```bash
# EDGAR CLI Environment Configuration

OPENROUTER_API_KEY=sk-or-v1-abc123def456...
JINA_API_KEY=jina_xyz789...
EDGAR_USER_AGENT=John Doe john.doe@company.com
```

## Security Features

### Masked Input (Interactive Mode)

When entering API keys:
```
Enter OpenRouter API Key: ●●●●●●●●●●●●●●●●
```

### Masked Display (Status Table)

When showing existing configuration:
```
│ OpenRouter │ ✅ Configured │ sk-or-v1-1...f55b5 │
```

Only first 10 and last 4 characters shown.

## Help Command

```bash
$ edgar-analyzer setup --help
```

**Output:**

```
Usage: setup [OPTIONS]

  Configure API keys and settings for the platform.

Options:
  --key TEXT                  API key to configure (openrouter, jina, edgar)
  --value TEXT                API key value (non-interactive mode)
  --validate / --no-validate  Validate API key
  --help                      Show this message and exit.
```

## Common Workflows

### First-Time Setup (Recommended)

```bash
# 1. Run interactive wizard
edgar-analyzer setup

# 2. Enter all keys when prompted

# 3. Validation runs automatically

# 4. Ready to use!
```

### Quick Update (Single Key)

```bash
# Update just one key
edgar-analyzer setup --key openrouter --value "new-key"
```

### CI/CD Setup (Skip Validation)

```bash
# In CI/CD pipeline
edgar-analyzer setup --key openrouter --value "$OPENROUTER_KEY" --no-validate
edgar-analyzer setup --key edgar --value "CI Bot ci@company.com" --no-validate
```

### Development Setup

```bash
# Interactive for dev environment
edgar-analyzer setup

# Then verify
cat .env.local | grep -E "OPENROUTER_API_KEY|JINA_API_KEY|EDGAR_USER_AGENT"
```

## Troubleshooting

### API Key Validation Fails

```bash
# Skip validation during setup
edgar-analyzer setup --key openrouter --value "..." --no-validate

# Test later manually
curl -H "Authorization: Bearer sk-or-v1-..." https://openrouter.ai/api/v1/models
```

### File Not Created

```bash
# Check current directory
pwd

# Should be in project root
# If not, cd to project root first
cd /path/to/edgar

# Then run setup
edgar-analyzer setup
```

### Permissions Error

```bash
# Check file permissions
ls -la .env.local

# If needed, fix permissions
chmod 644 .env.local
```

## Next Steps

After setup completes:

1. **Verify Configuration**:
   ```bash
   cat .env.local
   ```

2. **Test with Analysis**:
   ```bash
   edgar-analyzer analyze --cik 0000320193 --year 2023
   ```

3. **Run Fortune 500 Report**:
   ```bash
   edgar-analyzer fortune500 --year 2023 --limit 10
   ```

4. **Check Quality**:
   ```bash
   edgar-analyzer quality-test --year 2023 --limit 5
   ```

## Documentation

- **Full Guide**: [docs/guides/SETUP_COMMAND.md](docs/guides/SETUP_COMMAND.md)
- **Quick Start**: [SETUP_QUICK_START.md](SETUP_QUICK_START.md)
- **Implementation**: [SETUP_COMMAND_IMPLEMENTATION.md](SETUP_COMMAND_IMPLEMENTATION.md)
