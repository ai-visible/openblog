#!/usr/bin/env python3
"""
Test Refresh with Find and Replace Operations

Tests if refresh can handle simple find-and-replace style instructions.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
    if "GOOGLE_GEMINI_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_GEMINI_API_KEY"]
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from service.content_refresher import ContentParser, ContentRefresher
from pipeline.models.gemini_client import GeminiClient


async def test_simple_find_replace():
    """Test 1: Simple find and replace"""
    print("="*60)
    print("TEST 1: Simple Find and Replace")
    print("="*60)
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return False
    
    gemini_client = GeminiClient(api_key=api_key)
    refresher = ContentRefresher(gemini_client)
    
    test_content = {
        "headline": "Test Article",
        "sections": [
            {
                "heading": "Introduction",
                "content": "<p>In 2023, the company had 100 employees. The revenue was $1M in 2023.</p>"
            }
        ]
    }
    
    instructions = [
        "Replace all occurrences of '2023' with '2025'",
        "Replace '100 employees' with '200 employees'",
        "Replace '$1M' with '$2M'"
    ]
    
    print(f"\n📝 Original Content:")
    print(f"   {test_content['sections'][0]['content']}")
    
    print(f"\n🔧 Instructions (Find and Replace):")
    for inst in instructions:
        print(f"   - {inst}")
    
    try:
        refreshed = await refresher.refresh_content(
            content=test_content,
            instructions=instructions,
            target_sections=[0]
        )
        
        refreshed_content = refreshed['sections'][0]['content']
        
        print(f"\n📊 Result:")
        print(f"   {refreshed_content}")
        
        # Check if replacements worked
        checks = {
            "2023 → 2025": "2025" in refreshed_content and "2023" not in refreshed_content,
            "100 → 200": "200 employees" in refreshed_content,
            "$1M → $2M": "$2M" in refreshed_content or "2M" in refreshed_content
        }
        
        print(f"\n✅ Find & Replace Results:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        
        return all(checks.values())
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_complex_find_replace():
    """Test 2: Complex find and replace with context"""
    print("\n" + "="*60)
    print("TEST 2: Complex Find and Replace")
    print("="*60)
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return False
    
    gemini_client = GeminiClient(api_key=api_key)
    refresher = ContentRefresher(gemini_client)
    
    test_content = {
        "headline": "Product Guide",
        "sections": [
            {
                "heading": "Features",
                "content": "<p>Our product supports Windows 10 and macOS 12. Minimum requirements: Windows 10 or macOS 12.</p>"
            }
        ]
    }
    
    instructions = [
        "Replace 'Windows 10' with 'Windows 11'",
        "Replace 'macOS 12' with 'macOS 14'"
    ]
    
    print(f"\n📝 Original Content:")
    print(f"   {test_content['sections'][0]['content']}")
    
    print(f"\n🔧 Instructions:")
    for inst in instructions:
        print(f"   - {inst}")
    
    try:
        refreshed = await refresher.refresh_content(
            content=test_content,
            instructions=instructions,
            target_sections=[0]
        )
        
        refreshed_content = refreshed['sections'][0]['content']
        
        print(f"\n📊 Result:")
        print(f"   {refreshed_content}")
        
        # Check if replacements worked
        checks = {
            "Windows 10 → Windows 11": "Windows 11" in refreshed_content and "Windows 10" not in refreshed_content,
            "macOS 12 → macOS 14": "macOS 14" in refreshed_content and "macOS 12" not in refreshed_content
        }
        
        print(f"\n✅ Find & Replace Results:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        
        return all(checks.values())
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_find_replace_with_html():
    """Test 3: Find and replace in HTML content"""
    print("\n" + "="*60)
    print("TEST 3: Find and Replace in HTML")
    print("="*60)
    
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return False
    
    gemini_client = GeminiClient(api_key=api_key)
    refresher = ContentRefresher(gemini_client)
    
    test_content = {
        "headline": "Company Info",
        "sections": [
            {
                "heading": "About Us",
                "content": "<p>Founded in <strong>2020</strong>, we have been serving customers since <strong>2020</strong>.</p><ul><li>Established in <strong>2020</strong></li><li>First product launched in <strong>2020</strong></li></ul>"
            }
        ]
    }
    
    instructions = [
        "Replace all occurrences of '2020' with '2018'"
    ]
    
    print(f"\n📝 Original Content:")
    print(f"   {test_content['sections'][0]['content']}")
    
    print(f"\n🔧 Instructions:")
    print(f"   - Replace all occurrences of '2020' with '2018'")
    
    try:
        refreshed = await refresher.refresh_content(
            content=test_content,
            instructions=instructions,
            target_sections=[0]
        )
        
        refreshed_content = refreshed['sections'][0]['content']
        
        print(f"\n📊 Result:")
        print(f"   {refreshed_content}")
        
        # Check if replacements worked
        checks = {
            "All 2020 → 2018": "2018" in refreshed_content and "2020" not in refreshed_content,
            "HTML preserved": "<strong>" in refreshed_content and "</strong>" in refreshed_content,
            "Structure intact": "<ul>" in refreshed_content and "<li>" in refreshed_content
        }
        
        print(f"\n✅ Find & Replace Results:")
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"   {status} {check}")
        
        return all(checks.values())
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all find-and-replace tests"""
    print("\n" + "="*60)
    print("REFRESH FIND & REPLACE TESTS")
    print("="*60)
    print("\nTesting if refresh can handle find-and-replace operations...")
    
    results = []
    
    try:
        result1 = await test_simple_find_replace()
        results.append(("Simple Find & Replace", result1))
        
        result2 = await test_complex_find_replace()
        results.append(("Complex Find & Replace", result2))
        
        result3 = await test_find_replace_with_html()
        results.append(("Find & Replace in HTML", result3))
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{status}: {test_name}")
        
        print(f"\n📊 Results: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")
        
        if passed == total:
            print("\n✅ Refresh works with find-and-replace operations!")
        else:
            print(f"\n⚠️  Some find-and-replace operations may need refinement")
        
        return passed == total
        
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

