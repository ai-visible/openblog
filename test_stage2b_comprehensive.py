"""
Comprehensive Stage 2b Test - Before/After Comparison
Tests Stage 2b after all regex removal and AI-only fixes.
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

from pipeline.core.execution_context import ExecutionContext
from pipeline.core.company_context import CompanyContext
from pipeline.blog_generation.stage_02b_quality_refinement import QualityRefinementStage
from pipeline.models.output_schema import ArticleOutput

# Sample article with known issues (to test Stage 2b fixes)
SAMPLE_ARTICLE_WITH_ISSUES = {
    "Headline": "Cloud Security Best Practices 2025",
    "Subtitle": "Enterprise Guide to Zero Trust",
    "Teaser": "Learn how to secure your cloud infrastructure with modern best practices.",
    "Direct_Answer": "Cloud security involves protecting data, applications, and infrastructure in cloud environments. According to IBM, organizations should implement zero trust architecture.",
    "Intro": "<p>Cloud security is crucial for modern enterprises. Organizations must protect their data and applications.</p>",
    "Meta_Title": "Cloud Security Best Practices 2025",
    "Meta_Description": "Learn cloud security best practices for 2025.",
    "section_01_title": "What is Cloud Security?",
    "section_01_content": "<p>Cloud security involves protecting data—organizations must implement robust measures. Here are key points:</p><ul><li>Data encryption</li><li>Access controls</li><li>Monitoring</li></ul><p>According to Gartner research, cloud security is evolving rapidly.</p>",
    "section_02_title": "Best Practices",
    "section_02_content": "<p>Implementing cloud security requires a comprehensive approach. Furthermore, organizations should leverage modern tools. It's important to note that security is not optional.</p><p>Here are key points:</p><ul><li>Multi-factor authentication</li><li>Regular audits</li><li>Incident response plans</li></ul>",
    "section_03_title": "Zero Trust Architecture",
    "section_03_content": "<p>Zero trust is a security model that assumes no trust. Organizations must verify everything.</p><p>This </p><p>. Also, the implementation requires careful planning.</p>",
    "section_04_title": "Conclusion",
    "section_04_content": "<p>Cloud security is essential for modern enterprises. Organizations must stay vigilant.</p>",
    "Sources": "IBM, Gartner, Microsoft",
    "PAA": [],
    "FAQ": [],
    "Key_Takeaways": [],
    "image_01_url": "https://images.unsplash.com/photo-1563013544-824ae1b704d3",
    "image_01_alt_text": "Cloud security illustration",
    "image_01_credit": "Unsplash"
}

def analyze_content_quality(content: str, label: str = "") -> dict:
    """Analyze content for quality issues."""
    if not content:
        return {}
    
    issues = {
        "em_dashes": content.count("—"),
        "en_dashes": content.count("–"),
        "academic_citations": content.count("[") if "[" in content and any(c.isdigit() for c in content) else 0,
        "robotic_phrases": sum(1 for phrase in ["furthermore", "moreover", "it's important to note", "leverage", "utilize"] if phrase.lower() in content.lower()),
        "orphaned_paragraphs": content.count("<p>This </p>") + content.count("<p>. Also,"),
        "malformed_html": content.count("</p>") != content.count("<p>") if content.count("<p>") > 0 else False,
        "word_count": len(content.split()),
        "paragraph_count": content.count("<p>"),
        "list_count": content.count("<ul>"),
    }
    
    return issues

async def test_stage2b_comprehensive():
    """Test Stage 2b comprehensively with before/after comparison."""
    print("=" * 80)
    print("STAGE 2B COMPREHENSIVE TEST - BEFORE/AFTER COMPARISON")
    print("=" * 80)
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/stage2b_test_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create execution context with sample article (with issues)
    context = ExecutionContext(
        job_id="test_stage2b",
        job_config={
            "primary_keyword": "cloud security best practices",
            "company_url": "https://scaile.tech",
            "word_count": 3000,
            "language": "en",
            "tone": "professional"
        }
    )
    
    # Create ArticleOutput from sample
    article_output = ArticleOutput(**SAMPLE_ARTICLE_WITH_ISSUES)
    context.structured_data = article_output
    
    # ============================================================
    # BEFORE: Analyze content before Stage 2b
    # ============================================================
    print("📊 ANALYZING BEFORE STAGE 2B...")
    print()
    
    before_analysis = {}
    all_before_content = ""
    
    content_fields = [
        'Intro', 'Direct_Answer', 'Teaser',
        'section_01_content', 'section_02_content', 'section_03_content', 'section_04_content'
    ]
    
    for field in content_fields:
        content = getattr(article_output, field, "")
        if content:
            all_before_content += " " + str(content)
            before_analysis[field] = analyze_content_quality(str(content), f"BEFORE {field}")
    
    before_summary = analyze_content_quality(all_before_content, "BEFORE ALL")
    
    print("BEFORE STAGE 2B - Issues Found:")
    print(f"  Em dashes: {before_summary.get('em_dashes', 0)}")
    print(f"  En dashes: {before_summary.get('en_dashes', 0)}")
    print(f"  Academic citations: {before_summary.get('academic_citations', 0)}")
    print(f"  Robotic phrases: {before_summary.get('robotic_phrases', 0)}")
    print(f"  Orphaned paragraphs: {before_summary.get('orphaned_paragraphs', 0)}")
    print(f"  Malformed HTML: {before_summary.get('malformed_html', False)}")
    print(f"  Total word count: {before_summary.get('word_count', 0)}")
    print(f"  Paragraphs: {before_summary.get('paragraph_count', 0)}")
    print(f"  Lists: {before_summary.get('list_count', 0)}")
    print()
    
    # Save before state
    before_file = output_dir / "before_stage2b.json"
    with open(before_file, 'w') as f:
        json.dump({
            "article": article_output.dict(),
            "analysis": before_analysis,
            "summary": before_summary
        }, f, indent=2, default=str)
    
    # ============================================================
    # RUN STAGE 2B
    # ============================================================
    print("🚀 RUNNING STAGE 2B...")
    print()
    
    stage_2b = QualityRefinementStage()
    
    try:
        context_after = await stage_2b.execute(context)
        print("✅ Stage 2b completed successfully")
        print()
    except Exception as e:
        print(f"❌ Stage 2b failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ============================================================
    # AFTER: Analyze content after Stage 2b
    # ============================================================
    print("📊 ANALYZING AFTER STAGE 2B...")
    print()
    
    article_after = context_after.structured_data
    after_analysis = {}
    all_after_content = ""
    
    for field in content_fields:
        content = getattr(article_after, field, "")
        if content:
            all_after_content += " " + str(content)
            after_analysis[field] = analyze_content_quality(str(content), f"AFTER {field}")
    
    after_summary = analyze_content_quality(all_after_content, "AFTER ALL")
    
    print("AFTER STAGE 2B - Issues Found:")
    print(f"  Em dashes: {after_summary.get('em_dashes', 0)}")
    print(f"  En dashes: {after_summary.get('en_dashes', 0)}")
    print(f"  Academic citations: {after_summary.get('academic_citations', 0)}")
    print(f"  Robotic phrases: {after_summary.get('robotic_phrases', 0)}")
    print(f"  Orphaned paragraphs: {after_summary.get('orphaned_paragraphs', 0)}")
    print(f"  Malformed HTML: {after_summary.get('malformed_html', False)}")
    print(f"  Total word count: {after_summary.get('word_count', 0)}")
    print(f"  Paragraphs: {after_summary.get('paragraph_count', 0)}")
    print(f"  Lists: {after_summary.get('list_count', 0)}")
    print()
    
    # Save after state
    after_file = output_dir / "after_stage2b.json"
    with open(after_file, 'w') as f:
        json.dump({
            "article": article_after.dict(),
            "analysis": after_analysis,
            "summary": after_summary
        }, f, indent=2, default=str)
    
    # ============================================================
    # COMPARISON
    # ============================================================
    print("=" * 80)
    print("BEFORE vs AFTER COMPARISON")
    print("=" * 80)
    print()
    
    comparison = {}
    
    for field in content_fields:
        before_content = str(getattr(article_output, field, ""))
        after_content = str(getattr(article_after, field, ""))
        
        if before_content != after_content:
            comparison[field] = {
                "changed": True,
                "before_length": len(before_content),
                "after_length": len(after_content),
                "before": before_content[:200] + "..." if len(before_content) > 200 else before_content,
                "after": after_content[:200] + "..." if len(after_content) > 200 else after_content,
            }
        else:
            comparison[field] = {
                "changed": False,
                "length": len(before_content)
            }
    
    # Issue comparison
    print("ISSUE FIXES:")
    print()
    
    issues_fixed = []
    issues_remaining = []
    
    # Em dashes
    if before_summary.get('em_dashes', 0) > 0:
        if after_summary.get('em_dashes', 0) == 0:
            issues_fixed.append(f"✅ Em dashes: {before_summary.get('em_dashes', 0)} → 0")
        else:
            issues_remaining.append(f"⚠️  Em dashes: {before_summary.get('em_dashes', 0)} → {after_summary.get('em_dashes', 0)}")
    
    # En dashes
    if before_summary.get('en_dashes', 0) > 0:
        if after_summary.get('en_dashes', 0) == 0:
            issues_fixed.append(f"✅ En dashes: {before_summary.get('en_dashes', 0)} → 0")
        else:
            issues_remaining.append(f"⚠️  En dashes: {before_summary.get('en_dashes', 0)} → {after_summary.get('en_dashes', 0)}")
    
    # Academic citations
    if before_summary.get('academic_citations', 0) > 0:
        if after_summary.get('academic_citations', 0) == 0:
            issues_fixed.append(f"✅ Academic citations: {before_summary.get('academic_citations', 0)} → 0")
        else:
            issues_remaining.append(f"⚠️  Academic citations: {before_summary.get('academic_citations', 0)} → {after_summary.get('academic_citations', 0)}")
    
    # Robotic phrases
    if before_summary.get('robotic_phrases', 0) > 0:
        if after_summary.get('robotic_phrases', 0) < before_summary.get('robotic_phrases', 0):
            issues_fixed.append(f"✅ Robotic phrases: {before_summary.get('robotic_phrases', 0)} → {after_summary.get('robotic_phrases', 0)}")
        else:
            issues_remaining.append(f"⚠️  Robotic phrases: {before_summary.get('robotic_phrases', 0)} → {after_summary.get('robotic_phrases', 0)}")
    
    # Orphaned paragraphs
    if before_summary.get('orphaned_paragraphs', 0) > 0:
        if after_summary.get('orphaned_paragraphs', 0) == 0:
            issues_fixed.append(f"✅ Orphaned paragraphs: {before_summary.get('orphaned_paragraphs', 0)} → 0")
        else:
            issues_remaining.append(f"⚠️  Orphaned paragraphs: {before_summary.get('orphaned_paragraphs', 0)} → {after_summary.get('orphaned_paragraphs', 0)}")
    
    # Malformed HTML
    if before_summary.get('malformed_html', False):
        if not after_summary.get('malformed_html', False):
            issues_fixed.append("✅ Malformed HTML: Fixed")
        else:
            issues_remaining.append("⚠️  Malformed HTML: Still present")
    
    if issues_fixed:
        print("FIXED:")
        for fix in issues_fixed:
            print(f"  {fix}")
        print()
    
    if issues_remaining:
        print("REMAINING:")
        for issue in issues_remaining:
            print(f"  {issue}")
        print()
    
    # Field-by-field comparison
    print("FIELD CHANGES:")
    print()
    for field, comp in comparison.items():
        if comp.get("changed"):
            print(f"  ✅ {field}: Changed ({comp['before_length']} → {comp['after_length']} chars)")
        else:
            print(f"  ℹ️  {field}: No changes")
    print()
    
    # Save comparison
    comparison_file = output_dir / "comparison.json"
    with open(comparison_file, 'w') as f:
        json.dump({
            "before_summary": before_summary,
            "after_summary": after_summary,
            "field_comparison": comparison,
            "issues_fixed": issues_fixed,
            "issues_remaining": issues_remaining
        }, f, indent=2, default=str)
    
    # Save full article outputs
    before_full = output_dir / "before_full_article.json"
    with open(before_full, 'w') as f:
        json.dump(article_output.dict(), f, indent=2, default=str)
    
    after_full = output_dir / "after_full_article.json"
    with open(after_full, 'w') as f:
        json.dump(article_after.dict(), f, indent=2, default=str)
    
    print("=" * 80)
    print(f"✅ Test complete! Output saved to: {output_dir}")
    print("=" * 80)
    print()
    print("Files created:")
    print(f"  - {before_file.name}")
    print(f"  - {after_file.name}")
    print(f"  - {comparison_file.name}")
    print(f"  - {before_full.name}")
    print(f"  - {after_full.name}")

if __name__ == "__main__":
    asyncio.run(test_stage2b_comprehensive())

