#!/usr/bin/env python3
"""Test why the validator is returning 404 URLs."""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env first
env_local = Path('.env.local')
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path.cwd()))

from pipeline.processors.url_validator import CitationURLValidator
from pipeline.models.gemini_client import GeminiClient
from pipeline.config import Config

async def test_validation():
    """Test validation on the actual problematic URLs."""
    
    # URLs from the generated article that are 404
    bad_urls = [
        ("https://masterofcode.com/blog/ai-customer-service-statistics", "AI customer service statistics"),
        ("https://www.sobot.io/blog/ai-adoption-in-customer-service-statistics", "AI adoption statistics"),
        ("https://resourcera.com/ai-customer-service-statistics/", "AI customer service stats"),
    ]
    
    print("=" * 80)
    print("TESTING VALIDATOR ON FAILED URLS")
    print("=" * 80)
    print()
    
    config = Config()
    gemini = GeminiClient(api_key=config.google_api_key)
    validator = CitationURLValidator(gemini_client=gemini, config=config)
    
    for url, title in bad_urls:
        print(f"Testing: {url}")
        print(f"Title: {title}")
        print()
        
        # Test URL validation
        is_valid, final_url, final_title = await validator.validate_citation_url(
            url=url,
            title=title,
            company_url="https://example.com",
            competitors=[],
            language="en"
        )
        
        print(f"Result:")
        print(f"  Valid: {is_valid}")
        print(f"  Final URL: {final_url}")
        print(f"  Final Title: {final_title}")
        print()
        
        # Check if the "fixed" URL is actually valid
        if final_url != url:
            print("URL was replaced! Checking new URL...")
            import httpx
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                try:
                    response = await client.head(final_url, timeout=8.0)
                    print(f"  New URL Status: {response.status_code}")
                    if response.status_code == 404:
                        print(f"  ❌ REPLACEMENT URL IS ALSO 404!")
                except Exception as e:
                    print(f"  ❌ Error checking new URL: {e}")
        print()
        print("-" * 80)
        print()

asyncio.run(test_validation())
