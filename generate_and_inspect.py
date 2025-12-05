#!/usr/bin/env python3
"""
Generate new article with improvements and inspect quality.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core.workflow_engine import WorkflowEngine
from pipeline.blog_generation import (
    DataFetchStage,
    PromptBuildStage,
    GeminiCallStage,
    ExtractionStage,
    CitationsStage,
    InternalLinksStage,
    TableOfContentsStage,
    MetadataStage,
    FAQPAAStage,
    ImageStage,
    CleanupStage,
    StorageStage,
)

async def generate_and_inspect():
    """Generate article and inspect quality."""
    print("=" * 80)
    print("GENERATING ARTICLE WITH IMPROVEMENTS")
    print("=" * 80)
    print()
    
    job_config = {
        "primary_keyword": "AI adoption in customer service",
        "company_url": "https://example.com",
        "content_generation_instruction": "Focus on statistics and data-driven insights",
    }
    
    engine = WorkflowEngine()
    engine.register_stages([
        DataFetchStage(),
        PromptBuildStage(),
        GeminiCallStage(),
        ExtractionStage(),
        CitationsStage(),
        InternalLinksStage(),
        TableOfContentsStage(),
        MetadataStage(),
        FAQPAAStage(),
        ImageStage(),
        CleanupStage(),
        StorageStage(),
    ])
    
    result = await engine.execute("improvements-test", job_config)
    
    # Save article
    output_file = "article_with_improvements.json"
    with open(output_file, "w") as f:
        json.dump({
            "validated_article": result.validated_article,
            "quality_report": result.quality_report,
        }, f, indent=2)
    
    print(f"✅ Article saved to: {output_file}")
    print()
    
    # Inspect
    print("=" * 80)
    print("MANUAL QUALITY INSPECTION")
    print("=" * 80)
    print()
    
    import manual_quality_inspection
    manual_quality_inspection.inspect_article(output_file)
    
    return result

if __name__ == "__main__":
    asyncio.run(generate_and_inspect())

