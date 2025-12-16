# 🚀 Deploy to Railway - Quick Guide

I've set everything up! Here's how to deploy:

## Option 1: Automated Script (Easiest)

Just run:
```bash
./deploy_to_railway.sh
```

The script will:
1. ✅ Install Railway CLI (if needed)
2. ✅ Authenticate you with Railway
3. ✅ Create/select project
4. ✅ Set environment variables
5. ✅ Deploy!

**You'll need:**
- Your `GEMINI_API_KEY` (you'll be prompted)

## Option 2: Manual Steps

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
```

### Step 2: Login
```bash
railway login
```
(This opens your browser to authenticate)

### Step 3: Initialize Project
```bash
railway init
```
(Choose "Create new project" or "Link existing")

### Step 4: Set Environment Variable
```bash
railway variables set GEMINI_API_KEY="your_key_here"
```

### Step 5: Deploy!
```bash
railway up
```

### Step 6: Get Your URL
```bash
railway domain
```

## Option 3: Web Interface (No CLI)

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select `federicodeponte/openblog`
4. Go to Variables tab → Add `GEMINI_API_KEY`
5. Railway auto-deploys!

## ✅ What's Already Configured

- ✅ `railway.json` - Railway config
- ✅ `Procfile` - Start command
- ✅ `runtime.txt` - Python 3.11
- ✅ `nixpacks.toml` - Build config
- ✅ Health endpoint at `/health`

## 🎯 Quick Test After Deployment

```bash
# Get your URL
railway domain

# Test health
curl https://your-app.railway.app/health
```

## 📝 Need Help?

- Railway Docs: https://docs.railway.app
- Check logs: `railway logs`
- Open dashboard: `railway dashboard`

---

**Ready?** Run `./deploy_to_railway.sh` and follow the prompts! 🚀

