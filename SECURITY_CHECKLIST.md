# 🔒 Security Checklist for AI Document Assistant

## 🚨 CRITICAL: Secrets Management

### ✅ Before Every Commit:
- [ ] **NO API keys in code files**
- [ ] **NO passwords in configuration files**
- [ ] **NO JWT secrets in source code**
- [ ] **NO database credentials in code**
- [ ] **NO private keys or certificates**

### ✅ Environment Variables:
- [ ] Use `.env` files for local development
- [ ] Use environment variables in production
- [ ] Never commit `.env` files to git
- [ ] Use placeholder values in examples

### ✅ Configuration Files:
- [ ] Use `${VARIABLE_NAME:-default}` syntax in docker-compose
- [ ] Reference environment variables, don't hardcode
- [ ] Use strong, unique secrets for each environment

## 🔑 API Keys & Secrets

### OpenAI API:
- [ ] Store in environment variable: `OPENAI_API_KEY`
- [ ] Use placeholder in examples: `your-openai-api-key-here`
- [ ] Rotate keys regularly
- [ ] Monitor usage for unusual activity

### JWT Secrets:
- [ ] Generate strong, random secrets (64+ characters)
- [ ] Use different secrets for each environment
- [ ] Store in environment variable: `JWT_SECRET`
- [ ] Never commit actual secrets to git

### Database Credentials:
- [ ] Use environment variables for database URLs
- [ ] Use strong passwords
- [ ] Limit database access to application only
- [ ] Use connection pooling

## 🛡️ Security Best Practices

### Authentication:
- [ ] JWT tokens with proper expiration
- [ ] Secure password hashing (bcrypt)
- [ ] Rate limiting on auth endpoints
- [ ] Account lockout after failed attempts

### Data Protection:
- [ ] Input validation and sanitization
- [ ] SQL injection prevention (SQLAlchemy ORM)
- [ ] XSS protection
- [ ] CORS configuration
- [ ] HTTPS in production

### File Uploads:
- [ ] File type validation
- [ ] File size limits
- [ ] Virus scanning (if applicable)
- [ ] Secure file storage

## 🔍 Security Scanning

### Automated Checks:
- [ ] GitHub Actions security scanning
- [ ] Dependency vulnerability scanning
- [ ] Code quality checks
- [ ] Secret detection in CI/CD

### Manual Reviews:
- [ ] Code review for security issues
- [ ] Configuration file review
- [ ] Environment variable review
- [ ] Access control review

## 📋 Pre-Commit Checklist

```bash
# Check for exposed secrets
grep -r "sk-" . --exclude-dir=node_modules --exclude-dir=.git
grep -r "sk-proj-" . --exclude-dir=node_modules --exclude-dir=.git
grep -r "your-secret" . --exclude-dir=node_modules --exclude-dir=.git

# Check for hardcoded credentials
grep -r "password.*=" . --exclude-dir=node_modules --exclude-dir=.git
grep -r "api_key.*=" . --exclude-dir=node_modules --exclude-dir=.git

# Check for environment file commits
git status | grep ".env"
```

## 🚨 Emergency Response

### If Secrets Are Exposed:
1. **IMMEDIATELY revoke/rotate the exposed secret**
2. **Remove the secret from git history**
3. **Update all systems using the old secret**
4. **Investigate how the secret was exposed**
5. **Implement prevention measures**

### Git History Cleanup:
```bash
# Remove file from git history (use with caution)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch infra/docker-compose.yml' \
  --prune-empty --tag-name-filter cat -- --all

# Force push to remove from remote
git push origin --force --all
```

## 📚 Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Security Best Practices](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

## 🎯 Security Goals

- **Zero secrets in source code**
- **Environment-based configuration**
- **Regular security audits**
- **Automated vulnerability scanning**
- **Secure by default design**

---

**Remember: Security is everyone's responsibility. When in doubt, ask for a security review!** 🔒
