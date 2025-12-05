#!/usr/bin/env python3
"""
Stress Test: Prompt Fixes Verification

Tests the fixed prompt with multiple scenarios to ensure:
- Keyword density enforcement (8-12 exact)
- Grammar fixes (proper nouns, capitalization)
- No repetition of errors
- Consistency across multiple runs
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


class StressTestAuditor:
    """Audit generated articles for all fixed issues."""
    
    def audit_article(self, article_data: dict, keyword: str) -> dict:
        """Comprehensive audit of article quality."""
        issues = []
        metrics = {}
        
        # Extract all text
        text_content = self._extract_text(article_data)
        text_lower = text_content.lower()
        
        # 1. Grammar errors check
        grammar_errors = {
            'speed upd': 'speed up',
            'applys': 'applies',
            'Also,,': 'Also,',
            'aPI': 'API',
            'gartner': 'Gartner',
            'nielsen': 'Nielsen',
        }
        
        found_errors = {}
        for error, correction in grammar_errors.items():
            pattern = re.compile(re.escape(error), re.IGNORECASE)
            matches = list(pattern.finditer(text_content))
            if matches:
                found_errors[error] = {
                    'correction': correction,
                    'count': len(matches),
                    'locations': [m.start() for m in matches[:3]]
                }
        
        if found_errors:
            issues.append(f"Grammar errors: {len(found_errors)} types found")
        metrics['grammar_errors'] = len(found_errors)
        metrics['grammar_error_details'] = found_errors
        
        # 2. Proper noun capitalization
        proper_nouns = ['gartner', 'nielsen', 'api']
        capitalization_errors = []
        for noun in proper_nouns:
            # Find lowercase instances that should be capitalized
            pattern = re.compile(r'\b' + re.escape(noun) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(text_content)
            for match in matches:
                if match.group().islower():
                    capitalization_errors.append({
                        'word': match.group(),
                        'position': match.start(),
                        'should_be': noun.capitalize() if noun != 'api' else 'API'
                    })
        
        if capitalization_errors:
            issues.append(f"Capitalization errors: {len(capitalization_errors)} found")
        metrics['capitalization_errors'] = len(capitalization_errors)
        
        # 3. Sentence start capitalization
        sentence_start_errors = []
        sentences = re.split(r'[.!?]\s+', text_content)
        for sentence in sentences[:50]:  # Check first 50 sentences
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:
                # Skip HTML tags and citations
                if not sentence.startswith('<') and not sentence.startswith('['):
                    if sentence[0].islower():
                        sentence_start_errors.append(sentence[:50])
        
        if sentence_start_errors:
            issues.append(f"Sentence start errors: {len(sentence_start_errors)} found")
        metrics['sentence_start_errors'] = len(sentence_start_errors)
        
        # 4. Keyword density check
        keyword_lower = keyword.lower()
        mentions = text_lower.count(keyword_lower)
        
        if mentions < 8:
            issues.append(f"Keyword density too low: {mentions} (min 8)")
        elif mentions > 12:
            issues.append(f"Keyword density too high: {mentions} (max 12)")
        
        metrics['keyword_mentions'] = mentions
        metrics['keyword_target'] = "8-12"
        
        # 5. Headline length
        headline = article_data.get('headline', '') or article_data.get('Headline', '')
        headline_len = len(headline)
        if headline_len > 60:
            issues.append(f"Headline too long: {headline_len} chars (max 60)")
        metrics['headline_length'] = headline_len
        
        # 6. Intro length
        intro = article_data.get('intro', '') or article_data.get('Intro', '')
        intro_words = len(intro.split())
        if intro_words > 300:
            issues.append(f"Intro too long: {intro_words} words (max 300)")
        metrics['intro_words'] = intro_words
        
        # 7. Citation-only paragraphs
        citation_only_count = 0
        for section in article_data.get('sections', []):
            content = section.get('content', '')
            paras = re.findall(r'<p>([^<]*)</p>', content)
            for para in paras:
                para_clean = re.sub(r'\[(\d+)\]', '', para).strip()
                if len(para_clean) < 10 and re.search(r'\[\d+\]', para):
                    citation_only_count += 1
        
        if citation_only_count > 0:
            issues.append(f"Citation-only paragraphs: {citation_only_count}")
        metrics['citation_only_paras'] = citation_only_count
        
        # Calculate quality score
        base_score = 100
        score = base_score
        score -= len(found_errors) * 15  # Grammar errors are critical
        score -= len(capitalization_errors) * 5
        score -= len(sentence_start_errors) * 3
        score -= (1 if mentions < 8 or mentions > 12 else 0) * 10
        score -= (1 if headline_len > 60 else 0) * 5
        score -= (1 if intro_words > 300 else 0) * 5
        score -= citation_only_count * 5
        
        score = max(0, min(100, score))
        
        return {
            'issues': issues,
            'metrics': metrics,
            'score': score,
            'passed': len(issues) == 0
        }
    
    def _extract_text(self, article_data: dict) -> str:
        """Extract all text content."""
        text_parts = []
        
        for key in ['headline', 'Headline', 'subtitle', 'Subtitle', 'teaser', 'Teaser', 
                    'intro', 'Intro', 'direct_answer', 'Direct_Answer']:
            if key in article_data and article_data[key]:
                text_parts.append(str(article_data[key]))
        
        for section in article_data.get('sections', []):
            if section.get('content'):
                text_parts.append(section['content'])
        
        return ' '.join(text_parts)


async def stress_test_single(keyword: str, company_name: str, company_url: str, test_num: int):
    """Run a single stress test."""
    print(f"\n{'='*70}")
    print(f"STRESS TEST #{test_num}: {keyword}")
    print(f"{'='*70}")
    
    job_config = {
        "primary_keyword": keyword,
        "company_url": company_url,
        "company_name": company_name,
        "language": "en",
        "country": "US",
    }
    
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
        context = await engine.execute(
            job_id=f"stress-test-{test_num}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            job_config=job_config
        )
        
        if not context.validated_article:
            return {'success': False, 'error': 'No article generated'}
        
        article = context.validated_article
        
        # Extract sections
        sections = []
        for i in range(1, 10):
            title_key = f'section_{i:02d}_title'
            content_key = f'section_{i:02d}_content'
            if title_key in article and article[title_key]:
                sections.append({
                    'title': article[title_key],
                    'content': article.get(content_key, '')
                })
        
        # Audit
        auditor = StressTestAuditor()
        audit_result = auditor.audit_article({
            'headline': article.get('headline', '') or article.get('Headline', ''),
            'subtitle': article.get('subtitle', '') or article.get('Subtitle', ''),
            'intro': article.get('intro', '') or article.get('Intro', ''),
            'sections': sections,
        }, keyword)
        
        return {
            'success': True,
            'keyword': keyword,
            'audit': audit_result,
            'headline': article.get('headline', '') or article.get('Headline', ''),
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


async def run_stress_test():
    """Run comprehensive stress test."""
    print("=" * 70)
    print("PROMPT FIXES STRESS TEST")
    print("Testing: Keyword density, Grammar, Capitalization")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Verify API key
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        print("❌ ERROR: No API key found")
        return False
    
    print("✅ API key found")
    print()
    
    # Test scenarios - different keywords to stress test
    test_scenarios = [
        {
            'keyword': 'AI customer service automation',
            'company': 'TestCorp',
            'url': 'https://example.com'
        },
        {
            'keyword': 'cloud data security best practices',
            'company': 'SecureCloud',
            'url': 'https://example.com'
        },
    ]
    
    print(f"📋 Running {len(test_scenarios)} stress test scenarios...")
    print("   Each test validates: keyword density, grammar, capitalization")
    print()
    
    results = []
    for i, scenario in enumerate(test_scenarios, 1):
        result = await stress_test_single(
            scenario['keyword'],
            scenario['company'],
            scenario['url'],
            i
        )
        results.append(result)
        
        if result.get('success'):
            audit = result['audit']
            print(f"✅ Test #{i} completed")
            print(f"   Quality Score: {audit['score']}/100")
            print(f"   Keyword mentions: {audit['metrics']['keyword_mentions']} (target: 8-12)")
            print(f"   Grammar errors: {audit['metrics']['grammar_errors']}")
            print(f"   Capitalization errors: {audit['metrics']['capitalization_errors']}")
            if audit['issues']:
                print(f"   ⚠️  Issues: {', '.join(audit['issues'][:3])}")
        else:
            print(f"❌ Test #{i} failed: {result.get('error', 'Unknown error')}")
    
    print()
    print("=" * 70)
    print("STRESS TEST SUMMARY")
    print("=" * 70)
    
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    print()
    
    if successful:
        # Aggregate metrics
        avg_score = sum(r['audit']['score'] for r in successful) / len(successful)
        avg_keyword_mentions = sum(r['audit']['metrics']['keyword_mentions'] for r in successful) / len(successful)
        total_grammar_errors = sum(r['audit']['metrics']['grammar_errors'] for r in successful)
        total_capitalization_errors = sum(r['audit']['metrics']['capitalization_errors'] for r in successful)
        
        print("📊 Aggregate Metrics:")
        print(f"   Average Quality Score: {avg_score:.1f}/100")
        print(f"   Average Keyword Mentions: {avg_keyword_mentions:.1f} (target: 8-12)")
        print(f"   Total Grammar Errors: {total_grammar_errors}")
        print(f"   Total Capitalization Errors: {total_capitalization_errors}")
        print()
        
        # Check if fixes are working
        keyword_in_range = sum(1 for r in successful 
                              if 8 <= r['audit']['metrics']['keyword_mentions'] <= 12)
        no_grammar_errors = sum(1 for r in successful 
                                if r['audit']['metrics']['grammar_errors'] == 0)
        no_capitalization_errors = sum(1 for r in successful 
                                       if r['audit']['metrics']['capitalization_errors'] == 0)
        
        print("✅ Fix Verification:")
        print(f"   Keyword density in range: {keyword_in_range}/{len(successful)}")
        print(f"   No grammar errors: {no_grammar_errors}/{len(successful)}")
        print(f"   No capitalization errors: {no_capitalization_errors}/{len(successful)}")
        print()
        
        if keyword_in_range == len(successful) and no_grammar_errors == len(successful):
            print("🎉 ALL FIXES VERIFIED - Prompt improvements working!")
        else:
            print("⚠️  Some issues remain - prompt may need further refinement")
    
    # Save results
    output_file = Path(__file__).parent / "test_outputs" / f"stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump({
            'test_scenarios': test_scenarios,
            'results': results,
            'timestamp': datetime.now().isoformat(),
        }, f, indent=2)
    
    print(f"💾 Results saved to: {output_file}")
    
    return len(successful) == len(results) and len(successful) > 0


if __name__ == "__main__":
    success = asyncio.run(run_stress_test())
    sys.exit(0 if success else 1)

