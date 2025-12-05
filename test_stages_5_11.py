#!/usr/bin/env python3
"""
Test Stages 5-11 individually to measure timing.
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
    CitationsStage,
    InternalLinksStage,
    TableOfContentsStage,
    MetadataStage,
    FAQPAAStage,
    ImageStage,
    CleanupStage,
    StorageStage,
)

async def setup_context():
    """Run stages 0-3 to get base context."""
    print("Setting up base context (Stages 0-3)...")
    print("  (This includes Stage 2 Gemini call - will take ~2 min)")
    print()
    
    context = ExecutionContext(
        job_id="test-stages-5-11",
        job_config={
            "primary_keyword": "AI adoption in customer service",
            "company_url": "https://example.com",
            "company_name": "Example Corp",
        }
    )
    
    context = await DataFetchStage().execute(context)
    context = await PromptBuildStage().execute(context)
    context = await GeminiCallStage().execute(context)
    context = await ExtractionStage().execute(context)
    
    print("✅ Base context ready")
    print()
    return context

async def test_stage_5(context):
    """Test Stage 5: Internal Links"""
    print("=" * 80)
    print("TESTING STAGE 5: Internal Links")
    print("=" * 80)
    
    stage = InternalLinksStage()
    start = time.time()
    result = await asyncio.wait_for(stage.execute(context), timeout=30.0)
    duration = time.time() - start
    
    links_count = result.parallel_results.get('internal_links_count', 0)
    print(f"Time: {duration:.4f}s | Links: {links_count}")
    print()
    return result, duration

async def test_stage_6(context):
    """Test Stage 6: Table of Contents"""
    print("=" * 80)
    print("TESTING STAGE 6: Table of Contents")
    print("=" * 80)
    
    stage = TableOfContentsStage()
    start = time.time()
    result = await asyncio.wait_for(stage.execute(context), timeout=10.0)
    duration = time.time() - start
    
    toc_count = len(result.parallel_results.get('toc_dict', {}))
    print(f"Time: {duration:.4f}s | ToC items: {toc_count}")
    print()
    return result, duration

async def test_stage_7(context):
    """Test Stage 7: Metadata"""
    print("=" * 80)
    print("TESTING STAGE 7: Metadata")
    print("=" * 80)
    
    stage = MetadataStage()
    start = time.time()
    result = await asyncio.wait_for(stage.execute(context), timeout=10.0)
    duration = time.time() - start
    
    metadata = result.parallel_results.get('metadata')
    word_count = metadata.word_count if metadata else 0
    print(f"Time: {duration:.4f}s | Words: {word_count}")
    print()
    return result, duration

async def test_stage_8(context):
    """Test Stage 8: FAQ/PAA"""
    print("=" * 80)
    print("TESTING STAGE 8: FAQ/PAA")
    print("=" * 80)
    
    stage = FAQPAAStage()
    start = time.time()
    result = await asyncio.wait_for(stage.execute(context), timeout=10.0)
    duration = time.time() - start
    
    faq_items = result.parallel_results.get('faq_items')
    paa_items = result.parallel_results.get('paa_items')
    faq_count = len(faq_items.items) if hasattr(faq_items, 'items') else (len(faq_items) if isinstance(faq_items, list) else 0)
    paa_count = len(paa_items.items) if hasattr(paa_items, 'items') else (len(paa_items) if isinstance(paa_items, list) else 0)
    print(f"Time: {duration:.4f}s | FAQ: {faq_count}, PAA: {paa_count}")
    print()
    return result, duration

async def test_stage_9(context):
    """Test Stage 9: Image Generation"""
    print("=" * 80)
    print("TESTING STAGE 9: Image Generation")
    print("=" * 80)
    print("⚠️  This calls Replicate API - may take 30-60 seconds")
    
    stage = ImageStage()
    start = time.time()
    try:
        result = await asyncio.wait_for(stage.execute(context), timeout=120.0)
        duration = time.time() - start
        
        image_url = result.parallel_results.get('image_url', '')
        print(f"Time: {duration:.2f}s | Image: {'✅' if image_url else '❌'}")
        print()
        return result, duration
    except asyncio.TimeoutError:
        duration = time.time() - start
        print(f"❌ TIMEOUT after {duration:.1f}s")
        print()
        return context, duration

async def test_stage_10(context):
    """Test Stage 10: Cleanup & Validation"""
    print("=" * 80)
    print("TESTING STAGE 10: Cleanup & Validation")
    print("=" * 80)
    
    # First run parallel stages 4-9 to populate parallel_results
    print("Running parallel stages 4-9 first...")
    parallel_stages = [
        CitationsStage(),
        InternalLinksStage(),
        TableOfContentsStage(),
        MetadataStage(),
        FAQPAAStage(),
        ImageStage(),
    ]
    
    # Run in parallel
    results = await asyncio.gather(*[stage.execute(context) for stage in parallel_stages], return_exceptions=True)
    
    # Merge results
    for result in results:
        if isinstance(result, ExecutionContext):
            context.parallel_results.update(result.parallel_results)
    
    print("✅ Parallel stages complete")
    print()
    
    # Now test Stage 10
    stage = CleanupStage()
    start = time.time()
    result = await asyncio.wait_for(stage.execute(context), timeout=30.0)
    duration = time.time() - start
    
    passed = result.quality_report.get('passed', False) if result.quality_report else False
    print(f"Time: {duration:.4f}s | Quality: {'✅' if passed else '❌'}")
    print()
    return result, duration

async def test_stage_11(context):
    """Test Stage 11: Storage"""
    print("=" * 80)
    print("TESTING STAGE 11: HTML Generation & Storage")
    print("=" * 80)
    
    # Stage 11 needs Stage 10 output
    if not context.validated_article:
        print("⚠️  Stage 10 not run, running it first...")
        context, _ = await test_stage_10(context)
    
    stage = StorageStage()
    start = time.time()
    result = await asyncio.wait_for(stage.execute(context), timeout=30.0)
    duration = time.time() - start
    
    success = result.storage_result.get('success', False) if result.storage_result else False
    final_article = result.final_article or {}
    html_content = final_article.get('html_content', '') if isinstance(final_article, dict) else ''
    html_len = len(html_content) if isinstance(html_content, str) else 0
    print(f"Time: {duration:.4f}s | Success: {'✅' if success else '❌'} | HTML: {html_len} chars")
    print()
    return result, duration

async def main():
    print("=" * 80)
    print("TESTING STAGES 5-11")
    print("=" * 80)
    print()
    
    # Setup
    context = await setup_context()
    
    # Test each stage
    results = {}
    
    print("Testing parallel stages (5-9)...")
    print()
    
    context, results[5] = await test_stage_5(context)
    context, results[6] = await test_stage_6(context)
    context, results[7] = await test_stage_7(context)
    context, results[8] = await test_stage_8(context)
    context, results[9] = await test_stage_9(context)
    
    print("Testing sequential stages (10-11)...")
    print()
    
    context, results[10] = await test_stage_10(context)
    context, results[11] = await test_stage_11(context)
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("Stage timings:")
    for stage_num in sorted(results.keys()):
        duration = results[stage_num]
        status = "✅" if duration < 5.0 else "⚠️" if duration < 30.0 else "❌"
        print(f"  Stage {stage_num}: {duration:.4f}s {status}")
    
    total = sum(results.values())
    print()
    print(f"Total (Stages 5-11): {total:.2f}s ({total/60:.1f} min)")

if __name__ == "__main__":
    asyncio.run(main())

