#!/usr/bin/env python3
"""
Pipeline Stage-by-Stage Diagnostic Tool

Runs the pipeline and captures output after EACH stage to identify
exactly where issues are introduced.

Usage:
    python3 test_pipeline_stage_by_stage.py
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


def extract_content_snapshot(context: ExecutionContext, stage_num: int) -> dict:
    """Extract a snapshot of content after a stage."""
    snapshot = {
        "stage": stage_num,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Get structured data if available
    if context.structured_data:
        data = context.structured_data
        article_dict = data.dict() if hasattr(data, 'dict') else dict(data)
        
        # Extract key fields
        snapshot["headline"] = article_dict.get("Headline", "")
        snapshot["intro"] = article_dict.get("Intro", "")[:500] if article_dict.get("Intro") else ""
        snapshot["section_01_title"] = article_dict.get("section_01_title", "")
        snapshot["section_01_content"] = article_dict.get("section_01_content", "")[:1000] if article_dict.get("section_01_content") else ""
        snapshot["sources"] = article_dict.get("Sources", "")[:500] if article_dict.get("Sources") else ""
    
    # Get raw article if available
    if context.raw_article:
        snapshot["has_raw_article"] = True
        snapshot["raw_article_keys"] = list(context.raw_article.keys()) if isinstance(context.raw_article, dict) else "not a dict"
    
    return snapshot


def analyze_content_issues(content: str) -> list:
    """Analyze content for common issues."""
    issues = []
    
    if not content:
        return ["Empty content"]
    
    # Check for issues
    if "—" in content:
        issues.append(f"Em dashes found: {content.count('—')} instances")
    
    if "–" in content:
        issues.append(f"En dashes found: {content.count('–')} instances")
    
    # Check for [N] academic citations
    import re
    citations = re.findall(r'\[\d+\]', content)
    if citations:
        issues.append(f"Academic citations [N] found: {len(citations)} instances")
    
    # Check for </p>SOURCE patterns (citation after paragraph close)
    para_citation = re.findall(r'</p>\s*[A-Z][A-Za-z]+\s+(reports?|notes?|predicts?)', content)
    if para_citation:
        issues.append(f"Citations after </p> tags: {len(para_citation)} instances")
    
    # Check for <p><a class="citation"> (citation in own paragraph)
    p_citation = re.findall(r'<p>\s*<a[^>]*class="citation"', content)
    if p_citation:
        issues.append(f"Citations wrapped in <p> tags: {len(p_citation)} instances")
    
    # Check for malformed HTML
    if "<ul>" in content and "</p><ul>" in content:
        issues.append("Potential malformed HTML: </p><ul> pattern")
    
    # Check for lists
    ul_count = content.count("<ul>")
    ol_count = content.count("<ol>")
    if ul_count == 0 and ol_count == 0:
        issues.append("No lists found in content")
    else:
        issues.append(f"Lists found: {ul_count} <ul>, {ol_count} <ol>")
    
    # Check for robotic phrases
    robotic = ["Here's how", "Here's what", "Key points:", "delve into", "crucial to note"]
    for phrase in robotic:
        if phrase.lower() in content.lower():
            issues.append(f"Robotic phrase found: '{phrase}'")
    
    return issues


async def run_stage_by_stage_diagnostic():
    """Run pipeline with stage-by-stage output capture."""
    
    print("=" * 60)
    print("PIPELINE STAGE-BY-STAGE DIAGNOSTIC")
    print("=" * 60)
    print()
    
    # Create output directory
    output_dir = Path("output/stage_diagnostics")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Simple test job config
    job_config = {
        "keyword": "cloud security best practices",
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
        job_id=f"diagnostic-{timestamp}",
        job_config=job_config,
        company_data=company_data,
    )
    
    # Track snapshots
    snapshots = []
    
    # Custom progress callback to capture after each stage
    def capture_stage_output(stage_num: int, stage_name: str, status: str):
        print(f"  Stage {stage_num}: {stage_name} - {status}")
    
    # Create workflow engine
    engine = WorkflowEngine()
    
    # Get the stages
    stages = engine._get_stages()
    
    print(f"Found {len(stages)} stages to run")
    print()
    
    # Run each stage individually
    for stage_class in stages:
        stage = stage_class()
        stage_num = stage.stage_num
        stage_name = stage.stage_name
        
        print(f"\n{'='*60}")
        print(f"STAGE {stage_num}: {stage_name}")
        print("=" * 60)
        
        # Capture BEFORE state
        before_snapshot = extract_content_snapshot(context, stage_num)
        
        try:
            # Run the stage
            print(f"Running Stage {stage_num}...")
            context = await stage.execute(context)
            print(f"✅ Stage {stage_num} completed")
            
            # Capture AFTER state
            after_snapshot = extract_content_snapshot(context, stage_num)
            
            # Analyze content for issues
            if context.structured_data:
                data = context.structured_data
                article_dict = data.dict() if hasattr(data, 'dict') else dict(data)
                
                # Check intro
                intro = article_dict.get("Intro", "")
                if intro:
                    print(f"\n📋 Intro Analysis:")
                    issues = analyze_content_issues(intro)
                    for issue in issues:
                        print(f"   - {issue}")
                
                # Check section 1 content
                s1_content = article_dict.get("section_01_content", "")
                if s1_content:
                    print(f"\n📋 Section 1 Content Analysis:")
                    issues = analyze_content_issues(s1_content)
                    for issue in issues:
                        print(f"   - {issue}")
                
                # Save snapshot to file
                snapshot_file = output_dir / f"stage_{stage_num:02d}_{timestamp}.json"
                with open(snapshot_file, "w") as f:
                    json.dump(after_snapshot, f, indent=2, default=str)
                print(f"\n📁 Snapshot saved: {snapshot_file}")
            
            snapshots.append({
                "stage_num": stage_num,
                "stage_name": stage_name,
                "status": "success",
                "snapshot": after_snapshot,
            })
            
        except Exception as e:
            print(f"❌ Stage {stage_num} failed: {e}")
            snapshots.append({
                "stage_num": stage_num,
                "stage_name": stage_name,
                "status": "failed",
                "error": str(e),
            })
            
            # For critical stages, we might want to stop
            if stage_num <= 3:
                print(f"\n⚠️  Critical stage failed. Stopping diagnostic.")
                break
    
    # Final summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    for s in snapshots:
        status_icon = "✅" if s["status"] == "success" else "❌"
        print(f"{status_icon} Stage {s['stage_num']}: {s['stage_name']} - {s['status']}")
    
    # Save full diagnostic report
    report_file = output_dir / f"full_diagnostic_{timestamp}.json"
    with open(report_file, "w") as f:
        json.dump(snapshots, f, indent=2, default=str)
    print(f"\n📁 Full report saved: {report_file}")
    
    return snapshots


async def run_quick_stage2_diagnostic():
    """Run just Stage 2 and examine output closely."""
    
    print("=" * 60)
    print("STAGE 2 CONTENT GENERATION - DETAILED DIAGNOSTIC")
    print("=" * 60)
    print()
    
    from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage
    
    # Simple test job config
    job_config = {
        "keyword": "cloud security best practices",
        "content_type": "guide",
        "target_audience": "IT professionals",
        "word_count_target": 1500,
    }
    
    company_data = {
        "company_name": "TechCorp",
        "company_url": "https://example.com",
        "industry": "Technology",
    }
    
    # Create context
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    context = ExecutionContext(
        job_id=f"stage2-diag-{timestamp}",
        job_config=job_config,
        company_data=company_data,
    )
    
    # Stage 2 requires a prompt from Stage 1. Generate a simple prompt.
    context.prompt = f"""Write a comprehensive blog article about: {job_config['keyword']}

Target audience: {job_config.get('target_audience', 'IT professionals')}
Content type: {job_config.get('content_type', 'guide')}
Word count: {job_config.get('word_count_target', 2000)}

Create well-researched, authoritative content with proper citations.
"""
    
    # Run Stage 2
    stage = GeminiCallStage()
    print("Running Stage 2 (Gemini content generation)...")
    print("This will take 1-2 minutes...")
    print()
    
    context = await stage.execute(context)
    
    # Examine output
    if context.structured_data:
        data = context.structured_data
        article_dict = data.dict() if hasattr(data, 'dict') else dict(data)
        
        print("=" * 60)
        print("STAGE 2 OUTPUT ANALYSIS")
        print("=" * 60)
        
        # Check each section
        sections_to_check = [
            ("Intro", "Intro"),
            ("Section 1 Title", "section_01_title"),
            ("Section 1 Content", "section_01_content"),
            ("Section 2 Title", "section_02_title"),
            ("Section 2 Content", "section_02_content"),
            ("Sources", "Sources"),
        ]
        
        for label, field in sections_to_check:
            content = article_dict.get(field, "")
            print(f"\n📋 {label}:")
            print("-" * 40)
            
            if not content:
                print("   (empty)")
                continue
            
            # Show first 500 chars
            preview = content[:500] + "..." if len(content) > 500 else content
            print(preview)
            
            # Analyze issues
            print(f"\n   Issues found:")
            issues = analyze_content_issues(content)
            if issues:
                for issue in issues:
                    print(f"   ⚠️  {issue}")
            else:
                print("   ✅ No issues detected")
        
        # Save full output
        output_dir = Path("output/stage_diagnostics")
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_file = output_dir / f"stage2_output_{timestamp}.json"
        with open(output_file, "w") as f:
            json.dump(article_dict, f, indent=2, default=str)
        print(f"\n📁 Full Stage 2 output saved: {output_file}")
        
        return article_dict
    else:
        print("❌ No structured data returned from Stage 2")
        return None


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Pipeline Stage Diagnostic")
    parser.add_argument("--full", action="store_true", help="Run full pipeline diagnostic")
    parser.add_argument("--stage2", action="store_true", help="Run Stage 2 only diagnostic")
    args = parser.parse_args()
    
    if args.full:
        asyncio.run(run_stage_by_stage_diagnostic())
    elif args.stage2:
        asyncio.run(run_quick_stage2_diagnostic())
    else:
        # Default: run Stage 2 diagnostic (faster)
        print("Running Stage 2 diagnostic (use --full for full pipeline)")
        print()
        asyncio.run(run_quick_stage2_diagnostic())

