#!/usr/bin/env python3
"""
Test Stage 4 NoneType Handling

Tests the specific scenarios that were causing 'NoneType' object has no attribute 'get' errors.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_file = Path(__file__).parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
    if "GOOGLE_GEMINI_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_GEMINI_API_KEY"]
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.blog_generation.stage_04_citations import CitationsStage
from pipeline.core.execution_context import ExecutionContext
from pipeline.models.output_schema import ArticleOutput
from pipeline.config import Config


async def test_stage4_none_scenarios():
    """Test Stage 4 with None scenarios that were causing errors"""
    print("="*70)
    print("STAGE 4 NONETYPE HANDLING TEST")
    print("="*70)
    print()
    
    stage = CitationsStage(config=Config())
    
    # Create minimal valid structured_data (using model_validate to bypass required fields)
    structured_data_dict = {
        "Headline": "Test Article",
        "Teaser": "Test teaser",
        "Direct_Answer": "Test answer",
        "Intro": "Test intro paragraph",
        "Meta_Title": "Test Meta",
        "Meta_Description": "Test description",
        "section_01_title": "Section 1",
        "section_01_content": "Content 1",
        "Sources": "[1]: https://example.com – Test source"
    }
    structured_data = ArticleOutput.model_validate(structured_data_dict)
    
    test_scenarios = [
        {
            "name": "company_data=None, sitemap_data=None",
            "company_data": None,
            "sitemap_data": None,
            "expected": "Should handle gracefully (no crash)"
        },
        {
            "name": "company_data={}, sitemap_data=None",
            "company_data": {},
            "sitemap_data": None,
            "expected": "Should handle gracefully"
        },
        {
            "name": "company_data={'company_url': '...'}, sitemap_data=None",
            "company_data": {"company_url": "https://test.com"},
            "sitemap_data": None,
            "expected": "Should work"
        },
        {
            "name": "company_data={'company_url': '...'}, sitemap_data={}",
            "company_data": {"company_url": "https://test.com"},
            "sitemap_data": {},
            "expected": "Should work"
        },
        {
            "name": "company_data={'company_url': '...'}, sitemap_data={'competitors': []}",
            "company_data": {"company_url": "https://test.com"},
            "sitemap_data": {"competitors": []},
            "expected": "Should work"
        },
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print("="*70)
        print(f"Testing: {scenario['name']}")
        print("="*70)
        print(f"Expected: {scenario['expected']}")
        
        try:
            # Create context
            context = ExecutionContext(
                job_id="test-123",
                job_config={},
                company_data=scenario["company_data"],
                structured_data=structured_data
            )
            
            # Set sitemap_data if provided
            if scenario["sitemap_data"] is not None:
                context.sitemap_data = scenario["sitemap_data"]
            
            # Execute Stage 4
            start_time = asyncio.get_event_loop().time()
            
            try:
                context = await stage.execute(context)
                duration = asyncio.get_event_loop().time() - start_time
                
                print(f"  ✅ Stage 4 completed successfully in {duration:.2f}s")
                print(f"  Citations HTML length: {len(context.parallel_results.get('citations_html', ''))}")
                print(f"  Citations count: {context.parallel_results.get('citations_count', 0)}")
                results.append({"scenario": scenario["name"], "success": True, "duration": duration})
                
            except AttributeError as e:
                if "'NoneType' object has no attribute 'get'" in str(e):
                    print(f"  ❌ FAILED: NoneType error still occurs - {e}")
                    results.append({"scenario": scenario["name"], "success": False, "error": str(e)})
                else:
                    print(f"  ⚠️  Other AttributeError: {e}")
                    results.append({"scenario": scenario["name"], "success": False, "error": str(e)})
            except Exception as e:
                print(f"  ⚠️  Error: {e}")
                results.append({"scenario": scenario["name"], "success": False, "error": str(e)})
                
        except Exception as e:
            print(f"  ❌ Setup failed: {e}")
            results.append({"scenario": scenario["name"], "success": False, "error": str(e)})
        
        print()
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    print()
    
    passed = sum(1 for r in results if r.get("success"))
    total = len(results)
    
    print(f"Results: {passed}/{total} scenarios passed")
    print()
    
    for result in results:
        status = "✅" if result.get("success") else "❌"
        print(f"{status} {result['scenario']}")
        if not result.get("success"):
            print(f"   Error: {result.get('error', 'Unknown')}")
        elif "duration" in result:
            print(f"   Duration: {result['duration']:.2f}s")
    
    print()
    
    if passed == total:
        print("✅ ALL TESTS PASSED - NoneType handling is working correctly!")
    else:
        print(f"❌ {total - passed} TEST(S) FAILED - Review errors above")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(test_stage4_none_scenarios())
    sys.exit(0 if success else 1)

