"""
Test Stage 1 output - Show full prompt generation.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage
from pipeline.core.execution_context import ExecutionContext

async def test_stage1_output():
    """Test Stage 1 and show full output."""
    print("=" * 80)
    print("STAGE 1: PROMPT BUILD - FULL OUTPUT")
    print("=" * 80)
    
    # Create Stage 1 instance
    stage = PromptBuildStage()
    
    # Create execution context with test data
    context = ExecutionContext(
        job_id="test-stage1-output",
        job_config={
            "primary_keyword": "cloud security best practices",
            "language": "en",
        },
        company_data={
            "company_url": "https://example.com",
            "company_name": "Test Company",
            "industry": "Cybersecurity",
            "description": "A leading cybersecurity company providing cloud security solutions.",
            "products": ["Cloud Security Platform", "Threat Detection", "Compliance Management"],  # New name (opencontext compatible)
            "target_audience": "Enterprise IT security teams",
            "tone": "professional",  # New name (opencontext compatible)
            "competitors": ["Competitor A", "Competitor B"],
            "pain_points": [
                "Complex cloud environments",
                "Regulatory compliance challenges",
                "Threat detection gaps"
            ],
            "value_propositions": [
                "Unified security platform",
                "Real-time threat detection",
                "Automated compliance"
            ],
            "use_cases": [
                "Multi-cloud security",
                "Compliance automation",
                "Threat response"
            ],
            "content_themes": ["Cloud Security", "Compliance", "Threat Detection"],
            "system_instructions": "Focus on practical, actionable advice. Include real-world examples.",
            "client_knowledge_base": [
                "Founded in 2015",
                "Serves Fortune 500 companies",
                "ISO 27001 certified"
            ],
            "content_instructions": "Use conversational tone. Include statistics. Add case studies."
        }
    )
    
    print("\n📥 INPUT:")
    print(f"  Primary Keyword: {context.job_config['primary_keyword']}")
    print(f"  Language: {context.job_config['language']}")
    print(f"  Company URL: {context.company_data['company_url']}")
    print(f"  Company Name: {context.company_data['company_name']}")
    print(f"  Industry: {context.company_data['industry']}")
    
    # Execute Stage 1
    print("\n🔄 Executing Stage 1...\n")
    try:
        result_context = await stage.execute(context)
        
        print("=" * 80)
        print("STAGE 1 OUTPUT:")
        print("=" * 80)
        print(f"\n📝 Generated Prompt ({len(result_context.prompt)} characters):")
        print("-" * 80)
        print(result_context.prompt)
        print("-" * 80)
        
        print(f"\n📊 Context Stored:")
        print(f"  - prompt: {len(result_context.prompt)} chars")
        print(f"  - language: {result_context.language}")
        print(f"  - company_context: {type(result_context.company_context).__name__}")
        
        # Show company context details
        if hasattr(result_context.company_context, 'company_url'):
            print(f"\n🏢 Company Context:")
            print(f"  - company_url: {result_context.company_context.company_url}")
            print(f"  - company_name: {result_context.company_context.company_name}")
            print(f"  - industry: {result_context.company_context.industry}")
            print(f"  - tone: {result_context.company_context.tone}")
        
        return result_context
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = asyncio.run(test_stage1_output())
    if result:
        print("\n✅ Stage 1 test complete!")
    else:
        print("\n❌ Stage 1 test failed!")

