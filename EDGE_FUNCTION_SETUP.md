# Edge Function Setup Guide

This guide explains how to set up and deploy the blog-writer as an edge function.

## Architecture Overview

```
┌─────────────────────┐
│  Supabase Edge      │  →  Calls FastAPI service
│  Function           │     (blog-writer)
│  (generate-blog-v2) │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│  FastAPI Service    │  →  Executes Python code
│  (service/api.py)   │     (pipeline/blog_generation/)
└─────────────────────┘
```

## Prerequisites

1. **Supabase Project** - With edge functions enabled
2. **Python Service** - FastAPI service running (can be deployed on Cloud Run, Railway, etc.)
3. **Environment Variables** - Configured in Supabase

## Step 1: Deploy FastAPI Service

### Option A: Cloud Run (Recommended)

```bash
cd blog-writer/service

# Build Docker image
docker build -t blog-writer-service .

# Push to Google Container Registry
docker tag blog-writer-service gcr.io/YOUR_PROJECT/blog-writer-service
docker push gcr.io/YOUR_PROJECT/blog-writer-service

# Deploy to Cloud Run
gcloud run deploy blog-writer-service \
  --image gcr.io/YOUR_PROJECT/blog-writer-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_API_KEY=your_key
```

### Option B: Railway

```bash
cd blog-writer/service
railway up
```

### Option C: Local Development

```bash
cd blog-writer/service
pip install -r requirements.txt
python api.py
```

Service will run on `http://localhost:8000`

## Step 2: Configure Supabase Environment Variables

```bash
cd clients@scaile.tech-setup

# Set blog service URL
supabase secrets set BLOG_SERVICE_URL=https://your-service-url.run.app

# Set blog service API key (if using authentication)
supabase secrets set BLOG_SERVICE_API_KEY=your_api_key
```

## Step 3: Deploy Edge Function

```bash
cd clients@scaile.tech-setup

# Deploy the edge function
supabase functions deploy generate-blog-v2
```

## Step 4: Test Edge Function

### Local Testing

```bash
# Start Supabase locally
supabase start

# Serve edge function locally
supabase functions serve generate-blog-v2

# Test the function
curl -X POST http://localhost:54321/functions/v1/generate-blog-v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -d '{
    "projectId": "test-project-uuid",
    "keyword": "AI customer service automation",
    "companyUrl": "https://example.com",
    "companyName": "Example Corp"
  }'
```

### Production Testing

```bash
curl -X POST https://YOUR_PROJECT.supabase.co/functions/v1/generate-blog-v2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -d '{
    "projectId": "project-uuid",
    "keyword": "AI customer service automation",
    "companyUrl": "https://example.com"
  }'
```

## Edge Function API

### Request

```typescript
{
  projectId: string;              // Required: Project UUID
  keywordId?: string;             // Optional: Keyword UUID from database
  keyword?: string;               // Optional: Keyword text (if keywordId not provided)
  companyUrl: string;             // Required: Company website URL
  companyName?: string;           // Optional: Company name
  contentGenerationInstruction?: string;  // Optional: Additional instructions
  language?: string;              // Optional: Language code (default: project language)
  wordCount?: number;            // Optional: Target word count
  systemPrompts?: string[];       // Optional: System prompts
  reviewPrompts?: string[];       // Optional: Review prompts
  storeInDatabase?: boolean;       // Optional: Store in database (default: true)
  createGoogleDoc?: boolean;       // Optional: Create Google Doc (default: true)
  parentFolderId?: string;        // Optional: Parent folder ID for Google Doc
}
```

### Response

```typescript
{
  success: boolean;
  jobId: string;
  headline?: string;
  htmlContent?: string;
  validatedArticle?: Record<string, unknown>;
  qualityReport?: {
    metrics?: {
      aeo_score?: number;
      readability?: number;
      keyword_coverage?: number;
    };
    critical_issues?: string[];
    suggestions?: string[];
  };
  executionTimes?: Record<string, number>;
  durationSeconds: number;
  aeoScore?: number;
  criticalIssuesCount: number;
  articleId?: string;              // If stored in database
  docId?: string;                  // If Google Doc created
  docUrl?: string;                 // Google Doc URL
  error?: string;                  // If error occurred
}
```

## Integration Example

```typescript
// From your application
const response = await fetch(
  'https://YOUR_PROJECT.supabase.co/functions/v1/generate-blog-v2',
  {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${ANON_KEY}`,
    },
    body: JSON.stringify({
      projectId: 'project-uuid',
      keywordId: 'keyword-uuid',
      companyUrl: 'https://example.com',
      storeInDatabase: true,
      createGoogleDoc: true,
    }),
  }
);

const result = await response.json();

if (result.success) {
  console.log(`Blog generated: ${result.headline}`);
  console.log(`AEO Score: ${result.aeoScore}`);
  console.log(`Google Doc: ${result.docUrl}`);
} else {
  console.error(`Error: ${result.error}`);
}
```

## Monitoring

### Check Edge Function Logs

```bash
supabase functions logs generate-blog-v2
```

### Check Service Logs

If using Cloud Run:
```bash
gcloud run services logs read blog-writer-service --limit 50
```

## Troubleshooting

### Service Not Found

- Verify `BLOG_SERVICE_URL` is set correctly
- Check service is running and accessible
- Test service directly: `curl https://your-service-url/health`

### Authentication Errors

- Verify `BLOG_SERVICE_API_KEY` matches service configuration
- Check service allows unauthenticated access (if not using API key)

### Timeout Errors

- Blog generation takes 5-10 minutes
- Edge functions have 60s timeout by default
- Consider using async pattern or increasing timeout

### Database Errors

- Verify project exists in database
- Check keyword exists (if using keywordId)
- Verify Supabase service role key is configured

## Next Steps

1. ✅ Deploy FastAPI service
2. ✅ Configure environment variables
3. ✅ Deploy edge function
4. ⏳ Test end-to-end
5. ⏳ Monitor performance
6. ⏳ Optimize if needed

