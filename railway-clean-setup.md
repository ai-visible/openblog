# Clean Railway Deployment Setup

## Problem
We have mysterious deployments we can't track via CLI. This creates a clean, controllable deployment.

## Step-by-Step Clean Setup

### 1. Create New Service (Manual)
1. Go to Railway Dashboard: https://railway.app/dashboard
2. Select project: **openblog** 
3. Click "New Service"
4. Name it: **openblog-main**
5. Connect to GitHub repo: **federicodeponte/openblog**
6. Set branch: **main**

### 2. Environment Variables (Copy from Working)
From working deployment we know these are needed:

```
GEMINI_API_KEY=<your_gemini_key>
GPG_KEY=<your_gpg_key>  
SERPER_API_KEY=<your_serper_key>
```

**Get values from working deployment:**
```bash
# You'll need to copy these from wherever they're stored
# (likely your .env.local file or previous Railway dashboard)
```

### 3. Deploy Settings
- **Start Command:** `uvicorn service.api:app --host 0.0.0.0 --port $PORT`
- **Build Command:** (auto-detected from repo)
- **Health Check:** `/health`

### 4. Domain Setup
The service will auto-generate: `openblog-main-production.up.railway.app`

### 5. Verify
Once deployed, test:
```bash
curl https://openblog-main-production.up.railway.app/health
```

## Result
You'll have a clean, trackable deployment that:
- ✅ You created and control
- ✅ Has clear naming
- ✅ Is connected to your GitHub repo  
- ✅ Has all required environment variables
- ✅ Uses the latest code from main branch

## Clean Up Old Deployments
Once the new one works:
1. Delete the mysterious services
2. Use only the new clean deployment
3. Update documentation to point to new URL