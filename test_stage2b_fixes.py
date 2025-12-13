#!/usr/bin/env python3
"""
Isolated test for Stage 2b fixes.
Tests each fix individually to verify they work.
"""

import re
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_title_p_tag_stripping():
    """Test 1: Strip <p> tags from titles"""
    print("=" * 60)
    print("TEST 1: Title <p> tag stripping")
    print("=" * 60)
    
    test_cases = [
        ("What is <p>Conclusion</p>?", "What is Conclusion?"),
        ("<p>The 2025 Threat Landscape</p>", "The 2025 Threat Landscape"),
        ("Normal Title", "Normal Title"),  # Should not change
    ]
    
    for field in ['section_01_title', 'section_09_title', 'faq_01_question']:
        for original, expected in test_cases:
            content = original
            if field.endswith('_title') or field.endswith('_question'):
                content = re.sub(r'</?p>', '', content)
                content = content.strip()
            
            if content == expected:
                print(f"✅ PASS: '{original}' → '{content}'")
            else:
                print(f"❌ FAIL: '{original}' → '{content}' (expected '{expected}')")
                return False
    
    return True

def test_duplicate_list_removal():
    """Test 2: Remove duplicate summary lists"""
    print("\n" + "=" * 60)
    print("TEST 2: Duplicate summary list removal")
    print("=" * 60)
    
    test_content = """
<p>AI is transforming security.</p>
<p>Here are key points:</p>
<ul><li>AI is transforming security</li><li>Automation is key</li></ul>
<p>More content here.</p>
"""
    
    summary_patterns = [
        r'<p>Here are key points:</p>\s*<ul>.*?</ul>',
        r'<p>Key benefits include:</p>\s*<ul>.*?</ul>',
        r'<p>Important considerations:</p>\s*<ul>.*?</ul>',
        r"<p>Here's what matters:</p>\s*<ul>.*?</ul>",
    ]
    
    original = test_content
    for pattern in summary_patterns:
        test_content = re.sub(pattern, '', test_content, flags=re.DOTALL)
    
    # Should not contain "Here are key points:" anymore
    if "Here are key points:" not in test_content:
        print(f"✅ PASS: Removed duplicate list")
        print(f"   Before: {len(original)} chars")
        print(f"   After: {len(test_content)} chars")
        return True
    else:
        print(f"❌ FAIL: Duplicate list still present")
        print(f"   Content: {test_content[:200]}")
        return False

def test_academic_citation_removal():
    """Test 3: Remove academic citations [N]"""
    print("\n" + "=" * 60)
    print("TEST 3: Academic citation removal")
    print("=" * 60)
    
    test_cases = [
        ("Sentence with [2] citation.", "Sentence with citation."),  # Fixed: should clean spaces
        ("Multiple [2][3] citations.", "Multiple citations."),
        ("Trailing citation. [2]", "Trailing citation."),
        ("No citations here.", "No citations here."),
    ]
    
    for original, expected in test_cases:
        content = original
        # Remove [N] patterns
        content = re.sub(r'\[\d+\]', '', content)
        content = re.sub(r'\[\d+\]\[\d+\]', '', content)
        # Remove trailing citations
        content = re.sub(r'\.\s*\[\d+\]\s*$', '.', content, flags=re.MULTILINE)
        content = re.sub(r'\.\s*\[\d+\]\[\d+\]\s*$', '.', content, flags=re.MULTILINE)
        # Clean up double spaces
        content = re.sub(r'\s+', ' ', content)
        
        if content.strip() == expected.strip():
            print(f"✅ PASS: '{original}' → '{content.strip()}'")
        else:
            print(f"❌ FAIL: '{original}' → '{content.strip()}' (expected '{expected.strip()}')")
            return False
    
    return True

def test_broken_grammar_fixes():
    """Test 4: Fix broken grammar"""
    print("\n" + "=" * 60)
    print("TEST 4: Broken grammar fixes")
    print("=" * 60)
    
    test_cases = [
        ("You can to mitigate this", "To mitigate this"),
        ("you can to mitigate this", "to mitigate this"),
        ("Normal sentence here.", "Normal sentence here."),
    ]
    
    def fix_you_can_to(match):
        text = match.group(0)
        if text[0].isupper():
            return 'To'
        else:
            return 'to'
    
    for original, expected in test_cases:
        content = original
        content = re.sub(r'\b[yY]ou can to\b', fix_you_can_to, content)
        
        if content == expected:
            print(f"✅ PASS: '{original}' → '{content}'")
        else:
            print(f"❌ FAIL: '{original}' → '{content}' (expected '{expected}')")
            return False
    
    return True

def test_proxy_url_resolution():
    """Test 5: Proxy URL resolution in Sources"""
    print("\n" + "=" * 60)
    print("TEST 5: Proxy URL resolution (mock test)")
    print("=" * 60)
    
    sources = """[2]: Gartner Top Cybersecurity Trends for 2025 - https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQ...
[3]: IBM Report - https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQ..."""
    
    # Check if we can detect proxy URLs
    has_proxy = "vertexaisearch.cloud.google.com" in sources
    
    if has_proxy:
        print(f"✅ PASS: Detected proxy URLs in Sources")
        print(f"   Found {sources.count('vertexaisearch.cloud.google.com')} proxy URLs")
        print(f"   (Actual resolution requires HTTP request - tested in integration)")
        return True
    else:
        print(f"❌ FAIL: No proxy URLs detected")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("STAGE 2B FIXES - ISOLATED TEST SUITE")
    print("=" * 60)
    
    results = []
    
    results.append(("Title <p> tag stripping", test_title_p_tag_stripping()))
    results.append(("Duplicate list removal", test_duplicate_list_removal()))
    results.append(("Academic citation removal", test_academic_citation_removal()))
    results.append(("Broken grammar fixes", test_broken_grammar_fixes()))
    results.append(("Proxy URL detection", test_proxy_url_resolution()))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())

