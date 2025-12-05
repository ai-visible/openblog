# Quick Test Guide

## ✅ Environment Setup Complete

Your `.env.local` file has been created with:
```
GOOGLE_GEMINI_API_KEY=AIzaSyBxeTkT-PPFr1xqG0dnGZUMM7APKMmzuDI
```

## Ready to Test!

### Test 1: Local Blog Generation (5-10 minutes)

```bash
cd blog-writer
python3 test_local_blog_generation.py
```

**Expected:**
- All 12 stages execute
- Article generated with AEO score
- Results saved to `test_outputs/local_test_*.json`

### Test 2: API Service (if you want to test API)

**Terminal 1:**
```bash
cd blog-writer/service
pip install -r requirements.txt
python api.py
```

**Terminal 2:**
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test blog generation (5-10 minutes)
curl -X POST http://localhost:8000/write \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "AI customer service automation",
    "company_url": "https://example.com"
  }'
```

### Test 3: Parity Comparison

```bash
cd blog-writer
python3 test_parity.py
```

This will:
- Run local test
- Test API service (if running)
- Compare outputs
- Verify parity

## What to Expect

### Successful Test Output:
```
✅ API key found
✅ Registered 12 stages
🚀 Starting workflow execution...
✅ Headline: [Generated headline]
📊 AEO Score: [Score]/100
⏱️  Execution Times:
   stage_00: X.XXs
   stage_01: X.XXs
   ...
✅ Results saved to: test_outputs/local_test_*.json
```

### If You See Errors:
- **"No API key found"** → Check `.env.local` exists and has correct variable name
- **Import errors** → Run `pip install -r requirements.txt`
- **Timeout errors** → Normal for long-running stages (5-10 min total)

## Next Steps After Testing

1. ✅ Verify local test works
2. ✅ Test API service (optional)
3. ✅ Run parity test
4. ⏳ Deploy FastAPI service
5. ⏳ Deploy edge function
6. ⏳ Test end-to-end

## Notes

- Blog generation takes **5-10 minutes** (stages 4-9 run in parallel)
- API key is loaded from `.env.local` automatically
- Results are saved for comparison
- All tests use the same code path for parity

