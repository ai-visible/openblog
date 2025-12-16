# Simple Dockerfile for Railway deployment
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright for graphics (optional)
RUN pip install playwright && playwright install chromium --with-deps || true

# Copy application code
COPY . .

# Expose port (Railway sets PORT env var)
EXPOSE 3000

# Railway auto-detects FastAPI and generates: uvicorn service.api:app --port $PORT
# But $PORT doesn't expand. Solution: Use shell form CMD that Railway will respect
# This ensures PORT env var is properly expanded
CMD python3 -m uvicorn service.api:app --host 0.0.0.0 --port ${PORT:-3000}
