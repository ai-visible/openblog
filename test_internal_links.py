#!/usr/bin/env python3
"""
Quick test to verify internal links generation works with sitemap data.
"""

import asyncio
import json
from pathlib import Path
from pipeline.core.execution_context import ExecutionContext
from pipeline.blog_generation.stage_05_internal_links import InternalLinksStage
from pipeline.models.output_schema import ArticleOutput

async def test_internal_links():
    """Test internal links generation with mock sitemap data."""
    
    print('='*80)
    print('TESTING INTERNAL LINKS GENERATION')
    print('='*80)
    print()
    
    # Create mock article data
    article_data = {
        "Headline": "AI Automation in 2025: From Static Scripts to Autonomous Agents",
        "Subtitle": "How agentic AI is rewriting the rules",
        "section_01_title": "What is AI Automation? Beyond the Buzzwords",
        "section_02_title": "Top Use Cases: Where AI Automation Delivers Real Value",
        "section_03_title": "The Rise of Agentic AI: From Tools to Teammates",
    }
    
    structured_data = ArticleOutput(**article_data)
    
    # Create context with sitemap URLs
    context = ExecutionContext(
        job_id="test-internal-links",
        job_config={
            "sitemap_urls": [
                "https://example.com/blog/automation-guide",
                "https://example.com/blog/ai-trends-2025",
                "https://example.com/blog/enterprise-automation",
                "https://example.com/blog/ai-implementation",
            ]
        },
        structured_data=structured_data,
    )
    
    # Initialize Stage 5
    stage = InternalLinksStage()
    
    print("Running Stage 5 with mock sitemap URLs...")
    print(f"  Sitemap URLs: {len(context.job_config.get('sitemap_urls', []))}")
    print()
    
    try:
        # Run Stage 5
        result_context = await stage.execute(context)
        
        # Check results
        pr = result_context.parallel_results
        
        print("RESULTS:")
        print('-'*80)
        
        if 'internal_links_list' in pr:
            links_list = pr['internal_links_list']
            if hasattr(links_list, 'count'):
                count = links_list.count()
                print(f"✅ Internal links generated: {count}")
                
                if count > 0:
                    print("\nLinks:")
                    for i, link in enumerate(links_list.links[:5], 1):
                        print(f"  {i}. {link.title}")
                        print(f"     URL: {link.url}")
                        print(f"     Relevance: {link.relevance}")
                else:
                    print("⚠️  No links generated (URLs might not be accessible)")
            else:
                print(f"⚠️  internal_links_list type: {type(links_list)}")
        else:
            print("❌ internal_links_list not found")
        
        if 'internal_links_html' in pr:
            html = pr['internal_links_html']
            if html:
                print(f"\n✅ Internal links HTML generated: {len(str(html))} chars")
                print(f"   Preview: {str(html)[:200]}...")
            else:
                print("\n⚠️  internal_links_html is empty")
        else:
            print("\n❌ internal_links_html not found")
        
        if 'section_internal_links' in pr:
            section_links = pr['section_internal_links']
            if section_links:
                print(f"\n✅ Section links assigned: {len(section_links)} sections")
                for section_num, links in section_links.items():
                    print(f"   Section {section_num}: {len(links)} links")
            else:
                print("\n⚠️  No section links assigned")
        else:
            print("\n❌ section_internal_links not found")
        
        print()
        print('='*80)
        if pr.get('internal_links_count', 0) > 0:
            print("✅ TEST PASSED: Internal links generation works!")
        else:
            print("⚠️  TEST INCONCLUSIVE: No links generated (may need accessible URLs)")
        print('='*80)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_internal_links())
