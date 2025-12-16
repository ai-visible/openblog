#!/usr/bin/env python3
"""
Test Stage 7: Similarity Check

Verifies that Stage 7 correctly:
1. Extracts article data
2. Performs similarity check
3. Stores results in context.similarity_report
4. Handles cases with no similar articles
"""

import json
import asyncio
from pathlib import Path
from pipeline.core.execution_context import ExecutionContext
from pipeline.blog_generation.stage_07_similarity_check import HybridSimilarityCheckStage
from pipeline.models.output_schema import ArticleOutput

async def test_stage7():
    """Test Stage 7 similarity check."""
    
    print('='*80)
    print('TESTING STAGE 7: SIMILARITY CHECK')
    print('='*80)
    print()
    
    # Load actual article data from inspection
    stage6_file = Path('inspection_output_20251216-023614/stage_06/full_context.json')
    if not stage6_file.exists():
        print("❌ Inspection data not found")
        print("   Looking for: inspection_output_20251216-023614/stage_06/full_context.json")
        return
    
    data = json.load(open(stage6_file))
    structured_data_dict = data.get('structured_data', {})
    
    # Create context
    context = ExecutionContext(
        job_id="test-similarity-check",
        job_config={},
    )
    
    # Convert structured_data dict to ArticleOutput
    structured_data = ArticleOutput(**structured_data_dict)
    context.structured_data = structured_data
    
    # Initialize Stage 7
    stage = HybridSimilarityCheckStage()
    
    print("Running Stage 7 (Similarity Check)...")
    print(f"  Job ID: {context.job_id}")
    print(f"  Article: {structured_data.Headline[:60]}...")
    print()
    
    try:
        # Run Stage 7
        result_context = await stage.execute(context)
        
        # Check results
        print("RESULTS:")
        print('-'*80)
        
        # Check similarity_report (correct location)
        if hasattr(result_context, 'similarity_report') and result_context.similarity_report:
            similarity = result_context.similarity_report
            print(f"✅ similarity_report found in context")
            print(f"   Type: {type(similarity).__name__}")
            print(f"   Is too similar: {similarity.is_too_similar}")
            print(f"   Similarity score: {similarity.similarity_score:.2f}")
            print(f"   Analysis mode: {similarity.analysis_mode}")
            
            if hasattr(similarity, 'issues') and similarity.issues:
                print(f"   Issues: {len(similarity.issues)}")
                for issue in similarity.issues[:3]:
                    print(f"      - {issue}")
            
            if hasattr(similarity, 'similar_articles') and similarity.similar_articles:
                print(f"   Similar articles found: {len(similarity.similar_articles)}")
                for article in similarity.similar_articles[:3]:
                    print(f"      - {article.get('title', 'N/A')[:50]}...")
                    print(f"        Score: {article.get('similarity_score', 0):.2f}")
        else:
            print("❌ similarity_report NOT found in context")
        
        # Check parallel_results (should NOT be here for Stage 7)
        pr = result_context.parallel_results
        if 'similarity_check' in pr:
            print(f"\n⚠️  similarity_check found in parallel_results (unexpected)")
            print(f"   Stage 7 stores results in context.similarity_report, not parallel_results")
        else:
            print(f"\n✅ similarity_check NOT in parallel_results (correct)")
            print(f"   Stage 7 correctly stores results in context.similarity_report")
        
        # Check regeneration flag
        if hasattr(result_context, 'regeneration_needed'):
            print(f"\n✅ regeneration_needed flag: {result_context.regeneration_needed}")
        
        # Check batch stats
        if hasattr(result_context, 'batch_stats') and result_context.batch_stats:
            stats = result_context.batch_stats
            print(f"\n✅ Batch stats available:")
            print(f"   Articles checked: {stats.get('articles_checked', 0)}")
            print(f"   Similar articles found: {stats.get('similar_articles_found', 0)}")
        
        print()
        print('='*80)
        if hasattr(result_context, 'similarity_report') and result_context.similarity_report:
            print("✅ TEST PASSED: Stage 7 similarity check works!")
            print(f"   Similarity score: {result_context.similarity_report.similarity_score:.2f}")
            print(f"   Too similar: {result_context.similarity_report.is_too_similar}")
        else:
            print("❌ TEST FAILED: No similarity_report found")
        print('='*80)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stage7())

