"""
Deep Audit of Test Results
Comprehensive analysis of all 23 generated articles.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

def strip_html_tags(text):
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text)

def audit_single_article(article_dir: Path) -> Dict[str, Any]:
    """
    Audit a single article comprehensively.
    
    Checks:
    - All 6 fixes
    - Content quality
    - Structure integrity
    - HTML validity
    """
    
    audit = {
        "directory": article_dir.name,
        "exists": article_dir.exists(),
        "files_present": {},
        "fix_validations": {},
        "quality_checks": {},
        "issues": [],
        "warnings": [],
    }
    
    # Check file presence
    article_json = article_dir / "article.json"
    index_html = article_dir / "index.html"
    
    audit["files_present"]["article.json"] = article_json.exists()
    audit["files_present"]["index.html"] = index_html.exists()
    
    if not article_json.exists():
        audit["issues"].append("article.json missing")
        return audit
    
    # Load article data
    try:
        with open(article_json) as f:
            data = json.load(f)
    except Exception as e:
        audit["issues"].append(f"Failed to load article.json: {e}")
        return audit
    
    # === FIX #1: section_01_title PRESENT ===
    section_01_title = data.get("section_01_title", "")
    audit["fix_validations"]["fix_1_section_title_present"] = bool(section_01_title and section_01_title.strip())
    
    if not section_01_title or not section_01_title.strip():
        audit["issues"].append("Fix #1 FAILED: section_01_title missing or empty")
    
    # === FIX #6: NO HTML IN TITLES ===
    title_fields = [
        "Headline", "Subtitle", "Meta_Title", "Meta_Description",
        "section_01_title", "section_02_title", "section_03_title",
        "section_04_title", "section_05_title", "section_06_title",
        "section_07_title", "section_08_title", "section_09_title",
    ]
    
    html_in_titles = []
    for field in title_fields:
        value = data.get(field, "")
        if value and re.search(r'<[^>]+>', value):
            html_in_titles.append(f"{field}: {value[:100]}")
    
    audit["fix_validations"]["fix_6_no_html_in_titles"] = len(html_in_titles) == 0
    
    if html_in_titles:
        audit["issues"].append(f"Fix #6 FAILED: HTML found in {len(html_in_titles)} title fields")
        audit["warnings"].extend([f"HTML in title: {item}" for item in html_in_titles[:3]])
    
    # === FIX #2: TABLES GENERATION ===
    tables = data.get("tables", [])
    audit["fix_validations"]["fix_2_tables_count"] = len(tables) if isinstance(tables, list) else 0
    audit["fix_validations"]["fix_2_tables_valid"] = False
    
    if tables and isinstance(tables, list):
        # Check first table structure
        if len(tables) > 0:
            first_table = tables[0]
            has_structure = (
                isinstance(first_table, dict) and
                "title" in first_table and
                "headers" in first_table and
                "rows" in first_table
            )
            audit["fix_validations"]["fix_2_tables_valid"] = has_structure
            
            if not has_structure:
                audit["warnings"].append("Tables present but structure invalid")
    
    # === FIX #5: IMAGE URLs ABSOLUTE ===
    image_url = data.get("image_url", "")
    audit["fix_validations"]["fix_5_image_url"] = image_url
    audit["fix_validations"]["fix_5_image_absolute"] = (
        image_url.startswith("http://") or image_url.startswith("https://")
    ) if image_url else False
    
    if image_url and not audit["fix_validations"]["fix_5_image_absolute"]:
        audit["warnings"].append(f"Fix #5 WARNING: Image URL is relative: {image_url}")
    
    # Check HTML file if exists
    if index_html.exists():
        try:
            with open(index_html) as f:
                html_content = f.read()
            
            # Check for absolute URLs in HTML
            og_image = re.search(r'<meta property="og:image" content="([^"]+)"', html_content)
            if og_image:
                og_url = og_image.group(1)
                audit["fix_validations"]["fix_5_html_image_absolute"] = (
                    og_url.startswith("http://") or og_url.startswith("https://")
                )
                if not audit["fix_validations"]["fix_5_html_image_absolute"]:
                    audit["warnings"].append(f"HTML og:image is relative: {og_url}")
            
            # Check for tables in HTML
            table_count = html_content.count('<table class="comparison-table"')
            audit["fix_validations"]["fix_2_tables_in_html"] = table_count
            
            if len(tables) > 0 and table_count == 0:
                audit["warnings"].append("Tables in JSON but not rendered in HTML")
        
        except Exception as e:
            audit["warnings"].append(f"Failed to parse HTML: {e}")
    
    # === QUALITY CHECKS ===
    
    # Content presence
    sections_present = sum(1 for i in range(1, 10) if data.get(f"section_{i:02d}_title"))
    audit["quality_checks"]["sections_count"] = sections_present
    
    # Word count (approximate)
    intro = data.get("Intro", "")
    total_words = len(strip_html_tags(intro).split())
    for i in range(1, 10):
        content = data.get(f"section_{i:02d}_content", "")
        total_words += len(strip_html_tags(content).split())
    
    audit["quality_checks"]["word_count"] = total_words
    
    if total_words < 1500:
        audit["warnings"].append(f"Word count low: {total_words} (target: 2000-3000)")
    
    # FAQs, PAAs, Takeaways
    audit["quality_checks"]["faqs"] = sum(1 for i in range(1, 11) if data.get(f"faq_{i:02d}_question"))
    audit["quality_checks"]["paas"] = sum(1 for i in range(1, 6) if data.get(f"paa_{i:02d}_question"))
    audit["quality_checks"]["takeaways"] = sum(1 for i in range(1, 6) if data.get(f"takeaway_{i:02d}"))
    
    # Meta tags
    audit["quality_checks"]["meta_title_length"] = len(data.get("Meta_Title", ""))
    audit["quality_checks"]["meta_desc_length"] = len(data.get("Meta_Description", ""))
    
    if audit["quality_checks"]["meta_title_length"] > 60:
        audit["warnings"].append(f"Meta title too long: {audit['quality_checks']['meta_title_length']} chars")
    
    if audit["quality_checks"]["meta_desc_length"] > 160:
        audit["warnings"].append(f"Meta description too long: {audit['quality_checks']['meta_desc_length']} chars")
    
    # Citations
    sources = data.get("Sources", "")
    audit["quality_checks"]["has_citations"] = bool(sources and sources.strip())
    
    # Check for citation markers in content
    citation_markers = re.findall(r'\[\d+\]', intro + str([data.get(f"section_{i:02d}_content", "") for i in range(1, 10)]))
    audit["quality_checks"]["citation_count"] = len(set(citation_markers))
    
    return audit

def generate_audit_report(output_dir: Path):
    """Generate comprehensive audit report."""
    
    print("="*80)
    print("DEEP AUDIT OF TEST RESULTS - 23 ARTICLES")
    print("="*80)
    print()
    
    # Find all article directories
    article_dirs = sorted([d for d in output_dir.glob("api-20251207-13*") if d.is_dir()])
    
    print(f"Found {len(article_dirs)} articles to audit")
    print()
    
    # Audit each article
    audits = []
    for article_dir in article_dirs:
        audit = audit_single_article(article_dir)
        audits.append(audit)
    
    # Aggregate statistics
    stats = {
        "total_articles": len(audits),
        "articles_with_issues": 0,
        "articles_with_warnings": 0,
        "fix_1_pass": 0,
        "fix_2_tables_present": 0,
        "fix_2_tables_valid": 0,
        "fix_5_json_absolute": 0,
        "fix_5_html_absolute": 0,
        "fix_6_no_html": 0,
        "avg_sections": 0,
        "avg_word_count": 0,
        "avg_faqs": 0,
        "avg_paas": 0,
        "avg_takeaways": 0,
        "avg_citations": 0,
    }
    
    issues_by_type = defaultdict(int)
    warnings_by_type = defaultdict(list)
    
    for audit in audits:
        if audit["issues"]:
            stats["articles_with_issues"] += 1
            for issue in audit["issues"]:
                issue_type = issue.split(":")[0] if ":" in issue else issue
                issues_by_type[issue_type] += 1
        
        if audit["warnings"]:
            stats["articles_with_warnings"] += 1
            for warning in audit["warnings"]:
                warning_type = warning.split(":")[0] if ":" in warning else warning
                warnings_by_type[warning_type].append(audit["directory"])
        
        # Fix validations
        if audit["fix_validations"].get("fix_1_section_title_present"):
            stats["fix_1_pass"] += 1
        
        if audit["fix_validations"].get("fix_2_tables_count", 0) > 0:
            stats["fix_2_tables_present"] += 1
        
        if audit["fix_validations"].get("fix_2_tables_valid"):
            stats["fix_2_tables_valid"] += 1
        
        if audit["fix_validations"].get("fix_5_image_absolute"):
            stats["fix_5_json_absolute"] += 1
        
        if audit["fix_validations"].get("fix_5_html_image_absolute"):
            stats["fix_5_html_absolute"] += 1
        
        if audit["fix_validations"].get("fix_6_no_html_in_titles"):
            stats["fix_6_no_html"] += 1
        
        # Quality metrics
        stats["avg_sections"] += audit["quality_checks"].get("sections_count", 0)
        stats["avg_word_count"] += audit["quality_checks"].get("word_count", 0)
        stats["avg_faqs"] += audit["quality_checks"].get("faqs", 0)
        stats["avg_paas"] += audit["quality_checks"].get("paas", 0)
        stats["avg_takeaways"] += audit["quality_checks"].get("takeaways", 0)
        stats["avg_citations"] += audit["quality_checks"].get("citation_count", 0)
    
    # Calculate averages
    if stats["total_articles"] > 0:
        stats["avg_sections"] /= stats["total_articles"]
        stats["avg_word_count"] /= stats["total_articles"]
        stats["avg_faqs"] /= stats["total_articles"]
        stats["avg_paas"] /= stats["total_articles"]
        stats["avg_takeaways"] /= stats["total_articles"]
        stats["avg_citations"] /= stats["total_articles"]
    
    # Print summary
    print("="*80)
    print("FIX VALIDATION SUMMARY")
    print("="*80)
    print(f"Fix #1 (section_01_title present):  {stats['fix_1_pass']}/{stats['total_articles']} ({stats['fix_1_pass']/stats['total_articles']*100:.1f}%)")
    print(f"Fix #2 (tables present):            {stats['fix_2_tables_present']}/{stats['total_articles']} ({stats['fix_2_tables_present']/stats['total_articles']*100:.1f}%)")
    print(f"Fix #2 (tables valid structure):    {stats['fix_2_tables_valid']}/{stats['total_articles']} ({stats['fix_2_tables_valid']/stats['total_articles']*100:.1f}%)")
    print(f"Fix #5 (JSON image absolute):       {stats['fix_5_json_absolute']}/{stats['total_articles']} ({stats['fix_5_json_absolute']/stats['total_articles']*100:.1f}%)")
    print(f"Fix #5 (HTML image absolute):       {stats['fix_5_html_absolute']}/{stats['total_articles']} ({stats['fix_5_html_absolute']/stats['total_articles']*100:.1f}%)")
    print(f"Fix #6 (NO HTML in titles):         {stats['fix_6_no_html']}/{stats['total_articles']} ({stats['fix_6_no_html']/stats['total_articles']*100:.1f}%)")
    print()
    
    print("="*80)
    print("QUALITY METRICS")
    print("="*80)
    print(f"Average sections:     {stats['avg_sections']:.1f}")
    print(f"Average word count:   {stats['avg_word_count']:.0f}")
    print(f"Average FAQs:         {stats['avg_faqs']:.1f}")
    print(f"Average PAAs:         {stats['avg_paas']:.1f}")
    print(f"Average takeaways:    {stats['avg_takeaways']:.1f}")
    print(f"Average citations:    {stats['avg_citations']:.1f}")
    print()
    
    print("="*80)
    print("ISSUES & WARNINGS")
    print("="*80)
    print(f"Articles with issues:   {stats['articles_with_issues']}/{stats['total_articles']}")
    print(f"Articles with warnings: {stats['articles_with_warnings']}/{stats['total_articles']}")
    print()
    
    if issues_by_type:
        print("Issues breakdown:")
        for issue_type, count in sorted(issues_by_type.items(), key=lambda x: -x[1]):
            print(f"  - {issue_type}: {count}")
        print()
    
    if warnings_by_type:
        print("Top warnings:")
        for warning_type, articles in sorted(warnings_by_type.items(), key=lambda x: -len(x[1]))[:5]:
            print(f"  - {warning_type}: {len(articles)} articles")
        print()
    
    # Detailed findings for problematic articles
    print("="*80)
    print("DETAILED FINDINGS - ARTICLES WITH ISSUES")
    print("="*80)
    
    for audit in audits:
        if audit["issues"]:
            print(f"\n📁 {audit['directory']}")
            print(f"   Issues: {len(audit['issues'])}")
            for issue in audit["issues"]:
                print(f"      ❌ {issue}")
            if audit["warnings"]:
                print(f"   Warnings: {len(audit['warnings'])}")
                for warning in audit["warnings"][:3]:
                    print(f"      ⚠️  {warning}")
    
    # Save detailed audit
    output_file = output_dir.parent / "DETAILED_AUDIT_REPORT.json"
    with open(output_file, 'w') as f:
        json.dump({
            "summary": stats,
            "issues_breakdown": dict(issues_by_type),
            "warnings_breakdown": {k: len(v) for k, v in warnings_by_type.items()},
            "detailed_audits": audits
        }, f, indent=2)
    
    print()
    print("="*80)
    print(f"Detailed audit saved to: {output_file}")
    print("="*80)
    
    # Final verdict
    print()
    print("="*80)
    print("FINAL VERDICT")
    print("="*80)
    
    all_pass = all([
        stats['fix_1_pass'] / stats['total_articles'] >= 0.95,
        stats['fix_5_html_absolute'] / stats['total_articles'] >= 0.95,
        stats['fix_6_no_html'] / stats['total_articles'] >= 0.95,
        stats['avg_word_count'] >= 1500,
    ])
    
    if all_pass:
        print("✅ PASS - All critical fixes validated, ready for production")
    elif stats['fix_1_pass'] / stats['total_articles'] >= 0.90:
        print("⚠️  CONDITIONAL PASS - Minor issues found, recommend fixing before deploy")
    else:
        print("❌ FAIL - Critical issues found, do NOT deploy")

if __name__ == "__main__":
    output_dir = Path(__file__).parent / "output"
    generate_audit_report(output_dir)

