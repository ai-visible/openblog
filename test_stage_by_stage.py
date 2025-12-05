#!/usr/bin/env python3
"""
Test stages one at a time, using output from previous stage as input.

Usage:
    python3.13 test_stage_by_stage.py [stage_number]
    
    If stage_number is provided, test only that stage (requires previous outputs)
    If not provided, test all stages sequentially starting from Stage 0
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core import WorkflowEngine, ExecutionContext
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

# Directory to store stage outputs
STAGE_OUTPUT_DIR = Path(__file__).parent / "stage_outputs"
STAGE_OUTPUT_DIR.mkdir(exist_ok=True)


def save_stage_output(stage_num: int, context: ExecutionContext):
    """Save stage output to JSON file."""
    output_file = STAGE_OUTPUT_DIR / f"stage_{stage_num:02d}_output.json"
    
    # Convert context to serializable dict
    output = {
        "job_id": context.job_id,
        "job_config": context.job_config,
        "company_data": context.company_data,
        "language": context.language,
        "prompt": context.prompt[:500] + "..." if context.prompt and len(context.prompt) > 500 else context.prompt,
        "raw_article_length": len(context.raw_article) if context.raw_article else 0,
        "structured_data_keys": list(context.structured_data.model_dump().keys()) if context.structured_data else [],
        "parallel_results_keys": list(context.parallel_results.keys()) if context.parallel_results else [],
        "validated_article_keys": list(context.validated_article.keys()) if context.validated_article else [],
    }
    
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"   💾 Saved output to: {output_file}")


def load_stage_output(stage_num: int) -> dict:
    """Load stage output from JSON file."""
    output_file = STAGE_OUTPUT_DIR / f"stage_{stage_num:02d}_output.json"
    
    if not output_file.exists():
        raise FileNotFoundError(f"Stage {stage_num} output not found. Run previous stages first.")
    
    with open(output_file) as f:
        return json.load(f)


async def test_single_stage(stage_num: int, context: ExecutionContext):
    """Test a single stage and report timing."""
    stage_names = {
        0: "Data Fetch",
        1: "Prompt Build",
        2: "Gemini Call",
        3: "Extraction",
        4: "Citations",
        5: "Internal Links",
        6: "Table of Contents",
        7: "Metadata",
        8: "FAQ/PAA",
        9: "Image",
        10: "Cleanup",
        11: "Storage",
    }
    
    stage_name = stage_names.get(stage_num, f"Stage {stage_num}")
    
    print(f"\n{'=' * 80}")
    print(f"TESTING STAGE {stage_num}: {stage_name}")
    print(f"{'=' * 80}")
    
    engine = WorkflowEngine()
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
    
    stage_instance = engine.get_stage(stage_num)
    if not stage_instance:
        print(f"❌ Stage {stage_num} not registered")
        return None, 0
    
    start_time = time.time()
    try:
        result_context = await stage_instance.execute(context)
        duration = time.time() - start_time
        
        print(f"✅ Stage {stage_num} completed in {duration:.2f}s")
        
        # Show what was produced
        if stage_num == 0:
            print(f"   Company: {result_context.company_data.get('company_name', 'N/A')}")
            print(f"   Language: {result_context.language}")
        elif stage_num == 1:
            print(f"   Prompt length: {len(result_context.prompt)} chars")
        elif stage_num == 2:
            print(f"   Raw article: {len(result_context.raw_article)} chars")
        elif stage_num == 3:
            print(f"   Structured data: {type(result_context.structured_data).__name__}")
            if result_context.structured_data:
                print(f"   Sections: {sum(1 for i in range(1, 10) if getattr(result_context.structured_data, f'section_{i:02d}_title', ''))}")
        elif stage_num == 4:
            citations_count = result_context.parallel_results.get('citations_count', 0)
            print(f"   Citations: {citations_count}")
        elif stage_num == 10:
            print(f"   Validated article: {len(result_context.validated_article)} fields")
            aeo_score = result_context.quality_report.get('metrics', {}).get('aeo_score', 0)
            print(f"   AEO Score: {aeo_score}/100")
        elif stage_num == 11:
            storage_success = result_context.storage_result.get('success', False)
            print(f"   Storage: {'✅ Success' if storage_success else '❌ Failed'}")
        
        # Save output
        save_stage_output(stage_num, result_context)
        
        return result_context, duration
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ Stage {stage_num} FAILED after {duration:.2f}s")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return None, duration


async def main():
    """Test stages one at a time."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test stages individually")
    parser.add_argument("stage", type=int, nargs="?", help="Stage number to test (0-11)")
    parser.add_argument("--from", type=int, dest="from_stage", help="Start from this stage (loads previous output)")
    args = parser.parse_args()
    
    print("=" * 80)
    print("STAGE-BY-STAGE TESTING")
    print("=" * 80)
    print()
    print("Each stage uses output from the previous stage.")
    print(f"Outputs saved to: {STAGE_OUTPUT_DIR}")
    print()
    
    # Determine which stage to test
    if args.stage is not None:
        # Test single stage
        start_stage = args.stage
        end_stage = args.stage
    elif args.from_stage is not None:
        # Test from specific stage onwards
        start_stage = args.from_stage
        end_stage = 11
    else:
        # Test all stages from beginning
        start_stage = 0
        end_stage = 11
    
    # Initial context
    if start_stage == 0:
        # Start fresh
        job_config = {
            "primary_keyword": "AI adoption in customer service",
            "company_url": "https://example.com",
            "company_name": "Example Corp",
        }
        context = ExecutionContext(job_id="test-stage-by-stage", job_config=job_config)
    else:
        # Load previous stage output
        print(f"Loading output from Stage {start_stage - 1}...")
        prev_output = load_stage_output(start_stage - 1)
        context = ExecutionContext(
            job_id=prev_output.get("job_id", "test-stage-by-stage"),
            job_config=prev_output.get("job_config", {})
        )
        # Note: This is a simplified load - full context restoration would need more work
        # For now, we'll just use job_config and let the stage rebuild what it needs
    
    # Test stages sequentially
    total_time = 0
    
    for stage_num in range(start_stage, end_stage + 1):
        context, duration = await test_single_stage(stage_num, context)
        total_time += duration
        
        if context is None:
            print(f"\n⚠️  Stopping due to error in Stage {stage_num}")
            break
        
        print(f"\n⏱️  Cumulative time so far: {total_time:.2f}s")
        
        # Ask user if they want to continue
        if stage_num < end_stage:
            response = input(f"\nContinue to Stage {stage_num + 1}? (y/n): ").strip().lower()
            if response != 'y':
                print("Stopped by user.")
                break
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    print(f"Total time: {total_time:.2f}s")
    print(f"Outputs saved in: {STAGE_OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())

