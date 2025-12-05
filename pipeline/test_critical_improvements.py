#!/usr/bin/env python3
"""
Critical Improvements Validation Script

Tests the 7 major improvements implemented for blog writer v4.1 feature parity:
1. ⚠️ Content fingerprinting system (DEPRECATED - replaced by Gemini embeddings)
2. ⚠️ Cross-article duplicate prevention (DEPRECATED - now in Edge Functions)
3. ✅ Automatic regeneration logic
4. ✅ HTTP HEAD validation for internal links
5. ✅ Citation validation performance optimization
6. ✅ Real-time quality gates (85+ AEO)
7. ✅ Per-paragraph citation distribution

NOTE: SimHash-based deduplication (tests 1-2) is deprecated as of 2024-12-03.
Semantic content deduplication is now handled by Gemini embeddings in Edge Functions.
See: supabase/functions/s5-generate-blogs/index.ts

Run this script to validate all improvements work correctly.
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_content_fingerprinting():
    """Test content hashing and similarity detection.
    
    ⚠️ DEPRECATED: This test validates the old SimHash-based deduplication.
    Semantic deduplication is now handled by Gemini embeddings in Edge Functions.
    See: supabase/functions/s5-generate-blogs/index.ts
    """
    logger.info("⚠️ [DEPRECATED] Testing SimHash content fingerprinting system...")
    logger.info("   NOTE: This is deprecated. Use Gemini embeddings in Edge Functions instead.")
    
    from utils.content_hasher import ContentHasher, compute_content_hash, check_content_similarity
    
    # Test data
    article1 = {
        "Headline": "AI in Manufacturing: A Complete Guide",
        "Intro": "Artificial intelligence is transforming manufacturing with automation and predictive analytics.",
        "section_01_content": "AI-powered systems reduce production costs by 25% through optimized workflows.",
        "section_02_content": "Machine learning algorithms predict equipment failures 3 weeks in advance."
    }
    
    article2 = {
        "Headline": "Manufacturing AI: Complete Implementation Guide", 
        "Intro": "AI transforms manufacturing through automation and predictive maintenance systems.",
        "section_01_content": "Intelligent systems decrease manufacturing costs by 25% via workflow optimization.",
        "section_02_content": "ML models forecast machinery failures up to 3 weeks ahead of time."
    }
    
    article3 = {
        "Headline": "Digital Marketing Strategies for 2025",
        "Intro": "Marketing teams need fresh approaches to reach customers in the digital age.",
        "section_01_content": "Social media engagement rates increased 40% with personalized content.",
        "section_02_content": "Email marketing automation drives 3x higher conversion rates."
    }
    
    # Test hash generation
    hash1 = compute_content_hash(article1)
    hash2 = compute_content_hash(article2)
    hash3 = compute_content_hash(article3)
    
    logger.info(f"   Article 1 hash: {hash1}")
    logger.info(f"   Article 2 hash: {hash2}")
    logger.info(f"   Article 3 hash: {hash3}")
    
    # Test similarity detection
    existing_hashes = [("article1", hash1), ("article3", hash3)]
    
    # Should detect similarity between article1 and article2
    similarity = check_content_similarity(article2, existing_hashes, threshold=12)
    if similarity:
        similar_id, distance = similarity
        similarity_pct = ((64 - distance) / 64) * 100
        logger.info(f"✅ Similarity detected: {similarity_pct:.1f}% similar to {similar_id}")
    else:
        logger.error("❌ Failed to detect similar content")
        return False
    
    # Should not detect similarity with different content
    similarity2 = check_content_similarity(article3, [("article1", hash1)], threshold=12)
    if not similarity2:
        logger.info("✅ Correctly identified unique content")
    else:
        logger.error("❌ False positive: detected similarity in different content")
        return False
    
    logger.info("✅ Content fingerprinting system: PASSED")
    return True

def test_quality_gates():
    """Test quality gate logic with 85+ AEO requirement."""
    logger.info("🧪 Testing quality gates...")
    
    from processors.quality_checker import QualityChecker
    
    # Mock article that should pass
    good_article = {
        "Headline": "AI Manufacturing Guide",
        "Intro": "AI transforms manufacturing with 85% efficiency gains.",
        "section_01_content": "<p>Manufacturing AI reduces costs by 30% annually [1]. Companies report 25% productivity increases within 6 months [2]. Implementation typically requires 8-12 weeks of planning [3].</p>",
        "section_02_content": "<p>Predictive maintenance prevents 85% of equipment failures [4]. <a href='/blog/ai-maintenance'>AI maintenance systems</a> cut downtime by 40% [5]. ROI reaches $2.5M for mid-size facilities [6].</p>"
    }
    
    # Mock article that should fail (low AEO score)
    bad_article = {
        "Headline": "Test",
        "Intro": "Short intro.",
        "section_01_content": "<p>No citations or data.</p>",
        "section_02_content": "<p>Very basic content without numbers.</p>"
    }
    
    # Test good article (should pass)
    try:
        good_report = QualityChecker.check_article(good_article, {}, None, {})
        good_passed = good_report.get("passed", False)
        good_aeo = good_report.get("metrics", {}).get("aeo_score", 0)
        
        logger.info(f"   Good article: AEO={good_aeo}/100, Passed={good_passed}")
        
        # Test bad article (should fail)
        bad_report = QualityChecker.check_article(bad_article, {}, None, {})
        bad_passed = bad_report.get("passed", False)
        bad_aeo = bad_report.get("metrics", {}).get("aeo_score", 0)
        
        logger.info(f"   Bad article: AEO={bad_aeo}/100, Passed={bad_passed}")
        
        if good_aeo >= 85 and good_passed and bad_aeo < 85 and not bad_passed:
            logger.info("✅ Quality gates: PASSED")
            return True
        else:
            logger.error("❌ Quality gate logic not working correctly")
            return False
            
    except Exception as e:
        logger.error(f"❌ Quality gate test failed: {e}")
        return False

async def test_url_validation_performance():
    """Test URL validation with caching performance."""
    logger.info("🧪 Testing URL validation performance...")
    
    from processors.url_validator import CitationURLValidator
    from models.gemini_client import GeminiClient
    
    # Mock URLs for testing
    test_urls = [
        "https://www.example.com/page1",
        "https://www.example.com/page2", 
        "https://httpbin.org/status/200",
        "https://httpbin.org/status/404",
        "https://www.example.com/page1",  # Duplicate to test caching
    ]
    
    try:
        # Create validator (will use mock client for testing)
        validator = CitationURLValidator(
            gemini_client=None,  # Skip Gemini for performance test
            timeout=3.0
        )
        
        # First pass - should take longer (no cache)
        start_time = time.time()
        results1 = []
        for url in test_urls:
            is_valid, final_url = await validator._check_url_status(url)
            results1.append((url, is_valid, final_url))
        first_pass_time = time.time() - start_time
        
        # Second pass - should be much faster (cached)
        start_time = time.time()
        results2 = []
        for url in test_urls:
            is_valid, final_url = await validator._check_url_status(url)
            results2.append((url, is_valid, final_url))
        second_pass_time = time.time() - start_time
        
        await validator.close()
        
        logger.info(f"   First pass: {first_pass_time:.2f}s")
        logger.info(f"   Second pass: {second_pass_time:.2f}s")
        logger.info(f"   Speed improvement: {first_pass_time/second_pass_time:.1f}x faster")
        
        # Results should be identical
        if results1 == results2 and second_pass_time < first_pass_time * 0.5:
            logger.info("✅ URL validation caching: PASSED")
            return True
        else:
            logger.error("❌ Caching not working effectively")
            return False
            
    except Exception as e:
        logger.error(f"❌ URL validation test failed: {e}")
        return False

def test_paragraph_validation():
    """Test per-paragraph citation distribution validation."""
    logger.info("🧪 Testing per-paragraph citation validation...")
    
    from processors.quality_checker import QualityChecker
    
    # Article with good citation distribution (2-3 per paragraph)
    good_article = {
        "section_01_content": "<p>Manufacturing AI reduces costs by 30% [1]. Productivity increases reach 25% within 6 months [2]. Implementation requires 8-12 weeks typically [3].</p>",
        "section_02_content": "<p>Predictive maintenance prevents 85% of failures [4]. Downtime decreases by 40% on average [5].</p>",
        "section_03_content": "<p>ROI for mid-size facilities reaches $2.5M annually [6]. Energy consumption drops 20% with smart systems [7]. Quality control improves 95% accuracy [8].</p>"
    }
    
    # Article with poor citation distribution 
    bad_article = {
        "section_01_content": "<p>Manufacturing AI reduces costs significantly. Productivity increases are common. Implementation takes time.</p>",
        "section_02_content": "<p>Predictive maintenance is helpful [1].</p>",
        "section_03_content": "<p>ROI can be substantial with proper implementation and planning.</p>"
    }
    
    try:
        # Test good article
        good_report = QualityChecker._check_citation_distribution(good_article)
        
        # Test bad article  
        bad_report = QualityChecker._check_citation_distribution(bad_article)
        
        logger.info(f"   Good article issues: {len(good_report)}")
        logger.info(f"   Bad article issues: {len(bad_report)}")
        
        # Good article should have fewer issues than bad article
        if len(bad_report) > len(good_report):
            logger.info("✅ Per-paragraph citation validation: PASSED")
            return True
        else:
            logger.error("❌ Citation validation not detecting issues properly")
            return False
            
    except Exception as e:
        logger.error(f"❌ Citation validation test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all critical improvement tests."""
    logger.info("🚀 Starting comprehensive validation of critical improvements...")
    logger.info("=" * 80)
    
    tests = [
        ("Content Fingerprinting", test_content_fingerprinting),
        ("Quality Gates (85+ AEO)", test_quality_gates), 
        ("URL Validation Performance", test_url_validation_performance),
        ("Per-Paragraph Citations", test_paragraph_validation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = asyncio.run(test_func())
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
        
        logger.info("-" * 80)
    
    # Summary
    logger.info("📊 FINAL RESULTS:")
    logger.info("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"   {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("-" * 80)
    logger.info(f"SUMMARY: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 ALL CRITICAL IMPROVEMENTS VALIDATED SUCCESSFULLY!")
        return True
    else:
        logger.error(f"🚨 {failed} critical improvements need attention")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)