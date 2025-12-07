#!/usr/bin/env python3
"""
Run a local batch of 10 blogs using the pipeline with Gemini JSON schema.
Generates HTML files batch_01.html ... batch_10.html in the current folder.
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

from service.api import write_blog, BlogGenerationRequest, ExistingBlogSlug


def ensure_env():
    env_file = Path(__file__).parent / ".env.local"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded {env_file}")
    # Map GOOGLE_GEMINI_API_KEY -> GEMINI_API_KEY if needed
    if "GOOGLE_GEMINI_API_KEY" in os.environ and "GEMINI_API_KEY" not in os.environ:
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_GEMINI_API_KEY"]
        print("✅ Mapped GOOGLE_GEMINI_API_KEY → GEMINI_API_KEY")


async def main():
    ensure_env()

    topics = [
        "AI code generation tools 2025",
        "LLM agents for software delivery",
        "Secure AI coding workflows",
        "Testing AI-generated code",
        "AI refactoring large codebases",
        "AI in DevOps pipelines",
        "Agentic IDEs and context windows",
        "Governance for AI coding",
        "Measuring AI developer productivity",
        "Future of AI-assisted engineering",
    ]

    # Precompute batch sibling metadata for cross-linking
    batch_siblings = []
    for t in topics:
        slug = f"/blog/{t.lower().replace(' ', '-').replace(',', '').replace('?', '').replace('\"', '')}"
        batch_siblings.append(
            ExistingBlogSlug(
                slug=slug,
                title=t.title(),
                keyword=t,
            )
        )

    # Run sequentially for clarity/logging
    for idx, topic in enumerate(topics, start=1):
        print("=" * 80)
        print(f"🚀 Generating blog {idx}/10: {topic}")
        print("=" * 80)

        request = BlogGenerationRequest(
            primary_keyword=topic,
            company_url="https://devtech.example.com",
            language="en",
            country="US",
            batch_siblings=batch_siblings,
        )

        result = await write_blog(request)

        if not result.success:
            print(f"❌ Failed: {result.error}")
            continue

        html = result.html_content or result.html or ""
        if not html:
            print("⚠️ No HTML content returned")
            continue

        out_file = Path(f"batch_{idx:02d}.html")
        out_file.write_text(html, encoding="utf-8")
        print(f"✅ Saved {out_file} ({len(html)} chars)")


if __name__ == "__main__":
    asyncio.run(main())

