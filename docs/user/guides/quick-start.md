# Quick Start: Setup Command

**5-Minute Guide to API Key Configuration**

---

## 🚀 Quick Commands

### View Current Configuration

```bash
python -m edgar_analyzer setup
# Press 'n' to decline all reconfigurations
# This just shows your current status
```

### Update a Single Key (Non-Interactive)

```bash
# Update OpenRouter key
python -m edgar_analyzer setup \
  --key openrouter \
  --value YOUR_NEW_KEY_HERE \
  --no-validate

# Update Jina key
python -m edgar_analyzer setup \
  --key jina \
  --value YOUR_NEW_KEY_HERE \
  --no-validate

# Update EDGAR user agent
python -m edgar_analyzer setup \
  --key edgar \
  --value "Your Name your.email@example.com" \
  --no-validate
```

### Run Interactive Wizard

```bash
python -m edgar_analyzer setup
# Follow the prompts to configure all keys
```

---

## ✅ Your Current Configuration

Your `.env.local` already has these keys:

```
✅ OpenRouter: sk-or-v1-13358dd...8f55b5 (configured)
✅ Jina.ai:    jina_6b33070a6...MSBPJQ (configured)
✅ EDGAR:      YourCompany YourEmail@example.com (configured)
```

**All set!** No configuration needed unless you want to update keys.

---

## 🔐 Key Locations

Get your API keys from:

- **OpenRouter**: https://openrouter.ai/keys
- **Jina.ai**: https://jina.ai (optional)
- **EDGAR**: Your company name + email

---

## 📋 Common Tasks

### Test if Keys Work

```bash
# With validation (tests API connection)
python -m edgar_analyzer setup \
  --key openrouter \
  --value YOUR_KEY \
  --validate

# Output if valid:
# Testing openrouter... ✅
# ✅ OPENROUTER_API_KEY configured
```

### Update Multiple Keys

```bash
# Run wizard and update all at once
python -m edgar_analyzer setup

# Or run setup command multiple times
python -m edgar_analyzer setup --key openrouter --value KEY1 --no-validate
python -m edgar_analyzer setup --key jina --value KEY2 --no-validate
python -m edgar_analyzer setup --key edgar --value "Name email" --no-validate
```

### View Help

```bash
python -m edgar_analyzer setup --help
```

---

## 🎬 Demo

See all features in action:

```bash
python3 tests/demo_setup_command.py
```

---

## 📚 Full Documentation

- **Implementation Guide**: `docs/guides/SETUP_COMMAND_IMPLEMENTATION.md`
- **Summary**: `SETUP_COMMAND_SUMMARY.md`
- **Security Guide**: `docs/guides/API_KEY_SECURITY.md`

---

## 🆘 Troubleshooting

**Problem**: Command not found

```bash
# Solution: Make sure you're in the project directory
cd /Users/masa/Clients/Zach/projects/edgar
python -m edgar_analyzer setup
```

**Problem**: Validation fails

```bash
# Solution: Skip validation (still saves the key)
python -m edgar_analyzer setup --key openrouter --value YOUR_KEY --no-validate
```

**Problem**: Can't edit .env.local

```bash
# Solution: Check file permissions
ls -la .env.local
chmod 600 .env.local  # Make it readable/writable
```

---

**That's it!** Your setup command is ready to use. 🎉
