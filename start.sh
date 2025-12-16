#!/bin/bash
# Railway startup script - ensures python -m uvicorn runs correctly
exec python -m uvicorn service.api:app --host 0.0.0.0 --port ${PORT:-8000}
