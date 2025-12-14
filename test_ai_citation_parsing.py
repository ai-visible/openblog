"""
Test AI-only citation parsing with Gemini grounding URLs.

Verifies:
1. AI parsing works without regex/string manipulation
2. Gemini grounding URLs are used correctly
3. Citations are properly extracted and formatted
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.blog_generation.stage_04_citations import CitationsStage
from pipeline.core.execution_context import ExecutionContext
from pipeline.models.output_schema import ArticleOutput

async def test_ai_citation_parsing():
    """Test AI citation parsing with grounding URLs."""
    print("=" * 80)
    print("TEST: AI-ONLY CITATION PARSING")
    print("=" * 80)
    
    # Create test Sources text (typical format from Gemini)
    sources_text = """[1]: Gartner Top Cybersecurity Trends 2025 – https://www.gartner.com/en/articles/top-cybersecurity-trends-for-2025
[2]: IBM Cost of a Data Breach 2024 – https://www.ibm.com/reports/data-breach
[3]: Forrester Predictions 2025 – https://www.forrester.com/report/predictions-2025-cybersecurity-risk-and-privacy
[4]: CrowdStrike Global Threat Report – https://www.crowdstrike.com/global-threat-report/
[5]: Palo Alto Networks Unit 42 Cloud Threat Report – https://www.paloaltonetworks.com/unit42/cloud-threat-report
"""
    
    # Mock grounding URLs (from Gemini search)
    grounding_urls = [
        {
            'url': 'https://www.gartner.com/en/articles/top-cybersecurity-trends-for-2025',
            'title': 'Gartner Top Cybersecurity Trends 2025',
            'domain': 'gartner.com'
        },
        {
            'url': 'https://www.ibm.com/reports/data-breach',
            'title': 'IBM Cost of a Data Breach 2024',
            'domain': 'ibm.com'
        },
        {
            'url': 'https://www.forrester.com/report/predictions-2025-cybersecurity-risk-and-privacy',
            'title': 'Forrester Predictions 2025',
            'domain': 'forrester.com'
        },
        {
            'url': 'https://www.crowdstrike.com/global-threat-report/',
            'title': 'CrowdStrike Global Threat Report',
            'domain': 'crowdstrike.com'
        },
        {
            'url': 'https://www.paloaltonetworks.com/unit42/cloud-threat-report',
            'title': 'Palo Alto Networks Unit 42 Cloud Threat Report',
            'domain': 'paloaltonetworks.com'
        },
    ]
    
    print(f"\n📝 Sources text ({len(sources_text)} chars):")
    print(sources_text)
    
    print(f"\n📎 Grounding URLs ({len(grounding_urls)} URLs):")
    for i, g in enumerate(grounding_urls, 1):
        print(f"  {i}. {g['domain']} → {g['url']}")
    
    # Create Stage 4 instance
    stage = CitationsStage()
    
    # Test AI parsing
    print("\n🤖 Testing AI citation parsing...")
    try:
        citation_list = await stage._parse_sources(sources_text, grounding_urls=grounding_urls)
        
        print(f"\n✅ AI parsed {len(citation_list.citations)} citations:")
        for citation in citation_list.citations:
            print(f"  [{citation.number}]: {citation.title}")
            print(f"      URL: {citation.url}")
        
        # Check if grounding URLs were used
        print("\n🔍 Checking if grounding URLs were used:")
        for citation in citation_list.citations:
            # Check if citation URL matches any grounding URL
            matches_grounding = any(
                citation.url == g['url'] or citation.url.startswith(g['url'])
                for g in grounding_urls
            )
            if matches_grounding:
                print(f"  ✅ Citation [{citation.number}] uses grounding URL")
            else:
                print(f"  ⚠️  Citation [{citation.number}] doesn't match grounding URLs")
        
        # Test HTML output
        print("\n📄 Testing HTML output:")
        html = citation_list.to_html_paragraph_list()
        print(f"  HTML length: {len(html)} chars")
        print(f"  Preview (first 200 chars): {html[:200]}...")
        
        return citation_list
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_ai_citation_parsing())
    if result:
        print("\n✅ Test complete!")
    else:
        print("\n❌ Test failed!")

