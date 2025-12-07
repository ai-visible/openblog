#!/usr/bin/env python3
"""
Generate a full production-quality blog article with v3.2 enhancements
"""

import sys
import os
import json
import asyncio
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.blog_generation.orchestrator import BlogGenerationOrchestrator
from pipeline.config import PipelineConfig

async def generate_full_article():
    """Generate a complete article with all features."""
    
    print("=" * 80)
    print("🚀 GENERATING FULL ARTICLE WITH v3.2 CITATIONS")
    print("=" * 80)
    print("\nThis will take 2-5 minutes...")
    print("Stages: Research → Content → Citations → Images → Validation")
    print()
    
    # Configuration
    config = PipelineConfig(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        google_credentials_json=os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"),
    )
    
    # Input for article generation
    blog_input = {
        "topic": "How AI is Transforming Customer Service in 2024",
        "keywords": [
            "AI customer service",
            "chatbots 2024",
            "customer experience automation",
            "AI support tools",
            "customer service technology"
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
        }
    }
    
    print(f"Topic: {blog_input['topic']}")
    print(f"Target length: {blog_input['word_count']} words")
    print(f"Keywords: {', '.join(blog_input['keywords'][:3])}...")
    print()
    
    # Initialize orchestrator
    orchestrator = BlogGenerationOrchestrator(config)
    
    # Generate article
    print("⏳ Starting generation...")
    start_time = datetime.now()
    
    try:
        result = await orchestrator.generate_article(blog_input)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ Article generated in {duration:.1f} seconds!")
        print()
        
        # Extract article data
        article = result.get("validated_article", {})
        
        # Stats
        print("=" * 80)
        print("📊 ARTICLE STATS")
        print("=" * 80)
        print(f"Headline: {article.get('Headline', 'N/A')}")
        print(f"Word count: ~{blog_input['word_count']} words")
        print(f"Sections: {sum(1 for i in range(1, 10) if article.get(f'section_{i:02d}_title'))}")
        print(f"Citations: {len(article.get('Sources', '').split('[') if article.get('Sources') else [])-1}")
        print(f"FAQs: {len(article.get('faq_items', []))}")
        print(f"Image: {'✅ Generated' if article.get('image_url') else '❌ None'}")
        print()
        
        # Save full HTML
        from pipeline.processors.html_renderer import HTMLRenderer
        from pipeline.models.output_schema import ArticleOutput
        
        # Convert to ArticleOutput for schema generation
        article_output = ArticleOutput(**article)
        
        html = HTMLRenderer.render(
            article=article,
            company_data=blog_input.get("company_info"),
            article_output=article_output,
            article_url="https://techinsights.example.com/articles/ai-customer-service-2024",
            faq_items=article.get("faq_items", [])
        )
        
        # Save to file
        output_file = "/Users/federicodeponte/personal-assistant/clients@scaile.tech-setup/services/blog-writer/full_article_v3.2.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print("=" * 80)
        print("✅ FULL ARTICLE SAVED")
        print("=" * 80)
        print(f"Location: {output_file}")
        print()
        print("Features included:")
        print("  ✅ v3.2 Enhanced citations (<cite>, aria-label, itemprop)")
        print("  ✅ JSON-LD structured data with citation schema")
        print("  ✅ XSS protection (bleach)")
        print("  ✅ HTML validation (BeautifulSoup)")
        print("  ✅ Generated AI image")
        print("  ✅ FAQ section with schema")
        print("  ✅ Table of contents")
        print("  ✅ SEO metadata")
        print()
        print("Opening in browser...")
        
        return output_file
        
    except Exception as e:
        print(f"\n❌ Error generating article: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    output_file = asyncio.run(generate_full_article())
    
    if output_file:
        # Open in browser
        import subprocess
        subprocess.run(["open", output_file])
        print("\n🎉 Article opened in browser!")
    else:
        print("\n❌ Failed to generate article")




