#!/usr/bin/env python3
"""
Generate a REAL article directly using the pipeline - NO API
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent / ".env.local"
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded {env_file}")
    
    # Map GOOGLE_GEMINI_API_KEY to GEMINI_API_KEY if needed
    if "GOOGLE_GEMINI_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_GEMINI_API_KEY"]
        print("✅ Mapped GOOGLE_GEMINI_API_KEY → GEMINI_API_KEY")
else:
    print(f"⚠️  No .env.local found, using system env")

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

from service.api import write_blog, BlogGenerationRequest

async def main():
    print("=" * 80)
    print("🚀 GENERATING REAL ARTICLE - DIRECT PIPELINE")
    print("=" * 80)
    print()
    
    request_data = {
        "primary_keyword": "AI code generation tools comparison 2025",
        "company_url": "https://techinsights.ai",
        "language": "en",
        "country": "US",
        "company_name": "TechInsights",
        "company_data": {
            "company_name": "TechInsights",
            "company_info": "Technology analysis and insights platform",
            "company_competitors": ["Generic AI Blog", "AI Tools Magazine"],
            "company_url": "https://techinsights.ai"
        },
        "batch_siblings": [
            {"slug": "software-development-trends", "title": "Software Development Trends 2025", "keyword": "software development trends"},
            {"slug": "ai-development-tools", "title": "Best AI Development Tools", "keyword": "AI development tools"},
            {"slug": "code-quality-automation", "title": "Code Quality Automation", "keyword": "code quality automation"}
        ]
    }
    
    request = BlogGenerationRequest(**request_data)
    
    print(f"📝 Keyword: {request.primary_keyword}")
    print(f"🌐 Language: {request.language}")
    print()
    print("⏳ Generating with full AI pipeline...")
    print("   (Should take ~2 minutes)")
    print()
    
    import time
    start = time.time()
    
    result = await write_blog(request)
    
    duration = time.time() - start
    
    if result.success:
        print(f"✅ GENERATED in {duration:.1f}s!")
        print()
        
        # Get raw values - handle different response structures
        html = getattr(result, 'html_content', None) or getattr(result, 'html', None) or ""
        headline = getattr(result, 'headline', None) or "N/A"
        sections_count = len(getattr(result, 'sections', None) or [])
        
        # Strip unwanted paragraph tags from metadata
        import re
        headline = re.sub(r'^<p>|</p>$', '', headline.strip())
        
        print("=" * 80)
        print("📊 ARTICLE QUALITY ANALYSIS")
        print("=" * 80)
        print(f"Headline: {headline}")
        print(f"Headline Length: {len(headline)} chars (target: 50-60)")
        print(f"Sections: {sections_count}")
        print(f"HTML size: {len(html)} chars")
        print()
        
        # Analyze keyword density
        keyword = "AI code generation tools 2025"
        keyword_count = html.lower().count(keyword.lower())
        print(f"🔑 PRIMARY KEYWORD ANALYSIS")
        print(f"   '{keyword}' mentions: {keyword_count} (target: 5-8)")
        if keyword_count < 5:
            print(f"   ⚠️  UNDER target by {5 - keyword_count}")
        elif keyword_count > 8:
            print(f"   ⚠️  OVER target by {keyword_count - 8}")
        else:
            print(f"   ✅ WITHIN target range")
        print()
        
        # Analyze lists
        ul_count = html.count('<ul>')
        ol_count = html.count('<ol>')
        total_lists = ul_count + ol_count
        print(f"📋 LIST ANALYSIS")
        print(f"   <ul> lists: {ul_count}")
        print(f"   <ol> lists: {ol_count}")
        print(f"   Total lists: {total_lists} (target: 5-8)")
        if total_lists < 5:
            print(f"   ⚠️  UNDER target by {5 - total_lists}")
        elif total_lists > 8:
            print(f"   ⚠️  OVER target by {total_lists - 8}")
        else:
            print(f"   ✅ WITHIN target range")
        print()
        
        # Analyze internal links
        internal_links = html.count('<a href=')
        print(f"🔗 INTERNAL LINKS ANALYSIS")
        print(f"   Links found: {internal_links} (target: 3-5)")
        if internal_links < 3:
            print(f"   ⚠️  UNDER target by {3 - internal_links}")
        elif internal_links > 5:
            print(f"   ⚠️  OVER target by {internal_links - 5}")
        else:
            print(f"   ✅ WITHIN target range")
        print()
        
        # Analyze citations
        citation_pattern = r'\[\d+\]'
        citations = re.findall(citation_pattern, html)
        unique_citations = len(set(citations))
        print(f"📚 CITATION ANALYSIS")
        print(f"   Total citation markers: {len(citations)}")
        print(f"   Unique sources: {unique_citations} (target: 8-12)")
        if unique_citations < 8:
            print(f"   ⚠️  UNDER target by {8 - unique_citations}")
        elif unique_citations > 20:
            print(f"   ⚠️  OVER max (20) by {unique_citations - 20}")
        else:
            print(f"   ✅ WITHIN target range")
        print()
        
        # Analyze paragraphs (rough estimate)
        p_tags = html.count('<p>')
        print(f"📄 PARAGRAPH ANALYSIS")
        print(f"   <p> tags: {p_tags}")
        
        # Sample paragraph word count from first section
        section_match = re.search(r'<p>(.+?)</p>', html, re.DOTALL)
        if section_match:
            first_para = section_match.group(1)
            # Strip HTML tags for word count
            clean_para = re.sub(r'<[^>]+>', '', first_para)
            word_count = len(clean_para.split())
            print(f"   First paragraph: {word_count} words (target: 60-100)")
            if word_count < 60:
                print(f"   ⚠️  UNDER target by {60 - word_count} words")
            elif word_count > 100:
                print(f"   ⚠️  OVER target by {word_count - 100} words")
            else:
                print(f"   ✅ WITHIN target range")
        print()
        
        # Analyze banned phrases
        banned = ["seamlessly", "leverage", "cutting-edge", "robust", "comprehensive", "holistic"]
        found_banned = []
        for phrase in banned:
            if phrase in html.lower():
                found_banned.append(phrase)
        
        print(f"🚫 BANNED PHRASES CHECK")
        if found_banned:
            print(f"   ⚠️  Found: {', '.join(found_banned)}")
        else:
            print(f"   ✅ No banned phrases detected")
        print()
        
        if html:
            # Fix HTML metadata issues (remove <p> tags from title/meta)
            html = re.sub(r'<title>&lt;p&gt;(.+?)&lt;/p&gt;</title>', r'<title>\1</title>', html)
            html = re.sub(r'content="<p>(.+?)</p>"', r'content="\1"', html)
            
            output_file = "REAL_article_v3.2_FINAL.html"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"✅ Saved to: {output_file}")
            print()
            print("Opening in browser...")
            
            import subprocess
            subprocess.run(["open", output_file])
            print("🎉 DONE!")
        else:
            print("⚠️  No HTML generated")
            print(f"Result attributes: {dir(result)}")
    else:
        print(f"❌ Error: {result.error or 'Unknown error'}")
        print(f"Details: {result.details or 'N/A'}")

if __name__ == "__main__":
    asyncio.run(main())

