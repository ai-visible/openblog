# Blog Writer Service API

FastAPI service wrapper for blog-writer, exposing the blog generation workflow as a REST API for edge functions.

## Setup

```bash
cd service
pip install -r requirements.txt
```

## Environment Variables

```bash
GOOGLE_API_KEY=your_api_key
# OR
GOOGLE_GEMINI_API_KEY=your_api_key

# Optional
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
REPLICATE_API_TOKEN=your_replicate_token
```

## Running the Service

```bash
# Development
python api.py

# Production
uvicorn api:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### POST /write

Generate a blog article synchronously.

**Request:**
```json
{
  "primary_keyword": "AI customer service automation",
  "company_url": "https://example.com",
  "company_name": "Example Corp",
  "content_generation_instruction": "Focus on statistics",
  "language": "en",
  "word_count": 2000
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "api-20231122-143000-AI customer serv",
  "headline": "How AI is Transforming Customer Service",
  "html_content": "<html>...</html>",
  "validated_article": {...},
  "quality_report": {
    "metrics": {
      "aeo_score": 85
    },
    "critical_issues": []
  },
  "execution_times": {
    "stage_00": 2.5,
    "stage_01": 0.3,
    ...
  },
  "duration_seconds": 450.2,
  "aeo_score": 85,
  "critical_issues_count": 0
}
```

### GET /health

Health check endpoint.

### POST /write-async

Generate a blog article asynchronously (returns immediately).

### GET /status/{job_id}

Get status of an async job (not yet implemented).

## Integration with Edge Functions

This service should be deployed and accessible via `BLOG_SERVICE_URL`. The edge function will call `/write` endpoint.

