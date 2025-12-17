# 🛡️ Security Prevention Guide - Never Leak Secrets Again

## 🚨 What Happened
- **Incident**: API keys were hardcoded in `railway-deploy.sh` and committed to git
- **Impact**: Google API key, Serper API key, and DataForSEO credentials exposed publicly
- **Root Cause**: Direct hardcoding of secrets in source files

## 🛡️ Prevention Layers (Multi-layer Defense)

### Layer 1: Pre-commit Hooks (Automatic Blocking)
✅ **Status**: Active - Will block commits with secrets

**What it blocks**:
- Google API keys (`AIza...`)
- OpenAI API keys (`sk-...`)
- GitLab tokens (`glpat-...`)
- GitHub tokens (`ghp_...`)
- Slack tokens (`xoxb-...`)

**Test it**:
```bash
echo "AIzaSyDEMO123456789" > test-secret.txt
git add test-secret.txt
git commit -m "test"
# Should be BLOCKED with error message
```

### Layer 2: Enhanced .gitignore
✅ **Status**: Updated - Blocks secret files

**What it ignores**:
- All `.env*` files  
- Secret directories (`**/secrets/**`, `**/credentials/**`)
- Key files (`*-key.json`, `*-credentials.json`)
- Deployment scripts with secrets (`*-with-keys.*`)

### Layer 3: Secure Development Practices

#### ✅ DO:
```bash
# Store in environment variables
export GEMINI_API_KEY="your-key-here"

# Use in code  
api_key = os.getenv("GEMINI_API_KEY")
```

#### ❌ DON'T:
```bash
# Never hardcode in files
GEMINI_API_KEY="AIzaSy..." # NEVER DO THIS!
```

### Layer 4: Railway Environment Variables
✅ **Status**: Configured

**Set securely**:
```bash
railway variables --set "GEMINI_API_KEY=your-new-key"
railway variables --set "SERPER_API_KEY=your-new-key"
```

**Never in code**:
```python
# ✅ GOOD
api_key = os.getenv("GEMINI_API_KEY")

# ❌ BAD  
api_key = "AIzaSy123..." 
```

## 🔍 Regular Security Checks

### Weekly:
```bash
# Scan for any missed secrets
git log --oneline -n 20 | xargs -I {} git show {} | grep -E "(AIza|sk-|glpat-)"

# Check current files
grep -r "AIza" . --exclude-dir=.git
```

### Before Each Deployment:
```bash
# Run pre-commit on all files
pre-commit run --all-files

# Double-check no secrets
railway variables | grep -E "(GEMINI|SERPER|DATAFORSEO)"
```

## 🚨 Emergency Response Plan

### If Secrets Are Leaked:

1. **IMMEDIATE (< 5 minutes)**:
   ```bash
   # Rotate ALL exposed keys
   # - Google Cloud Console
   # - Serper.dev dashboard  
   # - DataForSEO dashboard
   ```

2. **CLEAN GIT HISTORY (< 30 minutes)**:
   ```bash
   # Remove from history
   git filter-repo --replace-text <(echo "EXPOSED_KEY")
   git push origin main --force
   ```

3. **UPDATE PRODUCTION (< 60 minutes)**:
   ```bash
   # Set new keys in Railway
   railway variables --set "KEY_NAME=new-key"
   ```

## 📋 Security Checklist for Developers

Before every commit:
- [ ] No hardcoded API keys in any files
- [ ] Environment variables used for all secrets
- [ ] Pre-commit hooks are active (`pre-commit install`)
- [ ] Test deployment script works with env vars only
- [ ] No `.env` files with real secrets committed

Before every deployment:
- [ ] Railway environment variables are set
- [ ] Local `.env.local` contains only dev/test keys
- [ ] Production keys are rotated if not used in >90 days
- [ ] Deployment script has no hardcoded secrets

## 🔧 Tools and Commands

**Check for secrets**:
```bash
# Manual scan
grep -r -E "(AIza|sk-|glpat-|ghp_|xoxb-)" --include="*.py" --include="*.sh" .

# Pre-commit scan
pre-commit run detect-secrets --all-files
```

**Clean history** (if secrets found):
```bash
git filter-repo --replace-text <(echo "SECRET_TO_REMOVE") --force
```

**Secure deployment**:
```bash
# Use Railway vars (secure)
railway up

# Not direct export (insecure)
export SECRET=value && railway up  # DON'T DO THIS
```

## 📞 Security Contacts

- **Immediate escalation**: Federico De Ponte
- **Security scanning**: GitGuardian (already monitoring)
- **Cloud security**: Google Cloud Security Command Center

## 🏆 Success Metrics

- ✅ Zero secrets in git history
- ✅ Pre-commit hooks block 100% of secret commits
- ✅ All production keys in Railway environment only
- ✅ Weekly security scans show zero findings

---

**Remember: Security is everyone's responsibility. When in doubt, use environment variables!**