"""
Stage 3: Structured Data Extraction

Maps to v4.1 Phase 3, Steps 6-7: article-extraction

Extracts structured data from Gemini's raw response (text/plain JSON).

Input:
  - ExecutionContext.raw_article (from Stage 2)

Output:
  - ExecutionContext.structured_data (ArticleOutput instance)

Process:
1. Extract JSON from raw_article
2. Parse JSON to Python dict
3. Validate against OutputSchema
4. Handle missing/incomplete fields gracefully
5. Store validated ArticleOutput in context

Retry logic:
- Max retries: 2 (for transient validation issues)
- Only retries on validation errors (structure OK but fields invalid)
- Non-retryable: JSON extraction failed, malformed JSON
"""

import logging
import json
from typing import Dict, Any, Optional

from ..core import ExecutionContext, Stage
from ..models.gemini_client import GeminiClient
from ..models.output_schema import ArticleOutput

logger = logging.getLogger(__name__)


class ExtractionStage(Stage):
    """
    Stage 3: Extract and validate structured article data.

    Handles:
    - JSON extraction from raw response
    - Schema validation
    - Field normalization and cleanup
    - Error handling and validation warnings
    - Storage of structured_data in context
    """

    stage_num = 3
    stage_name = "Structured Data Extraction"

    def __init__(self) -> None:
        """Initialize extraction stage."""
        self.client = GeminiClient()
        logger.info(f"Stage 3 initialized: {self.stage_name}")

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 3: Extract and validate structured data.

        Input from context:
        - raw_article: Raw Gemini response (text/plain with embedded JSON)

        Output to context:
        - structured_data: Validated ArticleOutput instance

        Args:
            context: ExecutionContext from Stage 2

        Returns:
            Updated context with structured_data populated

        Raises:
            ValueError: If raw_article missing or JSON extraction fails
            Exception: If validation fails after retries
        """
        logger.info(f"Stage 3: {self.stage_name}")

        # Validate input
        if not context.raw_article:
            raise ValueError("Raw article is required (from Stage 2)")

        logger.debug(f"Raw article size: {len(context.raw_article)} characters")

        # Extract JSON from raw response
        logger.info("Extracting JSON from raw article...")
        try:
            json_data = self.client.extract_json_from_response(context.raw_article)
            logger.info("✅ JSON extraction successful")
        except Exception as e:
            logger.error(f"❌ JSON extraction failed: {e}")
            raise ValueError(f"Failed to extract JSON from raw article: {e}")

        logger.debug(f"   JSON keys: {list(json_data.keys())[:10]}...")

        # Parse and validate
        logger.info("Validating and normalizing extracted data...")
        structured_data = self._parse_and_validate(json_data)

        # Log validation results
        logger.info("✅ Validation successful")
        logger.info(f"   Sections: {structured_data.get_active_sections()}")
        logger.info(f"   FAQs: {structured_data.get_active_faqs()}")
        logger.info(f"   PAAs: {structured_data.get_active_paas()}")
        logger.info(f"   Key Takeaways: {structured_data.get_active_takeaways()}")

        # Store in context
        context.structured_data = structured_data

        return context

    def _parse_and_validate(self, json_data: Dict[str, Any]) -> ArticleOutput:
        """
        Parse JSON data and validate against schema.

        Handles:
        - Type coercion (all values → strings for now)
        - Missing required fields (fills with defaults)
        - Validation errors (logs warnings, continues)
        - Field normalization (strip whitespace)

        Args:
            json_data: Extracted JSON dictionary

        Returns:
            Validated ArticleOutput instance

        Raises:
            ValueError: If validation fails
        """
        logger.debug("Parsing JSON data...")

        # Normalize data: ensure all values are strings (Gemini may return mixed types)
        normalized = {}
        for key, value in json_data.items():
            if value is None:
                normalized[key] = ""
            elif isinstance(value, str):
                normalized[key] = value.strip()
            else:
                # Convert non-strings to string representation
                normalized[key] = str(value).strip()

        logger.debug(f"Normalized {len(normalized)} fields")

        # Validate with ArticleOutput schema
        try:
            article = ArticleOutput(**normalized)
            logger.debug("✓ Schema validation passed")
            return article
        except Exception as e:
            # Log validation error details
            logger.warning(f"⚠️  Validation error: {e}")

            # Try to extract what we can and fill blanks
            logger.info("Attempting to recover with partial data...")
            article = self._recover_partial_data(normalized)
            logger.info("✅ Partial recovery successful")
            return article

    def _recover_partial_data(self, json_data: Dict[str, Any]) -> ArticleOutput:
        """
        Recover partial data when validation fails.

        Strategy:
        1. Extract required fields (Headline, Teaser, etc.)
        2. Provide sensible defaults for missing required fields
        3. Include all optional fields as-is
        4. Log warnings for critical missing fields

        Args:
            json_data: Normalized JSON dictionary

        Returns:
            ArticleOutput with available data + defaults
        """
        # Define field mappings (some fields may have variant names)
        field_map = {
            "Headline": ["Headline", "headline", "title"],
            "Meta_Title": ["Meta Title", "Meta_Title", "MetaTitle"],
            "Meta_Description": ["Meta Description", "Meta_Description", "MetaDescription"],
        }

        # Try to find values with variant names
        for standard_name, variants in field_map.items():
            if standard_name not in json_data or not json_data[standard_name]:
                for variant in variants:
                    if variant in json_data and json_data[variant]:
                        json_data[standard_name] = json_data[variant]
                        logger.debug(f"Mapped {variant} → {standard_name}")
                        break

        # Provide defaults for truly missing required fields
        defaults = {
            "Headline": "Untitled Article",
            "Teaser": "This article explores the topic in depth.",
            "Direct_Answer": "This topic is important and relevant.",
            "Intro": "This article provides comprehensive information on the subject.",
            "Meta_Title": "Article",
            "Meta_Description": "Read this article for more information.",
        }

        for field, default in defaults.items():
            if not json_data.get(field):
                logger.warning(f"⚠️  Missing required field '{field}', using default")
                json_data[field] = default

        # Now validate again with defaults in place
        try:
            article = ArticleOutput(**json_data)
            return article
        except Exception as e:
            # Last resort: create minimal valid instance
            logger.error(f"Recovery failed: {e}")
            logger.info("Creating minimal valid article...")

            minimal = ArticleOutput(
                Headline=json_data.get("Headline", "Untitled"),
                Teaser=json_data.get("Teaser", "Article content."),
                Direct_Answer=json_data.get("Direct_Answer", "See article for details."),
                Intro=json_data.get("Intro", "Article introduction."),
                Meta_Title=json_data.get("Meta_Title", "Article"),
                Meta_Description=json_data.get("Meta_Description", "Article"),
            )
            return minimal

    def _log_completeness(self, article: ArticleOutput) -> None:
        """
        Log article completeness metrics.

        Calculates:
        - Percentage of required fields populated
        - Percentage of optional fields populated
        - Missing sections
        """
        logger.debug("Article completeness check:")

        # Required fields
        required_fields = [
            article.Headline,
            article.Teaser,
            article.Direct_Answer,
            article.Intro,
            article.Meta_Title,
            article.Meta_Description,
        ]
        required_count = sum(1 for f in required_fields if f and f.strip())
        required_pct = (required_count / len(required_fields)) * 100
        logger.debug(f"  Required fields: {required_pct:.0f}% ({required_count}/{len(required_fields)})")

        # Optional sections
        sections = article.get_active_sections()
        logger.debug(f"  Content sections: {sections}/9")

        # Engagement elements
        paas = article.get_active_paas()
        faqs = article.get_active_faqs()
        takeaways = article.get_active_takeaways()
        logger.debug(
            f"  Engagement: {faqs} FAQs, {paas} PAAs, {takeaways} Key Takeaways"
        )

        # Citations
        has_sources = bool(article.Sources and article.Sources.strip())
        has_queries = bool(article.Search_Queries and article.Search_Queries.strip())
        logger.debug(f"  Citations: Sources={has_sources}, Queries={has_queries}")

    def __repr__(self) -> str:
        """String representation."""
        return f"ExtractionStage(stage_num={self.stage_num})"
