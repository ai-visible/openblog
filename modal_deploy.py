"""
Modal deployment configuration for blog-writer service

v3: Direct Google GenAI SDK for Gemini calls (no external dependencies)
    - Uses google-genai package with built-in Google Search grounding
    - Image generation via OpenRouter
"""

import modal
from pathlib import Path

app = modal.App("blog-writer")
local_dir = Path(__file__).parent

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install_from_requirements(local_dir / "requirements.txt")
    .add_local_python_source("main")
    .add_local_python_source("service")
    .add_local_python_source("pipeline")
)

@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("gemini-api-key"),  # For Gemini API (blog generation)
        modal.Secret.from_name("google-service-account"),  # For Drive upload
        modal.Secret.from_name("openrouter-api-key"),  # For Gemini 3 Pro Image generation
    ],
    timeout=3600,  # 1 hour - blog generation can take 2-10 min, buffer for retries
    max_containers=100,
    memory=2048,  # 2GB memory for blog generation pipeline
)
@modal.concurrent(max_inputs=100)
@modal.asgi_app()
def fastapi_app():
    from main import app
    return app
