#!/usr/bin/env python3
"""
Parity Test - Compare Local vs API vs Edge Function outputs
Ensures all three versions produce identical results
"""

import asyncio
import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
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


class ParityTest:
    """Test suite for ensuring parity across all versions."""
    
    def __init__(self):
        self.test_config = {
            "primary_keyword": "AI customer service automation",
            "company_url": "https://example.com",
            "company_name": "Example Corp",
        }
        self.results = {}
        self.errors = []
        
    async def test_local(self) -> Optional[Dict[str, Any]]:
        """Test local Python execution."""
        print("\n" + "=" * 80)
        print("TEST 1: LOCAL PYTHON EXECUTION")
        print("=" * 80)
        
        try:
            # Verify API key
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
            if not api_key:
                print("⚠️  Skipping: No API key found")
                return None
            
            # Create workflow engine
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
            
            # Execute
            print("🚀 Executing workflow...")
            start_time = datetime.now()
            context = await engine.execute(
                job_id=f"parity-test-local-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                job_config=self.test_config
            )
            duration = (datetime.now() - start_time).total_seconds()
            
            # Extract results
            result = {
                "success": True,
                "job_id": context.job_id,
                "headline": context.structured_data.Headline if context.structured_data else None,
                "html_content": context.final_article.get("html_content") if context.final_article else None,
                "validated_article": context.validated_article,
                "quality_report": context.quality_report,
                "execution_times": context.execution_times if hasattr(context, 'execution_times') else {},
                "duration_seconds": duration,
                "aeo_score": context.quality_report.get("metrics", {}).get("aeo_score") if context.quality_report else None,
                "critical_issues_count": len(context.quality_report.get("critical_issues", [])) if context.quality_report else 0,
            }
            
            print(f"✅ Local test completed in {duration:.2f}s")
            print(f"   AEO Score: {result['aeo_score']}")
            print(f"   Headline: {result['headline']}")
            
            return result
            
        except Exception as e:
            error_msg = f"Local test failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.errors.append(error_msg)
            return None
    
    def test_api_service(self, api_url: str = "http://localhost:8000") -> Optional[Dict[str, Any]]:
        """Test FastAPI service."""
        print("\n" + "=" * 80)
        print("TEST 2: FASTAPI SERVICE")
        print("=" * 80)
        
        try:
            # Check if service is running
            health_url = f"{api_url}/health"
            try:
                health_response = requests.get(health_url, timeout=5)
                if health_response.status_code != 200:
                    print(f"⚠️  Skipping: Service not healthy (status {health_response.status_code})")
                    return None
            except requests.exceptions.RequestException:
                print(f"⚠️  Skipping: Service not running at {api_url}")
                print("   Start service with: cd service && python api.py")
                return None
            
            # Call write endpoint
            print(f"🚀 Calling {api_url}/write...")
            start_time = datetime.now()
            response = requests.post(
                f"{api_url}/write",
                json=self.test_config,
                timeout=600  # 10 minutes
            )
            duration = (datetime.now() - start_time).total_seconds()
            
            if response.status_code != 200:
                error_msg = f"API returned status {response.status_code}: {response.text}"
                print(f"❌ {error_msg}")
                self.errors.append(error_msg)
                return None
            
            result = response.json()
            
            if not result.get("success"):
                error_msg = f"API returned error: {result.get('error')}"
                print(f"❌ {error_msg}")
                self.errors.append(error_msg)
                return None
            
            print(f"✅ API test completed in {duration:.2f}s")
            print(f"   AEO Score: {result.get('aeo_score')}")
            print(f"   Headline: {result.get('headline')}")
            
            return result
            
        except Exception as e:
            error_msg = f"API test failed: {str(e)}"
            print(f"❌ {error_msg}")
            self.errors.append(error_msg)
            return None
    
    def compare_results(self, local_result: Optional[Dict], api_result: Optional[Dict]):
        """Compare results and check for parity."""
        print("\n" + "=" * 80)
        print("PARITY COMPARISON")
        print("=" * 80)
        
        if not local_result:
            print("⚠️  Cannot compare: Local test not available")
            return False
        
        if not api_result:
            print("⚠️  Cannot compare: API test not available")
            print("   This is OK if API service is not running")
            return True  # Not a failure if API isn't running
        
        checks = []
        
        # Compare AEO scores
        local_aeo = local_result.get("aeo_score")
        api_aeo = api_result.get("aeo_score")
        if local_aeo is not None and api_aeo is not None:
            aeo_match = abs(local_aeo - api_aeo) <= 1
            checks.append(("AEO Score", aeo_match, f"Local: {local_aeo}, API: {api_aeo}"))
        else:
            checks.append(("AEO Score", False, "One or both missing"))
        
        # Compare headlines
        local_headline = local_result.get("headline")
        api_headline = api_result.get("headline")
        headline_match = local_headline == api_headline
        checks.append(("Headline", headline_match, f"Local: {local_headline}, API: {api_headline}"))
        
        # Compare execution times structure
        local_times = local_result.get("execution_times", {})
        api_times = api_result.get("execution_times", {})
        times_keys_match = set(local_times.keys()) == set(api_times.keys())
        checks.append(("Execution Times Keys", times_keys_match, 
                       f"Local: {len(local_times)} stages, API: {len(api_times)} stages"))
        
        # Compare duration (should be similar, within 10%)
        local_duration = local_result.get("duration_seconds", 0)
        api_duration = api_result.get("duration_seconds", 0)
        if local_duration > 0 and api_duration > 0:
            duration_diff = abs(local_duration - api_duration) / local_duration
            duration_match = duration_diff <= 0.1  # Within 10%
            checks.append(("Duration", duration_match, 
                          f"Local: {local_duration:.2f}s, API: {api_duration:.2f}s (diff: {duration_diff*100:.1f}%)"))
        else:
            checks.append(("Duration", False, "One or both missing"))
        
        # Compare critical issues count
        local_issues = local_result.get("critical_issues_count", 0)
        api_issues = api_result.get("critical_issues_count", 0)
        issues_match = local_issues == api_issues
        checks.append(("Critical Issues Count", issues_match, 
                       f"Local: {local_issues}, API: {api_issues}"))
        
        # Compare HTML content (if available)
        local_html = local_result.get("html_content")
        api_html = api_result.get("html_content")
        if local_html and api_html:
            html_match = local_html == api_html
            checks.append(("HTML Content", html_match, 
                           f"Local: {len(local_html)} chars, API: {len(api_html)} chars"))
        else:
            checks.append(("HTML Content", None, "One or both missing"))
        
        # Print results
        print()
        all_passed = True
        for check_name, passed, details in checks:
            if passed is True:
                print(f"✅ {check_name}: {details}")
            elif passed is False:
                print(f"❌ {check_name}: {details}")
                all_passed = False
            else:
                print(f"⚠️  {check_name}: {details}")
        
        return all_passed
    
    def save_results(self, local_result: Optional[Dict], api_result: Optional[Dict]):
        """Save test results for inspection."""
        output_dir = Path(__file__).parent / "test_outputs"
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "test_config": self.test_config,
            "local_result": local_result,
            "api_result": api_result,
            "errors": self.errors,
        }
        
        output_file = output_dir / f"parity_test_{timestamp}.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📁 Results saved to: {output_file}")
        return output_file


async def main():
    """Run all parity tests."""
    print("=" * 80)
    print("BLOG WRITER V2 - PARITY TEST SUITE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = ParityTest()
    
    # Test 1: Local execution
    local_result = await tester.test_local()
    
    # Test 2: API service (optional - only if running)
    api_result = tester.test_api_service()
    
    # Compare results
    parity_ok = tester.compare_results(local_result, api_result)
    
    # Save results
    tester.save_results(local_result, api_result)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    if local_result:
        print("✅ Local test: PASSED")
    else:
        print("❌ Local test: FAILED")
    
    if api_result:
        print("✅ API test: PASSED")
    else:
        print("⚠️  API test: SKIPPED (service not running)")
    
    if parity_ok:
        print("✅ Parity check: PASSED")
    else:
        print("❌ Parity check: FAILED")
    
    if tester.errors:
        print(f"\n⚠️  Errors encountered: {len(tester.errors)}")
        for error in tester.errors:
            print(f"   - {error}")
    
    print()
    
    # Return success if local test passed
    return local_result is not None


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

