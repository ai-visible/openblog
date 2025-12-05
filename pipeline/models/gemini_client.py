"""
AI Client with Tools Support - Using scaile-services OpenRouter Gateway

Handles:
- Initialization with scaile-services endpoint
- Configuration (text/plain + tools)
- API calls with tool execution
- Response parsing (JSON extraction from plain text)
- Retry logic (exponential backoff)
- Error handling

This client enables DEEP RESEARCH because:
- Tools: google_search + url_context enable web search during generation
- Response format: text/plain allows natural language + JSON mix
- scaile-services handles all model failover and tool execution

Configuration:
- Model: google/gemini-2.5-flash (default, fast) - configurable
- Quality mode: google/gemini-3-pro-preview (slower, higher quality)
- Response mime type: text/plain (NOT application/json)
- Temperature: 0.2 (consistency)
- Tools: [google_search, url_context] ENABLED via scaile-services

v2: Uses scaile-services OpenRouter gateway for all AI calls
"""

import os
import json
import re
import time
import asyncio
import logging
import httpx
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# scaile-services endpoint
SCAILE_SERVICES_URL = os.environ.get(
    "SCAILE_SERVICES_URL", 
    "https://clients--scaile-services-fastapi-app.modal.run"
)

# Default models
# Blog content needs high quality - use 3.0 Pro by default
DEFAULT_MODEL = "google/gemini-3-pro-preview"  # Quality mode (default for blog writing)
FAST_MODEL = "google/gemini-2.5-flash"  # Fast mode (for testing/drafts)


class GeminiClient:
    """
    AI client for content generation with tools.
    Uses scaile-services OpenRouter gateway for all AI calls.

    Implements:
    - Content generation with tools (google_search, url_context)
    - Response parsing (JSON extraction from text/plain)
    - Retry logic with exponential backoff
    - Error handling and logging
    """

    # Configuration constants
    RESPONSE_MIME_TYPE = "text/plain"  # Critical: NOT application/json
    TEMPERATURE = 0.2  # Consistency
    MAX_OUTPUT_TOKENS = 65536  # Full article (not sent to API by default)

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_WAIT = 5.0  # seconds
    RETRY_BACKOFF_MULTIPLIER = 2.0

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None) -> None:
        """
        Initialize AI client.

        Args:
            model: Model name (defaults to GEMINI_MODEL env var or google/gemini-2.5-flash)
            api_key: Ignored - scaile-services handles auth
        """
        # Set model (constructor arg > env var > default)
        self.MODEL = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        
        # Map old model names to new OpenRouter format if needed
        if not self.MODEL.startswith("google/") and not self.MODEL.startswith("openai/"):
            self.MODEL = f"google/{self.MODEL}"
        
        self.base_url = SCAILE_SERVICES_URL
        logger.info(f"AI client initialized (model: {self.MODEL}, backend: scaile-services)")

    async def generate_content(
        self,
        prompt: str,
        enable_tools: bool = True,
    ) -> str:
        """
        Generate content using scaile-services AI endpoint.

        Args:
            prompt: Complete prompt string
            enable_tools: Whether to enable tools (default: True)
                - google_search: Real-time web search
                - url_context: Ground content in URLs

        Returns:
            Raw response text (plain text with embedded JSON)

        Raises:
            Exception: If all retries fail
        """
        logger.info(f"Generating content with {self.MODEL}")
        logger.debug(f"Prompt length: {len(prompt)} characters")
        logger.debug(f"Tools enabled: {enable_tools}")

        # Build tools list
        tools = ["google_search", "url_context"] if enable_tools else []

        # Call API with retry logic
        response_text = await self._call_api_with_retry(prompt, tools)

        return response_text

    async def _call_api_with_retry(self, prompt: str, tools: List[str]) -> str:
        """
        Call scaile-services API with exponential backoff retry.

        Args:
            prompt: Complete prompt
            tools: List of tools to enable

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

                # Build request payload
                # Note: Blog generation uses text/plain to allow natural language + embedded JSON
                # The prompt itself instructs JSON output, but response format is text/plain
                payload = {
                    "prompt": prompt,
                    "model": self.MODEL,
                    "temperature": self.TEMPERATURE,
                    "response_format": "text/plain",  # Allow natural language + JSON mix
                }
                
                # Add tools if enabled
                if tools:
                    payload["tools"] = tools
                    payload["execute_tools"] = True

                # Make HTTP request (5 min timeout for deep research)
                async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
                    response = await client.post(
                        f"{self.base_url}/ai/generate",
                        json=payload
                    )

                if response.status_code != 200:
                    error_text = response.text[:500]
                    logger.error(f"AI service error: {response.status_code} - {error_text}")
                    
                    # Check if retryable
                    if response.status_code in [429, 503, 502, 504]:
                        last_error = Exception(f"HTTP {response.status_code}: {error_text[:200]}")
                        if attempt < self.MAX_RETRIES - 1:
                            logger.warning(f"Retryable error (attempt {attempt + 1})")
                            logger.info(f"Waiting {wait_time:.1f}s before retry...")
                            await asyncio.sleep(wait_time)
                            wait_time *= self.RETRY_BACKOFF_MULTIPLIER
                            continue
                    raise Exception(f"AI service error: {response.status_code} - {error_text[:200]}")

                result = response.json()
                response_text = result.get("content", "")

                if not response_text:
                    raise Exception("Empty response from AI service")

                logger.info(f"✅ API call succeeded ({len(response_text)} chars)")
                return response_text

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(f"Timeout error (attempt {attempt + 1}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    logger.info(f"Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    wait_time *= self.RETRY_BACKOFF_MULTIPLIER
                continue

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
                    time.sleep(wait_time)
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
        return f"GeminiClient(model={self.MODEL}, backend=scaile-services)"
