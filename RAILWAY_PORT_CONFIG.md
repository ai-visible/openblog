# Railway Target Port Configuration

## If Railway Requires a Port Number

Railway's "Target Port" field is for internal routing. Your app will still use the `$PORT` environment variable that Railway sets automatically.

### Recommended Options:

**Option 1: Use `$PORT` (if Railway accepts it)**
```
Target port: $PORT
```

**Option 2: Use `3000` (Railway's common default)**
```
Target port: 3000
```

**Option 3: Use `8080` (alternative)**
```
Target port: 8080
```

## Why This Works

1. **Railway sets `$PORT` automatically** - This is the actual port your app listens on
2. **Your app reads `$PORT`** - Code: `port = int(os.getenv("PORT", "8000"))`
3. **Start command uses `$PORT`** - `uvicorn service.api:app --host 0.0.0.0 --port $PORT`
4. **Target port is just for routing** - Railway uses it internally but your app uses `$PORT`

## What Happens

- Railway assigns a port (e.g., 3000, 8080, or random)
- Sets `PORT` environment variable to that value
- Your app reads `PORT` and listens on that port
- Railway routes traffic from the domain to that port
- The "target port" field is just Railway's routing config

## Recommendation

**Try `$PORT` first** - If Railway accepts environment variable syntax, use that.

**If not, use `3000`** - This is Railway's most common default port.

Either way, Railway will override it with the actual `PORT` env var, so your app will work correctly!

