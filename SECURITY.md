# 🔒 Security Guidelines for EDGAR CLI

## 🚨 CRITICAL SECURITY INCIDENT - RESOLVED

**Date**: 2025-11-21  
**Issue**: OpenRouter API key accidentally exposed in public repository  
**Status**: ✅ **RESOLVED**

### What Happened
- An OpenRouter API key (ending in ...fcd3) was accidentally committed to the public GitHub repository
- The key was found in `.env.local` file in commit `bd5f893`
- OpenRouter automatically detected the exposure and disabled the key

### Immediate Actions Taken
1. ✅ **Key Disabled**: OpenRouter automatically disabled the exposed key
2. ✅ **File Removed**: Removed `.env.local` from repository
3. ✅ **Gitignore Added**: Added comprehensive `.gitignore` to prevent future exposure
4. ✅ **History Updated**: Pushed security fixes to GitHub

### Required Next Steps
1. **Generate New API Key**: Visit https://openrouter.ai/keys to create a new key
2. **Update Local Configuration**: Add new key to local `.env.local` file (now gitignored)
3. **Update Applications**: Replace old key in any deployed applications

---

## 🛡️ Security Best Practices

### **API Key Management**

#### **✅ DO:**
- Store API keys in `.env.local` or `.env` files (gitignored)
- Use environment variables for sensitive configuration
- Rotate API keys regularly
- Use different keys for development, staging, and production
- Monitor for exposed keys using tools like GitHub secret scanning

#### **❌ DON'T:**
- Commit API keys to version control
- Share API keys in chat, email, or documentation
- Use production keys in development environments
- Hard-code API keys in source code
- Store keys in configuration files that get committed

### **Environment Configuration**

#### **Proper Setup:**
```bash
# 1. Copy the template
cp .env.template .env.local

# 2. Add your actual API key
echo "OPENROUTER_API_KEY=your_new_key_here" >> .env.local

# 3. Verify it's gitignored
git status  # Should not show .env.local
```

#### **File Structure:**
```
.env.template     # Template with placeholder values (committed)
.env.local        # Your actual keys (gitignored)
.env              # Alternative name (gitignored)
.env.production   # Production keys (gitignored)
```

### **Code Security**

#### **Sensitive Data Handling:**
```python
# ✅ GOOD: Use environment variables
import os
api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable required")

# ❌ BAD: Hard-coded keys
api_key = "sk-or-v1-84e3b1f192530465..."  # NEVER DO THIS
```

#### **Logging Security:**
```python
# ✅ GOOD: Mask sensitive data in logs
logger.info("API request", key_suffix=api_key[-4:])

# ❌ BAD: Log full keys
logger.info("Using API key", key=api_key)  # NEVER DO THIS
```

---

## 🔍 Security Monitoring

### **Automated Checks**
- GitHub secret scanning (enabled)
- Pre-commit hooks for sensitive file detection
- Regular security audits of dependencies

### **Manual Reviews**
- Code review for security implications
- Regular API key rotation
- Access control reviews

---

## 🚨 Incident Response

### **If You Accidentally Expose a Key:**

1. **Immediate Actions:**
   ```bash
   # Remove the file
   git rm sensitive_file
   git commit -m "SECURITY: Remove exposed credentials"
   
   # Add to gitignore
   echo "sensitive_file" >> .gitignore
   git add .gitignore
   git commit -m "SECURITY: Add sensitive files to gitignore"
   
   # Force push to update GitHub
   git push --force-with-lease origin main
   ```

2. **Rotate Credentials:**
   - Immediately disable/rotate the exposed key
   - Generate new credentials
   - Update all applications using the old key

3. **Notify Team:**
   - Alert team members about the exposure
   - Document the incident and resolution
   - Review processes to prevent recurrence

### **Emergency Contacts**
- OpenRouter Support: support@openrouter.ai
- Security Team: [Your security contact]

---

## 📋 Security Checklist

### **Before Each Commit:**
- [ ] No API keys in files being committed
- [ ] Sensitive files are gitignored
- [ ] No hard-coded credentials in code
- [ ] Environment variables used for configuration

### **Before Each Release:**
- [ ] Security review of new code
- [ ] Dependency security audit
- [ ] API key rotation if needed
- [ ] Access control review

### **Monthly Security Tasks:**
- [ ] Review and rotate API keys
- [ ] Update dependencies with security patches
- [ ] Review access logs and permissions
- [ ] Update security documentation

---

## 🔗 Resources

- [OpenRouter API Keys](https://openrouter.ai/keys)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [Git Security Best Practices](https://git-scm.com/book/en/v2/Git-Tools-Credential-Storage)
- [Environment Variable Security](https://12factor.net/config)

---

## 📞 Support

If you discover a security vulnerability or have security concerns:

1. **Do NOT** create a public issue
2. Contact the security team directly
3. Provide detailed information about the vulnerability
4. Allow time for proper remediation before disclosure

**Remember: Security is everyone's responsibility!** 🛡️
