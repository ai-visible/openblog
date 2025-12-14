"""
Isolated test to check image field generation and schema enforcement.
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

async def test_image_schema():
    """Test if Gemini generates image fields correctly."""
    print("=== ISOLATED IMAGE SCHEMA TEST ===\n")
    
    # Initialize client
    client = GeminiClient()
    
    # Build schema
    response_schema = build_article_response_schema(client._genai)
    
    # Check what fields are marked as required in the schema
    print("1. Checking schema required fields:")
    if hasattr(response_schema, 'required') and response_schema.required:
        print(f"   Required fields: {response_schema.required}")
        if 'image_01_url' in response_schema.required:
            print("   ✅ image_01_url is marked as REQUIRED in schema")
        else:
            print("   ❌ image_01_url is NOT in required list")
        if 'image_01_alt_text' in response_schema.required:
            print("   ✅ image_01_alt_text is marked as REQUIRED in schema")
        else:
            print("   ❌ image_01_alt_text is NOT in required list")
    else:
        print("   ⚠️  Schema has no required fields list")
    
    # Check Pydantic model
    print("\n2. Checking Pydantic model required fields:")
    required_fields = []
    for field_name, field_info in ArticleOutput.model_fields.items():
        if field_info.is_required():
            required_fields.append(field_name)
            if 'image' in field_name.lower():
                print(f"   ✅ {field_name} is REQUIRED in Pydantic model")
    
    print(f"\n   Total required fields: {len(required_fields)}")
    print(f"   Image-related required: {[f for f in required_fields if 'image' in f.lower()]}")
    
    # Simple test prompt
    test_prompt = """Write a short blog article about "cloud security best practices".

Include:
- Headline
- Teaser
- Direct Answer
- Intro
- At least 1 section with title and content
- Meta Title and Meta Description
- image_01_url: Provide a relevant Unsplash image URL
- image_01_alt_text: Provide alt text for the image

Keep it brief (500 words total)."""
    
    system_instruction = """You are a content writer. Output JSON matching the ArticleOutput schema.
CRITICAL: The schema requires image_01_url and image_01_alt_text - they are REQUIRED fields.
You MUST provide valid Unsplash URLs for image_01_url."""
    
    print("\n3. Testing Gemini API call with schema:")
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
        
        print("\n4. Checking generated fields:")
        image_fields = {k: v for k, v in data.items() if 'image' in k.lower()}
        
        if not image_fields:
            print("   ❌ NO image fields found in response!")
        else:
            for key, value in sorted(image_fields.items()):
                if value:
                    print(f"   ✅ {key}: {value[:80]}...")
                else:
                    print(f"   ❌ {key}: EMPTY")
        
        # Try to validate
        print("\n5. Validating against Pydantic model:")
        try:
            article = ArticleOutput(**data)
            print("   ✅ Validation PASSED")
            print(f"   image_01_url: {article.image_01_url[:80] if article.image_01_url else 'MISSING'}...")
            print(f"   image_01_alt_text: {article.image_01_alt_text[:80] if article.image_01_alt_text else 'MISSING'}...")
        except Exception as e:
            print(f"   ❌ Validation FAILED: {e}")
            
    except Exception as e:
        print(f"   ❌ API call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_image_schema())

