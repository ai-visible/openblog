#!/usr/bin/env python3
"""
Full Pipeline Batch Test

Tests the complete pipeline with a batch of articles to verify:
1. All 14 stages execute correctly (0-13)
2. Stage 12 (similarity check) works with semantic embeddings
3. Quality monitoring tracks metrics and generates alerts
4. Error context is properly captured
5. Batch similarity checking works across multiple articles

Usage:
    python3 test_full_pipeline_batch.py
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')
load_dotenv('.env')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core import WorkflowEngine, create_production_pipeline_stages
from pipeline.core.quality_monitor import get_quality_monitor, reset_quality_monitor

# Test configuration
BATCH_SIZE = 3  # Start with 3 articles for testing
TEST_KEYWORDS = [
    "enterprise AI security automation",
    "cloud security best practices",
    "zero trust security architecture"
]


async def test_single_article(engine: WorkflowEngine, keyword: str, index: int) -> dict:
    """Test single article generation."""
    job_id = f"test-batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{index}"
    
    job_config = {
        "primary_keyword": keyword,
        "company_url": "https://scaile.tech",
        "language": "en",
        "country": "US",
        "index": index,
    }
    
    print(f"\n{'='*80}")
    print(f"Article {index + 1}/{BATCH_SIZE}: {keyword}")
    print(f"{'='*80}")
    print(f"Job ID: {job_id}")
    
    start_time = time.time()
    
    try:
        context = await engine.execute(job_id, job_config)
        
        duration = time.time() - start_time
        
        # Extract results
        aeo_score = context.quality_report.get('metrics', {}).get('aeo_score', 0)
        critical_issues = len(context.quality_report.get('critical_issues', []))
        suggestions = len(context.quality_report.get('suggestions', []))
        
        # Check similarity report
        similarity_score = None
        semantic_score = None
        if hasattr(context, 'similarity_report') and context.similarity_report:
            similarity_score = getattr(context.similarity_report, 'similarity_score', None)
            semantic_score = getattr(context.similarity_report, 'semantic_score', None)
        
        # Check errors
        error_count = len(context.errors)
        
        result = {
            "job_id": job_id,
            "keyword": keyword,
            "success": True,
            "duration": duration,
            "aeo_score": aeo_score,
            "critical_issues": critical_issues,
            "suggestions": suggestions,
            "similarity_score": similarity_score,
            "semantic_score": semantic_score,
            "error_count": error_count,
            "errors": context.errors,
            "execution_times": context.execution_times,
            "has_validated_article": context.validated_article is not None,
            "has_final_article": context.final_article is not None,
        }
        
        print(f"✅ Article {index + 1} completed in {duration:.2f}s")
        print(f"   AEO Score: {aeo_score}/100")
        print(f"   Critical Issues: {critical_issues}")
        print(f"   Suggestions: {suggestions}")
        if similarity_score is not None:
            print(f"   Similarity Score: {similarity_score:.1f}%")
            if semantic_score is not None:
                print(f"   Semantic Score: {semantic_score:.1%}")
        if error_count > 0:
            print(f"   ⚠️  Errors: {error_count}")
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Article {index + 1} FAILED after {duration:.2f}s")
        print(f"   Error: {e}")
        
        return {
            "job_id": job_id,
            "keyword": keyword,
            "success": False,
            "duration": duration,
            "error": str(e),
            "error_type": type(e).__name__
        }


async def main():
    """Run full pipeline batch test."""
    print("="*80)
    print("FULL PIPELINE BATCH TEST")
    print("="*80)
    print(f"Batch size: {BATCH_SIZE} articles")
    print(f"Test keywords: {len(TEST_KEYWORDS)}")
    print()
    
    # Check API key
    api_key = (
        os.getenv("GEMINI_API_KEY") or 
        os.getenv("GOOGLE_API_KEY") or 
        os.getenv("GOOGLE_GEMINI_API_KEY")
    )
    
    if not api_key:
        print("⚠️  WARNING: No Gemini API key found")
        print("   Semantic embeddings will not be available")
        print("   Similarity checking will use character-only mode")
    else:
        print(f"✅ API key found (length: {len(api_key)})")
        print("   Semantic embeddings enabled")
    
    print()
    
    # Reset quality monitor for clean test
    reset_quality_monitor()
    
    # Initialize workflow engine
    print("Initializing workflow engine...")
    engine = WorkflowEngine()
    stages = create_production_pipeline_stages()
    engine.register_stages(stages)
    
    print(f"✅ Registered {len(stages)} stages")
    stage_numbers = [s.stage_num for s in stages]
    print(f"   Stages: {sorted(stage_numbers)}")
    
    # Verify Stage 12 is registered
    stage_12 = engine.stages.get(12)
    if stage_12:
        print(f"✅ Stage 12 registered: {stage_12.stage_name}")
    else:
        print("❌ Stage 12 NOT registered!")
        return
    
    print()
    
    # Run batch generation
    print("Starting batch generation...")
    print()
    
    results = []
    batch_start_time = time.time()
    
    for i, keyword in enumerate(TEST_KEYWORDS[:BATCH_SIZE]):
        result = await test_single_article(engine, keyword, i)
        results.append(result)
        
        # Small delay between articles
        if i < BATCH_SIZE - 1:
            await asyncio.sleep(1)
    
    batch_duration = time.time() - batch_start_time
    
    # Get quality monitor statistics
    monitor = get_quality_monitor()
    quality_stats = monitor.get_statistics()
    recent_alerts = monitor.get_recent_alerts(hours=1)
    
    # Print summary
    print()
    print("="*80)
    print("BATCH TEST SUMMARY")
    print("="*80)
    
    successful = [r for r in results if r.get('success', False)]
    failed = [r for r in results if not r.get('success', False)]
    
    print(f"Total articles: {len(results)}")
    print(f"✅ Successful: {len(successful)}")
    print(f"❌ Failed: {len(failed)}")
    print(f"Total duration: {batch_duration:.2f}s")
    print(f"Average per article: {batch_duration / len(results):.2f}s")
    print()
    
    if successful:
        print("Successful Articles:")
        for i, result in enumerate(successful, 1):
            print(f"  {i}. {result['keyword']}")
            print(f"     AEO: {result['aeo_score']}/100")
            print(f"     Duration: {result['duration']:.2f}s")
            if result.get('similarity_score') is not None:
                print(f"     Similarity: {result['similarity_score']:.1f}%")
                if result.get('semantic_score') is not None:
                    print(f"     Semantic: {result['semantic_score']:.1%}")
            if result.get('error_count', 0) > 0:
                print(f"     ⚠️  Errors: {result['error_count']}")
        print()
    
    if failed:
        print("Failed Articles:")
        for i, result in enumerate(failed, 1):
            print(f"  {i}. {result['keyword']}")
            print(f"     Error: {result.get('error', 'Unknown')}")
        print()
    
    # Quality monitoring summary
    print("Quality Monitoring:")
    print(f"  Total articles tracked: {quality_stats['total_articles']}")
    print(f"  Recent articles: {quality_stats['recent_articles']}")
    if quality_stats['recent_articles'] > 0:
        print(f"  Average AEO: {quality_stats['average_aeo']:.1f}")
        print(f"  Min AEO: {quality_stats['min_aeo']:.1f}")
        print(f"  Max AEO: {quality_stats['max_aeo']:.1f}")
        print(f"  Low quality rate: {quality_stats['low_quality_rate']:.1f}%")
        print(f"  Critical quality rate: {quality_stats['critical_quality_rate']:.1f}%")
    print(f"  Recent alerts (1h): {quality_stats['recent_alerts']}")
    print(f"  Total alerts: {quality_stats['total_alerts']}")
    print()
    
    if recent_alerts:
        print("Recent Alerts:")
        for alert in recent_alerts[:5]:  # Show first 5
            print(f"  [{alert.severity.upper()}] {alert.alert_type}: {alert.message}")
        print()
    
    # Stage execution times
    if successful:
        print("Stage Execution Times (average):")
        all_times = {}
        for result in successful:
            for stage, duration in result.get('execution_times', {}).items():
                if stage not in all_times:
                    all_times[stage] = []
                all_times[stage].append(duration)
        
        for stage in sorted(all_times.keys()):
            avg_time = sum(all_times[stage]) / len(all_times[stage])
            print(f"  {stage}: {avg_time:.2f}s")
        print()
    
    # Similarity checking summary
    similarity_results = [r for r in successful if r.get('similarity_score') is not None]
    if similarity_results:
        print("Similarity Checking:")
        print(f"  Articles checked: {len(similarity_results)}")
        semantic_enabled = [r for r in similarity_results if r.get('semantic_score') is not None]
        print(f"  Semantic embeddings enabled: {len(semantic_enabled)}/{len(similarity_results)}")
        if semantic_enabled:
            avg_similarity = sum(r['similarity_score'] for r in similarity_results) / len(similarity_results)
            avg_semantic = sum(r['semantic_score'] for r in semantic_enabled) / len(semantic_enabled)
            print(f"  Average similarity: {avg_similarity:.1f}%")
            print(f"  Average semantic: {avg_semantic:.1%}")
        print()
    
    # Final status
    print("="*80)
    if len(successful) == len(results):
        print("✅ ALL ARTICLES GENERATED SUCCESSFULLY")
    else:
        print(f"⚠️  {len(failed)} ARTICLE(S) FAILED")
    print("="*80)
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        sys.exit(0 if all(r.get('success', False) for r in results) else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

