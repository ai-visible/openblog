"""
Test script for Rewrite Engine

Tests surgical edits with mock article data.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.rewrites.rewrite_engine import RewriteEngine
from pipeline.rewrites.rewrite_instructions import RewriteInstruction, RewriteMode


# Mock article data (simplified)
MOCK_ARTICLE = {
    "Headline": "AI Code Generation Tools 2025: Speed vs Security",
    "Intro": "<p>AI tools are changing software development. Many teams now use them daily. But security concerns remain.</p>",
    "section_01_content": "<p>AI code generation tools 2025 are transforming development. When evaluating AI code generation tools 2025, security is paramount. The best AI code generation tools 2025 serve distinct use cases [1][2]. Teams must carefully assess AI code generation tools 2025 before adoption.</p>",
    "section_02_content": "<p>The market for AI code generation tools 2025 is projected to reach $7.37 billion this year [3]. Organizations using AI code generation tools 2025 report 30% faster development cycles. However, 45% of code from AI code generation tools 2025 contains vulnerabilities [4].</p>",
    "section_03_content": "<p>Security is the primary concern with AI code generation tools 2025. Here's how enterprises are mitigating risks. Key benefits include: automated scanning, faster review, better compliance. Important considerations: data privacy, IP protection, audit trails.</p>",
    "primary_keyword": "AI code generation tools 2025"
}


async def test_keyword_reduction():
    """
    Test Case 1: Reduce keyword from 9 mentions to 5-8
    """
    print("=" * 80)
    print("TEST 1: Keyword Reduction (9 mentions → 5-8)")
    print("=" * 80)
    
    engine = RewriteEngine()
    
    instruction = RewriteInstruction(
        target="all_sections",
        instruction="Reduce 'AI code generation tools 2025' from 9 to 5-8 mentions",
        mode=RewriteMode.QUALITY_FIX,
        preserve_structure=True,
        min_similarity=0.75,
        max_similarity=0.95,
        context={
            "keyword": "AI code generation tools 2025",
            "current_count": 9,
            "target_min": 5,
            "target_max": 8,
            "variations": ["these tools", "AI assistants", "code generators"]
        }
    )
    
    result = await engine.rewrite(MOCK_ARTICLE, instruction)
    
    print(f"\nStatus: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
    print(f"Attempts: {result.attempts_used}")
    print(f"Similarity: {result.similarity_score:.2%}")
    print(f"Validation: {'✅ PASSED' if result.validation_passed else '❌ FAILED'}")
    
    if result.success:
        # Count keyword in result
        keyword_count = result.updated_content.count("AI code generation tools 2025")
        print(f"Keyword mentions after: {keyword_count} (target: 5-8)")
        
        print("\n--- UPDATED CONTENT (first 300 chars) ---")
        print(result.updated_content[:300] + "...")
    else:
        print(f"Error: {result.error_message}")
    
    return result


async def test_paragraph_expansion():
    """
    Test Case 2: Expand short paragraph (24 words → 60-100)
    """
    print("\n\n" + "=" * 80)
    print("TEST 2: Paragraph Expansion (24 words → 60-100)")
    print("=" * 80)
    
    engine = RewriteEngine()
    
    instruction = RewriteInstruction(
        target="Intro",
        instruction="Expand first paragraph to 60-100 words with context and examples",
        mode=RewriteMode.QUALITY_FIX,
        preserve_structure=True,
        min_similarity=0.50,
        max_similarity=0.85,
        context={
            "current_words": 12,  # "AI tools are changing..." = 12 words
            "target_min": 60,
            "target_max": 100,
            "paragraph_index": 1
        }
    )
    
    result = await engine.rewrite(MOCK_ARTICLE, instruction)
    
    print(f"\nStatus: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
    print(f"Attempts: {result.attempts_used}")
    print(f"Similarity: {result.similarity_score:.2%}")
    print(f"Validation: {'✅ PASSED' if result.validation_passed else '❌ FAILED'}")
    
    if result.success:
        # Count words in result
        word_count = len(result.updated_content.split())
        print(f"Word count after: {word_count} (target: 60-100)")
        
        print("\n--- UPDATED CONTENT ---")
        print(result.updated_content)
    else:
        print(f"Error: {result.error_message}")
    
    return result


async def test_ai_marker_removal():
    """
    Test Case 3: Remove AI markers (em dashes, robotic phrases)
    """
    print("\n\n" + "=" * 80)
    print("TEST 3: AI Marker Removal")
    print("=" * 80)
    
    engine = RewriteEngine()
    
    instruction = RewriteInstruction(
        target="section_03_content",
        instruction="Remove robotic phrases like 'Here's how', 'Key benefits include:', 'Important considerations:'",
        mode=RewriteMode.QUALITY_FIX,
        preserve_structure=True,
        min_similarity=0.80,
        max_similarity=0.95,
        context={
            "markers_found": [
                "Here's how",
                "Key benefits include:",
                "Important considerations:"
            ]
        }
    )
    
    result = await engine.rewrite(MOCK_ARTICLE, instruction)
    
    print(f"\nStatus: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
    print(f"Attempts: {result.attempts_used}")
    print(f"Similarity: {result.similarity_score:.2%}")
    print(f"Validation: {'✅ PASSED' if result.validation_passed else '❌ FAILED'}")
    
    if result.success:
        # Check for markers in result
        has_markers = any(marker in result.updated_content for marker in [
            "Here's how", "Key benefits include:", "Important considerations:"
        ])
        print(f"AI markers present: {'❌ YES' if has_markers else '✅ NO'}")
        
        print("\n--- UPDATED CONTENT ---")
        print(result.updated_content)
    else:
        print(f"Error: {result.error_message}")
    
    return result


async def test_refresh_content():
    """
    Test Case 4: Refresh content with new information
    """
    print("\n\n" + "=" * 80)
    print("TEST 4: Content Refresh (Update statistics)")
    print("=" * 80)
    
    engine = RewriteEngine()
    
    instruction = RewriteInstruction(
        target="section_02_content",
        instruction="Update market projection to $8.5 billion (from $7.37B) and add Q4 2025 data",
        mode=RewriteMode.REFRESH,
        preserve_structure=True,
        min_similarity=0.60,  # More changes allowed for refresh
        max_similarity=0.85
    )
    
    result = await engine.rewrite(MOCK_ARTICLE, instruction)
    
    print(f"\nStatus: {'✅ SUCCESS' if result.success else '❌ FAILED'}")
    print(f"Attempts: {result.attempts_used}")
    print(f"Similarity: {result.similarity_score:.2%}")
    print(f"Validation: {'✅ PASSED' if result.validation_passed else '❌ FAILED'}")
    
    if result.success:
        # Check if new number is present
        has_new_value = "$8.5 billion" in result.updated_content
        print(f"New value present: {'✅ YES' if has_new_value else '❌ NO'}")
        
        print("\n--- UPDATED CONTENT ---")
        print(result.updated_content)
    else:
        print(f"Error: {result.error_message}")
    
    return result


async def main():
    """
    Run all tests.
    """
    print("\n🧪 REWRITE ENGINE TEST SUITE\n")
    
    results = []
    
    try:
        # Test 1: Keyword reduction
        result1 = await test_keyword_reduction()
        results.append(("Keyword Reduction", result1.success))
    except Exception as e:
        print(f"\n❌ Test 1 crashed: {e}")
        results.append(("Keyword Reduction", False))
    
    try:
        # Test 2: Paragraph expansion
        result2 = await test_paragraph_expansion()
        results.append(("Paragraph Expansion", result2.success))
    except Exception as e:
        print(f"\n❌ Test 2 crashed: {e}")
        results.append(("Paragraph Expansion", False))
    
    try:
        # Test 3: AI marker removal
        result3 = await test_ai_marker_removal()
        results.append(("AI Marker Removal", result3.success))
    except Exception as e:
        print(f"\n❌ Test 3 crashed: {e}")
        results.append(("AI Marker Removal", False))
    
    try:
        # Test 4: Content refresh
        result4 = await test_refresh_content()
        results.append(("Content Refresh", result4.success))
    except Exception as e:
        print(f"\n❌ Test 4 crashed: {e}")
        results.append(("Content Refresh", False))
    
    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), ".env.local")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✅ Loaded {env_path}")
    
    # Run tests
    asyncio.run(main())

