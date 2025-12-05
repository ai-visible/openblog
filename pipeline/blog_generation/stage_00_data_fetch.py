"""
Stage 0: Data Fetch & Auto-Detection

Maps to v4.1 Phase 1, Steps 1-3:
- Step 1: Schedule trigger (entry point)
- Step 2: get_supabase_information (or direct input)
- Step 3: set_field_names (normalize and validate)

New feature: Auto-detection of company information from company_url
- Scrape website for metadata
- Use Gemini to analyze business info
- Fetch sitemap for internal links pool

Input:
  - job_id: Unique identifier
  - primary_keyword: Blog topic/keyword
  - company_url: Company website (for auto-detection)
  - Optional: company_name, company_location, company_language (overrides)

Output:
  - ExecutionContext with populated:
    - job_config (primary_keyword, content_generation_instruction, etc)
    - company_data (auto-detected or overridden)
    - language
    - blog_page (internal links, keyword, etc)
"""

import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import re

from ..core import ExecutionContext, Stage

logger = logging.getLogger(__name__)


class DataFetchStage(Stage):
    """
    Stage 0: Fetch and auto-detect job data.

    Handles:
    - Validating required input fields
    - Auto-detecting company information from website
    - Applying user overrides
    - Normalizing field names
    - Building ExecutionContext
    """

    stage_num = 0
    stage_name = "Data Fetch & Auto-Detection"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 0: Data fetch and auto-detection.

        Args:
            context: ExecutionContext with job_id and job_config

        Returns:
            Updated ExecutionContext with company_data, language, blog_page

        Raises:
            ValueError: If required fields missing
            Exception: If auto-detection fails
        """
        logger.info(f"Stage 0: {self.stage_name}")
        logger.info(f"Job ID: {context.job_id}")

        # Step 1: Validate required input
        self._validate_input(context)
        logger.info("✅ Input validation passed")

        # Step 2: Auto-detect company information
        company_data = await self._auto_detect_company(
            context.job_config.get("company_url", "")
        )
        logger.info("✅ Company information auto-detected")

        # Step 3: Apply overrides
        company_data = self._apply_overrides(company_data, context.job_config)
        logger.info("✅ User overrides applied")

        # Step 4: Build normalized context
        context.company_data = company_data
        # Language priority: job_config.language > company_data.company_language > "en"
        context.language = context.job_config.get("language") or company_data.get("company_language", "en")
        context.blog_page = self._build_blog_page(context.job_config, company_data)
        context.job_config = self._normalize_job_config(context.job_config)

        logger.info(f"✅ ExecutionContext built")
        logger.info(f"   Company: {company_data.get('company_name', 'Unknown')}")
        logger.info(f"   Language: {context.language}")
        logger.info(f"   Keyword: {context.job_config.get('primary_keyword', 'Unknown')}")

        return context

    def _validate_input(self, context: ExecutionContext) -> None:
        """
        Validate required input fields.

        Args:
            context: ExecutionContext to validate

        Raises:
            ValueError: If required fields missing
        """
        required_fields = {
            "primary_keyword": "Blog topic/keyword",
            "company_url": "Company website URL",
        }

        job_config = context.job_config
        missing = []

        for field, description in required_fields.items():
            if not job_config.get(field):
                missing.append(f"{field} ({description})")

        if missing:
            raise ValueError(
                f"Missing required fields:\n  - " + "\n  - ".join(missing)
            )

        logger.debug(f"Required fields present: {', '.join(required_fields.keys())}")

    async def _auto_detect_company(self, company_url: str) -> Dict[str, Any]:
        """
        Auto-detect company information from URL.

        Operations:
        1. Extract domain and company name from URL
        2. Scrape website for metadata (language, location)
        3. Use Gemini to analyze company (industry, business model)
        4. Fetch sitemap for internal links pool

        Args:
            company_url: Company website URL

        Returns:
            Dictionary with auto-detected company information:
            - company_name: Detected or extracted from domain
            - company_url: Validated URL
            - company_location: Detected from metadata/Gemini
            - company_language: Detected language
            - company_info: Business info from Gemini analysis
            - company_competitors: Empty (will be filled later)
            - links: Internal links from sitemap

        Note:
            For MVP, return basic info. Full Gemini analysis optional.
        """
        logger.debug(f"Auto-detecting company info from: {company_url}")

        # Extract domain and basic info
        domain = self._extract_domain(company_url)
        company_name = self._extract_company_name(domain)

        logger.debug(f"Domain: {domain}")
        logger.debug(f"Company name: {company_name}")

        # Build initial company_data
        company_data = {
            "company_url": company_url,
            "company_name": company_name,
            "company_language": "en",  # Default to English, can be overridden
            "company_location": "Unknown",  # Can be overridden
            "company_info": {
                "description": f"Information about {company_name}",
                "industry": "Unknown",  # Can be filled by Gemini
                "business_model": "Unknown",
            },
            "company_competitors": [],  # Empty for now
        }

        # TODO: Add Gemini analysis for company info
        # TODO: Add website scraping for metadata
        # TODO: Add sitemap fetching for internal links

        logger.debug(f"Auto-detected company data: {company_data}")
        return company_data

    def _extract_domain(self, url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url: Full URL (e.g., https://www.example.com)

        Returns:
            Domain (e.g., example.com)

        Raises:
            ValueError: If URL is invalid
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            if not domain:
                raise ValueError(f"Invalid URL: {url}")
            return domain
        except Exception as e:
            raise ValueError(f"Could not parse URL '{url}': {e}")

    def _extract_company_name(self, domain: str) -> str:
        """
        Extract company name from domain.

        Examples:
        - "acme.com" → "ACME"
        - "my-company.co.uk" → "My Company"
        - "example.org" → "Example"

        Args:
            domain: Domain name (e.g., "example.com")

        Returns:
            Company name (title case)
        """
        # Remove TLD
        name = domain.split(".")[0]

        # Replace hyphens with spaces
        name = name.replace("-", " ")

        # Title case
        name = " ".join(word.capitalize() for word in name.split())

        return name

    def _apply_overrides(
        self, company_data: Dict[str, Any], job_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply user overrides to auto-detected company data.

        User can override:
        - company_name
        - company_location
        - company_language
        - company_competitors
        - content_generation_instruction
        - author_name, author_bio, author_url (for E-E-A-T scoring)

        Args:
            company_data: Auto-detected company data
            job_config: User-provided job configuration

        Returns:
            Updated company_data with overrides applied
        """
        override_fields = [
            "company_name",
            "company_location",
            "company_language",
            "company_competitors",
            "content_generation_instruction",
            # Author fields for E-E-A-T scoring
            "author_name",
            "author_bio",
            "author_url",
        ]

        for field in override_fields:
            if field in job_config and job_config[field]:
                company_data[field] = job_config[field]
                logger.debug(f"Override {field}: {job_config[field]}")
        
        # Also check for author fields inside job_config["company_data"] (from API request)
        if "company_data" in job_config and isinstance(job_config["company_data"], dict):
            nested_company_data = job_config["company_data"]
            author_fields = ["author_name", "author_bio", "author_url"]
            for field in author_fields:
                if field in nested_company_data and nested_company_data[field]:
                    company_data[field] = nested_company_data[field]
                    logger.debug(f"Override {field} from company_data: {nested_company_data[field]}")

        return company_data

    def _build_blog_page(
        self, job_config: Dict[str, Any], company_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build blog_page configuration.

        Contains blog-specific settings for this article:
        - primary_keyword
        - internal links (from sitemap or provided)
        - output settings

        Args:
            job_config: User job configuration
            company_data: Company information

        Returns:
            blog_page dictionary
        """
        # Build internal links from sitemap_urls + batch_siblings
        provided_links = job_config.get("links", "")
        sitemap_urls = list(job_config.get("sitemap_urls", []))  # Copy to avoid mutation
        batch_siblings = job_config.get("batch_siblings", [])
        
        # Merge batch siblings into URL pool for LLM prompt
        if batch_siblings:
            logger.info(f"Adding {len(batch_siblings)} batch siblings to link pool for prompt")
            for sibling in batch_siblings:
                sibling_url = sibling.get("slug", "")
                if sibling_url and sibling_url not in sitemap_urls:
                    sitemap_urls.append(sibling_url)
        
        if not provided_links and sitemap_urls:
            # Convert sitemap_urls to formatted link string for prompt
            link_lines = []
            for i, url in enumerate(sitemap_urls[:10], 1):
                # Extract readable title from URL
                parts = url.strip("/").split("/")
                title = parts[-1].replace("-", " ").title() if parts else "Related"
                link_lines.append(f"[{i}] {url} - {title}")
            provided_links = "\n".join(link_lines)
            logger.info(f"Built {len(link_lines)} links from sitemap_urls + batch_siblings")
        
        blog_page = {
            "primary_keyword": job_config.get("primary_keyword", ""),
            "links": provided_links,
            "image_url": job_config.get("image_url"),  # Optional: pre-generated image
        }

        return blog_page

    def _normalize_job_config(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize and validate job configuration fields.

        Maps v4.1 field names to Python names if needed.

        Args:
            job_config: Original job configuration

        Returns:
            Normalized job configuration
        """
        normalized = job_config.copy()

        # Ensure primary_keyword is set
        if "primary_keyword" not in normalized:
            normalized["primary_keyword"] = ""

        # Set default content generation instruction if not provided
        if "content_generation_instruction" not in normalized:
            normalized["content_generation_instruction"] = (
                "Write a comprehensive, SEO-optimized blog post. "
                "Follow all content rules strictly. "
                "Ensure paragraph length ≤ 25 words. "
                "Include 8+ sources, 1+ internal link per H2 section. "
                "Generate 5 FAQ items and 3 PAA items minimum."
            )

        return normalized
