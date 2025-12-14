#!/usr/bin/env python3
"""
Deep Inspection: Stage 2 → Stage 2b → Stage 3 Pure Outputs

Captures and analyzes pure outputs from:
- Stage 2: Raw Gemini JSON output
- Stage 2b: After quality refinement (if it runs)
- Stage 3: After structured data extraction

Analyzes:
- How perfect is Stage 2 output?
- What issues does Stage 2b fix?
- How perfect is output after Stage 2b?
- What remains after Stage 3?
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
from pipeline.models.output_schema import ArticleOutput


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


def extract_stage2_raw_json(context: ExecutionContext) -> Dict[str, Any]:
    """Extract raw JSON from Stage 2 output."""
    if not context.raw_article:
        return {}
    
    try:
        # raw_article is a JSON string
        if isinstance(context.raw_article, str):
            return json.loads(context.raw_article)
        return context.raw_article
    except:
        return {"raw": str(context.raw_article)[:500]}


def extract_stage3_content(context: ExecutionContext) -> Dict[str, Any]:
    """Extract content from Stage 3 structured data."""
    if not context.structured_data:
        return {}
    
    data = context.structured_data
    if hasattr(data, 'model_dump'):
        return data.model_dump()
    elif hasattr(data, 'dict'):
        return data.dict()
    elif isinstance(data, dict):
        return data
    return {}


async def run_deep_inspection():
    """Run pipeline and capture pure outputs from Stage 2, 2b, and 3."""
    
    # Ensure detailed prompt
    os.environ["STAGE2_PROMPT_STYLE"] = "detailed"
    
    print("=" * 80)
    print("DEEP INSPECTION: Stage 2 → Stage 2b → Stage 3 Pure Outputs")
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
    output_dir = Path(f"output/stage2_2b_3_inspection_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize engine
    engine = WorkflowEngine()
    stages = create_production_pipeline_stages()
    engine.register_stages(stages)
    
    # Create context
    context = ExecutionContext(
        job_id=f"inspection-{timestamp}",
        job_config={**test_config, **{"company_data": company_data}}
    )
    
    results = {
        "stage_2": {},
        "stage_2b": {},
        "stage_3": {},
        "analysis": {}
    }
    
    print("Running pipeline...")
    print()
    
    # Custom execution to capture Stage 2, 2b, and 3 outputs
    try:
        # Stage 0: Data Fetch
        print("Stage 0: Data Fetch...")
        context = await stages[0].execute(context)
        
        # Stage 1: Prompt Build
        print("Stage 1: Prompt Build...")
        context = await stages[1].execute(context)
        
        # Stage 2: Gemini Call
        print("\n" + "=" * 80)
        print("STAGE 2: Gemini Content Generation")
        print("=" * 80)
        context = await stages[2].execute(context)
        
        # Capture Stage 2 output
        stage2_raw_json = extract_stage2_raw_json(context)
        stage2_content = {}
        
        # Extract content from raw JSON
        if stage2_raw_json:
            for key in ['Intro', 'section_01_content', 'section_02_content', 'section_04_content', 'section_06_content', 'section_09_content']:
                if key in stage2_raw_json:
                    stage2_content[key] = stage2_raw_json[key]
        
        # Analyze Stage 2 content
        stage2_analysis = {}
        for key, content in stage2_content.items():
            if isinstance(content, str):
                stage2_analysis[key] = analyze_content_quality(content, "Stage 2")
        
        results["stage_2"] = {
            "raw_json_keys": list(stage2_raw_json.keys()) if isinstance(stage2_raw_json, dict) else [],
            "content": stage2_content,
            "analysis": stage2_analysis
        }
        
        print(f"✅ Stage 2 completed")
        json_keys_count = len(stage2_raw_json.keys()) if isinstance(stage2_raw_json, dict) else 0
        print(f"   Raw JSON keys: {json_keys_count}")
        print(f"   Content fields extracted: {len(stage2_content)}")
        
        # Save Stage 2 output
        stage2_file = output_dir / "stage_02_raw_output.json"
        with open(stage2_file, "w") as f:
            json.dump({
                "raw_json": stage2_raw_json,
                "content": stage2_content,
                "analysis": stage2_analysis
            }, f, indent=2, default=str)
        print(f"   Saved to: {stage2_file}")
        
        # Stage 3: Extraction
        print("\n" + "=" * 80)
        print("STAGE 3: Structured Data Extraction")
        print("=" * 80)
        context = await stages[3].execute(context)
        
        # Capture Stage 3 output (before Stage 2b)
        stage3_before_2b = extract_stage3_content(context)
        stage3_before_2b_content = {}
        stage3_before_2b_analysis = {}
        
        for key in ['Intro', 'section_01_content', 'section_02_content', 'section_04_content', 'section_06_content', 'section_09_content']:
            if key in stage3_before_2b:
                content = stage3_before_2b[key]
                if isinstance(content, str):
                    stage3_before_2b_content[key] = content
                    stage3_before_2b_analysis[key] = analyze_content_quality(content, "Stage 3 (before 2b)")
        
        results["stage_3"]["before_2b"] = {
            "content": stage3_before_2b_content,
            "analysis": stage3_before_2b_analysis
        }
        
        print(f"✅ Stage 3 completed (before Stage 2b)")
        print(f"   Content fields: {len(stage3_before_2b_content)}")
        
        # Check if Stage 2b runs
        print("\n" + "=" * 80)
        print("CHECKING: Will Stage 2b run?")
        print("=" * 80)
        
        # Stage 2b is conditional - check if it would run
        # It runs after Stage 3 if certain conditions are met
        stage_2b_ran = False
        
        # Try to find Stage 2b in the workflow
        # Actually, Stage 2b runs conditionally via WorkflowEngine._execute_stage_2b_conditional
        # Let's check the workflow engine logic
        
        # For now, let's check if Stage 2b would run by looking at the context
        # Stage 2b typically runs if structured_data exists and quality refinement is enabled
        
        # Continue with remaining stages to see if 2b runs
        # Actually, we need to check the workflow engine to see when 2b runs
        
        # Save Stage 3 (before 2b) output
        stage3_file = output_dir / "stage_03_before_2b.json"
        with open(stage3_file, "w") as f:
            json.dump({
                "content": stage3_before_2b_content,
                "analysis": stage3_before_2b_analysis
            }, f, indent=2, default=str)
        print(f"   Saved to: {stage3_file}")
        
        # Stage 2b: Quality Refinement (runs after Stage 3)
        print("\n" + "=" * 80)
        print("STAGE 2b: Quality Refinement")
        print("=" * 80)
        
        # Manually execute Stage 2b to capture its output
        from pipeline.blog_generation.stage_02b_quality_refinement import QualityRefinementStage
        stage_2b = QualityRefinementStage()
        
        # Capture BEFORE Stage 2b
        stage3_before_2b_final = extract_stage3_content(context)
        
        print("Running Stage 2b...")
        context = await stage_2b.execute(context)
        
        # Capture AFTER Stage 2b
        stage3_after_2b = extract_stage3_content(context)
        stage3_after_2b_content = {}
        stage3_after_2b_analysis = {}
        
        for key in ['Intro', 'section_01_content', 'section_02_content', 'section_04_content', 'section_06_content', 'section_09_content']:
            if key in stage3_after_2b:
                content = stage3_after_2b[key]
                if isinstance(content, str):
                    stage3_after_2b_content[key] = content
                    stage3_after_2b_analysis[key] = analyze_content_quality(content, "Stage 3 (after 2b)")
        
        results["stage_2b"] = {
            "before": {
                "content": {k: stage3_before_2b_final.get(k, "") for k in ['Intro', 'section_02_content', 'section_04_content'] if k in stage3_before_2b_final},
                "analysis": {k: analyze_content_quality(stage3_before_2b_final.get(k, ""), "Before 2b") for k in ['Intro', 'section_02_content', 'section_04_content'] if k in stage3_before_2b_final}
            },
            "after": {
                "content": stage3_after_2b_content,
                "analysis": stage3_after_2b_analysis
            }
        }
        
        print(f"✅ Stage 2b completed")
        print(f"   Content fields after: {len(stage3_after_2b_content)}")
        
        # Save Stage 2b comparison
        stage2b_file = output_dir / "stage_02b_comparison.json"
        with open(stage2b_file, "w") as f:
            json.dump(results["stage_2b"], f, indent=2, default=str)
        print(f"   Saved to: {stage2b_file}")
        
        print("\n" + "=" * 80)
        print("ANALYSIS: Stage 2 → Stage 3 → Stage 2b")
        print("=" * 80)
        
        # Compare Stage 2 vs Stage 3
        comparison = {}
        for key in ['Intro', 'section_02_content', 'section_04_content']:
            if key in stage2_content and key in stage3_before_2b_content:
                stage2_text = stage2_content[key]
                stage3_text = stage3_before_2b_content[key]
                
                comparison[key] = {
                    "identical": stage2_text == stage3_text,
                    "stage2_length": len(stage2_text),
                    "stage3_length": len(stage3_text),
                    "stage2_analysis": stage2_analysis.get(key, {}),
                    "stage3_analysis": stage3_before_2b_analysis.get(key, {}),
                }
                
                print(f"\n{key}:")
                print(f"   Identical: {comparison[key]['identical']}")
                print(f"   Stage 2 length: {comparison[key]['stage2_length']}")
                print(f"   Stage 3 length: {comparison[key]['stage3_length']}")
                
                # Compare issues
                s2_issues = comparison[key]['stage2_analysis'].get('issues', {})
                s3_issues = comparison[key]['stage3_analysis'].get('issues', {})
                
                print(f"   Stage 2 issues:")
                for issue, count in s2_issues.items():
                    if count > 0:
                        print(f"      - {issue}: {count}")
                
                print(f"   Stage 3 issues:")
                for issue, count in s3_issues.items():
                    if count > 0:
                        print(f"      - {issue}: {count}")
        
        results["analysis"]["stage2_vs_stage3"] = comparison
        
        # Compare Stage 3 (before 2b) vs Stage 3 (after 2b)
        print("\n" + "=" * 80)
        print("ANALYSIS: What did Stage 2b fix?")
        print("=" * 80)
        
        stage2b_fixes = {}
        for key in ['Intro', 'section_02_content', 'section_04_content']:
            if key in stage3_before_2b_content and key in stage3_after_2b_content:
                before_text = stage3_before_2b_content[key]
                after_text = stage3_after_2b_content[key]
                
                before_analysis = analyze_content_quality(before_text, "Before 2b")
                after_analysis = analyze_content_quality(after_text, "After 2b")
                
                fixes = {}
                
                # Check what changed
                if before_text != after_text:
                    fixes["content_changed"] = True
                    fixes["length_change"] = len(after_text) - len(before_text)
                else:
                    fixes["content_changed"] = False
                
                # Check issue fixes
                before_issues = before_analysis.get('issues', {})
                after_issues = after_analysis.get('issues', {})
                
                fixes["issues_fixed"] = {}
                for issue_type in ['em_dashes', 'en_dashes', 'academic_citations', 'br_tags']:
                    before_count = before_issues.get(issue_type, 0)
                    after_count = after_issues.get(issue_type, 0)
                    if before_count > after_count:
                        fixes["issues_fixed"][issue_type] = before_count - after_count
                
                # Check citation improvements
                before_citations = before_analysis.get('citations', {})
                after_citations = after_analysis.get('citations', {})
                
                fixes["citation_improvements"] = {
                    "links_added": max(0, after_citations.get('as_links', 0) - before_citations.get('as_links', 0)),
                    "strong_removed": max(0, before_citations.get('as_strong', 0) - after_citations.get('as_strong', 0)),
                }
                
                stage2b_fixes[key] = fixes
                
                print(f"\n{key}:")
                print(f"   Content changed: {fixes['content_changed']}")
                if fixes['content_changed']:
                    print(f"   Length change: {fixes['length_change']} chars")
                if fixes['issues_fixed']:
                    print(f"   Issues fixed:")
                    for issue, count in fixes['issues_fixed'].items():
                        print(f"      - {issue}: {count} fixed")
                if any(fixes['citation_improvements'].values()):
                    print(f"   Citation improvements:")
                    if fixes['citation_improvements']['links_added'] > 0:
                        print(f"      - Links added: {fixes['citation_improvements']['links_added']}")
                    if fixes['citation_improvements']['strong_removed'] > 0:
                        print(f"      - Strong tags removed: {fixes['citation_improvements']['strong_removed']}")
        
        results["analysis"]["stage2b_fixes"] = stage2b_fixes
        
        # Final quality assessment
        print("\n" + "=" * 80)
        print("FINAL QUALITY ASSESSMENT")
        print("=" * 80)
        
        final_assessment = {}
        for key in ['Intro', 'section_02_content', 'section_04_content']:
            if key in stage3_after_2b_content:
                analysis = analyze_content_quality(stage3_after_2b_content[key], "Final")
                final_assessment[key] = {
                    "quality_score": "perfect" if all(v == 0 for k, v in analysis.get('issues', {}).items() if k != 'academic_citations') else "has_issues",
                    "issues": {k: v for k, v in analysis.get('issues', {}).items() if v > 0},
                    "citations": analysis.get('citations', {}),
                    "lists": analysis.get('lists', {}),
                }
                
                print(f"\n{key} (Final):")
                print(f"   Quality: {final_assessment[key]['quality_score']}")
                if final_assessment[key]['issues']:
                    print(f"   Remaining issues:")
                    for issue, count in final_assessment[key]['issues'].items():
                        print(f"      - {issue}: {count}")
                print(f"   Citations as links: {final_assessment[key]['citations'].get('as_links', 0)}")
                print(f"   Lists: {final_assessment[key]['lists'].get('bullet', 0)} bullet, {final_assessment[key]['lists'].get('numbered', 0)} numbered")
        
        results["analysis"]["final_assessment"] = final_assessment
        
        # Save full results
        results_file = output_dir / "full_analysis.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✅ Full analysis saved to: {results_file}")
        print(f"📁 Output directory: {output_dir}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    asyncio.run(run_deep_inspection())

