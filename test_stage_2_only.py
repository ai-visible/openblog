#!/usr/bin/env python3
"""
Test Stage 2 only - Gemini call (likely bottleneck).
"""

import asyncio
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
from pipeline.blog_generation import DataFetchStage, PromptBuildStage, GeminiCallStage

async def test_stage_2():
    print("=" * 80)
    print("TESTING STAGE 2: Gemini Call (Article Generation)")
    print("=" * 80)
    print()
    print("⚠️  This stage calls Gemini API - will take ~50-60 seconds")
    print()
    
    # Run Stages 0-1 first
    print("Running Stages 0-1 first...")
    context = ExecutionContext(
        job_id="test-stage-2",
        job_config={
            "primary_keyword": "AI adoption in customer service",
            "company_url": "https://example.com",
            "company_name": "Example Corp",
        }
    )
    context = await DataFetchStage().execute(context)
    context = await PromptBuildStage().execute(context)
    print(f"✅ Stages 0-1 complete")
    print(f"   Prompt ready: {len(context.prompt)} chars")
    print()
    
    # Test Stage 2
    print("Executing Stage 2 (Gemini API call)...")
    print("  This will take ~50-60 seconds (Gemini API)")
    print()
    
    stage2 = GeminiCallStage()
    start = time.time()
    
    try:
        result = await asyncio.wait_for(stage2.execute(context), timeout=120.0)
        duration = time.time() - start
        
        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Stage 2 execution time: {duration:.2f}s")
        print(f"Raw article length: {len(result.raw_article)} chars")
        print()
        
        if duration > 90:
            print(f"⚠️  WARNING: Stage 2 took {duration:.1f}s (expected ~50-60s)")
        else:
            print(f"✅ Stage 2 timing is normal: {duration:.1f}s")
        
        # Show article preview
        if result.raw_article:
            print()
            print("Article preview (first 300 chars):")
            print("-" * 80)
            print(result.raw_article[:300] + "...")
            print("-" * 80)
            
    except asyncio.TimeoutError:
        duration = time.time() - start
        print(f"\n❌ TIMEOUT: Stage 2 took longer than 120 seconds!")
        print(f"   Time elapsed: {duration:.1f}s")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_stage_2())


