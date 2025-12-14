#!/usr/bin/env python3
"""
Pipeline Test with Stage-by-Stage Output Storage

Runs the full pipeline and stores output after EACH stage for inspection.
This allows us to see exactly where issues are introduced.

Usage:
    python3 test_pipeline_with_stage_outputs.py
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core import ExecutionContext
from pipeline.core.workflow_engine import WorkflowEngine
from pipeline.models.output_schema import ArticleOutput


def save_stage_output(context: ExecutionContext, stage_num: int, stage_name: str, output_dir: Path):
    """Save output after a stage completes."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    stage_output = {
        "stage_num": stage_num,
        "stage_name": stage_name,
        "timestamp": timestamp,
    }
    
    # Save structured_data if available
    if context.structured_data:
        data = context.structured_data
        article_dict = data.dict() if hasattr(data, 'dict') else dict(data)
        stage_output["structured_data"] = article_dict
        
        # Extract key fields for quick inspection
        stage_output["preview"] = {
            "headline": article_dict.get("Headline", ""),
            "intro_preview": article_dict.get("Intro", "")[:300] if article_dict.get("Intro") else "",
            "section_01_title": article_dict.get("section_01_title", ""),
            "section_01_preview": article_dict.get("section_01_content", "")[:300] if article_dict.get("section_01_content") else "",
            "sources_preview": article_dict.get("Sources", "")[:500] if article_dict.get("Sources") else "",
        }
    
    # Save raw_article if available
    if context.raw_article:
        stage_output["has_raw_article"] = True
        if isinstance(context.raw_article, dict):
            stage_output["raw_article_keys"] = list(context.raw_article.keys())
            # Save a preview of raw article
            stage_output["raw_article_preview"] = {
                k: str(v)[:200] for k, v in list(context.raw_article.items())[:5]
            }
    
    # Save parallel_results if available
    if hasattr(context, 'parallel_results') and context.parallel_results:
        stage_output["parallel_results_keys"] = list(context.parallel_results.keys())
    
    # Save to file
    filename = f"stage_{stage_num:02d}_{stage_name.replace(' ', '_').lower()}_{timestamp}.json"
    filepath = output_dir / filename
    
    with open(filepath, "w") as f:
        json.dump(stage_output, f, indent=2, default=str)
    
    return filepath


def analyze_content_quality(content: str) -> dict:
    """Analyze content for quality issues."""
    import re
    
    if not content:
        return {"empty": True}
    
    issues = {
        "em_dashes": len(re.findall(r'—', content)),
        "en_dashes": len(re.findall(r'–', content)),
        "academic_citations": len(re.findall(r'\[\d+\]', content)),
        "bullet_lists": content.count('<ul>'),
        "numbered_lists": content.count('<ol>'),
        "list_items": content.count('<li>'),
        "paragraphs": content.count('<p>'),
        "strong_tags": content.count('<strong>'),
        "malformed_html": len(re.findall(r'</p>\s*[A-Z][A-Za-z]+\s+(reports?|notes?)', content)),
        "citation_in_p": len(re.findall(r'<p>\s*<a[^>]*class="citation"', content)),
    }
    
    return issues


async def run_pipeline_with_output_storage():
    """Run pipeline and store output after each stage."""
    
    print("=" * 70)
    print("PIPELINE TEST WITH STAGE-BY-STAGE OUTPUT STORAGE")
    print("=" * 70)
    print()
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/pipeline_stages_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Simple test job config
    job_config = {
        "primary_keyword": "cloud security best practices",
        "keyword": "cloud security best practices",
        "company_url": "https://example.com",  # Required by Stage 0
        "content_type": "guide",
        "target_audience": "IT professionals",
        "word_count_target": 2000,
    }
    
    company_data = {
        "company_name": "TechCorp",
        "company_url": "https://example.com",
        "industry": "Technology",
    }
    
    # Create initial context
    context = ExecutionContext(
        job_id=f"pipeline-test-{timestamp}",
        job_config=job_config,
        company_data=company_data,
    )
    
    # Create workflow engine
    engine = WorkflowEngine()
    # Get stages from stage factory
    from pipeline.core.stage_factory import create_production_pipeline_stages
    stages = create_production_pipeline_stages()
    
    print(f"Found {len(stages)} stages to run")
    print()
    
    stage_outputs = []
    
    # Run each stage
    for stage in stages:
        stage_num = stage.stage_num
        stage_name = stage.stage_name
        
        print(f"\n{'='*70}")
        print(f"STAGE {stage_num}: {stage_name}")
        print("=" * 70)
        
        try:
            # Run stage
            print(f"Running Stage {stage_num}...")
            context = await stage.execute(context)
            print(f"✅ Stage {stage_num} completed")
            
            # Save output
            output_file = save_stage_output(context, stage_num, stage_name, output_dir)
            print(f"📁 Output saved: {output_file.name}")
            
            # Analyze content quality if structured_data exists
            if context.structured_data:
                data = context.structured_data
                article_dict = data.dict() if hasattr(data, 'dict') else dict(data)
                
                # Analyze intro
                intro = article_dict.get("Intro", "")
                if intro:
                    intro_issues = analyze_content_quality(intro)
                    if intro_issues.get("em_dashes", 0) > 0 or intro_issues.get("en_dashes", 0) > 0:
                        print(f"   ⚠️  Intro issues: {intro_issues.get('em_dashes', 0)} em dashes, {intro_issues.get('en_dashes', 0)} en dashes")
                
                # Analyze section 1
                s1 = article_dict.get("section_01_content", "")
                if s1:
                    s1_issues = analyze_content_quality(s1)
                    lists = s1_issues.get("bullet_lists", 0) + s1_issues.get("numbered_lists", 0)
                    if lists > 0:
                        print(f"   ✅ Section 1 has {lists} lists")
                    if s1_issues.get("em_dashes", 0) > 0:
                        print(f"   ⚠️  Section 1 has {s1_issues.get('em_dashes', 0)} em dashes")
            
            stage_outputs.append({
                "stage_num": stage_num,
                "stage_name": stage_name,
                "status": "success",
                "output_file": str(output_file),
            })
            
        except Exception as e:
            print(f"❌ Stage {stage_num} failed: {e}")
            import traceback
            traceback.print_exc()
            
            stage_outputs.append({
                "stage_num": stage_num,
                "stage_name": stage_name,
                "status": "failed",
                "error": str(e),
            })
            
            # For critical stages, stop
            if stage_num <= 3:
                print(f"\n⚠️  Critical stage failed. Stopping.")
                break
    
    # Final summary
    print("\n" + "=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    
    for s in stage_outputs:
        status_icon = "✅" if s["status"] == "success" else "❌"
        print(f"{status_icon} Stage {s['stage_num']}: {s['stage_name']} - {s['status']}")
    
    # Save summary
    summary_file = output_dir / "pipeline_summary.json"
    with open(summary_file, "w") as f:
        json.dump({
            "timestamp": timestamp,
            "stages": stage_outputs,
            "output_directory": str(output_dir),
        }, f, indent=2, default=str)
    
    print(f"\n📁 Summary saved: {summary_file}")
    print(f"\n📁 All stage outputs in: {output_dir}")
    print(f"\n💡 To inspect: Open {output_dir} and check each stage_*.json file")
    
    return stage_outputs, output_dir


if __name__ == "__main__":
    asyncio.run(run_pipeline_with_output_storage())

