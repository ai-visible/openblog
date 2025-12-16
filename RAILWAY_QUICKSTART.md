# Railway Quick Start Guide

## 🚀 Deploy in 3 Steps

### Step 1: Connect to Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `openblog` repository

### Step 2: Add Environment Variables

In Railway Dashboard → Variables, add:

```bash
GEMINI_API_KEY=your_api_key_here
```

### Step 3: Deploy

Railway will automatically:
- ✅ Detect Python project
- ✅ Install dependencies
- ✅ Start the server

**That's it!** Your app will be live at `https://your-app.railway.app`

## 📋 Files Created for Railway

- ✅ `railway.json` - Railway configuration
- ✅ `Procfile` - Start command
- ✅ `runtime.txt` - Python 3.11
- ✅ `nixpacks.toml` - Build config (handles Playwright)

## 🔍 Verify Deployment

```bash
# Health check
curl https://your-app.railway.app/health

# Should return:
# {"status":"healthy","service":"blog-writer","version":"1.0.0",...}
```

## 🐛 Troubleshooting

**Build fails?**
- Check Railway logs for errors
- Verify `GEMINI_API_KEY` is set
- Ensure git dependency repo is accessible

**App won't start?**
- Check logs: Railway Dashboard → Deployments → Logs
- Verify `$PORT` is used (already configured)

**Need help?**
- See full guide: `RAILWAY_DEPLOYMENT.md`
- Railway docs: https://docs.railway.app

