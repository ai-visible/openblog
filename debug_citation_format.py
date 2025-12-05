#!/usr/bin/env python3
"""
Debug Citation Format

Analyzes the actual format of citations returned by the API.
"""

import asyncio
import json
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_citation_format():
    """Debug the actual citation format from API."""
    
    # Test with 1 keyword
    job_data = {
        "primary_keyword": "AI in manufacturing",
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
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        logger.info("Generating test article...")
        response = await client.post("https://clients--blog-writer-fastapi-app.modal.run/write", json=job_data)
        
        if response.status_code == 200:
            article = response.json()
            
            # Dump the entire structure
            logger.info("=== FULL ARTICLE STRUCTURE ===")
            for key in article.keys():
                logger.info(f"Key: {key}")
                if isinstance(article[key], str):
                    logger.info(f"  Type: string (length: {len(article[key])})")
                    if len(article[key]) < 500:  # Show short fields
                        logger.info(f"  Value: {article[key][:200]}...")
                    else:
                        logger.info(f"  Value: {article[key][:200]}... [truncated]")
                elif isinstance(article[key], list):
                    logger.info(f"  Type: list (length: {len(article[key])})")
                    logger.info(f"  Value: {article[key]}")
                else:
                    logger.info(f"  Type: {type(article[key])}")
                    logger.info(f"  Value: {article[key]}")
                logger.info("-" * 40)
            
            # Focus on literature/citations 
            if "literature" in article:
                logger.info("=== LITERATURE FIELD ANALYSIS ===")
                literature = article["literature"]
                logger.info(f"Literature type: {type(literature)}")
                if isinstance(literature, list):
                    logger.info(f"Literature length: {len(literature)}")
                    for i, item in enumerate(literature):
                        logger.info(f"Item {i}: {type(item)} = {item}")
                elif isinstance(literature, str):
                    logger.info(f"Literature string (length {len(literature)}):")
                    logger.info(literature)
                
            # Check for other citation-related fields
            citation_fields = ["sources", "citations", "references", "bibliography"]
            for field in citation_fields:
                if field in article:
                    logger.info(f"=== {field.upper()} FIELD ===")
                    logger.info(f"Type: {type(article[field])}")
                    logger.info(f"Value: {article[field]}")
        else:
            logger.error(f"API error: {response.status_code}")
            logger.error(response.text)

if __name__ == "__main__":
    asyncio.run(debug_citation_format())