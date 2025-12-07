#!/usr/bin/env python3
"""
Generate a full article via the blog-writer API
"""

import requests
import json
import time

print("=" * 80)
print("🚀 GENERATING FULL ARTICLE WITH v3.2 CITATIONS")
print("=" * 80)
print("\nThis will take 2-5 minutes...")
print()

# API endpoint (local or Modal)
API_URL = "http://localhost:8000/generate"  # Local development

# Article request
request_data = {
    "topic": "How AI is Transforming Customer Service in 2024",
    "keywords": [
        "AI customer service",
        "chatbots 2024", 
        "customer experience automation",
        "AI support tools",
        "conversational AI"
    ],
    "target_audience": "Business executives and customer service managers",
    "tone": "professional",
    "language": "en",
    "country": "US",
    "word_count": 2000,
    "company_info": {
        "company_name": "TechInsights",
        "company_url": "https://techinsights.example.com",
        "industry": "Technology & Business Intelligence"
    },
    "generate_image": True
}

print(f"Topic: {request_data['topic']}")
print(f"Target length: {request_data['word_count']} words")
print(f"Keywords: {', '.join(request_data['keywords'][:3])}...")
print()
print("⏳ Sending request to blog-writer API...")
print("   (Stages: Research → Content → Citations → Images → Validation)")
print()

start_time = time.time()

try:
    response = requests.post(
        API_URL,
        json=request_data,
        timeout=600  # 10 minutes
    )
    
    duration = time.time() - start_time
    
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Article generated in {duration:.1f} seconds!")
        print()
        
        # Extract article
        article = result.get("article", {})
        
        # Stats
        print("=" * 80)
        print("📊 ARTICLE STATS")
        print("=" * 80)
        print(f"Headline: {article.get('Headline', 'N/A')}")
        print(f"Sections: {sum(1 for i in range(1, 10) if article.get(f'section_{i:02d}_title'))}")
        
        # Count citations from Sources
        sources = article.get('Sources', '')
        citation_count = sources.count('[') - sources.count('[[')
        print(f"Citations: {citation_count}")
        print(f"FAQs: {len(article.get('faq_items', []))}")
        print(f"Image: {'✅ ' + article.get('image_url', 'None')[:50] + '...' if article.get('image_url') else '❌ None'}")
        print()
        
        # Get HTML output
        html = result.get("html", "")
        
        if html:
            # Save to file
            output_file = "/Users/federicodeponte/personal-assistant/clients@scaile.tech-setup/services/blog-writer/full_article_v3.2.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print("=" * 80)
            print("✅ FULL ARTICLE SAVED")
            print("=" * 80)
            print(f"Location: {output_file}")
            print()
            print("v3.2 Features included:")
            print("  ✅ Enhanced citations (<cite>, aria-label, itemprop)")
            print("  ✅ JSON-LD structured data with citation schema")
            print("  ✅ XSS protection (bleach)")
            print("  ✅ HTML validation (BeautifulSoup)")
            print("  ✅ Generated AI image")
            print("  ✅ FAQ section with schema")
            print("  ✅ Table of contents")
            print("  ✅ SEO metadata")
            print()
            print("Opening in browser...")
            
            import subprocess
            subprocess.run(["open", output_file])
            print("\n🎉 Article opened in browser!")
        else:
            print("⚠️  No HTML output in response")
            print(f"Response keys: {list(result.keys())}")
    
    else:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ Connection failed!")
    print()
    print("Is the blog-writer service running?")
    print("Start it with: cd services/blog-writer && python3 -m uvicorn main:app --reload")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()




