"""
Main entry point for blog-writer Modal deployment
Re-exports the FastAPI app from service.api
"""
import sys
from pathlib import Path

# Add the current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from service.api import app

__all__ = ["app"]
