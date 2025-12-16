#!/bin/bash
set -e
# Railway startup script - ensures python -m uvicorn runs correctly
# Use full path to python and explicit uvicorn module
cd /app || cd "$(dirname "$0")/.." || true
exec python3 -m uvicorn service.api:app --host 0.0.0.0 --port ${PORT:-8000}
