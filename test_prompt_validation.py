#!/usr/bin/env python3
"""
Quick Prompt Validation Test

Validates that prompt fixes are correctly applied:
- Keyword density rule (EXACTLY 8-12)
- Grammar rules (proper nouns, capitalization, common errors)
- No repetition (DRY)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.prompts.main_article import get_main_article_prompt

def validate_prompt_fixes():
    """Validate all prompt fixes are correctly applied."""
    print("=" * 70)
    print("PROMPT FIXES VALIDATION TEST")
    print("=" * 70)
    print()
    
    prompt = get_main_article_prompt(
        primary_keyword="AI customer service automation",
        company_name="TestCorp",
        company_info={"description": "Test company"},
        language="en",
        country="US"
    )
    
    print(f"📊 Prompt Length: {len(prompt):,} chars")
    print()
    
    # Validation checks
    checks = {
        'Keyword Density - EXACTLY 8-12': 'EXACTLY 8-12' in prompt and 'Count total mentions' in prompt,
        'Keyword Density - Consequences': 'keyword stuffing' in prompt.lower() and 'insufficient optimization' in prompt.lower(),
        'Grammar - Proper Nouns': 'Capitalize proper nouns' in prompt and 'Gartner' in prompt and 'Nielsen' in prompt and 'API' in prompt,
        'Grammar - Sentence Starts': 'sentence starts' in prompt.lower(),
        'Grammar - Common Errors': 'speed upd' in prompt.lower() and 'applys' in prompt.lower() and 'aPI' in prompt.lower(),
        'DRY - No Repetition': prompt.count('NEVER') <= 4,
        'DRY - Consolidated Rules': 'HTML:' in prompt or 'Keep all HTML tags' in prompt,
    }
    
    print("✅ Fix Validation:")
    print("-" * 70)
    all_passed = True
    for check_name, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    print()
    print("=" * 70)
    if all_passed:
        print("🎉 ALL PROMPT FIXES VALIDATED!")
        print("   ✅ Keyword density: Strict enforcement")
        print("   ✅ Grammar: Proper nouns, capitalization, common errors")
        print("   ✅ DRY SOLID KISS: No repetition, consolidated rules")
    else:
        print("⚠️  Some fixes missing - review above")
    
    print()
    
    # Show key sections
    print("📄 Key Sections Preview:")
    print("-" * 70)
    
    # Keyword rule
    keyword_match = re.search(r'Primary Keyword.*?EXACTLY 8-12.*?(?=\n\n|\d+\.)', prompt, re.DOTALL)
    if keyword_match:
        print("Keyword Rule:")
        print(keyword_match.group(0)[:200] + "...")
        print()
    
    # Grammar rule
    grammar_match = re.search(r'Grammar.*?Write professionally', prompt, re.DOTALL)
    if grammar_match:
        print("Grammar Rule:")
        print(grammar_match.group(0)[:200] + "...")
        print()
    
    return all_passed

if __name__ == "__main__":
    import re
    success = validate_prompt_fixes()
    sys.exit(0 if success else 1)

