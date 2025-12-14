#!/usr/bin/env python3
"""
Verification script to check all fixes in generated HTML.
"""
import re
from pathlib import Path
from datetime import datetime

def verify_fixes(html_file: Path):
    """Verify all fixes in the generated HTML."""
    print("=" * 80)
    print("VERIFYING ALL FIXES IN GENERATED HTML")
    print("=" * 80)
    print(f"\nFile: {html_file}\n")
    
    html = html_file.read_text(encoding='utf-8')
    
    issues = []
    successes = []
    
    # 1. Check meta description
    meta_desc_match = re.search(r'<meta name="description" content="([^"]*)"', html)
    if meta_desc_match:
        meta_desc = meta_desc_match.group(1)
        if meta_desc and len(meta_desc.strip()) > 10:
            successes.append("✅ Meta description: Present and populated")
        else:
            issues.append("❌ Meta description: Empty or too short")
    else:
        issues.append("❌ Meta description: Not found")
    
    # 2. Check teaser
    if '<p class="teaser">' in html:
        teaser_match = re.search(r'<p class="teaser">([^<]+)</p>', html)
        if teaser_match and len(teaser_match.group(1).strip()) > 10:
            successes.append("✅ Teaser paragraph: Present and populated")
        else:
            issues.append("❌ Teaser paragraph: Empty or too short")
    else:
        issues.append("❌ Teaser paragraph: Not found")
    
    # 3. Check section variety (count paragraphs per section)
    sections = re.findall(r'<h2 id="toc_\d+">[^<]+</h2>', html)
    section_paragraph_counts = []
    for i, section in enumerate(sections):
        # Find content between this h2 and next h2
        start_idx = html.find(section)
        if i < len(sections) - 1:
            next_section = sections[i + 1]
            end_idx = html.find(next_section, start_idx)
        else:
            end_idx = html.find('</article>', start_idx)
        
        if end_idx > start_idx:
            section_content = html[start_idx:end_idx]
            para_count = section_content.count('<p>')
            section_paragraph_counts.append(para_count)
    
    if len(section_paragraph_counts) >= 3:
        # Check for variety (not all same length)
        unique_counts = len(set(section_paragraph_counts))
        if unique_counts >= 2:
            successes.append(f"✅ Section variety: {len(section_paragraph_counts)} sections with {unique_counts} different lengths")
        else:
            issues.append(f"⚠️  Section variety: {len(section_paragraph_counts)} sections but all same length")
    else:
        issues.append(f"⚠️  Section variety: Only {len(section_paragraph_counts)} sections found")
    
    # 4. Check sources formatting
    sources_match = re.search(r'<section class="citations">(.*?)</section>', html, re.DOTALL)
    if sources_match:
        sources_content = sources_match.group(1)
        # Check if sources have titles (not just URLs)
        bare_urls = len(re.findall(r'<li>https?://', sources_content))
        links_with_titles = len(re.findall(r'<li><a href=', sources_content))
        if links_with_titles > 0:
            successes.append(f"✅ Sources formatting: {links_with_titles} sources with titles")
        elif bare_urls > 0:
            issues.append(f"❌ Sources formatting: {bare_urls} bare URLs without titles")
        else:
            issues.append("⚠️  Sources formatting: No sources found")
    else:
        issues.append("❌ Sources section: Not found")
    
    # 5. Check TOC formatting (should have line breaks)
    toc_match = re.search(r'<div class="toc">(.*?)</div>', html, re.DOTALL)
    if toc_match:
        toc_content = toc_match.group(1)
        if '\n                <li>' in toc_content:
            successes.append("✅ TOC formatting: Line breaks between items")
        else:
            issues.append("❌ TOC formatting: No line breaks between items")
    else:
        issues.append("⚠️  TOC: Not found")
    
    # 6. Check paragraph spacing
    if '</p>\n<p>' in html:
        successes.append("✅ Paragraph spacing: Newlines between paragraphs")
    else:
        issues.append("⚠️  Paragraph spacing: No newlines found (may be fine if content is compact)")
    
    # 7. Check schema markup
    if 'application/ld+json' in html:
        schema_count = html.count('application/ld+json')
        if schema_count >= 2:
            successes.append(f"✅ Schema markup: {schema_count} schemas found")
        else:
            issues.append(f"⚠️  Schema markup: Only {schema_count} schema found (expected 2+)")
    else:
        issues.append("❌ Schema markup: Not found")
    
    # 8. Check for em/en dashes
    em_dashes = html.count('—')
    en_dashes = html.count('–')
    if em_dashes == 0 and en_dashes == 0:
        successes.append("✅ Em/en dashes: None found (zero tolerance enforced)")
    else:
        issues.append(f"❌ Em/en dashes: Found {em_dashes} em dashes and {en_dashes} en dashes")
    
    # 9. Check for broken paragraph structure
    broken_patterns = [
        r'</p>\s*<p><strong>[^<]+</strong></p>',  # </p><p><strong>text</strong></p>
        r'<p><strong>[^<]+</strong></p>\s*[^<]',  # <p><strong>text</strong></p> followed by text
    ]
    broken_count = 0
    for pattern in broken_patterns:
        broken_count += len(re.findall(pattern, html))
    
    if broken_count == 0:
        successes.append("✅ Paragraph structure: No broken patterns found")
    else:
        issues.append(f"❌ Paragraph structure: {broken_count} broken patterns found")
    
    # 10. Check internal links
    if '<aside class="section-related">' in html:
        internal_link_count = html.count('<aside class="section-related">')
        successes.append(f"✅ Internal links: {internal_link_count} sections with internal links")
    else:
        issues.append("⚠️  Internal links: None found (may not be in test data)")
    
    # 11. Check for mismatched paragraph tags
    open_p = html.count('<p>')
    close_p = html.count('</p>')
    if open_p == close_p:
        successes.append(f"✅ Paragraph tags: Balanced ({open_p} <p> and {close_p} </p>)")
    else:
        issues.append(f"❌ Paragraph tags: Mismatched ({open_p} <p> vs {close_p} </p>)")
    
    # Print results
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    
    print(f"\n✅ SUCCESSES ({len(successes)}):")
    for success in successes:
        print(f"   {success}")
    
    if issues:
        print(f"\n⚠️  ISSUES ({len(issues)}):")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("\n🎉 No issues found!")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {len(successes)} checks passed, {len(issues)} issues found")
    print("=" * 80)
    
    return len(issues) == 0

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        html_file = Path(sys.argv[1])
    else:
        # Find latest test output
        output_dir = Path("output")
        test_dirs = sorted([d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("test-fixes-")], reverse=True)
        if test_dirs:
            html_file = test_dirs[0] / "index.html"
        else:
            print("❌ No test output found. Please provide HTML file path.")
            sys.exit(1)
    
    if not html_file.exists():
        print(f"❌ File not found: {html_file}")
        sys.exit(1)
    
    success = verify_fixes(html_file)
    sys.exit(0 if success else 1)

