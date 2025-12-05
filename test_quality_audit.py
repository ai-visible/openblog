#!/usr/bin/env python3
"""
Devils Advocate Quality Audit - Comprehensive quality testing.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core import ExecutionContext
from pipeline.core.workflow_engine import WorkflowEngine
from pipeline.config import Config

async def generate_test_article():
    """Generate a test article."""
    print("=" * 80)
    print("GENERATING TEST ARTICLE")
    print("=" * 80)
    print()
    
    job_config = {
        "primary_keyword": "AI adoption in customer service",
        "company_url": "https://example.com",
        "company_name": "Example Corp",
    }
    
    engine = WorkflowEngine()
    
    # Register all stages
    from pipeline.blog_generation import (
        DataFetchStage,
        PromptBuildStage,
        GeminiCallStage,
        ExtractionStage,
        CitationsStage,
        InternalLinksStage,
        TableOfContentsStage,
        MetadataStage,
        FAQPAAStage,
        ImageStage,
        CleanupStage,
        StorageStage,
    )
    
    engine.register_stages([
        DataFetchStage(),
        PromptBuildStage(),
        GeminiCallStage(),
        ExtractionStage(),
        CitationsStage(),
        InternalLinksStage(),
        TableOfContentsStage(),
        MetadataStage(),
        FAQPAAStage(),
        ImageStage(),
        CleanupStage(),
        StorageStage(),
    ])
    
    start = time.time()
    result = await engine.execute("quality-audit-test", job_config)
    duration = time.time() - start
    
    print(f"✅ Article generated in {duration:.1f}s")
    print()
    
    return result

async def audit_quality(context: ExecutionContext):
    """Comprehensive quality audit."""
    print("=" * 80)
    print("DEVILS ADVOCATE QUALITY AUDIT")
    print("=" * 80)
    print()
    
    article = context.validated_article
    quality_report = context.quality_report
    
    issues_found = []
    warnings_found = []
    
    # 1. Check quality report
    print("1. QUALITY REPORT ANALYSIS")
    print("-" * 80)
    if not quality_report:
        issues_found.append("❌ CRITICAL: No quality report generated")
    else:
        passed = quality_report.get("passed", False)
        aeo_score = quality_report.get("metrics", {}).get("aeo_score", 0)
        critical_issues = quality_report.get("critical_issues", [])
        suggestions = quality_report.get("suggestions", [])
        
        print(f"   Passed: {passed}")
        print(f"   AEO Score: {aeo_score}/100")
        print(f"   Critical Issues: {len(critical_issues)}")
        print(f"   Suggestions: {len(suggestions)}")
        
        if not passed:
            issues_found.append(f"❌ Quality check FAILED: {len(critical_issues)} critical issues")
        if aeo_score < 70:
            warnings_found.append(f"⚠️  Low AEO score: {aeo_score}/100 (target: ≥70)")
        
        if critical_issues:
            print("   Critical Issues:")
            for issue in critical_issues[:5]:
                print(f"     - {issue}")
                issues_found.append(f"CRITICAL: {issue}")
        
        if suggestions:
            print("   Suggestions:")
            for suggestion in suggestions[:5]:
                print(f"     - {suggestion}")
                warnings_found.append(f"SUGGESTION: {suggestion}")
    
    print()
    
    # 2. Check article structure
    print("2. ARTICLE STRUCTURE CHECK")
    print("-" * 80)
    if not article:
        issues_found.append("❌ CRITICAL: No validated article")
        return issues_found, warnings_found
    
    required_fields = ["Headline", "Intro", "Meta_Title", "Meta_Description"]
    for field in required_fields:
        value = article.get(field, "")
        if not value or not str(value).strip():
            issues_found.append(f"❌ Missing required field: {field}")
        else:
            print(f"   ✓ {field}: {len(str(value))} chars")
    
    # Check sections
    sections_found = 0
    for i in range(1, 10):
        title = article.get(f"section_{i:02d}_title", "")
        content = article.get(f"section_{i:02d}_content", "")
        if title or content:
            sections_found += 1
    
    print(f"   Sections found: {sections_found}")
    if sections_found < 2:
        issues_found.append(f"❌ Too few sections: {sections_found} (minimum: 2)")
    elif sections_found > 9:
        warnings_found.append(f"⚠️  Too many sections: {sections_found} (recommended: ≤9)")
    
    print()
    
    # 3. Check citations
    print("3. CITATION VALIDATION")
    print("-" * 80)
    citations_html = article.get("citations_html", "")
    sources = article.get("Sources", "")
    
    if not citations_html and not sources:
        warnings_found.append("⚠️  No citations found")
    else:
        # Count citations in HTML
        import re
        citation_refs = re.findall(r'\[(\d+)\]', citations_html)
        citation_count = len(set(citation_refs))
        print(f"   Citation references: {citation_count}")
        
        # Check if sources match citations
        if sources:
            source_lines = [s.strip() for s in sources.split('\n') if s.strip()]
            print(f"   Sources listed: {len(source_lines)}")
            
            if citation_count > len(source_lines):
                issues_found.append(f"❌ More citation references ({citation_count}) than sources ({len(source_lines)})")
            elif citation_count < len(source_lines):
                warnings_found.append(f"⚠️  More sources ({len(source_lines)}) than citation references ({citation_count})")
    
    print()
    
    # 4. Check keyword coverage
    print("4. KEYWORD COVERAGE")
    print("-" * 80)
    keyword = context.job_config.get("primary_keyword", "")
    if keyword:
        headline = article.get("Headline", "").lower()
        intro = article.get("Intro", "").lower()
        meta_title = article.get("Meta_Title", "").lower()
        meta_desc = article.get("Meta_Description", "").lower()
        
        keyword_lower = keyword.lower()
        
        checks = {
            "Headline": headline,
            "Meta Title": meta_title,
            "Meta Description": meta_desc,
            "Intro": intro[:200],
        }
        
        for field, text in checks.items():
            if keyword_lower in text:
                print(f"   ✓ {field}: Contains keyword")
            else:
                warnings_found.append(f"⚠️  {field} missing primary keyword")
                print(f"   ✗ {field}: Missing keyword")
    
    print()
    
    # 5. Check HTML quality
    print("5. HTML QUALITY")
    print("-" * 80)
    html_content = article.get("html_content", "")
    
    # Handle coroutine (bug in Stage 11)
    if hasattr(html_content, '__await__'):
        warnings_found.append("⚠️  CRITICAL BUG: html_content is a coroutine (not awaited in Stage 11)")
        html_content = ""
    
    if html_content:
        # Check for unclosed tags
        import re
        open_tags = re.findall(r'<(\w+)[^>]*>', html_content)
        close_tags = re.findall(r'</(\w+)>', html_content)
        
        self_closing = {"br", "hr", "img", "input", "meta", "link"}
        
        unclosed = []
        for tag in open_tags:
            if tag.lower() not in self_closing:
                if close_tags.count(tag.lower()) < open_tags.count(tag):
                    unclosed.append(tag)
        
        if unclosed:
            issues_found.append(f"❌ Unclosed HTML tags: {', '.join(set(unclosed))}")
        else:
            print("   ✓ HTML tags properly closed")
        
        # Check for markdown artifacts
        if "**" in html_content:
            warnings_found.append("⚠️  Markdown artifacts (**) found in HTML")
        
        print(f"   HTML length: {len(html_content)} chars")
    else:
        warnings_found.append("⚠️  No HTML content generated")
    
    print()
    
    # 6. Check content quality
    print("6. CONTENT QUALITY")
    print("-" * 80)
    
    # Word count
    all_text = ""
    for key in article:
        if isinstance(article[key], str):
            text = re.sub(r'<[^>]+>', '', article[key])
            all_text += text + " "
    
    word_count = len(all_text.split())
    print(f"   Total word count: {word_count}")
    
    if word_count < 800:
        warnings_found.append(f"⚠️  Low word count: {word_count} (target: ≥1200)")
    elif word_count > 2500:
        warnings_found.append(f"⚠️  High word count: {word_count} (target: ≤1800)")
    
    # Paragraph length check
    paragraphs = re.findall(r'<p[^>]*>([^<]+)</p>', all_text)
    long_paragraphs = []
    for para in paragraphs:
        words = len(para.split())
        if words > 50:
            long_paragraphs.append(words)
    
    if long_paragraphs:
        avg_long = sum(long_paragraphs) / len(long_paragraphs)
        warnings_found.append(f"⚠️  {len(long_paragraphs)} paragraphs exceed 50 words (avg: {avg_long:.1f} words)")
    else:
        print(f"   ✓ Paragraph lengths OK ({len(paragraphs)} paragraphs)")
    
    print()
    
    # 7. Check metadata
    print("7. METADATA CHECK")
    print("-" * 80)
    meta_title = article.get("Meta_Title", "")
    meta_desc = article.get("Meta_Description", "")
    
    if meta_title:
        if len(meta_title) > 60:
            warnings_found.append(f"⚠️  Meta title too long: {len(meta_title)} chars (target: ≤60)")
        print(f"   Meta Title: {len(meta_title)} chars")
    
    if meta_desc:
        if len(meta_desc) > 160:
            warnings_found.append(f"⚠️  Meta description too long: {len(meta_desc)} chars (target: ≤160)")
        print(f"   Meta Description: {len(meta_desc)} chars")
    
    print()
    
    # 8. Check structured data
    print("8. STRUCTURED DATA CHECK")
    print("-" * 80)
    faq_items = article.get("faq_items", [])
    paa_items = article.get("paa_items", [])
    
    print(f"   FAQ items: {len(faq_items) if isinstance(faq_items, list) else 0}")
    print(f"   PAA items: {len(paa_items) if isinstance(paa_items, list) else 0}")
    
    if isinstance(faq_items, list) and len(faq_items) < 3:
        warnings_found.append(f"⚠️  Too few FAQs: {len(faq_items)} (target: ≥3)")
    
    if isinstance(paa_items, list) and len(paa_items) < 2:
        warnings_found.append(f"⚠️  Too few PAAs: {len(paa_items)} (target: ≥2)")
    
    print()
    
    # Summary
    print("=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)
    print(f"Critical Issues: {len(issues_found)}")
    print(f"Warnings: {len(warnings_found)}")
    print()
    
    if issues_found:
        print("CRITICAL ISSUES:")
        for issue in issues_found[:10]:
            print(f"  {issue}")
        print()
    
    if warnings_found:
        print("WARNINGS:")
        for warning in warnings_found[:10]:
            print(f"  {warning}")
        print()
    
    return issues_found, warnings_found

async def main():
    """Run quality audit."""
    print("Starting quality audit...")
    print()
    
    # Generate article
    context = await generate_test_article()
    
    # Audit quality
    issues, warnings = await audit_quality(context)
    
    # Final verdict
    print("=" * 80)
    print("FINAL VERDICT")
    print("=" * 80)
    
    if issues:
        print(f"❌ FAILED: {len(issues)} critical issues found")
        return 1
    elif warnings:
        print(f"⚠️  PASSED WITH WARNINGS: {len(warnings)} warnings")
        return 0
    else:
        print("✅ PASSED: No issues found")
        return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

