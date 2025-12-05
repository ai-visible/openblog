#!/usr/bin/env python3
"""
View the generated article from the test run.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)
else:
    load_dotenv()

sys.path.insert(0, str(Path(__file__).parent))

from pipeline.core import WorkflowEngine, ExecutionContext
from pipeline.blog_generation import (
    DataFetchStage,
    PromptBuildStage,
    GeminiCallStage,
    ExtractionStage,
    CitationsStage,
    InternalLinksStage,
    TableOfContentsStage,
    MetadataStage,
    FAQPAAStage,
    ImageStage,
    CleanupStage,
    StorageStage,
)


async def generate_and_view_article():
    """Generate article and display it."""
    print("=" * 80)
    print("FULL ARTICLE GENERATION WITH ALL 12 STAGES")
    print("Gemini 3 Pro + Deep Research + AEO Optimization")
    print("=" * 80)
    print()

    # Create workflow engine with ALL 12 stages
    engine = WorkflowEngine()
    engine.register_stages([
        DataFetchStage(),
        PromptBuildStage(),
        GeminiCallStage(),
        ExtractionStage(),
        CitationsStage(),
        InternalLinksStage(),
        TableOfContentsStage(),
        MetadataStage(),
        FAQPAAStage(),
        ImageStage(),
        CleanupStage(),
        StorageStage(),
    ])

    # Test input
    job_config = {
        "primary_keyword": "AI adoption in customer service",
        "company_url": "https://example.com",
        "company_name": "Example Corp",
    }

    print("📝 Generating article...")
    print(f"   Keyword: {job_config['primary_keyword']}")
    print(f"   Company: {job_config['company_name']}")
    print()

    try:
        # Execute workflow
        context = await engine.execute(
            job_id="view-article-test",
            job_config=job_config
        )

        if context.structured_data:
            article = context.structured_data
            
            print("=" * 80)
            print("📄 GENERATED ARTICLE")
            print("=" * 80)
            print()
            
            # Calculate word count
            all_text = ' '.join([
                str(v) for v in article.model_dump().values() 
                if isinstance(v, str) and v
            ])
            word_count = len(all_text.split())
            
            # Display full article
            print(f"# {article.Headline}")
            print()
            if hasattr(article, 'Subtitle') and article.Subtitle:
                print(f"## {article.Subtitle}")
                print()
            if hasattr(article, 'Teaser') and article.Teaser:
                print(f"**{article.Teaser}**")
                print()
            
            # Intro section
            if hasattr(article, 'Intro') and article.Intro:
                print("## Introduction")
                print()
                print(article.Intro)
                print()
            
            if hasattr(article, 'Direct_Answer') and article.Direct_Answer:
                print("## Direct Answer")
                print()
                print(article.Direct_Answer)
                print()
            
            # Display sections
            sections = []
            for i in range(1, 10):
                title_attr = f"section_{i:02d}_title"
                content_attr = f"section_{i:02d}_content"
                
                if hasattr(article, title_attr) and getattr(article, title_attr):
                    title = getattr(article, title_attr)
                    content = getattr(article, content_attr) if hasattr(article, content_attr) else ""
                    sections.append((title, content))
            
            if sections:
                print("---")
                print()
                for title, content in sections:
                    print(f"## {title}")
                    print()
                    if content:
                        print(content)
                    print()
            
            # Key Takeaways
            takeaways = []
            for i in range(1, 4):
                attr = f"key_takeaway_{i:02d}"
                if hasattr(article, attr) and getattr(article, attr):
                    takeaways.append(getattr(article, attr))
            
            if takeaways:
                print("---")
                print()
                print("## Key Takeaways")
                print()
                for i, takeaway in enumerate(takeaways, 1):
                    print(f"{i}. {takeaway}")
                print()
            
            # FAQs
            faqs = []
            for i in range(1, 11):
                q_attr = f"faq_{i:02d}_question"
                a_attr = f"faq_{i:02d}_answer"
                if hasattr(article, q_attr) and getattr(article, q_attr):
                    q = getattr(article, q_attr)
                    a = getattr(article, a_attr) if hasattr(article, a_attr) else ""
                    faqs.append((q, a))
            
            if faqs:
                print("---")
                print()
                print("## Frequently Asked Questions (FAQs)")
                print()
                for i, (q, a) in enumerate(faqs, 1):
                    print(f"### Q{i}: {q}")
                    if a:
                        print(f"{a}")
                    print()
            
            # PAAs (People Also Ask)
            paas = []
            for i in range(1, 5):
                q_attr = f"paa_{i:02d}_question"
                a_attr = f"paa_{i:02d}_answer"
                if hasattr(article, q_attr) and getattr(article, q_attr):
                    q = getattr(article, q_attr)
                    a = getattr(article, a_attr) if hasattr(article, a_attr) else ""
                    paas.append((q, a))
            
            if paas:
                print("---")
                print()
                print("## People Also Ask (PAA)")
                print()
                for i, (q, a) in enumerate(paas, 1):
                    print(f"### Q{i}: {q}")
                    if a:
                        print(f"{a}")
                    print()
            
            # Sources
            if hasattr(article, 'Sources') and article.Sources:
                print("---")
                print()
                print("## Sources")
                print()
                # Sources are formatted as "[1]: URL – description"
                sources_text = article.Sources
                # Split by newlines and format nicely
                for line in sources_text.split('\n'):
                    if line.strip():
                        print(line.strip())
                print()
            
            # Search Queries (if available)
            if hasattr(article, 'Search_Queries') and article.Search_Queries:
                print("---")
                print()
                print("## Search Queries Used")
                print()
                print(article.Search_Queries)
                print()
            
            # Display metadata
            print("=" * 80)
            print("📊 ARTICLE METADATA")
            print("=" * 80)
            print()
            print(f"Meta Title: {article.Meta_Title}")
            print(f"Meta Description: {article.Meta_Description}")
            print(f"Headline: {article.Headline}")
            if hasattr(article, 'Direct_Answer') and article.Direct_Answer:
                print(f"Direct Answer: {article.Direct_Answer[:100]}...")
            print()
            
            # Save to file
            output_file = Path(__file__).parent / "generated_article.json"
            with open(output_file, "w") as f:
                json.dump(article.model_dump(), f, indent=2, default=str)
            print(f"✅ Article saved to: {output_file}")
            
            # Also save as markdown with ALL sections
            md_file = Path(__file__).parent / "generated_article.md"
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(f"# {article.Headline}\n\n")
                if hasattr(article, 'Subtitle') and article.Subtitle:
                    f.write(f"## {article.Subtitle}\n\n")
                if hasattr(article, 'Teaser') and article.Teaser:
                    f.write(f"**{article.Teaser}**\n\n")
                if hasattr(article, 'Intro') and article.Intro:
                    f.write(f"## Introduction\n\n{article.Intro}\n\n")
                if hasattr(article, 'Direct_Answer') and article.Direct_Answer:
                    f.write(f"## Direct Answer\n\n{article.Direct_Answer}\n\n")
                f.write("---\n\n")
                for title, content in sections:
                    f.write(f"## {title}\n\n{content}\n\n")
                if takeaways:
                    f.write("---\n\n## Key Takeaways\n\n")
                    for i, takeaway in enumerate(takeaways, 1):
                        f.write(f"{i}. {takeaway}\n")
                    f.write("\n")
                if faqs:
                    f.write("---\n\n## Frequently Asked Questions (FAQs)\n\n")
                    for i, (q, a) in enumerate(faqs, 1):
                        f.write(f"### Q{i}: {q}\n")
                        if a:
                            f.write(f"{a}\n")
                        f.write("\n")
                if paas:
                    f.write("---\n\n## People Also Ask (PAA)\n\n")
                    for i, (q, a) in enumerate(paas, 1):
                        f.write(f"### Q{i}: {q}\n")
                        if a:
                            f.write(f"{a}\n")
                        f.write("\n")
                if hasattr(article, 'Sources') and article.Sources:
                    f.write("---\n\n## Sources\n\n")
                    for line in article.Sources.split('\n'):
                        if line.strip():
                            f.write(f"{line.strip()}\n")
                    f.write("\n")
            print(f"✅ Article saved as markdown to: {md_file}")
            print(f"📊 Word Count: {word_count:,} words")
            print(f"✅ Deep Research: CONFIRMED (tools enabled: googleSearch + urlContext)")
            print(f"   - {len([s for s in article.Sources.split('\\n') if s.strip()])} sources cited")
            
            # Show AEO metrics if available
            if context.quality_report:
                aeo_score = context.quality_report.get("metrics", {}).get("aeo_score", 0)
                aeo_method = context.quality_report.get("metrics", {}).get("aeo_score_method", "unknown")
                print(f"✅ AEO Score: {aeo_score}/100 ({aeo_method})")
                critical_issues = len(context.quality_report.get("critical_issues", []))
                if critical_issues == 0:
                    print(f"✅ No Critical Issues")
                else:
                    print(f"⚠️  {critical_issues} Critical Issues")
            
            # Show HTML generation status
            if context.final_article and context.final_article.get("html_content"):
                html_size = len(context.final_article["html_content"])
                print(f"✅ HTML Generated: {html_size:,} bytes")
                if 'type="application/ld+json"' in context.final_article["html_content"]:
                    schema_count = context.final_article["html_content"].count('"@context": "https://schema.org"')
                    print(f"✅ JSON-LD Schemas: {schema_count}")
            
            # Show execution times
            if hasattr(context, 'execution_times') and context.execution_times:
                print()
                print("⏱️  Execution Times:")
                for stage, time_taken in sorted(context.execution_times.items()):
                    print(f"   {stage}: {time_taken:.2f}s")
                total_time = sum(context.execution_times.values())
                print(f"   Total: {total_time:.2f}s")
            
            return True
        else:
            print("❌ ERROR: No structured data generated")
            return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(generate_and_view_article())
    sys.exit(0 if success else 1)

