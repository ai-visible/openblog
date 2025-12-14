#!/usr/bin/env python3
"""
Isolated test for semantic embedding similarity checking.

Tests ONLY the semantic embedding functionality:
1. GeminiEmbeddingClient initialization
2. Embedding generation
3. Semantic similarity calculation
4. HybridSimilarityChecker with semantic mode

Uses existing generated articles - no full pipeline execution.
"""

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables (try both locations)
load_dotenv('.env.local')
load_dotenv('.env')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("="*80)
print("SEMANTIC EMBEDDING SIMILARITY CHECK - ISOLATION TEST")
print("="*80)
print()

# Check if google-generativeai is installed
try:
    import google.generativeai as genai
    print("✅ google-generativeai package is installed")
except ImportError:
    print("❌ google-generativeai package NOT installed")
    print("   Install with: pip install google-generativeai")
    sys.exit(1)

# Check for API key (try multiple env var names)
api_key = (
    os.getenv("GEMINI_API_KEY") or 
    os.getenv("GOOGLE_API_KEY") or 
    os.getenv("GOOGLE_GEMINI_API_KEY")
)

if not api_key:
    print("❌ GEMINI_API_KEY, GOOGLE_API_KEY, or GOOGLE_GEMINI_API_KEY not found")
    print("   Set API key in .env.local file")
    sys.exit(1)
else:
    print(f"✅ API key found (length: {len(api_key)})")

# Load test articles
output_dir = Path("output")
article1_path = output_dir / "api-20251213-133744-enterprise AI securi" / "article.json"
article2_path = output_dir / "api-20251213-140206-enterprise AI securi" / "article.json"

if not article1_path.exists():
    print(f"❌ Article 1 not found: {article1_path}")
    sys.exit(1)

if not article2_path.exists():
    print(f"❌ Article 2 not found: {article2_path}")
    sys.exit(1)

try:
    with open(article1_path, 'r') as f:
        article1 = json.load(f)
    headline1 = article1.get('Headline', 'N/A').replace('<p>', '').replace('</p>', '')
    print(f"✅ Loaded article 1: {headline1[:60]}...")
except Exception as e:
    print(f"❌ Failed to load article 1: {e}")
    sys.exit(1)

try:
    with open(article2_path, 'r') as f:
        article2 = json.load(f)
    headline2 = article2.get('Headline', 'N/A').replace('<p>', '').replace('</p>', '')
    print(f"✅ Loaded article 2: {headline2[:60]}...")
except Exception as e:
    print(f"❌ Failed to load article 2: {e}")
    sys.exit(1)

print()
print("="*80)
print("TEST 1: GeminiEmbeddingClient - Basic Functionality")
print("="*80)

from pipeline.utils.gemini_embeddings import GeminiEmbeddingClient

try:
    client = GeminiEmbeddingClient(api_key=api_key)
    print("✅ GeminiEmbeddingClient initialized")
    
    # Test embedding generation
    test_text = article1.get('Intro', '')[:500] if article1.get('Intro') else "Test text"
    # Strip HTML tags for cleaner test
    import re
    test_text = re.sub(r'<[^>]+>', ' ', test_text).strip()[:500]
    
    print(f"\n📝 Testing embedding generation...")
    print(f"   Text: '{test_text[:100]}...'")
    
    embedding = client.embed_text(test_text)
    if embedding:
        print(f"✅ Embedding generated: {len(embedding)} dimensions")
        print(f"   First 5 values: {[f'{v:.4f}' for v in embedding[:5]]}")
        print(f"   Embedding magnitude: {sum(v*v for v in embedding)**0.5:.4f}")
    else:
        print("❌ Embedding generation FAILED - returned None")
        sys.exit(1)
    
    # Test similarity comparison
    print(f"\n📊 Testing similarity comparison...")
    text1 = article1.get('Intro', '')[:500] if article1.get('Intro') else ""
    text2 = article2.get('Intro', '')[:500] if article2.get('Intro') else ""
    
    # Strip HTML
    text1 = re.sub(r'<[^>]+>', ' ', text1).strip()[:500]
    text2 = re.sub(r'<[^>]+>', ' ', text2).strip()[:500]
    
    if text1 and text2:
        similarity = client.compare_texts(text1, text2)
        print(f"✅ Similarity calculated: {similarity:.3f} (0.0-1.0 scale)")
        print(f"   Article 1 intro: '{text1[:80]}...'")
        print(f"   Article 2 intro: '{text2[:80]}...'")
        
        if similarity > 0.5:
            print(f"   ⚠️  High similarity detected - articles may be too similar")
        elif similarity > 0.3:
            print(f"   ℹ️  Moderate similarity - expected for related topics")
        else:
            print(f"   ✅ Low similarity - articles are distinct")
    else:
        print("⚠️  Missing intro text in articles")
    
    # Get stats
    stats = client.get_stats()
    print(f"\n📈 Client Statistics:")
    print(f"   Requests made: {stats['requests_made']}")
    print(f"   Cache hits: {stats['cache_hits']}")
    print(f"   Cache hit rate: {stats['cache_hit_rate']}")
    print(f"   API errors: {stats['api_errors']}")
    
except Exception as e:
    print(f"❌ Error testing GeminiEmbeddingClient: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("="*80)
print("TEST 2: HybridSimilarityChecker - Semantic Mode")
print("="*80)

from pipeline.utils.hybrid_similarity_checker import HybridSimilarityChecker

try:
    checker = HybridSimilarityChecker(embedding_client=client)
    print(f"✅ HybridSimilarityChecker initialized")
    print(f"   Semantic mode: {checker.semantic_mode}")
    print(f"   Embedding client: {checker.embedding_client is not None}")
    print(f"   Semantic threshold: {checker.SEMANTIC_THRESHOLD}")
    
    # Add first article
    print(f"\n📝 Adding article 1 to checker...")
    slug1 = checker.add_article(article1, "test-article-1")
    print(f"✅ Added article 1: {slug1}")
    
    # Check if embedding was generated
    summary1 = checker.articles.get(slug1)
    if summary1:
        if summary1.content_embedding:
            print(f"   ✅ Embedding generated for article 1: {len(summary1.content_embedding)} dims")
            print(f"   ✅ Embedding text prepared: {len(summary1.embedding_text or '')} chars")
        else:
            print(f"   ❌ NO EMBEDDING GENERATED for article 1!")
            print(f"   ⚠️  This means semantic similarity will NOT work")
    
    # Check second article against first
    print(f"\n🔍 Checking article 2 similarity against article 1...")
    result = checker.check_content_similarity(article2, "test-article-2")
    
    print(f"\n📊 SIMILARITY RESULTS:")
    print(f"   Similarity Score: {result.similarity_score:.1f}%")
    print(f"   Too Similar: {result.is_too_similar}")
    print(f"   Analysis Mode: {result.analysis_mode}")
    
    if result.shingle_score is not None:
        print(f"   Shingle Score: {result.shingle_score:.1f}%")
    else:
        print(f"   Shingle Score: N/A")
    
    if result.semantic_score is not None:
        print(f"   ✅ Semantic Score: {result.semantic_score:.3f} ({result.semantic_score*100:.1f}%)")
        if result.semantic_score > checker.SEMANTIC_THRESHOLD:
            print(f"      ⚠️  Above semantic threshold ({checker.SEMANTIC_THRESHOLD})")
        else:
            print(f"      ✅ Below semantic threshold")
    else:
        print(f"   ❌ Semantic Score: NONE - EMBEDDINGS NOT WORKING!")
    
    print(f"   Similar Article: {result.similar_article}")
    print(f"   Issues Found: {len(result.issues)}")
    for issue in result.issues[:5]:
        print(f"     - {issue}")
    
    # Critical check
    print(f"\n🔬 CRITICAL ANALYSIS:")
    if result.semantic_score is None:
        print(f"   ❌ FAILURE: Semantic embeddings are NOT working!")
        print(f"   ❌ Semantic score is None - embeddings were not generated or compared")
        print(f"   ⚠️  This means semantic similarity checking is DISABLED")
    elif result.semantic_score == 0.0:
        print(f"   ⚠️  WARNING: Semantic score is 0.0")
        print(f"   ⚠️  This could mean:")
        print(f"      - Articles are completely different (unlikely for related topics)")
        print(f"      - Embedding generation failed silently")
        print(f"      - Cosine similarity calculation failed")
    else:
        print(f"   ✅ SUCCESS: Semantic embeddings ARE working!")
        print(f"   ✅ Semantic similarity: {result.semantic_score:.3f}")
        print(f"   ✅ Hybrid score combines character ({result.shingle_score:.1f}%) + semantic ({result.semantic_score*100:.1f}%)")
    
    # Check batch stats
    batch_stats = checker.get_batch_stats()
    print(f"\n📈 Batch Statistics:")
    print(f"   Articles in batch: {batch_stats.get('articles_count', 0)}")
    print(f"   Embedding requests: {checker._embedding_requests}")
    print(f"   Embedding cache hits: {checker._embedding_cache_hits}")
    
except Exception as e:
    print(f"❌ Error testing HybridSimilarityChecker: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("="*80)
print("TEST 3: Verify Embedding Generation Path")
print("="*80)

# Check if embeddings are actually being generated
try:
    # Create a fresh checker
    checker2 = HybridSimilarityChecker(embedding_client=client)
    
    # Add article and check embedding
    slug = checker2.add_article(article1, "debug-article")
    summary = checker2.articles.get(slug)
    
    if summary:
        print(f"✅ Article summary created")
        print(f"   Content length: {len(summary.content_shingles)} shingles")
        print(f"   Embedding text length: {len(summary.embedding_text or '')} chars")
        
        if summary.content_embedding:
            print(f"   ✅ EMBEDDING EXISTS: {len(summary.content_embedding)} dimensions")
            print(f"   ✅ Embedding first 3 values: {[f'{v:.4f}' for v in summary.content_embedding[:3]]}")
        else:
            print(f"   ❌ NO EMBEDDING - checking why...")
            
            # Debug: try generating embedding manually
            if summary.embedding_text:
                print(f"   📝 Trying manual embedding generation...")
                manual_embedding = client.embed_text(summary.embedding_text)
                if manual_embedding:
                    print(f"   ✅ Manual embedding works: {len(manual_embedding)} dims")
                    print(f"   ❌ But summary.content_embedding is None - BUG IN _generate_embedding()")
                else:
                    print(f"   ❌ Manual embedding also fails - API issue")
            else:
                print(f"   ❌ No embedding_text prepared - content too short?")
                print(f"   ❌ Content text length: {len(checker2._extract_content(article1))}")
    
except Exception as e:
    print(f"❌ Error in debug check: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("TEST COMPLETE")
print("="*80)

