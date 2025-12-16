# Railway Environment Variables

## Required (Must Set)

### `GEMINI_API_KEY`
**Required:** Yes  
**Description:** Your Google Gemini API key for AI content generation  
**Where to get:** https://aistudio.google.com/app/apikey  
**Example:** `AIzaSy...`

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

## Quick Setup

**Required environment variables:**
```bash
GEMINI_API_KEY=your_gemini_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

That's it! Only these two are needed.

## How to Set in Railway

1. Go to Railway Dashboard → Your Project → Variables tab
2. Click "New Variable"
3. Add `GEMINI_API_KEY` = `your_gemini_api_key`
4. Click "New Variable" again
5. Add `SERPER_API_KEY` = `your_serper_api_key` (use: `***SERPER-API-KEY-REMOVED***`)
6. Railway will auto-redeploy

## Testing

After setting `GEMINI_API_KEY`:

```bash
# Health check (works without API key)
curl https://your-domain/health

# Blog generation (requires API key)
curl -X POST https://your-domain/blog/write \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "test",
    "company_url": "https://example.com"
  }'
```

---

**TL;DR:** Set `GEMINI_API_KEY` and `SERPER_API_KEY` - that's all you need! 🚀

