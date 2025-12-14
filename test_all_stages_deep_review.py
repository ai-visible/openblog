#!/usr/bin/env python3
"""
Comprehensive Deep Review: ALL Pipeline Stages

Captures and analyzes pure outputs from EVERY stage:
- Stage 0: Data Fetch
- Stage 1: Prompt Build
- Stage 2: Gemini Content Generation
- Stage 3: Structured Data Extraction
- Stage 2b: Quality Refinement
- Stage 4: Citations
- Stage 5: Internal Links
- Stage 6: Table of Contents
- Stage 7: Metadata
- Stage 8: FAQ/PAA
- Stage 9: Image Generation
- Stage 10: Cleanup
- Stage 11: Storage
- Stage 12: Similarity Check
- Stage 13: Review Iteration

For each stage, we'll:
1. Capture the pure output
2. Analyze content quality
3. Compare before/after
4. Identify what each stage changes
"""

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core.execution_context import ExecutionContext
from pipeline.core.workflow_engine import WorkflowEngine
from pipeline.core.stage_factory import create_production_pipeline_stages


def extract_content_snapshot(context: ExecutionContext, stage_num: int, stage_name: str) -> Dict[str, Any]:
    """Extract a snapshot of content after a stage."""
    snapshot = {
        "stage_num": stage_num,
        "stage_name": stage_name,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Get structured data if available
    if context.structured_data:
        data = context.structured_data
        if hasattr(data, 'model_dump'):
            article_dict = data.model_dump()
        elif hasattr(data, 'dict'):
            article_dict = data.dict()
        elif isinstance(data, dict):
            article_dict = data
        else:
            article_dict = {}
        
        # Extract key content fields
        snapshot["content"] = {
            "headline": article_dict.get("Headline", ""),
            "intro": article_dict.get("Intro", ""),
            "section_01_title": article_dict.get("section_01_title", ""),
            "section_01_content": article_dict.get("section_01_content", ""),
            "section_02_title": article_dict.get("section_02_title", ""),
            "section_02_content": article_dict.get("section_02_content", ""),
            "section_04_content": article_dict.get("section_04_content", ""),
            "section_06_content": article_dict.get("section_06_content", ""),
            "sources": article_dict.get("Sources", ""),
        }
    
    # Get raw article if available
    if context.raw_article:
        snapshot["has_raw_article"] = True
        if isinstance(context.raw_article, str):
            try:
                snapshot["raw_article_preview"] = json.loads(context.raw_article)
            except:
                snapshot["raw_article_preview"] = str(context.raw_article)[:500]
        else:
            snapshot["raw_article_preview"] = str(context.raw_article)[:500]
    
    # Get parallel results if available
    if hasattr(context, 'parallel_results') and context.parallel_results:
        snapshot["parallel_results"] = {}
        for key in ['citations_html', 'internal_links_html', 'toc_html', 'metadata_html', 'faq_html', 'paa_html']:
            if key in context.parallel_results:
                snapshot["parallel_results"][key] = str(context.parallel_results[key])[:1000]
    
    # Get validated article if available
    if hasattr(context, 'validated_article') and context.validated_article:
        snapshot["has_validated_article"] = True
    
    return snapshot


def analyze_content_quality(content: str, stage_name: str) -> Dict[str, Any]:
    """Deep analysis of content quality."""
    if not content:
        return {"empty": True}
    
    analysis = {
        "stage": stage_name,
        "length": len(content),
        "word_count": len(content.split()),
        "paragraphs": content.count('<p>'),
        "lists": {
            "bullet": content.count('<ul>'),
            "numbered": content.count('<ol>'),
            "items": content.count('<li>'),
        },
        "citations": {
            "as_links": len(re.findall(r'<a[^>]*class="citation"[^>]*>', content)),
            "as_strong": len(re.findall(r'<strong>[^<]*(?:report|study|research|data|analysis)[^<]*</strong>', content, re.I)),
            "total_strong_tags": content.count('<strong>'),
        },
        "issues": {
            "em_dashes": len(re.findall(r'—', content)),
            "en_dashes": len(re.findall(r'–', content)),
            "academic_citations": len(re.findall(r'\[\d+\]', content)),
            "br_tags": content.count('<br><br>'),
            "malformed_html": len(re.findall(r'</p>\s*[A-Z][a-z]+\s+(reports?|notes?|finds?)', content)),
        },
        "html_structure": {
            "unclosed_tags": content.count('<p>') - content.count('</p>'),
            "nested_lists": len(re.findall(r'<ul>.*?<ul>', content, re.DOTALL)),
            "lists_in_paragraphs": len(re.findall(r'<p>.*?<ul>', content, re.DOTALL)),
        }
    }
    
    return analysis


async def run_comprehensive_stage_review():
    """Run pipeline and capture outputs from ALL stages."""
    
    # Ensure detailed prompt
    os.environ["STAGE2_PROMPT_STYLE"] = "detailed"
    
    print("=" * 80)
    print("COMPREHENSIVE DEEP REVIEW: ALL PIPELINE STAGES")
    print("=" * 80)
    print("\nUsing DETAILED prompt style")
    print()
    
    # Test config
    test_config = {
        "primary_keyword": "cloud security best practices",
        "company_url": "https://example.com",
        "word_count": 2000,
        "language": "en"
    }
    
    company_data = {
        "company_name": "Test Company",
        "company_url": "https://example.com",
        "author_name": "Test Author"
    }
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/all_stages_review_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize engine
    engine = WorkflowEngine()
    stages = create_production_pipeline_stages()
    engine.register_stages(stages)
    
    # Create job config
    job_config = {**test_config, **{"company_data": company_data}}
    job_id = f"all-stages-review-{timestamp}"
    
    all_stage_outputs = {}
    
    print("Running pipeline with stage-by-stage capture...")
    print()
    
    # Custom progress callback to capture stage outputs
    def progress_callback(stage_id, stage_name, completed):
        if completed:
            snapshot = extract_content_snapshot(context, int(stage_id) if stage_id.isdigit() else 0, stage_name)
            all_stage_outputs[f"stage_{stage_id}"] = snapshot
    
    try:
        # Stage 0: Data Fetch
        print("=" * 80)
        print("STAGE 0: Data Fetch & Auto-Detection")
        print("=" * 80)
        context = await stages[0].execute(ExecutionContext(job_id=job_id, job_config=job_config))
        snapshot = extract_content_snapshot(context, 0, "Data Fetch")
        all_stage_outputs["stage_0"] = snapshot
        print(f"✅ Stage 0 completed")
        print(f"   Company: {snapshot.get('content', {}).get('headline', 'N/A')}")
        
        # Stage 1: Prompt Build
        print("\n" + "=" * 80)
        print("STAGE 1: Prompt Construction")
        print("=" * 80)
        context = await stages[1].execute(context)
        snapshot = extract_content_snapshot(context, 1, "Prompt Build")
        all_stage_outputs["stage_1"] = snapshot
        print(f"✅ Stage 1 completed")
        print(f"   Prompt length: {len(context.prompt) if hasattr(context, 'prompt') and context.prompt else 'N/A'}")
        
        # Stage 2: Gemini Call
        print("\n" + "=" * 80)
        print("STAGE 2: Gemini Content Generation")
        print("=" * 80)
        context = await stages[2].execute(context)
        snapshot = extract_content_snapshot(context, 2, "Gemini Generation")
        all_stage_outputs["stage_2"] = snapshot
        
        # Analyze Stage 2 content
        if snapshot.get("content", {}).get("intro"):
            analysis = analyze_content_quality(snapshot["content"]["intro"], "Stage 2")
            snapshot["analysis"] = {"intro": analysis}
        
        print(f"✅ Stage 2 completed")
        print(f"   Headline: {snapshot.get('content', {}).get('headline', 'N/A')[:60]}...")
        print(f"   Intro length: {len(snapshot.get('content', {}).get('intro', ''))}")
        
        # Stage 3: Extraction
        print("\n" + "=" * 80)
        print("STAGE 3: Structured Data Extraction")
        print("=" * 80)
        context = await stages[3].execute(context)
        snapshot = extract_content_snapshot(context, 3, "Extraction")
        all_stage_outputs["stage_3"] = snapshot
        
        # Compare Stage 2 vs Stage 3
        if all_stage_outputs["stage_2"].get("content", {}).get("intro") and snapshot.get("content", {}).get("intro"):
            s2_intro = all_stage_outputs["stage_2"]["content"]["intro"]
            s3_intro = snapshot["content"]["intro"]
            snapshot["comparison_with_stage2"] = {
                "intro_identical": s2_intro == s3_intro,
                "intro_length_diff": len(s3_intro) - len(s2_intro)
            }
        
        print(f"✅ Stage 3 completed")
        print(f"   Intro identical to Stage 2: {snapshot.get('comparison_with_stage2', {}).get('intro_identical', 'N/A')}")
        
        # Stage 2b: Quality Refinement
        print("\n" + "=" * 80)
        print("STAGE 2b: Quality Refinement")
        print("=" * 80)
        
        # Capture before Stage 2b
        before_2b = extract_content_snapshot(context, 3, "Before 2b")
        
        # Run Stage 2b
        from pipeline.blog_generation.stage_02b_quality_refinement import QualityRefinementStage
        stage_2b = QualityRefinementStage()
        context = await stage_2b.execute(context)
        
        # Capture after Stage 2b
        after_2b = extract_content_snapshot(context, 2, "After 2b")
        all_stage_outputs["stage_2b"] = {
            "before": before_2b,
            "after": after_2b
        }
        
        # Compare before/after
        if before_2b.get("content", {}).get("intro") and after_2b.get("content", {}).get("intro"):
            b_intro = before_2b["content"]["intro"]
            a_intro = after_2b["content"]["intro"]
            all_stage_outputs["stage_2b"]["comparison"] = {
                "intro_changed": b_intro != a_intro,
                "intro_length_diff": len(a_intro) - len(b_intro)
            }
        
        print(f"✅ Stage 2b completed")
        if all_stage_outputs["stage_2b"].get("comparison", {}).get("intro_changed"):
            print(f"   Intro changed: {all_stage_outputs['stage_2b']['comparison']['intro_length_diff']} chars")
        
        # Stage 4-9: Parallel stages
        print("\n" + "=" * 80)
        print("STAGES 4-9: Parallel Execution")
        print("=" * 80)
        
        # Capture before parallel
        before_parallel = extract_content_snapshot(context, 3, "Before Parallel")
        
        # Run parallel stages manually to capture outputs
        parallel_stages = [stages[i] for i in [4, 5, 6, 7, 8, 9]]
        parallel_results = await asyncio.gather(*[stage.execute(context) for stage in parallel_stages], return_exceptions=True)
        
        # Use the first successful result (they all modify the same context)
        for i, result in enumerate(parallel_results):
            if not isinstance(result, Exception):
                context = result
                stage_num = [4, 5, 6, 7, 8, 9][i]
                snapshot = extract_content_snapshot(context, stage_num, stages[stage_num].stage_name)
                all_stage_outputs[f"stage_{stage_num}"] = snapshot
        
        # Capture after parallel
        after_parallel = extract_content_snapshot(context, 9, "After Parallel")
        
        # Save individual parallel stage outputs
        for stage_num in [4, 5, 6, 7, 8, 9]:
            stage = stages[stage_num]
            stage_name = stage.stage_name
            snapshot = extract_content_snapshot(context, stage_num, stage_name)
            all_stage_outputs[f"stage_{stage_num}"] = snapshot
        
        print(f"✅ Stages 4-9 completed")
        print(f"   Citations: {'Yes' if after_parallel.get('parallel_results', {}).get('citations_html') else 'No'}")
        print(f"   TOC: {'Yes' if after_parallel.get('parallel_results', {}).get('toc_html') else 'No'}")
        print(f"   FAQ: {'Yes' if after_parallel.get('parallel_results', {}).get('faq_html') else 'No'}")
        
        # Stage 10: Cleanup
        print("\n" + "=" * 80)
        print("STAGE 10: Cleanup")
        print("=" * 80)
        before_cleanup = extract_content_snapshot(context, 9, "Before Cleanup")
        context = await stages[10].execute(context)
        after_cleanup = extract_content_snapshot(context, 10, "After Cleanup")
        all_stage_outputs["stage_10"] = {
            "before": before_cleanup,
            "after": after_cleanup
        }
        
        # Compare cleanup changes
        if before_cleanup.get("content", {}).get("intro") and after_cleanup.get("content", {}).get("intro"):
            b_intro = before_cleanup["content"]["intro"]
            a_intro = after_cleanup["content"]["intro"]
            all_stage_outputs["stage_10"]["comparison"] = {
                "intro_changed": b_intro != a_intro,
                "intro_length_diff": len(a_intro) - len(b_intro)
            }
        
        print(f"✅ Stage 10 completed")
        if all_stage_outputs["stage_10"].get("comparison", {}).get("intro_changed"):
            print(f"   Intro changed: {all_stage_outputs['stage_10']['comparison']['intro_length_diff']} chars")
        
        # Stage 11: Storage
        print("\n" + "=" * 80)
        print("STAGE 11: Storage")
        print("=" * 80)
        before_storage = extract_content_snapshot(context, 10, "Before Storage")
        context = await stages[11].execute(context)
        after_storage = extract_content_snapshot(context, 11, "After Storage")
        all_stage_outputs["stage_11"] = {
            "before": before_storage,
            "after": after_storage
        }
        
        print(f"✅ Stage 11 completed")
        print(f"   Has validated article: {after_storage.get('has_validated_article', False)}")
        
        # Stage 12: Similarity Check (if exists)
        if len(stages) > 12:
            print("\n" + "=" * 80)
            print("STAGE 12: Similarity Check")
            print("=" * 80)
            before_sim = extract_content_snapshot(context, 11, "Before Similarity")
            context = await stages[12].execute(context)
            after_sim = extract_content_snapshot(context, 12, "After Similarity")
            all_stage_outputs["stage_12"] = {
                "before": before_sim,
                "after": after_sim
            }
            print(f"✅ Stage 12 completed")
        
        # Stage 13: Review Iteration (if exists)
        if len(stages) > 13:
            print("\n" + "=" * 80)
            print("STAGE 13: Review Iteration")
            print("=" * 80)
            before_review = extract_content_snapshot(context, 12 if len(stages) > 12 else 11, "Before Review")
            context = await stages[13].execute(context)
            after_review = extract_content_snapshot(context, 13, "After Review")
            all_stage_outputs["stage_13"] = {
                "before": before_review,
                "after": after_review
            }
            print(f"✅ Stage 13 completed")
        
        # Save all outputs
        results_file = output_dir / "all_stages_outputs.json"
        with open(results_file, "w") as f:
            json.dump(all_stage_outputs, f, indent=2, default=str)
        
        print(f"\n✅ All stages completed!")
        print(f"📁 Full outputs saved to: {results_file}")
        print(f"📁 Output directory: {output_dir}")
        
        # Generate summary
        print("\n" + "=" * 80)
        print("STAGE-BY-STAGE SUMMARY")
        print("=" * 80)
        
        for stage_key in sorted(all_stage_outputs.keys()):
            stage_data = all_stage_outputs[stage_key]
            stage_name = stage_data.get("stage_name", stage_key)
            print(f"\n{stage_key}: {stage_name}")
            if "content" in stage_data:
                intro_len = len(stage_data["content"].get("intro", ""))
                print(f"   Intro length: {intro_len} chars")
            if "comparison" in stage_data:
                if stage_data["comparison"].get("intro_changed"):
                    print(f"   ⚠️  Intro changed: {stage_data['comparison']['intro_length_diff']} chars")
        
        return all_stage_outputs
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(run_comprehensive_stage_review())

