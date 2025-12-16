# 🚀 Simple Railway Deployment

## Just 3 Steps!

### Step 1: Run the deployment script
```bash
./railway_deploy_interactive.sh
```

This will:
- ✅ Open browser for Railway login (you authenticate)
- ✅ Create/link Railway project
- ✅ Ask for your GEMINI_API_KEY
- ✅ Deploy automatically!

### Step 2: Provide your API key
When prompted, paste your `GEMINI_API_KEY`

### Step 3: Done!
Your app will be live! The script will show you the URL.

---

## Alternative: Web Interface (Even Easier!)

1. **Go to**: https://railway.app/new
2. **Click**: "Deploy from GitHub repo"
3. **Select**: `federicodeponte/openblog`
4. **Go to**: Variables tab
5. **Add**: `GEMINI_API_KEY` = `your_key_here`
6. **Done!** Railway auto-deploys!

---

## What I've Already Set Up

✅ All Railway config files created
✅ Start command configured
✅ Python version specified
✅ Playwright build config
✅ Health endpoint ready

**You just need to:**
1. Authenticate with Railway (one-time)
2. Provide your API key
3. Deploy!

---

**Ready?** Run `./railway_deploy_interactive.sh` 🚀

