#!/usr/bin/env python3
"""
Citation Validation Test Script

Tests the citation validation system with HTTP HEAD validation to fix broken links.
This addresses the 85 broken citations found in baseline testing.

Run this script to test citation validation with 3 articles.
"""

import asyncio
import json
import logging
import os
import time
import httpx
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_citation_validation():
    """Test citation validation with actual API calls."""
    logger.info("🧪 Testing Citation URL Validation System...")
    logger.info("=" * 80)
    
    # Test with 3 keywords to validate citations
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
        
        # Create request payload
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
        }
        
        # Make sure citation validation is EXPLICITLY enabled
        job_data["citation_validation_enabled"] = True
        
        try:
            # Generate article
            start_time = time.time()
            async with httpx.AsyncClient(timeout=300.0) as client:
                logger.info(f"   📝 Generating article with citation validation enabled...")
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
                        "broken_examples": broken_citations[:5],  # First 5 examples
                        "valid_examples": valid_citations[:5]   # First 5 examples
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
    generate_validation_report(results)
    
    return results

async def analyze_citation_urls(article: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """Analyze citation URLs in the article to check which are broken."""
    logger.info("   🔍 Analyzing citation URLs...")
    
    # Extract citation URLs from literature field (now a list of dicts)
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

def generate_validation_report(results: Dict[str, Any]):
    """Generate and save a validation test report."""
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
            "test_type": "Citation Validation Test",
            "keywords_tested": total_tests,
            "successful_tests": successful_tests
        },
        "validation_metrics": {
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
    report_filename = f"citation_validation_report_{timestamp}.json"
    with open(report_filename, "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    logger.info("📊 CITATION VALIDATION TEST RESULTS:")
    logger.info("=" * 80)
    logger.info(f"Tests completed: {successful_tests}/{total_tests}")
    if successful_tests > 0:
        logger.info(f"Average generation time: {avg_generation_time:.1f}s")
        logger.info(f"Citation success rate: {avg_citation_success:.1f}%")
        logger.info(f"Total citations tested: {total_citations}")
        logger.info(f"Valid citations: {total_valid}")
        logger.info(f"Broken citations: {total_broken}")
        logger.info(f"Overall citation success: {total_valid}/{total_citations} ({report['validation_metrics']['overall_citation_success_rate']:.1f}%)")
    logger.info(f"📁 Full report saved: {report_filename}")
    
    # Compare to baseline
    baseline_citation_success = 43  # From baseline: ~57% broken = 43% success  
    current_success = report['validation_metrics']['overall_citation_success_rate']
    improvement = current_success - baseline_citation_success
    
    logger.info("-" * 80)
    logger.info(f"📈 COMPARISON TO BASELINE:")
    logger.info(f"Baseline citation success rate: {baseline_citation_success}%")
    logger.info(f"Current citation success rate: {current_success:.1f}%")
    logger.info(f"Improvement: {improvement:+.1f} percentage points")
    
    if improvement > 20:
        logger.info("🎉 MAJOR IMPROVEMENT - Citation validation working effectively!")
    elif improvement > 5:
        logger.info("✅ Good improvement - Citation validation helping")
    elif improvement > -5:
        logger.info("⚠️  Similar performance - Validation may not be fully enabled")
    else:
        logger.info("❌ Worse performance - Validation system may have issues")

if __name__ == "__main__":
    # Set environment variables to ensure validation is enabled
    os.environ["ENABLE_CITATION_VALIDATION"] = "true"
    os.environ["CITATION_VALIDATION_TIMEOUT"] = "8.0"
    os.environ["MAX_VALIDATION_ATTEMPTS"] = "10"
    
    asyncio.run(test_citation_validation())