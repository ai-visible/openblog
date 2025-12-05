#!/usr/bin/env python3
"""
Step 2: Test Raw URLs Before Validation

Extract URLs from the raw article (Stage 2 output) and test them BEFORE
any validation or processing. This will show us the true success rate 
of URLs as they come from Gemini's tool usage.
"""

import asyncio
import json
import logging
import httpx
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_raw_urls_before_validation():
    """Test URLs as they come out of Stage 2 (before any validation)."""
    logger.info("🔍 STEP 2: Testing Raw URLs Before Validation")
    logger.info("=" * 80)
    
    # Load the raw article from Step 1
    try:
        with open("debug_tools_article.json", "r") as f:
            article = json.load(f)
    except FileNotFoundError:
        logger.error("❌ debug_tools_article.json not found. Run debug_tools_working.py first.")
        return
    
    # Extract literature URLs (these are raw from Stage 2)
    literature = article.get("literature", [])
    if not literature:
        logger.error("❌ No literature found in article")
        return
    
    logger.info(f"📋 Found {len(literature)} citations from Stage 2 (raw, before validation)")
    logger.info("🧪 Testing each URL with HTTP HEAD...")
    
    # Test each URL
    results = []
    async with httpx.AsyncClient(timeout=10.0) as client:
        for citation in literature:
            if isinstance(citation, dict) and "url" in citation:
                url = citation["url"]
                number = citation.get("number", "?")
                description = citation.get("description", "")
                
                try:
                    response = await client.head(url, follow_redirects=True)
                    is_valid = response.status_code == 200
                    status = f"HTTP {response.status_code}"
                    
                    results.append({
                        "number": number,
                        "url": url,
                        "description": description,
                        "valid": is_valid,
                        "status": status
                    })
                    
                    status_icon = "✅" if is_valid else "❌"
                    logger.info(f"   [{number}] {status_icon} {status}: {url}")
                    
                except httpx.TimeoutException:
                    results.append({
                        "number": number,
                        "url": url,
                        "description": description,
                        "valid": False,
                        "status": "Timeout"
                    })
                    logger.info(f"   [{number}] ⏱️  Timeout: {url}")
                    
                except httpx.RequestError as e:
                    results.append({
                        "number": number,
                        "url": url,
                        "description": description,
                        "valid": False,
                        "status": str(e)
                    })
                    logger.info(f"   [{number}] ❌ Error: {url}")
    
    # Calculate statistics
    total_urls = len(results)
    valid_urls = sum(1 for r in results if r["valid"])
    invalid_urls = total_urls - valid_urls
    success_rate = (valid_urls / total_urls) * 100 if total_urls > 0 else 0
    
    logger.info("=" * 80)
    logger.info("📊 STEP 2 RESULTS:")
    logger.info(f"   Total URLs: {total_urls}")
    logger.info(f"   Valid URLs: {valid_urls}")
    logger.info(f"   Invalid URLs: {invalid_urls}")
    logger.info(f"   Success Rate: {success_rate:.1f}%")
    
    # Analyze by domain
    analyze_by_domain(results)
    
    # Show examples
    show_examples(results)
    
    # Save results for comparison
    save_results(results, success_rate)
    
    return results, success_rate

def analyze_by_domain(results: List[dict]):
    """Analyze success rates by domain."""
    logger.info("🌐 SUCCESS RATES BY DOMAIN:")
    
    domain_stats = {}
    for result in results:
        url = result["url"]
        # Extract domain
        import re
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if domain_match:
            domain = domain_match.group(1)
            if domain not in domain_stats:
                domain_stats[domain] = {"total": 0, "valid": 0}
            domain_stats[domain]["total"] += 1
            if result["valid"]:
                domain_stats[domain]["valid"] += 1
    
    # Sort by total URLs
    sorted_domains = sorted(domain_stats.items(), key=lambda x: x[1]["total"], reverse=True)
    
    for domain, stats in sorted_domains[:15]:  # Top 15 domains
        success_rate = (stats["valid"] / stats["total"]) * 100
        status = "✅" if success_rate > 50 else "⚠️" if success_rate > 0 else "❌"
        logger.info(f"   {status} {domain}: {stats['valid']}/{stats['total']} ({success_rate:.0f}%)")

def show_examples(results: List[dict]):
    """Show examples of working vs broken URLs."""
    logger.info("💡 EXAMPLES:")
    
    # Working URLs
    working = [r for r in results if r["valid"]]
    if working:
        logger.info("✅ Working URLs (examples):")
        for example in working[:5]:
            logger.info(f"   {example['url']}")
    
    # Broken URLs
    broken = [r for r in results if not r["valid"]]
    if broken:
        logger.info("❌ Broken URLs (examples):")
        for example in broken[:5]:
            logger.info(f"   {example['url']} -> {example['status']}")

def save_results(results: List[dict], success_rate: float):
    """Save results for comparison with validation."""
    summary = {
        "test_type": "Raw URLs Before Validation (Stage 2 Output)",
        "timestamp": "2025-12-03",
        "total_urls": len(results),
        "valid_urls": sum(1 for r in results if r["valid"]),
        "success_rate": success_rate,
        "detailed_results": results
    }
    
    with open("raw_urls_test_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info("📁 Results saved: raw_urls_test_results.json")

if __name__ == "__main__":
    asyncio.run(test_raw_urls_before_validation())