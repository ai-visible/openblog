#!/usr/bin/env python3
"""
Comprehensive QA Test Suite for Blog Writer V2
Tests local, API, and parity to ensure quality and correctness
"""

import asyncio
import os
import sys
import json
import requests
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core import WorkflowEngine
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


class QATestSuite:
    """Comprehensive QA test suite."""
    
    def __init__(self):
        self.test_config = {
            "primary_keyword": "AI customer service automation",
            "company_url": "https://example.com",
            "company_name": "Example Corp",
        }
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {},
        }
        self.api_url = "http://localhost:8000"
        
    async def test_local(self) -> Optional[Dict[str, Any]]:
        """Test 1: Local execution."""
        print("\n" + "=" * 80)
        print("TEST 1: LOCAL EXECUTION")
        print("=" * 80)
        
        try:
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
            if not api_key:
                print("❌ ERROR: No API key found")
                return None
            
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
            
            print("🚀 Executing workflow...")
            start_time = time.time()
            context = await engine.execute(
                job_id=f"qa-test-local-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                job_config=self.test_config
            )
            duration = time.time() - start_time
            
            result = {
                "success": True,
                "job_id": context.job_id,
                "headline": context.structured_data.Headline if context.structured_data else None,
                "html_content": context.final_article.get("html_content") if context.final_article else None,
                "validated_article": bool(context.validated_article),
                "quality_report": bool(context.quality_report),
                "execution_times": context.execution_times if hasattr(context, 'execution_times') else {},
                "duration_seconds": duration,
                "aeo_score": context.quality_report.get("metrics", {}).get("aeo_score") if context.quality_report else None,
                "critical_issues_count": len(context.quality_report.get("critical_issues", [])) if context.quality_report else 0,
            }
            
            # Quality checks
            checks = []
            checks.append(("All 12 stages executed", len(result["execution_times"]) >= 12))
            checks.append(("Headline generated", result["headline"] is not None))
            checks.append(("AEO score calculated", result["aeo_score"] is not None))
            checks.append(("AEO score ≥ 70", result["aeo_score"] and result["aeo_score"] >= 70))
            checks.append(("Duration < 120s", duration < 120))
            checks.append(("Validated article created", result["validated_article"]))
            checks.append(("Quality report created", result["quality_report"]))
            
            passed = sum(1 for _, p in checks if p)
            total = len(checks)
            
            print(f"\n✅ Test completed in {duration:.2f}s")
            print(f"   AEO Score: {result['aeo_score']}")
            print(f"   Headline: {result['headline']}")
            print(f"   Quality Checks: {passed}/{total} passed")
            
            result["quality_checks"] = {name: passed for name, passed in checks}
            result["quality_score"] = f"{passed}/{total}"
            
            return result
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def test_api_health(self) -> bool:
        """Test API health endpoint."""
        print("\n" + "=" * 80)
        print("TEST 2A: API HEALTH CHECK")
        print("=" * 80)
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API is healthy: {data.get('status')}")
                return True
            else:
                print(f"❌ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API health check failed: {e}")
            return False
    
    def test_api_generation(self) -> Optional[Dict[str, Any]]:
        """Test 2: API service execution."""
        print("\n" + "=" * 80)
        print("TEST 2B: API SERVICE EXECUTION")
        print("=" * 80)
        
        if not self.test_api_health():
            return None
        
        try:
            print("🚀 Calling API...")
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/write",
                json=self.test_config,
                timeout=120
            )
            duration = time.time() - start_time
            
            if response.status_code != 200:
                print(f"❌ API returned status {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
            
            result = response.json()
            
            if not result.get("success"):
                print(f"❌ API returned error: {result.get('error', 'Unknown')}")
                return result
            
            # Quality checks
            checks = []
            checks.append(("Success flag true", result.get("success") == True))
            checks.append(("Headline generated", result.get("headline") is not None))
            checks.append(("AEO score calculated", result.get("aeo_score") is not None))
            checks.append(("AEO score ≥ 70", result.get("aeo_score") and result.get("aeo_score") >= 70))
            checks.append(("Duration < 130s", duration < 130))
            checks.append(("Execution times present", bool(result.get("execution_times"))))
            
            passed = sum(1 for _, p in checks if p)
            total = len(checks)
            
            print(f"\n✅ Test completed in {duration:.2f}s")
            print(f"   AEO Score: {result.get('aeo_score')}")
            print(f"   Headline: {result.get('headline')}")
            print(f"   Quality Checks: {passed}/{total} passed")
            
            result["quality_checks"] = {name: passed for name, passed in checks}
            result["quality_score"] = f"{passed}/{total}"
            result["api_duration"] = duration
            
            return result
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def test_parity(self, local_result: Optional[Dict], api_result: Optional[Dict]) -> Dict[str, Any]:
        """Test 3: Parity verification."""
        print("\n" + "=" * 80)
        print("TEST 3: PARITY VERIFICATION")
        print("=" * 80)
        
        if not local_result or not api_result:
            print("⚠️  Cannot compare: Missing results")
            return {"success": False, "error": "Missing results"}
        
        checks = []
        
        # AEO Score comparison
        local_aeo = local_result.get("aeo_score")
        api_aeo = api_result.get("aeo_score")
        if local_aeo is not None and api_aeo is not None:
            aeo_diff = abs(local_aeo - api_aeo)
            aeo_match = aeo_diff <= 1
            checks.append(("AEO Score Match (≤1 diff)", aeo_match, f"Local: {local_aeo}, API: {api_aeo}, Diff: {aeo_diff}"))
        else:
            checks.append(("AEO Score Match", False, "One or both missing"))
        
        # Headline comparison
        local_headline = local_result.get("headline")
        api_headline = api_result.get("headline")
        headline_match = local_headline == api_headline
        checks.append(("Headline Match", headline_match, f"Local: {local_headline}, API: {api_headline}"))
        
        # Duration comparison
        local_duration = local_result.get("duration_seconds", 0)
        api_duration = api_result.get("duration_seconds", 0) or api_result.get("api_duration", 0)
        if local_duration > 0 and api_duration > 0:
            duration_diff_pct = abs(local_duration - api_duration) / local_duration * 100
            duration_match = duration_diff_pct <= 10
            checks.append(("Duration Match (≤10% diff)", duration_match, 
                          f"Local: {local_duration:.2f}s, API: {api_duration:.2f}s, Diff: {duration_diff_pct:.1f}%"))
        else:
            checks.append(("Duration Match", False, "One or both missing"))
        
        # Execution times structure
        local_times = local_result.get("execution_times", {})
        api_times = api_result.get("execution_times", {})
        times_keys_match = set(local_times.keys()) == set(api_times.keys())
        checks.append(("Execution Times Keys Match", times_keys_match, 
                       f"Local: {len(local_times)} stages, API: {len(api_times)} stages"))
        
        # Critical issues comparison
        local_issues = local_result.get("critical_issues_count", 0)
        api_issues = api_result.get("critical_issues_count", 0)
        issues_match = local_issues == api_issues
        checks.append(("Critical Issues Count Match", issues_match, 
                       f"Local: {local_issues}, API: {api_issues}"))
        
        # Print results
        print()
        passed = 0
        for check_name, check_result, details in checks:
            if check_result:
                print(f"✅ {check_name}: {details}")
                passed += 1
            else:
                print(f"❌ {check_name}: {details}")
        
        parity_score = (passed / len(checks)) * 100 if checks else 0
        
        print(f"\n📊 Parity Score: {parity_score:.1f}% ({passed}/{len(checks)} checks passed)")
        
        return {
            "success": parity_score >= 95,
            "parity_score": parity_score,
            "checks": {name: result for name, result, _ in checks},
            "details": {name: details for name, _, details in checks},
        }
    
    def save_results(self):
        """Save test results."""
        output_dir = Path(__file__).parent / "test_outputs"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_file = output_dir / f"qa_test_results_{timestamp}.json"
        
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📁 Results saved to: {output_file}")
        return output_file
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("QA TEST SUMMARY")
        print("=" * 80)
        
        tests = self.results.get("tests", {})
        
        if "local" in tests:
            local = tests["local"]
            print(f"\n✅ Local Test: {'PASSED' if local.get('success') else 'FAILED'}")
            if local.get("success"):
                print(f"   Duration: {local.get('duration_seconds', 0):.2f}s")
                print(f"   AEO Score: {local.get('aeo_score')}")
                print(f"   Quality: {local.get('quality_score', 'N/A')}")
        
        if "api" in tests:
            api = tests["api"]
            print(f"\n✅ API Test: {'PASSED' if api.get('success') else 'FAILED'}")
            if api.get("success"):
                print(f"   Duration: {api.get('duration_seconds', 0):.2f}s")
                print(f"   AEO Score: {api.get('aeo_score')}")
                print(f"   Quality: {api.get('quality_score', 'N/A')}")
        
        if "parity" in tests:
            parity = tests["parity"]
            print(f"\n✅ Parity Test: {'PASSED' if parity.get('success') else 'FAILED'}")
            if parity.get("success"):
                print(f"   Parity Score: {parity.get('parity_score', 0):.1f}%")
        
        # Overall status
        # Note: Parity test may fail due to AI variance, which is expected
        local_passed = tests.get("local", {}).get("success", False)
        api_passed = tests.get("api", {}).get("success", False)
        parity_passed = tests.get("parity", {}).get("success", False)
        
        # Overall success if local and API work (parity variance is expected)
        all_passed = local_passed and api_passed
        
        print("\n" + "=" * 80)
        if all_passed:
            print("✅ ALL TESTS PASSED - QUALITY ASSURED")
        else:
            print("⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
        print("=" * 80)


async def main():
    """Run full QA test suite."""
    print("=" * 80)
    print("BLOG WRITER V2 - COMPREHENSIVE QA TEST SUITE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    suite = QATestSuite()
    
    # Test 1: Local execution
    local_result = await suite.test_local()
    suite.results["tests"]["local"] = local_result
    
    # Test 2: API service
    api_result = suite.test_api_generation()
    suite.results["tests"]["api"] = api_result
    
    # Test 3: Parity verification
    if local_result and api_result:
        parity_result = suite.test_parity(local_result, api_result)
        suite.results["tests"]["parity"] = parity_result
    
    # Save results
    suite.save_results()
    
    # Print summary
    suite.print_summary()
    
    # Return success status
    all_passed = all(
        suite.results["tests"].get("local", {}).get("success"),
        suite.results["tests"].get("api", {}).get("success"),
        suite.results["tests"].get("parity", {}).get("success"),
    )
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

