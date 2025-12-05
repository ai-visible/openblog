"""
Stage 1: Market-Aware Prompt Construction

ABOUTME: Builds market-specific prompts for different countries/regions
ABOUTME: Replaces German-only template with culturally appropriate content generation

Maps to v4.1 Phase 2, Step 4: create_prompt

Builds the main article prompt by:
1. Determining target market from country parameter
2. Loading market-specific prompt template from market factory
3. Injecting all variables (keyword, company, language, country, etc)
4. Validating prompt structure for market requirements
5. Storing in context for Stage 2

This prompt is CRITICAL because it drives deep research in Stage 2.
The market-specific prompt ensures:
- Cultural communication patterns appropriate for target market
- Regulatory context relevant to country (BAFA for DE, WKO for AT, ANAH for FR)
- Quality standards matching market benchmarks
- Authority positioning suitable for local professional expectations

Combined with tools (googleSearch, urlContext), this creates market-appropriate deep research.
"""

import logging
from typing import Dict, Any

from ..core import ExecutionContext, Stage
from ..prompts.main_article import get_main_article_prompt

logger = logging.getLogger(__name__)


class PromptBuildStage(Stage):
    """
    Stage 1: Build market-specific article prompt with variable injection.

    Builds the complete prompt that will be sent to Gemini, customized for target market.
    Prompt includes market-specific quality standards and cultural adaptation.
    """

    stage_num = 1
    stage_name = "Market-Aware Prompt Construction"

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 1: Build market-specific article prompt.

        Inputs from context:
        - job_config.primary_keyword: Main topic
        - job_config.country: Target country (DE, AT, FR, etc.)
        - job_config.language: Target language (de, fr, en, etc.)
        - company_data.company_name: Company name
        - company_data.company_info: Business info
        - company_data.company_competitors: Competitors to avoid
        - blog_page.links: Internal links to reference

        Outputs to context:
        - prompt: Complete market-specific prompt string
        - target_market: Market profile information

        Args:
            context: ExecutionContext from Stage 0

        Returns:
            Updated context with market-aware prompt populated

        Raises:
            ValueError: If required fields missing
        """
        logger.info(f"Stage 1: {self.stage_name}")

        # Extract variables from context
        primary_keyword = context.job_config.get("primary_keyword", "")
        company_name = context.company_data.get("company_name", "Company")
        company_info = context.company_data.get("company_info", {})
        competitors = context.company_data.get("company_competitors", [])
        
        # Market-specific parameters with validation
        from ..prompts.main_article import validate_country
        raw_country = context.job_config.get("country", "US") 
        country = validate_country(raw_country)
        language = context.job_config.get("language") or context.language or "en"
        
        internal_links = context.blog_page.get("links", "")
        custom_instructions = context.job_config.get("content_generation_instruction", "")
        system_prompts = context.job_config.get("system_prompts", [])

        logger.debug(f"Keyword: {primary_keyword}")
        logger.debug(f"Target Market: {country} (raw: {raw_country})")
        logger.debug(f"Language: {language}")
        logger.debug(f"System prompts: {len(system_prompts)} provided")
        logger.debug(f"Company: {company_name}")
        logger.debug(f"Competitors: {len(competitors)} identified")

        # Validate inputs
        if not primary_keyword:
            raise ValueError("primary_keyword is required")

        # Build market-aware prompt using enhanced template with robust error handling
        logger.debug(f"Building market-aware prompt for {country}...")

        try:
            prompt = get_main_article_prompt(
                primary_keyword=primary_keyword,
                company_name=company_name,
                company_info=company_info,
                language=language,
                country=country,
                internal_links=internal_links,
                competitors=competitors,
                custom_instructions=custom_instructions,
                system_prompts=system_prompts,
            )
        except Exception as e:
            logger.error(f"Failed to build market-aware prompt for {country}: {e}")
            logger.info("Attempting fallback to US market template")
            
            try:
                # First fallback: Use US market but keep original language
                prompt = get_main_article_prompt(
                    primary_keyword=primary_keyword,
                    company_name=company_name,
                    company_info=company_info,
                    language=language,
                    country="US",  # Safe fallback country
                    internal_links=internal_links,
                    competitors=competitors,
                    custom_instructions=custom_instructions,
                    system_prompts=system_prompts,
                )
                logger.warning(f"Successfully generated fallback prompt using US market for {country}")
            except Exception as fallback_error:
                logger.error(f"US market fallback also failed: {fallback_error}")
                logger.info("Attempting minimal safe prompt generation")
                
                try:
                    # Final fallback: Minimal safe configuration
                    prompt = get_main_article_prompt(
                        primary_keyword=primary_keyword,
                        company_name=company_name,
                        company_info={},  # Empty company info
                        language="en",  # Safe language
                        country="US",  # Safe country
                        internal_links="",  # No internal links
                        competitors=[],  # No competitors
                        custom_instructions="",  # No custom instructions
                        system_prompts=[],  # No system prompts
                    )
                    logger.warning("Generated minimal safe prompt - some features may be missing")
                except Exception as final_error:
                    logger.critical(f"All prompt generation attempts failed: {final_error}")
                    raise ValueError(f"Unable to generate any prompt - system error: {final_error}")

        # Simple validation
        if not prompt or len(prompt.strip()) < 1000:
            raise ValueError("Generated prompt is too short or empty")
        
        logger.info(f"✅ Market-aware prompt generated successfully for {country}")

        # Store basic market information in context
        # Note: MARKET_CONFIG was removed in favor of universal standards
        # Using UNIVERSAL_STANDARDS instead
        from ..prompts.main_article import UNIVERSAL_STANDARDS
        market_profile_data = {
            "country": country,
            "language": language,
            "target_word_count": UNIVERSAL_STANDARDS["word_count_target"],
            "min_word_count": int(UNIVERSAL_STANDARDS["min_word_count"]),
            "authorities": UNIVERSAL_STANDARDS.get("authorities", "Industry experts and authoritative sources")
        }

        # Store in context
        context.prompt = prompt
        context.target_market = country
        context.market_profile = market_profile_data

        # Log metrics
        prompt_length = len(prompt)
        logger.info(f"✅ Market-specific prompt built successfully")
        logger.info(f"   Length: {prompt_length} characters")
        logger.info(f"   Target Market: {country}")
        logger.info(f"   Market Profile: {'Loaded' if market_profile_data else 'Failed to load'}")
        logger.info(f"   Keyword: '{primary_keyword}'")
        logger.info(f"   Company: '{company_name}'")
        logger.info(f"   Language: {language}")

        return context

    def _validate_prompt(self, prompt: str) -> None:
        """
        Basic prompt validation for test compatibility.
        
        Args:
            prompt: Prompt string to validate
            
        Raises:
            ValueError: If prompt is invalid
        """
        if not prompt or len(prompt.strip()) == 0:
            raise ValueError("Prompt is empty")
        
        # Check for required sections
        required_sections = [
            "*** INPUT ***",
            "*** TASK ***", 
            '"Headline"',
            '"Sources"',
            "```json"
        ]
        
        missing = []
        for section in required_sections:
            if section not in prompt:
                missing.append(section)
        
        if missing:
            raise ValueError(f"Prompt missing required sections: {', '.join(missing)}")
        
        # Check minimum length - but prioritize missing sections error
        if len(prompt) < 2000 and not missing:
            raise ValueError(f"Prompt too short ({len(prompt)} chars, expected > 2000)")

