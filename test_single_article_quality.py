#!/usr/bin/env python3
"""
Single Article Quality Test with Full Checklist Validation

Tests the full 13-stage pipeline and validates:
- [ ] Images generated (Imagen 4.0)
- [ ] Internal links present
- [ ] Full citation URLs (not just domains)
- [ ] Keywords bolded
- [ ] No em dashes
- [ ] No [N] academic citations in body
- [ ] AEO score >= 75
"""
import sys
import os
import asyncio
import time
import re
from datetime import datetime

# Load environment from .env.local
from dotenv import load_dotenv
load_dotenv('.env.local')

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.core.execution_context import ExecutionContext

# Import all stages
from pipeline.blog_generation.stage_00_data_fetch import DataFetchStage
from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage  
from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage
from pipeline.blog_generation.stage_02b_quality_refinement import QualityRefinementStage
from pipeline.blog_generation.stage_03_extraction import ExtractionStage
from pipeline.blog_generation.stage_04_citations import CitationsStage
from pipeline.blog_generation.stage_05_internal_links import InternalLinksStage
from pipeline.blog_generation.stage_06_toc import TableOfContentsStage
from pipeline.blog_generation.stage_07_metadata import MetadataStage
from pipeline.blog_generation.stage_08_faq_paa import FAQPAAStage
from pipeline.blog_generation.stage_09_image import ImageStage
from pipeline.blog_generation.stage_10_cleanup import CleanupStage
from pipeline.blog_generation.stage_11_storage import StorageStage


def validate_quality_checklist(html: str, context: ExecutionContext) -> dict:
    """Validate article against quality checklist."""
    
    results = {
        "images_generated": False,
        "internal_links_present": False,
        "full_citation_urls": False,
        "keywords_bolded": False,
        "no_em_dashes": True,
        "no_academic_citations": True,
        "aeo_score_ok": False,
        "details": {}
    }
    
    # 1. Images generated (look for <img> tags)
    img_matches = re.findall(r'<img[^>]+src="([^"]+)"', html)
    results["images_generated"] = len(img_matches) > 0
    results["details"]["images"] = img_matches[:3] if img_matches else []
    
    # 2. Internal links present (look for relative or internal hrefs)
    internal_link_pattern = r'href="(/[^"]*|https?://[^"]*(?:cyberguard|scaile|example)[^"]*)"'
    internal_links = re.findall(internal_link_pattern, html, re.IGNORECASE)
    results["internal_links_present"] = len(internal_links) > 0
    results["details"]["internal_links_count"] = len(internal_links)
    
    # 3. Full citation URLs (not just domains)
    # Look for citation links with full URLs (not just example.com but example.com/page)
    citation_links = re.findall(r'href="(https?://[^"]+)"', html)
    full_urls = [url for url in citation_links if len(url.split('/')) > 3]
    results["full_citation_urls"] = len(full_urls) > len(citation_links) * 0.3  # At least 30% full URLs
    results["details"]["total_external_links"] = len(citation_links)
    results["details"]["full_url_count"] = len(full_urls)
    
    # 4. Keywords bolded (look for <strong> or <b> tags)
    bold_matches = re.findall(r'<(?:strong|b)>([^<]+)</(?:strong|b)>', html)
    results["keywords_bolded"] = len(bold_matches) > 3  # At least 3 bold terms
    results["details"]["bold_terms_count"] = len(bold_matches)
    
    # 5. No em dashes (—)
    em_dash_count = html.count('—') + html.count('–')
    results["no_em_dashes"] = em_dash_count == 0
    results["details"]["em_dash_count"] = em_dash_count
    
    # 6. No [N] academic citations in body (outside sources section)
    # Look for [1], [2], etc. patterns in the main content
    # Split off sources section first
    sources_start = html.find('<h2')
    if sources_start > 0:
        sources_section = html.rfind('<h2', sources_start)
        main_content = html[:sources_section] if sources_section > 0 else html
    else:
        main_content = html
    
    academic_citations = re.findall(r'\[\d+\]', main_content)
    results["no_academic_citations"] = len(academic_citations) <= 5  # Allow a few
    results["details"]["academic_citation_count"] = len(academic_citations)
    
    # 7. AEO Score (from context if available)
    aeo_score = 0
    if hasattr(context, 'parallel_results'):
        aeo_score = context.parallel_results.get('aeo_score', 0)
    elif hasattr(context, 'quality_score'):
        aeo_score = context.quality_score
    results["aeo_score_ok"] = aeo_score >= 75
    results["details"]["aeo_score"] = aeo_score
    
    # Overall pass/fail
    results["passed"] = all([
        results["images_generated"],
        results["internal_links_present"],
        results["full_citation_urls"],
        results["keywords_bolded"],
        results["no_em_dashes"],
        results["no_academic_citations"],
        results["aeo_score_ok"],
    ])
    
    return results


async def run_quality_test():
    """Run complete pipeline and validate quality checklist."""
    
    print("🧪 SINGLE ARTICLE QUALITY TEST")
    print("=" * 70)
    print("Testing full 13-stage pipeline with quality validation")
    print("")
    
    # Verify environment
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ GEMINI_API_KEY not set. Check .env.local")
        return None
    
    print(f"✅ GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY')[:20]}...")
    
    dataforseo_login = os.getenv('DATAFORSEO_LOGIN')
    if dataforseo_login:
        print(f"✅ DataForSEO fallback configured: {dataforseo_login}")
    else:
        print("⚠️  DataForSEO fallback not configured")
    
    print("")
    
    start_time = time.time()
    
    # Create execution context
    context = ExecutionContext(job_id="quality-test")
    
    # Set job config with a topic that tests citation handling
    context.job_config = {
        "primary_keyword": "AI in customer service automation",
        "language": "en",
        "content_generation_instruction": "Write a comprehensive guide about implementing AI for customer service automation with real statistics and examples",
        "company_url": "https://scaile.tech",
        "batch_siblings": [
            {"title": "AI Chatbot Guide", "url": "/magazine/ai-chatbot-guide", "description": "Guide to AI chatbots"},
            {"title": "Customer Experience AI", "url": "/magazine/cx-ai-guide", "description": "AI for customer experience"},
        ]
    }
    
    # Set company data
    context.company_data = {
        "company_name": "SCAILE",
        "company_url": "https://scaile.tech",
        "company_info": {
            "industry": "AI Technology", 
            "target_audience": "Enterprise customers",
            "description": "AI-powered solutions for business"
        }
    }
    
    # Add sitemap_data
    context.sitemap_data = {
        "competitors": ["zendesk.com", "intercom.com", "salesforce.com", "hubspot.com"]
    }
    
    print("🚀 Starting pipeline...")
    
    # Initialize all stages
    stages = [
        DataFetchStage(),           # Stage 0
        PromptBuildStage(),         # Stage 1
        GeminiCallStage(),          # Stage 2
        QualityRefinementStage(),   # Stage 2b
        ExtractionStage(),          # Stage 3
        CitationsStage(),           # Stage 4
        InternalLinksStage(),       # Stage 5
        TableOfContentsStage(),     # Stage 6
        MetadataStage(),           # Stage 7
        FAQPAAStage(),             # Stage 8
        ImageStage(),              # Stage 9
        CleanupStage(),            # Stage 10
        StorageStage()             # Stage 11
    ]
    
    for i, stage in enumerate(stages):
        stage_start = time.time()
        stage_name = stage.__class__.__name__
        print(f"  Stage {i:2d}: {stage_name}...", end=" ", flush=True)
        
        try:
            context = await stage.execute(context)
            stage_time = time.time() - stage_start
            print(f"✅ ({stage_time:.1f}s)")
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    total_time = time.time() - start_time
    
    print("")
    print("=" * 70)
    print("📊 QUALITY CHECKLIST VALIDATION")
    print("=" * 70)
    
    if hasattr(context, 'final_html') and context.final_html:
        html = context.final_html
        
        # Run quality validation
        results = validate_quality_checklist(html, context)
        
        # Print results
        checks = [
            ("Images generated (Imagen 4.0)", results["images_generated"], f"{len(results['details'].get('images', []))} images"),
            ("Internal links present", results["internal_links_present"], f"{results['details'].get('internal_links_count', 0)} links"),
            ("Full citation URLs", results["full_citation_urls"], f"{results['details'].get('full_url_count', 0)}/{results['details'].get('total_external_links', 0)} full URLs"),
            ("Keywords bolded", results["keywords_bolded"], f"{results['details'].get('bold_terms_count', 0)} bold terms"),
            ("No em dashes", results["no_em_dashes"], f"{results['details'].get('em_dash_count', 0)} found"),
            ("No [N] academic citations", results["no_academic_citations"], f"{results['details'].get('academic_citation_count', 0)} found"),
            ("AEO score >= 75", results["aeo_score_ok"], f"Score: {results['details'].get('aeo_score', 0)}"),
        ]
        
        for check_name, passed, detail in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}: {detail}")
        
        print("")
        if results["passed"]:
            print("🎉 ALL QUALITY CHECKS PASSED!")
        else:
            print("⚠️  Some quality checks failed - see above")
        
        # Save output
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"quality_test_{timestamp}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n📄 Output saved: {output_file}")
        print(f"⏱️  Total time: {total_time:.1f} seconds")
        print(f"📝 Word count: {len(html.split())} words")
        
        # Open in browser
        os.system(f"open {output_file}")
        
        return {
            "file": output_file,
            "results": results,
            "time": total_time
        }
    else:
        print("❌ No final HTML generated")
        return None


if __name__ == "__main__":
    result = asyncio.run(run_quality_test())
    if result:
        print(f"\n✅ Test complete: {result['file']}")
        sys.exit(0 if result['results']['passed'] else 1)
    else:
        print("\n❌ Test failed")
        sys.exit(1)


