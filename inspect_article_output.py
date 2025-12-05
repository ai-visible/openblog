#!/usr/bin/env python3
"""
Deep inspection of generated article output.
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

from pipeline.core import ExecutionContext
from pipeline.core.workflow_engine import WorkflowEngine

async def generate_and_inspect():
    """Generate article and inspect output."""
    print("=" * 80)
    print("GENERATING ARTICLE FOR DEEP INSPECTION")
    print("=" * 80)
    print()
    
    job_config = {
        "primary_keyword": "AI adoption in customer service",
        "company_url": "https://example.com",
        "company_name": "Example Corp",
    }
    
    engine = WorkflowEngine()
    
    # Register all stages
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
    
    print("Generating article...")
    context = await engine.execute("inspection-test", job_config)
    
    # Save full output
    output_file = Path("article_output_full.json")
    with open(output_file, "w") as f:
        json.dump({
            "validated_article": context.validated_article,
            "quality_report": context.quality_report,
            "structured_data": context.structured_data.model_dump() if context.structured_data else None,
        }, f, indent=2, default=str)
    
    print(f"✅ Article generated and saved to {output_file}")
    print()
    
    return context

if __name__ == "__main__":
    asyncio.run(generate_and_inspect())

