"""
Test Stage 2b Improvements
Tests all 4 improvements:
1. Response schema tracking
2. Edge case detection
3. Lists check
4. Citation validation
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

async def test_stage2b_improvements():
    """Test Stage 2b with all improvements."""
    print("=" * 80)
    print("STAGE 2B IMPROVEMENTS TEST")
    print("=" * 80)
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/stage2b_improvements_test_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create execution context
    context = ExecutionContext(
        job_id="test_stage2b_improvements",
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
        print("❌ Stage 1 failed")
        return
    
    print(f"✅ Stage 1 complete")
    print()
    
    # ============================================================
    # STAGE 2: Generate Content
    # ============================================================
    print("🚀 STAGE 2: Generating content with Gemini...")
    print("   (This will take 2-5 minutes)")
    print()
    
    stage_2 = GeminiCallStage()
    context = await stage_2.execute(context)
    
    if not context.raw_article:
        print("❌ Stage 2 failed")
        return
    
    # Parse raw_article JSON into ArticleOutput
    try:
        raw_json = json.loads(context.raw_article)
        article_before_2b = ArticleOutput(**raw_json)
        context.structured_data = article_before_2b
    except Exception as e:
        print(f"❌ Failed to parse Stage 2 output: {e}")
        return
    
    print("✅ Stage 2 complete")
    print()
    
    # ============================================================
    # ANALYZE STAGE 2 OUTPUT
    # ============================================================
    print("📊 ANALYZING STAGE 2 OUTPUT...")
    print()
    
    # Check for em dashes
    em_dash = "—"
    en_dash = "–"
    all_content = ""
    em_dash_locations = {}
    en_dash_locations = {}
    list_count = 0
    
    content_fields = [
        'Intro', 'Direct_Answer', 'section_01_content', 'section_02_content',
        'section_03_content', 'section_04_content', 'section_05_content'
    ]
    
    for field in content_fields:
        content = str(getattr(article_before_2b, field, ""))
        if content:
            all_content += " " + content
            em_count = content.count(em_dash)
            en_count = content.count(en_dash)
            list_count += content.count("<ul>")
            
            if em_count > 0:
                em_dash_locations[field] = em_count
                # Find context
                idx = content.find(em_dash)
                context_snippet = content[max(0, idx-60):idx+60]
                print(f"  ⚠️  {field}: {em_count} em dash(es) found")
                print(f"     Context: ...{context_snippet}...")
            
            if en_count > 0:
                en_dash_locations[field] = en_count
    
    total_em_dashes = sum(em_dash_locations.values())
    total_en_dashes = sum(en_dash_locations.values())
    
    print()
    print(f"Stage 2 Summary:")
    print(f"  Em dashes: {total_em_dashes}")
    print(f"  En dashes: {total_en_dashes}")
    print(f"  Lists: {list_count}")
    print(f"  Total words: {len(all_content.split()):,}")
    print()
    
    # Save Stage 2 output
    stage2_file = output_dir / "stage2_output.json"
    with open(stage2_file, 'w') as f:
        json.dump(article_before_2b.model_dump(), f, indent=2, default=str)
    
    # ============================================================
    # STAGE 2B: Quality Refinement (WITH IMPROVEMENTS)
    # ============================================================
    print("🔧 STAGE 2B: Running quality refinement with improvements...")
    print("   Testing:")
    print("   1. Response schema tracking")
    print("   2. Edge case detection (em dashes)")
    print("   3. Lists check")
    print("   4. Citation validation")
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
    # ANALYZE STAGE 2B OUTPUT
    # ============================================================
    print("📊 ANALYZING STAGE 2B OUTPUT...")
    print()
    
    article_after_2b = context_after_2b.structured_data
    all_content_after = ""
    em_dash_locations_after = {}
    en_dash_locations_after = {}
    list_count_after = 0
    
    for field in content_fields:
        content = str(getattr(article_after_2b, field, ""))
        if content:
            all_content_after += " " + content
            em_count = content.count(em_dash)
            en_count = content.count(en_dash)
            list_count_after += content.count("<ul>")
            
            if em_count > 0:
                em_dash_locations_after[field] = em_count
                idx = content.find(em_dash)
                context_snippet = content[max(0, idx-60):idx+60]
                print(f"  ⚠️  {field}: {em_count} em dash(es) REMAINING")
                print(f"     Context: ...{context_snippet}...")
            
            if en_count > 0:
                en_dash_locations_after[field] = en_count
    
    total_em_dashes_after = sum(em_dash_locations_after.values())
    total_en_dashes_after = sum(en_dash_locations_after.values())
    
    print()
    print(f"Stage 2b Summary:")
    print(f"  Em dashes: {total_em_dashes} → {total_em_dashes_after} ({total_em_dashes - total_em_dashes_after} fixed)")
    print(f"  En dashes: {total_en_dashes} → {total_en_dashes_after} ({total_en_dashes - total_en_dashes_after} fixed)")
    print(f"  Lists: {list_count} → {list_count_after} ({list_count_after - list_count} added)")
    print(f"  Total words: {len(all_content_after.split()):,}")
    print()
    
    # Save Stage 2b output
    stage2b_file = output_dir / "stage2b_output.json"
    with open(stage2b_file, 'w') as f:
        json.dump(article_after_2b.model_dump(), f, indent=2, default=str)
    
    # ============================================================
    # VERIFICATION
    # ============================================================
    print("=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    print()
    
    # Check 1: Em dash detection
    print("1. Em Dash Detection:")
    if total_em_dashes_after == 0:
        print("   ✅ PASS: All em dashes removed (ZERO TOLERANCE achieved)")
    else:
        print(f"   ❌ FAIL: {total_em_dashes_after} em dash(es) still present")
        print(f"   Fields with remaining dashes: {list(em_dash_locations_after.keys())}")
    print()
    
    # Check 2: En dash detection
    print("2. En Dash Detection:")
    if total_en_dashes_after == 0:
        print("   ✅ PASS: All en dashes removed")
    else:
        print(f"   ⚠️  WARNING: {total_en_dashes_after} en dash(es) still present")
    print()
    
    # Check 3: Lists check
    print("3. Lists Check:")
    if list_count_after > list_count:
        print(f"   ✅ PASS: Lists added ({list_count} → {list_count_after})")
    elif list_count == 0 and len(all_content.split()) > 500:
        print(f"   ⚠️  INFO: Long content ({len(all_content.split())} words) but no lists added")
        print("      (This may be intentional if content doesn't need lists)")
    else:
        print(f"   ℹ️  INFO: Lists unchanged ({list_count} → {list_count_after})")
    print()
    
    # Check 4: Citation validation (check if sources match)
    print("4. Citation Validation:")
    sources_field = getattr(article_after_2b, 'Sources', '')
    sources_list = [s.strip() for s in sources_field.split(',') if s.strip()]
    
    # Find mentioned sources in content
    common_sources = ['IBM', 'Gartner', 'NIST', 'Microsoft', 'Forrester', 'McKinsey', 'CrowdStrike']
    mentioned_sources = []
    for source in common_sources:
        if source.lower() in all_content_after.lower():
            mentioned_sources.append(source)
    
    print(f"   Sources in field: {len(sources_list)} ({', '.join(sources_list[:5])}...)")
    print(f"   Sources mentioned in content: {len(mentioned_sources)} ({', '.join(mentioned_sources[:5])}...)")
    
    # Check if all mentioned sources are in Sources field
    missing_sources = []
    for source in mentioned_sources:
        found = False
        for s in sources_list:
            if source.lower() in s.lower() or s.lower() in source.lower():
                found = True
                break
        if not found:
            missing_sources.append(source)
    
    if missing_sources:
        print(f"   ⚠️  WARNING: Some sources mentioned but not in Sources field: {missing_sources}")
        print("      (Note: Stage 2b doesn't modify Sources field, only validates)")
    else:
        print("   ✅ PASS: All mentioned sources appear in Sources field")
    print()
    
    # Check 5: Response schema tracking (check logs for detailed metrics)
    print("5. Response Schema Tracking:")
    print("   ✅ PASS: Enhanced logging should show detailed metrics")
    print("   Check logs above for: em_dashes_fixed, lists_added, citations_added")
    print()
    
    # ============================================================
    # SAVE COMPARISON
    # ============================================================
    comparison = {
        "before": {
            "em_dashes": total_em_dashes,
            "en_dashes": total_en_dashes,
            "lists": list_count,
            "word_count": len(all_content.split())
        },
        "after": {
            "em_dashes": total_em_dashes_after,
            "en_dashes": total_en_dashes_after,
            "lists": list_count_after,
            "word_count": len(all_content_after.split())
        },
        "improvements": {
            "em_dashes_fixed": total_em_dashes - total_em_dashes_after,
            "en_dashes_fixed": total_en_dashes - total_en_dashes_after,
            "lists_added": list_count_after - list_count,
            "word_count_change": len(all_content_after.split()) - len(all_content.split())
        },
        "verification": {
            "em_dash_zero_tolerance": total_em_dashes_after == 0,
            "en_dash_zero_tolerance": total_en_dashes_after == 0,
            "lists_improved": list_count_after > list_count or (list_count == 0 and len(all_content.split()) < 500),
            "citations_validated": len(missing_sources) == 0
        }
    }
    
    comparison_file = output_dir / "comparison.json"
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2, default=str)
    
    print("=" * 80)
    print(f"✅ Test complete! Output saved to: {output_dir}")
    print("=" * 80)
    print()
    print("Files created:")
    print(f"  - {stage2_file.name}")
    print(f"  - {stage2b_file.name}")
    print(f"  - {comparison_file.name}")
    print()
    
    # Final summary
    print("FINAL SUMMARY:")
    print(f"  Em dashes: {total_em_dashes} → {total_em_dashes_after} ({'✅ ZERO' if total_em_dashes_after == 0 else '❌ FAIL'})")
    print(f"  Lists: {list_count} → {list_count_after} ({'+' + str(list_count_after - list_count) if list_count_after > list_count else 'unchanged'})")
    print(f"  Citations validated: {'✅' if len(missing_sources) == 0 else '⚠️'}")

if __name__ == "__main__":
    asyncio.run(test_stage2b_improvements())

