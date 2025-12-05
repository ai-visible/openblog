#!/usr/bin/env python3
"""
Comprehensive Quality Test Script

Runs full article generation and audits all quality metrics.
Generates quality report.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_local = Path(__file__).parent.parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.core import WorkflowEngine
from pipeline.blog_generation import (
    DataFetchStage, PromptBuildStage, GeminiCallStage, ExtractionStage,
    CitationsStage, InternalLinksStage, TableOfContentsStage, MetadataStage,
    FAQPAAStage, ImageStage, CleanupStage, StorageStage,
)
from tests.prompt_engineering.test_comprehensive_quality import ComprehensiveQualityAuditor


async def test_single_article(keyword: str, company_name: str, company_url: str, test_num: int):
    """Generate and audit a single article."""
    print(f"\n{'='*70}")
    print(f"TEST #{test_num}: {keyword}")
    print(f"{'='*70}")
    
    engine = WorkflowEngine()
    engine.register_stages([
        DataFetchStage(), PromptBuildStage(), GeminiCallStage(), ExtractionStage(),
        CitationsStage(), InternalLinksStage(), TableOfContentsStage(), MetadataStage,
        FAQPAAStage(), ImageStage(), CleanupStage(), StorageStage(),
    ])
    
    try:
        context = await engine.execute(
            job_id=f"quality-test-{test_num}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            job_config={
                "primary_keyword": keyword,
                "company_url": company_url,
                "company_name": company_name,
                "language": "en",
                "country": "US",
            }
        )
        
        if not context.validated_article:
            return {'success': False, 'error': 'No article generated'}
        
        article = context.validated_article
        
        # Extract sections
        sections = []
        for i in range(1, 10):
            title_key = f'section_{i:02d}_title'
            content_key = f'section_{i:02d}_content'
            if title_key in article and article[title_key]:
                sections.append({
                    'title': article[title_key],
                    'content': article.get(content_key, '')
                })
        
        # Audit
        auditor = ComprehensiveQualityAuditor()
        audit_result = auditor.audit_article({
            'headline': article.get('headline', '') or article.get('Headline', ''),
            'subtitle': article.get('subtitle', '') or article.get('Subtitle', ''),
            'intro': article.get('intro', '') or article.get('Intro', ''),
            'direct_answer': article.get('direct_answer', '') or article.get('Direct_Answer', ''),
            'sections': sections,
        }, keyword)
        
        return {
            'success': True,
            'keyword': keyword,
            'audit': audit_result,
            'headline': article.get('headline', '') or article.get('Headline', ''),
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


async def run_comprehensive_test():
    """Run comprehensive quality test."""
    print("=" * 70)
    print("COMPREHENSIVE QUALITY TEST")
    print("Testing: All quality metrics across multiple keywords")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verify API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: No API key found")
        return False
    
    print("✅ API key found")
    print()
    
    # Test scenarios
    test_scenarios = [
        {
            'keyword': 'cloud data security best practices',
            'company': 'SecureCloud',
            'url': 'https://example.com'
        },
        {
            'keyword': 'AI customer service automation',
            'company': 'TestCorp',
            'url': 'https://example.com'
        },
        {
            'keyword': 'enterprise workflow automation tools',
            'company': 'WorkflowPro',
            'url': 'https://example.com'
        },
    ]
    
    print(f"📋 Running {len(test_scenarios)} test scenarios...")
    print()
    
    results = []
    for i, scenario in enumerate(test_scenarios, 1):
        result = await test_single_article(
            scenario['keyword'],
            scenario['company'],
            scenario['url'],
            i
        )
        results.append(result)
        
        if result.get('success'):
            audit = result['audit']
            print(f"✅ Test #{i} completed")
            print(f"   Quality Score: {audit['score']}/100")
            print(f"   Keyword mentions: {audit['metrics']['keyword_mentions']} (target: 8-12)")
            print(f"   Grammar errors: {audit['metrics']['grammar_errors']}")
            print(f"   Headline length: {audit['metrics']['headline_length']} (target: 50-60)")
            if audit['issues']:
                print(f"   ⚠️  Issues: {', '.join(audit['issues'][:3])}")
        else:
            print(f"❌ Test #{i} failed: {result.get('error', 'Unknown error')}")
    
    print()
    print("=" * 70)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 70)
    
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    print()
    
    if successful:
        # Aggregate metrics
        avg_score = sum(r['audit']['score'] for r in successful) / len(successful)
        avg_keyword_mentions = sum(r['audit']['metrics']['keyword_mentions'] for r in successful) / len(successful)
        total_grammar_errors = sum(r['audit']['metrics']['grammar_errors'] for r in successful)
        avg_headline_len = sum(r['audit']['metrics']['headline_length'] for r in successful) / len(successful)
        
        print("📊 Aggregate Metrics:")
        print(f"   Average Quality Score: {avg_score:.1f}/100")
        print(f"   Average Keyword Mentions: {avg_keyword_mentions:.1f} (target: 8-12)")
        print(f"   Total Grammar Errors: {total_grammar_errors}")
        print(f"   Average Headline Length: {avg_headline_len:.1f} (target: 50-60)")
        print()
        
        # Check success criteria
        keyword_in_range = sum(1 for r in successful 
                              if 8 <= r['audit']['metrics']['keyword_mentions'] <= 12)
        no_grammar_errors = sum(1 for r in successful 
                                if r['audit']['metrics']['grammar_errors'] == 0)
        headline_compliant = sum(1 for r in successful 
                                if 50 <= r['audit']['metrics']['headline_length'] <= 60)
        high_aeo_score = sum(1 for r in successful 
                            if r['audit']['score'] >= 80)
        
        print("✅ Success Criteria:")
        print(f"   Keyword density in range: {keyword_in_range}/{len(successful)}")
        print(f"   No grammar errors: {no_grammar_errors}/{len(successful)}")
        print(f"   Headline compliant: {headline_compliant}/{len(successful)}")
        print(f"   AEO score ≥80: {high_aeo_score}/{len(successful)}")
        print()
        
        if (keyword_in_range == len(successful) and 
            no_grammar_errors == len(successful) and 
            headline_compliant == len(successful) and
            high_aeo_score == len(successful)):
            print("🎉 ALL SUCCESS CRITERIA MET!")
        else:
            print("⚠️  Some criteria not met - review above")
    
    # Save results
    output_file = Path(__file__).parent.parent / "test_outputs" / f"comprehensive_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            'test_scenarios': test_scenarios,
            'results': results,
            'timestamp': datetime.now().isoformat(),
        }, f, indent=2)
    
    print(f"💾 Results saved to: {output_file}")
    
    return len(successful) == len(results) and len(successful) > 0


if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1)

