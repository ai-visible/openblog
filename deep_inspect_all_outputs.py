#!/usr/bin/env python3
"""
DEEP INSPECTION - ALL STAGE OUTPUTS

Comprehensive analysis of every stage's output:
- Data structures
- Content quality
- HTML structure
- Citations
- Links
- Completeness
- Issues
"""

import json
import re
from pathlib import Path
from collections import Counter
from html.parser import HTMLParser
from typing import Dict, List, Any, Optional


class HTMLStructureParser(HTMLParser):
    """Parse HTML to detect structure issues."""
    def __init__(self):
        super().__init__()
        self.errors = []
        self.tag_stack = []
        self.citations = []
        self.lists = []
        self.current_tag = None
    
    def handle_starttag(self, tag, attrs):
        self.tag_stack.append(tag)
        self.current_tag = tag
        
        # Check for nested tags
        if len(self.tag_stack) > 1:
            prev_tag = self.tag_stack[-2]
            if prev_tag == 'p' and tag == 'p':
                self.errors.append(f"Nested <p> inside <p>")
            if prev_tag == 'a' and tag == 'a':
                self.errors.append(f"Nested <a> inside <a>")
        
        # Extract citation links
        if tag == 'a':
            href = None
            citation_class = False
            for attr_name, attr_value in attrs:
                if attr_name == 'href':
                    href = attr_value
                if attr_name == 'class' and 'citation' in attr_value:
                    citation_class = True
            
            if citation_class and href:
                self.citations.append({
                    'href': href,
                    'tag': self.get_starttag_text()
                })
        
        # Track lists
        if tag == 'ul':
            self.lists.append({'type': 'ul', 'depth': len(self.tag_stack)})
        if tag == 'li':
            self.lists.append({'type': 'li', 'depth': len(self.tag_stack)})
    
    def handle_endtag(self, tag):
        if not self.tag_stack:
            self.errors.append(f"Closing tag </{tag}> without opening tag")
        elif self.tag_stack[-1] != tag:
            self.errors.append(f"Mismatched tag: expected </{self.tag_stack[-1]}>, got </{tag}>")
        else:
            self.tag_stack.pop()
    
    def close(self):
        super().close()
        if self.tag_stack:
            self.errors.append(f"Unclosed tags: {self.tag_stack}")


def inspect_stage_0(context_data: Dict) -> Dict[str, Any]:
    """Deep inspection of Stage 0 output."""
    inspection = {
        'stage': 0,
        'name': 'Data Fetch',
        'findings': [],
        'issues': []
    }
    
    # Check job config
    if 'job_config' in context_data:
        config = context_data['job_config']
        inspection['findings'].append({
            'check': 'Job Config Present',
            'status': 'PASS',
            'details': {'keys': list(config.keys()) if isinstance(config, dict) else 'N/A'}
        })
    else:
        inspection['issues'].append('Missing job_config')
    
    # Check company data
    if 'company_data' in context_data:
        company = context_data['company_data']
        inspection['findings'].append({
            'check': 'Company Data Present',
            'status': 'PASS',
            'details': {'keys': list(company.keys()) if isinstance(company, dict) else 'N/A'}
        })
    else:
        inspection['issues'].append('Missing company_data')
    
    return inspection


def inspect_stage_1(context_data: Dict) -> Dict[str, Any]:
    """Deep inspection of Stage 1 output."""
    inspection = {
        'stage': 1,
        'name': 'Prompt Build',
        'findings': [],
        'issues': []
    }
    
    prompt = context_data.get('prompt', '')
    
    if prompt:
        inspection['findings'].append({
            'check': 'Prompt Generated',
            'status': 'PASS',
            'details': {
                'length': len(prompt),
                'has_keyword': 'primary_keyword' in prompt.lower() or 'ai automation' in prompt.lower(),
                'has_company': 'company' in prompt.lower() or 'example' in prompt.lower()
            }
        })
        
        # Check prompt quality
        if len(prompt) < 500:
            inspection['issues'].append('Prompt seems too short')
        if len(prompt) > 10000:
            inspection['issues'].append('Prompt seems too long')
    else:
        inspection['issues'].append('Missing prompt')
    
    return inspection


def inspect_stage_2(context_data: Dict) -> Dict[str, Any]:
    """Deep inspection of Stage 2 output."""
    inspection = {
        'stage': 2,
        'name': 'Content Generation',
        'findings': [],
        'issues': []
    }
    
    if 'structured_data' not in context_data:
        inspection['issues'].append('Missing structured_data')
        return inspection
    
    sd = context_data['structured_data']
    
    # Required fields check
    required_fields = ['Headline', 'Subtitle', 'Intro', 'Direct_Answer', 'Sources']
    for field in required_fields:
        if field in sd and sd[field]:
            val = str(sd[field])
            inspection['findings'].append({
                'check': f'{field} Present',
                'status': 'PASS',
                'details': {'length': len(val), 'preview': val[:100]}
            })
        else:
            inspection['issues'].append(f'Missing or empty required field: {field}')
    
    # Sections check
    sections_with_content = []
    for i in range(1, 10):
        key = f'section_{i:02d}_content'
        if key in sd and sd[key]:
            content = str(sd[key])
            sections_with_content.append({
                'num': i,
                'length': len(content),
                'has_html': '<p>' in content,
                'citations': content.count('class="citation"')
            })
    
    inspection['findings'].append({
        'check': 'Sections Generated',
        'status': 'PASS' if len(sections_with_content) >= 6 else 'WARN',
        'details': {
            'count': len(sections_with_content),
            'sections': sections_with_content
        }
    })
    
    # Sources check
    if 'Sources' in sd:
        sources = str(sd['Sources'])
        citation_count = sources.count('[')
        inspection['findings'].append({
            'check': 'Sources Field',
            'status': 'PASS',
            'details': {
                'length': len(sources),
                'citation_markers': citation_count,
                'has_urls': 'http' in sources
            }
        })
    
    # FAQ/PAA check
    faq_count = sum(1 for i in range(1, 7) if f'faq_{i:02d}_question' in sd and sd[f'faq_{i:02d}_question'])
    paa_count = sum(1 for i in range(1, 5) if f'paa_{i:02d}_question' in sd and sd[f'paa_{i:02d}_question'])
    
    inspection['findings'].append({
        'check': 'FAQ/PAA Generated',
        'status': 'PASS',
        'details': {'faq_count': faq_count, 'paa_count': paa_count}
    })
    
    return inspection


def inspect_stage_3(context_data: Dict) -> Dict[str, Any]:
    """Deep inspection of Stage 3 output."""
    inspection = {
        'stage': 3,
        'name': 'Quality Refinement',
        'findings': [],
        'issues': []
    }
    
    if 'structured_data' not in context_data:
        inspection['issues'].append('Missing structured_data')
        return inspection
    
    sd = context_data['structured_data']
    
    # Compare with Stage 2 to see improvements
    # Check for conversational phrases
    html_fields = ['Intro', 'Direct_Answer'] + [f'section_{i:02d}_content' for i in range(1, 7)]
    total_conversational = 0
    total_questions = 0
    total_citations = 0
    
    for field in html_fields:
        if field in sd and sd[field]:
            content = str(sd[field])
            
            # Conversational phrases
            phrases = ["let's", "how does", "what is", "you'll", "here's", "you can", "if you"]
            field_phrases = sum(content.lower().count(p) for p in phrases)
            total_conversational += field_phrases
            
            # Question formats
            questions = ["what is", "how does", "why does", "when should", "where can"]
            field_questions = sum(1 for q in questions if f'<strong>{q}' in content.lower())
            total_questions += field_questions
            
            # Citations
            field_citations = content.count('class="citation"')
            total_citations += field_citations
            
            # HTML structure check
            parser = HTMLStructureParser()
            try:
                parser.feed(content)
                if parser.errors:
                    inspection['issues'].extend([f'{field}: {e}' for e in parser.errors])
            except Exception as e:
                inspection['issues'].append(f'{field}: HTML parsing error - {e}')
            
            # Check for unencoded &
            unencoded_amp = re.findall(r'&(?!amp;|lt;|gt;|quot;|#\d+;|#[xX][0-9a-fA-F]+;)', content)
            if unencoded_amp:
                inspection['issues'].append(f'{field}: Found {len(unencoded_amp)} unencoded & characters')
    
    inspection['findings'].append({
        'check': 'Quality Improvements',
        'status': 'PASS',
        'details': {
            'conversational_phrases': total_conversational,
            'question_formats': total_questions,
            'citations': total_citations
        }
    })
    
    # Check required fields are not empty
    required_fields = ['Intro', 'Direct_Answer', 'section_01_content', 'section_02_content']
    for field in required_fields:
        if field not in sd or not sd[field]:
            inspection['issues'].append(f'Required field empty: {field}')
    
    return inspection


def inspect_stage_4(context_data: Dict) -> Dict[str, Any]:
    """Deep inspection of Stage 4 output."""
    inspection = {
        'stage': 4,
        'name': 'Citations Validation',
        'findings': [],
        'issues': []
    }
    
    pr = context_data.get('parallel_results', {})
    
    # Check citations_html
    if 'citations_html' in pr:
        citations_html = pr['citations_html']
        inspection['findings'].append({
            'check': 'Citations HTML Generated',
            'status': 'PASS',
            'details': {'length': len(str(citations_html))}
        })
    else:
        inspection['issues'].append('Missing citations_html')
    
    # Check citation map
    if 'validated_citation_map' in pr:
        citation_map = pr['validated_citation_map']
        if isinstance(citation_map, dict):
            inspection['findings'].append({
                'check': 'Citation Map Present',
                'status': 'PASS',
                'details': {'count': len(citation_map), 'sample': list(citation_map.items())[:3]}
            })
        else:
            inspection['issues'].append('Citation map is not a dict')
    else:
        inspection['issues'].append('Missing validated_citation_map')
    
    # Check citations_list
    if 'citations_list' in pr:
        citations_list = pr['citations_list']
        inspection['findings'].append({
            'check': 'Citations List Present',
            'status': 'PASS',
            'details': {'type': type(citations_list).__name__}
        })
    
    return inspection


def inspect_stage_5(context_data: Dict) -> Dict[str, Any]:
    """Deep inspection of Stage 5 output."""
    inspection = {
        'stage': 5,
        'name': 'Internal Links',
        'findings': [],
        'issues': []
    }
    
    pr = context_data.get('parallel_results', {})
    
    # Check internal links
    if 'internal_links_html' in pr:
        links_html = pr['internal_links_html']
        inspection['findings'].append({
            'check': 'Internal Links HTML Generated',
            'status': 'PASS',
            'details': {'length': len(str(links_html))}
        })
    else:
        inspection['issues'].append('Missing internal_links_html')
    
    return inspection


def inspect_stage_6(context_data: Dict) -> Dict[str, Any]:
    """Deep inspection of Stage 6 output."""
    inspection = {
        'stage': 6,
        'name': 'Image Generation',
        'findings': [],
        'issues': []
    }
    
    pr = context_data.get('parallel_results', {})
    
    # Check image
    if 'image_url' in pr:
        image_url = pr['image_url']
        inspection['findings'].append({
            'check': 'Image URL Generated',
            'status': 'PASS',
            'details': {'url': str(image_url)[:70]}
        })
    else:
        inspection['issues'].append('Missing image_url')
    
    return inspection


def inspect_stage_7(context_data: Dict) -> Dict[str, Any]:
    """Deep inspection of Stage 7 output."""
    inspection = {
        'stage': 7,
        'name': 'Similarity Check',
        'findings': [],
        'issues': []
    }
    
    pr = context_data.get('parallel_results', {})
    
    # Check similarity results
    if 'similarity_check' in pr:
        similarity = pr['similarity_check']
        inspection['findings'].append({
            'check': 'Similarity Check Complete',
            'status': 'PASS',
            'details': {'type': type(similarity).__name__}
        })
    else:
        inspection['issues'].append('Missing similarity_check')
    
    return inspection


def inspect_stage_8(context_data: Dict) -> Dict[str, Any]:
    """Deep inspection of Stage 8 output - CRITICAL."""
    inspection = {
        'stage': 8,
        'name': 'Merge & Link',
        'findings': [],
        'issues': [],
        'critical_checks': []
    }
    
    if 'validated_article' not in context_data:
        inspection['issues'].append('CRITICAL: Missing validated_article')
        return inspection
    
    va = context_data['validated_article']
    
    # CRITICAL CHECK 1: No content manipulation fields
    manip_fields = [
        'humanized', 'normalized', 'sanitized', 'cleaned',
        'conversational_phrases_added', 'aeo_enforced',
        'converted_to_questions', 'split_paragraphs'
    ]
    
    found_manip = []
    for field in va.keys():
        field_lower = field.lower()
        for manip in manip_fields:
            if manip in field_lower:
                found_manip.append(field)
    
    if found_manip:
        inspection['critical_checks'].append({
            'check': 'No Content Manipulation Fields',
            'status': 'FAIL',
            'details': {'found': found_manip}
        })
        inspection['issues'].append(f'CRITICAL: Found content manipulation fields: {found_manip}')
    else:
        inspection['critical_checks'].append({
            'check': 'No Content Manipulation Fields',
            'status': 'PASS',
            'details': {}
        })
    
    # CRITICAL CHECK 2: Citation map
    if '_citation_map' in va:
        citation_map = va['_citation_map']
        if isinstance(citation_map, dict) and len(citation_map) > 0:
            inspection['critical_checks'].append({
                'check': 'Citation Map Present',
                'status': 'PASS',
                'details': {'count': len(citation_map)}
            })
            
            # Verify citation URLs are valid
            invalid_urls = []
            for num, url in citation_map.items():
                if not url or not isinstance(url, str):
                    invalid_urls.append(num)
                elif not url.startswith(('http://', 'https://', '#')):
                    invalid_urls.append(num)
            
            if invalid_urls:
                inspection['issues'].append(f'Invalid citation URLs: {invalid_urls}')
        else:
            inspection['critical_checks'].append({
                'check': 'Citation Map Present',
                'status': 'WARN',
                'details': {'empty': True}
            })
    else:
        inspection['critical_checks'].append({
            'check': 'Citation Map Present',
            'status': 'FAIL',
            'details': {}
        })
        inspection['issues'].append('CRITICAL: Missing _citation_map')
    
    # Check parallel results merge
    has_image = 'image_url' in va and va['image_url']
    has_toc = 'toc' in va or any('toc' in k.lower() for k in va.keys())
    
    inspection['findings'].append({
        'check': 'Parallel Results Merged',
        'status': 'PASS' if (has_image and has_toc) else 'WARN',
        'details': {'has_image': has_image, 'has_toc': has_toc}
    })
    
    # Deep HTML inspection
    html_fields = ['Intro', 'Direct_Answer'] + [f'section_{i:02d}_content' for i in range(1, 7)]
    html_issues = []
    
    for field in html_fields:
        if field in va and va[field]:
            html = str(va[field])
            
            # HTML structure validation
            parser = HTMLStructureParser()
            try:
                parser.feed(html)
                if parser.errors:
                    html_issues.extend([f'{field}: {e}' for e in parser.errors])
            except Exception as e:
                html_issues.append(f'{field}: HTML parsing error - {e}')
            
            # Check for unencoded &
            unencoded = re.findall(r'&(?!amp;|lt;|gt;|quot;|#\d+;|#[xX][0-9a-fA-F]+;)', html)
            if unencoded:
                html_issues.append(f'{field}: {len(unencoded)} unencoded & characters')
            
            # Check citation links
            citations = re.findall(r'<a[^>]*class=["\']citation["\'][^>]*>', html)
            if citations:
                # Verify all citations have href
                for i, cit in enumerate(citations):
                    if 'href=' not in cit:
                        html_issues.append(f'{field}: Citation {i+1} missing href')
    
    if html_issues:
        inspection['issues'].extend(html_issues)
    
    # Data structure check
    nested_dicts = sum(1 for v in va.values() if isinstance(v, dict))
    inspection['findings'].append({
        'check': 'Data Flattening',
        'status': 'PASS' if nested_dicts < 10 else 'WARN',
        'details': {'nested_dicts': nested_dicts, 'total_fields': len(va)}
    })
    
    return inspection


def inspect_stage_9(context_data: Dict) -> Dict[str, Any]:
    """Deep inspection of Stage 9 output."""
    inspection = {
        'stage': 9,
        'name': 'Storage & Export',
        'findings': [],
        'issues': []
    }
    
    sr = context_data.get('storage_result', {})
    
    if sr:
        if isinstance(sr, dict):
            success = sr.get('success', False)
            inspection['findings'].append({
                'check': 'Storage Success',
                'status': 'PASS' if success else 'FAIL',
                'details': {'success': success}
            })
            
            # Check exported files
            if 'exported_files' in sr:
                files = sr['exported_files']
                expected_formats = ['html', 'markdown', 'pdf', 'csv', 'xlsx', 'json']
                found_formats = list(files.keys()) if isinstance(files, dict) else []
                missing = [f for f in expected_formats if f not in found_formats]
                
                inspection['findings'].append({
                    'check': 'Export Formats',
                    'status': 'PASS' if len(missing) == 0 else 'WARN',
                    'details': {
                        'found': found_formats,
                        'missing': missing
                    }
                })
        else:
            inspection['issues'].append('storage_result is not a dict')
    else:
        inspection['issues'].append('Missing storage_result')
    
    return inspection


def main():
    """Run deep inspection of all stages."""
    output_dir = Path('inspection_output_20251216-023614')
    
    print('='*80)
    print('DEEP INSPECTION - ALL STAGE OUTPUTS')
    print('='*80)
    
    all_inspections = []
    
    # Inspect each stage
    inspectors = [
        inspect_stage_0,
        inspect_stage_1,
        inspect_stage_2,
        inspect_stage_3,
        inspect_stage_4,
        inspect_stage_5,
        inspect_stage_6,
        inspect_stage_7,
        inspect_stage_8,
        inspect_stage_9,
    ]
    
    for stage_num, inspector in enumerate(inspectors):
        stage_file = output_dir / f'stage_{stage_num:02d}' / 'full_context.json'
        
        if not stage_file.exists():
            print(f'\n⚠️  Stage {stage_num}: Output file not found')
            continue
        
        print(f'\n\n{"="*80}')
        print(f'STAGE {stage_num}: {inspector.__name__.replace("inspect_stage_", "").replace("_", " ").title()}')
        print(f'{"="*80}')
        
        try:
            context_data = json.load(open(stage_file))
            inspection = inspector(context_data)
            all_inspections.append(inspection)
            
            # Print findings
            if inspection['findings']:
                print(f'\n✅ Findings:')
                for finding in inspection['findings']:
                    status_icon = "✅" if finding['status'] == 'PASS' else "⚠️" if finding['status'] == 'WARN' else "❌"
                    print(f'  {status_icon} {finding["check"]}: {finding["status"]}')
                    if 'details' in finding:
                        for key, value in finding['details'].items():
                            if isinstance(value, (str, int, float, bool)):
                                print(f'      {key}: {value}')
                            elif isinstance(value, list) and len(value) <= 3:
                                print(f'      {key}: {value}')
            
            # Print critical checks (Stage 8)
            if inspection.get('critical_checks'):
                print(f'\n🔍 Critical Checks:')
                for check in inspection['critical_checks']:
                    status_icon = "✅" if check['status'] == 'PASS' else "⚠️" if check['status'] == 'WARN' else "❌"
                    print(f'  {status_icon} {check["check"]}: {check["status"]}')
            
            # Print issues
            if inspection['issues']:
                print(f'\n⚠️  Issues Found ({len(inspection["issues"])}):')
                for issue in inspection['issues'][:10]:  # Limit to first 10
                    print(f'  - {issue}')
                if len(inspection['issues']) > 10:
                    print(f'  ... and {len(inspection["issues"]) - 10} more')
        
        except Exception as e:
            print(f'\n❌ Error inspecting Stage {stage_num}: {e}')
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f'\n\n{"="*80}')
    print('DEEP INSPECTION SUMMARY')
    print(f'{"="*80}')
    
    total_issues = sum(len(i['issues']) for i in all_inspections)
    critical_failures = sum(1 for i in all_inspections if any(c.get('status') == 'FAIL' for c in i.get('critical_checks', [])))
    
    print(f'\nTotal Stages Inspected: {len(all_inspections)}')
    print(f'Total Issues Found: {total_issues}')
    print(f'Critical Failures: {critical_failures}')
    
    # Stage 8 critical checks
    stage8_inspection = next((i for i in all_inspections if i['stage'] == 8), None)
    if stage8_inspection:
        print(f'\n🔍 Stage 8 Critical Checks:')
        for check in stage8_inspection.get('critical_checks', []):
            status_icon = "✅" if check['status'] == 'PASS' else "⚠️" if check['status'] == 'WARN' else "❌"
            print(f'  {status_icon} {check["check"]}: {check["status"]}')
    
    # Save full report
    report_file = output_dir / 'deep_inspection_report.json'
    with open(report_file, 'w') as f:
        json.dump({
            'summary': {
                'total_stages': len(all_inspections),
                'total_issues': total_issues,
                'critical_failures': critical_failures
            },
            'inspections': all_inspections
        }, f, indent=2, default=str)
    
    print(f'\n📄 Full report saved: {report_file}')


if __name__ == "__main__":
    main()

