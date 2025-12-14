"""
Test Stage 2 prompt comparison: Detailed vs Light prompts.

Compares output quality between:
- Detailed prompt (current, comprehensive)
- Light prompt (minimal, focused)

Runs both versions and saves outputs for comparison.
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

from pipeline.core.execution_context import ExecutionContext
from pipeline.core.workflow_engine import WorkflowEngine
from pipeline.core.stage_factory import create_production_pipeline_stages

async def run_prompt_comparison():
    """Run pipeline with both prompt styles and compare outputs."""
    
    # Test configuration
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
    output_dir = Path(f"output/prompt_comparison_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Test 1: Detailed prompt (default)
    print("\n" + "="*80)
    print("TEST 1: DETAILED PROMPT")
    print("="*80)
    
    os.environ["STAGE2_PROMPT_STYLE"] = "detailed"
    
    engine = WorkflowEngine()
    stages = create_production_pipeline_stages()
    engine.register_stages(stages)
    
    try:
        result_detailed = await engine.execute(
            job_id=f"test-detailed-{timestamp}",
            job_config={**test_config, **{"company_data": company_data}}
        )
        results["detailed"] = {
            "success": True,
            "stage_3_output": extract_stage3_content(result_detailed),
            "prompt_length": len(getattr(result_detailed, 'prompt', '')) if hasattr(result_detailed, 'prompt') else 0,
        }
        print("✅ Detailed prompt test completed")
    except Exception as e:
        results["detailed"] = {
            "success": False,
            "error": str(e)
        }
        print(f"❌ Detailed prompt test failed: {e}")
    
    # Test 2: Light prompt
    print("\n" + "="*80)
    print("TEST 2: LIGHT PROMPT")
    print("="*80)
    
    os.environ["STAGE2_PROMPT_STYLE"] = "light"
    
    engine = WorkflowEngine()
    stages = create_production_pipeline_stages()
    engine.register_stages(stages)
    
    try:
        result_light = await engine.execute(
            job_id=f"test-light-{timestamp}",
            job_config={**test_config, **{"company_data": company_data}}
        )
        results["light"] = {
            "success": True,
            "stage_3_output": extract_stage3_content(result_light),
            "prompt_length": len(getattr(result_light, 'prompt', '')) if hasattr(result_light, 'prompt') else 0,
        }
        print("✅ Light prompt test completed")
    except Exception as e:
        results["light"] = {
            "success": False,
            "error": str(e)
        }
        print(f"❌ Light prompt test failed: {e}")
    
    # Save comparison results
    comparison_file = output_dir / "comparison.json"
    with open(comparison_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # Generate comparison report
    generate_comparison_report(results, output_dir)
    
    print(f"\n✅ Comparison complete. Results saved to: {output_dir}")
    return results

def extract_stage3_content(context):
    """Extract Stage 3 content for comparison."""
    if not hasattr(context, 'structured_data') or not context.structured_data:
        return None
    
    # Convert to dict if needed
    if hasattr(context.structured_data, 'model_dump'):
        data = context.structured_data.model_dump()
    elif isinstance(context.structured_data, dict):
        data = context.structured_data
    else:
        return None
    
    # Extract key fields for comparison
    return {
        "intro": data.get("Intro", ""),
        "section_02_content": data.get("section_02_content", ""),
        "section_04_content": data.get("section_04_content", ""),
        "section_06_content": data.get("section_06_content", ""),
        "section_09_content": data.get("section_09_content", ""),
    }

def generate_comparison_report(results, output_dir):
    """Generate markdown comparison report."""
    report = ["# Stage 2 Prompt Comparison Report\n"]
    report.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    if not results.get("detailed", {}).get("success") or not results.get("light", {}).get("success"):
        report.append("## ⚠️ One or both tests failed\n")
        report.append(f"Detailed: {results.get('detailed', {}).get('error', 'N/A')}\n")
        report.append(f"Light: {results.get('light', {}).get('error', 'N/A')}\n")
        with open(output_dir / "comparison_report.md", "w") as f:
            f.write("\n".join(report))
        return
    
    detailed = results["detailed"]["stage_3_output"]
    light = results["light"]["stage_3_output"]
    
    report.append("## Comparison Metrics\n\n")
    report.append("| Metric | Detailed | Light | Winner |\n")
    report.append("|--------|----------|-------|--------|\n")
    
    # Compare citations
    detailed_citations = count_citations(detailed)
    light_citations = count_citations(light)
    report.append(f"| Citations as `<a>` links | {detailed_citations} | {light_citations} | {'Detailed' if detailed_citations > light_citations else 'Light'} |\n")
    
    # Compare paragraph tags
    detailed_paragraphs = count_paragraph_tags(detailed)
    light_paragraphs = count_paragraph_tags(light)
    report.append(f"| `<p>` tags used | {detailed_paragraphs} | {light_paragraphs} | {'Detailed' if detailed_paragraphs > light_paragraphs else 'Light'} |\n")
    
    # Compare lists
    detailed_lists = count_lists(detailed)
    light_lists = count_lists(light)
    report.append(f"| Lists present | {detailed_lists} | {light_lists} | {'Detailed' if detailed_lists > light_lists else 'Light'} |\n")
    
    # Compare br tags (fewer is better)
    detailed_br = count_br_tags(detailed)
    light_br = count_br_tags(light)
    report.append(f"| `<br><br>` tags (fewer better) | {detailed_br} | {light_br} | {'Detailed' if detailed_br < light_br else 'Light'} |\n")
    
    report.append("\n## Detailed Content Comparison\n\n")
    
    # Compare each section
    sections = ["intro", "section_02_content", "section_04_content", "section_06_content", "section_09_content"]
    
    for section in sections:
        report.append(f"### {section}\n\n")
        report.append("**Detailed Prompt Output:**\n")
        report.append(f"```html\n{detailed.get(section, 'N/A')[:500]}...\n```\n\n")
        report.append("**Light Prompt Output:**\n")
        report.append(f"```html\n{light.get(section, 'N/A')[:500]}...\n```\n\n")
        
        # Compare specific issues
        report.append("**Issues Found:**\n")
        
        detailed_text = detailed.get(section, "")
        light_text = light.get(section, "")
        
        # Check citations
        if "<strong>" in detailed_text and "citation" in detailed_text.lower():
            report.append("- Detailed: Citations as `<strong>` tags ❌\n")
        if "<a" in detailed_text and "citation" in detailed_text:
            report.append("- Detailed: Citations as `<a>` links ✅\n")
        
        if "<strong>" in light_text and "citation" in light_text.lower():
            report.append("- Light: Citations as `<strong>` tags ❌\n")
        if "<a" in light_text and "citation" in light_text:
            report.append("- Light: Citations as `<a>` links ✅\n")
        
        # Check paragraphs
        if "<br><br>" in detailed_text:
            report.append("- Detailed: Uses `<br><br>` ❌\n")
        if "<p>" in detailed_text:
            report.append("- Detailed: Uses `<p>` tags ✅\n")
        
        if "<br><br>" in light_text:
            report.append("- Light: Uses `<br><br>` ❌\n")
        if "<p>" in light_text:
            report.append("- Light: Uses `<p>` tags ✅\n")
        
        report.append("\n")
    
    with open(output_dir / "comparison_report.md", "w") as f:
        f.write("\n".join(report))

def count_citations(content_dict):
    """Count citations as <a> links."""
    total = 0
    for text in content_dict.values():
        if isinstance(text, str):
            total += text.count('<a') + text.count('class="citation"')
    return total

def count_paragraph_tags(content_dict):
    """Count <p> tags."""
    total = 0
    for text in content_dict.values():
        if isinstance(text, str):
            total += text.count('<p>')
    return total

def count_lists(content_dict):
    """Count lists."""
    total = 0
    for text in content_dict.values():
        if isinstance(text, str):
            total += text.count('<ul>') + text.count('<ol>')
    return total

def count_br_tags(content_dict):
    """Count <br><br> tags."""
    total = 0
    for text in content_dict.values():
        if isinstance(text, str):
            total += text.count('<br><br>')
    return total

if __name__ == "__main__":
    asyncio.run(run_prompt_comparison())

