"""
Manual Testing Checklist for Refresh Workflow v2.0

Run these tests manually to verify all functionality works as expected.
"""

import asyncio
import os
import json
from service.api import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Ensure API key is set
os.environ.setdefault("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))

def test_1_refresh_html_with_stat_updates():
    """Test 1: Refresh HTML article with stat updates → verify JSON output, no hallucinations"""
    print("\n=== TEST 1: HTML Refresh with Stat Updates ===")
    
    html_content = """
    <h1>AI Adoption Trends</h1>
    <h2>Market Overview</h2>
    <p>In 2023, approximately 45% of enterprises adopted AI solutions.</p>
    <p>The market was valued at $150 billion globally.</p>
    """
    
    response = client.post("/refresh", json={
        "content": html_content,
        "content_format": "html",
        "instructions": ["Update all 2023 statistics to 2025 data"],
        "target_sections": [0],
        "output_format": "json"
    })
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Sections Updated: {data.get('sections_updated')}")
        
        # Check for hallucinations
        refreshed_content = data.get('refreshed_content', {})
        for section in refreshed_content.get('sections', []):
            content = section.get('content', '')
            if 'You can aI' in content or 'What is How Do' in content:
                print("❌ HALLUCINATION DETECTED!")
            else:
                print("✅ No hallucinations detected")
        
        print(f"Refreshed Content: {json.dumps(refreshed_content, indent=2)[:200]}...")
    else:
        print(f"❌ Error: {response.json()}")


def test_2_refresh_with_malformed_instruction():
    """Test 2: Refresh with malformed instruction → verify error handling"""
    print("\n=== TEST 2: Malformed Instruction ===")
    
    response = client.post("/refresh", json={
        "content": "<h1>Test</h1>",
        "instructions": [],  # Empty instructions
        "output_format": "json"
    })
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 422:
        print("✅ Correctly rejected empty instructions with 422")
    else:
        print(f"❌ Expected 422, got {response.status_code}")
    print(f"Response: {response.json()}")


def test_3_rate_limiting():
    """Test 3: Make 15 requests in 1 minute → verify rate limiting (429 after 10)"""
    print("\n=== TEST 3: Rate Limiting ===")
    
    html_content = "<h1>Test</h1><p>Content</p>"
    
    success_count = 0
    rate_limited_count = 0
    
    for i in range(15):
        response = client.post("/refresh", json={
            "content": html_content,
            "instructions": ["Make it better"],
            "output_format": "json"
        })
        
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited_count += 1
        
        print(f"Request {i+1}: {response.status_code}")
    
    print(f"\n✅ Success: {success_count}")
    print(f"🚫 Rate Limited: {rate_limited_count}")
    
    if rate_limited_count > 0 and success_count <= 10:
        print("✅ Rate limiting working correctly")
    else:
        print("❌ Rate limiting may not be working as expected")


def test_4_diff_preview():
    """Test 4: Request diff preview → verify additions/deletions highlighted"""
    print("\n=== TEST 4: Diff Preview ===")
    
    html_content = """
    <h1>Original Article</h1>
    <h2>Section One</h2>
    <p>This is the original content from 2023.</p>
    """
    
    response = client.post("/refresh", json={
        "content": html_content,
        "content_format": "html",
        "instructions": ["Update year to 2025"],
        "target_sections": [0],
        "output_format": "html",
        "include_diff": True
    })
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data.get('diff_text') and data.get('diff_html'):
            print("✅ Diff generated successfully")
            print(f"Diff Text (first 200 chars): {data['diff_text'][:200]}")
            print(f"Diff HTML present: {len(data['diff_html'])} chars")
        else:
            print("❌ Diff not generated")
    else:
        print(f"❌ Error: {response.json()}")


def test_5_markdown_refresh():
    """Test 5: Refresh markdown article → verify format conversion works"""
    print("\n=== TEST 5: Markdown Refresh ===")
    
    markdown_content = """
# Tech Trends

## Introduction

This content needs updating.

## Conclusion

Final thoughts here.
"""
    
    response = client.post("/refresh", json={
        "content": markdown_content,
        "content_format": "markdown",
        "instructions": ["Make it more technical", "Add examples"],
        "output_format": "markdown"
    })
    
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        if data.get('refreshed_markdown'):
            print("✅ Markdown output generated")
            print(f"Output (first 200 chars): {data['refreshed_markdown'][:200]}")
        else:
            print("❌ No markdown output")
    else:
        print(f"❌ Error: {response.json()}")


def test_6_concurrent_requests():
    """Test 6: Submit concurrent requests → verify no race conditions"""
    print("\n=== TEST 6: Concurrent Requests ===")
    
    import concurrent.futures
    
    def make_request(idx):
        html_content = f"<h1>Article {idx}</h1><p>Content {idx}</p>"
        response = client.post("/refresh", json={
            "content": html_content,
            "instructions": ["Improve tone"],
            "output_format": "json"
        })
        return (idx, response.status_code)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request, i) for i in range(5)]
        results = [f.result() for f in futures]
    
    success_count = sum(1 for _, status in results if status == 200)
    print(f"Concurrent requests: {len(results)}")
    print(f"Successful: {success_count}")
    
    if success_count == len(results):
        print("✅ All concurrent requests succeeded (no race conditions)")
    else:
        print("❌ Some concurrent requests failed")
        for idx, status in results:
            if status != 200:
                print(f"  Request {idx}: {status}")


if __name__ == "__main__":
    print("=" * 60)
    print("REFRESH WORKFLOW v2.0 - MANUAL TESTING")
    print("=" * 60)
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  WARNING: GEMINI_API_KEY not set!")
        print("Some tests may fail. Set GEMINI_API_KEY in environment.")
        print()
    
    try:
        test_1_refresh_html_with_stat_updates()
        test_2_refresh_with_malformed_instruction()
        test_3_rate_limiting()
        test_4_diff_preview()
        test_5_markdown_refresh()
        test_6_concurrent_requests()
        
        print("\n" + "=" * 60)
        print("MANUAL TESTING COMPLETE")
        print("=" * 60)
        print("\nReview results above to verify:")
        print("1. ✅ No hallucinations in JSON output")
        print("2. ✅ Error handling for malformed requests (422)")
        print("3. ✅ Rate limiting works (429 after 10 req/min)")
        print("4. ✅ Diff preview generates correctly")
        print("5. ✅ Markdown format conversion works")
        print("6. ✅ Concurrent requests succeed without race conditions")
        
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()

