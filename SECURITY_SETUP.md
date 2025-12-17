# 🔒 OpenBlog Security Setup Guide

## ⚠️ CRITICAL: Secure Your API Immediately

Your OpenBlog API is currently **OPEN TO THE PUBLIC** until you set up API keys.

## 🚀 Quick Security Setup (5 minutes)

### Step 1: Generate API Keys
```bash
cd /path/to/openblog
python3 generate_api_key.py
```

This will output:
```
OPENBLOG_API_KEYS="ob_prod_ABC123...,ob_staging_XYZ789...,ob_dev_DEF456..."
```

### Step 2: Set Environment Variables

**Local Development (.env.local):**
```bash
# Add to your .env.local file
OPENBLOG_API_KEYS="ob_prod_7Zq3Am6qgCXPuFFppDswxRyTQwHBBnp6,ob_staging_biqTvDNCYoRgAUViyuibojKVKyntE9Zk"
```

**Production Deployment:**
- **Railway**: Go to project settings → Environment → Add `OPENBLOG_API_KEYS`
- **Vercel**: Go to project settings → Environment Variables → Add `OPENBLOG_API_KEYS`
- **Docker**: Add to your docker-compose.yml or Dockerfile ENV

### Step 3: Test Authentication

**Without API Key (should fail):**
```bash
curl https://your-api.com/write
# Response: 401 Unauthorized
```

**With Valid API Key (should work):**
```bash
curl -H "Authorization: Bearer ob_prod_7Zq3Am6qgCXPuFFppDswxRyTQwHBBnp6" \
     https://your-api.com/write
# Response: 200 OK
```

### Step 4: Update Client Code

**JavaScript/Node.js:**
```javascript
const response = await fetch('https://your-api.com/write', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${process.env.OPENBLOG_API_KEY}`
  },
  body: JSON.stringify({
    primary_keyword: "AI automation",
    company_url: "https://example.com"
  })
});
```

**Python:**
```python
import requests

headers = {
    'Authorization': f'Bearer {os.getenv("OPENBLOG_API_KEY")}',
    'Content-Type': 'application/json'
}

response = requests.post(
    'https://your-api.com/write',
    headers=headers,
    json={
        'primary_keyword': 'AI automation',
        'company_url': 'https://example.com'
    }
)
```

## 🔐 Security Features Implemented

✅ **API Key Authentication**: Bearer token or X-API-Key header
✅ **Multiple Keys**: Support prod/staging/dev environments  
✅ **Rate Limiting**: 10 requests/minute per IP
✅ **CORS Protection**: Only allowed origins can access
✅ **Backward Compatibility**: API stays open if no keys configured
✅ **Secure Generation**: 256-bit entropy cryptographic keys

## 📋 Key Management Best Practices

### DO:
- ✅ Store keys in environment variables
- ✅ Use different keys for prod/staging/dev
- ✅ Rotate keys periodically (quarterly)
- ✅ Monitor usage logs
- ✅ Use HTTPS only in production

### DON'T:
- ❌ Commit keys to Git repositories
- ❌ Share keys via email/chat
- ❌ Use the same key everywhere
- ❌ Hardcode keys in source code
- ❌ Forget to set keys in production

## 🚨 Emergency: If Keys Are Compromised

1. **Immediately generate new keys:**
   ```bash
   python3 generate_api_key.py
   ```

2. **Update environment variables** in all deployments

3. **Deploy/restart services** to activate new keys

4. **Revoke old keys** by removing from `OPENBLOG_API_KEYS`

5. **Audit access logs** for unauthorized usage

## 📊 Monitoring & Logs

The API logs all authentication attempts:
- ✅ Valid key usage: `Valid API key used: ob_prod_ABC123...`
- ⚠️ Missing keys: `No API keys configured - API is open to public!`
- ❌ Invalid keys: `Invalid API key` (401 response)

Monitor your deployment logs for these messages.

## 🆘 Support

If you need help with security setup:
1. Check the logs for authentication errors
2. Verify environment variables are set correctly
3. Test with curl commands above
4. Ensure HTTPS is used in production

---

**🔒 Your API will be secure once you complete Step 2 (setting environment variables)!**