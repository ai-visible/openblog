#!/usr/bin/env python3
"""E2E test for scaile.tech keyword generation"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Try to load from .env.local or .env file
try:
    from dotenv import load_dotenv
    env_file = Path('.env.local')
    if not env_file.exists():
        env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print(f"✅ Loaded environment from {env_file}")
except ImportError:
    pass  # dotenv not available, use environment variables only

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.keyword_generation.adapter import KeywordV2Adapter
from pipeline.keyword_generation.logging_config import setup_logging

# Enable logging to see batch execution details
setup_logging(level="INFO")


async def test_scaile():
    """Test keyword generation for scaile.tech"""
    print("=" * 70)
    print("Testing Keyword Generation V2 for scaile.tech")
    print("=" * 70)
    
    # Check API keys
    google_key = os.getenv('GOOGLE_API_KEY')
    seranking_key = os.getenv('SERANKING_API_KEY')
    
    if not google_key:
        print("\n❌ ERROR: GOOGLE_API_KEY environment variable not set")
        print("   Please set it with: export GOOGLE_API_KEY='your-key'")
        return None
    
    print(f"\n✅ Google API Key: Set")
    if seranking_key:
        print(f"✅ SE Ranking API Key: Set")
    else:
        print(f"⚠️  SE Ranking API Key: Not set (gap analysis will be skipped)")
    
    # Create adapter
    print("\n🔧 Initializing adapter...")
    adapter = KeywordV2Adapter()
    
    # Test parameters
    company_name = "Scaile"
    domain = "scaile.tech"
    location = "Germany"
    keyword_count = 50
    cluster_count = 5
    min_score = 40
    
    print(f"\n📋 Test Parameters:")
    print(f"  Company: {company_name}")
    print(f"  Domain: {domain}")
    print(f"  Location: {location}")
    print(f"  Keyword Count: {keyword_count}")
    print(f"  Cluster Count: {cluster_count}")
    print(f"  Min Score: {min_score}")
    
    print(f"\n🚀 Starting keyword generation...")
    print("   This may take 1-2 minutes...")
    start_time = datetime.now()
    
    try:
        # Generate keywords
        result = await adapter.generate_for_blog_writer_async(
            company_name=company_name,
            domain=domain,
            location=location,
            keyword_count=keyword_count,
            cluster_count=cluster_count,
            min_score=min_score,
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n✅ Generation completed in {elapsed:.2f}s")
        
        # Display results
        print(f"\n📊 Results:")
        stats = result.get('statistics', {})
        print(f"  Total Keywords: {stats.get('total_keywords', 0)}")
        print(f"  AI Keywords: {stats.get('ai_keywords', 0)}")
        print(f"  Gap Keywords: {stats.get('gap_keywords', 0)}")
        print(f"  Clusters: {len(result.get('clusters', []))}")
        
        # Show sample keywords
        keywords = result.get('keywords', [])
        if keywords:
            print(f"\n🔑 Top Keywords (first 15):")
            for i, kw in enumerate(keywords[:15], 1):
                score = kw.get('score', 0)
                keyword = kw.get('keyword', '')
                cluster = kw.get('cluster', 'N/A')
                intent = kw.get('intent', 'N/A')
                source = kw.get('source', 'N/A')
                print(f"  {i:2d}. [{score:3d}] {keyword[:45]:<45} | {cluster[:20]:<20} | {intent}")
        
        # Show clusters
        clusters = result.get('clusters', [])
        if clusters:
            print(f"\n📁 Clusters ({len(clusters)} total):")
            clusters_with_kws = result.get('clusters_with_keywords', {})
            for cluster in clusters[:10]:  # Show first 10
                cluster_kws = clusters_with_kws.get(cluster, [])
                print(f"  - {cluster}: {len(cluster_kws)} keywords")
        
        # Save results
        output_file = f"scaile_keywords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {output_file}")
        
        print("\n" + "=" * 70)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 70)
        
        return result
        
    except ValueError as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n❌ Validation Error after {elapsed:.2f}s:")
        print(f"   {e}")
        return None
    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n❌ Error after {elapsed:.2f}s:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(test_scaile())
    sys.exit(0 if result else 1)

