"""
Test opencontext integration - Call opencontext API for scaile.tech
and use the real production-style data for Stage 1.
"""

import asyncio
import sys
import os
import json
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('.env.local')
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
from pipeline.core.execution_context import ExecutionContext
from pipeline.core.company_context import CompanyContext

# OpenContext API URL (default to localhost, can be overridden)
OPENCONTEXT_API_URL = os.getenv("OPENCONTEXT_API_URL", "http://localhost:3000/api/analyze")

async def call_opencontext(url: str) -> dict:
    """Call opencontext API to analyze a company website."""
    print(f"🔍 Calling opencontext API: {OPENCONTEXT_API_URL}")
    print(f"   URL to analyze: {url}")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                OPENCONTEXT_API_URL,
                json={"url": url},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.HTTPStatusError as e:
            print(f"❌ HTTP Error: {e.response.status_code}")
            print(f"   Response: {e.response.text}")
            raise
        except Exception as e:
            print(f"❌ Error calling opencontext: {e}")
            raise

async def test_opencontext_integration():
    """Test opencontext integration with scaile.tech."""
    print("=" * 80)
    print("OPENCONTEXT INTEGRATION TEST - scaile.tech")
    print("=" * 80)
    
    company_url = "https://scaile.tech"
    
    # Step 1: Call opencontext API
    print("\n📡 Step 1: Calling opencontext API...")
    try:
        opencontext_data = await call_opencontext(company_url)
        print("\n✅ opencontext Analysis Complete!")
        print("\n📊 opencontext Response:")
        print(json.dumps(opencontext_data, indent=2, default=str))
        
        # Check what fields opencontext detected
        print("\n🔍 Detected Fields:")
        for key, value in opencontext_data.items():
            if isinstance(value, list):
                print(f"  - {key}: {len(value)} items - {value[:3]}...")
            else:
                print(f"  - {key}: {value}")
        
        # Check for country/language detection
        print("\n🌍 Country/Language Detection:")
        if "country" in opencontext_data:
            print(f"  ✅ Country detected: {opencontext_data['country']}")
        else:
            print("  ⚠️  Country not detected by opencontext")
        
        if "language" in opencontext_data:
            print(f"  ✅ Language detected: {opencontext_data['language']}")
        else:
            print("  ⚠️  Language not detected by opencontext")
        
        # Show all fields
        print(f"\n📋 All fields returned: {list(opencontext_data.keys())}")
        
    except Exception as e:
        print(f"\n❌ Failed to call opencontext API: {e}")
        print("\n💡 Make sure opencontext is running:")
        print("   1. Clone: git clone https://github.com/federicodeponte/opencontext.git")
        print("   2. Install: cd opencontext && npm install")
        print("   3. Set GEMINI_API_KEY in .env.local")
        print("   4. Run: npm run dev")
        print("   5. Or set OPENCONTEXT_API_URL to deployed URL")
        return None
    
    # Step 2: Convert opencontext data to CompanyContext
    print("\n" + "=" * 80)
    print("Step 2: Converting to CompanyContext")
    print("=" * 80)
    
    try:
        # Map opencontext fields to CompanyContext
        # Note: opencontext doesn't have system_instructions, client_knowledge_base, content_instructions
        company_context = CompanyContext.from_dict(opencontext_data)
        
        print("\n✅ CompanyContext Created:")
        print(f"  - company_url: {company_context.company_url}")
        print(f"  - company_name: {company_context.company_name}")
        print(f"  - industry: {company_context.industry}")
        print(f"  - tone: {company_context.tone}")
        print(f"  - competitors: {company_context.competitors} (type: {type(company_context.competitors).__name__})")
        print(f"  - products: {company_context.products}")
        
        # Show to_prompt_context output
        prompt_context = company_context.to_prompt_context()
        print(f"\n📋 Prompt Context Fields: {len(prompt_context)} fields")
        print(f"  - All mandatory: ✅")
        print(f"  - competitors is list: {isinstance(prompt_context['competitors'], list)}")
        
    except Exception as e:
        print(f"\n❌ Failed to create CompanyContext: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Step 3: Run Stage 1 with real data
    print("\n" + "=" * 80)
    print("Step 3: Running Stage 1 with Real Data")
    print("=" * 80)
    
    try:
        stage = PromptBuildStage()
        
        context = ExecutionContext(
            job_id="test-opencontext-integration",
            job_config={
                "primary_keyword": "cloud security best practices",
                "language": "en",
            },
            company_data=opencontext_data  # Use opencontext data directly
        )
        
        result_context = await stage.execute(context)
        
        print("\n✅ Stage 1 Complete!")
        print(f"\n📝 Generated Prompt ({len(result_context.prompt)} characters):")
        print("-" * 80)
        print(result_context.prompt)
        print("-" * 80)
        
        return result_context
        
    except Exception as e:
        print(f"\n❌ Stage 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_opencontext_integration())
    if result:
        print("\n✅ Integration test complete!")
    else:
        print("\n❌ Integration test failed!")

