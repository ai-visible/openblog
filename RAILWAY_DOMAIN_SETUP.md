# Railway Domain Setup Guide

## Public Networking Options

Railway offers two ways to expose your service:

### Option 1: Generate Service Domain (Easiest - Recommended)

**Steps:**
1. Go to Railway Dashboard → Settings → Networking
2. Under "Public Networking", click **"Generate Service Domain"**
3. **Leave target port empty or use `$PORT`** - Railway sets this automatically!
4. Railway will create: `openblog-production-xxxx.up.railway.app`

**Why this works:**
- Railway automatically sets `$PORT` environment variable
- Your app reads `$PORT` from environment (already configured)
- No manual port configuration needed!

### Option 2: Custom Domain (Your Own Domain)

**Steps:**
1. Go to Railway Dashboard → Settings → Networking
2. Under "Custom Domain", click **"Add Custom Domain"**
3. Enter your domain (e.g., `api.yourdomain.com`)
4. **Target port:** Leave empty or use `$PORT` (Railway handles it)
5. Railway will provide DNS records to add to your domain

**DNS Setup:**
- Railway will show you CNAME records to add
- Add them to your domain's DNS settings
- Railway automatically provisions SSL certificates

## Port Configuration

### ❌ DON'T Use Fixed Ports
- Don't set port to `8080` or any fixed number
- Railway assigns ports dynamically
- Your app uses `$PORT` environment variable (already configured)

### ✅ Correct Configuration
Your app already uses:
```python
port = int(os.getenv("PORT", "8000"))  # Reads from Railway's $PORT
```

And your start command:
```bash
uvicorn service.api:app --host 0.0.0.0 --port $PORT
```

This is **already correct** - Railway will set `$PORT` automatically!

## Quick Setup

### For Service Domain:
1. Click "Generate Service Domain"
2. **Leave target port empty** (or use `$PORT` if required)
3. Copy the generated domain
4. Done! ✅

### For Custom Domain:
1. Click "Add Custom Domain"
2. Enter your domain
3. **Leave target port empty** (or use `$PORT`)
4. Add DNS records Railway provides
5. Wait for SSL provisioning (automatic)
6. Done! ✅

## Testing

Once domain is set up:

```bash
# Service domain
curl https://openblog-production-xxxx.up.railway.app/health

# Custom domain
curl https://api.yourdomain.com/health
```

## Important Notes

- **Port:** Railway handles this automatically via `$PORT`
- **SSL:** Railway provisions SSL automatically (Let's Encrypt)
- **DNS:** Only needed for custom domains
- **Service Domain:** Works immediately, no DNS setup needed

---

**Recommendation:** Start with "Generate Service Domain" - it's instant and works immediately!

