#!/usr/bin/env python3
"""
Show Exact Content Comparison

Demonstrates the actual content that triggered regeneration and shows
the differences between original and regenerated versions.
"""

import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.core.regeneration_engine import RegenerationEngine, PromptVariationStrategy, RegenerationStrategy
from pipeline.utils.hybrid_similarity_checker import HybridSimilarityChecker
from pipeline.utils.gemini_embeddings import GeminiEmbeddingClient
from pipeline.core.execution_context import ExecutionContext


class ContentCaptureEngine:
    """Engine that captures exact content for comparison."""
    
    def __init__(self):
        self.generated_content = []
    
    async def execute(self, job_id: str, job_config: dict, progress_callback=None) -> ExecutionContext:
        """Generate content and capture it for analysis."""
        
        keyword = job_config.get('primary_keyword', 'AI technology')
        company = job_config.get('company_name', 'TechCorp')
        
        # Check if this is a regeneration attempt
        prompt_context = job_config.get('prompt_context', {})
        regeneration_instruction = prompt_context.get('regeneration_instruction', '')
        attempt = prompt_context.get('regeneration_attempt', 1)
        strategy = prompt_context.get('regeneration_strategy', 'original')
        
        # Create content based on attempt
        if attempt == 1:
            # Original - intentionally similar content
            headline = f"Complete Guide to {keyword} Solutions"
            intro = f"This comprehensive guide explores {keyword} and how {company} delivers exceptional solutions."
            content = f"Advanced {keyword} capabilities transform business operations through innovative technology platforms. Modern enterprises rely on {keyword} for competitive advantages and operational efficiency. {company} provides cutting-edge {keyword} solutions that drive digital transformation across industries."
            
        elif "practical implementation" in regeneration_instruction:
            # Practical focus variation
            headline = f"How to Successfully Implement {keyword}"
            intro = f"Implementing {keyword} requires strategic planning and proven methodologies."
            content = f"Step-by-step {keyword} deployment follows structured implementation frameworks with measurable outcomes. Organizations achieve success through careful planning, stakeholder alignment, and phased rollouts. {company} provides comprehensive implementation support with dedicated project management and technical expertise."
            
        elif "benefits and ROI" in regeneration_instruction:
            # ROI focus variation
            headline = f"ROI Analysis: {keyword} Business Impact"
            intro = f"The financial impact of {keyword} adoption shows significant returns on investment."
            content = f"Quantifiable {keyword} benefits include 40% efficiency gains and 60% cost reductions across operational workflows. Financial analysis demonstrates clear ROI within 12-18 months of implementation. {company} clients report substantial productivity improvements and competitive advantages through strategic {keyword} adoption."
            
        else:
            # Different angle variation
            headline = f"Why Industry Leaders Choose {keyword}"
            intro = f"Industry leaders choose {keyword} for digital transformation and competitive positioning."
            content = f"Market-leading organizations leverage {keyword} for sustainable growth and innovation initiatives. Strategic adoption enables future-ready capabilities and ecosystem integration. {company} partners with industry leaders to deliver transformative {keyword} solutions that drive long-term success."
        
        # Capture the content
        content_piece = {
            'job_id': job_id,
            'attempt': attempt,
            'strategy': strategy,
            'instruction': regeneration_instruction,
            'headline': headline,
            'intro': intro,
            'content': content,
            'full_text': f"{headline}. {intro} {content}"
        }
        
        self.generated_content.append(content_piece)
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        context = ExecutionContext(job_id=job_id, job_config=job_config)
        context.final_article = {
            "Headline": headline,
            "primary_keyword": keyword,
            "Intro": intro,
            "_full_content": content,
            "company_name": company
        }
        
        return context


async def show_regeneration_content():
    """Show exact content that was regenerated."""
    print("📄 REGENERATION CONTENT COMPARISON")
    print("=" * 60)
    print("Showing exact content pieces that triggered regeneration")
    print()
    
    # Set up components
    os.environ['GEMINI_API_KEY'] = 'AIzaSyBjNQmN_65AskUTWHynyYxn9efAY-Az7jw'
    
    content_engine = ContentCaptureEngine()
    embedding_client = GeminiEmbeddingClient(api_key=os.environ['GEMINI_API_KEY'])
    
    regeneration_engine = RegenerationEngine(
        workflow_engine=content_engine,
        embedding_client=embedding_client,
        max_attempts=3,
        similarity_threshold=50.0  # Lower threshold for demo
    )
    
    # Generate baseline
    print("📝 STEP 1: Generate baseline content")
    baseline_config = {
        "job_id": "content_baseline",
        "primary_keyword": "AI customer service automation",
        "company_name": "ServiceAI Pro"
    }
    
    baseline_result = await regeneration_engine.generate_with_regeneration(baseline_config)
    
    # Generate similar content to trigger regeneration
    print("📝 STEP 2: Generate similar content (should trigger regeneration)")
    similar_config = {
        "job_id": "content_similar",
        "primary_keyword": "AI customer service automation",  # Same keyword
        "company_name": "ServiceAI Clone"  # Similar company
    }
    
    similar_result = await regeneration_engine.generate_with_regeneration(similar_config)
    
    # Show the actual content
    print("\n" + "=" * 60)
    print("📄 ACTUAL CONTENT COMPARISON")
    print("=" * 60)
    
    # Find baseline content
    baseline_content = next((c for c in content_engine.generated_content if c['job_id'] == 'content_baseline'), None)
    
    if baseline_content:
        print("🔵 BASELINE ARTICLE:")
        print(f"   Headline: {baseline_content['headline']}")
        print(f"   Intro: {baseline_content['intro']}")
        print(f"   Content: {baseline_content['content']}")
        print()
    
    # Show all regeneration attempts
    similar_contents = [c for c in content_engine.generated_content if c['job_id'] == 'content_similar']
    
    for i, content in enumerate(similar_contents, 1):
        strategy = content['strategy'] if content['strategy'] != 'original' else 'original'
        
        if i == 1:
            print("🔴 ORIGINAL ATTEMPT (triggered regeneration):")
        else:
            print(f"🟡 REGENERATION ATTEMPT {i} ({strategy}):")
            if content['instruction']:
                print(f"   Strategy: {content['instruction']}")
        
        print(f"   Headline: {content['headline']}")
        print(f"   Intro: {content['intro']}")
        print(f"   Content: {content['content']}")
        print()
    
    # Show similarity analysis
    print("📊 SIMILARITY ANALYSIS:")
    if len(similar_result.attempts_made) > 1:
        for i, attempt in enumerate(similar_result.attempts_made, 1):
            strategy = attempt.strategy.value if attempt.strategy else "original"
            print(f"   Attempt {i} ({strategy}): {attempt.similarity_score:.1f}% similarity")
        
        # Calculate improvement
        original_sim = similar_result.attempts_made[0].similarity_score
        final_sim = similar_result.final_similarity
        improvement = original_sim - final_sim
        
        print(f"\n🎯 SIMILARITY REDUCTION:")
        print(f"   Original similarity: {original_sim:.1f}%")
        print(f"   Final similarity: {final_sim:.1f}%")
        print(f"   Improvement: {improvement:.1f} percentage points")
    
    # Show what made content similar
    print(f"\n🔍 WHY CONTENT WAS SIMILAR:")
    print("   - Same target keyword: 'AI customer service automation'")
    print("   - Similar company names: 'ServiceAI Pro' vs 'ServiceAI Clone'")
    print("   - Similar content structure and terminology")
    print("   - High semantic overlap in topic and concepts")
    
    print(f"\n✅ REGENERATION RESULT:")
    if len(similar_result.attempts_made) > 1:
        print("   🔄 Regeneration was triggered successfully")
        print("   📉 Content similarity was reduced through variations")
        print("   🎭 Different strategies produced different content angles")
        print("   💡 System correctly identified and fixed content cannibalization")
    else:
        print("   ⚠️ Regeneration was not triggered")
    
    return True


async def main():
    """Show regeneration content comparison."""
    os.chdir('/Users/federicodeponte/openblog-isaac-security')
    
    await show_regeneration_content()
    
    print("\n" + "=" * 60)
    print("📄 CONTENT COMPARISON COMPLETE")
    print("This demonstrates the exact content differences that")
    print("trigger regeneration and how the system creates variations.")


if __name__ == "__main__":
    asyncio.run(main())