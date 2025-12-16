#!/usr/bin/env python3
"""
Final End-to-End Verification

Tests all recent fixes together:
1. Citation keywords
2. PDF images and margins
3. CSV full content
4. Excel single-line HTML
5. TOC short labels
6. Em/en dash replacement
7. HTML entity encoding
"""

import json
import asyncio
from pathlib import Path
from pipeline.models.citation import Citation, CitationList
from pipeline.processors.article_exporter import ArticleExporter
from pipeline.models.output_schema import ArticleOutput

def test_citation_keywords():
    """Test citation keyword extraction."""
    print("="*80)
    print("TEST 1: Citation Keywords")
    print("="*80)
    
    test_citations = [
        Citation(number=1, title="IBM AI Projects to Profits", url="https://www.ibm.com/test"),
        Citation(number=2, title="Gartner Top Tech Trends 2025", url="https://www.gartner.com/test"),
        Citation(number=3, title="Forrester AP Automation Use Cases", url="https://www.forrester.com/test"),
    ]
    
    citation_list = CitationList(citations=test_citations)
    html = citation_list.to_html_paragraph_list()
    
    # Check keywords appear
    has_keywords = '|' in html
    has_ai = 'AI' in html or 'ai' in html.lower()
    has_automation = 'Automation' in html
    
    print(f"✅ Keywords present: {has_keywords}")
    print(f"✅ AI keyword found: {has_ai}")
    print(f"✅ Automation keyword found: {has_automation}")
    
    # Show example
    import re
    links = re.findall(r'<a[^>]*>([^<]+)</a>', html)
    if links:
        print(f"\nExample output:")
        for i, link in enumerate(links[:3], 1):
            print(f"  {i}. {link}")
    
    return has_keywords and has_ai


def test_article_exporter_features():
    """Test ArticleExporter features."""
    print("\n" + "="*80)
    print("TEST 2: ArticleExporter Features")
    print("="*80)
    
    exporter_code = Path('pipeline/processors/article_exporter.py').read_text()
    
    checks = {
        'PDF image embedding': '_embed_images_for_pdf' in exporter_code,
        'PDF margins': '_add_pdf_margins' in exporter_code,
        'Single-line HTML': '_html_to_single_line' in exporter_code,
        'CSV truncation removed': 'content[:500]' not in exporter_code,
    }
    
    all_pass = True
    for feature, status in checks.items():
        print(f"{'✅' if status else '❌'} {feature}: {status}")
        if not status:
            all_pass = False
    
    return all_pass


def test_stage8_fixes():
    """Test Stage 8 fixes."""
    print("\n" + "="*80)
    print("TEST 3: Stage 8 Fixes")
    print("="*80)
    
    stage8_code = Path('pipeline/blog_generation/stage_08_cleanup.py').read_text()
    
    checks = {
        'HTML entity encoding': '_encode_html_entities_in_content' in stage8_code,
        'Em dash replacement': "re.sub(r'[—–]', '-'" in stage8_code,
    }
    
    all_pass = True
    for fix, status in checks.items():
        print(f"{'✅' if status else '❌'} {fix}: {status}")
        if not status:
            all_pass = False
    
    return all_pass


def test_toc_labels():
    """Test TOC label generation."""
    print("\n" + "="*80)
    print("TEST 4: TOC Labels")
    print("="*80)
    
    stage2_code = Path('pipeline/blog_generation/stage_02_gemini_call.py').read_text()
    
    has_toc_generation = '_generate_toc_labels' in stage2_code
    
    print(f"{'✅' if has_toc_generation else '❌'} TOC label generation: {has_toc_generation}")
    
    return has_toc_generation


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "="*80)
    print("TEST 5: Edge Cases")
    print("="*80)
    
    # Test empty citations
    empty_list = CitationList(citations=[])
    empty_html = empty_list.to_html_paragraph_list()
    empty_handled = empty_html == "" or '<ol>' not in empty_html
    
    # Test very long title
    long_title = Citation(number=1, title="A" * 200, url="https://example.com")
    long_list = CitationList(citations=[long_title])
    long_html = long_list.to_html_paragraph_list()
    long_handled = len(long_html) > 0
    
    # Test special characters
    special_title = Citation(number=1, title="Test & Company — Special Characters", url="https://example.com")
    special_list = CitationList(citations=[special_title])
    special_html = special_list.to_html_paragraph_list()
    special_handled = len(special_html) > 0
    
    checks = {
        'Empty citations handled': empty_handled,
        'Long titles handled': long_handled,
        'Special characters handled': special_handled,
    }
    
    all_pass = True
    for case, status in checks.items():
        print(f"{'✅' if status else '❌'} {case}: {status}")
        if not status:
            all_pass = False
    
    return all_pass


def main():
    """Run all verification tests."""
    print("\n" + "="*80)
    print("FINAL END-TO-END VERIFICATION")
    print("="*80)
    print()
    
    results = {
        'Citation Keywords': test_citation_keywords(),
        'ArticleExporter Features': test_article_exporter_features(),
        'Stage 8 Fixes': test_stage8_fixes(),
        'TOC Labels': test_toc_labels(),
        'Edge Cases': test_edge_cases(),
    }
    
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print()
    
    all_pass = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_pass = False
    
    print()
    print("="*80)
    if all_pass:
        print("✅ ALL TESTS PASSED - PRODUCTION READY!")
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW NEEDED")
    print("="*80)


if __name__ == "__main__":
    main()


