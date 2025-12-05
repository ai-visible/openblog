#!/usr/bin/env python3
"""
Test Modal Environment Variables

This script tests what environment variables are actually available in the Modal runtime
and specifically checks for Gemini API key availability.
"""

import os
import json
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_environment_variables():
    """Test what environment variables are available."""
    logger.info("🔍 TESTING MODAL ENVIRONMENT VARIABLES")
    logger.info("=" * 80)
    
    # Check common API key environment variable names
    api_key_vars = [
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY", 
        "GOOGLE_GEMINI_API_KEY",
        "GEMINI_API_KEY_API",
        "GEMINI_API_KEY_KEY",
        "GEMINI",
        "GOOGLE",
    ]
    
    found_keys = {}
    for var_name in api_key_vars:
        value = os.getenv(var_name)
        if value:
            # Mask the key for security (show first 8 chars + ...)
            masked = f"{value[:8]}..." if len(value) > 8 else "***"
            found_keys[var_name] = masked
            logger.info(f"✅ Found {var_name}: {masked}")
        else:
            logger.info(f"❌ Missing {var_name}")
    
    # Check all environment variables containing 'API' or 'KEY'
    logger.info("\n🔍 ALL ENVIRONMENT VARIABLES CONTAINING 'API' OR 'KEY':")
    api_env_vars = {}
    for key, value in os.environ.items():
        if 'API' in key.upper() or 'KEY' in key.upper():
            masked = f"{value[:8]}..." if len(value) > 8 else "***"
            api_env_vars[key] = masked
            logger.info(f"   {key}: {masked}")
    
    # Test Google GenAI SDK import and authentication
    logger.info("\n🧪 TESTING GOOGLE GENAI SDK:")
    try:
        import google.genai as genai
        logger.info("✅ google.genai imported successfully")
        
        # Try to find an API key
        api_key = None
        for var_name in api_key_vars:
            if os.getenv(var_name):
                api_key = os.getenv(var_name)
                logger.info(f"✅ Using API key from {var_name}")
                break
        
        if api_key:
            try:
                client = genai.Client(api_key=api_key)
                logger.info("✅ GenAI Client created successfully")
                
                # Try to call the API (simple test)
                from google.genai.types import Tool, GoogleSearch, GenerateContentConfig
                logger.info("✅ Google Search tools imported successfully")
                
                # Test if tools can be configured
                tools = [Tool(google_search=GoogleSearch())]
                config = GenerateContentConfig(tools=tools, max_output_tokens=100)
                logger.info("✅ Google Search tools configured successfully")
                
                # Try a minimal API call to test authentication
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents="Say hello",
                        config=GenerateContentConfig(max_output_tokens=50),
                    )
                    logger.info("✅ Basic API call successful")
                    logger.info(f"   Response: {response.text[:100]}...")
                except Exception as api_error:
                    logger.error(f"❌ API call failed: {api_error}")
                
            except Exception as client_error:
                logger.error(f"❌ GenAI Client creation failed: {client_error}")
        else:
            logger.error("❌ No API key found for GenAI SDK")
            
    except ImportError as e:
        logger.error(f"❌ google.genai import failed: {e}")
    
    # Save results for analysis
    results = {
        "found_api_keys": found_keys,
        "all_api_env_vars": api_env_vars,
        "test_timestamp": "2025-12-03",
    }
    
    return results

async def main():
    """Main test function."""
    results = test_environment_variables()
    
    # Save to file for inspection
    with open("modal_env_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("\n📁 Results saved: modal_env_test_results.json")
    return results

if __name__ == "__main__":
    asyncio.run(main())