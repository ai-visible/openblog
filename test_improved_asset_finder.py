#!/usr/bin/env python3
"""
Test Improved Asset Finder - Using Google Images Search

Tests the improved approach that uses Google Images search directly
instead of scraping random images from pages.
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

async def test_improved_search():
    """Test improved asset finder with Google Images search."""
    print("\n" + "="*80)
    print("IMPROVED ASSET FINDER - Google Images Search")
    print("="*80)
    print("\nThis version uses 'images:' prefix to search Google Images directly,")
    print("which gives much more relevant results than scraping random page images.\n")
    
    agent = AssetFinderAgent()
    
    request = AssetFinderRequest(
        article_topic="cloud security statistics",
        article_headline="Cloud Security Statistics 2024",
        max_results=5,
        image_types=["chart", "infographic", "photo"]
    )
    
    print("="*80)
    print("STAGE 1: Building Search Query")
    print("="*80)
    query = agent._build_search_query(request)
    print(f"\n✅ Query: {query}")
    print("\n💡 Notice: Uses 'images:' prefix for Google Images search")
    print("   This targets images directly, not random page content\n")
    
    print("="*80)
    print("STAGE 2: Searching Google Images")
    print("="*80)
    print("\n📡 Using Gemini + Google Images Search...")
    print("   This searches Google Images SERP directly")
    print("   Gets pre-filtered, relevant images\n")
    
    response = await agent.find_assets(request)
    
    print("="*80)
    print("RESULTS")
    print("="*80)
    print(f"\n✅ Success: {response.success}")
    print(f"🔍 Search Query Used: {response.search_query_used}")
    print(f"📦 Found {len(response.assets)} assets\n")
    
    for i, asset in enumerate(response.assets, 1):
        print(f"Asset {i}:")
        print(f"  📸 Title: {asset.title}")
        print(f"  🔗 URL: {asset.url[:80]}...")
        print(f"  📦 Source: {asset.source}")
        print(f"  🎨 Type: {asset.image_type}")
        print(f"  📝 Description: {asset.description[:80]}...")
        if asset.license_info:
            print(f"  📄 License: {asset.license_info}")
        print()
    
    print("="*80)
    print("COMPARISON")
    print("="*80)
    print("\n❌ Old Approach (Page Scraping):")
    print("   • Finds random images from pages")
    print("   • Includes logos, icons, navigation elements")
    print("   • Example: Found Spacelift logo, random SVG icons")
    print("\n✅ New Approach (Google Images Search):")
    print("   • Searches Google Images SERP directly")
    print("   • Pre-filtered by relevance")
    print("   • Focuses on free stock photo sites")
    print("   • Much more relevant results!")

if __name__ == "__main__":
    asyncio.run(test_improved_search())

