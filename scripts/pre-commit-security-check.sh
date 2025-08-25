#!/bin/bash

# Pre-commit Security Check Script
# This script checks for potential security issues before committing

echo "🔒 Running pre-commit security checks..."

# Check for exposed API keys (using a different pattern to avoid self-reference)
if grep -r "sk-proj" . --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv --exclude-dir=__pycache__ --exclude=SECURITY_CHECKLIST.md --exclude=scripts/pre-commit-security-check.sh | grep -v "pre-commit-security-check.sh" > /dev/null 2>&1; then
    echo "❌ CRITICAL: OpenAI API key found in code!"
    echo "   Please remove the API key before committing."
    exit 1
fi

# Check for hardcoded secrets (using a different pattern)
if grep -r "your-secret-key" . --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv --exclude-dir=__pycache__ --exclude=SECURITY_CHECKLIST.md --exclude=scripts/pre-commit-security-check.sh | grep -v "pre-commit-security-check.sh" > /dev/null 2>&1; then
    echo "❌ WARNING: Hardcoded secret placeholder found!"
    echo "   Please replace with environment variable references."
    exit 1
fi

# Check for .env files being committed (only added/modified, not deleted)
if git status --porcelain | grep -E "^[AM].*\.env" > /dev/null 2>&1; then
    echo "❌ CRITICAL: .env file detected in git staging!"
    echo "   Please remove .env files from staging area."
    exit 1
fi

echo "✅ Security checks passed!"
exit 0
