#!/usr/bin/env python3
"""
Production Test: Spherecast Blog Generation with Simplified Prompt

Tests the simplified prompt with real Spherecast data:
- Generates article using new prompt
- Verifies quality improvements (grammar, citations, length)
- Checks for issues we fixed (speed upd, applys, citation-only paragraphs)
"""

import asyncio
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core import WorkflowEngine
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


class QualityAuditor:
    """Audit generated article for quality improvements."""
    
    def audit_article(self, article_data: dict) -> dict:
        """Audit article for quality issues we fixed."""
        issues = []
        metrics = {}
        
        # Extract text content
        text_content = self._extract_text(article_data)
        
        # Check 1: Grammar errors (should be fixed)
        grammar_errors = {
            'speed upd': 'speed up',
            'applys': 'applies',
            'Also,,': 'Also,',
            '. .': '.',
        }
        
        found_errors = []
        for error, correction in grammar_errors.items():
            if error in text_content:
                found_errors.append(f"'{error}' → should be '{correction}'")
        
        if found_errors:
            issues.append(f"Grammar errors found: {', '.join(found_errors)}")
        metrics['grammar_errors'] = len(found_errors)
        
        # Check 2: Citation embedding (should be fixed)
        citation_only_paras = re.findall(r'<p>\s*\[\d+\](\[\d+\])*\s*</p>', text_content)
        if citation_only_paras:
            issues.append(f"Citation-only paragraphs found: {len(citation_only_paras)}")
        metrics['citation_only_paras'] = len(citation_only_paras)
        
        # Check 3: Headline length (should be ≤60)
        headline = article_data.get('headline', '')
        headline_len = len(headline)
        if headline_len > 60:
            issues.append(f"Headline too long: {headline_len} chars (max 60)")
        metrics['headline_length'] = headline_len
        
        # Check 4: Intro length (should be ≤300 words)
        intro = article_data.get('intro', '')
        intro_words = len(intro.split())
        if intro_words > 300:
            issues.append(f"Intro too long: {intro_words} words (max 300)")
        metrics['intro_words'] = intro_words
        
        # Check 5: Empty headings
        sections = article_data.get('sections', [])
        empty_headings = []
        for section in sections:
            content = section.get('content', '')
            # Remove HTML tags and check if substantial
            text_only = re.sub(r'<[^>]+>', '', content).strip()
            if len(text_only) < 100:
                empty_headings.append(section.get('title', 'Unknown'))
        
        if empty_headings:
            issues.append(f"Empty headings found: {len(empty_headings)}")
        metrics['empty_headings'] = len(empty_headings)
        
        # Check 6: Keyword density (should be 8-12)
        keyword = article_data.get('primary_keyword', '')
        if keyword:
            keyword_lower = keyword.lower()
            text_lower = text_content.lower()
            mentions = text_lower.count(keyword_lower)
            if mentions < 8:
                issues.append(f"Keyword density too low: {mentions} mentions (min 8)")
            elif mentions > 15:
                issues.append(f"Keyword density too high: {mentions} mentions (max 12 recommended)")
            metrics['keyword_mentions'] = mentions
        
        # Calculate quality score
        base_score = 100
        score = base_score - (len(issues) * 10) - (metrics.get('grammar_errors', 0) * 5)
        score = max(0, min(100, score))
        
        return {
            'issues': issues,
            'metrics': metrics,
            'score': score
        }
    
    def _extract_text(self, article_data: dict) -> str:
        """Extract all text content from article."""
        text_parts = []
        
        # Headline, subtitle, teaser, intro
        for key in ['headline', 'subtitle', 'teaser', 'intro', 'direct_answer']:
            if key in article_data and article_data[key]:
                text_parts.append(str(article_data[key]))
        
        # Sections
        for section in article_data.get('sections', []):
            if section.get('content'):
                text_parts.append(section['content'])
        
        return ' '.join(text_parts)


async def test_spherecast_production():
    """Test blog generation for Spherecast with simplified prompt."""
    print("=" * 80)
    print("PRODUCTION TEST: Spherecast Blog Generation")
    print("Testing Simplified Prompt Quality Improvements")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verify API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: No API key found")
        print("   Set GOOGLE_API_KEY or GOOGLE_GEMINI_API_KEY environment variable")
        return False
    
    print("✅ API key found")
    print()
    
    # Spherecast configuration
    job_config = {
        "primary_keyword": "AI podcast platform for content creators",
        "company_url": "https://www.spherecast.ai",
        "company_name": "Spherecast",
        "language": "en",
        "country": "US",
    }
    
    print("📝 Test Configuration:")
    print(f"   Company: {job_config['company_name']}")
    print(f"   URL: {job_config['company_url']}")
    print(f"   Keyword: {job_config['primary_keyword']}")
    print()
    print("⏱️  Expected duration: 5-10 minutes")
    print()
    
    # Create workflow engine
    engine = WorkflowEngine()
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
    
    try:
        print("🚀 Starting blog generation...")
        print()
        
        # Execute workflow
        context = await engine.execute(
            job_id=f"spherecast-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            job_config=job_config
        )
        
        print()
        print("=" * 80)
        print("QUALITY AUDIT RESULTS")
        print("=" * 80)
        print()
        
        # Extract article data for audit
        if not context.validated_article:
            print("❌ No validated article found in context")
            return False
        
        article = context.validated_article  # This is a Dict[str, Any]
        
        # Extract sections from article dict
        sections = []
        for i in range(1, 10):
            title_key = f'section_{i:02d}_title'
            content_key = f'section_{i:02d}_content'
            if title_key in article and article[title_key]:
                sections.append({
                    'title': article[title_key],
                    'content': article.get(content_key, '')
                })
        
        # Run quality audit
        auditor = QualityAuditor()
        audit_result = auditor.audit_article({
            'headline': article.get('headline', ''),
            'subtitle': article.get('subtitle', ''),
            'teaser': article.get('teaser', ''),
            'intro': article.get('intro', ''),
            'direct_answer': article.get('direct_answer', ''),
            'sections': sections,
            'primary_keyword': job_config['primary_keyword'],
        })
        
        # Display results
        print(f"📊 Quality Score: {audit_result['score']}/100")
        print()
        
        print("📋 Metrics:")
        for key, value in audit_result['metrics'].items():
            print(f"   {key}: {value}")
        print()
        
        if audit_result['issues']:
            print("⚠️  Issues Found:")
            for issue in audit_result['issues']:
                print(f"   - {issue}")
        else:
            print("✅ No quality issues found!")
        
        print()
        print("=" * 80)
        print("VERIFICATION SUMMARY")
        print("=" * 80)
        
        checks = []
        
        # Verify fixes
        checks.append(("Grammar errors", audit_result['metrics']['grammar_errors'] == 0))
        checks.append(("Citation-only paragraphs", audit_result['metrics']['citation_only_paras'] == 0))
        checks.append(("Headline length ≤60", audit_result['metrics']['headline_length'] <= 60))
        checks.append(("Intro length ≤300 words", audit_result['metrics']['intro_words'] <= 300))
        checks.append(("No empty headings", audit_result['metrics']['empty_headings'] == 0))
        checks.append(("Keyword density 8-12", 8 <= audit_result['metrics'].get('keyword_mentions', 0) <= 12))
        
        print()
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}")
        
        all_passed = all(passed for _, passed in checks)
        
        print()
        if all_passed:
            print("✅ ALL QUALITY CHECKS PASSED!")
            print("   Simplified prompt is working correctly.")
        else:
            print("⚠️  Some quality checks failed.")
            print("   Review issues above and refine prompt if needed.")
        
        # Save results
        output_file = Path(__file__).parent / "test_outputs" / f"spherecast_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({
                'test_config': job_config,
                'audit_result': audit_result,
                'article': {
                    'headline': article.get('headline', ''),
                    'subtitle': article.get('subtitle', ''),
                    'intro_length': audit_result['metrics']['intro_words'],
                    'sections_count': len(sections),
                },
                'timestamp': datetime.now().isoformat(),
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_spherecast_production())
    sys.exit(0 if success else 1)

