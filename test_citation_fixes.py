#!/usr/bin/env python3
"""
Citation Validation Fixes Test

Tests the improved citation validation system with:
1. Updated prompts with verified domains
2. Increased search timeout (12s → 20s)  
3. Enhanced authority domain database
4. Better cache invalidation (different TTL for failed URLs)

Expected results: Significant improvement in citation success rates.
"""

import asyncio
import json
import logging
import time
import httpx
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_citation_fixes():
    """Test citation validation with all fixes applied."""
    logger.info("🧪 Testing Citation Validation FIXES...")
    logger.info("=" * 80)
    logger.info("✅ Applied fixes:")
    logger.info("   • Updated prompts with verified domains only")
    logger.info("   • Increased Gemini timeout: 12s → 20s")
    logger.info("   • Enhanced authority domain database")
    logger.info("   • Better cache invalidation (failed URLs retry faster)")
    logger.info("=" * 80)
    
    # Test with same keywords as before for comparison
    test_keywords = [
        "AI in manufacturing",
        "Digital marketing automation", 
        "Cloud computing security"
    ]
    
    # Blog writer API endpoint
    api_endpoint = "https://clients--blog-writer-fastapi-app.modal.run"
    
    results = {}
    
    for i, keyword in enumerate(test_keywords):
        logger.info(f"Testing {i+1}/{len(test_keywords)}: {keyword}")
        
        # Create request payload with validation ENABLED (testing fixes)
        job_data = {
            "primary_keyword": keyword,
            "company_name": "SCAILE",
            "company_url": "https://scaile.tech",
            "language": "en",
            "company_data": {
                "description": "AI growth agency specializing in automation and optimization",
                "industry": "Technology Services",
                "target_audience": ["B2B companies seeking AI solutions"],
                "competitors": ["OpenAI", "Anthropic", "Jasper"]
            }
            # Citation validation enabled by default - testing the FIXED system
        }
        
        try:
            # Generate article
            start_time = time.time()
            async with httpx.AsyncClient(timeout=300.0) as client:
                logger.info(f"   📝 Generating article with FIXED validation system...")
                response = await client.post(f"{api_endpoint}/write", json=job_data)
                
                if response.status_code == 200:
                    generation_time = time.time() - start_time
                    article = response.json()
                    
                    # Analyze citation URLs
                    broken_citations, valid_citations = await analyze_citation_urls(article)
                    
                    results[keyword] = {
                        "success": True,
                        "generation_time": generation_time,
                        "total_citations": len(broken_citations) + len(valid_citations),
                        "broken_citations": len(broken_citations),
                        "valid_citations": len(valid_citations),
                        "citation_success_rate": len(valid_citations) / (len(broken_citations) + len(valid_citations)) * 100 if (len(broken_citations) + len(valid_citations)) > 0 else 0,
                        "broken_examples": broken_citations[:3],  # First 3 examples
                        "valid_examples": valid_citations[:3]   # First 3 examples
                    }
                    
                    logger.info(f"   ✅ Generated in {generation_time:.1f}s")
                    logger.info(f"   📊 Citations: {len(valid_citations)} valid, {len(broken_citations)} broken ({results[keyword]['citation_success_rate']:.1f}% success)")
                    
                else:
                    logger.error(f"   ❌ API error: {response.status_code}")
                    results[keyword] = {
                        "success": False, 
                        "error": f"HTTP {response.status_code}",
                        "generation_time": time.time() - start_time
                    }
                    
        except Exception as e:
            logger.error(f"   ❌ Exception: {e}")
            results[keyword] = {
                "success": False,
                "error": str(e),
                "generation_time": 0
            }
        
        logger.info("-" * 80)
    
    # Generate summary report
    generate_comparison_report(results)
    
    return results

async def analyze_citation_urls(article: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """Analyze citation URLs in the article to check which are broken."""
    logger.info("   🔍 Analyzing citation URLs...")
    
    # Extract citation URLs from literature field (list of dicts)
    citation_urls = []
    if "literature" in article and isinstance(article["literature"], list):
        for citation in article["literature"]:
            if isinstance(citation, dict) and "url" in citation:
                citation_urls.append(citation["url"])
    
    logger.info(f"   📋 Found {len(citation_urls)} citation URLs to validate")
    
    if not citation_urls:
        return [], []
    
    # Test each URL with HTTP HEAD
    broken_citations = []
    valid_citations = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in citation_urls:
            try:
                # Quick HTTP HEAD check
                response = await client.head(url, follow_redirects=True)
                if response.status_code == 200:
                    valid_citations.append(url)
                else:
                    broken_citations.append(f"{url} -> HTTP {response.status_code}")
            except httpx.TimeoutException:
                broken_citations.append(f"{url} -> Timeout")
            except httpx.RequestError as e:
                broken_citations.append(f"{url} -> {str(e)}")
            except Exception as e:
                broken_citations.append(f"{url} -> {str(e)}")
    
    return broken_citations, valid_citations

def generate_comparison_report(results: Dict[str, Any]):
    """Generate and save a comparison test report."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Calculate overall metrics
    successful_tests = sum(1 for r in results.values() if r.get("success", False))
    total_tests = len(results)
    
    if successful_tests > 0:
        avg_generation_time = sum(r["generation_time"] for r in results.values() if r.get("success", False)) / successful_tests
        avg_citation_success = sum(r["citation_success_rate"] for r in results.values() if r.get("success", False)) / successful_tests
        total_citations = sum(r["total_citations"] for r in results.values() if r.get("success", False))
        total_valid = sum(r["valid_citations"] for r in results.values() if r.get("success", False))
        total_broken = sum(r["broken_citations"] for r in results.values() if r.get("success", False))
    else:
        avg_generation_time = 0
        avg_citation_success = 0
        total_citations = 0
        total_valid = 0
        total_broken = 0
    
    report = {
        "test_metadata": {
            "timestamp": timestamp,
            "test_type": "Citation Validation FIXES Test",
            "keywords_tested": total_tests,
            "successful_tests": successful_tests,
            "fixes_applied": [
                "Updated prompts with verified domains only",
                "Increased Gemini timeout: 12s → 20s", 
                "Enhanced authority domain database",
                "Better cache invalidation (failed URLs retry faster)"
            ]
        },
        "citation_metrics": {
            "average_generation_time": avg_generation_time,
            "average_citation_success_rate": avg_citation_success,
            "total_citations_tested": total_citations,
            "total_valid_citations": total_valid,
            "total_broken_citations": total_broken,
            "overall_citation_success_rate": (total_valid / total_citations * 100) if total_citations > 0 else 0
        },
        "detailed_results": results
    }
    
    # Save report
    report_filename = f"citation_fixes_report_{timestamp}.json"
    with open(report_filename, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    logger.info("📊 CITATION FIXES TEST RESULTS:")
    logger.info("=" * 80)
    logger.info(f"Tests completed: {successful_tests}/{total_tests}")
    if successful_tests > 0:
        logger.info(f"Average generation time: {avg_generation_time:.1f}s")
        logger.info(f"Citation success rate: {avg_citation_success:.1f}%")
        logger.info(f"Total citations tested: {total_citations}")
        logger.info(f"Valid citations: {total_valid}")
        logger.info(f"Broken citations: {total_broken}")
        logger.info(f"Overall citation success: {total_valid}/{total_citations} ({report['citation_metrics']['overall_citation_success_rate']:.1f}%)")
    logger.info(f"📁 Full report saved: {report_filename}")
    
    # Compare to previous test results
    previous_results = {
        "with_validation_enabled": 14.4,  # From previous test
        "with_validation_disabled": 22.7, # From previous test
        "baseline": 43                     # From original baseline
    }
    
    current_success = report['citation_metrics']['overall_citation_success_rate']
    
    logger.info("-" * 80)
    logger.info(f"📈 IMPROVEMENT COMPARISON:")
    logger.info(f"Original baseline: {previous_results['baseline']}%")
    logger.info(f"Validation disabled: {previous_results['with_validation_disabled']}%") 
    logger.info(f"Validation enabled (before fixes): {previous_results['with_validation_enabled']}%")
    logger.info(f"Validation enabled (AFTER fixes): {current_success:.1f}%")
    
    improvement_vs_broken = current_success - previous_results['with_validation_enabled']
    improvement_vs_disabled = current_success - previous_results['with_validation_disabled']
    improvement_vs_baseline = current_success - previous_results['baseline']
    
    logger.info("-" * 40)
    logger.info(f"🚀 IMPROVEMENTS:")
    logger.info(f"vs Broken validation: {improvement_vs_broken:+.1f} percentage points")
    logger.info(f"vs Disabled validation: {improvement_vs_disabled:+.1f} percentage points")  
    logger.info(f"vs Original baseline: {improvement_vs_baseline:+.1f} percentage points")
    
    # Success assessment
    if current_success >= 75:
        logger.info("🎉 EXCELLENT - Citation validation fixes working very well!")
    elif current_success >= 50:
        logger.info("✅ GOOD - Significant improvement, validation system now helpful")
    elif current_success >= 30:
        logger.info("⚠️  MODERATE - Some improvement but more work needed")
    else:
        logger.info("❌ POOR - Fixes didn't work, need different approach")

if __name__ == "__main__":
    asyncio.run(test_citation_fixes())