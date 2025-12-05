#!/usr/bin/env python3
"""
Test each stage individually to identify bottlenecks.

Usage:
    python3.13 test_stages_individually.py
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

from pipeline.core import WorkflowEngine, ExecutionContext
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


async def test_stage(stage_num: int, stage_name: str, stage_instance, context: ExecutionContext):
    """Test a single stage and report timing."""
    print(f"\n{'=' * 80}")
    print(f"TESTING STAGE {stage_num}: {stage_name}")
    print(f"{'=' * 80}")
    
    start_time = time.time()
    try:
        result_context = await stage_instance.execute(context)
        duration = time.time() - start_time
        
        print(f"✅ Stage {stage_num} completed in {duration:.2f}s")
        
        # Show what was produced
        if hasattr(result_context, 'parallel_results') and result_context.parallel_results:
            print(f"   Parallel results keys: {list(result_context.parallel_results.keys())}")
        if hasattr(result_context, 'validated_article') and result_context.validated_article:
            print(f"   Validated article: {len(result_context.validated_article)} fields")
        if hasattr(result_context, 'raw_article') and result_context.raw_article:
            print(f"   Raw article: {len(result_context.raw_article)} chars")
        if hasattr(result_context, 'structured_data') and result_context.structured_data:
            print(f"   Structured data: {type(result_context.structured_data).__name__}")
        
        return result_context, duration, None
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Stage {stage_num} FAILED after {duration:.2f}s: {e}")
        import traceback
        traceback.print_exc()
        return context, duration, e


async def main():
    """Test all stages individually."""
    print("=" * 80)
    print("INDIVIDUAL STAGE TESTING")
    print("=" * 80)
    print()
    print("This will test each stage separately to identify bottlenecks.")
    print()
    
    # Setup
    job_config = {
        "primary_keyword": "AI adoption in customer service",
        "company_url": "https://example.com",
        "company_name": "Example Corp",
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
    
    context = ExecutionContext(job_id="test-individual", job_config=job_config)
    
    # Test each stage sequentially
    stages_to_test = [
        (0, "Data Fetch", engine.get_stage(0)),
        (1, "Prompt Build", engine.get_stage(1)),
        (2, "Gemini Call", engine.get_stage(2)),
        (3, "Extraction", engine.get_stage(3)),
        (4, "Citations", engine.get_stage(4)),
        (5, "Internal Links", engine.get_stage(5)),
        (6, "Table of Contents", engine.get_stage(6)),
        (7, "Metadata", engine.get_stage(7)),
        (8, "FAQ/PAA", engine.get_stage(8)),
        (9, "Image", engine.get_stage(9)),
        (10, "Cleanup", engine.get_stage(10)),
        (11, "Storage", engine.get_stage(11)),
    ]
    
    results = {}
    total_time = 0
    
    for stage_num, stage_name, stage_instance in stages_to_test:
        if not stage_instance:
            print(f"\n⚠️  Stage {stage_num} not registered, skipping")
            continue
        
        context, duration, error = await test_stage(stage_num, stage_name, stage_instance, context)
        results[stage_num] = {
            'name': stage_name,
            'duration': duration,
            'error': error
        }
        total_time += duration
        
        if error:
            print(f"\n⚠️  Stopping due to error in Stage {stage_num}")
            break
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    print(f"{'Stage':<25} {'Duration':<15} {'Status'}")
    print("-" * 80)
    
    for stage_num in sorted(results.keys()):
        result = results[stage_num]
        status = "✅ PASS" if not result['error'] else "❌ FAIL"
        print(f"{result['name']:<25} {result['duration']:>8.2f}s      {status}")
    
    print("-" * 80)
    print(f"{'TOTAL':<25} {total_time:>8.2f}s")
    print()
    
    # Identify bottlenecks
    slow_stages = [(num, r['name'], r['duration']) for num, r in results.items() if r['duration'] > 5.0]
    if slow_stages:
        print("⚠️  SLOW STAGES (>5s):")
        for num, name, duration in sorted(slow_stages, key=lambda x: x[2], reverse=True):
            print(f"   Stage {num} ({name}): {duration:.2f}s")
        print()
    
    print("✅ Individual stage testing complete!")


if __name__ == "__main__":
    asyncio.run(main())

