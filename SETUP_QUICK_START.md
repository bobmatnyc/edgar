# Setup Command - Quick Start

## TL;DR

```bash
# Run interactive setup wizard
edgar-analyzer setup

# Or configure keys directly
edgar-analyzer setup --key openrouter --value "sk-or-v1-..."
edgar-analyzer setup --key jina --value "jina_..."
edgar-analyzer setup --key edgar --value "YourName email@example.com"
```

## What It Does

Configures API keys and saves them to `.env.local`:
- **OpenRouter** (required): LLM provider for data extraction
- **Jina.ai** (optional): Web content extraction
- **EDGAR User Agent** (required): SEC API identification

## Quick Examples

### First Time Setup

```bash
# Interactive wizard (recommended)
edgar-analyzer setup
```

### Update Single Key

```bash
# Update OpenRouter key
edgar-analyzer setup --key openrouter --value "sk-or-v1-new-key"
```

### Skip Validation (Faster)

```bash
# Don't test connection (useful for CI/CD)
edgar-analyzer setup --key openrouter --value "..." --no-validate
```

## Where to Get Keys

- **OpenRouter**: https://openrouter.ai/keys
- **Jina.ai**: https://jina.ai
- **EDGAR**: Use your name and email (e.g., "John Doe john@company.com")

## File Location

Configuration saved to: `.env.local` (project root)

## Verify Setup

```bash
# Check if .env.local exists and has keys
cat .env.local | grep -E "OPENROUTER_API_KEY|JINA_API_KEY|EDGAR_USER_AGENT"
```

## Full Documentation

See: [docs/guides/SETUP_COMMAND.md](docs/guides/SETUP_COMMAND.md)
