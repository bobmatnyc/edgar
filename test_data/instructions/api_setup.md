# API Setup Instructions - Alpha Testing

**Required for**: Code generation, Weather API scenario
**Time**: ~5 minutes per API key
**Cost**: Free tier available for all services

---

## OpenRouter API Key (REQUIRED)

**Purpose**: AI code generation (Sonnet 4.5)
**Cost**: Free tier available (~$5 credit), $0.10-$0.20 per generation
**Required for**: All scenarios involving code generation

### Setup Steps

1. **Sign Up**
   - Visit: https://openrouter.ai/
   - Click "Sign in" in top-right corner
   - Choose sign-in method (Google, GitHub, or email)

2. **Get API Key**
   - After sign-in, click profile icon → "API Keys"
   - Click "Create Key" button
   - Give it a name: "Edgar Platform Testing"
   - Copy the API key (starts with `sk-or-v1-...`)
   - **Important**: Save this key - you can't view it again!

3. **Add Credits** (if needed)
   - Free tier includes ~$5 credit for testing
   - If needed, click "Add Credits" → Add $10 (recommended)
   - This is enough for 50-100 code generations

4. **Configure in .env.local**
   ```bash
   # Open .env.local in your editor
   nano .env.local  # or vim, code, etc.

   # Add this line:
   OPENROUTER_API_KEY=sk-or-v1-your-key-here

   # Save and exit
   ```

5. **Test Connection**
   ```bash
   python -m edgar_analyzer setup test
   ```

   **Expected Output**:
   ```
   Testing OpenRouter connection...
   ✓ API key found
   ✓ Connection successful
   ✓ Model access verified: anthropic/claude-sonnet-4.5
   ```

### Troubleshooting

**Error: "API key not found"**
- Check `.env.local` exists in project root
- Verify key starts with `sk-or-v1-`
- No quotes around the key value
- No spaces before or after the key

**Error: "Invalid API key"**
- Copy the key again from OpenRouter dashboard
- Ensure you copied the complete key (often very long)
- Check for extra characters at beginning/end

**Error: "Insufficient credits"**
- Add credits at https://openrouter.ai/credits
- $10 is sufficient for full alpha testing

---

## OpenWeatherMap API Key (OPTIONAL)

**Purpose**: Weather data extraction (Scenario 3 only)
**Cost**: Free tier (60 calls/minute, 1M calls/month)
**Required for**: Scenario 3 (Weather API Integration)

### Setup Steps

1. **Sign Up**
   - Visit: https://openweathermap.org/api
   - Click "Sign Up" button
   - Fill out registration form
   - Verify your email address

2. **Get API Key**
   - After email verification, log in
   - Go to "API keys" tab in your account
   - Default API key is already created
   - Or click "Generate" to create new key
   - Copy the API key (32-character hex string)
   - **Note**: New keys take 10-20 minutes to activate

3. **Configure in .env.local**
   ```bash
   # Add this line to .env.local:
   OPENWEATHERMAP_API_KEY=your_32_character_key_here
   ```

4. **Test API Key** (wait 10-20 minutes after creation)
   ```bash
   # Test with curl
   curl "https://api.openweathermap.org/data/2.5/weather?q=London&appid=YOUR_API_KEY"

   # Or use the platform
   python -m edgar_analyzer setup validate-keys
   ```

   **Expected**: JSON response with weather data

### Free Tier Limits

- **Calls per minute**: 60
- **Calls per month**: 1,000,000
- **Data**: Current weather only (no forecasts)

**More than enough for testing!**

### Troubleshooting

**Error: "Invalid API key"**
- Wait 10-20 minutes after key creation
- Check you copied the correct key from dashboard
- Verify key is 32 characters (alphanumeric)

**Error: "Rate limit exceeded"**
- Free tier: max 60 calls/minute
- Wait 1 minute and retry
- For testing, this should never happen

---

## Jina.ai Reader API Key (OPTIONAL)

**Purpose**: Web scraping and content extraction
**Cost**: Free tier available (1M tokens/month)
**Required for**: Advanced web scraping scenarios (not in alpha scenarios)

### Setup Steps

1. **Sign Up**
   - Visit: https://jina.ai/reader
   - Click "Get Started" or "Sign Up"
   - Use Google, GitHub, or email

2. **Get API Key**
   - After sign-in, go to dashboard
   - Find "API Keys" section
   - Click "Create New Key"
   - Name it: "Edgar Platform Testing"
   - Copy the Bearer token

3. **Configure in .env.local**
   ```bash
   # Add this line to .env.local:
   JINA_API_KEY=your_bearer_token_here
   ```

4. **Test API Key**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     "https://r.jina.ai/https://example.com"
   ```

### Free Tier Limits

- **Tokens per month**: 1,000,000 (very generous)
- **Rate limit**: 200 requests/minute
- **Features**: Full access to Reader API

**Note**: Jina.ai is NOT required for alpha testing scenarios. This is for advanced use cases only.

---

## Configuration Summary

After completing API setups, your `.env.local` should look like:

```bash
# .env.local

# Required for code generation (all scenarios)
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key-here

# Optional - for Weather API scenario
OPENWEATHERMAP_API_KEY=your_32_character_key_here

# Optional - for advanced web scraping (not in alpha scenarios)
JINA_API_KEY=your_jina_bearer_token_here

# Platform configuration (defaults shown)
LOG_LEVEL=INFO
EDGAR_RATE_LIMIT_DELAY=0.1
```

---

## Verification

**Test all API keys at once**:

```bash
python -m edgar_analyzer setup validate-keys
```

**Expected Output**:
```
Validating API keys...

✓ OpenRouter API Key: Valid
  - Model access: anthropic/claude-sonnet-4.5
  - Credits remaining: $4.85

✓ OpenWeatherMap API Key: Valid (or "Not configured")
  - Tier: Free
  - Calls remaining today: 60

✓ Jina.ai API Key: Valid (or "Not configured")
  - Tier: Free
  - Tokens remaining: 1,000,000

All required API keys are configured correctly!
```

---

## Cost Estimate for Alpha Testing

**OpenRouter** (Required):
- Free tier: $5 credit included
- Cost per generation: ~$0.10-$0.20
- Alpha testing needs: ~10-20 generations
- **Total**: $2-$4 (covered by free tier)

**OpenWeatherMap** (Optional):
- Free tier: 1M calls/month
- Alpha testing needs: ~5-10 calls
- **Total**: $0 (completely free)

**Jina.ai** (Optional):
- Free tier: 1M tokens/month
- Alpha testing needs: Not used in alpha scenarios
- **Total**: $0 (not needed)

**Grand Total**: $0-$4 (OpenRouter free tier may cover all)

---

## Security Best Practices

### DO ✅

- Store API keys in `.env.local` (gitignored)
- Never commit API keys to git
- Use environment variables for keys
- Rotate keys after testing (if shared)

### DON'T ❌

- Hardcode keys in Python files
- Share keys in Slack/email
- Commit `.env.local` to git
- Use production keys for testing

### If You Accidentally Expose a Key

1. **Immediately revoke** the key in the service dashboard
2. **Generate new key**
3. **Update .env.local** with new key
4. **Check git history** - if committed, rewrite history or rotate

---

## Support

**Issues with API Setup?**

- **Slack**: #edgar-alpha-testing
- **Email**: edgar-support@example.com
- **Documentation**: See User Testing Guide for troubleshooting

**Common Questions**:

**Q: Do I need all API keys?**
A: Only OpenRouter is required. OpenWeatherMap is optional (for Scenario 3 only).

**Q: What if I run out of OpenRouter credits?**
A: Add $10 credits - that's enough for 50-100 generations (way more than testing needs).

**Q: Can I share my API key with other testers?**
A: No - each tester should get their own key. Keys can track usage and have rate limits.

**Q: How do I know if my key is working?**
A: Run `python -m edgar_analyzer setup test` - it will verify OpenRouter connection.

---

**Document Version**: 1.0
**Last Updated**: 2025-12-04
**Maintained By**: Platform Development Team
