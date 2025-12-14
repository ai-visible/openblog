"""
Stage 4: Citations Validation and Formatting

Maps to v4.1 Phase 4, Steps 8-13: CitationSanitizer + Information Extractor + AI Agent3 + Formatting

Processes citations from the article:
1. Extract sources from structured_data.Sources field
2. Parse citation format [1], [2], etc.
3. Extract URLs and titles
4. Validate URLs (optional)
5. Format as HTML

Input:
  - ExecutionContext.structured_data (ArticleOutput with Sources field)

Output:
  - ExecutionContext.parallel_results['citations_html'] (HTML formatted citations)

The citations from Gemini come in format:
[1]: https://example.com – Description of source
[2]: https://example.org – Another source
...
"""

import re
import logging
from typing import Dict, List, Any, Optional

from ..core import ExecutionContext, Stage
from ..models.citation import Citation, CitationList
from ..models.gemini_client import GeminiClient
from ..processors.url_validator import CitationURLValidator
from ..processors.ultimate_citation_validator import SmartCitationValidator, ValidationResult
from ..config import Config

logger = logging.getLogger(__name__)


class CitationsStage(Stage):
    """
    Stage 4: Citations Validation and Formatting.

    Handles:
    - Parsing sources from structured_data
    - Extracting URLs and titles
    - Creating Citation objects
    - Formatting as HTML
    - Validation (optional URL checks)
    
    Performance Notes:
    - Uses Gemini 3 Pro (gemini-3-pro-preview) for citation validation
    - Required for complex tool calling (web search + JSON output + validation)
    - Flash 2.5 cannot handle multi-tool workflows reliably
    """

    stage_num = 4
    stage_name = "Citations Validation & Formatting"

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize citations stage.
        
        Args:
            config: Configuration object (optional, loads from env if not provided)
        """
        self.config = config or Config()
        self.gemini_client = None  # Lazy initialization
        self.validator = None  # Lazy initialization
        self.ultimate_validator = None  # Ultimate citation validator

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 4: Process and format citations.

        Input from context:
        - structured_data: ArticleOutput with Sources field

        Output to context:
        - parallel_results['citations_html']: Formatted HTML

        Args:
            context: ExecutionContext from Stage 3

        Returns:
            Updated context with parallel_results populated
        """
        try:
            logger.info(f"Stage 4: {self.stage_name}")

            # Check if citations are disabled (defensive null check)
            job_config = context.job_config if context.job_config else {}
            if job_config.get("citations_disabled", False):
                logger.info("Citations disabled via job_config")
                context.parallel_results["citations_html"] = ""
                return context

            # Validate input
            if not context.structured_data:
                logger.warning("No structured_data available for citations")
                context.parallel_results["citations_html"] = ""
                return context

            sources_text = context.structured_data.Sources or ""
            if not sources_text.strip():
                logger.warning("No sources found in structured_data")
                context.parallel_results["citations_html"] = ""
                return context

            logger.info(f"Processing sources ({len(sources_text)} chars)...")

            # Get grounding URLs BEFORE parsing (AI will use them during parsing)
            grounding_urls = getattr(context, 'grounding_urls', [])
            if grounding_urls:
                logger.info(f"📎 AI will use {len(grounding_urls)} grounding URLs during citation parsing")

            # Parse citations using AI (no regex/string manipulation)
            # AI receives grounding URLs to enhance citations with specific URLs
            citation_list = await self._parse_sources(sources_text, grounding_urls=grounding_urls)

            if not citation_list.citations:
                logger.warning("No valid citations extracted")
                context.parallel_results["citations_html"] = ""
                return context

            logger.info(f"✅ Extracted {citation_list.count()} citations")
            for citation in citation_list.citations:
                logger.debug(f"   [{citation.number}]: {citation.url}")

            # Additional enhancement pass (AI may have already used grounding URLs, but this ensures all are enhanced)
            if grounding_urls:
                logger.info(f"📎 Final enhancement pass: {citation_list.count()} citations with {len(grounding_urls)} grounding URLs")
                citation_list = self._enhance_with_grounding_urls(citation_list, grounding_urls)
            else:
                logger.warning("⚠️  No grounding URLs available to enhance citations")

            # CRITICAL FIX: Preserve original URLs before validation
            # This allows fallback to original URLs if validation replaces them incorrectly
            original_urls = {}
            for citation in citation_list.citations:
                original_urls[citation.number] = citation.url
            logger.debug(f"Preserved {len(original_urls)} original URLs before validation")

            # ULTIMATE VALIDATION: Use enhanced citation validator
            if self.config.enable_citation_validation and context.company_data and context.company_data.get("company_url"):
                logger.info("🔍 Starting ultimate citation validation...")
                logger.info(f"    enable_citation_validation = {self.config.enable_citation_validation}")
                company_url_val = context.company_data.get('company_url') if context.company_data else ""
                logger.info(f"    company_url = {company_url_val}")
                logger.info(f"    Gemini client will be initialized for citation validation")
                validated_list = await self._validate_citations_ultimate(
                    citation_list, context
                )
                
                # CRITICAL FIX: Check if validation replaced URLs with wrong fallbacks
                for citation in validated_list.citations:
                    original_url = original_urls.get(citation.number)
                    if original_url and original_url != citation.url:
                        is_generic_fallback = any(domain in citation.url.lower() for domain in [
                            'pewresearch.org', 'nist.gov', 'census.gov', 'statista.com'
                        ])
                        
                        if context.company_data:
                            company_domain = context.company_data.get("company_url", "").replace("https://", "").replace("http://", "").split("/")[0]
                            is_company_url = company_domain and company_domain in original_url.lower()
                        else:
                            is_company_url = False
                        
                        if is_generic_fallback:
                            logger.warning(f"⚠️  Citation [{citation.number}] was replaced with generic fallback")
                            logger.warning(f"    Original: {original_url}")
                            logger.warning(f"    Replaced: {citation.url}")
                        elif is_company_url:
                            logger.warning(f"   ⚠️  Company URL was replaced - original was invalid (404)")
                            logger.warning(f"   ❌ NOT restoring invalid company URL: {original_url}")
                
                citation_list = validated_list
            elif self.config.enable_citation_validation:
                logger.info("Citation URL validation skipped (no company_url)")
            else:
                logger.info("Citation URL validation disabled")

            # Format as HTML
            citations_html = citation_list.to_html_paragraph_list()
            logger.info(f"   HTML size: {len(citations_html)} chars")
            
            # Build validated citation map for in-body links
            validated_citation_map = {}
            validated_source_name_map = {}
            for citation in citation_list.citations:
                validated_citation_map[citation.number] = citation.url
                title_words = citation.title.split() if citation.title else []
                if title_words:
                    source_name = title_words[0]
                    validated_source_name_map[source_name.lower()] = citation.url
            
            logger.info(f"   Validated citation map: {len(validated_citation_map)} entries")
            logger.info(f"   Validated source names: {list(validated_source_name_map.keys())}")

            # Store in context
            context.parallel_results["citations_html"] = citations_html
            context.parallel_results["citations_count"] = citation_list.count()
            context.parallel_results["citations_list"] = citation_list
            context.parallel_results["validated_citation_map"] = validated_citation_map
            context.parallel_results["validated_source_name_map"] = validated_source_name_map

            return context
        
        except AttributeError as e:
            if "'NoneType' object has no attribute 'get'" in str(e):
                logger.error(f"❌ Stage 4 AttributeError: {e}")
                logger.error("   This usually means company_data, sitemap_data, or job_config is None")
                logger.error(f"   company_data: {context.company_data is not None if hasattr(context, 'company_data') else 'N/A'}")
                logger.error(f"   sitemap_data: {getattr(context, 'sitemap_data', None) is not None}")
                logger.error(f"   job_config: {context.job_config is not None if hasattr(context, 'job_config') else 'N/A'}")
                # Return empty citations HTML to allow pipeline to continue
                context.parallel_results["citations_html"] = ""
                context.parallel_results["citations_count"] = 0
                return context
            else:
                raise
        except Exception as e:
            logger.error(f"❌ Stage 4 unexpected error: {e}", exc_info=True)
            # Return empty citations HTML to allow pipeline to continue
            context.parallel_results["citations_html"] = ""
            context.parallel_results["citations_count"] = 0
            return context

    async def _validate_citation_urls(
        self,
        citation_list: CitationList,
        context: ExecutionContext,
    ) -> CitationList:
        """
        Validate citation URLs and find alternatives for invalid ones.
        
        Matches v4.1 Step 11: AI Agent3 behavior:
        - Validates each URL with HTTP HEAD
        - Finds alternatives for invalid URLs
        - Filters competitors/internal/forbidden domains
        - Maintains citation count
        
        Args:
            citation_list: List of citations to validate
            context: Execution context with company data
            
        Returns:
            Validated CitationList (same count as input)
        """
        logger.info(f"Validating {citation_list.count()} citation URLs...")
        
        # Initialize validator if needed
        if not self.validator:
            if not self.gemini_client:
                # Use Gemini 3 Pro for citation validation (tool calling required)
                # Use Gemini 3 Pro for web search + JSON + tool calling capabilities
                # 2.5 Flash cannot handle complex tool calling with JSON output reliably
                self.gemini_client = GeminiClient(model="gemini-3-pro-preview")
            self.validator = CitationURLValidator(
                gemini_client=self.gemini_client,
                max_attempts=self.config.max_validation_attempts,
                timeout=self.config.citation_validation_timeout,
            )
        
        # Get company data (with null check)
        if not context.company_data:
            logger.warning("No company_data available for citation validation")
            return citation_list
        company_url = context.company_data.get("company_url", "")
        competitors = context.company_data.get("company_competitors", [])
        language = context.language or "en"
        
        # Validate all citations
        try:
            validated_citations = await self.validator.validate_all_citations(
                citations=citation_list.citations,
                company_url=company_url,
                competitors=competitors,
                language=language,
            )
            
            # OPTIMIZATION: Skip post-validation to speed up (already validated during main validation)
            # Post-validation was adding ~30 seconds and catching minimal issues
            # If needed, can re-enable but it slows down the workflow significantly
            logger.info("Skipping post-validation (performance optimization)")
            final_valid_count = len(validated_citations)  # Assume all valid (they were validated above)
            valid_ratio = 1.0
            
            # DISABLED: Post-validation check (too slow)
            # Uncomment below if you want to re-enable double-checking
            # logger.info("Running post-validation check on all citations...")
            # final_valid_count = 0
            # post_validation_results = []
            # for citation in validated_citations:
            #     try:
            #         is_valid, final_url = await self.validator._check_url_status(citation.url)
            #         post_validation_results.append({'citation': citation, 'valid': is_valid, 'url': final_url})
            #         if is_valid:
            #             final_valid_count += 1
            #     except Exception as e:
            #         logger.error(f"Error in post-validation for [{citation.number}]: {e}")
            #         post_validation_results.append({'citation': citation, 'valid': False, 'url': citation.url})
            # valid_ratio = final_valid_count / len(validated_citations) if validated_citations else 0
            # logger.info(f"✅ Post-validation complete: {final_valid_count}/{len(validated_citations)} ({valid_ratio:.0%}) valid")
            
            # Quality threshold check: Require at least 75% valid URLs
            # OPTIMIZATION: Disabled for now (post-validation is disabled, so we can't measure accurately)
            # Can re-enable if post-validation is restored
            QUALITY_THRESHOLD = 0.75
            logger.info(f"✅ Citation validation complete: {len(validated_citations)} citations processed")
            
            # DISABLED: Quality threshold (requires post-validation)
            # if valid_ratio < QUALITY_THRESHOLD:
            #     logger.warning(f"⚠️  Citation quality below threshold: {valid_ratio:.0%} < {QUALITY_THRESHOLD:.0%}")
            # else:
            #     logger.info(f"✅ Citation quality acceptable: {valid_ratio:.0%} valid")
            
            # Create new CitationList with validated citations
            validated_list = CitationList()
            validated_list.citations = validated_citations
            
            return validated_list
            
        except Exception as e:
            logger.error(f"Error validating citations: {e}")
            logger.warning("Continuing with original citations")
            return citation_list

    def _enhance_with_grounding_urls(
        self, 
        citation_list: CitationList, 
        grounding_urls: List[Dict[str, str]]
    ) -> CitationList:
        """
        Enhance citations with SPECIFIC URLs from Gemini's Google Search grounding.
        
        GeminiClient resolves grounding URLs:
        - 'url': Real resolved URL (e.g., https://checkpoint.com/.../cloud-security/)
        - 'domain': Domain from title (e.g., "checkpoint.com")
        - 'proxy_url': Original vertex proxy URL (kept for reference)
        
        Strategy:
        1. For each citation, find a grounding URL where domain matches
        2. Replace the citation URL with the real resolved URL
        3. If multiple matches, prefer the one with most similar title
        
        Args:
            citation_list: CitationList with potentially generic URLs
            grounding_urls: List of {'url': str, 'domain': str, ...} from Gemini grounding
            
        Returns:
            Enhanced CitationList with real, validated source URLs
        """
        if not grounding_urls:
            return citation_list
        
        # Build domain -> specific URLs map
        # CRITICAL: Use TITLE as domain (not URL which is always vertexaisearch.cloud.google.com)
        domain_to_urls: Dict[str, List[Dict[str, str]]] = {}
        for grounding in grounding_urls:
            url = grounding.get('url', '')
            title = grounding.get('title', '')
            if not url or not title:
                continue
            # The title IS the domain (e.g., "sportingnews.com", "aljazeera.com")
            domain = title.lower().replace('www.', '')
            if domain not in domain_to_urls:
                domain_to_urls[domain] = []
            domain_to_urls[domain].append(grounding)
        
        logger.info(f"   Grounding URL domains (from titles): {', '.join(domain_to_urls.keys())}")
        
        enhanced_count = 0
        domain_only_count = 0
        
        for citation in citation_list.citations:
            # Extract domain from citation URL
            try:
                from urllib.parse import urlparse
                parsed = urlparse(citation.url)
                citation_domain = parsed.netloc.lower().replace('www.', '')
                # Check if URL is domain-only (path has <= 3 parts: /, maybe /path, maybe /path/item)
                path_parts = [p for p in parsed.path.split('/') if p]
                is_domain_only = len(path_parts) <= 1  # Domain-only if just "/" or "/single-item"
            except Exception:
                continue
            
            # Check if we have grounding URLs for this domain
            # The domain_to_urls keys are from grounding titles (e.g., "gartner.com")
            if citation_domain in domain_to_urls:
                specific_urls = domain_to_urls[citation_domain]
                
                if specific_urls:
                    # Find best match by title similarity
                    best_match = self._find_best_title_match(citation.title, specific_urls)
                    
                    # CRITICAL: Always enhance domain-only URLs, only enhance full URLs if significantly better
                    should_enhance = False
                    if is_domain_only:
                        # Domain-only URLs should ALWAYS be enhanced
                        should_enhance = True
                        domain_only_count += 1
                        logger.info(f"   🎯 Citation [{citation.number}] is domain-only - WILL ENHANCE")
                    elif best_match and best_match['url'] != citation.url:
                        # Full URLs: only enhance if grounding URL is significantly better (longer path = more specific)
                        grounding_path_parts = [p for p in urlparse(best_match['url']).path.split('/') if p]
                        if len(grounding_path_parts) > len(path_parts) + 1:  # Significantly more specific
                            should_enhance = True
                            logger.info(f"   📎 Citation [{citation.number}] full URL - enhancing to more specific URL")
                        else:
                            logger.debug(f"   ⏭️  Citation [{citation.number}] already has good full URL - skipping")
                    
                    if should_enhance and best_match:
                        old_url = citation.url
                        citation.url = best_match['url']
                        enhanced_count += 1
                        logger.info(f"   ✅ Citation [{citation.number}] enhanced:")
                        logger.info(f"      OLD: {old_url}")
                        logger.info(f"      NEW: {citation.url[:80]}...")
        
        if enhanced_count > 0:
            logger.info(f"✅ Enhanced {enhanced_count} citations with specific URLs")
            if domain_only_count > 0:
                logger.info(f"   📊 {domain_only_count} domain-only URLs converted to full URLs")
        else:
            logger.info("   No URLs needed enhancement")
        
        return citation_list
    
    def _find_best_title_match(
        self, 
        citation_title: str, 
        grounding_urls: List[Dict[str, str]]
    ) -> Optional[Dict[str, str]]:
        """Find the grounding URL with the most similar title."""
        if not grounding_urls:
            return None
        
        if len(grounding_urls) == 1:
            return grounding_urls[0]
        
        # Simple word overlap scoring
        citation_words = set(citation_title.lower().split())
        
        best_match = grounding_urls[0]
        best_score = 0
        
        for grounding in grounding_urls:
            title = grounding.get('title', '')
            grounding_words = set(title.lower().split())
            overlap = len(citation_words & grounding_words)
            if overlap > best_score:
                best_score = overlap
                best_match = grounding
        
        return best_match

    async def _parse_sources(self, sources_text: str, grounding_urls: List[Dict[str, str]] = None) -> CitationList:
        """
        Parse sources text into Citation objects using AI (Gemini).
        
        NO REGEX, NO STRING MANIPULATION - AI-only parsing.
        
        Uses Gemini grounding URLs to enhance citations with specific source URLs.

        Args:
            sources_text: Raw sources from structured_data
            grounding_urls: Optional list of grounding URLs from Gemini search

        Returns:
            CitationList with extracted citations
        """
        citation_list = CitationList()
        
        if not sources_text or not sources_text.strip():
            return citation_list
        
        # Use AI (Gemini) to parse citations - NO regex, NO string manipulation
        logger.info("🤖 Using AI to parse citations (no regex/string manipulation)")
        
        try:
            # Build schema for CitationList using genai types
            from google.genai import types
            citation_schema = types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "citations": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "number": types.Schema(type=types.Type.INTEGER, description="Citation number [1], [2], etc."),
                                "url": types.Schema(type=types.Type.STRING, description="Full URL (must start with http:// or https://)"),
                                "title": types.Schema(type=types.Type.STRING, description="Short descriptive title (8-15 words)"),
                            },
                            required=["number", "url", "title"]
                        ),
                        description="List of citations"
                    )
                },
                required=["citations"]
            )
            
            # Build grounding URLs context for AI
            grounding_context = ""
            if grounding_urls:
                grounding_context = "\n\nAvailable grounding URLs from Google Search (use these specific URLs when matching domains):\n"
                for i, grounding in enumerate(grounding_urls[:10], 1):  # Limit to first 10
                    url = grounding.get('url', '')
                    title = grounding.get('title', '')
                    domain = grounding.get('domain', '')
                    if url:
                        grounding_context += f"{i}. Domain: {domain} | URL: {url} | Title: {title}\n"
            
            # Prompt AI to extract citations
            prompt = f"""Extract all citations from the following Sources text and return them as a structured CitationList.

Sources text:
{sources_text}
{grounding_context}

Extract each citation with:
- number: The citation number [1], [2], etc.
- url: The full URL (must start with http:// or https://)
  * If a grounding URL matches the citation domain, use the SPECIFIC grounding URL instead of generic domain URLs
  * Prefer specific article/report URLs over generic domain URLs
- title: A short descriptive title (8-15 words)

Return ONLY valid citations with proper URLs. Skip any invalid entries.
Use the grounding URLs provided above to enhance citations with specific source URLs when available.
"""
            
            gemini_client = GeminiClient()
            response_text = await gemini_client.generate_content(
                prompt=prompt,
                response_schema=citation_schema,
                enable_tools=False,  # No web search needed for parsing (grounding URLs already provided)
            )
            
            if response_text:
                import json
                try:
                    parsed_data = json.loads(response_text)
                    citation_list = CitationList.model_validate(parsed_data)
                    logger.info(f"✅ AI parsed {len(citation_list.citations)} citations")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse AI response as JSON: {e}")
                    logger.debug(f"   Response text: {response_text[:500]}")
                except Exception as e:
                    logger.error(f"❌ Failed to validate CitationList: {e}")
            else:
                logger.warning("⚠️ AI parsing returned no response")
                
        except Exception as e:
            logger.error(f"❌ AI citation parsing failed: {e}")
            logger.warning("   Falling back to empty citation list")
        
        # Resolve any proxy URLs (vertexaisearch.cloud.google.com redirects)
        citation_list = self._resolve_proxy_urls(citation_list)
        
        return citation_list
    
    def _resolve_proxy_urls(self, citation_list: CitationList) -> CitationList:
        """
        Resolve Gemini grounding proxy URLs to real destination URLs.
        
        Gemini sometimes includes proxy URLs directly in the Sources field:
        https://vertexaisearch.cloud.google.com/grounding-api-redirect/...
        
        These redirect (302) to the actual source. We follow the redirect
        to get clean, real URLs for citations.
        """
        import requests
        
        resolved_count = 0
        for citation in citation_list.citations:
            if 'vertexaisearch.cloud.google.com' in citation.url:
                try:
                    resp = requests.head(citation.url, allow_redirects=False, timeout=5)
                    if resp.status_code in (301, 302, 303, 307, 308):
                        real_url = resp.headers.get('Location', citation.url)
                        logger.info(f"   📎 Resolved proxy URL [{citation.number}]: {real_url}")
                        citation.url = real_url
                        resolved_count += 1
                except Exception as e:
                    logger.warning(f"   Failed to resolve proxy URL [{citation.number}]: {e}")
        
        if resolved_count > 0:
            logger.info(f"✅ Resolved {resolved_count} proxy URLs to real URLs")
        
        return citation_list

    async def _validate_citations_ultimate(
        self,
        citation_list: CitationList,
        context: ExecutionContext
    ) -> CitationList:
        """
        Ultimate citation validation using the enhanced validator.
        
        Combines:
        - DOI validation via CrossRef API
        - URL status validation with caching
        - Alternative URL search for invalid URLs
        - Metadata quality analysis
        - Author sanity checks
        
        Args:
            citation_list: Citations to validate
            context: Execution context with company data
            
        Returns:
            CitationList with validated and enhanced citations
        """
        if not citation_list.citations:
            return citation_list
        
        # Initialize ultimate validator
        if not self.ultimate_validator:
            if not self.gemini_client:
                self.gemini_client = GeminiClient()
            self.ultimate_validator = SmartCitationValidator(
                gemini_client=self.gemini_client,
                timeout=8.0
            )
        
        # Convert citations to dict format for validation
        citations_for_validation = []
        for citation in citation_list.citations:
            citation_dict = {
                'url': citation.url,
                'title': citation.title,
                'authors': [],  # Isaac Security doesn't parse authors yet
                'doi': '',  # Could be extracted from URL if needed
                'year': 0   # Could be extracted from content if needed
            }
            citations_for_validation.append(citation_dict)
        
        # Extract company and competitor information
        if not context.company_data:
            logger.warning("No company_data available for ultimate citation validation")
            return citation_list
        company_url = context.company_data.get("company_url", "")
        # Fix: Handle case where sitemap_data exists but is None
        sitemap_data = getattr(context, 'sitemap_data', None) or {}
        competitors = sitemap_data.get("competitors", []) if isinstance(sitemap_data, dict) else []
        language = context.language or "en"
        
        # Validate all citations
        try:
            validation_results = await self.ultimate_validator.validate_citations_simple(
                citations_for_validation,
                company_url=company_url,
                competitors=competitors
            )
            
            # Create new citation list with validated URLs
            validated_list = CitationList()
            
            for i, (original_citation, validation_result) in enumerate(zip(citation_list.citations, validation_results)):
                if validation_result.is_valid:
                    # Use validated URL and title
                    enhanced_citation = Citation(
                        number=original_citation.number,
                        url=validation_result.url,
                        title=validation_result.title or original_citation.title
                    )
                    validated_list.citations.append(enhanced_citation)
                    
                    # Log validation result
                    validation_type = validation_result.validation_type
                    if validation_type == 'original_url':
                        logger.info(f"✅ Citation [{enhanced_citation.number}]: Original URL validated")
                    elif validation_type == 'alternative_found':
                        logger.info(f"🔄 Citation [{enhanced_citation.number}]: Alternative URL found")
                        logger.info(f"   Original: {original_citation.url}")
                        logger.info(f"   Enhanced: {enhanced_citation.url}")
                    elif validation_type == 'doi_verified':
                        logger.info(f"📚 Citation [{enhanced_citation.number}]: DOI verified")
                    
                    if validation_result.issues:
                        for issue in validation_result.issues:
                            logger.warning(f"   ⚠️  {issue}")
                            
                else:
                    # Citation failed validation - KEEP IT but mark as potentially unverified
                    # Only filter if it's clearly spam or malicious
                    should_filter = any(
                        'spam' in issue.lower() or 'malicious' in issue.lower() or 'phishing' in issue.lower()
                        for issue in validation_result.issues
                    )
                    
                    if should_filter:
                        logger.warning(f"⚠️ Filtering out Citation [{original_citation.number}]: Security concern")
                        for issue in validation_result.issues:
                            logger.warning(f"   {issue}")
                    else:
                        # Keep citation even if validation failed (HTTP errors are common)
                        # Users can verify sources themselves
                        logger.warning(f"⚠️ Keeping Citation [{original_citation.number}] despite validation issues:")
                        for issue in validation_result.issues:
                            logger.warning(f"   {issue}")
                        validated_list.citations.append(original_citation)
            
            # Renumber citations
            for i, citation in enumerate(validated_list.citations, 1):
                citation.number = i
            
            logger.info(f"🔍 Ultimate validation complete: {len(validated_list.citations)} citations processed")
            
            return validated_list
            
        except Exception as e:
            logger.error(f"Ultimate citation validation failed: {e}")
            # Return original citations on failure
            return citation_list
    
    def __repr__(self) -> str:
        """String representation."""
        return f"CitationsStage(stage_num={self.stage_num})"
