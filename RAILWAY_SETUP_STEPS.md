# Railway Setup Steps

## Current Status
✅ Deployment is building (5 seconds ago)
⚠️ Previous deployments crashed - need to check logs

## Next Steps

### 1. Generate Domain (Required for Public Access)

In Railway Dashboard → Settings → Networking:
1. Click **"Generate Domain"** button
2. Railway will create a domain like: `openblog-production-xxxx.up.railway.app`
3. Copy this domain - this is your API endpoint URL

### 2. Wait for Build to Complete

Watch the deployment status:
- Should show "Deployment successful" when done
- If it crashes again, check logs

### 3. Test the Deployment

Once domain is generated and deployment is successful:

```bash
# Replace with your actual domain
curl https://openblog-production-xxxx.up.railway.app/health
```

### 4. Check Previous Crashes

If deployment keeps crashing:
1. Go to Railway Dashboard → Deployments
2. Click on a crashed deployment
3. Check "Deploy Logs" for errors
4. Common issues:
   - Missing `GEMINI_API_KEY` environment variable
   - Port binding issues
   - Import errors

## Environment Variables

Make sure these are set in Railway Dashboard → Variables:

**Required:**
- `GEMINI_API_KEY` - Your Gemini API key

**Optional:**
- `DATAFORSEO_LOGIN` - For search fallback
- `DATAFORSEO_PASSWORD` - For search fallback
- `GOOGLE_SERVICE_ACCOUNT_JSON` - For Drive integration

## Testing After Setup

```bash
# Health check
curl https://your-domain.up.railway.app/health

# API docs
open https://your-domain.up.railway.app/docs

# Test blog generation
curl -X POST https://your-domain.up.railway.app/blog/write \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "test",
    "company_url": "https://example.com"
  }'
```

