"""
Tests for Stage 2: Gemini Content Generation

Tests:
- Gemini client initialization
- API configuration (tools enabled, text/plain format)
- Response parsing (JSON extraction from plain text)
- Error handling and retry logic
- Response validation
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pipeline.core import ExecutionContext
from pipeline.blog_generation.stage_02_gemini_call import GeminiCallStage
from pipeline.models.gemini_client import GeminiClient


@pytest.fixture
def valid_context():
    """Create valid ExecutionContext for Stage 2."""
    return ExecutionContext(
        job_id="test-job-123",
        job_config={"primary_keyword": "test"},
        company_data={"company_name": "Test Co"},
        language="en",
        prompt="""*** INPUT ***
Primary Keyword: test

*** TASK ***
Write a blog post.

*** CONTENT RULES ***
Rule 1: Keep it short.

*** OUTPUT ***
Output format:
```json
{
  "Headline": "Test Article",
  "section_01_title": "Introduction",
  "section_01_content": "<p>Test content</p>"
}
```""",
    )


class TestGeminiClient:
    """Test Gemini client functionality."""

    def test_client_initialization(self):
        """Test client can be initialized."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                # Should not raise
                client = GeminiClient()
                assert client is not None

    def test_client_initialization_missing_key(self):
        """Test initialization fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_GEMINI_API_KEY"):
                GeminiClient()

    def test_extract_json_from_code_block(self):
        """Test JSON extraction from code block."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                client = GeminiClient()

                response = """Some text before

```json
{
  "Headline": "Test",
  "section_01_title": "Intro"
}
```

Some text after"""

                result = client.extract_json_from_response(response)

                assert result["Headline"] == "Test"
                assert result["section_01_title"] == "Intro"

    def test_extract_json_from_plain_text(self):
        """Test JSON extraction from plain text (no code block)."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                client = GeminiClient()

                response = """Some text before {"Headline": "Test", "section_01_title": "Intro"} some text after"""

                result = client.extract_json_from_response(response)

                assert result["Headline"] == "Test"
                assert result["section_01_title"] == "Intro"

    def test_extract_json_not_found(self):
        """Test extraction fails when no JSON present."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                client = GeminiClient()

                response = "Just some plain text with no JSON"

                with pytest.raises(ValueError, match="No JSON found"):
                    client.extract_json_from_response(response)

    def test_is_retryable_error_rate_limit(self):
        """Test rate limit error is marked as retryable."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                client = GeminiClient()

                error = Exception("429 Rate limit exceeded")
                assert client._is_retryable_error(error) is True

    def test_is_retryable_error_timeout(self):
        """Test timeout error is marked as retryable."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                client = GeminiClient()

                error = Exception("Timeout waiting for response")
                assert client._is_retryable_error(error) is True

    def test_is_retryable_error_auth_failure(self):
        """Test auth error is NOT retryable."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                client = GeminiClient()

                error = Exception("401 Authentication failed")
                assert client._is_retryable_error(error) is False

    def test_is_retryable_error_bad_request(self):
        """Test bad request error is NOT retryable."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                client = GeminiClient()

                error = Exception("400 Bad request")
                assert client._is_retryable_error(error) is False


class TestGeminiCallStage:
    """Test Stage 2: Gemini Call."""

    @pytest.mark.asyncio
    async def test_execute_success(self, valid_context):
        """Test successful Stage 2 execution."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                with patch(
                    "src.stages.stage_02_gemini_call.GeminiClient"
                ) as mock_client_class:
                    # Mock the client
                    mock_client = MagicMock()
                    mock_client_class.return_value = mock_client

                    # Mock successful response
                    test_response = """```json
{
  "Headline": "Test Article",
  "section_01_title": "Intro",
  "section_01_content": "<p>Test</p>"
}
```"""
                    mock_client.generate_content.return_value = test_response

                    # Execute stage
                    stage = GeminiCallStage()
                    result = await stage.execute(valid_context)

                    # Verify
                    assert result.raw_article == test_response
                    assert len(result.raw_article) > 0

    @pytest.mark.asyncio
    async def test_execute_missing_prompt(self):
        """Test execution fails without prompt."""
        context = ExecutionContext(
            job_id="test",
            job_config={},
            company_data={},
            language="en",
            prompt="",  # Missing!
        )

        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                stage = GeminiCallStage()

                with pytest.raises(ValueError, match="Prompt is required"):
                    await stage.execute(context)

    def test_validate_response_success(self, valid_context):
        """Test response validation with valid response."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                stage = GeminiCallStage()

                response = """Some content here
```json
{
  "Headline": "Test",
  "content": "Some substantial content that is long enough"
}
```"""

                # Should not raise
                stage._validate_response(response)

    def test_validate_response_empty(self):
        """Test validation fails with empty response."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                stage = GeminiCallStage()

                with pytest.raises(ValueError, match="Empty response"):
                    stage._validate_response("")

    def test_validate_response_too_short(self):
        """Test validation warns about short response."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.genai"):
                stage = GeminiCallStage()

                response = "Too short"

                # Should not raise, but logs warning
                stage._validate_response(response)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
