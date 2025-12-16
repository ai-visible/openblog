#!/usr/bin/env python3
"""
Deep HTML Inspection - Reads and analyzes actual HTML content
"""

import json
import re
import os
from pathlib import Path

def inspect_html_deeply():
    output_dir = Path('inspection_output_20251216-023614')
    
    stage2 = json.load(open(output_dir / 'stage_02' / 'full_context.json'))
    stage3 = json.load(open(output_dir / 'stage_03' / 'full_context.json'))
    
    sd2 = stage2['structured_data']
    sd3 = stage3['structured_data']
    
    print('='*80)
    print('DEEP HTML INSPECTION - ALL SECTIONS')
    print('='*80)
    
    # Inspect each section's HTML
    for i in range(1, 7):
        key = f'section_{i:02d}_content'
        if key in sd2 and key in sd3:
            print(f'\n\n{"="*80}')
            print(f'SECTION {i}: {sd2.get(f"section_{i:02d}_title", "N/A")}')
            print(f'{"="*80}')
            
            html2 = sd2[key]
            html3 = sd3[key]
            
            # Extract all HTML elements
            print(f'\n📊 HTML Structure:')
            print(f'  Stage 2: {len(html2)} chars, {html2.count("<p>")} paragraphs')
            print(f'  Stage 3: {len(html3)} chars, {html3.count("<p>")} paragraphs')
            
            # Extract first paragraph HTML
            paras2 = re.findall(r'<p[^>]*>(.*?)</p>', html2, re.DOTALL)
            paras3 = re.findall(r'<p[^>]*>(.*?)</p>', html3, re.DOTALL)
            
            if paras2 and paras3:
                print(f'\n📄 First Paragraph HTML Comparison:')
                print(f'\n  Stage 2 HTML:')
                print(f'    {paras2[0][:400]}...')
                
                print(f'\n  Stage 3 HTML:')
                print(f'    {paras3[0][:400]}...')
                
                # Extract text
                text2 = re.sub(r'<[^>]+>', '', paras2[0])
                text3 = re.sub(r'<[^>]+>', '', paras3[0])
                
                print(f'\n  Text Comparison:')
                print(f'    Stage 2: {text2[:250]}...')
                print(f'    Stage 3: {text3[:250]}...')
                
                # Find bold tags
                bold2 = re.findall(r'<strong>(.*?)</strong>', paras2[0])
                bold3 = re.findall(r'<strong>(.*?)</strong>', paras3[0])
                
                if bold3:
                    print(f'\n  ✅ Stage 3 Added Bold Phrases: {bold3[:5]}')
                
                # Find lists
                lists2 = html2.count('<ul>')
                lists3 = html3.count('<ul>')
                if lists3 > lists2:
                    print(f'\n  ✅ Stage 3 Added Lists: {lists3 - lists2} new list(s)')
                    # Extract list HTML
                    list_html = re.findall(r'<ul[^>]*>(.*?)</ul>', html3, re.DOTALL)
                    if list_html:
                        items = re.findall(r'<li[^>]*>(.*?)</li>', list_html[0], re.DOTALL)
                        print(f'      List items: {len(items)}')
                        for j, item in enumerate(items[:3], 1):
                            text = re.sub(r'<[^>]+>', '', item)
                            print(f'        {j}. {text[:60]}...')
    
    # Check Stage 8
    stage8_file = output_dir / 'stage_08' / 'full_context.json'
    if stage8_file.exists():
        print(f'\n\n{"="*80}')
        print('STAGE 8 HTML INSPECTION - CRITICAL')
        print(f'{"="*80}')
        
        stage8 = json.load(open(stage8_file))
        
        if 'validated_article' in stage8:
            va = stage8['validated_article']
            
            print(f'\n🔍 Content Manipulation Fields Check:')
            manip_fields = [k for k in va.keys() if any(x in k.lower() for x in ['humanized', 'normalized', 'sanitized', 'cleaned', 'conversational_phrases', 'aeo_enforced'])]
            if manip_fields:
                print(f'  ❌ FOUND: {manip_fields}')
            else:
                print(f'  ✅ PASS: No content manipulation fields')
            
            print(f'\n📄 HTML Fields in validated_article:')
            html_fields = ['Intro', 'Direct_Answer'] + [f'section_{i:02d}_content' for i in range(1, 10)]
            for field in html_fields:
                if field in va and va[field]:
                    html = str(va[field])
                    print(f'\n  {field}:')
                    print(f'    Length: {len(html)} chars')
                    print(f'    Paragraphs: {html.count("<p>")}')
                    citations = html.count('class="citation"')
                    print(f'    Citations: {citations}')
                    print(f'    HTML preview: {html[:200]}...')
                    
                    # Check citation linking
                    if '_citation_map' in va:
                        print(f'    ✅ Has citation map')
                        # Check if citations are linked
                        citation_refs = re.findall(r'\[(\d+)\]', html)
                        if citation_refs:
                            print(f'    ⚠️  Found [1] format citations: {len(citation_refs)}')
                        else:
                            # Check for <a href="#source-1"> format
                            linked = re.findall(r'<a[^>]*href=["\']#source-(\d+)["\']', html)
                            if linked:
                                print(f'    ✅ Citations linked: {len(linked)} links')
    else:
        print(f'\n\n⏳ Stage 8 not ready yet')

if __name__ == "__main__":
    inspect_html_deeply()

