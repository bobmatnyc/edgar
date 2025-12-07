# 🔒 API Key Security Guide

Comprehensive guide for secure API key management in the EDGAR CLI system.

## 🎯 Security Status

### ✅ **Current Security Implementation**
- **API Key Location**: Stored in `.env.local` (gitignored)
- **Git Protection**: `.env.local` is properly gitignored and not tracked
- **Environment Loading**: Secure loading via python-dotenv
- **Key Validation**: Proper format validation and length checking

## 🔐 API Key Configuration

### **📋 Setup Process**
1. **Copy Template**: `cp .env.template .env.local`
2. **Add API Key**: Edit `.env.local` with your OpenRouter API key
3. **Verify Security**: Ensure `.env.local` is gitignored

### **🔧 Configuration Format**
```bash
# .env.local
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### **✅ Validation Commands**
```bash
# Check if API key is configured
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.local')
key = os.getenv('OPENROUTER_API_KEY')
print('✅ API Key configured' if key and key.startswith('sk-or-v1-') else '❌ API Key missing')
"

# Test API key functionality
python tests/test_centralized_openrouter.py
```

## 🛡️ Security Best Practices

### **🔒 File Security**
- **Never commit `.env.local`** - It's gitignored for security
- **Use different keys** for development, staging, and production
- **Rotate API keys regularly** for enhanced security
- **Set proper file permissions**: `chmod 600 .env.local`

### **🔐 Key Management**
- **Obtain keys from**: https://openrouter.ai/keys
- **Store securely**: Use environment variables or secure vaults in production
- **Monitor usage**: Track API usage and costs
- **Revoke compromised keys**: Immediately revoke if exposed

### **🚨 Security Checklist**
- [ ] `.env.local` exists and contains valid API key
- [ ] `.env.local` is gitignored and not tracked by git
- [ ] API key starts with `sk-or-v1-` (OpenRouter format)
- [ ] File permissions are restrictive (`600` or similar)
- [ ] No API keys in source code or documentation
- [ ] Different keys used for different environments

## 🔍 Security Validation

### **📊 Git Security Check**
```bash
# Verify .env.local is gitignored
git status --porcelain | grep .env.local
# Should return empty (no output)

# Verify .env.local is not tracked
git ls-files | grep .env.local
# Should return empty (no output)

# Check gitignore configuration
grep -n "\.env\.local" .gitignore
# Should show: .env.local
```

### **🔧 API Key Validation**
```bash
# Test API key format and functionality
source venv/bin/activate
python -c "
from src.edgar_analyzer.services.openrouter_service import OpenRouterService
import asyncio

async def test():
    try:
        service = OpenRouterService()
        response = await service.chat_completion(
            messages=[{'role': 'user', 'content': 'Test'}],
            model='x-ai/grok-4.1-fast:free',
            max_tokens=10
        )
        print('✅ API Key working:', len(response) > 0)
    except Exception as e:
        print('❌ API Key error:', str(e))

asyncio.run(test())
"
```

## 🚨 Security Incidents

### **🔴 If API Key is Exposed**
1. **Immediately revoke** the exposed key at https://openrouter.ai/keys
2. **Generate new key** and update `.env.local`
3. **Check usage logs** for unauthorized access
4. **Review git history** to ensure no keys were committed
5. **Update documentation** if exposure was through docs

### **🔧 Recovery Process**
```bash
# 1. Generate new API key from OpenRouter
# 2. Update .env.local
echo "OPENROUTER_API_KEY=sk-or-v1-new-key-here" > .env.local

# 3. Test new key
python tests/test_centralized_openrouter.py

# 4. Verify security
git status | grep .env.local  # Should be empty
```

## 📋 Environment Management

### **🔧 Development Environment**
```bash
# .env.local (development)
OPENROUTER_API_KEY=sk-or-v1-dev-key-here
DEBUG_MODE=true
LOG_LEVEL=DEBUG
```

### **🚀 Production Environment**
```bash
# Use environment variables or secure vault
export OPENROUTER_API_KEY=sk-or-v1-prod-key-here
export DEBUG_MODE=false
export LOG_LEVEL=WARNING
```

### **🧪 Testing Environment**
```bash
# .env.test (for CI/CD)
OPENROUTER_API_KEY=sk-or-v1-test-key-here
TEST_MODE=true
```

## 🎯 Compliance and Monitoring

### **📊 Usage Monitoring**
- Monitor API usage through OpenRouter dashboard
- Set up billing alerts for cost control
- Track request patterns for anomaly detection
- Regular security audits of key usage

### **📋 Compliance Requirements**
- Follow OpenRouter's terms of service
- Implement proper data handling procedures
- Maintain audit logs of API usage
- Regular security reviews and updates

## 🆘 Troubleshooting

### **Common Issues**
- **API Key Not Found**: Check `.env.local` exists and contains key
- **Invalid Key Format**: Ensure key starts with `sk-or-v1-`
- **Permission Denied**: Check file permissions on `.env.local`
- **Git Tracking**: Verify `.env.local` is in `.gitignore`

### **Debug Commands**
```bash
# Check environment loading
python -c "from dotenv import load_dotenv; load_dotenv('.env.local'); import os; print(os.getenv('OPENROUTER_API_KEY', 'NOT_FOUND')[:20])"

# Verify gitignore
git check-ignore .env.local  # Should output: .env.local

# Test API connectivity
edgar-analyzer --cli  # Should work without errors
```

---

**Secure API key management is critical for system security and operational integrity.** 🔒🛡️
