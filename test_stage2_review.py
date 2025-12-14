"""
Test Stage 2 with full prompt setup and output review.
Runs Stage 1 → Stage 2 and saves output for review.
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
from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage

async def run_stage2_review():
    """Run Stage 1 → Stage 2 and save output for review."""
    
    print("=" * 80)
    print("STAGE 2 CONTENT GENERATION - OUTPUT REVIEW")
    print("=" * 80)
    print()
    
    # Test configuration
    job_config = {
        "primary_keyword": "cloud security best practices",
        "company_url": "https://scaile.tech",
        "word_count": 3000,
        "language": "en",
        "tone": "professional"
    }
    
    company_data = {
        "company_name": "SCAILE",
        "company_url": "https://scaile.tech",
        "industry": "AI Development Tools",
        "description": "SCAILE provides AI-powered development tools for enterprise teams",
        "products": ["AI code generation", "automated testing", "code review assistance"],
        "target_audience": "Enterprise development teams, CTOs, engineering managers",
        "tone": "Professional, technical, authoritative"
    }
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"output/stage2_review_{timestamp}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    print()
    
    # Create initial context
    context = ExecutionContext(
        job_id=f"stage2-review-{timestamp}",
        job_config=job_config,
        company_data=company_data
    )
    
    # Run Stage 1: Build Prompt
    print("🔧 Stage 1: Building prompt...")
    print()
    stage1 = PromptBuildStage()
    context = await stage1.execute(context)
    
    # Save Stage 1 output
    stage1_output = {
        "prompt": context.prompt,
        "company_context": context.company_context.__dict__ if hasattr(context, 'company_context') else None,
        "language": context.language
    }
    
    with open(output_dir / "stage1_prompt.json", "w", encoding="utf-8") as f:
        json.dump(stage1_output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Stage 1 complete")
    print(f"   Prompt length: {len(context.prompt)} characters")
    print()
    
    # Save prompt to text file for easy reading
    with open(output_dir / "stage1_prompt.txt", "w", encoding="utf-8") as f:
        f.write(context.prompt)
    
    print("📝 Prompt saved to:")
    print(f"   - {output_dir / 'stage1_prompt.txt'}")
    print(f"   - {output_dir / 'stage1_prompt.json'}")
    print()
    
    # Run Stage 2: Generate Content
    print("🚀 Stage 2: Generating content with Gemini...")
    print("   (This will take 2-5 minutes with deep research)")
    print()
    
    stage2 = GeminiCallStage()
    context = await stage2.execute(context)
    
    # Parse JSON output
    try:
        raw_json = json.loads(context.raw_article)
    except json.JSONDecodeError:
        print("⚠️  Warning: Could not parse JSON from raw_article")
        raw_json = None
    
    # Save Stage 2 output
    stage2_output = {
        "raw_article": context.raw_article,
        "parsed_json": raw_json,
        "grounding_urls": context.grounding_urls if hasattr(context, 'grounding_urls') else [],
        "source_name_map": context.parallel_results.get("source_name_map_from_grounding", {}) if hasattr(context, 'parallel_results') else {}
    }
    
    with open(output_dir / "stage2_output.json", "w", encoding="utf-8") as f:
        json.dump(stage2_output, f, indent=2, ensure_ascii=False)
    
    # Save raw JSON to separate file for easy reading
    if raw_json:
        with open(output_dir / "stage2_output_pretty.json", "w", encoding="utf-8") as f:
            json.dump(raw_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Stage 2 complete")
    print(f"   Raw article length: {len(context.raw_article)} characters")
    if raw_json:
        print(f"   Parsed JSON keys: {len(raw_json)} fields")
        if "section_01_content" in raw_json:
            section1_preview = raw_json["section_01_content"][:200].replace("\n", " ")
            print(f"   Section 1 preview: {section1_preview}...")
    print()
    
    # Extract key metrics for review
    review_summary = {
        "timestamp": timestamp,
        "job_config": job_config,
        "stage1": {
            "prompt_length": len(context.prompt),
            "language": context.language
        },
        "stage2": {
            "raw_article_length": len(context.raw_article),
            "is_valid_json": raw_json is not None,
            "grounding_urls_count": len(context.grounding_urls) if hasattr(context, 'grounding_urls') else 0
        }
    }
    
    if raw_json:
        # Count citations
        citation_count = 0
        for key, value in raw_json.items():
            if isinstance(value, str) and 'class="citation"' in value:
                citation_count += value.count('class="citation"')
        
        # Count sections
        sections = [k for k in raw_json.keys() if k.startswith("section_") and k.endswith("_title") and raw_json.get(k)]
        section_count = len(sections)
        
        # Count lists
        list_count = 0
        for key, value in raw_json.items():
            if isinstance(value, str):
                list_count += value.count("<ul>") + value.count("<ol>")
        
        # Count conversational phrases
        conversational_phrases = ["you can", "you'll", "here's", "let's", "this is", "when you", "if you"]
        phrase_count = 0
        all_content = " ".join([str(v) for v in raw_json.values() if isinstance(v, str)])
        for phrase in conversational_phrases:
            phrase_count += all_content.lower().count(phrase)
        
        # Count question headers
        question_headers = [k for k in sections if raw_json.get(k, "").strip().endswith("?")]
        question_header_count = len(question_headers)
        
        review_summary["stage2"]["metrics"] = {
            "citation_count": citation_count,
            "section_count": section_count,
            "list_count": list_count,
            "conversational_phrases": phrase_count,
            "question_headers": question_header_count,
            "sections": sections[:5]  # First 5 section titles
        }
    
    with open(output_dir / "review_summary.json", "w", encoding="utf-8") as f:
        json.dump(review_summary, f, indent=2, ensure_ascii=False)
    
    print("📊 Review Summary:")
    print(json.dumps(review_summary, indent=2))
    print()
    
    print("📁 All outputs saved to:")
    print(f"   {output_dir}/")
    print()
    print("Files created:")
    print(f"   - stage1_prompt.txt (readable prompt)")
    print(f"   - stage1_prompt.json (structured prompt data)")
    print(f"   - stage2_output.json (raw + parsed output)")
    print(f"   - stage2_output_pretty.json (formatted JSON)")
    print(f"   - review_summary.json (metrics summary)")
    print()
    
    return context, output_dir

if __name__ == "__main__":
    asyncio.run(run_stage2_review())

