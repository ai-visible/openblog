"""
Proper Stage 2b Test - Using Real Stage 2 Output
Tests Stage 2b on actual Stage 2 output, not sample data.
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
from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage
from pipeline.blog_generation.stage_02b_quality_refinement import QualityRefinementStage
from pipeline.models.output_schema import ArticleOutput

def analyze_content_quality(content: str, label: str = "") -> dict:
    """Analyze content for quality issues."""
    if not content:
        return {}
    
    issues = {
        "em_dashes": content.count("—"),
        "en_dashes": content.count("–"),
        "academic_citations": content.count("[") if "[" in content and any(c.isdigit() for c in content) else 0,
        "robotic_phrases": sum(1 for phrase in ["furthermore", "moreover", "it's important to note", "leverage", "utilize", "seamlessly", "comprehensive", "robust"] if phrase.lower() in content.lower()),
        "orphaned_paragraphs": content.count("<p>This </p>") + content.count("<p>. Also,") + content.count("<p>This.</p>"),
        "word_count": len(content.split()),
        "paragraph_count": content.count("<p>"),
        "list_count": content.count("<ul>"),
        "citation_count": content.lower().count('according to') + content.lower().count('reports') + content.lower().count('research by'),
        "question_patterns": sum(1 for pattern in ['what is', 'how does', 'why does', 'when should', 'where can', 'how can', 'what are'] if pattern in content.lower()),
        "conversational_phrases": sum(1 for phrase in ['you can', "you'll", "here's", "let's", "this is", "when you", "if you"] if phrase in content.lower()),
    }
    
    return issues

async def test_stage2b_on_real_stage2():
    """Test Stage 2b on real Stage 2 output."""
    print("=" * 80)
    print("STAGE 2B TEST - USING REAL STAGE 2 OUTPUT")
    print("=" * 80)
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/stage2b_real_test_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create execution context
    context = ExecutionContext(
        job_id="test_stage2b_real",
        job_config={
            "primary_keyword": "cloud security best practices",
            "company_url": "https://scaile.tech",
            "word_count": 3000,
            "language": "en",
            "tone": "professional"
        },
        company_data={
            "company_url": "https://scaile.tech",
            "company_name": "Scaile",
            "industry": "Technology",
            "description": "Scaile is a technology company"
        }
    )
    
    # ============================================================
    # STAGE 1: Build Prompt
    # ============================================================
    print("📝 STAGE 1: Building prompt...")
    stage_1 = PromptBuildStage()
    context = await stage_1.execute(context)
    
    if not context.prompt:
        print("❌ Stage 1 failed - no prompt generated")
        return
    
    print(f"✅ Stage 1 complete (prompt length: {len(context.prompt)} chars)")
    print()
    
    # ============================================================
    # STAGE 2: Generate Content (Real Output)
    # ============================================================
    print("🚀 STAGE 2: Generating content with Gemini...")
    print("   (This will take 2-5 minutes with deep research)")
    print()
    
    stage_2 = GeminiCallStage()
    context = await stage_2.execute(context)
    
    if not context.raw_article:
        print("❌ Stage 2 failed - no raw_article generated")
        return
    
    print("✅ Stage 2 complete")
    print()
    
    # Parse raw_article JSON into ArticleOutput
    import json
    try:
        raw_json = json.loads(context.raw_article)
        article_before_2b = ArticleOutput(**raw_json)
        # Set structured_data for Stage 2b
        context.structured_data = article_before_2b
    except Exception as e:
        print(f"❌ Failed to parse Stage 2 output: {e}")
        return
    
    # ============================================================
    # BEFORE STAGE 2B: Analyze Stage 2 output
    # ============================================================
    print("📊 ANALYZING STAGE 2 OUTPUT (BEFORE STAGE 2B)...")
    print()
    before_analysis = {}
    all_before_content = ""
    
    content_fields = [
        'Intro', 'Direct_Answer', 'Teaser',
        'section_01_content', 'section_02_content', 'section_03_content',
        'section_04_content', 'section_05_content'
    ]
    
    for field in content_fields:
        content = getattr(article_before_2b, field, "")
        if content:
            content_str = str(content)
            all_before_content += " " + content_str
            before_analysis[field] = analyze_content_quality(content_str, f"BEFORE {field}")
    
    before_summary = analyze_content_quality(all_before_content, "BEFORE ALL")
    
    print("STAGE 2 OUTPUT - Issues Found:")
    print(f"  Em dashes: {before_summary.get('em_dashes', 0)}")
    print(f"  En dashes: {before_summary.get('en_dashes', 0)}")
    print(f"  Academic citations: {before_summary.get('academic_citations', 0)}")
    print(f"  Robotic phrases: {before_summary.get('robotic_phrases', 0)}")
    print(f"  Orphaned paragraphs: {before_summary.get('orphaned_paragraphs', 0)}")
    print(f"  Total word count: {before_summary.get('word_count', 0):,}")
    print(f"  Paragraphs: {before_summary.get('paragraph_count', 0)}")
    print(f"  Lists: {before_summary.get('list_count', 0)}")
    print(f"  Citations: {before_summary.get('citation_count', 0)}")
    print(f"  Question patterns: {before_summary.get('question_patterns', 0)}")
    print(f"  Conversational phrases: {before_summary.get('conversational_phrases', 0)}")
    print()
    
    # Save Stage 2 output
    stage2_file = output_dir / "stage2_output.json"
    with open(stage2_file, 'w') as f:
        json.dump(article_before_2b.model_dump(), f, indent=2, default=str)
    
    # ============================================================
    # STAGE 2B: Quality Refinement
    # ============================================================
    print("🔧 STAGE 2B: Running quality refinement...")
    print("   (This will take 1-3 minutes)")
    print()
    
    stage_2b = QualityRefinementStage()
    
    try:
        context_after_2b = await stage_2b.execute(context)
        print("✅ Stage 2b completed successfully")
        print()
    except Exception as e:
        print(f"❌ Stage 2b failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ============================================================
    # AFTER STAGE 2B: Analyze refined output
    # ============================================================
    print("📊 ANALYZING STAGE 2B OUTPUT (AFTER REFINEMENT)...")
    print()
    
    article_after_2b = context_after_2b.structured_data
    after_analysis = {}
    all_after_content = ""
    
    for field in content_fields:
        content = getattr(article_after_2b, field, "")
        if content:
            content_str = str(content)
            all_after_content += " " + content_str
            after_analysis[field] = analyze_content_quality(content_str, f"AFTER {field}")
    
    after_summary = analyze_content_quality(all_after_content, "AFTER ALL")
    
    print("STAGE 2B OUTPUT - Issues Found:")
    print(f"  Em dashes: {after_summary.get('em_dashes', 0)}")
    print(f"  En dashes: {after_summary.get('en_dashes', 0)}")
    print(f"  Academic citations: {after_summary.get('academic_citations', 0)}")
    print(f"  Robotic phrases: {after_summary.get('robotic_phrases', 0)}")
    print(f"  Orphaned paragraphs: {after_summary.get('orphaned_paragraphs', 0)}")
    print(f"  Total word count: {after_summary.get('word_count', 0):,}")
    print(f"  Paragraphs: {after_summary.get('paragraph_count', 0)}")
    print(f"  Lists: {after_summary.get('list_count', 0)}")
    print(f"  Citations: {after_summary.get('citation_count', 0)}")
    print(f"  Question patterns: {after_summary.get('question_patterns', 0)}")
    print(f"  Conversational phrases: {after_summary.get('conversational_phrases', 0)}")
    print()
    
    # Save Stage 2b output
    stage2b_file = output_dir / "stage2b_output.json"
    with open(stage2b_file, 'w') as f:
        json.dump(article_after_2b.model_dump(), f, indent=2, default=str)
    
    # ============================================================
    # COMPARISON
    # ============================================================
    print("=" * 80)
    print("STAGE 2 vs STAGE 2B COMPARISON")
    print("=" * 80)
    print()
    
    print("ISSUE FIXES:")
    print()
    
    issues_fixed = []
    issues_remaining = []
    
    # Em dashes
    before_em = before_summary.get('em_dashes', 0)
    after_em = after_summary.get('em_dashes', 0)
    if before_em > 0:
        if after_em == 0:
            issues_fixed.append(f"✅ Em dashes: {before_em} → 0")
        else:
            issues_remaining.append(f"⚠️  Em dashes: {before_em} → {after_em}")
    
    # En dashes
    before_en = before_summary.get('en_dashes', 0)
    after_en = after_summary.get('en_dashes', 0)
    if before_en > 0:
        if after_en == 0:
            issues_fixed.append(f"✅ En dashes: {before_en} → 0")
        else:
            issues_remaining.append(f"⚠️  En dashes: {before_en} → {after_en}")
    
    # Robotic phrases
    before_rp = before_summary.get('robotic_phrases', 0)
    after_rp = after_summary.get('robotic_phrases', 0)
    if before_rp > 0:
        if after_rp < before_rp:
            issues_fixed.append(f"✅ Robotic phrases: {before_rp} → {after_rp}")
        else:
            issues_remaining.append(f"⚠️  Robotic phrases: {before_rp} → {after_rp}")
    
    # Orphaned paragraphs
    before_op = before_summary.get('orphaned_paragraphs', 0)
    after_op = after_summary.get('orphaned_paragraphs', 0)
    if before_op > 0:
        if after_op == 0:
            issues_fixed.append(f"✅ Orphaned paragraphs: {before_op} → 0")
        else:
            issues_remaining.append(f"⚠️  Orphaned paragraphs: {before_op} → {after_op}")
    
    # AEO improvements
    before_citations = before_summary.get('citation_count', 0)
    after_citations = after_summary.get('citation_count', 0)
    if after_citations > before_citations:
        issues_fixed.append(f"✅ Citations: {before_citations} → {after_citations}")
    
    before_questions = before_summary.get('question_patterns', 0)
    after_questions = after_summary.get('question_patterns', 0)
    if after_questions > before_questions:
        issues_fixed.append(f"✅ Question patterns: {before_questions} → {after_questions}")
    
    before_phrases = before_summary.get('conversational_phrases', 0)
    after_phrases = after_summary.get('conversational_phrases', 0)
    if after_phrases > before_phrases:
        issues_fixed.append(f"✅ Conversational phrases: {before_phrases} → {after_phrases}")
    
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
    field_changes = {}
    for field in content_fields:
        before_content = str(getattr(article_before_2b, field, ""))
        after_content = str(getattr(article_after_2b, field, ""))
        
        if before_content != after_content:
            field_changes[field] = {
                "changed": True,
                "before_length": len(before_content),
                "after_length": len(after_content),
                "before_words": len(before_content.split()),
                "after_words": len(after_content.split()),
            }
            print(f"  ✅ {field}: Changed ({len(before_content)} → {len(after_content)} chars, {len(before_content.split())} → {len(after_content.split())} words)")
        else:
            print(f"  ℹ️  {field}: No changes")
    print()
    
    # Save comparison
    comparison_file = output_dir / "comparison.json"
    with open(comparison_file, 'w') as f:
        json.dump({
            "before_summary": before_summary,
            "after_summary": after_summary,
            "field_changes": field_changes,
            "issues_fixed": issues_fixed,
            "issues_remaining": issues_remaining
        }, f, indent=2, default=str)
    
    # Show sample field comparisons
    print("=" * 80)
    print("SAMPLE FIELD COMPARISONS")
    print("=" * 80)
    print()
    
    sample_fields = ['Intro', 'Direct_Answer', 'section_01_content']
    for field in sample_fields:
        if field in field_changes:
            before_content = str(getattr(article_before_2b, field, ""))
            after_content = str(getattr(article_after_2b, field, ""))
            
            print(f"\n{field}:")
            print("-" * 80)
            print(f"BEFORE ({len(before_content)} chars):")
            print(before_content[:500] + "..." if len(before_content) > 500 else before_content)
            print()
            print(f"AFTER ({len(after_content)} chars):")
            print(after_content[:500] + "..." if len(after_content) > 500 else after_content)
            print()
    
    print("=" * 80)
    print(f"✅ Test complete! Output saved to: {output_dir}")
    print("=" * 80)
    print()
    print("Files created:")
    print(f"  - {stage2_file.name}")
    print(f"  - {stage2b_file.name}")
    print(f"  - {comparison_file.name}")

if __name__ == "__main__":
    asyncio.run(test_stage2b_on_real_stage2())

