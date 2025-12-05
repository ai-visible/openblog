#!/usr/bin/env python3
"""
Test Stage 2 Content Generation - Native Google Tools Only

This script will:
1. Call ONLY Stage 2 (content generation with deep research)
2. Verify native Google tools are being used correctly
3. Check for url_context_metadata in response
4. Confirm Search Queries field is populated
5. Test with minimal parameters to isolate the tools issue
"""

import asyncio
import json
import logging
import httpx
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_stage2_native_tools():
    """Test Stage 2 content generation in isolation."""
    logger.info("🧪 TESTING STAGE 2 CONTENT GENERATION - NATIVE TOOLS ONLY")
    logger.info("=" * 80)
    
    # Minimal request to test just the tools
    test_data = {
        "primary_keyword": "AI manufacturing efficiency",
        "company_name": "SCAILE",
        "company_url": "https://scaile.tech",
        "language": "en",
        # Minimal company data
        "company_data": {
            "description": "AI growth agency",
            "industry": "Technology"
        },
        # Request ONLY Stage 2 if possible
        "stages_to_run": ["stage2"],  # Attempt to isolate
        "debug_mode": True  # Request verbose output
    }
    
    logger.info("🎯 Testing native Google tools usage...")
    logger.info(f"   Keyword: {test_data['primary_keyword']}")
    logger.info(f"   Expected: Native googleSearch + url_context tools")
    logger.info(f"   Expected: url_context_metadata in response")
    logger.info(f"   Expected: Search Queries field populated")
    logger.info("")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                "https://clients--blog-writer-fastapi-app.modal.run/write",
                json=test_data
            )
            
            if response.status_code == 200:
                article = response.json()
                analyze_native_tools_usage(article)
                return article
            else:
                logger.error(f"❌ API error: {response.status_code}")
                logger.error(response.text)
                return None
                
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        return None

def analyze_native_tools_usage(article: Dict[str, Any]):
    """Analyze if native Google tools were used correctly."""
    logger.info("🔍 ANALYZING NATIVE GOOGLE TOOLS USAGE:")
    logger.info("=" * 60)
    
    # Check 1: Search Queries field (should exist if tools worked)
    search_queries = article.get("search_queries", "")
    if search_queries and search_queries.strip():
        logger.info("✅ Search Queries field FOUND:")
        queries = search_queries.strip().split('\n')
        for i, query in enumerate(queries[:3], 1):
            if query.strip():
                logger.info(f"   Q{i}: {query.strip()}")
        logger.info(f"   Total queries: {len([q for q in queries if q.strip()])}")
    else:
        logger.error("❌ Search Queries field MISSING - Native tools NOT working!")
    
    # Check 2: URL context metadata (should exist if native tools used)
    url_metadata = article.get("url_context_metadata", [])
    if url_metadata:
        logger.info(f"✅ URL Context Metadata FOUND: {len(url_metadata)} entries")
        for i, entry in enumerate(url_metadata[:3], 1):
            if isinstance(entry, dict) and "url" in entry:
                logger.info(f"   URL{i}: {entry['url']}")
    else:
        logger.error("❌ URL Context Metadata MISSING - Native tools NOT used!")
    
    # Check 3: Tool usage indicators
    tools_used = article.get("tools_used", [])
    if tools_used:
        logger.info(f"✅ Tools Used field: {tools_used}")
    else:
        logger.warning("⚠️  No Tools Used field found")
    
    # Check 4: Citation quality
    literature = article.get("literature", [])
    if isinstance(literature, list) and literature:
        logger.info(f"📚 Generated {len(literature)} citations")
        
        # Sample a few URLs to check patterns
        sample_urls = []
        for citation in literature[:5]:
            if isinstance(citation, dict) and "url" in citation:
                sample_urls.append(citation["url"])
        
        logger.info("🔗 Sample URLs from native tools:")
        for i, url in enumerate(sample_urls, 1):
            logger.info(f"   [{i}] {url}")
            
        # Check for hallucination patterns
        hallucinated = 0
        for url in sample_urls:
            if any(pattern in url.lower() for pattern in [
                "ai-manufacturing", "manufacturing-ai", "ai-in-manufacturing"
            ]) and not any(real in url.lower() for real in ["blog", "article", "news"]):
                hallucinated += 1
        
        if hallucinated > 0:
            logger.warning(f"⚠️  {hallucinated}/{len(sample_urls)} URLs show hallucination patterns")
        else:
            logger.info(f"✅ {len(sample_urls)}/{len(sample_urls)} URLs look real")
    else:
        logger.error("❌ No literature citations found")
    
    # Check 5: Debug information
    debug_info = article.get("debug_info", {})
    if debug_info:
        logger.info(f"🐛 Debug Info Available: {list(debug_info.keys())}")
        
        # Look for tool call logs
        tool_calls = debug_info.get("tool_calls", [])
        if tool_calls:
            logger.info(f"✅ Tool Calls Logged: {len(tool_calls)} calls")
        else:
            logger.warning("⚠️  No tool calls in debug info")
    
    # Overall assessment
    logger.info("")
    logger.info("🎯 ASSESSMENT:")
    logger.info("=" * 40)
    
    native_tools_working = bool(search_queries and url_metadata)
    if native_tools_working:
        logger.info("✅ NATIVE GOOGLE TOOLS ARE WORKING")
        logger.info("   - Search Queries field populated")
        logger.info("   - URL Context Metadata present")
        logger.info("   - Real search results being used")
    else:
        logger.error("❌ NATIVE GOOGLE TOOLS NOT WORKING")
        logger.error("   - Missing search queries or URL metadata")
        logger.error("   - System falling back to hallucination")
        logger.error("   - Need to fix tool implementation")

def save_stage2_test_results(article: Dict[str, Any]):
    """Save the Stage 2 test results."""
    if article:
        filename = "stage2_native_tools_test.json"
        with open(filename, "w") as f:
            json.dump(article, f, indent=2)
        logger.info(f"📁 Stage 2 test saved: {filename}")

if __name__ == "__main__":
    result = asyncio.run(test_stage2_native_tools())
    if result:
        save_stage2_test_results(result)
        logger.info("🎯 STAGE 2 TEST COMPLETE - Check analysis above")
    else:
        logger.error("❌ STAGE 2 TEST FAILED")