"""
Tests for Stage 3: Extraction

Tests:
- Schema validation (ArticleOutput model)
- JSON extraction and parsing
- Partial data recovery
- Field normalization
- Completeness metrics
- Error handling
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pipeline.core import ExecutionContext
from pipeline.blog_generation.stage_03_extraction import ExtractionStage
from pipeline.models.output_schema import ArticleOutput


@pytest.fixture
def valid_context():
    """Create valid ExecutionContext for Stage 3."""
    return ExecutionContext(
        job_id="test-job-123",
        job_config={"primary_keyword": "test"},
        company_data={"company_name": "Test Co"},
        language="en",
        prompt="Test prompt",
        raw_article="""```json
{
  "Headline": "Test Article",
  "Subtitle": "A helpful guide",
  "Teaser": "This article explores an important topic.",
  "Direct_Answer": "Here is the answer to your question.",
  "Intro": "This is the introduction paragraph with more details.",
  "Meta_Title": "Test Article | Company",
  "Meta_Description": "Read this test article for information.",
  "section_01_title": "Introduction",
  "section_01_content": "<p>First section content</p>",
  "section_02_title": "Main Content",
  "section_02_content": "<p>Second section content</p>",
  "key_takeaway_01": "First takeaway point",
  "faq_01_question": "What is this about?",
  "faq_01_answer": "This article is about testing.",
  "Sources": "[1]: https://example.com – Test source",
  "Search_Queries": "Q1: test queries"
}
```""",
    )


class TestArticleOutputSchema:
    """Test ArticleOutput Pydantic model."""

    def test_valid_article_creation(self):
        """Test creating valid ArticleOutput."""
        article = ArticleOutput(
            Headline="Test Article",
            Teaser="Hook text here.",
            Direct_Answer="Answer here.",
            Intro="Intro paragraph here.",
            Meta_Title="Test | Co",
            Meta_Description="Description here.",
        )
        assert article.Headline == "Test Article"
        assert article.Teaser == "Hook text here."

    def test_required_fields_validation(self):
        """Test that required fields are validated."""
        with pytest.raises(ValueError):
            ArticleOutput(
                Headline="",  # Empty!
                Teaser="Hook",
                Direct_Answer="Answer",
                Intro="Intro",
                Meta_Title="Title",
                Meta_Description="Desc",
            )

    def test_optional_fields_empty(self):
        """Test optional fields can be empty."""
        article = ArticleOutput(
            Headline="Title",
            Teaser="Teaser",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="Meta",
            Meta_Description="Desc",
            section_01_title="",  # Optional, can be empty
            Lead_Survey_Title="",  # Optional, can be empty
        )
        assert article.section_01_title == ""
        assert article.Lead_Survey_Title == ""

    def test_meta_title_length_warning(self):
        """Test meta title exceeding recommended length."""
        # Should not raise, just log warning
        article = ArticleOutput(
            Headline="Title",
            Teaser="Teaser",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="This is a very long meta title that exceeds 60 characters significantly",
            Meta_Description="Desc",
        )
        assert len(article.Meta_Title) > 60

    def test_get_active_sections(self):
        """Test counting active sections."""
        article = ArticleOutput(
            Headline="Title",
            Teaser="Teaser",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="Meta",
            Meta_Description="Desc",
            section_01_title="Section 1",
            section_01_content="Content 1",
            section_02_title="Section 2",
            section_02_content="Content 2",
        )
        assert article.get_active_sections() == 2

    def test_get_active_faqs(self):
        """Test counting active FAQs."""
        article = ArticleOutput(
            Headline="Title",
            Teaser="Teaser",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="Meta",
            Meta_Description="Desc",
            faq_01_question="Q1",
            faq_01_answer="A1",
            faq_02_question="Q2",
            faq_02_answer="A2",
        )
        assert article.get_active_faqs() == 2

    def test_article_repr(self):
        """Test string representation."""
        article = ArticleOutput(
            Headline="Test Article with longer title",
            Teaser="Teaser",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="Meta",
            Meta_Description="Desc",
            section_01_title="Section 1",
        )
        repr_str = repr(article)
        assert "ArticleOutput" in repr_str
        assert "sections=1" in repr_str


class TestExtractionStage:
    """Test Stage 3: Extraction."""

    @pytest.mark.asyncio
    async def test_execute_success(self, valid_context):
        """Test successful Stage 3 execution."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.GeminiClient.__init__", return_value=None):
                with patch("src.models.gemini_client.GeminiClient.extract_json_from_response") as mock_extract:
                    mock_extract.return_value = {
                        "Headline": "Test Article",
                        "Teaser": "Hook",
                        "Direct_Answer": "Answer",
                        "Intro": "Intro",
                        "Meta_Title": "Meta",
                        "Meta_Description": "Desc",
                        "section_01_title": "Introduction",
                        "section_01_content": "<p>Content</p>",
                    }

                    stage = ExtractionStage()

                    # Execute
                    result = await stage.execute(valid_context)

                    # Verify structured_data is populated
                    assert result.structured_data is not None
                    assert isinstance(result.structured_data, ArticleOutput)
                    assert result.structured_data.Headline == "Test Article"
                    assert result.structured_data.section_01_title == "Introduction"

    @pytest.mark.asyncio
    async def test_execute_missing_raw_article(self):
        """Test execution fails without raw_article."""
        context = ExecutionContext(
            job_id="test",
            job_config={},
            company_data={},
            language="en",
            prompt="test",
            raw_article="",  # Missing!
        )

        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.GeminiClient.__init__", return_value=None):
                stage = ExtractionStage()

                with pytest.raises(ValueError, match="Raw article is required"):
                    await stage.execute(context)

    def test_parse_and_validate_success(self, valid_context):
        """Test successful parsing and validation."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.GeminiClient.__init__", return_value=None):
                stage = ExtractionStage()

                json_data = {
                    "Headline": "Test Article",
                    "Teaser": "Hook text.",
                    "Direct_Answer": "Answer text.",
                    "Intro": "Intro paragraph.",
                    "Meta_Title": "Test | Co",
                    "Meta_Description": "Description.",
                    "section_01_title": "Section 1",
                    "section_01_content": "<p>Content</p>",
                }

                article = stage._parse_and_validate(json_data)

                assert isinstance(article, ArticleOutput)
                assert article.Headline == "Test Article"
                assert article.get_active_sections() == 1

    def test_parse_and_validate_with_whitespace(self):
        """Test normalization of whitespace."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.GeminiClient.__init__", return_value=None):
                stage = ExtractionStage()

                json_data = {
                    "Headline": "  Test Article  ",  # Has whitespace
                    "Teaser": "\nTeaser text\n",
                    "Direct_Answer": "Answer",
                    "Intro": "Intro",
                    "Meta_Title": "Meta",
                    "Meta_Description": "Desc",
                }

                article = stage._parse_and_validate(json_data)

                # Whitespace should be stripped
                assert article.Headline == "Test Article"
                assert article.Teaser == "Teaser text"

    def test_parse_and_validate_with_none_values(self):
        """Test handling of None values."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.GeminiClient.__init__", return_value=None):
                stage = ExtractionStage()

                json_data = {
                    "Headline": "Test",
                    "Subtitle": None,  # None value
                    "Teaser": "Teaser",
                    "Direct_Answer": "Answer",
                    "Intro": "Intro",
                    "Meta_Title": "Meta",
                    "Meta_Description": "Desc",
                    "section_01_title": None,  # None value
                }

                article = stage._parse_and_validate(json_data)

                # None should become empty string
                assert article.Subtitle == ""
                assert article.section_01_title == ""

    def test_parse_and_validate_with_non_string_values(self):
        """Test handling of non-string values."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.GeminiClient.__init__", return_value=None):
                stage = ExtractionStage()

                json_data = {
                    "Headline": "Test",
                    "Teaser": 123,  # Integer!
                    "Direct_Answer": True,  # Boolean!
                    "Intro": ["list", "value"],  # List!
                    "Meta_Title": "Meta",
                    "Meta_Description": "Desc",
                }

                article = stage._parse_and_validate(json_data)

                # Non-strings should be converted
                assert article.Teaser == "123"
                assert article.Direct_Answer == "True"
                assert "[" in article.Intro  # String representation of list

    def test_recover_partial_data_missing_headline(self):
        """Test recovery when Headline is missing."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.GeminiClient.__init__", return_value=None):
                stage = ExtractionStage()

                json_data = {
                    "Headline": "",  # Empty
                    "Teaser": "Teaser",
                    "Direct_Answer": "Answer",
                    "Intro": "Intro",
                    "Meta_Title": "Meta",
                    "Meta_Description": "Desc",
                }

                # This should trigger recovery
                article = stage._recover_partial_data(json_data)

                # Should have recovered with default
                assert article.Headline == "Untitled Article"

    def test_recover_partial_data_field_mapping(self):
        """Test field name mapping during recovery."""
        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.GeminiClient.__init__", return_value=None):
                stage = ExtractionStage()

                json_data = {
                    "headline": "Article",  # lowercase variant
                    "Teaser": "Teaser",
                    "Direct_Answer": "Answer",
                    "Intro": "Intro",
                    "Meta Title": "Meta",  # Space variant
                    "Meta_Description": "Desc",
                }

                article = stage._recover_partial_data(json_data)

                # Should have mapped variants
                assert article.Headline == "Article"
                assert article.Meta_Title == "Meta"

    @pytest.mark.asyncio
    async def test_execute_with_plain_json_no_codeblock(self):
        """Test execution with JSON not in code block."""
        context = ExecutionContext(
            job_id="test",
            job_config={},
            company_data={},
            language="en",
            prompt="test",
            raw_article="""Some text before
            {"Headline": "Article", "Teaser": "Teaser", "Direct_Answer": "Answer", "Intro": "Intro", "Meta_Title": "Meta", "Meta_Description": "Desc"}
            Some text after""",
        )

        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.GeminiClient.__init__", return_value=None):
                stage = ExtractionStage()
                result = await stage.execute(context)

                assert result.structured_data is not None
                assert result.structured_data.Headline == "Article"

    @pytest.mark.asyncio
    async def test_execute_invalid_json(self):
        """Test execution fails with invalid JSON."""
        context = ExecutionContext(
            job_id="test",
            job_config={},
            company_data={},
            language="en",
            prompt="test",
            raw_article="No JSON here at all, just plain text",
        )

        with patch.dict("os.environ", {"GOOGLE_GEMINI_API_KEY": "test-key"}):
            with patch("src.models.gemini_client.GeminiClient.__init__", return_value=None):
                with patch("src.models.gemini_client.GeminiClient.extract_json_from_response") as mock_extract:
                    mock_extract.side_effect = ValueError("No JSON found")
                    stage = ExtractionStage()

                    with pytest.raises(ValueError, match="Failed to extract JSON"):
                        await stage.execute(context)


class TestArticleOutputCompleteness:
    """Test completeness metrics."""

    def test_completeness_minimal(self):
        """Test article with minimal content."""
        article = ArticleOutput(
            Headline="Title",
            Teaser="Teaser",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="Meta",
            Meta_Description="Desc",
        )
        assert article.get_active_sections() == 0
        assert article.get_active_faqs() == 0
        assert article.get_active_paas() == 0
        assert article.get_active_takeaways() == 0

    def test_completeness_full(self):
        """Test article with full content."""
        article = ArticleOutput(
            Headline="Title",
            Teaser="Teaser",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="Meta",
            Meta_Description="Desc",
            section_01_title="S1",
            section_01_content="C1",
            section_02_title="S2",
            section_02_content="C2",
            section_03_title="S3",
            section_03_content="C3",
            section_04_title="S4",
            section_04_content="C4",
            section_05_title="S5",
            section_05_content="C5",
            section_06_title="S6",
            section_06_content="C6",
            section_07_title="S7",
            section_07_content="C7",
            section_08_title="S8",
            section_08_content="C8",
            section_09_title="S9",
            section_09_content="C9",
            key_takeaway_01="T1",
            key_takeaway_02="T2",
            key_takeaway_03="T3",
            faq_01_question="Q1",
            faq_01_answer="A1",
            faq_02_question="Q2",
            faq_02_answer="A2",
            faq_03_question="Q3",
            faq_03_answer="A3",
            faq_04_question="Q4",
            faq_04_answer="A4",
            faq_05_question="Q5",
            faq_05_answer="A5",
            faq_06_question="Q6",
            faq_06_answer="A6",
            paa_01_question="P1",
            paa_01_answer="PA1",
            paa_02_question="P2",
            paa_02_answer="PA2",
            paa_03_question="P3",
            paa_03_answer="PA3",
            paa_04_question="P4",
            paa_04_answer="PA4",
        )
        assert article.get_active_sections() == 9
        assert article.get_active_faqs() == 6
        assert article.get_active_paas() == 4
        assert article.get_active_takeaways() == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
