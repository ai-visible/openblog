#!/usr/bin/env python3
"""
Test HTML Sanitization and Validation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.processors.cleanup import HTMLCleaner

print("=" * 80)
print("🧪 HTML SANITIZATION TEST")
print("=" * 80)

test_cases = [
    {
        "name": "XSS - Script tag injection",
        "input": '<p>Normal text</p><script>alert("XSS")</script><p>More text</p>',
        "expected_contains": "Normal text",
        "expected_not_contains": "<script>",
        "risk": "🔴 CRITICAL"
    },
    {
        "name": "XSS - Event handler",
        "input": '<p onclick="alert(1)">Click me</p>',
        "expected_contains": "Click me",
        "expected_not_contains": "onclick",
        "risk": "🔴 CRITICAL"
    },
    {
        "name": "Unclosed <p> tag",
        "input": "<p>Paragraph one<p>Paragraph two</p>",
        "expected_contains": "Paragraph one",
        "expected_contains2": "Paragraph two",
        "risk": "🟠 HIGH"
    },
    {
        "name": "Invalid nesting",
        "input": "<ul><strong><li>Item</li></strong></ul>",
        "expected_contains": "Item",
        "risk": "🟠 MEDIUM"
    },
    {
        "name": "Markdown bold",
        "input": "<p>This is **important** text</p>",
        "expected_contains": "important",
        "expected_not_contains": "**",
        "risk": "🟡 LOW"
    },
    {
        "name": "Empty href",
        "input": '<a href="">link</a>',
        "expected_contains": "link",
        "expected_not_contains": 'href=""',
        "risk": "🟡 LOW"
    },
    {
        "name": "Valid citation link",
        "input": '<p>Text <a href="https://example.com" target="_blank" rel="noopener noreferrer">[1]</a></p>',
        "expected_contains": "[1]",
        "expected_contains2": "https://example.com",
        "risk": "✅ VALID"
    },
]

print("\n📊 RUNNING TESTS:")
print("-" * 80)

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. {test['risk']} {test['name']}")
    print(f"   Input: {test['input'][:80]}...")
    
    # Clean the HTML
    output = HTMLCleaner.sanitize(test['input'])
    
    print(f"   Output: {output[:80]}...")
    
    # Check expected_contains
    if "expected_contains" in test:
        if test["expected_contains"] in output:
            print(f"   ✅ Contains: '{test['expected_contains']}'")
            passed += 1
        else:
            print(f"   ❌ Missing: '{test['expected_contains']}'")
            failed += 1
    
    if "expected_contains2" in test:
        if test["expected_contains2"] in output:
            print(f"   ✅ Contains: '{test['expected_contains2']}'")
            passed += 1
        else:
            print(f"   ❌ Missing: '{test['expected_contains2']}'")
            failed += 1
    
    # Check expected_not_contains
    if "expected_not_contains" in test:
        if test["expected_not_contains"] not in output:
            print(f"   ✅ Removed: '{test['expected_not_contains']}'")
            passed += 1
        else:
            print(f"   ❌ Still contains: '{test['expected_not_contains']}'")
            failed += 1

print("\n" + "=" * 80)
print("📊 TEST RESULTS")
print("=" * 80)

total = passed + failed
success_rate = (passed / total * 100) if total > 0 else 0

print(f"\n✅ Passed: {passed}/{total}")
print(f"❌ Failed: {failed}/{total}")
print(f"📈 Success rate: {success_rate:.1f}%")

if failed == 0:
    print("\n🎉 ALL TESTS PASSED! HTML sanitization is working correctly.")
    print("✅ PRODUCTION READY")
else:
    print(f"\n⚠️  {failed} test(s) failed - review sanitization logic")
    if failed > 2:
        print("🚨 BLOCKER: Too many failures, DO NOT SHIP")
    else:
        print("⚠️  Review failures, may be acceptable edge cases")

print("\n" + "=" * 80)

