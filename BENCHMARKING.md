# Blog Writer Pipeline - Benchmarking Guide

This document describes how to benchmark and compare the local Python version with the edge function version to ensure feature/quality/output parity.

## Architecture

```
┌─────────────────┐
│  Local Test     │  →  Direct Python execution
│  (test_local)   │
└─────────────────┘

┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Edge Function  │  →  │  FastAPI Service │  →  │  Python Code    │
│  (generate-     │     │  (api.py)        │     │  (pipeline/)          │
│   blog-v2)      │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Setup

### 1. Local Testing

```bash
cd blog-writer
python3 test_local_blog_generation.py
```

This will:
- Execute all 12 stages locally
- Save results to `test_outputs/local_test_*.json`
- Save full article to `test_outputs/local_article_*.json`

### 2. FastAPI Service

```bash
cd blog-writer/service
pip install -r requirements.txt
python api.py
```

Service runs on `http://localhost:8000`

### 3. Edge Function

Deploy the edge function:
```bash
cd clients@scaile.tech-setup
supabase functions deploy generate-blog-v2
```

Or test locally:
```bash
supabase functions serve generate-blog-v2
```

## Benchmarking Process

### Step 1: Run Local Test

```bash
cd blog-writer
export GOOGLE_API_KEY=your_key
python3 test_local_blog_generation.py
```

**Output:**
- `test_outputs/local_test_TIMESTAMP.json` - Summary metrics
- `test_outputs/local_article_TIMESTAMP.json` - Full article data

### Step 2: Test FastAPI Service

```bash
curl -X POST http://localhost:8000/write \
  -H "Content-Type: application/json" \
  -d '{
    "primary_keyword": "AI customer service automation",
    "company_url": "https://example.com",
    "company_name": "Example Corp"
  }' | jq > test_outputs/api_test_TIMESTAMP.json
```

### Step 3: Test Edge Function

```bash
curl -X POST http://localhost:54321/functions/v1/generate-blog-v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -d '{
    "projectId": "project-uuid",
    "keyword": "AI customer service automation",
    "companyUrl": "https://example.com",
    "companyName": "Example Corp"
  }' | jq > test_outputs/edge_test_TIMESTAMP.json
```

## Comparison Metrics

### 1. Execution Times

Compare execution times for each stage:

```python
# Local
local_times = {
    "stage_00": 2.5,
    "stage_01": 0.3,
    ...
}

# API
api_times = response["execution_times"]

# Edge Function
edge_times = response["executionTimes"]
```

**Expected:** API and Edge Function should have similar times (within 5% variance due to network overhead).

### 2. Quality Metrics

Compare AEO scores and quality reports:

```python
# All should match
local_aeo = local_data["aeo_score"]
api_aeo = api_response["aeo_score"]
edge_aeo = edge_response["aeoScore"]

assert abs(local_aeo - api_aeo) < 1, "AEO score mismatch"
assert abs(local_aeo - edge_aeo) < 1, "AEO score mismatch"
```

### 3. Output Content

Compare article content:

```python
# Headlines should match
assert local_headline == api_headline == edge_headline

# HTML content should be identical
assert local_html == api_html == edge_html

# Validated article structure should match
assert local_article.keys() == api_article.keys() == edge_article.keys()
```

### 4. Feature Parity Checklist

- [ ] All 12 stages execute successfully
- [ ] AEO scoring works identically
- [ ] HTML generation matches
- [ ] Citations validation works
- [ ] Internal links generation works
- [ ] FAQ/PAA extraction works
- [ ] Image generation works (if enabled)
- [ ] Quality report structure matches
- [ ] Error handling is consistent

## Automated Benchmarking Script

Create `benchmark.py`:

```python
import asyncio
import json
import requests
from pathlib import Path
from datetime import datetime

async def benchmark():
    """Run all three versions and compare results."""
    
    test_config = {
        "primary_keyword": "AI customer service automation",
        "company_url": "https://example.com",
        "company_name": "Example Corp",
    }
    
    # 1. Local test
    # (Run via subprocess)
    
    # 2. API test
    api_response = requests.post(
        "http://localhost:8000/write",
        json=test_config
    ).json()
    
    # 3. Edge function test
    edge_response = requests.post(
        "http://localhost:54321/functions/v1/generate-blog-v2",
        headers={"Authorization": "Bearer YOUR_KEY"},
        json={
            "projectId": "test-project",
            "keyword": test_config["primary_keyword"],
            "companyUrl": test_config["company_url"],
            "companyName": test_config["company_name"],
        }
    ).json()
    
    # Compare results
    compare_results(api_response, edge_response)

def compare_results(api_result, edge_result):
    """Compare API and Edge function results."""
    metrics = [
        ("aeo_score", "aeoScore"),
        ("duration_seconds", "durationSeconds"),
        ("headline", "headline"),
    ]
    
    for api_key, edge_key in metrics:
        api_val = api_result.get(api_key)
        edge_val = edge_result.get(edge_key)
        
        if api_val != edge_val:
            print(f"⚠️  Mismatch in {api_key}: API={api_val}, Edge={edge_val}")
        else:
            print(f"✅ {api_key} matches")
```

## Expected Results

### Performance

- **Local:** Fastest (no network overhead)
- **API:** ~100-500ms overhead (network + serialization)
- **Edge Function:** ~200-800ms overhead (network + edge function + API)

### Quality

All three should produce **identical**:
- AEO scores
- Article content
- HTML output
- Quality reports

### Features

All three should support:
- Same input parameters
- Same output structure
- Same error handling
- Same validation rules

## Troubleshooting

### Mismatched AEO Scores

- Check if same API keys are used
- Verify environment variables match
- Check for timing differences (some stages may have slight variance)

### Different HTML Output

- Verify same version of cleanup/storage stages
- Check for environment-specific configurations
- Ensure same Supabase/storage settings

### Execution Time Differences

- Network overhead is expected
- Edge function adds ~200-500ms
- API adds ~100-300ms
- Total variance should be < 10%

## Next Steps

1. ✅ Test local version
2. ✅ Create FastAPI service
3. ✅ Create edge function
4. ⏳ Run benchmarks
5. ⏳ Verify parity
6. ⏳ Deploy to production

