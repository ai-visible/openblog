#!/usr/bin/env python3
"""
Diagnose AEO Score - Identify why scores are below 90
"""

import sys
import json
import glob
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.utils.aeo_scorer import AEOScorer
from pipeline.models.output_schema import ArticleOutput

def diagnose_score(article_output, primary_keyword, input_data=None):
    """Diagnose AEO score breakdown."""
    scorer = AEOScorer()
    
    scores = {}
    
    # Score each component
    scores['direct_answer'] = scorer._score_direct_answer(article_output, primary_keyword)
    scores['qa_format'] = scorer._score_qa_format(article_output)
    scores['citation_clarity'] = scorer._score_citation_clarity(article_output)
    scores['natural_language'] = scorer._score_natural_language(article_output, primary_keyword)
    scores['structured_data'] = scorer._score_structured_data(article_output)
    scores['eat'] = scorer._score_eat(article_output, input_data) if input_data else 0.0
    
    total = sum(scores.values())
    
    print("=" * 80)
    print("AEO SCORE DIAGNOSIS")
    print("=" * 80)
    print(f"\nTotal Score: {total:.1f}/100")
    print(f"Target: >90")
    print(f"Gap: {90 - total:.1f} points needed")
    
    print("\n" + "-" * 80)
    print("COMPONENT BREAKDOWN:")
    print("-" * 80)
    
    max_scores = {
        'direct_answer': 25,
        'qa_format': 20,
        'citation_clarity': 15,
        'natural_language': 15,
        'structured_data': 10,
        'eat': 15,
    }
    
    for component, score in scores.items():
        max_score = max_scores[component]
        percentage = (score / max_score * 100) if max_score > 0 else 0
        status = "✅" if score >= max_score * 0.8 else "⚠️" if score >= max_score * 0.5 else "❌"
        missing = max_score - score
        
        print(f"{status} {component.replace('_', ' ').title():25s}: {score:5.1f}/{max_score:2.0f} ({percentage:5.1f}%)")
        if missing > 0:
            print(f"   Missing: {missing:.1f} points")
    
    print("\n" + "-" * 80)
    print("RECOMMENDATIONS TO REACH >90:")
    print("-" * 80)
    
    # Identify biggest gaps
    gaps = [(k, max_scores[k] - v) for k, v in scores.items() if max_scores[k] - v > 0]
    gaps.sort(key=lambda x: x[1], reverse=True)
    
    for component, missing in gaps[:3]:
        print(f"\n🔧 {component.replace('_', ' ').title()}: Missing {missing:.1f} points")
        if component == 'eat':
            print("   → Add author_bio, author_url, author_name to input_data")
        elif component == 'citation_clarity':
            print("   → Ensure 60%+ paragraphs have 2+ citations")
        elif component == 'qa_format':
            print("   → Ensure 2+ section titles are in question format")
        elif component == 'natural_language':
            print("   → Add more conversational phrases (8+ required)")
        elif component == 'structured_data':
            print("   → Add more lists (3+ required) and headings")
    
    return scores, total

if __name__ == "__main__":
    # Load latest test result
    files = glob.glob('test_outputs/local_test_*.json')
    if not files:
        print("No test results found")
        sys.exit(1)
    
    latest = max(files)
    print(f"Analyzing: {latest}\n")
    
    # This would need to load the actual ArticleOutput from the test
    # For now, just show the structure
    print("To diagnose a specific article, load ArticleOutput and run:")
    print("  diagnose_score(article_output, 'keyword', input_data)")

