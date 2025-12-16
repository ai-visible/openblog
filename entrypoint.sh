#!/bin/bash
set -e
exec python3 -m uvicorn service.api:app --host 0.0.0.0 --port ${PORT:-8000}

