#!/usr/bin/env python3
"""
Debug Tools Functionality

Step 1 of issue isolation: Check if googleSearch + urlContext tools are actually working
during content generation in Stage 2.

This script will:
1. Generate 1 test article with verbose logging
2. Examine logs for evidence of tool calls
3. Check raw article output for search results vs hallucinations
"""

import asyncio
import json
import logging
import httpx
import re
from typing import Dict, Any

# Setup verbose logging to catch tool calls
logging.basicConfig(
    level=logging.DEBUG,  # Capture all log levels
    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_tools_functionality():
    """Debug if web search tools are working during content generation."""
    logger.info("🔍 STEP 1: Debugging Web Search Tools Functionality")
    logger.info("=" * 80)
    
    # Test with a simple keyword
    test_keyword = "AI in manufacturing"
    
    # Create request payload
    job_data = {
        "primary_keyword": test_keyword,
        "company_name": "SCAILE",
        "company_url": "https://scaile.tech", 
        "language": "en",
        "company_data": {
            "description": "AI growth agency",
            "industry": "Technology Services",
            "target_audience": ["B2B companies"],
            "competitors": ["OpenAI"]
        }
    }
    
    logger.info(f"🧪 Testing tools functionality with keyword: {test_keyword}")
    logger.info("📝 Generating article and monitoring for tool calls...")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                "https://clients--blog-writer-fastapi-app.modal.run/write",
                json=job_data
            )
            
            if response.status_code == 200:
                article = response.json()
                
                # Analyze the response for tool usage evidence
                analyze_tool_usage(article)
                
                # Analyze the URLs for search vs hallucination patterns
                analyze_url_patterns(article)
                
                return article
            else:
                logger.error(f"❌ API error: {response.status_code}")
                logger.error(response.text)
                return None
                
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        return None

def analyze_tool_usage(article: Dict[str, Any]):
    """Analyze the article response for evidence of tool usage."""
    logger.info("🔍 ANALYZING TOOL USAGE EVIDENCE:")
    logger.info("=" * 60)
    
    # Check if there are search queries in the article
    search_queries = article.get("search_queries", "")
    if search_queries:
        logger.info("✅ Search Queries field found:")
        queries = search_queries.split('\n')
        for i, query in enumerate(queries[:5], 1):  # Show first 5
            if query.strip():
                logger.info(f"   Q{i}: {query.strip()}")
        logger.info(f"   Total queries: {len([q for q in queries if q.strip()])}")
    else:
        logger.warning("⚠️  No Search Queries field found")
    
    # Check if citations look like they came from searches vs hallucinations
    literature = article.get("literature", [])
    if isinstance(literature, list) and literature:
        logger.info(f"📚 Found {len(literature)} citations to analyze")
        
        # Look for patterns that suggest real vs fake URLs
        real_patterns = 0
        fake_patterns = 0
        
        for citation in literature:
            if isinstance(citation, dict) and "url" in citation:
                url = citation["url"]
                description = citation.get("description", "")
                
                # Patterns suggesting real search results
                if any(pattern in url.lower() for pattern in [
                    "/article/", "/news/", "/blog/", "/research/", "/report/",
                    "/publications/", "/insights/", "/studies/"
                ]):
                    real_patterns += 1
                
                # Patterns suggesting hallucination
                if any(pattern in url.lower() for pattern in [
                    "ai-in-manufacturing", "manufacturing-ai", "artificial-intelligence-manufacturing"
                ]) and not any(real in url.lower() for real in ["article", "blog", "news"]):
                    fake_patterns += 1
        
        logger.info(f"🔍 URL Pattern Analysis:")
        logger.info(f"   Real-looking URLs: {real_patterns}")
        logger.info(f"   Fake-looking URLs: {fake_patterns}")
        logger.info(f"   Ratio: {real_patterns/(real_patterns+fake_patterns)*100:.1f}% real-looking")
        
    else:
        logger.warning("⚠️  No literature field found or empty")

def analyze_url_patterns(article: Dict[str, Any]):
    """Analyze URL patterns to determine if they're from search or hallucinated."""
    logger.info("🔗 ANALYZING URL PATTERNS:")
    logger.info("=" * 60)
    
    literature = article.get("literature", [])
    if not isinstance(literature, list):
        logger.warning("⚠️  Literature is not a list")
        return
    
    if not literature:
        logger.warning("⚠️  No citations found")
        return
    
    # Analyze domains
    domains = {}
    suspicious_patterns = []
    
    for citation in literature:
        if isinstance(citation, dict) and "url" in citation:
            url = citation["url"]
            description = citation.get("description", "")
            
            # Extract domain
            domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if domain_match:
                domain = domain_match.group(1)
                domains[domain] = domains.get(domain, 0) + 1
            
            # Check for suspicious patterns
            if "ai-in-manufacturing" in url.lower():
                suspicious_patterns.append(f"Keyword stuffed URL: {url}")
            
            # Check for obviously fake paths
            if re.search(r'/\d{4}/\d{2}/\d{2}/', url) and "blog" not in url:
                suspicious_patterns.append(f"Fake date pattern: {url}")
    
    # Report findings
    logger.info(f"📊 Domain Distribution (Top 10):")
    sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)
    for domain, count in sorted_domains[:10]:
        logger.info(f"   {domain}: {count} URLs")
    
    if suspicious_patterns:
        logger.warning(f"🚨 Suspicious URL Patterns Found ({len(suspicious_patterns)}):")
        for pattern in suspicious_patterns[:5]:  # Show first 5
            logger.warning(f"   {pattern}")
    
    # Overall assessment
    total_urls = len(literature)
    unique_domains = len(domains)
    avg_urls_per_domain = total_urls / unique_domains if unique_domains > 0 else 0
    
    logger.info(f"📈 SUMMARY:")
    logger.info(f"   Total URLs: {total_urls}")
    logger.info(f"   Unique domains: {unique_domains}")
    logger.info(f"   Avg URLs per domain: {avg_urls_per_domain:.1f}")
    logger.info(f"   Suspicious patterns: {len(suspicious_patterns)}")
    
    # Assessment
    if avg_urls_per_domain > 3:
        logger.warning("⚠️  HIGH repetition per domain - suggests limited search diversity")
    
    if len(suspicious_patterns) > total_urls * 0.3:
        logger.error("🚨 HIGH fake pattern rate - tools likely not working properly")
    elif len(suspicious_patterns) > 0:
        logger.warning("⚠️  SOME fake patterns - tools may be partially working")
    else:
        logger.info("✅ LOW fake pattern rate - tools appear to be working")

def save_debug_results(article: Dict[str, Any]):
    """Save the debug results for further analysis."""
    if article:
        filename = f"debug_tools_article.json"
        with open(filename, "w") as f:
            json.dump(article, f, indent=2)
        logger.info(f"📁 Debug article saved: {filename}")

if __name__ == "__main__":
    result = asyncio.run(debug_tools_functionality())
    if result:
        save_debug_results(result)
        logger.info("🎯 STEP 1 COMPLETE - Check logs above for tool usage evidence")
    else:
        logger.error("❌ STEP 1 FAILED - Could not generate test article")