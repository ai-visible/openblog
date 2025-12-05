"""
Tests for Stage 0: Data Fetch & Auto-Detection

Tests:
- Input validation
- Domain extraction
- Company name extraction
- Auto-detection
- Override application
"""

import pytest
from pipeline.core import ExecutionContext
from pipeline.blog_generation import DataFetchStage


@pytest.fixture
def stage():
    """Create Stage 0 instance."""
    return DataFetchStage()


@pytest.fixture
def valid_context():
    """Create valid ExecutionContext for testing."""
    return ExecutionContext(
        job_id="test-job-123",
        job_config={
            "primary_keyword": "Python blog writing",
            "company_url": "https://www.example.com",
        },
    )


class TestDataFetchStage:
    """Test Stage 0 data fetching and auto-detection."""

    @pytest.mark.asyncio
    async def test_execute_success(self, stage, valid_context):
        """Test successful Stage 0 execution."""
        result = await stage.execute(valid_context)

        # Check context is populated
        assert result.job_id == "test-job-123"
        assert result.company_data is not None
        assert result.language
        assert result.blog_page is not None

        # Check company data
        assert "company_name" in result.company_data
        assert "company_url" in result.company_data
        assert result.company_data["company_url"] == "https://www.example.com"

        # Check language defaults to 'en'
        assert result.language == "en"

        # Check blog_page
        assert result.blog_page["primary_keyword"] == "Python blog writing"

    def test_validate_input_success(self, stage, valid_context):
        """Test input validation with valid data."""
        # Should not raise
        stage._validate_input(valid_context)

    def test_validate_input_missing_keyword(self, stage):
        """Test input validation fails without primary_keyword."""
        context = ExecutionContext(
            job_id="test",
            job_config={
                "company_url": "https://example.com",
                # Missing primary_keyword
            },
        )

        with pytest.raises(ValueError, match="primary_keyword"):
            stage._validate_input(context)

    def test_validate_input_missing_url(self, stage):
        """Test input validation fails without company_url."""
        context = ExecutionContext(
            job_id="test",
            job_config={
                "primary_keyword": "test",
                # Missing company_url
            },
        )

        with pytest.raises(ValueError, match="company_url"):
            stage._validate_input(context)

    def test_extract_domain(self, stage):
        """Test domain extraction from URL."""
        test_cases = [
            ("https://www.example.com", "example.com"),
            ("https://example.com", "example.com"),
            ("http://www.my-company.org", "my-company.org"),
            ("https://sub.domain.co.uk", "sub.domain.co.uk"),
        ]

        for url, expected_domain in test_cases:
            domain = stage._extract_domain(url)
            assert domain == expected_domain

    def test_extract_domain_invalid(self, stage):
        """Test domain extraction with invalid URL."""
        with pytest.raises(ValueError):
            stage._extract_domain("not-a-url")

    def test_extract_company_name(self, stage):
        """Test company name extraction from domain."""
        test_cases = [
            ("example.com", "Example"),
            ("my-company.org", "My Company"),
            ("acme-corp.co.uk", "Acme Corp"),
            ("xyz.io", "Xyz"),
        ]

        for domain, expected_name in test_cases:
            name = stage._extract_company_name(domain)
            assert name == expected_name

    def test_apply_overrides(self, stage):
        """Test applying user overrides to auto-detected data."""
        auto_detected = {
            "company_name": "Auto Detected Inc",
            "company_location": "USA",
            "company_language": "en",
        }

        job_config = {
            "company_name": "User Provided Inc",  # Override
            "company_location": "Germany",  # Override
            # company_language not overridden
        }

        result = stage._apply_overrides(auto_detected, job_config)

        # Check overrides applied
        assert result["company_name"] == "User Provided Inc"
        assert result["company_location"] == "Germany"
        assert result["company_language"] == "en"  # Not overridden

    def test_normalize_job_config(self, stage):
        """Test job config normalization."""
        config = {
            "primary_keyword": "test",
            "company_url": "https://example.com",
        }

        normalized = stage._normalize_job_config(config)

        # Check defaults added
        assert "content_generation_instruction" in normalized
        assert len(normalized["content_generation_instruction"]) > 0

    def test_normalize_job_config_preserves_instruction(self, stage):
        """Test that existing instruction is preserved."""
        config = {
            "primary_keyword": "test",
            "company_url": "https://example.com",
            "content_generation_instruction": "Custom instruction",
        }

        normalized = stage._normalize_job_config(config)

        assert normalized["content_generation_instruction"] == "Custom instruction"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
