#!/usr/bin/env python3
"""
Deep HTML Output Audit

Thoroughly audits the HTML content from each stage:
- HTML structure and validity
- Citation links and formatting
- Conversational phrases
- Content quality improvements
- Paragraph structure
- Lists and formatting
"""

import json
import re
from pathlib import Path
from collections import Counter


def audit_html_structure(html_content: str, stage_name: str):
    """Audit HTML structure and quality."""
    print(f"\n{'='*80}")
    print(f"HTML STRUCTURE AUDIT: {stage_name}")
    print(f"{'='*80}\n")
    
    # Basic stats
    print("📊 Basic Statistics:")
    print(f"  Total length: {len(html_content)} chars")
    print(f"  Paragraphs: {html_content.count('<p>')}")
    print(f"  Unclosed <p> tags: {html_content.count('<p>') - html_content.count('</p>')}")
    print(f"  Lists: {html_content.count('<ul>')} unordered, {html_content.count('<ol>')} ordered")
    print(f"  List items: {html_content.count('<li>')}")
    print(f"  Bold tags: {html_content.count('<strong>')}")
    print(f"  Italic tags: {html_content.count('<em>')}")
    
    # Extract paragraphs
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html_content, re.DOTALL)
    print(f"\n  Paragraph Analysis:")
    print(f"    Total paragraphs: {len(paragraphs)}")
    
    if paragraphs:
        word_counts = []
        citation_counts = []
        for para in paragraphs:
            text = re.sub(r'<[^>]+>', '', para)
            words = len(text.split())
            citations = len(re.findall(r'<a[^>]*class=["\']citation["\']', para))
            word_counts.append(words)
            citation_counts.append(citations)
        
        print(f"    Average words per paragraph: {sum(word_counts)/len(word_counts):.1f}")
        print(f"    Min words: {min(word_counts)}, Max words: {max(word_counts)}")
        print(f"    Paragraphs with citations: {sum(1 for c in citation_counts if c > 0)}/{len(paragraphs)}")
        print(f"    Average citations per paragraph: {sum(citation_counts)/len(citation_counts):.2f}")
        print(f"    Paragraphs with 2+ citations: {sum(1 for c in citation_counts if c >= 2)}")
    
    # Citation links audit
    print(f"\n  Citation Links Audit:")
    citation_pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*class=["\']citation["\'][^>]*>([^<]+)</a>'
    citations = re.findall(citation_pattern, html_content)
    print(f"    Total citation links: {len(citations)}")
    
    if citations:
        print(f"    Sample citations:")
        for i, (url, text) in enumerate(citations[:5], 1):
            print(f"      [{i}] \"{text[:40]}...\" → {url[:70]}...")
        
        # Check URL validity
        valid_urls = sum(1 for url, _ in citations if url.startswith(('http://', 'https://')))
        print(f"    Valid URLs: {valid_urls}/{len(citations)}")
    
    # Conversational phrases audit
    print(f"\n  Conversational Phrases Audit:")
    phrases = [
        "let's", "how does", "what is", "why does", "you'll", "here's", 
        "you can", "if you", "when you", "that's", "this is", "how can",
        "what are", "how do", "why should", "where can"
    ]
    
    phrase_counts = {}
    for phrase in phrases:
        count = html_content.lower().count(phrase)
        if count > 0:
            phrase_counts[phrase] = count
    
    print(f"    Total unique phrases found: {len(phrase_counts)}")
    print(f"    Total phrase occurrences: {sum(phrase_counts.values())}")
    if phrase_counts:
        print(f"    Top phrases:")
        for phrase, count in sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"      \"{phrase}\": {count}x")
    
    # Question format audit
    print(f"\n  Question Format Audit:")
    question_words = ["what", "how", "why", "when", "where", "which", "who"]
    question_count = sum(1 for word in question_words 
                         if re.search(rf'<strong>{word}\s+', html_content, re.IGNORECASE))
    print(f"    Question-format phrases (bold): {question_count}")
    
    # HTML validity checks
    print(f"\n  HTML Validity Checks:")
    # Check for unclosed tags
    open_tags = re.findall(r'<([a-zA-Z]+)[^>]*>', html_content)
    close_tags = re.findall(r'</([a-zA-Z]+)>', html_content)
    tag_balance = Counter(open_tags) - Counter(close_tags)
    if tag_balance:
        print(f"    ⚠️  Unclosed tags: {dict(tag_balance)}")
    else:
        print(f"    ✅ All tags properly closed")
    
    # Check for malformed attributes
    malformed = re.findall(r'<[^>]*\s+[^=]+\s+[^>]*>', html_content)
    if malformed:
        print(f"    ⚠️  Potentially malformed attributes: {len(malformed)}")
    else:
        print(f"    ✅ No malformed attributes detected")
    
    return {
        'length': len(html_content),
        'paragraphs': len(paragraphs),
        'citations': len(citations),
        'conversational_phrases': sum(phrase_counts.values()),
        'unique_phrases': len(phrase_counts),
        'question_formats': question_count
    }


def compare_stages(stage2_data: dict, stage3_data: dict):
    """Compare Stage 2 vs Stage 3 HTML outputs."""
    print(f"\n\n{'='*80}")
    print("STAGE 2 vs STAGE 3 COMPARISON")
    print(f"{'='*80}\n")
    
    sd2 = stage2_data['structured_data']
    sd3 = stage3_data['structured_data']
    
    # Compare Intro
    print("📝 INTRO COMPARISON:")
    print("-" * 80)
    intro2_stats = audit_html_structure(sd2['Intro'], "Stage 2 Intro")
    intro3_stats = audit_html_structure(sd3['Intro'], "Stage 3 Intro")
    
    print(f"\n  Improvements:")
    print(f"    Citations: {intro2_stats['citations']} → {intro3_stats['citations']} ({intro3_stats['citations'] - intro2_stats['citations']:+d})")
    print(f"    Conversational phrases: {intro2_stats['conversational_phrases']} → {intro3_stats['conversational_phrases']} ({intro3_stats['conversational_phrases'] - intro2_stats['conversational_phrases']:+d})")
    print(f"    Question formats: {intro2_stats['question_formats']} → {intro3_stats['question_formats']} ({intro3_stats['question_formats'] - intro2_stats['question_formats']:+d})")
    
    # Compare each section
    for i in range(1, 7):
        key = f'section_{i:02d}_content'
        if key in sd2 and key in sd3:
            print(f"\n\n📄 SECTION {i} COMPARISON:")
            print("-" * 80)
            s2_stats = audit_html_structure(sd2[key], f"Stage 2 Section {i}")
            s3_stats = audit_html_structure(sd3[key], f"Stage 3 Section {i}")
            
            print(f"\n  Improvements:")
            print(f"    Citations: {s2_stats['citations']} → {s3_stats['citations']} ({s3_stats['citations'] - s2_stats['citations']:+d})")
            print(f"    Conversational phrases: {s2_stats['conversational_phrases']} → {s3_stats['conversational_phrases']} ({s3_stats['conversational_phrases'] - s2_stats['conversational_phrases']:+d})")
            print(f"    Question formats: {s2_stats['question_formats']} → {s3_stats['question_formats']} ({s3_stats['question_formats'] - s2_stats['question_formats']:+d})")
            
            # Show actual content differences
            print(f"\n  Content Changes:")
            # Extract first paragraph from each
            paras2 = re.findall(r'<p[^>]*>(.*?)</p>', sd2[key], re.DOTALL)
            paras3 = re.findall(r'<p[^>]*>(.*?)</p>', sd3[key], re.DOTALL)
            
            if paras2 and paras3:
                text2 = re.sub(r'<[^>]+>', '', paras2[0])[:200]
                text3 = re.sub(r'<[^>]+>', '', paras3[0])[:200]
                
                if text2 != text3:
                    print(f"    Stage 2 first para: {text2}...")
                    print(f"    Stage 3 first para: {text3}...")
                    
                    # Find what was added
                    added_phrases = []
                    for phrase in ["let's", "how does", "what is", "you'll", "here's"]:
                        if phrase in text3.lower() and phrase not in text2.lower():
                            added_phrases.append(phrase)
                    if added_phrases:
                        print(f"    ✅ Added phrases: {', '.join(added_phrases)}")


def audit_stage8_output(stage8_data: dict):
    """Audit Stage 8 output - critical check for simplification."""
    print(f"\n\n{'='*80}")
    print("STAGE 8 OUTPUT AUDIT - CRITICAL SIMPLIFICATION CHECK")
    print(f"{'='*80}\n")
    
    if 'validated_article' not in stage8_data:
        print("  ⚠️  No validated_article found")
        return
    
    va = stage8_data['validated_article']
    
    print("🔍 Content Manipulation Fields Check (CRITICAL):")
    print("-" * 80)
    
    # Check for content manipulation fields
    content_manip_fields = [
        'humanized', 'normalized', 'sanitized', 'cleaned',
        'conversational_phrases_added', 'aeo_enforced',
        'converted_to_questions', 'split_paragraphs',
        'enhanced_direct_answer', 'fixed_citation_distribution'
    ]
    
    found_manip = []
    for field in va.keys():
        field_lower = field.lower()
        for manip in content_manip_fields:
            if manip in field_lower:
                found_manip.append(field)
                break
    
    if found_manip:
        print(f"  ❌ CRITICAL FAILURE: Found {len(found_manip)} content manipulation fields:")
        for field in found_manip:
            print(f"      - {field}")
    else:
        print(f"  ✅ PASS: No content manipulation fields found")
        print(f"      (Stage 8 correctly only merges and links)")
    
    # Check citation linking
    print(f"\n🔗 Citation Linking Check:")
    print("-" * 80)
    
    has_citation_map = '_citation_map' in va
    if has_citation_map:
        citation_map = va['_citation_map']
        print(f"  ✅ Citation map present: {len(citation_map)} entries")
        print(f"      Sample entries:")
        for num, url in list(citation_map.items())[:3]:
            print(f"        [{num}] → {url[:70]}...")
        
        # Check if citations are linked in content
        if 'Intro' in va:
            intro = va['Intro']
            # Look for citation links like <a href="#source-1">
            citation_links = re.findall(r'<a[^>]*href=["\']#source-(\d+)["\']', intro)
            if citation_links:
                print(f"      ✅ Citations linked in Intro: {len(citation_links)} links")
            else:
                # Check for [1] format
                citation_refs = re.findall(r'\[(\d+)\]', intro)
                if citation_refs:
                    print(f"      ⚠️  Found citation refs [1] format: {len(citation_refs)}")
                    print(f"      (Should be converted to <a href> links)")
    else:
        print(f"  ⚠️  No citation map found")
    
    # Check parallel results merge
    print(f"\n📦 Parallel Results Merge Check:")
    print("-" * 80)
    
    has_image = 'image_url' in va and va['image_url']
    has_toc = 'toc' in va or any('toc' in k for k in va.keys())
    has_faq = 'faq_items' in va or any('faq' in k.lower() for k in va.keys())
    has_paa = 'paa_items' in va or any('paa' in k.lower() for k in va.keys())
    
    print(f"  Image URL merged: {'✅' if has_image else '❌'}")
    if has_image:
        print(f"      URL: {va.get('image_url', 'N/A')[:70]}...")
    
    print(f"  ToC merged: {'✅' if has_toc else '❌'}")
    if has_toc:
        toc = va.get('toc', {})
        if isinstance(toc, dict):
            print(f"      Entries: {len(toc)}")
    
    print(f"  FAQ merged: {'✅' if has_faq else '❌'}")
    print(f"  PAA merged: {'✅' if has_paa else '❌'}")
    
    # Check data flattening
    print(f"\n📊 Data Structure Check:")
    print("-" * 80)
    
    nested_dicts = sum(1 for v in va.values() if isinstance(v, dict))
    nested_lists = sum(1 for v in va.values() if isinstance(v, list))
    
    print(f"  Total fields: {len(va)}")
    print(f"  Nested dicts: {nested_dicts} (should be < 5 for flattening)")
    print(f"  Nested lists: {nested_lists}")
    
    # Show preserved nested structures (should only be technical ones)
    preserved = []
    for key, value in va.items():
        if isinstance(value, dict) and key.startswith('_'):
            preserved.append(key)
    
    if preserved:
        print(f"  Preserved nested structures (technical only): {preserved}")
        print(f"      ✅ Correct - only technical fields preserved")
    
    # HTML content audit
    print(f"\n📄 HTML Content Quality Check:")
    print("-" * 80)
    
    html_fields = ['Intro', 'Direct_Answer'] + [f'section_{i:02d}_content' for i in range(1, 10)]
    total_html_length = 0
    total_citations = 0
    
    for field in html_fields:
        if field in va and va[field]:
            content = str(va[field])
            total_html_length += len(content)
            citations = len(re.findall(r'<a[^>]*class=["\']citation["\']', content))
            total_citations += citations
    
    print(f"  Total HTML content: {total_html_length:,} chars")
    print(f"  Total citations in HTML: {total_citations}")
    print(f"  Average citations per field: {total_citations/len([f for f in html_fields if f in va and va[f]]):.1f}")


def main():
    """Run deep HTML audit."""
    output_dir = Path('inspection_output_20251216-023614')
    
    print("="*80)
    print("DEEP HTML OUTPUT AUDIT")
    print("="*80)
    
    # Load stages
    stage2_file = output_dir / 'stage_02' / 'full_context.json'
    stage3_file = output_dir / 'stage_03' / 'full_context.json'
    stage8_file = output_dir / 'stage_08' / 'full_context.json'
    
    if not stage2_file.exists():
        print(f"❌ Stage 2 output not found: {stage2_file}")
        return
    
    stage2_data = json.load(open(stage2_file))
    
    if stage3_file.exists():
        stage3_data = json.load(open(stage3_file))
        compare_stages(stage2_data, stage3_data)
    else:
        print("⚠️  Stage 3 output not found yet")
    
    if stage8_file.exists():
        stage8_data = json.load(open(stage8_file))
        audit_stage8_output(stage8_data)
    else:
        print("\n⚠️  Stage 8 output not found yet - waiting for completion...")


if __name__ == "__main__":
    main()

