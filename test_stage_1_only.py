#!/usr/bin/env python3
"""
Test Stage 1 only - using Stage 0 output.
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
from pipeline.blog_generation import DataFetchStage, PromptBuildStage

async def test_stage_1():
    print("=" * 80)
    print("TESTING STAGE 1: Prompt Build")
    print("=" * 80)
    print()
    
    # First run Stage 0 to get context
    print("Running Stage 0 first...")
    context = ExecutionContext(
        job_id="test-stage-1",
        job_config={
            "primary_keyword": "AI adoption in customer service",
            "company_url": "https://example.com",
            "company_name": "Example Corp",
        }
    )
    stage0 = DataFetchStage()
    context = await stage0.execute(context)
    print(f"✅ Stage 0 complete")
    print()
    
    # Now test Stage 1
    print("Executing Stage 1...")
    stage1 = PromptBuildStage()
    
    start = time.time()
    result = await stage1.execute(context)
    duration = time.time() - start
    
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Stage 1 execution time: {duration:.4f}s")
    print(f"Prompt length: {len(result.prompt)} chars")
    print()
    
    if duration > 1.0:
        print(f"⚠️  WARNING: Stage 1 took {duration:.3f}s (should be <0.1s)")
    else:
        print(f"✅ Stage 1 is fast: {duration:.4f}s")
    
    # Show prompt preview
    if result.prompt:
        print()
        print("Prompt preview (first 200 chars):")
        print("-" * 80)
        print(result.prompt[:200] + "...")
        print("-" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(test_stage_1(), timeout=10.0))
    except asyncio.TimeoutError:
        print("\n❌ TIMEOUT: Stage 1 took longer than 10 seconds!")
        sys.exit(1)


