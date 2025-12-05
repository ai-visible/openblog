#!/usr/bin/env python3
"""
Test script to verify AEO improvements are working correctly.
"""

import asyncio
import json
import re
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core.workflow_engine import WorkflowEngine
from pipeline.core.execution_context import ExecutionContext

async def test_aeo_improvements():
    """Test AEO improvements on a generated article."""
    print("=" * 80)
    print("TESTING AEO IMPROVEMENTS")
    print("=" * 80)
    print()
    
    # Create test job config
    job_config = {
        "primary_keyword": "AI adoption in customer service",
        "company_url": "https://example.com",
        "content_generation_instruction": "Focus on statistics and data-driven insights",
    }
    
    print("1. Generating article with improved workflow...")
    print("-" * 80)
    
    try:
        engine = WorkflowEngine()
        result_context = await engine.execute(
            job_id="test-aeo-improvements",
            job_config=job_config
        )
        
        if not result_context.validated_article:
            print("❌ FAILED: No validated article generated")
            return False
        
        article = result_context.validated_article
        quality_report = result_context.quality_report
        
        print(f"✅ Article generated successfully")
        print(f"   AEO Score: {quality_report.get('metrics', {}).get('aeo_score', 0)}/100")
        print()
        
        # Test 1: HTML Bug Fixes
        print("2. Testing HTML Bug Fixes...")
        print("-" * 80)
        html_content = article.get("content", "") + " " + " ".join([
            article.get(f"section_{i:02d}_content", "") for i in range(1, 10)
        ])
        
        double_closing_tags = html_content.count("</p></p>")
        if double_closing_tags > 0:
            print(f"❌ FAILED: Found {double_closing_tags} double closing tags (</p></p>)")
            return False
        else:
            print(f"✅ PASSED: No double closing tags found")
        print()
        
        # Test 2: Meta Tag Truncation
        print("3. Testing Meta Tag Truncation...")
        print("-" * 80)
        meta_title = article.get("Meta_Title", "")
        meta_desc = article.get("Meta_Description", "")
        
        if len(meta_title) > 60:
            print(f"❌ FAILED: Meta Title exceeds 60 chars: {len(meta_title)} chars")
            print(f"   Title: {meta_title}")
            return False
        else:
            print(f"✅ PASSED: Meta Title is {len(meta_title)} chars (≤60)")
        
        if len(meta_desc) > 160:
            print(f"❌ FAILED: Meta Description exceeds 160 chars: {len(meta_desc)} chars")
            return False
        else:
            print(f"✅ PASSED: Meta Description is {len(meta_desc)} chars (≤160)")
        print()
        
        # Test 3: Citation Distribution
        print("4. Testing Citation Distribution...")
        print("-" * 80)
        paragraphs = re.findall(r'<p[^>]*>.*?</p>', html_content, re.DOTALL)
        paras_with_2plus = sum(1 for para in paragraphs if len(re.findall(r'\[\d+\]', para)) >= 2)
        distribution = (paras_with_2plus / len(paragraphs) * 100) if paragraphs else 0
        
        print(f"   Paragraphs with 2+ citations: {paras_with_2plus}/{len(paragraphs)} ({distribution:.1f}%)")
        if distribution >= 60:
            print(f"✅ PASSED: Citation distribution meets target (≥60%)")
        else:
            print(f"⚠️  WARNING: Citation distribution below target ({distribution:.1f}% < 60%)")
        print()
        
        # Test 4: Conversational Phrases
        print("5. Testing Conversational Phrases...")
        print("-" * 80)
        conversational_phrases = [
            "how to", "what is", "why does", "when should", "where can",
            "you can", "you should", "let's", "here's", "this is",
            "how can", "what are", "how do", "why should", "where are",
        ]
        content_lower = html_content.lower()
        phrase_count = sum(1 for phrase in conversational_phrases if phrase in content_lower)
        
        print(f"   Conversational phrases found: {phrase_count}")
        if phrase_count >= 8:
            print(f"✅ PASSED: Conversational phrases meet target (≥8)")
        else:
            print(f"⚠️  WARNING: Conversational phrases below target ({phrase_count} < 8)")
        print()
        
        # Test 5: Question Headers
        print("6. Testing Question Headers...")
        print("-" * 80)
        question_patterns = ["what is", "how does", "why does", "when should", "where can", "what are", "how can"]
        question_headers = 0
        for i in range(1, 10):
            title = article.get(f"section_{i:02d}_title", "")
            if title and any(pattern in title.lower() for pattern in question_patterns):
                question_headers += 1
                print(f"   Found: {title}")
        
        print(f"   Question headers found: {question_headers}")
        if question_headers >= 2:
            print(f"✅ PASSED: Question headers meet target (≥2)")
        else:
            print(f"⚠️  WARNING: Question headers below target ({question_headers} < 2)")
        print()
        
        # Test 6: Lists
        print("7. Testing Lists...")
        print("-" * 80)
        list_count = html_content.count("<ul>") + html_content.count("<ol>")
        print(f"   Lists found: {list_count}")
        if list_count >= 3:
            print(f"✅ PASSED: Lists meet target (≥3)")
        else:
            print(f"⚠️  WARNING: Lists below target ({list_count} < 3)")
        print()
        
        # Test 7: Paragraph Length
        print("8. Testing Paragraph Length...")
        print("-" * 80)
        long_paragraphs = []
        for para in paragraphs:
            text_no_html = re.sub(r'<[^>]+>', ' ', para)
            word_count = len(text_no_html.split())
            if word_count > 50:
                long_paragraphs.append(word_count)
        
        print(f"   Paragraphs >50 words: {len(long_paragraphs)}")
        if len(long_paragraphs) == 0:
            print(f"✅ PASSED: No paragraphs exceed 50 words")
        else:
            print(f"⚠️  WARNING: {len(long_paragraphs)} paragraphs exceed 50 words")
        print()
        
        # Summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"AEO Score: {quality_report.get('metrics', {}).get('aeo_score', 0)}/100")
        print(f"Critical Issues: {len(quality_report.get('critical_issues', []))}")
        print()
        
        # Check if improvements are working
        improvements_working = (
            double_closing_tags == 0 and
            len(meta_title) <= 60 and
            len(meta_desc) <= 160
        )
        
        if improvements_working:
            print("✅ CORE IMPROVEMENTS WORKING:")
            print("   - HTML bug fixes: PASSED")
            print("   - Meta tag truncation: PASSED")
            print("   - Post-processing enforcement: ACTIVE")
        else:
            print("❌ SOME IMPROVEMENTS NOT WORKING")
        
        return improvements_working
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_aeo_improvements())
    sys.exit(0 if success else 1)

