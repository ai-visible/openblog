#!/usr/bin/env python3
"""
Full end-to-end test: Generate article and audit AEO improvements.
"""

import asyncio
import json
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core.workflow_engine import WorkflowEngine

async def generate_and_audit():
    """Generate article and perform comprehensive audit."""
    print("=" * 80)
    print("FULL GENERATION & AUDIT TEST")
    print("=" * 80)
    print()
    
    # Create test job config
    job_config = {
        "primary_keyword": "AI adoption in customer service",
        "company_url": "https://example.com",
        "content_generation_instruction": "Focus on statistics and data-driven insights",
    }
    
    print("Step 1: Generating article...")
    print("-" * 80)
    
    try:
        engine = WorkflowEngine()
        
        # Register all stages
        from pipeline.blog_generation import (
            DataFetchStage,
            PromptBuildStage,
            GeminiCallStage,
            ExtractionStage,
            CitationsStage,
            InternalLinksStage,
            TableOfContentsStage,
            MetadataStage,
            FAQPAAStage,
            ImageStage,
            CleanupStage,
            StorageStage,
        )
        
        engine.register_stages([
            DataFetchStage(),
            PromptBuildStage(),
            GeminiCallStage(),
            ExtractionStage(),
            CitationsStage(),
            InternalLinksStage(),
            TableOfContentsStage(),
            MetadataStage(),
            FAQPAAStage(),
            ImageStage(),
            CleanupStage(),
            StorageStage(),
        ])
        
        result_context = await engine.execute(
            job_id="test-full-audit",
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
        
        # Save article for inspection
        output_file = "test_article_output.json"
        with open(output_file, "w") as f:
            json.dump({
                "validated_article": article,
                "quality_report": quality_report,
            }, f, indent=2)
        print(f"   Article saved to: {output_file}")
        print()
        
        # Comprehensive audit
        print("Step 2: Comprehensive Audit")
        print("=" * 80)
        print()
        
        # Get all content
        html_content = article.get("content", "") + " " + " ".join([
            article.get(f"section_{i:02d}_content", "") for i in range(1, 10)
        ])
        
        all_issues = []
        all_passes = []
        
        # Audit 1: HTML Quality
        print("1. HTML Quality Check")
        print("-" * 80)
        double_closing_tags = html_content.count("</p></p>")
        if double_closing_tags > 0:
            print(f"❌ FAILED: Found {double_closing_tags} double closing tags (</p></p>)")
            all_issues.append(f"HTML: {double_closing_tags} double closing tags")
        else:
            print(f"✅ PASSED: No double closing tags found")
            all_passes.append("HTML: No double closing tags")
        
        # Check for other HTML issues
        unclosed_tags = html_content.count("<p>") - html_content.count("</p>")
        if unclosed_tags != 0:
            print(f"⚠️  WARNING: Unclosed <p> tags: {unclosed_tags} mismatch")
        print()
        
        # Audit 2: Meta Tags
        print("2. Meta Tag Validation")
        print("-" * 80)
        meta_title = article.get("Meta_Title", "")
        meta_desc = article.get("Meta_Description", "")
        
        if len(meta_title) > 60:
            print(f"❌ FAILED: Meta Title exceeds 60 chars: {len(meta_title)}")
            print(f"   Title: {meta_title}")
            all_issues.append(f"Meta Title: {len(meta_title)} chars (limit: 60)")
        else:
            print(f"✅ PASSED: Meta Title is {len(meta_title)} chars (≤60)")
            all_passes.append(f"Meta Title: {len(meta_title)} chars")
        
        if len(meta_desc) > 160:
            print(f"❌ FAILED: Meta Description exceeds 160 chars: {len(meta_desc)}")
            all_issues.append(f"Meta Description: {len(meta_desc)} chars (limit: 160)")
        else:
            print(f"✅ PASSED: Meta Description is {len(meta_desc)} chars (≤160)")
            all_passes.append(f"Meta Description: {len(meta_desc)} chars")
        print()
        
        # Audit 3: Citation Distribution
        print("3. Citation Distribution")
        print("-" * 80)
        paragraphs = re.findall(r'<p[^>]*>.*?</p>', html_content, re.DOTALL)
        total_paragraphs = len(paragraphs)
        paras_with_citations = sum(1 for para in paragraphs if re.search(r'\[\d+\]', para))
        paras_with_2plus = sum(1 for para in paragraphs if len(re.findall(r'\[\d+\]', para)) >= 2)
        distribution = (paras_with_2plus / total_paragraphs * 100) if total_paragraphs > 0 else 0
        
        print(f"   Total paragraphs: {total_paragraphs}")
        print(f"   Paragraphs with citations: {paras_with_citations}/{total_paragraphs}")
        print(f"   Paragraphs with 2+ citations: {paras_with_2plus}/{total_paragraphs} ({distribution:.1f}%)")
        
        if distribution >= 60:
            print(f"✅ PASSED: Citation distribution meets target (≥60%)")
            all_passes.append(f"Citations: {distribution:.1f}% paragraphs with 2+ citations")
        else:
            print(f"⚠️  WARNING: Citation distribution below target ({distribution:.1f}% < 60%)")
            all_issues.append(f"Citations: {distribution:.1f}% paragraphs with 2+ citations (target: 60%+)")
        print()
        
        # Audit 4: Conversational Phrases
        print("4. Conversational Phrases")
        print("-" * 80)
        conversational_phrases = [
            "how to", "what is", "why does", "when should", "where can",
            "you can", "you should", "let's", "here's", "this is",
            "how can", "what are", "how do", "why should", "where are",
        ]
        content_lower = html_content.lower()
        phrase_count = sum(1 for phrase in conversational_phrases if phrase in content_lower)
        found_phrases = [p for p in conversational_phrases if p in content_lower]
        
        print(f"   Conversational phrases found: {phrase_count}/15")
        print(f"   Phrases: {', '.join(found_phrases[:10])}")
        
        if phrase_count >= 8:
            print(f"✅ PASSED: Conversational phrases meet target (≥8)")
            all_passes.append(f"Conversational: {phrase_count} phrases found")
        else:
            print(f"⚠️  WARNING: Conversational phrases below target ({phrase_count} < 8)")
            all_issues.append(f"Conversational: {phrase_count} phrases (target: 8+)")
        print()
        
        # Audit 5: Question Headers
        print("5. Question Headers")
        print("-" * 80)
        question_patterns = ["what is", "how does", "why does", "when should", "where can", "what are", "how can"]
        question_headers = []
        for i in range(1, 10):
            title = article.get(f"section_{i:02d}_title", "")
            if title:
                title_lower = title.lower()
                if any(pattern in title_lower for pattern in question_patterns):
                    question_headers.append(title)
        
        print(f"   Question headers found: {len(question_headers)}")
        for header in question_headers:
            print(f"   - {header}")
        
        if len(question_headers) >= 2:
            print(f"✅ PASSED: Question headers meet target (≥2)")
            all_passes.append(f"Question headers: {len(question_headers)} found")
        else:
            print(f"⚠️  WARNING: Question headers below target ({len(question_headers)} < 2)")
            all_issues.append(f"Question headers: {len(question_headers)} (target: 2+)")
        print()
        
        # Audit 6: Lists
        print("6. Lists (Structured Data)")
        print("-" * 80)
        list_count = html_content.count("<ul>") + html_content.count("<ol>")
        print(f"   Lists found: {list_count}")
        
        if list_count >= 3:
            print(f"✅ PASSED: Lists meet target (≥3)")
            all_passes.append(f"Lists: {list_count} found")
        else:
            print(f"⚠️  WARNING: Lists below target ({list_count} < 3)")
            all_issues.append(f"Lists: {list_count} (target: 3+)")
        print()
        
        # Audit 7: Paragraph Length
        print("7. Paragraph Length")
        print("-" * 80)
        long_paragraphs = []
        for para in paragraphs:
            text_no_html = re.sub(r'<[^>]+>', ' ', para)
            word_count = len(text_no_html.split())
            if word_count > 50:
                long_paragraphs.append(word_count)
        
        avg_length = sum(len(re.sub(r'<[^>]+>', ' ', p).split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        
        print(f"   Total paragraphs: {len(paragraphs)}")
        print(f"   Average length: {avg_length:.1f} words")
        print(f"   Paragraphs >50 words: {len(long_paragraphs)}")
        
        if len(long_paragraphs) == 0:
            print(f"✅ PASSED: No paragraphs exceed 50 words")
            all_passes.append(f"Paragraph length: All ≤50 words")
        else:
            print(f"⚠️  WARNING: {len(long_paragraphs)} paragraphs exceed 50 words")
            all_issues.append(f"Paragraph length: {len(long_paragraphs)} paragraphs >50 words")
        print()
        
        # Audit 8: AEO Score Breakdown
        print("8. AEO Score Analysis")
        print("-" * 80)
        aeo_score = quality_report.get('metrics', {}).get('aeo_score', 0)
        print(f"   AEO Score: {aeo_score}/100")
        
        if aeo_score >= 70:
            print(f"✅ PASSED: AEO score meets target (≥70)")
            all_passes.append(f"AEO Score: {aeo_score}/100")
        elif aeo_score >= 60:
            print(f"⚠️  WARNING: AEO score below target but acceptable ({aeo_score} < 70)")
            all_issues.append(f"AEO Score: {aeo_score}/100 (target: 70+)")
        else:
            print(f"❌ FAILED: AEO score too low ({aeo_score} < 60)")
            all_issues.append(f"AEO Score: {aeo_score}/100 (target: 70+)")
        print()
        
        # Summary
        print("=" * 80)
        print("AUDIT SUMMARY")
        print("=" * 80)
        print()
        print(f"AEO Score: {aeo_score}/100")
        print(f"Critical Issues: {len(quality_report.get('critical_issues', []))}")
        print()
        
        print("✅ PASSED CHECKS:")
        for check in all_passes:
            print(f"   - {check}")
        print()
        
        if all_issues:
            print("⚠️  ISSUES FOUND:")
            for issue in all_issues:
                print(f"   - {issue}")
        else:
            print("✅ NO ISSUES FOUND")
        print()
        
        # Overall assessment
        critical_failures = [
            issue for issue in all_issues 
            if "FAILED" in issue or "HTML" in issue or "Meta Title" in issue
        ]
        
        if critical_failures:
            print("❌ CRITICAL FAILURES DETECTED")
            return False
        elif aeo_score >= 70:
            print("✅ ALL IMPROVEMENTS WORKING - AEO SCORE IMPROVED")
            return True
        elif aeo_score >= 60:
            print("⚠️  IMPROVEMENTS PARTIALLY WORKING - NEEDS OPTIMIZATION")
            return True  # Still pass, but needs work
        else:
            print("❌ AEO SCORE TOO LOW - IMPROVEMENTS NOT EFFECTIVE")
            return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(generate_and_audit())
    sys.exit(0 if success else 1)

