# Fire-and-Forget Async Architecture

## Overview

The blog-writer service now supports **fire-and-forget async architecture** for handling long-running content generation tasks (5+ minutes). This system is designed for production environments where quality takes precedence over speed.

## Why Async Architecture?

### The Quality Challenge
High-quality blog content generation with deep research requires:
- **5-30 minutes** execution time (realistic for quality content)
- **20+ web searches** during generation via tools
- **Multiple quality gates** with regeneration if needed
- **AEO scoring** and comprehensive validation

### Traditional Sync Problems
- **Request timeouts**: Most HTTP clients timeout after 60-120 seconds
- **Resource blocking**: Synchronous requests tie up server resources
- **Poor user experience**: Users wait without progress feedback
- **Server restart vulnerability**: Lost jobs on deployment/restart

### Async Solution Benefits
✅ **No timeouts**: Submit job, get immediate response  
✅ **Progress tracking**: Real-time stage completion updates  
✅ **Persistent storage**: Jobs survive server restarts  
✅ **Resource efficiency**: Handle multiple concurrent jobs  
✅ **Webhook callbacks**: Automatic notifications when complete  
✅ **Quality focus**: No rush for completion, deep research enabled  

## Architecture Components

### 1. JobManager
Central orchestrator for async job processing.

**Key Features:**
- **SQLite persistence**: Jobs stored in database
- **Concurrent processing**: Configurable job slots (default: 3)
- **Progress tracking**: Stage-by-stage progress updates
- **Automatic cleanup**: Old jobs purged after 7 days
- **Error handling**: Retry logic and failure tracking

### 2. Job States
```
pending → running → completed/failed/cancelled
```

- **pending**: Queued, waiting for processing slot
- **running**: Currently executing pipeline stages
- **completed**: Successfully finished with results
- **failed**: Failed with error message
- **cancelled**: Manually cancelled

### 3. Progress Tracking
- **Current stage**: Which pipeline stage is executing
- **Progress percentage**: 0-100% completion
- **Stages completed**: Count of finished stages
- **Estimated remaining**: Time prediction based on progress

## API Reference

### Submit Async Job
```http
POST /write-async
```

**Request:**
```json
{
  "primary_keyword": "energy efficiency",
  "company_url": "https://example.com",
  "language": "en",
  "country": "US",
  "callback_url": "https://your-app.com/webhook",
  "priority": 2,
  "max_duration_minutes": 30
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Blog generation job queued. Use /jobs/{job_id}/status to track progress.",
  "polling_url": "/jobs/550e8400-e29b-41d4-a716-446655440000/status",
  "estimated_duration_minutes": "5-30 (quality takes time)"
}
```

### Check Job Status
```http
GET /jobs/{job_id}/status
```

**Response (Running):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "created_at": "2025-12-04T10:00:00Z",
  "started_at": "2025-12-04T10:00:05Z",
  "current_stage": "stage_02",
  "progress_percent": 23,
  "stages_completed": 3,
  "total_stages": 13,
  "estimated_remaining_seconds": 480
}
```

**Response (Completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "created_at": "2025-12-04T10:00:00Z",
  "started_at": "2025-12-04T10:00:05Z",
  "completed_at": "2025-12-04T10:12:30Z",
  "duration_seconds": 745,
  "progress_percent": 100,
  "stages_completed": 13,
  "total_stages": 13,
  "quality_score": 87.5,
  "result": {
    "success": true,
    "headline": "Complete Guide to Energy Efficiency...",
    "html_content": "<article>...</article>",
    "aeo_score": 87.5,
    "word_count": 2450,
    "meta_title": "Energy Efficiency Guide 2024...",
    "meta_description": "Discover proven strategies...",
    "citations": [...],
    "image_url": "https://drive.google.com/...",
    // ... full BlogGenerationResponse
  }
}
```

### List Jobs
```http
GET /jobs?status=running&limit=20&offset=0
```

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "running",
      "created_at": "2025-12-04T10:00:00Z",
      "progress_percent": 45,
      "stages_completed": 6
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0,
  "has_more": false
}
```

### Cancel Job
```http
POST /jobs/{job_id}/cancel
```

**Response:**
```json
{
  "success": true,
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Job cancelled successfully"
}
```

### System Statistics
```http
GET /jobs/stats
```

**Response:**
```json
{
  "status_counts": {
    "pending": 5,
    "running": 2,
    "completed": 150,
    "failed": 3
  },
  "running_jobs": 2,
  "max_concurrent": 3,
  "capacity_used_percent": 67,
  "average_duration_seconds": 420.5,
  "database_path": "jobs.db",
  "timestamp": "2025-12-04T10:15:00Z"
}
```

## Usage Patterns

### 1. Basic Fire-and-Forget
```python
import httpx
import asyncio
import time

async def generate_blog_async():
    async with httpx.AsyncClient() as client:
        # Submit job
        response = await client.post("https://blog-writer/write-async", json={
            "primary_keyword": "renewable energy",
            "company_url": "https://energy-company.com"
        })
        
        job_data = response.json()
        job_id = job_data["job_id"]
        print(f"Job submitted: {job_id}")
        
        # Poll for completion
        while True:
            status_response = await client.get(f"https://blog-writer/jobs/{job_id}/status")
            status = status_response.json()
            
            print(f"Progress: {status['progress_percent']}% - {status['status']}")
            
            if status["status"] in ["completed", "failed", "cancelled"]:
                break
                
            await asyncio.sleep(30)  # Poll every 30 seconds
        
        if status["status"] == "completed":
            result = status["result"]
            print(f"✅ Blog generated: {result['headline']}")
            print(f"Quality score: {result['aeo_score']}")
            return result
        else:
            print(f"❌ Job failed: {status.get('error')}")
            return None
```

### 2. Webhook Integration
```python
# Submit job with webhook
async def submit_with_webhook():
    async with httpx.AsyncClient() as client:
        response = await client.post("https://blog-writer/write-async", json={
            "primary_keyword": "solar panels",
            "company_url": "https://solar-company.com",
            "callback_url": "https://your-app.com/blog-webhook",
            "priority": 1  # High priority
        })
        
        return response.json()

# Webhook handler (FastAPI example)
from fastapi import FastAPI

app = FastAPI()

@app.post("/blog-webhook")
async def blog_webhook(payload: dict):
    job_id = payload["job_id"]
    status = payload["status"]
    
    if status == "completed":
        result = payload["result"]
        # Process completed blog
        await save_blog_to_database(result)
        await notify_content_team(job_id, result["headline"])
    
    return {"status": "received"}
```

### 3. Batch Processing
```python
async def batch_blog_generation(keywords: list):
    job_ids = []
    
    # Submit all jobs
    async with httpx.AsyncClient() as client:
        for keyword in keywords:
            response = await client.post("https://blog-writer/write-async", json={
                "primary_keyword": keyword,
                "company_url": "https://company.com",
                "priority": 2,  # Normal priority
                "batch_id": "batch_2024_12"
            })
            
            job_data = response.json()
            job_ids.append(job_data["job_id"])
            print(f"Submitted: {keyword} -> {job_data['job_id']}")
    
    # Monitor batch progress
    completed = []
    failed = []
    
    while len(completed) + len(failed) < len(job_ids):
        for job_id in job_ids:
            if job_id in completed or job_id in failed:
                continue
                
            status_response = await client.get(f"https://blog-writer/jobs/{job_id}/status")
            status = status_response.json()
            
            if status["status"] == "completed":
                completed.append(job_id)
                result = status["result"]
                print(f"✅ Completed: {result['headline']} (AEO: {result['aeo_score']})")
            
            elif status["status"] == "failed":
                failed.append(job_id)
                print(f"❌ Failed: {job_id} - {status.get('error')}")
        
        await asyncio.sleep(60)  # Check every minute
    
    print(f"Batch complete: {len(completed)} succeeded, {len(failed)} failed")
    return completed, failed
```

## Production Deployment

### Environment Variables
```env
# Job Manager Configuration
BLOG_WRITER_MAX_CONCURRENT=3
BLOG_WRITER_DB_PATH=/data/jobs.db
BLOG_WRITER_JOB_CLEANUP_DAYS=7

# Service Configuration
GOOGLE_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create data directory for job persistence
RUN mkdir -p /data
VOLUME ["/data"]

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "service.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
version: '3.8'

services:
  blog-writer:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data  # Persist job database
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - BLOG_WRITER_MAX_CONCURRENT=5
      - BLOG_WRITER_DB_PATH=/data/jobs.db
    restart: unless-stopped
    
  # Optional: Monitoring
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
```

### Load Balancer Setup
```nginx
# nginx.conf
upstream blog_writer {
    server blog-writer-1:8000;
    server blog-writer-2:8000;
    server blog-writer-3:8000;
}

server {
    listen 80;
    server_name blog-writer.yourdomain.com;
    
    # Async endpoints - long timeout
    location ~ ^/(write-async|jobs) {
        proxy_pass http://blog_writer;
        proxy_timeout 120s;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
    
    # Sync endpoint - very long timeout
    location /write {
        proxy_pass http://blog_writer;
        proxy_timeout 1800s;  # 30 minutes
        proxy_read_timeout 1800s;
        proxy_send_timeout 1800s;
    }
    
    # Quick endpoints
    location / {
        proxy_pass http://blog_writer;
        proxy_timeout 30s;
    }
}
```

## Monitoring and Observability

### Key Metrics to Track

**Job Metrics:**
- Job submission rate (jobs/hour)
- Average completion time
- Success/failure rates
- Queue depth (pending jobs)
- Concurrent job utilization

**Quality Metrics:**
- Average AEO scores
- Regeneration rates
- Quality gate pass rates

**System Metrics:**
- Memory usage during job execution
- API response times
- Database size growth

### Logging Strategy
```python
import logging
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage in job processing
logger.info("job_submitted", 
    job_id=job_id, 
    keyword=primary_keyword, 
    priority=priority,
    estimated_duration=max_duration_minutes
)

logger.info("job_completed",
    job_id=job_id,
    duration_seconds=duration,
    aeo_score=aeo_score,
    word_count=word_count,
    quality_passed=quality_passed
)
```

### Alerting Rules
```yaml
# Prometheus alerting rules
groups:
  - name: blog_writer_alerts
    rules:
      - alert: HighJobFailureRate
        expr: rate(blog_jobs_failed_total[5m]) > 0.1
        for: 2m
        annotations:
          summary: "High blog generation failure rate"
          
      - alert: JobQueueBacklog
        expr: blog_jobs_pending > 20
        for: 5m
        annotations:
          summary: "Blog job queue has significant backlog"
          
      - alert: LongRunningJob
        expr: blog_job_duration_seconds > 2400  # 40 minutes
        annotations:
          summary: "Blog job running longer than expected"
```

## Migration Guide

### From Sync to Async

**Before (Synchronous):**
```python
async def generate_blog():
    response = await client.post("/write", json=request_data)
    if response.status_code == 200:
        result = response.json()
        return result
    else:
        raise Exception("Generation failed")
```

**After (Asynchronous):**
```python
async def generate_blog():
    # Submit job
    response = await client.post("/write-async", json=request_data)
    job_data = response.json()
    job_id = job_data["job_id"]
    
    # Poll for completion
    while True:
        status_response = await client.get(f"/jobs/{job_id}/status")
        status = status_response.json()
        
        if status["status"] == "completed":
            return status["result"]
        elif status["status"] == "failed":
            raise Exception(f"Generation failed: {status['error']}")
        
        await asyncio.sleep(30)
```

### Gradual Rollout Strategy

1. **Phase 1**: Deploy async endpoints alongside existing sync
2. **Phase 2**: Migrate non-critical workflows to async
3. **Phase 3**: Update high-volume batch processing to async
4. **Phase 4**: Deprecate sync endpoint (keep for emergency use)

## Troubleshooting

### Common Issues

**Job Stuck in Pending:**
```bash
# Check system capacity
curl http://blog-writer/jobs/stats

# Look for resource constraints
docker stats blog-writer-container
```

**High Failure Rate:**
```bash
# Check recent failures
curl "http://blog-writer/jobs?status=failed&limit=10"

# Review error patterns in logs
docker logs blog-writer-container | grep "job_failed"
```

**Slow Job Completion:**
```bash
# Monitor running jobs
curl "http://blog-writer/jobs?status=running"

# Check individual job progress
curl "http://blog-writer/jobs/{job_id}/status"
```

**Database Growing Too Large:**
```bash
# Check job cleanup settings
curl http://blog-writer/jobs/stats

# Manually trigger cleanup (if needed)
sqlite3 /data/jobs.db "DELETE FROM jobs WHERE status IN ('completed', 'failed') AND completed_at < datetime('now', '-7 days')"
```

## FAQ

**Q: How long do jobs typically take?**
A: 5-30 minutes depending on complexity. Deep research with 20+ web searches takes time for quality.

**Q: What happens if the server restarts during a job?**
A: Running jobs are marked as failed. They can be resubmitted. Pending jobs remain queued.

**Q: Can I increase concurrency?**
A: Yes, but monitor memory usage. Each job uses ~200-500MB. Start with 3 concurrent, increase gradually.

**Q: How do I handle webhook failures?**
A: Implement retry logic in your webhook endpoint. The system makes one delivery attempt.

**Q: What's the maximum job timeout?**
A: Default is 30 minutes, configurable up to 60 minutes. Quality content requires patience.

**Q: How do I monitor job progress?**
A: Poll `/jobs/{job_id}/status` every 30-60 seconds. It shows current stage and percentage.

## Conclusion

The fire-and-forget async architecture transforms blog generation from a blocking operation into a scalable, quality-first system. By embracing the reality that high-quality content takes time (5-30 minutes), we can build robust production systems that prioritize quality over speed.

Key benefits:
- **No more timeouts** or blocking operations
- **Real-time progress tracking** for better UX
- **Quality-first approach** with deep research
- **Production-ready** with persistence and monitoring
- **Scalable** to handle multiple concurrent jobs

This architecture acknowledges that "quality takes time" and builds systems that work with this reality rather than against it.