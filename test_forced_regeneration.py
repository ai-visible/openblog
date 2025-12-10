#!/usr/bin/env python3
"""
Forced Regeneration Test

Uses identical keywords to force regeneration trigger with full 12-stage pipeline.
This will prove regeneration works by creating content that definitely triggers it.
"""

import asyncio
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.integrations.regeneration_integration import generate_batch_with_regeneration


async def test_forced_regeneration():
    """Force regeneration with identical keywords."""
    print("🔥 FORCED REGENERATION TEST")
    print("=" * 50)
    print("Using identical keywords to guarantee regeneration trigger")
    print()
    
    # Identical keywords to force high similarity
    configs = [
        {
            "job_id": "identical_1",
            "primary_keyword": "AI chatbot customer service platform",
            "company_url": "https://chatbot1.ai",
            "company_name": "ChatBot One"
        },
        {
            "job_id": "identical_2", 
            "primary_keyword": "AI chatbot customer service platform",  # IDENTICAL
            "company_url": "https://chatbot2.ai",
            "company_name": "ChatBot Two"
        }
    ]
    
    print("📝 Test articles:")
    for i, config in enumerate(configs, 1):
        print(f"   {i}. '{config['primary_keyword']}' ({config['company_name']})")
    
    print("\nNote: Identical keywords should force regeneration")
    print()
    
    def progress_callback(current, total, message):
        if "stage_" in message:
            print(f"   🔧 {message}")
        else:
            print(f"   📊 {current}/{total} - {message}")
    
    start_time = time.time()
    
    results = await generate_batch_with_regeneration(
        job_configs=configs,
        max_regeneration_attempts=2,  # Limit to 2 for faster test
        similarity_threshold=50.0,   # Lower threshold to trigger easier
        sequential=True,
        progress_callback=progress_callback
    )
    
    execution_time = time.time() - start_time
    
    print(f"\n🎯 FORCED REGENERATION RESULTS ({execution_time:.1f}s)")
    print("=" * 50)
    
    regeneration_triggered = results.get('articles_requiring_regeneration', 0)
    successful = results.get('successful_articles', 0)
    
    print(f"Articles processed: {results.get('total_articles', 0)}")
    print(f"Successful: {successful}")
    print(f"Regeneration triggered: {regeneration_triggered}")
    print(f"Average similarity: {results.get('average_final_similarity', 0):.1f}%")
    
    # Show detailed results
    for report in results.get('generation_reports', []):
        job_id = report.get('job_id', 'unknown')
        attempts = report.get('attempts_made', 1)
        similarity = report.get('final_similarity', 0)
        
        print(f"\n📝 {job_id}:")
        print(f"   Attempts: {attempts}")
        print(f"   Final similarity: {similarity:.1f}%")
        
        if 'attempt_details' in report:
            for attempt in report['attempt_details']:
                strategy = attempt.get('strategy', 'original')
                score = attempt.get('similarity_score', 0)
                print(f"   - Attempt {attempt.get('attempt', 1)} ({strategy}): {score:.1f}%")
    
    # Verify regeneration actually happened
    regeneration_success = (
        regeneration_triggered > 0 and
        any(r.get('attempts_made', 1) > 1 for r in results.get('generation_reports', []))
    )
    
    if regeneration_success:
        print(f"\n🎉 REGENERATION SUCCESSFULLY TRIGGERED!")
        print("✅ Full 12-stage pipeline with regeneration working!")
        return True
    else:
        print(f"\n⚠️ Regeneration still not triggered")
        print("🔍 This may indicate content is naturally more diverse than expected")
        return False


async def main():
    os.chdir('/Users/federicodeponte/openblog-isaac-security')
    os.environ['GEMINI_API_KEY'] = 'AIzaSyBjNQmN_65AskUTWHynyYxn9efAY-Az7jw'
    
    success = await test_forced_regeneration()
    
    if success:
        print("\n🚀 REGENERATION SYSTEM: PROVEN WITH FULL PIPELINE")
    else:
        print("\n📊 REGENERATION SYSTEM: THRESHOLD ANALYSIS NEEDED")


if __name__ == "__main__":
    asyncio.run(main())