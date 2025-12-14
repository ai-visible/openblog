#!/usr/bin/env python3
"""
Test the simple HTML renderer vs the complex one.

This script:
1. Loads a raw Stage 2 output
2. Renders it with the simple renderer
3. Analyzes the output for issues

Usage:
    python3 test_simple_renderer.py
"""

import json
from pathlib import Path
from datetime import datetime

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")


def analyze_html_for_issues(html: str) -> dict:
    """Analyze HTML content for common issues."""
    import re
    
    issues = {
        "em_dashes": len(re.findall(r'—', html)),
        "en_dashes": len(re.findall(r'–', html)),
        "academic_citations": len(re.findall(r'\[\d+\]', html)),
        "citation_after_p": len(re.findall(r'</p>\s*[A-Z][A-Za-z]+\s+(reports?|notes?)', html)),
        "citation_in_p_tag": len(re.findall(r'<p>\s*<a[^>]*class="citation"', html)),
        "bullet_lists": html.count('<ul>'),
        "numbered_lists": html.count('<ol>'),
        "list_items": html.count('<li>'),
        "paragraphs": html.count('<p>'),
        "strong_tags": html.count('<strong>'),
        "links": html.count('<a '),
    }
    
    return issues


def test_simple_renderer():
    """Test the simple renderer with a raw Stage 2 output."""
    
    print("=" * 60)
    print("SIMPLE RENDERER TEST")
    print("=" * 60)
    print()
    
    # Load latest raw output
    raw_dir = Path("output/raw_gemini_outputs")
    raw_files = sorted(raw_dir.glob("raw_output_*.json"))
    
    if not raw_files:
        print("❌ No raw output files found")
        return
    
    latest_file = raw_files[-1]
    print(f"Loading: {latest_file.name}")
    
    with open(latest_file) as f:
        data = json.load(f)
    
    # Get parsed preview (the actual article data)
    article = data.get("parsed_preview", {})
    
    if not article:
        print("❌ No parsed_preview in raw output")
        return
    
    print(f"✅ Loaded article: {article.get('Headline', 'No title')}")
    print()
    
    # Render with simple renderer
    from pipeline.processors.html_renderer_simple import HTMLRendererSimple
    
    company_data = {
        "company_name": "TechCorp",
        "company_url": "https://example.com",
    }
    
    print("Rendering with HTMLRendererSimple...")
    html = HTMLRendererSimple.render(article, company_data)
    
    # Save output
    output_dir = Path("output/simple_renderer_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"simple_output_{timestamp}.html"
    
    with open(output_file, "w") as f:
        f.write(html)
    
    print(f"✅ Saved to: {output_file}")
    print()
    
    # Analyze for issues
    print("=" * 60)
    print("OUTPUT ANALYSIS")
    print("=" * 60)
    
    issues = analyze_html_for_issues(html)
    
    print(f"\n📊 Content Statistics:")
    print(f"   Paragraphs: {issues['paragraphs']}")
    print(f"   Strong tags: {issues['strong_tags']}")
    print(f"   Links: {issues['links']}")
    print(f"   Bullet lists: {issues['bullet_lists']}")
    print(f"   Numbered lists: {issues['numbered_lists']}")
    print(f"   List items: {issues['list_items']}")
    
    print(f"\n⚠️  Potential Issues:")
    print(f"   Em dashes (—): {issues['em_dashes']}")
    print(f"   En dashes (–): {issues['en_dashes']}")
    print(f"   Academic citations [N]: {issues['academic_citations']}")
    print(f"   Citations after </p>: {issues['citation_after_p']}")
    print(f"   Citations wrapped in <p>: {issues['citation_in_p_tag']}")
    
    # Verdict
    print()
    print("=" * 60)
    print("VERDICT")
    print("=" * 60)
    
    critical_issues = (
        issues['citation_after_p'] + 
        issues['citation_in_p_tag']
    )
    
    if critical_issues == 0:
        print("✅ No critical HTML structure issues!")
    else:
        print(f"❌ Found {critical_issues} critical HTML structure issues")
    
    if issues['bullet_lists'] + issues['numbered_lists'] == 0:
        print("⚠️  No lists in content (need to improve system instruction)")
    else:
        print(f"✅ Has {issues['bullet_lists'] + issues['numbered_lists']} lists")
    
    if issues['em_dashes'] > 0:
        print(f"⚠️  {issues['em_dashes']} em dashes need fixing")
    
    print()
    print(f"View the output: open {output_file}")
    
    return html, issues


if __name__ == "__main__":
    test_simple_renderer()

