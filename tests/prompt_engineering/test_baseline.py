#!/usr/bin/env python3
"""
Baseline Quality Test for Blog Generation Prompt

Tests the current prompt against quality criteria:
- Grammar/typos
- Citation embedding
- Length compliance
- Structure quality
- AEO optimization
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.prompts.main_article import get_main_article_prompt


class PromptQualityAuditor:
    """Audit prompt quality and output compliance."""
    
    def __init__(self):
        self.issues = []
        self.metrics = {}
    
    def audit_prompt(self, prompt: str) -> Dict[str, Any]:
        """Audit the prompt itself for quality."""
        issues = []
        metrics = {}
        
        # Check prompt length
        prompt_length = len(prompt)
        metrics['prompt_length'] = prompt_length
        
        if prompt_length > 5000:
            issues.append("Prompt is very long (>5000 chars)")
        elif prompt_length < 1000:
            issues.append("Prompt is very short (<1000 chars)")
        
        # Check for critical rules
        critical_rules = [
            "citation",
            "headline",
            "intro",
            "keyword",
            "NEVER"
        ]
        
        found_rules = []
        for rule in critical_rules:
            if rule.lower() in prompt.lower():
                found_rules.append(rule)
        
        metrics['critical_rules_present'] = len(found_rules)
        metrics['critical_rules_coverage'] = len(found_rules) / len(critical_rules)
        
        if metrics['critical_rules_coverage'] < 0.8:
            issues.append(f"Missing critical rules: {set(critical_rules) - set(found_rules)}")
        
        # Check for variable interpolation
        variable_pattern = r'\{[^}]+\}'
        variables = re.findall(variable_pattern, prompt)
        metrics['variable_count'] = len(set(variables))
        
        if metrics['variable_count'] < 5:
            issues.append("Too few variables - may not be dynamic enough")
        
        return {
            'issues': issues,
            'metrics': metrics,
            'score': self._calculate_prompt_score(issues, metrics)
        }
    
    def audit_output(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Audit generated article output."""
        issues = []
        metrics = {}
        
        # Grammar check (basic)
        text_content = self._extract_text_content(output)
        grammar_issues = self._check_grammar(text_content)
        issues.extend(grammar_issues)
        metrics['grammar_errors'] = len(grammar_issues)
        
        # Citation check
        citation_issues = self._check_citations(output)
        issues.extend(citation_issues)
        metrics['citation_issues'] = len(citation_issues)
        
        # Length check
        length_issues = self._check_lengths(output)
        issues.extend(length_issues)
        metrics['length_issues'] = len(length_issues)
        
        # Structure check
        structure_issues = self._check_structure(output)
        issues.extend(structure_issues)
        metrics['structure_issues'] = len(structure_issues)
        
        # Calculate overall score
        metrics['total_issues'] = len(issues)
        metrics['score'] = self._calculate_output_score(issues, metrics)
        
        return {
            'issues': issues,
            'metrics': metrics
        }
    
    def _extract_text_content(self, output: Dict[str, Any]) -> str:
        """Extract all text content from output."""
        text_parts = []
        
        # Headline, subtitle, teaser
        for key in ['Headline', 'Subtitle', 'Teaser', 'Intro', 'Direct_Answer']:
            if key in output and output[key]:
                text_parts.append(str(output[key]))
        
        # Section content
        for i in range(1, 10):
            key = f'section_{i:02d}_content'
            if key in output and output[key]:
                text_parts.append(str(output[key]))
        
        return ' '.join(text_parts)
    
    def _check_grammar(self, text: str) -> List[str]:
        """Check for common grammar errors."""
        issues = []
        
        # Common errors from audit
        errors = {
            'speed upd': 'speed up',
            'applys': 'applies',
            'Also,,': 'Also,',
            '. .': '.',
        }
        
        for error, correction in errors.items():
            if error in text:
                issues.append(f"Grammar error: '{error}' should be '{correction}'")
        
        return issues
    
    def _check_citations(self, output: Dict[str, Any]) -> List[str]:
        """Check citation embedding."""
        issues = []
        
        # Check section content for citation-only paragraphs
        for i in range(1, 10):
            key = f'section_{i:02d}_content'
            if key in output and output[key]:
                content = str(output[key])
                # Look for paragraphs with only citations
                citation_only_pattern = r'<p>\s*\[\d+\](\[\d+\])*\s*</p>'
                matches = re.findall(citation_only_pattern, content)
                if matches:
                    issues.append(f"Section {i}: Citation-only paragraph found")
        
        return issues
    
    def _check_lengths(self, output: Dict[str, Any]) -> List[str]:
        """Check length compliance."""
        issues = []
        
        # Headline length
        if 'Headline' in output and output['Headline']:
            headline_len = len(output['Headline'])
            if headline_len > 60:
                issues.append(f"Headline too long: {headline_len} chars (max 60)")
            elif headline_len < 30:
                issues.append(f"Headline too short: {headline_len} chars (min 30)")
        
        # Intro length (word count)
        if 'Intro' in output and output['Intro']:
            intro_text = str(output['Intro'])
            word_count = len(intro_text.split())
            if word_count > 300:
                issues.append(f"Intro too long: {word_count} words (max 300)")
            elif word_count < 100:
                issues.append(f"Intro too short: {word_count} words (min 100)")
        
        return issues
    
    def _check_structure(self, output: Dict[str, Any]) -> List[str]:
        """Check structure quality."""
        issues = []
        
        # Count sections with content
        sections_with_content = 0
        empty_sections = []
        
        for i in range(1, 10):
            title_key = f'section_{i:02d}_title'
            content_key = f'section_{i:02d}_content'
            
            if title_key in output and output[title_key]:
                if content_key in output and output[content_key]:
                    content = str(output[content_key])
                    # Check if content is substantial (not just citations)
                    if len(content.strip()) > 100:
                        sections_with_content += 1
                    else:
                        empty_sections.append(i)
                else:
                    empty_sections.append(i)
        
        if sections_with_content < 8:
            issues.append(f"Too few sections with content: {sections_with_content} (min 8)")
        
        if empty_sections:
            issues.append(f"Empty sections found: {empty_sections}")
        
        return issues
    
    def _calculate_prompt_score(self, issues: List[str], metrics: Dict[str, Any]) -> float:
        """Calculate prompt quality score."""
        base_score = 100
        
        # Deduct for issues
        score = base_score - (len(issues) * 5)
        
        # Bonus for good coverage
        if metrics.get('critical_rules_coverage', 0) >= 0.9:
            score += 5
        
        return max(0, min(100, score))
    
    def _calculate_output_score(self, issues: List[str], metrics: Dict[str, Any]) -> float:
        """Calculate output quality score."""
        base_score = 100
        
        # Deduct for issues
        score = base_score - (len(issues) * 5)
        
        # Deduct for specific issue types
        score -= metrics.get('grammar_errors', 0) * 3
        score -= metrics.get('citation_issues', 0) * 5
        score -= metrics.get('length_issues', 0) * 2
        score -= metrics.get('structure_issues', 0) * 3
        
        return max(0, min(100, score))


def test_prompt_generation():
    """Test that prompt generates correctly."""
    print("🧪 Testing Prompt Generation")
    print("=" * 60)
    
    # Test parameters
    test_keyword = "AI customer service automation"
    test_company = "Test Company"
    test_info = {
        "description": "A test company",
        "industry": "Technology"
    }
    
    try:
        prompt = get_main_article_prompt(
            primary_keyword=test_keyword,
            company_name=test_company,
            company_info=test_info,
            language="en",
            country="US"
        )
        
        print(f"✅ Prompt generated successfully")
        print(f"   Length: {len(prompt)} characters")
        
        # Audit prompt
        auditor = PromptQualityAuditor()
        audit_result = auditor.audit_prompt(prompt)
        
        print(f"\n📊 Prompt Quality Score: {audit_result['score']}/100")
        print(f"   Critical rules coverage: {audit_result['metrics']['critical_rules_coverage']*100:.1f}%")
        print(f"   Variables found: {audit_result['metrics']['variable_count']}")
        
        if audit_result['issues']:
            print(f"\n⚠️  Issues found:")
            for issue in audit_result['issues']:
                print(f"   - {issue}")
        else:
            print("\n✅ No issues found!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating prompt: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_prompt_generation()
    sys.exit(0 if success else 1)

