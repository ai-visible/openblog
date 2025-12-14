"""
Test with EXPLICIT section assignments - telling Gemini which sections should be LONG.
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

async def test_explicit_section_assignment():
    """Test with explicit section length assignments."""
    print("=== EXPLICIT SECTION ASSIGNMENT TEST ===\n")
    
    # Initialize client
    client = GeminiClient()
    
    # Build schema
    response_schema = build_article_response_schema(client._genai)
    
    # EXPLICIT ASSIGNMENT - Tell Gemini exactly which sections should be LONG
    test_prompt = """Write a blog article about "cloud security best practices".

SECTION LENGTH ASSIGNMENTS (MANDATORY - FOLLOW EXACTLY):
- section_01: MUST be LONG (700+ words, 8-12 paragraphs) - Comprehensive deep dive on "What is cloud security?"
- section_02: MUST be MEDIUM (400-600 words, 5-7 paragraphs) - Balanced explanation
- section_03: MUST be LONG (700+ words, 8-12 paragraphs) - Comprehensive deep dive on "How to implement cloud security"
- section_04: MUST be MEDIUM (400-600 words, 5-7 paragraphs) - Balanced explanation
- section_05: MUST be SHORT (200-300 words, 2-3 paragraphs) - Quick overview
- section_06: MUST be SHORT (200-300 words, 2-3 paragraphs) - Quick overview

CRITICAL: section_01 and section_03 MUST be 700+ words each. These are your LONG sections.
For LONG sections, provide:
- Multiple detailed examples
- Case studies
- Extensive citations (every paragraph)
- Comprehensive explanations
- Real-world scenarios

Include:
- Headline
- Teaser
- Direct Answer
- Intro
- 6 sections with titles and content (following length assignments above)
- Meta Title and Meta Description
- image_01_url (Unsplash URL)
- image_01_alt_text

Total article should be around 3000 words."""
    
    system_instruction = """You are a content writer. Output JSON matching the ArticleOutput schema.

CRITICAL SECTION LENGTH REQUIREMENTS:
The main prompt specifies which sections should be LONG (700+ words), MEDIUM (400-600 words), or SHORT (200-300 words).
You MUST follow these assignments exactly.

For LONG sections (700+ words):
- Provide comprehensive coverage
- Include multiple examples and case studies
- Add detailed explanations
- Use extensive citations (every paragraph)
- Write 8-12 paragraphs minimum

For MEDIUM sections (400-600 words):
- Balanced depth with examples
- 5-7 paragraphs
- Include citations in most paragraphs

For SHORT sections (200-300 words):
- Quick, focused answers
- 2-3 paragraphs
- Concise explanations"""
    
    print("1. Testing with EXPLICIT section assignments:")
    print("   (Telling Gemini: section_01 and section_03 MUST be LONG)")
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
            
            # Check if this was supposed to be LONG
            expected = ""
            if section_key == 'section_01_content' or section_key == 'section_03_content':
                expected = " (EXPECTED: LONG)"
            
            print(f"   {section_key}: ~{word_count} words ({section_type}){expected}")
        
        long_sections = sum(1 for w in section_lengths if w >= 700)
        medium_sections = sum(1 for w in section_lengths if 400 <= w < 700)
        short_sections = sum(1 for w in section_lengths if w < 400)
        
        print(f"\n   Distribution: {long_sections} LONG, {medium_sections} MEDIUM, {short_sections} SHORT")
        
        # Check specific sections
        section_01_words = len(data.get('section_01_content', '').split())
        section_03_words = len(data.get('section_03_content', '').split())
        
        print(f"\n   Expected LONG sections:")
        print(f"   - section_01: {section_01_words} words {'✅ LONG' if section_01_words >= 700 else '❌ NOT LONG (need 700+)'}")
        print(f"   - section_03: {section_03_words} words {'✅ LONG' if section_03_words >= 700 else '❌ NOT LONG (need 700+)'}")
        
        if long_sections >= 2:
            print("\n   ✅ SUCCESS - LONG sections created!")
        else:
            print("\n   ❌ FAILED - Still no LONG sections")
            print(f"\n   Analysis:")
            print(f"   - Max section length: {max(section_lengths)} words")
            print(f"   - section_01 (expected LONG): {section_01_words} words")
            print(f"   - section_03 (expected LONG): {section_03_words} words")
            
    except Exception as e:
        print(f"   ❌ API call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_explicit_section_assignment())

