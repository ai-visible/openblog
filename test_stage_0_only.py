#!/usr/bin/env python3
"""
Test Stage 0 only - minimal test excluding import time.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

# NOW measure imports
import_start = time.time()
from pipeline.core import ExecutionContext
from pipeline.blog_generation import DataFetchStage
import_time = time.time() - import_start

print(f"Import time: {import_time:.3f}s")
print()

# Test Stage 0
async def test_stage_0():
    print("=" * 80)
    print("TESTING STAGE 0: Data Fetch & Auto-Detection")
    print("=" * 80)
    print()
    
    # Create context
    context_start = time.time()
    context = ExecutionContext(
        job_id="test-stage-0",
        job_config={
            "primary_keyword": "AI adoption in customer service",
            "company_url": "https://example.com",
            "company_name": "Example Corp",
        }
    )
    context_time = time.time() - context_start
    print(f"Context creation: {context_time:.4f}s")
    
    # Create stage
    stage_start = time.time()
    stage = DataFetchStage()
    stage_time = time.time() - stage_start
    print(f"Stage creation: {stage_time:.4f}s")
    
    # Execute stage with detailed timing
    print()
    print("Executing Stage 0...")
    print("  (Breaking down into sub-steps)")
    
    execute_start = time.time()
    
    # Step 1: Validate input
    step1_start = time.time()
    stage._validate_input(context)
    step1_time = time.time() - step1_start
    print(f"    Step 1 (validate_input): {step1_time:.4f}s")
    
    # Step 2: Auto-detect company
    step2_start = time.time()
    company_data = await stage._auto_detect_company(
        context.job_config.get("company_url", "")
    )
    step2_time = time.time() - step2_start
    print(f"    Step 2 (auto_detect_company): {step2_time:.4f}s")
    
    # Step 3: Apply overrides
    step3_start = time.time()
    company_data = stage._apply_overrides(company_data, context.job_config)
    step3_time = time.time() - step3_start
    print(f"    Step 3 (apply_overrides): {step3_time:.4f}s")
    
    # Step 4: Build context
    step4_start = time.time()
    context.company_data = company_data
    context.language = company_data.get("company_language", "en")
    context.blog_page = stage._build_blog_page(context.job_config, company_data)
    context.job_config = stage._normalize_job_config(context.job_config)
    step4_time = time.time() - step4_start
    print(f"    Step 4 (build_context): {step4_time:.4f}s")
    
    result = context
    execute_time = time.time() - execute_start
    
    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Stage 0 execution time: {execute_time:.4f}s")
    print()
    print(f"Company: {result.company_data.get('company_name', 'N/A')}")
    print(f"Language: {result.language}")
    print(f"Keyword: {result.job_config.get('primary_keyword', 'N/A')}")
    print()
    
    if execute_time > 0.1:
        print(f"⚠️  WARNING: Stage 0 took {execute_time:.3f}s (should be <0.01s)")
        print("   This suggests there's a bottleneck!")
    else:
        print(f"✅ Stage 0 is fast: {execute_time:.4f}s")

if __name__ == "__main__":
    try:
        # Add 2 second timeout (Stage 0 should be instant)
        result = asyncio.run(asyncio.wait_for(test_stage_0(), timeout=2.0))
    except asyncio.TimeoutError:
        print("\n" + "=" * 80)
        print("❌ TIMEOUT: Stage 0 took longer than 2 seconds!")
        print("=" * 80)
        print("This should be instant (<0.01s). Something is blocking.")
        print()
        print("Possible causes:")
        print("  1. Slow imports (check import time above)")
        print("  2. Blocking operation in ExecutionContext.__init__")
        print("  3. Blocking operation in DataFetchStage.__init__")
        print("  4. Network call somewhere (shouldn't happen in Stage 0)")
        sys.exit(1)

