#!/usr/bin/env python3
"""
Compare Asset Finding Approaches

Tests both:
1. Gemini + Google Search with "images:" prefix (current)
2. DataForSEO Google Images API (proposed fallback/enhancement)

Compares quality, relevance, and results.
"""

import asyncio
import os
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

async def test_gemini_images_search():
    """Test Approach 1: Gemini + Google Search with images: prefix"""
    print("\n" + "="*80)
    print("APPROACH 1: Gemini + Google Search (images: prefix)")
    print("="*80)
    
    agent = AssetFinderAgent()
    
    request = AssetFinderRequest(
        article_topic="cloud security statistics",
        max_results=5,
        image_types=["chart", "infographic"]
    )
    
    print(f"\nQuery: {agent._build_search_query(request)}")
    print("Method: Gemini AI + Google Search tool")
    print("Cost: Free (included with Gemini)")
    print()
    
    response = await agent.find_assets(request)
    
    print(f"✅ Found {len(response.assets)} assets\n")
    
    for i, asset in enumerate(response.assets, 1):
        print(f"  {i}. {asset.title[:60]}")
        print(f"     Source: {asset.source}")
        print(f"     URL: {asset.url[:70]}...")
    
    return response.assets

async def test_dataforseo_images():
    """Test Approach 2: DataForSEO Google Images API"""
    print("\n" + "="*80)
    print("APPROACH 2: DataForSEO Google Images API")
    print("="*80)
    
    from pipeline.agents.google_images_finder import GoogleImagesFinder
    
    finder = GoogleImagesFinder()
    
    if not finder.is_configured():
        print("\n⚠️  DataForSEO not configured")
        print("   Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD")
        return []
    
    print("\nMethod: DataForSEO Google Images API")
    print("Cost: $0.50 per 1,000 queries")
    print("Filters: size=large, license=creativeCommons")
    print()
    
    images = await finder.search_images(
        query="cloud security statistics chart infographic",
        max_results=5,
        size="large",
        license="creativeCommons"
    )
    
    print(f"✅ Found {len(images)} images\n")
    
    for i, img in enumerate(images, 1):
        print(f"  {i}. {img.title[:60]}")
        print(f"     Source: {img.source}")
        print(f"     Size: {img.width}x{img.height}" if img.width and img.height else "     Size: Unknown")
        print(f"     License: {img.license or 'Unknown'}")
        print(f"     URL: {img.url[:70]}...")
    
    return images

async def compare_approaches():
    """Compare both approaches side-by-side"""
    print("\n" + "="*80)
    print("COMPARISON: Approach 1 vs Approach 2")
    print("="*80)
    
    print("\n📊 Testing both approaches with same query...")
    print("   Query: 'cloud security statistics chart infographic'\n")
    
    # Test Approach 1
    gemini_assets = await test_gemini_images_search()
    await asyncio.sleep(2)
    
    # Test Approach 2
    dataforseo_images = await test_dataforseo_images()
    
    # Comparison
    print("\n" + "="*80)
    print("QUALITY COMPARISON")
    print("="*80)
    
    print("\n✅ Approach 1: Gemini + Google Search")
    print(f"   Results: {len(gemini_assets)} assets")
    print("   Pros:")
    print("     • Free (included with Gemini)")
    print("     • Fast (direct API call)")
    print("     • Good relevance (Google's algorithm)")
    print("   Cons:")
    print("     • Less control over filters")
    print("     • Depends on Gemini's interpretation")
    print("     • May include some irrelevant results")
    
    print("\n✅ Approach 2: DataForSEO Google Images API")
    print(f"   Results: {len(dataforseo_images)} images")
    print("   Pros:")
    print("     • Direct Google Images SERP access")
    print("     • Advanced filtering (size, license, type)")
    print("     • More control over results")
    print("     • Structured data (dimensions, license)")
    print("   Cons:")
    print("     • Cost: $0.50 per 1,000 queries")
    print("     • Requires API credentials")
    print("     • Slightly slower (polling)")
    
    print("\n💡 RECOMMENDATION:")
    if len(dataforseo_images) > len(gemini_assets):
        print("   DataForSEO provides MORE results with better filtering")
        print("   Use as PRIMARY for better quality")
    elif len(dataforseo_images) == 0:
        print("   DataForSEO not configured or API issue")
        print("   Use Gemini as PRIMARY, DataForSEO as FALLBACK")
    else:
        print("   Both approaches work well")
        print("   Use Gemini as PRIMARY (free), DataForSEO as FALLBACK (when filters needed)")

if __name__ == "__main__":
    asyncio.run(compare_approaches())

