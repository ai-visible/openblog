#!/usr/bin/env python3
"""
Verify Stage 8 Output - Critical Simplification Check

Verifies that Stage 8:
1. Has NO content manipulation fields
2. Has citation map
3. Properly merged parallel results
4. HTML content preserved correctly
"""

import json
from pathlib import Path

def verify_stage8():
    output_dir = Path('inspection_output_20251216-023614')
    stage8_file = output_dir / 'stage_08' / 'full_context.json'
    
    if not stage8_file.exists():
        print("⏳ Stage 8 output not found yet")
        return
    
    print('='*80)
    print('STAGE 8 VERIFICATION - CRITICAL SIMPLIFICATION CHECK')
    print('='*80)
    
    stage8 = json.load(open(stage8_file))
    
    if 'validated_article' not in stage8:
        print("❌ CRITICAL: No validated_article found in Stage 8 output")
        return
    
    va = stage8['validated_article']
    
    # CHECK 1: Content Manipulation Fields
    print('\n\n🔍 CHECK 1: Content Manipulation Fields (CRITICAL)')
    print('-'*80)
    
    manip_fields = [
        'humanized', 'normalized', 'sanitized', 'cleaned',
        'conversational_phrases_added', 'aeo_enforced',
        'converted_to_questions', 'split_paragraphs',
        'enhanced_direct_answer', 'fixed_citation_distribution',
        'prepared_and_cleaned', 'normalized_output'
    ]
    
    found_manip = []
    for field in va.keys():
        field_lower = field.lower()
        for manip in manip_fields:
            if manip in field_lower:
                found_manip.append(field)
                break
    
    if found_manip:
        print(f'❌ CRITICAL FAILURE: Found {len(found_manip)} content manipulation fields:')
        for field in found_manip:
            print(f'    - {field}')
    else:
        print(f'✅ PASS: No content manipulation fields found')
        print(f'    Stage 8 correctly only merges and links')
    
    # CHECK 2: Citation Map
    print('\n\n🔍 CHECK 2: Citation Map')
    print('-'*80)
    
    if '_citation_map' not in va:
        print('❌ CRITICAL: Missing _citation_map')
    else:
        citation_map = va['_citation_map']
        if not isinstance(citation_map, dict):
            print(f'❌ CRITICAL: _citation_map is not a dict (type: {type(citation_map)})')
        elif len(citation_map) == 0:
            print('⚠️  WARNING: _citation_map is empty')
        else:
            print(f'✅ PASS: Citation map present with {len(citation_map)} entries')
            print(f'    Sample entries:')
            for num, url in list(citation_map.items())[:3]:
                print(f'      [{num}] → {url[:70]}...')
    
    # CHECK 3: Parallel Results Merge
    print('\n\n🔍 CHECK 3: Parallel Results Merge')
    print('-'*80)
    
    has_image = 'image_url' in va and va['image_url']
    has_toc = 'toc' in va or any('toc' in k.lower() for k in va.keys())
    has_faq = 'faq' in str(va).lower() or any('faq' in k.lower() for k in va.keys())
    has_paa = 'paa' in str(va).lower() or any('paa' in k.lower() for k in va.keys())
    
    status_icon_img = "✅" if has_image else "❌"
    print(f'  Image URL: {status_icon_img}')
    if has_image:
        print(f'      URL: {va.get("image_url", "N/A")[:70]}...')
    
    status_icon_toc = "✅" if has_toc else "❌"
    print(f'  ToC: {status_icon_toc}')
    if has_toc:
        toc = va.get('toc', {})
        if isinstance(toc, dict):
            print(f'      Entries: {len(toc)}')
    
    status_icon_faq = "✅" if has_faq else "⚠️"
    print(f'  FAQ: {status_icon_faq}')
    status_icon_paa = "✅" if has_paa else "⚠️"
    print(f'  PAA: {status_icon_paa}')
    
    # CHECK 4: HTML Content Preservation
    print('\n\n🔍 CHECK 4: HTML Content Preservation')
    print('-'*80)
    
    html_fields = ['Intro', 'Direct_Answer'] + [f'section_{i:02d}_content' for i in range(1, 7)]
    html_preserved = True
    
    for field in html_fields:
        if field in va and va[field]:
            html = str(va[field])
            # Check if HTML structure is preserved
            if '<p>' in html and '</p>' in html:
                # Check for unencoded &
                if '&' in html:
                    # Check if it's properly encoded (not standalone &)
                    import re
                    unencoded = re.findall(r'&(?!amp;|lt;|gt;|quot;|#\d+;|#[xX][0-9a-fA-F]+;)', html)
                    if unencoded:
                        print(f'  ⚠️  {field}: Found {len(unencoded)} potentially unencoded & characters')
                        html_preserved = False
                    else:
                        print(f'  ✅ {field}: HTML structure preserved, entities encoded')
                else:
                    print(f'  ✅ {field}: HTML structure preserved')
            else:
                print(f'  ⚠️  {field}: No HTML structure found')
    
    # CHECK 5: Data Structure
    print('\n\n🔍 CHECK 5: Data Structure')
    print('-'*80)
    
    nested_dicts = sum(1 for v in va.values() if isinstance(v, dict))
    nested_lists = sum(1 for v in va.values() if isinstance(v, list))
    
    print(f'  Total fields: {len(va)}')
    print(f'  Nested dicts: {nested_dicts} (should be < 5 for flattening)')
    print(f'  Nested lists: {nested_lists}')
    
    if nested_dicts > 10:
        print(f'  ⚠️  WARNING: Many nested dicts ({nested_dicts}) - may not be fully flattened')
    else:
        print(f'  ✅ Data structure looks flattened')
    
    # Summary
    print('\n\n' + '='*80)
    print('VERIFICATION SUMMARY')
    print('='*80)
    
    checks_passed = []
    checks_failed = []
    
    if not found_manip:
        checks_passed.append('No content manipulation fields')
    else:
        checks_failed.append('Content manipulation fields found')
    
    if '_citation_map' in va and isinstance(va['_citation_map'], dict) and len(va['_citation_map']) > 0:
        checks_passed.append('Citation map present')
    else:
        checks_failed.append('Citation map missing or invalid')
    
    if has_image and has_toc:
        checks_passed.append('Parallel results merged')
    else:
        checks_failed.append('Parallel results not fully merged')
    
    if html_preserved:
        checks_passed.append('HTML content preserved')
    else:
        checks_failed.append('HTML content issues found')
    
    print(f'\n✅ Passed: {len(checks_passed)}')
    for check in checks_passed:
        print(f'    - {check}')
    
    if checks_failed:
        print(f'\n❌ Failed: {len(checks_failed)}')
        for check in checks_failed:
            print(f'    - {check}')
    else:
        print(f'\n✅ All checks passed! Stage 8 is correctly simplified.')

if __name__ == "__main__":
    verify_stage8()

