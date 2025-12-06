"""
AI Client with Tools Support - Direct Google GenAI SDK

Uses google-genai SDK directly for:
- Gemini content generation
- Built-in Google Search grounding (free 1,500/day)
  - Automatically fetches URL context from search results
  - Provides real-time web information
- Response parsing (JSON extraction from plain text)
- Retry logic with exponential backoff

Configuration:
- Model: gemini-3.0-pro-preview (default, Gemini 3.0 Pro Preview)
- Quality mode: gemini-3.0-pro-preview (same model)
- Response mime type: text/plain (NOT application/json)
- Temperature: 0.2 (consistency)
- Tools: Google Search (includes URL context via search results)
"""

import os
import json
import re
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Default models - using Gemini 3.0 Pro Preview
DEFAULT_MODEL = "gemini-3-pro-preview"  # Gemini 3.0 Pro Preview with search grounding (includes URL context)
QUALITY_MODEL = "gemini-3-pro-preview"  # Same model for quality mode


class GeminiClient:
    """
    AI client for content generation with Google Search grounding.
    Uses google-genai SDK directly.

    Implements:
    - Content generation with Google Search grounding
      (automatically fetches URL context from search results)
    - Response parsing (JSON extraction from text/plain)
    - Retry logic with exponential backoff
    - Error handling and logging
    """

    # Configuration constants
    RESPONSE_MIME_TYPE = "text/plain"  # Critical: NOT application/json
    TEMPERATURE = 0.2  # Consistency
    MAX_OUTPUT_TOKENS = 65536  # Full article

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_WAIT = 5.0  # seconds
    RETRY_BACKOFF_MULTIPLIER = 2.0

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None) -> None:
        """
        Initialize AI client.

        Args:
            model: Model name (defaults to GEMINI_MODEL env var or gemini-2.0-flash-exp)
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
        """
        # Set model
        self.MODEL = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        
        # Get API key
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable required")
        
        # Initialize client with v1alpha API version for Gemini 3.0 Pro Preview
        try:
            from google import genai
            from google.genai import types
            # Use v1alpha API version for preview models
            self.client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(api_version='v1alpha')
            )
            self._genai = genai
            logger.info(f"AI client initialized (model: {self.MODEL}, backend: google-genai SDK, API: v1alpha)")
        except ImportError:
            raise ImportError("google-genai package required. Install with: pip install google-genai")

    async def generate_content(
        self,
        prompt: str,
        enable_tools: bool = True,
    ) -> str:
        """
        Generate content using Gemini API with Google Search grounding.

        Args:
            prompt: Complete prompt string
            enable_tools: Whether to enable Google Search grounding (includes URL context)

        Returns:
            Raw response text (plain text with embedded JSON)

        Raises:
            Exception: If all retries fail
        """
        logger.info(f"Generating content with {self.MODEL}")
        logger.debug(f"Prompt length: {len(prompt)} characters")
        logger.debug(f"Grounding tools: {enable_tools}")

        # Call API with retry logic
        response_text = await self._call_api_with_retry(prompt, enable_tools)

        return response_text

    async def _call_api_with_retry(self, prompt: str, enable_grounding: bool) -> str:
        """
        Call Gemini API with exponential backoff retry.

        Args:
            prompt: Complete prompt
            enable_grounding: Whether to enable Google Search grounding (includes URL context)

        Returns:
            Response text

        Raises:
            Exception: If all retries fail
        """
        last_error = None
        wait_time = self.INITIAL_RETRY_WAIT

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.debug(f"API call attempt {attempt + 1}/{self.MAX_RETRIES}")

                # Build grounding tools if enabled
                tools = None
                if enable_grounding:
                    # Google Search grounding automatically includes URL context from search results
                    tools = [
                        self._genai.types.Tool(google_search=self._genai.types.GoogleSearch()),
                    ]
                    logger.debug("Google Search grounding enabled (includes URL context)")

                # Make synchronous call (google-genai doesn't have native async)
                # Run in executor to not block event loop
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.models.generate_content(
                        model=self.MODEL,
                        contents=prompt,
                        config=self._genai.types.GenerateContentConfig(
                            temperature=self.TEMPERATURE,
                            max_output_tokens=self.MAX_OUTPUT_TOKENS,
                            tools=tools,
                        )
                    )
                )

                # Extract text from response
                if not response or not response.text:
                    raise Exception("Empty response from Gemini API")

                response_text = response.text
                logger.info(f"✅ API call succeeded ({len(response_text)} chars)")
                
                # Log grounding metadata if available
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                        gm = candidate.grounding_metadata
                        if hasattr(gm, 'search_entry_point') and gm.search_entry_point:
                            logger.info("🔍 Google Search grounding used")
                        if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                            logger.info(f"📎 {len(gm.grounding_chunks)} grounding sources")

                return response_text

            except Exception as e:
                last_error = e
                error_type = type(e).__name__
                error_str = str(e).lower()

                # Check if error is retryable
                retryable = self._is_retryable_error(e)

                if not retryable:
                    logger.error(f"Non-retryable error: {error_type}: {e}")
                    raise

                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(
                        f"Retryable error (attempt {attempt + 1}): {error_type}: {e}"
                    )
                    logger.info(f"Waiting {wait_time:.1f}s before retry...")
                    await asyncio.sleep(wait_time)
                    wait_time *= self.RETRY_BACKOFF_MULTIPLIER
                else:
                    logger.error(f"All {self.MAX_RETRIES} retries failed: {error_type}")

        # All retries failed
        raise Exception(
            f"AI API call failed after {self.MAX_RETRIES} retries: {last_error}"
        )

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Check if error is retryable.

        Retryable:
        - Rate limit errors (429)
        - Timeout errors
        - Network errors
        - Service unavailable (503)

        Not retryable:
        - Authentication errors (401, 403)
        - Bad requests (400)
        - Validation errors
        - Malformed input

        Args:
            error: Exception to check

        Returns:
            True if error is retryable
        """
        error_str = str(error).lower()

        # Retryable patterns
        retryable_patterns = [
            "rate limit",
            "429",
            "timeout",
            "connection",
            "service unavailable",
            "503",
            "temporarily unavailable",
            "deadline exceeded",
            "resource exhausted",
            "quota",
        ]

        # Non-retryable patterns
        non_retryable_patterns = [
            "authentication",
            "401",
            "403",
            "forbidden",
            "unauthorized",
            "bad request",
            "400",
            "invalid",
            "malformed",
            "api key",
        ]

        # Check patterns
        for pattern in non_retryable_patterns:
            if pattern in error_str:
                return False

        for pattern in retryable_patterns:
            if pattern in error_str:
                return True

        # Default: retry unknown errors
        return True

    def extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from text/plain response.

        Response may contain:
        - JSON wrapped in ```json ... ```
        - Plain JSON object
        - Text before/after JSON
        - Multiple JSON blocks (concatenate)

        Args:
            response_text: Raw response text from AI

        Returns:
            Parsed JSON as dictionary

        Raises:
            ValueError: If no valid JSON found
            json.JSONDecodeError: If JSON is malformed
        """
        logger.debug(f"Extracting JSON from {len(response_text)} chars")

        # Try code block first
        code_block_match = re.search(r"```json\s*([\s\S]*?)\s*```", response_text)
        if code_block_match:
            json_str = code_block_match.group(1)
            logger.debug("Found JSON in code block")
            return json.loads(json_str)

        # Try plain JSON object
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if json_match:
            json_str = json_match.group(0)
            logger.debug("Found JSON object")
            return json.loads(json_str)

        # No JSON found
        raise ValueError("No JSON found in response")

    def __repr__(self) -> str:
        """String representation."""
        return f"GeminiClient(model={self.MODEL}, backend=google-genai)"
