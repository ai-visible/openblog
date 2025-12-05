#!/usr/bin/env python3
"""
Local test script for blog generation workflow.
Tests the original version locally before creating edge function.
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


async def test_local_blog_generation():
    """Test blog generation locally."""
    print("=" * 80)
    print("LOCAL BLOG GENERATION TEST")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verify API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: No API key found")
        print("   Set GOOGLE_API_KEY or GOOGLE_GEMINI_API_KEY environment variable")
        return None
    
    print("✅ API key found")
    print()
    
    # Create workflow engine
    engine = WorkflowEngine()
    
    # Register all stages
    print("📋 Registering all 12 stages...")
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
    print(f"✅ Registered {len(engine.list_stages())} stages")
    print()
    
    # Test input - using a real keyword for testing
    job_config = {
        "primary_keyword": "AI customer service automation",
        "company_url": "https://example.com",
    }
    
    print("📝 Test Configuration:")
    print(f"   Primary Keyword: {job_config['primary_keyword']}")
    print(f"   Company URL: {job_config['company_url']}")
    print()
    print("⏱️  Expected duration: 5-10 minutes (stages 4-9 run in parallel)")
    print()
    
    try:
        # Execute full workflow
        print("🚀 Starting workflow execution...")
        print()
        
        start_time = datetime.now()
        context = await engine.execute(
            job_id=f"local-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            job_config=job_config
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Print results summary
        print()
        print("=" * 80)
        print("GENERATION RESULTS")
        print("=" * 80)
        print()
        
        # Basic info
        if context.structured_data:
            print(f"✅ Headline: {context.structured_data.Headline}")
            print()
        
        # Quality metrics
        if context.quality_report:
            metrics = context.quality_report.get("metrics", {})
            aeo_score = metrics.get("aeo_score", 0)
            print(f"📊 AEO Score: {aeo_score}/100")
            print(f"   Method: {metrics.get('aeo_score_method', 'N/A')}")
            
            critical_issues = len(context.quality_report.get("critical_issues", []))
            if critical_issues > 0:
                print(f"⚠️  Critical Issues: {critical_issues}")
            else:
                print("✅ No Critical Issues")
            print()
        
        # Execution times
        if hasattr(context, 'execution_times') and context.execution_times:
            print("⏱️  Execution Times:")
            for stage, time_taken in sorted(context.execution_times.items()):
                print(f"   {stage}: {time_taken:.2f}s")
            total_time = sum(context.execution_times.values())
            print(f"   Total: {total_time:.2f}s")
            print()
        
        # Save results for comparison
        output_dir = Path(__file__).parent / "test_outputs"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = output_dir / f"local_test_{timestamp}.json"
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "job_id": context.job_id,
            "job_config": job_config,
            "duration_seconds": duration,
            "execution_times": context.execution_times if hasattr(context, 'execution_times') else {},
            "headline": context.structured_data.Headline if context.structured_data else None,
            "aeo_score": context.quality_report.get("metrics", {}).get("aeo_score", 0) if context.quality_report else 0,
            "critical_issues_count": len(context.quality_report.get("critical_issues", [])) if context.quality_report else 0,
            "has_html": bool(context.final_article and context.final_article.get("html_content")),
            "has_validated_article": bool(context.validated_article),
        }
        
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"✅ Results saved to: {output_file}")
        print()
        
        # Save full article for inspection
        if context.final_article:
            article_file = output_dir / f"local_article_{timestamp}.json"
            with open(article_file, "w") as f:
                json.dump({
                    "validated_article": context.validated_article,
                    "final_article": context.final_article,
                    "quality_report": context.quality_report,
                }, f, indent=2, default=str)
            print(f"✅ Full article saved to: {article_file}")
            print()
        
        print("=" * 80)
        print("✅ LOCAL TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        return context
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ LOCAL TEST FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(test_local_blog_generation())
    sys.exit(0 if result else 1)

