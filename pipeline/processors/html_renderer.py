"""
HTML Renderer - Converts validated article to production HTML.

Simple, clean rendering with:
- Semantic HTML5 structure
- Responsive meta tags
- Open Graph metadata
- Schema.org structured data
- Optimized for SEO and accessibility
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..utils.schema_markup import generate_all_schemas, render_schemas_as_json_ld
from ..models.output_schema import ArticleOutput

logger = logging.getLogger(__name__)


class HTMLRenderer:
    """Render validated article data to production HTML."""

    @staticmethod
    def render(
        article: Dict[str, Any],
        company_data: Optional[Dict[str, Any]] = None,
        article_output: Optional[ArticleOutput] = None,
        article_url: Optional[str] = None,
        faq_items: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Render article to production HTML.

        Args:
            article: Validated article dictionary
            company_data: Company metadata (for copyright, logo, etc)

        Returns:
            Complete HTML document string
        """
        if not article:
            return ""

        # Extract key fields
        headline = article.get("Headline", "Untitled")
        subtitle = article.get("Subtitle", "")
        intro = article.get("Intro", "")
        content = HTMLRenderer._build_content(article)
        meta_desc = article.get("Meta_Description", "")
        meta_title = article.get("Meta_Title", headline)
        image_url = article.get("image_url", "")
        image_alt = article.get("image_alt_text", "")
        sources = article.get("Sources", "")
        toc = article.get("toc", {})
        # Use passed faq_items if provided, otherwise extract from article
        if faq_items is None:
            faq_items = article.get("faq_items", [])
        paa_items = article.get("paa_items", [])
        internal_links = article.get("internal_links_html", "")
        read_time = article.get("read_time", 5)
        publication_date = article.get("publication_date", datetime.now().isoformat())

        company_name = company_data.get("company_name", "") if company_data else ""
        company_url = company_data.get("company_url", "") if company_data else ""

        # Generate JSON-LD schemas with error handling
        schemas_html = ""
        if article_output:
            try:
                base_url = company_url.rsplit('/', 1)[0] if company_url else None
                schemas = generate_all_schemas(
                    output=article_output,
                    company_data=company_data,
                    article_url=article_url,
                    base_url=base_url,
                    faq_items=faq_items,
                )
                schemas_html = render_schemas_as_json_ld(schemas)
            except Exception as e:
                logger.warning(f"Schema generation failed: {e}. Continuing without schemas.")
                schemas_html = ""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{HTMLRenderer._escape_attr(meta_desc)}">
    <title>{HTMLRenderer._escape_html(meta_title)}</title>

    {HTMLRenderer._og_tags(headline, meta_desc, image_url, company_url)}
    
    {schemas_html}

    <style>
        :root {{
            --primary: #0066cc;
            --text: #1a1a1a;
            --text-light: #666;
            --bg-light: #f9f9f9;
            --border: #e0e0e0;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: var(--text);
            line-height: 1.6;
            background: white;
        }}

        .container {{ max-width: 900px; margin: 0 auto; padding: 0 20px; }}

        header {{ padding: 40px 0; border-bottom: 1px solid var(--border); margin-bottom: 40px; }}
        header h1 {{ font-size: 2.5em; margin-bottom: 10px; line-height: 1.2; }}
        header .meta {{ color: var(--text-light); font-size: 0.95em; }}

        .featured-image {{ width: 100%; max-height: 400px; object-fit: cover; margin: 30px 0; border-radius: 8px; }}

        .intro {{ font-size: 1.1em; color: var(--text-light); margin: 30px 0; font-style: italic; }}

        .toc {{ background: var(--bg-light); padding: 20px; border-radius: 8px; margin: 30px 0; }}
        .toc h2 {{ font-size: 1.2em; margin-bottom: 15px; }}
        .toc ul {{ list-style: none; }}
        .toc li {{ margin: 8px 0; }}
        .toc a {{ color: var(--primary); text-decoration: none; }}
        .toc a:hover {{ text-decoration: underline; }}

        article {{ margin: 40px 0; }}
        article h2 {{ font-size: 1.8em; margin: 40px 0 20px; }}
        article h3 {{ font-size: 1.3em; margin: 30px 0 15px; }}
        article p {{ margin: 15px 0; }}
        article ul, article ol {{ margin: 15px 0 15px 30px; }}
        article li {{ margin: 8px 0; }}
        article a {{ color: var(--primary); text-decoration: none; }}
        article a:hover {{ text-decoration: underline; }}

        .faq, .paa {{ margin: 40px 0; }}
        .faq h2, .paa h2 {{ font-size: 1.5em; margin-bottom: 20px; }}
        .faq-item, .paa-item {{ margin: 20px 0; padding: 15px; background: var(--bg-light); border-radius: 6px; }}
        .faq-item h3, .paa-item h3 {{ margin-bottom: 10px; font-size: 1.1em; }}

        .more-links {{ margin: 40px 0; padding: 20px; background: var(--bg-light); border-radius: 8px; }}
        .more-links h2 {{ font-size: 1.3em; margin-bottom: 15px; }}
        .more-links ul {{ list-style: none; margin: 0; }}
        .more-links li {{ margin: 10px 0; }}
        .more-links a {{ color: var(--primary); text-decoration: none; }}

        footer {{ border-top: 1px solid var(--border); margin-top: 60px; padding: 40px 0; color: var(--text-light); font-size: 0.9em; }}
        footer a {{ color: var(--primary); }}

        .citations {{ margin: 40px 0; padding: 20px; background: var(--bg-light); border-left: 4px solid var(--primary); }}
        .citations h2 {{ font-size: 1.2em; margin-bottom: 15px; }}
        .citations ol {{ margin: 0 0 0 20px; }}
        .citations li {{ margin: 10px 0; }}
    </style>
</head>
<body>
    <header class="container">
        <h1>{HTMLRenderer._escape_html(headline)}</h1>
        {f'<h2 class="subtitle">{HTMLRenderer._escape_html(subtitle)}</h2>' if subtitle else ''}
        <div class="meta">
            <span>Published: {publication_date.split('T')[0]}</span>
            <span> • </span>
            <span>Read time: {read_time} min</span>
            {f' • <span><a href="{HTMLRenderer._escape_attr(company_url)}">{HTMLRenderer._escape_html(company_name)}</a></span>' if company_url else ''}
        </div>
    </header>

    <main class="container">
        {f'<img src="{HTMLRenderer._escape_attr(image_url)}" alt="{HTMLRenderer._escape_attr(image_alt)}" class="featured-image">' if image_url else ''}

        {f'<p class="intro">{HTMLRenderer._escape_html(intro)}</p>' if intro else ''}

        {HTMLRenderer._render_toc(toc)}

        <article>
            {content}
        </article>

        {HTMLRenderer._render_paa(paa_items)}
        {HTMLRenderer._render_faq(faq_items)}
        {internal_links}
        {HTMLRenderer._render_citations(sources)}
    </main>

    <footer class="container">
        <p>© {datetime.now().year} {HTMLRenderer._escape_html(company_name)}. All rights reserved.</p>
        {f'<p><a href="{HTMLRenderer._escape_attr(company_url)}">Visit {HTMLRenderer._escape_html(company_name)}</a></p>' if company_url else ''}
    </footer>
</body>
</html>"""
        return html

    @staticmethod
    def _build_content(article: Dict[str, Any]) -> str:
        """Build article content from sections."""
        parts = []

        for i in range(1, 10):
            title_key = f"section_{i:02d}_title"
            content_key = f"section_{i:02d}_content"

            title = article.get(title_key, "")
            content = article.get(content_key, "")

            if title and title.strip():
                parts.append(f"<h2>{HTMLRenderer._escape_html(title)}</h2>")

            if content and content.strip():
                parts.append(content)

        return "\n".join(parts) if parts else "<p>No content available.</p>"

    @staticmethod
    def _render_toc(toc: Dict[str, Any]) -> str:
        """Render table of contents."""
        if not toc:
            return ""

        items = [f'<li><a href="#{k}">{HTMLRenderer._escape_html(v)}</a></li>' for k, v in toc.items() if v]

        if not items:
            return ""

        return f"""<div class="toc">
            <h2>Table of Contents</h2>
            <ul>
                {''.join(items)}
            </ul>
        </div>"""

    @staticmethod
    def _render_faq(faq_items: list) -> str:
        """Render FAQ section."""
        if not faq_items:
            return ""

        items_html = []
        for item in faq_items:
            q = item.get("question", "")
            a = item.get("answer", "")
            if q and a:
                items_html.append(
                    f'<div class="faq-item"><h3>{HTMLRenderer._escape_html(q)}</h3><p>{a}</p></div>'
                )

        if not items_html:
            return ""

        return f"""<section class="faq">
            <h2>Frequently Asked Questions</h2>
            {''.join(items_html)}
        </section>"""

    @staticmethod
    def _render_paa(paa_items: list) -> str:
        """Render People Also Ask section."""
        if not paa_items:
            return ""

        items_html = []
        for item in paa_items:
            q = item.get("question", "")
            a = item.get("answer", "")
            if q and a:
                items_html.append(
                    f'<div class="paa-item"><h3>{HTMLRenderer._escape_html(q)}</h3><p>{a}</p></div>'
                )

        if not items_html:
            return ""

        return f"""<section class="paa">
            <h2>People Also Ask</h2>
            {''.join(items_html)}
        </section>"""

    @staticmethod
    def _render_citations(sources: str) -> str:
        """Render citations section."""
        if not sources or not sources.strip():
            return ""

        lines = [line.strip() for line in sources.split("\n") if line.strip()]
        if not lines:
            return ""

        items_html = [f"<li>{HTMLRenderer._escape_html(line)}</li>" for line in lines]

        return f"""<section class="citations">
            <h2>Sources</h2>
            <ol>
                {''.join(items_html)}
            </ol>
        </section>"""

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

    @staticmethod
    def _escape_attr(text: str) -> str:
        """Escape HTML attribute values."""
        if not text:
            return ""
        return str(text).replace('"', "&quot;").replace("'", "&#x27;")

    @staticmethod
    def _og_tags(title: str, desc: str, image: str, url: str) -> str:
        """Generate OpenGraph meta tags."""
        tags = [
            f'<meta property="og:title" content="{HTMLRenderer._escape_attr(title)}">',
            f'<meta property="og:description" content="{HTMLRenderer._escape_attr(desc)}">',
        ]

        if image:
            tags.append(f'<meta property="og:image" content="{HTMLRenderer._escape_attr(image)}">')

        if url:
            tags.append(f'<meta property="og:url" content="{HTMLRenderer._escape_attr(url)}">')

        tags.append('<meta property="og:type" content="article">')

        return "\n    ".join(tags)
