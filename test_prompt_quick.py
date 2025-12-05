#!/usr/bin/env python3
"""
Quick Prompt Test - Verify Simplified Prompt Quality

Tests prompt generation and structure without full article generation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.prompts.main_article import get_main_article_prompt

def test_prompt():
    """Test prompt generation for Spherecast."""
    print("=" * 70)
    print("QUICK PROMPT TEST - Spherecast")
    print("=" * 70)
    print()
    
    # Spherecast configuration
    prompt = get_main_article_prompt(
        primary_keyword="AI podcast platform for content creators",
        company_name="Spherecast",
        company_info={
            "description": "AI-powered podcast platform",
            "industry": "Technology"
        },
        language="en",
        country="US"
    )
    
    print(f"✅ Prompt generated: {len(prompt):,} characters")
    print()
    
    # Verify simplifications
    checks = []
    
    # Check 1: No specific typo list
    if 'speed upd' not in prompt and 'applys' not in prompt:
        checks.append(("✅ No specific typo list", True))
    else:
        checks.append(("❌ Still has typo list", False))
    
    # Check 2: Simple grammar instruction
    if 'Proofread all content for grammar' in prompt:
        checks.append(("✅ Simple grammar instruction", True))
    else:
        checks.append(("❌ Missing grammar instruction", False))
    
    # Check 3: Citation embedding rule
    if 'embedded within sentences' in prompt or 'embedded in sentences' in prompt:
        checks.append(("✅ Citation embedding rule present", True))
    else:
        checks.append(("❌ Missing citation rule", False))
    
    # Check 4: Length constraints
    if '60' in prompt and 'headline' in prompt.lower():
        checks.append(("✅ Headline length constraint", True))
    else:
        checks.append(("❌ Missing headline constraint", False))
    
    if '300' in prompt and 'intro' in prompt.lower():
        checks.append(("✅ Intro length constraint", True))
    else:
        checks.append(("❌ Missing intro constraint", False))
    
    # Check 5: No repetitive reminders
    if prompt.lower().count('count each character') == 0:
        checks.append(("✅ No repetitive reminders", True))
    else:
        checks.append(("❌ Has repetitive reminders", False))
    
    # Check 6: Essential fixes maintained
    essential = {
        'Citation embedding': 'embedded' in prompt.lower() and 'citation' in prompt.lower(),
        'Headline length': '60' in prompt and 'headline' in prompt.lower(),
        'Intro length': '300' in prompt and 'intro' in prompt.lower(),
        'Content depth': '2-3 paragraphs' in prompt or 'at least 2-3' in prompt,
        'Keyword usage': '8-12' in prompt and 'keyword' in prompt.lower()
    }
    
    print("📋 Verification Results:")
    print("-" * 70)
    for check_name, passed in checks:
        print(f"  {check_name}")
    
    print()
    print("📋 Essential Fixes:")
    print("-" * 70)
    for fix_name, present in essential.items():
        status = "✅" if present else "❌"
        print(f"  {status} {fix_name}")
    
    all_passed = all(passed for _, passed in checks) and all(essential.values())
    
    print()
    print("=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Prompt is properly simplified!")
    else:
        print("⚠️  Some checks failed - review above")
    print()
    
    # Show prompt preview
    print("📄 Prompt Preview (first 500 chars):")
    print("-" * 70)
    print(prompt[:500] + "...")
    print()
    
    return all_passed

if __name__ == "__main__":
    success = test_prompt()
    sys.exit(0 if success else 1)

