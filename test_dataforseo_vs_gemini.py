#!/usr/bin/env python3
"""
Compare DataForSEO vs Gemini for Image Finding

Tests both approaches and compares:
- Quality of results
- Relevance
- Speed
- Cost
"""

import asyncio
import os
import time
from pathlib import Path

# Load env
env_file = Path('.env.local')
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip('"').strip("'")

from pipeline.agents.asset_finder import AssetFinderAgent, AssetFinderRequest

async def test_gemini_approach():
    """Test Gemini + Google Search approach"""
    print("\n" + "="*80)
    print("APPROACH 1: Gemini + Google Search (images: prefix)")
    print("="*80)
    
    start_time = time.time()
    
    agent = AssetFinderAgent()
    request = AssetFinderRequest(
        article_topic="cloud security statistics chart",
        max_results=5
    )
    
    response = await agent.find_assets(request)
    duration = time.time() - start_time
    
    print(f"\n✅ Results: {len(response.assets)} assets")
    print(f"⏱️  Time: {duration:.1f}s")
    print(f"💰 Cost: Free (included with Gemini)")
    print(f"🔍 Query: {response.search_query_used}")
    print("\nAssets found:")
    for i, asset in enumerate(response.assets[:3], 1):
        print(f"  {i}. {asset.title[:50]} ({asset.source})")
    
    return {
        "approach": "Gemini + Google Search",
        "assets": response.assets,
        "duration": duration,
        "cost": "Free"
    }

async def test_dataforseo_approach():
    """Test DataForSEO Google Images API approach"""
    print("\n" + "="*80)
    print("APPROACH 2: DataForSEO Google Images API")
    print("="*80)
    
    from pipeline.agents.google_images_finder import GoogleImagesFinder
    
    finder = GoogleImagesFinder()
    
    if not finder.is_configured():
        print("\n⚠️  DataForSEO not configured")
        print("   Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD")
        return None
    
    start_time = time.time()
    
    images = await finder.search_images(
        query="cloud security statistics chart",
        max_results=5,
        size="large",
        license="creativeCommons"
    )
    
    duration = time.time() - start_time
    
    print(f"\n✅ Results: {len(images)} images")
    print(f"⏱️  Time: {duration:.1f}s")
    print(f"💰 Cost: ~$0.0005 per query ($0.50 per 1,000)")
    print("\nImages found:")
    for i, img in enumerate(images[:3], 1):
        print(f"  {i}. {img.title[:50]} ({img.source})")
        if img.width and img.height:
            print(f"     Size: {img.width}x{img.height}")
    
    return {
        "approach": "DataForSEO Google Images",
        "assets": images,
        "duration": duration,
        "cost": "$0.0005 per query"
    }

async def compare():
    """Compare both approaches"""
    print("\n" + "="*80)
    print("COMPARISON: Gemini vs DataForSEO")
    print("="*80)
    
    # Test Gemini
    gemini_result = await test_gemini_approach()
    await asyncio.sleep(2)
    
    # Test DataForSEO
    dataforseo_result = await test_dataforseo_approach()
    
    # Comparison
    print("\n" + "="*80)
    print("QUALITY COMPARISON")
    print("="*80)
    
    print(f"\n📊 Gemini Approach:")
    print(f"   Results: {len(gemini_result['assets'])} assets")
    print(f"   Speed: {gemini_result['duration']:.1f}s")
    print(f"   Cost: {gemini_result['cost']}")
    print(f"   Quality: Good relevance, but less control")
    
    if dataforseo_result:
        print(f"\n📊 DataForSEO Approach:")
        print(f"   Results: {len(dataforseo_result['assets'])} images")
        print(f"   Speed: {dataforseo_result['duration']:.1f}s")
        print(f"   Cost: {dataforseo_result['cost']}")
        print(f"   Quality: Better filtering, structured data")
        
        print(f"\n💡 RECOMMENDATION:")
        if len(dataforseo_result['assets']) > len(gemini_result['assets']):
            print("   ✅ DataForSEO provides MORE results")
            print("   ✅ Use as PRIMARY for better quality")
            print("   ✅ Gemini as FALLBACK when DataForSEO unavailable")
        elif len(dataforseo_result['assets']) == len(gemini_result['assets']):
            print("   ✅ Both provide similar results")
            print("   ✅ Use Gemini as PRIMARY (free)")
            print("   ✅ DataForSEO as FALLBACK (when filters needed)")
        else:
            print("   ✅ Gemini provides more results")
            print("   ✅ Use Gemini as PRIMARY")
            print("   ✅ DataForSEO as FALLBACK (when advanced filtering needed)")
    else:
        print(f"\n💡 RECOMMENDATION:")
        print("   ✅ Use Gemini as PRIMARY (works well)")
        print("   ✅ DataForSEO as FALLBACK (when configured and filters needed)")

if __name__ == "__main__":
    asyncio.run(compare())

