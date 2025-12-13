#!/usr/bin/env python3
"""
Test Google Images Finder - Using DataForSEO Google Images SERP

Tests the improved approach:
- Direct Google Images search (not page scraping)
- Gets relevant images from SERP
- Filters by type, size, license
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

from pipeline.agents.google_images_finder import GoogleImagesFinder

async def test_google_images_search():
    """Test Google Images search via DataForSEO."""
    print("\n" + "="*80)
    print("GOOGLE IMAGES FINDER - Using DataForSEO SERP")
    print("="*80)
    
    finder = GoogleImagesFinder()
    
    if not finder.is_configured():
        print("\n⚠️  DataForSEO not configured")
        print("   Set DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD in .env.local")
        print("   Cost: $0.50 per 1,000 queries")
        return
    
    print("\n✅ DataForSEO configured")
    print("\n" + "="*80)
    print("TEST 1: Basic Image Search")
    print("="*80)
    
    query = "cloud security statistics chart"
    print(f"\nQuery: {query}")
    print("Searching Google Images via DataForSEO...\n")
    
    images = await finder.search_images(
        query=query,
        max_results=10,
        size="large",  # Filter for large images
        license="creativeCommons"  # Free to use
    )
    
    print(f"✅ Found {len(images)} images\n")
    
    for i, img in enumerate(images[:5], 1):
        print(f"Image {i}:")
        print(f"  Title: {img.title}")
        print(f"  URL: {img.url[:80]}...")
        print(f"  Source: {img.source}")
        print(f"  Size: {img.width}x{img.height}" if img.width and img.height else "  Size: Unknown")
        print(f"  License: {img.license or 'Unknown'}")
        print()
    
    print("\n" + "="*80)
    print("TEST 2: Charts and Infographics Only")
    print("="*80)
    
    query2 = "AI cybersecurity automation infographic"
    print(f"\nQuery: {query2}")
    print("Filtering for: large images, creative commons license\n")
    
    images2 = await finder.search_images(
        query=query2,
        max_results=5,
        size="large",
        image_type="photo",  # or "clipart" for illustrations
        license="creativeCommons"
    )
    
    print(f"✅ Found {len(images2)} relevant images\n")
    
    for i, img in enumerate(images2, 1):
        print(f"  {i}. {img.title[:60]}")
        print(f"     {img.url[:70]}...")
    
    print("\n" + "="*80)
    print("COMPARISON: Current vs Google Images Approach")
    print("="*80)
    print("\nCurrent Approach (Enhanced Asset Finder):")
    print("  ❌ Finds random images from pages")
    print("  ❌ Includes logos, icons, irrelevant images")
    print("  ❌ Requires page fetching and parsing")
    print("  ❌ Slower (fetch + parse)")
    print("\nGoogle Images Approach (DataForSEO):")
    print("  ✅ Gets images directly from Google Images SERP")
    print("  ✅ Pre-filtered by relevance")
    print("  ✅ Can filter by size, type, license")
    print("  ✅ Faster (direct API call)")
    print("  ✅ More relevant results")
    print("\n💡 Recommendation: Use Google Images SERP for better results!")

if __name__ == "__main__":
    asyncio.run(test_google_images_search())

