# Railway Deployment Guide

This guide will help you deploy OpenBlog to Railway.

## Prerequisites

1. A Railway account ([railway.app](https://railway.app))
2. GitHub repository with your code
3. API keys ready (see Environment Variables below)

## Quick Deploy

### Option 1: Deploy from GitHub (Recommended)

1. **Connect Repository**
   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `openblog` repository

2. **Configure Environment Variables**
   - In your Railway project, go to "Variables" tab
   - Add the required variables (see below)

3. **Deploy**
   - Railway will automatically detect the Python project
   - It will use `Procfile` or `railway.json` for the start command
   - Deployment will start automatically

### Option 2: Deploy via Railway CLI

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to existing project (or create new)
railway link

# Deploy
railway up
```

## Environment Variables

Add these in Railway Dashboard → Variables:

### Required

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### Optional

```bash
# DataForSEO fallback (when Google Search quota exhausted)
DATAFORSEO_LOGIN=your_email
DATAFORSEO_PASSWORD=your_password

# Google Drive integration
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
GOOGLE_DELEGATION_SUBJECT=user@domain.com

# Supabase storage (if using)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJxxxxx

# OpenRouter (alternative to Gemini)
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

## Configuration Files

The following files are configured for Railway:

- **`railway.json`** - Railway-specific configuration
- **`Procfile`** - Process file (Railway will use this)
- **`runtime.txt`** - Python version specification
- **`nixpacks.toml`** - Build configuration (handles Playwright)

## Build Process

Railway will:

1. Detect Python project from `requirements.txt`
2. Install Python 3.11 (from `runtime.txt`)
3. Install dependencies from `requirements.txt`
4. Install Playwright Chromium browser (required for HTML to PNG)
5. Start the FastAPI server using the Procfile command

## Start Command

The app starts with:
```bash
uvicorn service.api:app --host 0.0.0.0 --port $PORT
```

Railway automatically sets `$PORT` environment variable.

## Health Check

Railway will check:
- `GET /health` endpoint (should return 200)

## Troubleshooting

### Build Fails

**Issue**: Git dependency (`openfigma`) fails to install
- **Solution**: Ensure Railway has access to the GitHub repository
- Or: Fork `openfigma` to a public repo Railway can access

**Issue**: Playwright installation fails
- **Solution**: Check `nixpacks.toml` - it should install Chromium automatically
- If issues persist, Railway may need additional system dependencies

### Runtime Errors

**Issue**: `ModuleNotFoundError`
- **Solution**: Check `requirements.txt` includes all dependencies
- Verify the git dependency URL is accessible

**Issue**: Port binding errors
- **Solution**: Ensure using `$PORT` environment variable (already configured)

**Issue**: Playwright browser not found
- **Solution**: Verify `playwright install chromium` runs during build
- Check build logs for Playwright installation

### API Errors

**Issue**: `GEMINI_API_KEY` not found
- **Solution**: Add environment variable in Railway Dashboard → Variables
- Ensure variable name matches exactly (case-sensitive)

## Monitoring

### View Logs

```bash
# Via CLI
railway logs

# Via Dashboard
# Go to your project → Deployments → Click on deployment → View logs
```

### Check Health

```bash
# Get your Railway URL
railway domain

# Test health endpoint
curl https://your-app.railway.app/health
```

## Scaling

Railway automatically scales based on traffic. For high-traffic scenarios:

1. **Upgrade Plan**: Railway Pro plan for better performance
2. **Resource Limits**: Adjust in Railway Dashboard → Settings
3. **Concurrency**: The FastAPI app handles concurrent requests automatically

## Cost Optimization

- **Free Tier**: 500 hours/month, $5 credit
- **Hobby Plan**: $5/month for more resources
- **Pro Plan**: $20/month for production workloads

## Custom Domain

1. Go to Railway Dashboard → Settings → Domains
2. Add your custom domain
3. Configure DNS records as instructed
4. Railway will provision SSL automatically

## Updates

Railway automatically redeploys when you push to your connected branch:

```bash
git push origin main
```

Railway will detect the push and trigger a new deployment.

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: GitHub Issues

## Verification

After deployment, test the API:

```bash
# Get your Railway URL
RAILWAY_URL=$(railway domain)

# Test health
curl $RAILWAY_URL/health

# Test blog generation
curl -X POST $RAILWAY_URL/blog/write \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "AI automation",
    "company_url": "https://example.com"
  }'
```

---

**Ready to deploy?** Connect your GitHub repo to Railway and add your environment variables!

