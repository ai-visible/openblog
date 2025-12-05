#!/usr/bin/env python3
"""
Test Stage 4 only - Citations validation (likely the real bottleneck).
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core import ExecutionContext
from pipeline.blog_generation import (
    DataFetchStage,
    PromptBuildStage,
    GeminiCallStage,
    ExtractionStage,
    CitationsStage,
)

async def test_stage_4():
    print("=" * 80)
    print("TESTING STAGE 4: Citations Validation")
    print("=" * 80)
    print()
    print("⚠️  This stage validates URLs - may take time if validation enabled")
    print()
    
    # Run Stages 0-3 first
    print("Running Stages 0-3 first...")
    context = ExecutionContext(
        job_id="test-stage-4",
        job_config={
            "primary_keyword": "AI adoption in customer service",
            "company_url": "https://example.com",
            "company_name": "Example Corp",
        }
    )
    
    stages = [
        DataFetchStage(),
        PromptBuildStage(),
        GeminiCallStage(),
        ExtractionStage(),
    ]
    
    for i, stage in enumerate(stages):
        print(f"  Running Stage {i}...")
        context = await stage.execute(context)
    
    print(f"✅ Stages 0-3 complete")
    if context.structured_data:
        sources = context.structured_data.Sources or ""
        citation_count = sources.count('[') if sources else 0
        print(f"   Citations found: {citation_count}")
    print()
    
    # Test Stage 4
    print("Executing Stage 4 (Citations validation)...")
    print()
    
    stage4 = CitationsStage()
    start = time.time()
    
    try:
        result = await asyncio.wait_for(stage4.execute(context), timeout=600.0)  # 10 min timeout
        duration = time.time() - start
        
        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Stage 4 execution time: {duration:.2f}s ({duration/60:.1f} minutes)")
        
        citations_count = result.parallel_results.get('citations_count', 0)
        print(f"Citations processed: {citations_count}")
        print()
        
        if duration > 300:  # 5 minutes
            print(f"❌ CRITICAL: Stage 4 took {duration/60:.1f} minutes!")
            print("   This is the bottleneck - citation validation is too slow")
        elif duration > 60:  # 1 minute
            print(f"⚠️  WARNING: Stage 4 took {duration:.1f}s (expected <60s)")
        else:
            print(f"✅ Stage 4 timing is acceptable: {duration:.1f}s")
            
    except asyncio.TimeoutError:
        duration = time.time() - start
        print(f"\n❌ TIMEOUT: Stage 4 took longer than 10 minutes!")
        print(f"   Time elapsed: {duration/60:.1f} minutes")
        print("   Citation validation is blocking the workflow")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_stage_4())


