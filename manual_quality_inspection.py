#!/usr/bin/env python3
"""
Manual quality inspection of generated article.
"""

import json
import re
import sys
from pathlib import Path

def inspect_article(article_file):
    """Manually inspect article quality."""
    print("=" * 80)
    print("MANUAL QUALITY INSPECTION")
    print("=" * 80)
    print()
    
    with open(article_file, "r") as f:
        data = json.load(f)
    
    article = data.get("validated_article", {})
    quality_report = data.get("quality_report", {})
    
    # Get all content
    html_content = article.get("content", "") + " " + " ".join([
        article.get(f"section_{i:02d}_content", "") for i in range(1, 10)
    ])
    
    print("1. HTML STRUCTURE INSPECTION")
    print("-" * 80)
    
    # Check for double closing tags
    double_tags = html_content.count("</p></p>")
    print(f"Double closing tags (</p></p>): {double_tags}")
    if double_tags > 0:
        # Find examples
        matches = list(re.finditer(r'</p></p>', html_content))
        print(f"   Found at positions: {[m.start() for m in matches[:5]]}")
        # Show context
        for i, match in enumerate(matches[:3], 1):
            start = max(0, match.start() - 50)
            end = min(len(html_content), match.end() + 50)
            context = html_content[start:end]
            print(f"   Example {i}: ...{context}...")
    
    # Check paragraph structure
    paragraphs = re.findall(r'<p[^>]*>.*?</p>', html_content, re.DOTALL)
    print(f"\nTotal paragraphs: {len(paragraphs)}")
    
    # Check for malformed HTML
    open_p = html_content.count("<p>") + html_content.count("<p ")
    close_p = html_content.count("</p>")
    print(f"<p> tags: {open_p}, </p> tags: {close_p}")
    if open_p != close_p:
        print(f"   ⚠️  Mismatch: {abs(open_p - close_p)} unclosed tags")
    
    print("\n2. CONTENT QUALITY INSPECTION")
    print("-" * 80)
    
    # Sample paragraphs
    print("Sample paragraphs (first 5):")
    for i, para in enumerate(paragraphs[:5], 1):
        text = re.sub(r'<[^>]+>', ' ', para)
        words = len(text.split())
        citations = len(re.findall(r'\[\d+\]', para))
        print(f"\n   Para {i}:")
        print(f"   Words: {words}, Citations: {citations}")
        print(f"   Text: {text[:100]}...")
    
    # Citation distribution analysis
    print("\n3. CITATION DISTRIBUTION ANALYSIS")
    print("-" * 80)
    citation_counts = []
    for para in paragraphs:
        citations = len(re.findall(r'\[\d+\]', para))
        citation_counts.append(citations)
    
    paras_with_0 = sum(1 for c in citation_counts if c == 0)
    paras_with_1 = sum(1 for c in citation_counts if c == 1)
    paras_with_2plus = sum(1 for c in citation_counts if c >= 2)
    
    print(f"Paragraphs with 0 citations: {paras_with_0}")
    print(f"Paragraphs with 1 citation: {paras_with_1}")
    print(f"Paragraphs with 2+ citations: {paras_with_2plus}")
    print(f"Distribution: {paras_with_2plus/len(paragraphs)*100:.1f}% have 2+ citations")
    
    # Show examples of paragraphs with different citation counts
    print("\n   Examples:")
    for count in [0, 1, 2]:
        examples = [para for para, c in zip(paragraphs, citation_counts) if c == count][:2]
        if examples:
            print(f"\n   Paragraphs with {count} citation(s):")
            for para in examples:
                text = re.sub(r'<[^>]+>', ' ', para)[:80]
                print(f"   - {text}...")
    
    print("\n4. CONVERSATIONAL LANGUAGE INSPECTION")
    print("-" * 80)
    conversational_phrases = [
        "how to", "what is", "why does", "when should", "where can",
        "you can", "you should", "let's", "here's", "this is",
        "how can", "what are", "how do", "why should", "where are",
    ]
    content_lower = html_content.lower()
    found_phrases = {p: content_lower.count(p) for p in conversational_phrases if p in content_lower}
    
    print(f"Conversational phrases found: {len(found_phrases)}")
    for phrase, count in sorted(found_phrases.items(), key=lambda x: x[1], reverse=True):
        print(f"   '{phrase}': {count} occurrences")
    
    # Show examples in context
    if found_phrases:
        print("\n   Examples in context:")
        for phrase in list(found_phrases.keys())[:3]:
            matches = list(re.finditer(re.escape(phrase), content_lower))
            if matches:
                match = matches[0]
                start = max(0, match.start() - 30)
                end = min(len(html_content), match.end() + 50)
                context = html_content[start:end]
                print(f"   '{phrase}': ...{context}...")
    
    print("\n5. SECTION HEADERS INSPECTION")
    print("-" * 80)
    question_patterns = ["what is", "how does", "why does", "when should", "where can", "what are", "how can"]
    question_headers = []
    statement_headers = []
    
    for i in range(1, 10):
        title = article.get(f"section_{i:02d}_title", "")
        if title:
            title_lower = title.lower()
            if any(pattern in title_lower for pattern in question_patterns):
                question_headers.append(title)
            else:
                statement_headers.append(title)
    
    print(f"Question-format headers: {len(question_headers)}")
    for header in question_headers:
        print(f"   ✓ {header}")
    
    print(f"\nStatement-format headers: {len(statement_headers)}")
    for header in statement_headers[:5]:
        print(f"   - {header}")
    
    print("\n6. STRUCTURED DATA INSPECTION")
    print("-" * 80)
    list_count = html_content.count("<ul>") + html_content.count("<ol>")
    print(f"Lists found: {list_count}")
    
    # Find list examples
    list_matches = list(re.finditer(r'<(ul|ol)[^>]*>.*?</\1>', html_content, re.DOTALL))
    print(f"List instances: {len(list_matches)}")
    
    for i, match in enumerate(list_matches[:3], 1):
        list_html = match.group(0)
        items = re.findall(r'<li[^>]*>(.*?)</li>', list_html, re.DOTALL)
        print(f"\n   List {i}: {len(items)} items")
        for j, item in enumerate(items[:3], 1):
            text = re.sub(r'<[^>]+>', ' ', item).strip()
            print(f"   - {text[:60]}...")
    
    print("\n7. META TAGS INSPECTION")
    print("-" * 80)
    meta_title = article.get("Meta_Title", "")
    meta_desc = article.get("Meta_Description", "")
    
    print(f"Meta Title ({len(meta_title)} chars):")
    print(f"   '{meta_title}'")
    print(f"   {'✅ Within limit' if len(meta_title) <= 60 else '❌ Exceeds 60 chars'}")
    
    print(f"\nMeta Description ({len(meta_desc)} chars):")
    print(f"   '{meta_desc}'")
    print(f"   {'✅ Within limit' if len(meta_desc) <= 160 else '❌ Exceeds 160 chars'}")
    
    print("\n8. AEO SCORE BREAKDOWN")
    print("-" * 80)
    aeo_score = quality_report.get('metrics', {}).get('aeo_score', 0)
    print(f"AEO Score: {aeo_score}/100")
    
    # Detailed breakdown if available
    metrics = quality_report.get('metrics', {})
    if 'aeo_score_method' in metrics:
        print(f"Scoring method: {metrics['aeo_score_method']}")
    
    print("\n9. OVERALL ASSESSMENT")
    print("-" * 80)
    
    issues = []
    if double_tags > 0:
        issues.append(f"❌ {double_tags} double closing tags")
    if len(meta_title) > 60:
        issues.append(f"❌ Meta Title too long ({len(meta_title)} chars)")
    if len(meta_desc) > 160:
        issues.append(f"❌ Meta Description too long ({len(meta_desc)} chars)")
    if paras_with_2plus / len(paragraphs) < 0.6:
        issues.append(f"⚠️  Citation distribution low ({paras_with_2plus/len(paragraphs)*100:.1f}%)")
    if len(found_phrases) < 8:
        issues.append(f"⚠️  Conversational phrases low ({len(found_phrases)})")
    if len(question_headers) < 2:
        issues.append(f"⚠️  Question headers low ({len(question_headers)})")
    if list_count < 3:
        issues.append(f"⚠️  Lists low ({list_count})")
    if aeo_score < 70:
        issues.append(f"⚠️  AEO score below target ({aeo_score}/100)")
    
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ All checks passed!")
    
    print("\n" + "=" * 80)
    return article, quality_report

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        article_file = sys.argv[1]
    else:
        # Try to find the most recent article file
        article_files = list(Path(".").glob("*article*.json"))
        if article_files:
            latest = max(article_files, key=lambda p: p.stat().st_mtime)
            article_file = str(latest)
        else:
            print("No article files found")
            sys.exit(1)
    
    print(f"Inspecting: {article_file}\n")
    inspect_article(article_file)

