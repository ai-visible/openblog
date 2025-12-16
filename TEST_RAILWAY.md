# 🧪 Testing Railway Deployment

## Quick Test Guide

### Step 1: Get Your Railway URL

**Option A: From Railway Dashboard**
1. Go to Railway Dashboard → Your Project → Settings
2. Go to "Domains" tab
3. Copy your Railway URL (e.g., `https://openblog-production.up.railway.app`)

**Option B: Via Railway CLI**
```bash
railway domain
```

### Step 2: Test Health Endpoint

```bash
# Replace with your Railway URL
curl https://your-app.railway.app/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "blog-writer",
  "version": "1.0.0",
  "timestamp": "2025-12-16T..."
}
```

### Step 3: Test API Endpoints

#### Health Check
```bash
curl https://your-app.railway.app/health
```

#### View API Documentation
Open in browser:
- **Swagger UI**: `https://your-app.railway.app/docs`
- **ReDoc**: `https://your-app.railway.app/redoc`

#### Test Blog Generation (requires GEMINI_API_KEY)
```bash
curl -X POST https://your-app.railway.app/blog/write \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "AI automation",
    "company_url": "https://example.com"
  }'
```

**Note:** This will fail if `GEMINI_API_KEY` isn't set in Railway Variables.

### Step 4: Automated Test Script

Use the provided test script:

```bash
./test_railway_deployment.sh https://your-app.railway.app
```

## Common Issues

### ❌ Health Check Returns 502/503
- **Cause**: App might still be starting
- **Fix**: Wait 30-60 seconds and retry

### ❌ Health Check Returns 404
- **Cause**: Wrong URL or app not deployed
- **Fix**: Check Railway Dashboard → Deployments

### ❌ Blog Write Returns 500
- **Cause**: Missing `GEMINI_API_KEY` environment variable
- **Fix**: Add `GEMINI_API_KEY` in Railway Dashboard → Variables

### ❌ Connection Refused
- **Cause**: Service might not be exposed
- **Fix**: Check Railway Dashboard → Settings → Generate Domain

## Full API Test

### Test All Endpoints

```bash
RAILWAY_URL="https://your-app.railway.app"

# 1. Health
echo "Testing health..."
curl "$RAILWAY_URL/health"

# 2. API Docs
echo "Opening docs..."
open "$RAILWAY_URL/docs"  # macOS
# xdg-open "$RAILWAY_URL/docs"  # Linux

# 3. Blog Write (if API key is set)
echo "Testing blog write..."
curl -X POST "$RAILWAY_URL/blog/write" \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "test keyword",
    "company_url": "https://example.com",
    "word_count": 1000
  }'
```

## Verify Environment Variables

Make sure these are set in Railway Dashboard → Variables:

- ✅ `GEMINI_API_KEY` (required)
- ⚠️ `DATAFORSEO_LOGIN` (optional)
- ⚠️ `DATAFORSEO_PASSWORD` (optional)
- ⚠️ `GOOGLE_SERVICE_ACCOUNT_JSON` (optional)
- ⚠️ `SUPABASE_URL` (optional)

## Success Indicators

✅ Health endpoint returns 200 OK  
✅ `/docs` shows Swagger UI  
✅ Blog write endpoint accepts requests (may return error without API key, but should respond)  
✅ No 502/503 errors after 1 minute  

---

**Your app is live! 🎉**

