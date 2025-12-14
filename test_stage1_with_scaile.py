"""
Test Stage 1 with real production-style data from scaile.tech
Based on web research and opencontext-compatible format.
"""

import asyncio
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env.local')
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
from pipeline.core.execution_context import ExecutionContext
from pipeline.core.company_context import CompanyContext

# Real production-style data for scaile.tech (opencontext-compatible format)
SCAILE_DATA = {
    "company_name": "SCAILE",
    "company_url": "https://scaile.tech",
    "industry": "AI-powered go-to-market (GTM) solutions",
    "description": "SCAILE is a software company based in Hamburg, Germany, specializing in building AI-powered GTM machines focused on hyper-niche domination on autopilot.",
    "products": [
        "AI Visibility Engine",
        "AI GTM machines",
        "AI-powered go-to-market automation"
    ],
    "target_audience": "Companies seeking to enhance their visibility in AI-driven search results and improve their go-to-market strategies",
    "competitors": [],  # Would be detected by opencontext
    "tone": "Professional, innovative, data-driven, and customer-focused",
    "pain_points": [
        "Low visibility in AI Overviews and ChatGPT",
        "Manual go-to-market processes",
        "Difficulty achieving hyper-niche market dominance"
    ],
    "value_propositions": [
        "Productized engine for AI visibility",
        "Fast, automated, KPI-first approaches",
        "Hyper-niche market domination on autopilot"
    ],
    "use_cases": [
        "Appearing in AI Overviews for relevant searches",
        "ChatGPT search optimization",
        "Automated GTM strategy execution"
    ],
    "content_themes": [
        "AI integration",
        "Automation",
        "Measurable results",
        "AI Visibility Engine",
        "AI Overviews optimization",
        "ChatGPT search optimization"
    ]
}

# Additional fields that opencontext doesn't detect (but openblog uses)
EXTRA_FIELDS = {
    "system_instructions": "Focus on AI-powered solutions, automation, and measurable KPI-driven results. Emphasize productized approaches over manual processes.",
    "client_knowledge_base": [
        "Based in Hamburg, Germany",
        "Founded to enable AI visibility in search results",
        "Specializes in hyper-niche market domination",
        "Productized GTM engine approach"
    ],
    "content_instructions": "Use professional tone with emphasis on innovation and automation. Include specific metrics and KPIs. Focus on AI-driven search optimization."
}

# Country and language (not currently detected by opencontext, but should be)
DETECTED_METADATA = {
    "country": "Germany",  # Primary country
    "language": "en",  # Primary language
    "location": "Hamburg, Germany"
}

async def test_stage1_with_scaile():
    """Test Stage 1 with real scaile.tech data."""
    print("=" * 80)
    print("STAGE 1 TEST - scaile.tech (Production-Style Data)")
    print("=" * 80)
    
    # Combine opencontext data with extra fields
    full_company_data = {**SCAILE_DATA, **EXTRA_FIELDS}
    
    print("\n📊 Company Data (opencontext-compatible):")
    print(f"  - Company: {full_company_data['company_name']}")
    print(f"  - URL: {full_company_data['company_url']}")
    print(f"  - Industry: {full_company_data['industry']}")
    print(f"  - Products: {len(full_company_data['products'])} items")
    print(f"  - Competitors: {len(full_company_data['competitors'])} items")
    print(f"  - Tone: {full_company_data['tone']}")
    
    print("\n🌍 Detected Metadata (NOT in opencontext currently):")
    print(f"  - Country: {DETECTED_METADATA['country']}")
    print(f"  - Language: {DETECTED_METADATA['language']}")
    print(f"  - Location: {DETECTED_METADATA['location']}")
    
    print("\n💡 Note: opencontext currently detects 12 fields but NOT:")
    print("  - Country (primary country)")
    print("  - Language (primary language)")
    print("  - Location (city/country)")
    
    # Create CompanyContext
    print("\n" + "=" * 80)
    print("Step 1: Creating CompanyContext")
    print("=" * 80)
    
    company_context = CompanyContext.from_dict(full_company_data)
    
    print("\n✅ CompanyContext Created:")
    print(f"  - company_url: {company_context.company_url}")
    print(f"  - company_name: {company_context.company_name}")
    print(f"  - industry: {company_context.industry}")
    print(f"  - tone: {company_context.tone}")
    print(f"  - competitors: {company_context.competitors} (type: {type(company_context.competitors).__name__})")
    print(f"  - products: {company_context.products}")
    
    # Show to_prompt_context output
    prompt_context = company_context.to_prompt_context()
    print(f"\n📋 Prompt Context: {len(prompt_context)} fields (all mandatory)")
    print(f"  - competitors is list: {isinstance(prompt_context['competitors'], list)}")
    
    # Run Stage 1
    print("\n" + "=" * 80)
    print("Step 2: Running Stage 1")
    print("=" * 80)
    
    stage = PromptBuildStage()
    
    context = ExecutionContext(
        job_id="test-scaile-stage1",
        job_config={
            "primary_keyword": "AI visibility engine",
            "language": DETECTED_METADATA["language"],  # Use detected language
        },
        company_data=full_company_data
    )
    
    result_context = await stage.execute(context)
    
    print("\n✅ Stage 1 Complete!")
    print(f"\n📝 Generated Prompt ({len(result_context.prompt)} characters):")
    print("-" * 80)
    print(result_context.prompt)
    print("-" * 80)
    
    # Show what opencontext should detect
    print("\n" + "=" * 80)
    print("SUMMARY: What opencontext Should Detect")
    print("=" * 80)
    print("\n✅ Currently Detects (12 fields):")
    print("  1. company_name")
    print("  2. company_url")
    print("  3. industry")
    print("  4. description")
    print("  5. products (array)")
    print("  6. target_audience")
    print("  7. competitors (array)")
    print("  8. tone")
    print("  9. pain_points (array)")
    print("  10. value_propositions (array)")
    print("  11. use_cases (array)")
    print("  12. content_themes (array)")
    
    print("\n❌ Should Also Detect (but currently doesn't):")
    print("  - country (primary country) - e.g., 'Germany'")
    print("  - language (primary language) - e.g., 'en'")
    print("  - location (city/country) - e.g., 'Hamburg, Germany'")
    
    print("\n💡 To add country/language detection to opencontext:")
    print("  - Analyze website content language (HTML lang attribute, content analysis)")
    print("  - Detect country from domain (.de, .com, etc.) or content context")
    print("  - Use Gemini to extract geographic/language context from website")
    
    return result_context

if __name__ == "__main__":
    result = asyncio.run(test_stage1_with_scaile())
    if result:
        print("\n✅ Test complete!")
    else:
        print("\n❌ Test failed!")

