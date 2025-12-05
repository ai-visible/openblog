"""
Tests for CitationURLValidator

Tests:
- HTTP HEAD validation (valid URLs, 404s, timeouts)
- Alternative URL search (Gemini with GoogleSearch tool)
- URL filtering (competitors, internal links, forbidden domains)
- Fallback to company URL
- Citation count preservation
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pipeline.processors.url_validator import CitationURLValidator, FORBIDDEN_HOSTS
from pipeline.models.citation import Citation, CitationList
from pipeline.models.gemini_client import GeminiClient


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client."""
    client = Mock(spec=GeminiClient)
    client.generate_content = Mock(return_value="https://example.org – Alternative source")
    return client


@pytest.fixture
def validator(mock_gemini_client):
    """Create validator instance with mocked dependencies."""
    return CitationURLValidator(
        gemini_client=mock_gemini_client,
        max_attempts=3,  # Lower for faster tests
        timeout=2.0,
    )


class TestCitationURLValidator:
    """Test CitationURLValidator class."""

    @pytest.mark.asyncio
    async def test_check_url_status_valid(self, validator):
        """Test checking valid URL (HTTP 200)."""
        with patch.object(validator.http_client, 'head') as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = "https://example.com"
            mock_head.return_value = mock_response

            is_valid, final_url = await validator._check_url_status("https://example.com")

            assert is_valid is True
            assert final_url == "https://example.com"
            mock_head.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_url_status_404(self, validator):
        """Test checking invalid URL (HTTP 404)."""
        with patch.object(validator.http_client, 'head') as mock_head:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.url = "https://example.com/404"
            mock_head.return_value = mock_response

            is_valid, final_url = await validator._check_url_status("https://example.com/404")

            assert is_valid is False
            assert final_url == "https://example.com/404"

    @pytest.mark.asyncio
    async def test_check_url_status_timeout(self, validator):
        """Test handling timeout."""
        import httpx
        with patch.object(validator.http_client, 'head') as mock_head:
            mock_head.side_effect = httpx.TimeoutException("Timeout")

            is_valid, final_url = await validator._check_url_status("https://example.com")

            assert is_valid is False
            assert final_url == "https://example.com"

    @pytest.mark.asyncio
    async def test_check_url_status_redirect(self, validator):
        """Test handling redirect (301/302)."""
        with patch.object(validator.http_client, 'head') as mock_head:
            mock_head_response = Mock()
            mock_head_response.status_code = 301
            mock_head_response.url = "https://example.com/old"
            mock_head.return_value = mock_head_response

            with patch.object(validator.http_client, 'get') as mock_get:
                mock_get_response = Mock()
                mock_get_response.status_code = 200
                mock_get_response.url = "https://example.com/new"
                mock_get.return_value = mock_get_response

                is_valid, final_url = await validator._check_url_status("https://example.com/old")

                assert is_valid is True
                assert final_url == "https://example.com/new"

    def test_is_error_page_url(self, validator):
        """Test error page detection."""
        assert validator._is_error_page_url("https://example.com/404") is True
        assert validator._is_error_page_url("https://example.com/not-found") is True
        assert validator._is_error_page_url("https://example.com/error") is True
        assert validator._is_error_page_url("https://example.com/page") is False
        assert validator._is_error_page_url("https://example.com/article") is False

    def test_should_filter_url_forbidden_host(self, validator):
        """Test filtering forbidden hosts."""
        assert validator._should_filter_url(
            "https://vertexaisearch.cloud.google.com/page",
            "https://company.com",
            []
        ) is True

        assert validator._should_filter_url(
            "https://cloud.google.com/docs",
            "https://company.com",
            []
        ) is True

    def test_should_filter_url_company_domain(self, validator):
        """Test filtering company domain."""
        assert validator._should_filter_url(
            "https://company.com/page",
            "https://company.com",
            []
        ) is True

        assert validator._should_filter_url(
            "https://subdomain.company.com/page",
            "https://company.com",
            []
        ) is True

        assert validator._should_filter_url(
            "https://external.com/page",
            "https://company.com",
            []
        ) is False

    def test_should_filter_url_competitor(self, validator):
        """Test filtering competitor domains."""
        assert validator._should_filter_url(
            "https://competitor.com/page",
            "https://company.com",
            ["competitor.com"]
        ) is True

        assert validator._should_filter_url(
            "https://subdomain.competitor.com/page",
            "https://company.com",
            ["competitor.com"]
        ) is True

        assert validator._should_filter_url(
            "https://external.com/page",
            "https://company.com",
            ["competitor.com"]
        ) is False

    def test_normalize_hostname(self, validator):
        """Test hostname normalization."""
        assert validator._normalize_hostname("www.example.com") == "example.com"
        assert validator._normalize_hostname(".example.com") == "example.com"
        assert validator._normalize_hostname("EXAMPLE.COM") == "example.com"
        assert validator._normalize_hostname("subdomain.example.com") == "subdomain.example.com"

    def test_is_subdomain(self, validator):
        """Test subdomain detection."""
        assert validator._is_subdomain("subdomain.example.com", "example.com") is True
        assert validator._is_subdomain("example.com", "example.com") is False
        assert validator._is_subdomain("other.com", "example.com") is False

    def test_build_search_query(self, validator):
        """Test search query building."""
        query = validator._build_search_query("Test Citation Title")
        assert query == "Test Citation Title"

        query = validator._build_search_query("[1] Test Citation Title")
        assert "[1]" not in query

        long_title = " ".join(["word"] * 50)
        query = validator._build_search_query(long_title)
        assert len(query) <= 103  # 100 + "..."

    def test_extract_urls_from_response(self, validator):
        """Test URL extraction from Gemini response."""
        response = "Check out https://example.com for more info"
        urls = validator._extract_urls_from_response(response)
        assert "https://example.com" in urls

        response = '{"url": "https://example.org"}'
        urls = validator._extract_urls_from_response(response)
        assert "https://example.org" in urls

        response = "No URLs here"
        urls = validator._extract_urls_from_response(response)
        assert len(urls) == 0

    def test_extract_title_from_response(self, validator):
        """Test title extraction from Gemini response."""
        response = '{"url_meta_title": "Test Title"}'
        title = validator._extract_title_from_response(response, "https://example.com")
        assert title == "Test Title"

        response = "title: Test Title https://example.com"
        title = validator._extract_title_from_response(response, "https://example.com")
        assert title == "Test Title" or title is None

    def test_get_company_fallback(self, validator):
        """Test company URL fallback."""
        is_valid, url, title = validator._get_company_fallback("https://company.com")
        assert is_valid is True
        assert url == "https://company.com"
        assert "company" in title.lower() or "Company" in title

    @pytest.mark.asyncio
    async def test_validate_citation_url_valid(self, validator):
        """Test validating a valid citation URL."""
        with patch.object(validator, '_check_url_status', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = (True, "https://example.com")
            with patch.object(validator, '_should_filter_url', return_value=False):

                is_valid, url, title = await validator.validate_citation_url(
                    url="https://example.com",
                    title="Test Source",
                    company_url="https://company.com",
                    competitors=[],
                    language="en",
                )

                assert is_valid is True
                assert url == "https://example.com"
                assert title == "Test Source"

    @pytest.mark.asyncio
    async def test_validate_citation_url_invalid_finds_alternative(self, validator):
        """Test validating invalid URL finds alternative."""
        with patch.object(validator, '_check_url_status', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = (False, "https://example.com/404")
            with patch.object(validator, '_find_alternative_url', new_callable=AsyncMock) as mock_find:
                mock_find.return_value = ("https://alternative.com", "Alternative Source")

                is_valid, url, title = await validator.validate_citation_url(
                    url="https://example.com/404",
                    title="Test Source",
                    company_url="https://company.com",
                    competitors=[],
                    language="en",
                )

                assert is_valid is True
                assert url == "https://alternative.com"
                assert title == "Alternative Source"

    @pytest.mark.asyncio
    async def test_validate_citation_url_fallback(self, validator):
        """Test fallback to company URL when all searches fail."""
        with patch.object(validator, '_check_url_status', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = (False, "https://example.com/404")
            with patch.object(validator, '_find_alternative_url', new_callable=AsyncMock) as mock_find:
                mock_find.return_value = None  # No alternative found

                is_valid, url, title = await validator.validate_citation_url(
                    url="https://example.com/404",
                    title="Test Source",
                    company_url="https://company.com",
                    competitors=[],
                    language="en",
                )

                assert is_valid is True
                assert url == "https://company.com"
                assert "company" in title.lower() or "Company" in title

    @pytest.mark.asyncio
    async def test_validate_citation_url_filtered_finds_alternative(self, validator):
        """Test that filtered URLs trigger alternative search."""
        with patch.object(validator, '_check_url_status', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = (True, "https://competitor.com")
            with patch.object(validator, '_should_filter_url', return_value=True):
                with patch.object(validator, '_find_alternative_url', new_callable=AsyncMock) as mock_find:
                    mock_find.return_value = ("https://external.com", "External Source")

                    is_valid, url, title = await validator.validate_citation_url(
                        url="https://competitor.com",
                        title="Test Source",
                        company_url="https://company.com",
                        competitors=["competitor.com"],
                        language="en",
                    )

                    assert is_valid is True
                    assert url == "https://external.com"

    @pytest.mark.asyncio
    async def test_find_alternative_url_success(self, validator):
        """Test finding alternative URL successfully."""
        validator.gemini_client.generate_content = Mock(return_value="https://example.org – Alternative")
        
        with patch.object(validator, '_extract_urls_from_response', return_value=["https://example.org"]):
            with patch.object(validator, '_normalize_url', return_value="https://example.org"):
                with patch.object(validator, '_should_filter_url', return_value=False):
                    with patch.object(validator, '_check_url_status', new_callable=AsyncMock) as mock_check:
                        mock_check.return_value = (True, "https://example.org")
                        with patch.object(validator, '_extract_title_from_response', return_value="Alternative"):

                            result = await validator._find_alternative_url(
                                title="Test Source",
                                company_url="https://company.com",
                                competitors=[],
                                language="en",
                            )

                            assert result is not None
                            assert result[0] == "https://example.org"
                            assert result[1] == "Alternative"

    @pytest.mark.asyncio
    async def test_find_alternative_url_no_valid_candidates(self, validator):
        """Test when no valid alternative URLs found."""
        validator.gemini_client.generate_content = Mock(return_value="https://competitor.com")
        
        with patch.object(validator, '_extract_urls_from_response', return_value=["https://competitor.com"]):
            with patch.object(validator, '_normalize_url', return_value="https://competitor.com"):
                with patch.object(validator, '_should_filter_url', return_value=True):  # All filtered

                    result = await validator._find_alternative_url(
                        title="Test Source",
                        company_url="https://company.com",
                        competitors=["competitor.com"],
                        language="en",
                    )

                    assert result is None

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_validate_all_citations_parallel_execution(self, validator):
        """Test that validate_all_citations runs validations in parallel."""
        import asyncio
        from unittest.mock import AsyncMock, patch
        
        citations = [
            Citation(number=1, url="https://example.com/1", title="Source 1"),
            Citation(number=2, url="https://example.com/2", title="Source 2"),
            Citation(number=3, url="https://example.com/3", title="Source 3"),
        ]
        
        # Track call times to verify parallel execution
        call_times = []
        
        async def mock_validate_with_delay(url, title, **kwargs):
            """Mock validation with delay to detect sequential vs parallel."""
            import time
            call_times.append(time.time())
            await asyncio.sleep(0.1)  # Simulate validation delay
            return (True, url, title)
        
        with patch.object(validator, 'validate_citation_url', side_effect=mock_validate_with_delay):
            start_time = asyncio.get_event_loop().time()
            validated = await validator.validate_all_citations(
                citations=citations,
                company_url="https://company.com",
                competitors=[],
            )
            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
        
        # If parallel: should take ~0.1s (all run concurrently)
        # If sequential: would take ~0.3s (3 × 0.1s)
        assert duration < 0.2, f"Expected parallel execution (<0.2s), but took {duration:.2f}s"
        assert len(validated) == 3
        assert len(call_times) == 3

    @pytest.mark.asyncio
    async def test_validate_all_citations_preserves_count(self, validator):
        """Test that citation count is preserved."""
        citations = [
            Citation(number=1, url="https://example.com", title="Source 1"),
            Citation(number=2, url="https://example.org", title="Source 2"),
            Citation(number=3, url="https://example.net", title="Source 3"),
        ]

        with patch.object(validator, 'validate_citation_url', new_callable=AsyncMock) as mock_validate:
            mock_validate.side_effect = [
                (True, "https://example.com", "Source 1"),
                (True, "https://example.org", "Source 2"),
                (True, "https://example.net", "Source 3"),
            ]

            validated = await validator.validate_all_citations(
                citations=citations,
                company_url="https://company.com",
                competitors=[],
                language="en",
            )

            assert len(validated) == 3
            assert mock_validate.call_count == 3

    @pytest.mark.asyncio
    async def test_validate_all_citations_replaces_invalid(self, validator):
        """Test that invalid URLs are replaced."""
        citations = [
            Citation(number=1, url="https://example.com/404", title="Source 1"),
            Citation(number=2, url="https://example.org", title="Source 2"),
        ]

        with patch.object(validator, 'validate_citation_url', new_callable=AsyncMock) as mock_validate:
            mock_validate.side_effect = [
                (True, "https://alternative.com", "Alternative Source"),  # Replaced
                (True, "https://example.org", "Source 2"),  # Kept
            ]

            validated = await validator.validate_all_citations(
                citations=citations,
                company_url="https://company.com",
                competitors=[],
                language="en",
            )

            assert len(validated) == 2
            assert validated[0].url == "https://alternative.com"
            assert validated[1].url == "https://example.org"

    @pytest.mark.asyncio
    async def test_close(self, validator):
        """Test closing HTTP client."""
        with patch.object(validator.http_client, 'aclose', new_callable=AsyncMock) as mock_close:
            await validator.close()
            mock_close.assert_called_once()

    def test_repr(self, validator):
        """Test string representation."""
        repr_str = repr(validator)
        assert "CitationURLValidator" in repr_str
        assert "max_attempts=3" in repr_str
        assert "timeout=2.0" in repr_str


class TestCitationURLValidatorIntegration:
    """Integration tests for URL validation (with real HTTP calls disabled)."""

    @pytest.mark.asyncio
    async def test_full_validation_workflow(self, validator):
        """Test complete validation workflow."""
        citation_list = CitationList()
        citation_list.add_citation("https://example.com", "Valid Source")
        citation_list.add_citation("https://example.org/404", "Invalid Source")

        with patch.object(validator, 'validate_citation_url', new_callable=AsyncMock) as mock_validate:
            mock_validate.side_effect = [
                (True, "https://example.com", "Valid Source"),
                (True, "https://alternative.com", "Alternative Source"),  # Replaced
            ]

            validated = await validator.validate_all_citations(
                citations=citation_list.citations,
                company_url="https://company.com",
                competitors=[],
                language="en",
            )

            assert len(validated) == 2
            assert validated[0].url == "https://example.com"
            assert validated[1].url == "https://alternative.com"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

