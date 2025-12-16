#!/usr/bin/env python3
"""
REAL Issue Hunt - Proper HTML Validation
"""

import json
import re
from pathlib import Path
from html.parser import HTMLParser

class HTMLValidator(HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors = []
        self.tag_stack = []
    
    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        # Check for invalid nesting
        if len(self.tag_stack) > 1:
            prev_tag = self.tag_stack[-2]
            # <p> cannot contain <p>
            if prev_tag == 'p' and tag == 'p':
                self.errors.append(f"Nested <p> inside <p> at position {self.getpos()}")
            # <a> cannot contain <a>
            if prev_tag == 'a' and tag == 'a':
                self.errors.append(f"Nested <a> inside <a> at position {self.getpos()}")
    
    def handle_endtag(self, tag):
        if not self.tag_stack:
            self.errors.append(f"Closing tag </{tag}> without opening tag at {self.getpos()}")
        elif self.tag_stack[-1] != tag:
            self.errors.append(f"Mismatched tag: expected </{self.tag_stack[-1]}>, got </{tag}> at {self.getpos()}")
        else:
            self.tag_stack.pop()
    
    def close(self):
        super().close()
        if self.tag_stack:
            self.errors.append(f"Unclosed tags: {self.tag_stack}")

def hunt_real_issues():
    output_dir = Path('inspection_output_20251216-023614')
    
    stage2 = json.load(open(output_dir / 'stage_02' / 'full_context.json'))
    stage3 = json.load(open(output_dir / 'stage_03' / 'full_context.json'))
    
    sd2 = stage2['structured_data']
    sd3 = stage3['structured_data']
    
    issues = []
    
    print('='*80)
    print('REAL ISSUE HUNT - PROPER HTML VALIDATION')
    print('='*80)
    
    # Check each stage
    for stage_name, sd in [('Stage 2', sd2), ('Stage 3', sd3)]:
        print(f'\n\n{"="*80}')
        print(f'{stage_name} HTML Validation')
        print(f'{"="*80}')
        
        html_fields = ['Intro', 'Direct_Answer'] + [f'section_{i:02d}_content' for i in range(1, 10)]
        
        for field in html_fields:
            if field in sd and sd[field]:
                html = str(sd[field])
                
                # ISSUE 1: Validate HTML structure
                validator = HTMLValidator()
                try:
                    validator.feed(html)
                    validator.close()
                    if validator.errors:
                        for error in validator.errors:
                            issues.append(f"❌ {stage_name} {field}: {error}")
                except Exception as e:
                    issues.append(f"❌ {stage_name} {field}: HTML parsing error - {e}")
                
                # ISSUE 2: Check citation links
                citations = re.findall(r'<a[^>]*class=["\']citation["\'][^>]*>', html)
                for i, cit in enumerate(citations):
                    # Check href
                    href_match = re.search(r'href=["\']([^"\']*)["\']', cit)
                    if not href_match:
                        issues.append(f"❌ {stage_name} {field}: Citation {i+1} missing href")
                    else:
                        href = href_match.group(1)
                        if not href:
                            issues.append(f"❌ {stage_name} {field}: Citation {i+1} has empty href")
                        elif not href.startswith(('http://', 'https://', '#')):
                            issues.append(f"⚠️  {stage_name} {field}: Citation {i+1} has unusual href: {href[:50]}")
                    
                    # Check if citation has closing tag
                    cit_pos = html.find(cit)
                    if cit_pos != -1:
                        # Find next </a> after this citation
                        next_close = html.find('</a>', cit_pos)
                        if next_close == -1:
                            issues.append(f"❌ {stage_name} {field}: Citation {i+1} missing closing </a>")
                        else:
                            # Check if there's another <a> before the closing </a>
                            between = html[cit_pos:next_close]
                            if '<a' in between[1:]:  # Skip the opening tag itself
                                issues.append(f"❌ {stage_name} {field}: Citation {i+1} has nested <a> tag")
                
                # ISSUE 3: Check for empty paragraphs
                paras = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
                for i, para in enumerate(paras):
                    text = re.sub(r'<[^>]+>', '', para).strip()
                    if len(text) == 0:
                        issues.append(f"❌ {stage_name} {field}: Paragraph {i+1} is completely empty")
                    elif len(text) < 5:
                        issues.append(f"⚠️  {stage_name} {field}: Paragraph {i+1} is very short ({len(text)} chars): '{text}'")
                
                # ISSUE 4: Check citation distribution
                paras = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
                long_paras_no_citations = []
                for i, para in enumerate(paras):
                    text = re.sub(r'<[^>]+>', '', para).strip()
                    citations = len(re.findall(r'<a[^>]*class=["\']citation["\']', para))
                    if len(text) > 100 and citations == 0:
                        long_paras_no_citations.append(i+1)
                
                if len(long_paras_no_citations) > len(paras) * 0.4:
                    issues.append(f"⚠️  {stage_name} {field}: {len(long_paras_no_citations)}/{len(paras)} long paragraphs lack citations")
                
                # ISSUE 5: Check for broken HTML entities
                if '&' in html:
                    # Check for unencoded & that's not part of an entity
                    if re.search(r'&[^#a-zA-Z]', html):
                        issues.append(f"⚠️  {stage_name} {field}: Potential unencoded & character")
                
                # ISSUE 6: Check for unclosed lists
                ul_count = html.count('<ul>')
                ul_close_count = html.count('</ul>')
                if ul_count != ul_close_count:
                    issues.append(f"❌ {stage_name} {field}: Unclosed <ul> tags ({ul_count} open, {ul_close_count} closed)")
                
                li_count = html.count('<li>')
                li_close_count = html.count('</li>')
                if li_count != li_close_count:
                    issues.append(f"❌ {stage_name} {field}: Unclosed <li> tags ({li_count} open, {li_close_count} closed)")
                
                # ISSUE 7: Check for <li> outside <ul>
                # This is complex, but we can check if <li> appears without <ul> before it
                li_positions = [m.start() for m in re.finditer(r'<li[^>]*>', html)]
                for li_pos in li_positions:
                    # Check if there's a <ul> before this <li>
                    before_li = html[:li_pos]
                    last_ul = before_li.rfind('<ul')
                    last_ul_close = before_li.rfind('</ul>')
                    if last_ul == -1 or (last_ul_close > last_ul):
                        issues.append(f"⚠️  {stage_name} {field}: <li> tag at position {li_pos} may be outside <ul>")
                        break  # Only report once per field
                
                # ISSUE 8: Check for malformed attributes
                # Look for attributes without values or with unquoted values
                if re.search(r'<[^>]*\s+[a-zA-Z-]+[^=]\s*[^>]*>', html):
                    issues.append(f"⚠️  {stage_name} {field}: Potential malformed attributes")
    
    # Check Stage 8 if available
    stage8_file = output_dir / 'stage_08' / 'full_context.json'
    if stage8_file.exists():
        print(f'\n\n{"="*80}')
        print('STAGE 8 ISSUE CHECK - CRITICAL')
        print(f'{"="*80}')
        
        stage8 = json.load(open(stage8_file))
        
        if 'validated_article' in stage8:
            va = stage8['validated_article']
            
            # CRITICAL: Check for content manipulation fields
            manip_fields = [k for k in va.keys() if any(x in k.lower() for x in 
                ['humanized', 'normalized', 'sanitized', 'cleaned', 'conversational_phrases_added', 
                 'aeo_enforced', 'converted_to_questions', 'split_paragraphs'])]
            if manip_fields:
                issues.append(f"❌ CRITICAL Stage 8: Found content manipulation fields: {manip_fields}")
            else:
                print("✅ Stage 8: No content manipulation fields found")
            
            # Check citation map
            if '_citation_map' not in va:
                issues.append(f"❌ Stage 8: Missing _citation_map")
            else:
                citation_map = va['_citation_map']
                if not isinstance(citation_map, dict):
                    issues.append(f"❌ Stage 8: _citation_map is not a dict")
                elif len(citation_map) == 0:
                    issues.append(f"⚠️  Stage 8: _citation_map is empty")
    
    # Print all issues
    print('\n\n' + '='*80)
    print('ISSUES FOUND')
    print('='*80)
    
    if issues:
        critical = [i for i in issues if '❌' in i]
        warnings = [i for i in issues if '⚠️' in i]
        
        if critical:
            print(f'\n❌ CRITICAL ISSUES ({len(critical)}):')
            for i, issue in enumerate(critical, 1):
                print(f'  {i}. {issue}')
        
        if warnings:
            print(f'\n⚠️  WARNINGS ({len(warnings)}):')
            for i, issue in enumerate(warnings, 1):
                print(f'  {i}. {issue}')
        
        print(f'\n\nTotal: {len(issues)} issues ({len(critical)} critical, {len(warnings)} warnings)')
    else:
        print('\n✅ No issues found! HTML is clean.')

if __name__ == "__main__":
    hunt_real_issues()

