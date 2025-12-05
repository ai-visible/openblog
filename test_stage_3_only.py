#!/usr/bin/env python3
"""
Test Stage 3 only - Structured Data Extraction.
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
from pipeline.blog_generation import (
    DataFetchStage,
    PromptBuildStage,
    GeminiCallStage,
    ExtractionStage,
)

async def test_stage_3():
    print("=" * 80)
    print("TESTING STAGE 3: Structured Data Extraction")
    print("=" * 80)
    print()
    
    # Run Stages 0-2 first
    print("Running Stages 0-2 first...")
    context = ExecutionContext(
        job_id="test-stage-3",
        job_config={
            "primary_keyword": "AI adoption in customer service",
            "company_url": "https://example.com",
            "company_name": "Example Corp",
        }
    )
    
    context = await DataFetchStage().execute(context)
    context = await PromptBuildStage().execute(context)
    print(f"✅ Stages 0-1 complete")
    
    # Stage 2 (Gemini call) - this takes time
    print("  Running Stage 2 (Gemini API call - will take ~2 min)...")
    context = await GeminiCallStage().execute(context)
    print(f"✅ Stage 2 complete")
    print(f"   Raw article: {len(context.raw_article)} chars")
    print()
    
    # Test Stage 3
    print("Executing Stage 3 (Extraction)...")
    stage3 = ExtractionStage()
    
    start = time.time()
    try:
        result = await asyncio.wait_for(stage3.execute(context), timeout=10.0)
        duration = time.time() - start
        
        print()
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Stage 3 execution time: {duration:.4f}s")
        
        if result.structured_data:
            sections = sum(1 for i in range(1, 10) if getattr(result.structured_data, f"Section_{i:02d}_Title", None))
            faqs = sum(1 for i in range(1, 7) if getattr(result.structured_data, f"FAQ_{i:02d}_Question", None))
            print(f"Sections extracted: {sections}")
            print(f"FAQs extracted: {faqs}")
        
        print()
        if duration > 1.0:
            print(f"⚠️  WARNING: Stage 3 took {duration:.3f}s (should be <0.1s)")
        else:
            print(f"✅ Stage 3 is fast: {duration:.4f}s")
            
    except asyncio.TimeoutError:
        duration = time.time() - start
        print(f"\n❌ TIMEOUT: Stage 3 took longer than 10 seconds!")
        print(f"   Time elapsed: {duration:.1f}s")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_stage_3())

