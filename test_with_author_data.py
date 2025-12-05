#!/usr/bin/env python3
"""
Test blog generation with author data to verify >90 AEO scores
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core import WorkflowEngine
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


async def test_with_author_data():
    """Test blog generation with author data for E-E-A-T scoring."""
    print("=" * 80)
    print("TESTING WITH AUTHOR DATA FOR >90 AEO SCORES")
    print("=" * 80)
    print()
    
    # Verify API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: No API key found")
        return
    
    # Initialize engine
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
    
    # Job config with author data
    job_config = {
        "primary_keyword": "AI customer service automation",
        "company_url": "https://example.com",
        "company_name": "Example Corp",
        # Author data for E-E-A-T scoring
        "author_name": "Sarah Johnson",
        "author_bio": "Sarah Johnson is a Senior Customer Experience Strategist with over 12 years of experience in AI automation and customer service optimization. She holds a Master's degree in Business Analytics and is a certified expert in conversational AI technologies.",
        "author_url": "https://example.com/about/sarah-johnson",
    }
    
    print("🚀 Executing workflow with author data...")
    print(f"   Author: {job_config['author_name']}")
    print(f"   Bio: {job_config['author_bio'][:80]}...")
    print()
    
    start_time = datetime.now()
    context = await engine.execute(
        job_id=f"test-author-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        job_config=job_config
    )
    duration = (datetime.now() - start_time).total_seconds()
    
    # Get results
    aeo_score = context.quality_report.get("metrics", {}).get("aeo_score", 0) if context.quality_report else 0
    aeo_method = context.quality_report.get("metrics", {}).get("aeo_score_method", "unknown") if context.quality_report else "unknown"
    headline = context.structured_data.Headline if context.structured_data else None
    
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"✅ Duration: {duration:.2f}s")
    print(f"📊 AEO Score: {aeo_score}/100")
    print(f"   Method: {aeo_method}")
    print(f"📝 Headline: {headline}")
    print(f"⚠️  Critical Issues: {len(context.quality_report.get('critical_issues', [])) if context.quality_report else 0}")
    
    if aeo_score >= 90:
        print()
        print("🎉 SUCCESS! AEO Score ≥ 90!")
    elif aeo_score >= 85:
        print()
        print("✅ Good! AEO Score ≥ 85 (close to target)")
    else:
        print()
        print("⚠️  AEO Score < 85 - may need further optimization")
    
    # Save results
    output_dir = Path(__file__).parent / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "job_id": context.job_id,
        "duration_seconds": duration,
        "aeo_score": aeo_score,
        "aeo_score_method": aeo_method,
        "headline": headline,
        "has_author_data": True,
        "author_name": job_config.get("author_name"),
        "critical_issues_count": len(context.quality_report.get("critical_issues", [])) if context.quality_report else 0,
    }
    
    output_file = output_dir / f"test_with_author_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n📁 Results saved to: {output_file}")
    
    return aeo_score >= 90


if __name__ == "__main__":
    success = asyncio.run(test_with_author_data())
    sys.exit(0 if success else 1)

