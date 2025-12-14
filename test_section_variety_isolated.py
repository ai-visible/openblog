"""
Isolated test to understand why Gemini isn't creating LONG sections.
Testing with minimal prompt to isolate the section variety issue.
"""
import json
import asyncio
import os
from dotenv import load_dotenv
from pipeline.models.gemini_client import GeminiClient
from pipeline.models.output_schema import ArticleOutput
from pipeline.models.gemini_client import build_article_response_schema

# Load environment variables
load_dotenv('.env.local')

async def test_section_variety():
    """Test section variety with focused prompt."""
    print("=== ISOLATED SECTION VARIETY TEST ===\n")
    
    # Initialize client
    client = GeminiClient()
    
    # Build schema
    response_schema = build_article_response_schema(client._genai)
    
    # MINIMAL, FOCUSED PROMPT - Only about section variety
    test_prompt = """Write a blog article about "cloud security best practices".

CRITICAL SECTION VARIETY REQUIREMENT:
You MUST create sections with VARIED lengths:
- At least 2 LONG sections: 700+ words each (8-12 paragraphs, comprehensive deep dives)
- At least 2 MEDIUM sections: 400-600 words each (5-7 paragraphs)
- Remaining sections: 200-300 words each (2-3 paragraphs, quick overviews)

DO NOT create all sections with similar lengths. Some sections MUST be MUCH longer than others.

Include:
- Headline
- Teaser
- Direct Answer
- Intro
- At least 5 sections with titles and content
- Meta Title and Meta Description
- image_01_url (Unsplash URL)
- image_01_alt_text

Keep total article around 3000 words."""
    
    # FOCUSED system instruction - Only section variety
    system_instruction = """You are a content writer. Output JSON matching the ArticleOutput schema.

CRITICAL SECTION VARIETY REQUIREMENT (THIS IS MANDATORY):
- You MUST create sections with VARIED lengths
- At least 2 LONG sections: 700+ words each (8-12 paragraphs, comprehensive deep dives with multiple examples, case studies, detailed explanations)
- At least 2 MEDIUM sections: 400-600 words each (5-7 paragraphs, balanced depth)
- Remaining sections: 200-300 words each (2-3 paragraphs, quick overviews)

WORD COUNT MATH:
For a 3000-word article:
- 2 LONG sections × 750 words = 1,500 words
- 2 MEDIUM sections × 500 words = 1,000 words
- 1 SHORT section × 250 words = 250 words
Total: ~2,750 words (perfect for variety)

CRITICAL: Do NOT distribute words evenly. You MUST create some sections that are MUCH longer than others.
When writing, decide BEFORE you start which sections will be LONG (700+ words) and which will be MEDIUM (400+ words).
For LONG sections, provide comprehensive coverage with multiple examples, case studies, detailed explanations, and extensive citations."""
    
    print("1. Testing with MINIMAL, FOCUSED prompt (only section variety):")
    print("   Calling Gemini API...")
    
    try:
        response = await client.generate_content(
            prompt=test_prompt,
            enable_tools=True,
            response_schema=response_schema,
            system_instruction=system_instruction
        )
        
        print(f"   ✅ API call succeeded ({len(response)} chars)")
        
        # Parse response
        data = json.loads(response)
        
        print("\n2. Analyzing section lengths:")
        sections = [k for k in data.keys() if k.startswith('section_') and k.endswith('_content') and data.get(k)]
        
        section_lengths = []
        for section_key in sorted(sections):
            content = data[section_key]
            word_count = len(content.split())
            section_lengths.append(word_count)
            section_type = 'SHORT' if word_count < 400 else 'MEDIUM' if word_count < 700 else 'LONG'
            print(f"   {section_key}: ~{word_count} words ({section_type})")
        
        long_sections = sum(1 for w in section_lengths if w >= 700)
        medium_sections = sum(1 for w in section_lengths if 400 <= w < 700)
        short_sections = sum(1 for w in section_lengths if w < 400)
        
        print(f"\n   Distribution: {long_sections} LONG, {medium_sections} MEDIUM, {short_sections} SHORT")
        
        if long_sections >= 2 and medium_sections >= 2:
            print("   ✅ SUCCESS - Variety achieved!")
        else:
            print("   ❌ FAILED - No LONG sections created")
            print(f"\n   Analysis:")
            print(f"   - Average section length: {sum(section_lengths) / len(section_lengths):.0f} words")
            print(f"   - Max section length: {max(section_lengths)} words")
            print(f"   - Min section length: {min(section_lengths)} words")
            print(f"   - All sections are {'similar' if max(section_lengths) - min(section_lengths) < 300 else 'varied'} in length")
            
            if max(section_lengths) < 700:
                print(f"\n   ⚠️  ROOT CAUSE: Even the longest section ({max(section_lengths)} words) is below the 700-word LONG threshold")
                print(f"   Gemini is not creating sections long enough to meet the LONG requirement.")
            
    except Exception as e:
        print(f"   ❌ API call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_section_variety())

