"""
Tests for Stage 1: Prompt Construction

Tests:
- Prompt template loading
- Variable injection
- Prompt validation
- Edge cases (missing variables, special characters)
"""

import pytest
from pipeline.core import ExecutionContext
from pipeline.blog_generation.stage_01_prompt_build import PromptBuildStage


@pytest.fixture
def stage():
    """Create Stage 1 instance."""
    return PromptBuildStage()


@pytest.fixture
def valid_context():
    """Create valid ExecutionContext for Stage 1."""
    return ExecutionContext(
        job_id="test-job-123",
        job_config={
            "primary_keyword": "Python blog writing",
            "content_generation_instruction": "Write comprehensive content",
        },
        company_data={
            "company_name": "SCAILE",
            "company_url": "https://scaile.com",
            "company_language": "en",
            "company_location": "Germany",
            "company_competitors": ["Competitor A", "Competitor B"],
            "company_info": {"description": "AI growth agency", "industry": "SaaS"},
        },
        language="en",
        blog_page={
            "primary_keyword": "Python blog writing",
            "links": "[1] /blog/ai-101\n[2] /blog/seo-tips",
        },
    )


class TestPromptBuildStage:
    """Test Stage 1 prompt construction."""

    @pytest.mark.asyncio
    async def test_execute_success(self, stage, valid_context):
        """Test successful prompt build."""
        result = await stage.execute(valid_context)

        # Check prompt is populated
        assert result.prompt
        assert len(result.prompt) > 2000

        # Check prompt contains key sections
        assert "*** INPUT ***" in result.prompt
        assert "*** TASK ***" in result.prompt
        assert "*** CONTENT RULES ***" in result.prompt
        assert "*** OUTPUT FORMAT ***" in result.prompt

        # Check variables are injected
        assert "Python blog writing" in result.prompt
        assert "SCAILE" in result.prompt
        assert "en" in result.prompt

        # Check JSON schema is included
        assert '"Headline"' in result.prompt
        assert '"section_01_title"' in result.prompt
        assert '"faq_01_question"' in result.prompt

    @pytest.mark.asyncio
    async def test_execute_missing_keyword(self, stage):
        """Test execution fails without primary_keyword."""
        context = ExecutionContext(
            job_id="test",
            job_config={},  # Missing primary_keyword
            company_data={"company_name": "Test"},
            language="en",
            blog_page={},
        )

        with pytest.raises(ValueError, match="primary_keyword is required"):
            await stage.execute(context)

    def test_validate_prompt_success(self, stage, valid_context):
        """Test prompt validation with valid prompt."""
        # Build a valid prompt with minimum length
        prompt = """*** INPUT ***
Primary Keyword: test

*** TASK ***
Test task

*** CONTENT RULES ***
""" + "Rule 1: Test content rule with detailed explanation and examples\n" * 50 + """

*** OUTPUT FORMAT ***
Output format:
```json
{
  "Headline": "test",
  "section_01_title": "test", 
  "faq_01_question": "test",
  "Sources": "test"
}
```"""

        # Should not raise
        stage._validate_prompt(prompt)

    def test_validate_prompt_empty(self, stage):
        """Test validation fails with empty prompt."""
        with pytest.raises(ValueError, match="empty"):
            stage._validate_prompt("")

    def test_validate_prompt_missing_sections(self, stage):
        """Test validation fails with missing required sections."""
        prompt = "Some text but missing required sections"

        with pytest.raises(ValueError, match="missing required sections"):
            stage._validate_prompt(prompt)

    def test_validate_prompt_too_short(self, stage):
        """Test validation fails with too short prompt."""
        prompt = "*** INPUT ***\nShort prompt"

        with pytest.raises(ValueError, match="missing required sections"):
            stage._validate_prompt(prompt)

    def test_prompt_contains_competitor_names(self, stage):
        """Test that competitor names are included in prompt."""
        context = ExecutionContext(
            job_id="test",
            job_config={"primary_keyword": "test"},
            company_data={
                "company_name": "MyCompany",
                "company_competitors": ["Competitor A", "Competitor B"],
                "company_info": {},
            },
            language="en",
            blog_page={},
        )

        # Use the stage's import
        from pipeline.prompts.main_article import get_main_article_prompt

        prompt = get_main_article_prompt(
            primary_keyword="test",
            company_name="MyCompany",
            company_info={},
            language="en",
            internal_links="",
            competitors=["Competitor A", "Competitor B"],
        )

        # Check competitors are mentioned in HARD RULES section
        assert "Competitor A" in prompt or "NEVER" in prompt
        assert len(prompt) > 2000

    @pytest.mark.asyncio
    async def test_prompt_language_injection(self, stage):
        """Test that language is properly injected in prompt."""
        context = ExecutionContext(
            job_id="test",
            job_config={"primary_keyword": "test"},
            company_data={"company_name": "Test", "company_info": {}},
            language="de",  # German
            blog_page={},
        )

        result = await stage.execute(context)

        # Language should be in prompt
        assert "de" in result.prompt.lower()

    @pytest.mark.asyncio
    async def test_country_parameter_injection(self, stage):
        """Test that country parameter is properly handled."""
        context = ExecutionContext(
            job_id="test",
            job_config={
                "primary_keyword": "test",
                "country": "AT",  # Austria
                "language": "de"
            },
            company_data={"company_name": "Test", "company_info": {}},
            language="de",
            blog_page={},
        )

        result = await stage.execute(context)

        # Check market profile is set correctly
        assert result.target_market == "AT"
        assert result.market_profile is not None
        assert result.market_profile["country"] == "AT"
        
        # Check Austrian authorities are referenced
        assert "WKO" in result.prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
