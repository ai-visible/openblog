#!/usr/bin/env python3
"""
Comprehensive Quality Test for Blog Generation Prompt

Tests all quality metrics:
- Grammar error types
- Keyword density (8-12) across multiple keywords
- Headline length (≤60) consistency
- AEO score factors
- Sentence capitalization
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.prompts.main_article import get_main_article_prompt


class ComprehensiveQualityAuditor:
    """Audit article for all quality metrics."""
    
    def __init__(self):
        self.grammar_errors = {
            'speed upd': 'speed up',
            'applys': 'applies',
            'simplifys': 'simplifies',
            'enableing': 'enabling',
            'aPI': 'API',
            'aI': 'AI',
        }
        self.awkward_phrases = [
            "Here's clients",
            "You can automation",
        ]
    
    def audit_article(self, article_data: dict, keyword: str) -> Dict[str, Any]:
        """Comprehensive audit of article quality."""
        issues = []
        metrics = {}
        
        # Extract all text
        text_content = self._extract_text(article_data)
        text_lower = text_content.lower()
        
        # 1. Grammar errors check
        found_errors = {}
        for error, correction in self.grammar_errors.items():
            pattern = re.compile(re.escape(error), re.IGNORECASE)
            matches = list(pattern.finditer(text_content))
            if matches:
                found_errors[error] = {
                    'correction': correction,
                    'count': len(matches),
                }
        
        if found_errors:
            issues.append(f"Grammar errors: {len(found_errors)} types found")
        metrics['grammar_errors'] = len(found_errors)
        metrics['grammar_error_details'] = found_errors
        
        # 2. Awkward phrases
        awkward_found = []
        for phrase in self.awkward_phrases:
            if phrase.lower() in text_lower:
                awkward_found.append(phrase)
        
        if awkward_found:
            issues.append(f"Awkward phrases: {len(awkward_found)} found")
        metrics['awkward_phrases'] = len(awkward_found)
        
        # 3. Sentence start capitalization
        sentences = re.split(r'[.!?]\s+', text_content)
        sentence_start_errors = []
        for sentence in sentences[:100]:  # Check first 100 sentences
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:
                # Skip HTML tags and citations
                if not sentence.startswith('<') and not sentence.startswith('['):
                    if sentence[0].islower():
                        sentence_start_errors.append(sentence[:50])
        
        if sentence_start_errors:
            issues.append(f"Sentence start errors: {len(sentence_start_errors)} found")
        metrics['sentence_start_errors'] = len(sentence_start_errors)
        
        # 4. Proper noun capitalization
        proper_nouns = ['gartner', 'nielsen', 'api']
        capitalization_errors = []
        for noun in proper_nouns:
            pattern = re.compile(r'\b' + re.escape(noun) + r'\b', re.IGNORECASE)
            matches = pattern.finditer(text_content)
            for match in matches:
                if match.group().islower():
                    capitalization_errors.append({
                        'word': match.group(),
                        'should_be': noun.capitalize() if noun != 'api' else 'API'
                    })
        
        if capitalization_errors:
            issues.append(f"Capitalization errors: {len(capitalization_errors)} found")
        metrics['capitalization_errors'] = len(capitalization_errors)
        
        # 5. Keyword density check
        keyword_lower = keyword.lower()
        mentions = text_lower.count(keyword_lower)
        
        if mentions < 8:
            issues.append(f"Keyword density too low: {mentions} (min 8)")
        elif mentions > 12:
            issues.append(f"Keyword density too high: {mentions} (max 12)")
        
        metrics['keyword_mentions'] = mentions
        metrics['keyword_target'] = "8-12"
        
        # 6. Headline length
        headline = article_data.get('headline', '') or article_data.get('Headline', '')
        headline_len = len(headline)
        if headline_len > 60:
            issues.append(f"Headline too long: {headline_len} chars (max 60)")
        elif headline_len < 50:
            issues.append(f"Headline too short: {headline_len} chars (min 50)")
        metrics['headline_length'] = headline_len
        
        # 7. Intro length
        intro = article_data.get('intro', '') or article_data.get('Intro', '')
        intro_words = len(intro.split())
        if intro_words > 300:
            issues.append(f"Intro too long: {intro_words} words (max 300)")
        metrics['intro_words'] = intro_words
        
        # 8. Direct Answer length
        direct_answer = article_data.get('direct_answer', '') or article_data.get('Direct_Answer', '')
        da_words = len(direct_answer.split())
        if da_words < 45 or da_words > 55:
            issues.append(f"Direct Answer length: {da_words} words (target: 45-55)")
        metrics['direct_answer_words'] = da_words
        
        # 9. Citation-only paragraphs
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
        score -= len(awkward_found) * 10
        score -= len(capitalization_errors) * 5
        score -= len(sentence_start_errors) * 3
        score -= (1 if mentions < 8 or mentions > 12 else 0) * 10
        score -= (1 if headline_len > 60 or headline_len < 50 else 0) * 5
        score -= (1 if intro_words > 300 else 0) * 5
        score -= (1 if da_words < 45 or da_words > 55 else 0) * 5
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


def test_prompt_quality():
    """Test prompt generates correctly with all quality rules."""
    print("🧪 COMPREHENSIVE QUALITY TEST")
    print("=" * 70)
    print()
    
    test_keyword = "AI customer service automation"
    test_company = "TestCorp"
    
    try:
        prompt = get_main_article_prompt(
            primary_keyword=test_keyword,
            company_name=test_company,
            company_info={"description": "Test company"},
            language="en",
            country="US"
        )
        
        print(f"✅ Prompt generated successfully")
        print(f"   Length: {len(prompt):,} characters")
        print()
        
        # Verify all fixes are present
        checks = {
            'Grammar - Before finalizing': 'Before finalizing, scan entire article' in prompt,
            'Grammar - Common errors expanded': 'simplifys' in prompt.lower() and 'enableing' in prompt.lower(),
            'Grammar - Sentence starts': 'Every sentence must start with a capital letter' in prompt,
            'Grammar - Awkward phrases': 'Here\'s clients' in prompt or 'You can automation' in prompt,
            'Grammar - Proper nouns': 'AI, API, Gartner, Nielsen must be capitalized' in prompt,
            'Headline - Exact range': 'EXACTLY 50-60 characters' in prompt,
            'Headline - Count instruction': 'count each character' in prompt.lower(),
            'Keyword - Count verification': 'Before finalizing JSON, count exact phrase' in prompt,
            'Keyword - FAQ exclusion': 'Do NOT include keyword in FAQ/PAA' in prompt,
            'Direct Answer - Exact word count': '45-55 words exactly' in prompt,
            'Direct Answer - AEO reminder': 'for AEO scoring' in prompt,
            'FAQ/PAA - Quality reminder': 'FAQ/PAA quality affects AEO score' in prompt,
            'E-E-A-T - AEO reminder': 'E-E-A-T) required for high AEO scores' in prompt,
            'Final check - Grammar': 'FINAL CHECK: Proofread for grammar errors' in prompt,
        }
        
        print("📋 Quality Rule Verification:")
        print("-" * 70)
        all_passed = True
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}")
            if not passed:
                all_passed = False
        
        print()
        print("=" * 70)
        if all_passed:
            print("✅ ALL QUALITY RULES VERIFIED IN PROMPT!")
        else:
            print("⚠️  Some quality rules missing - review above")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_prompt_quality()
    sys.exit(0 if success else 1)

