"""
Tests for Stage 4: Citations

Tests:
- Citation model (URL validation, title length)
- CitationList collection
- Source parsing (various formats)
- HTML formatting
- Stage execution and output
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pipeline.core import ExecutionContext
from pipeline.models.citation import Citation, CitationList
from pipeline.models.output_schema import ArticleOutput
from pipeline.blog_generation.stage_04_citations import CitationsStage
from pipeline.config import Config


@pytest.fixture
def valid_context():
    """Create valid ExecutionContext for Stage 4."""
    article = ArticleOutput(
        Headline="Test Article",
        Teaser="Hook",
        Direct_Answer="Answer",
        Intro="Intro",
        Meta_Title="Meta",
        Meta_Description="Desc",
        Sources="[1]: https://example.com – Test source\n[2]: https://example.org – Another source",
    )

    return ExecutionContext(
        job_id="test-job-123",
        job_config={"primary_keyword": "test"},
        company_data={"company_name": "Test Co"},
        language="en",
        prompt="Test prompt",
        raw_article="Test article",
        structured_data=article,
    )


class TestCitationModel:
    """Test Citation model."""

    def test_valid_citation_creation(self):
        """Test creating valid citation."""
        citation = Citation(
            number=1,
            url="https://example.com",
            title="Example Source",
        )
        assert citation.number == 1
        assert citation.url == "https://example.com"
        assert citation.title == "Example Source"

    def test_citation_url_protocol_validation(self):
        """Test URL protocol validation."""
        # Without protocol - should add https://
        citation = Citation(
            number=1,
            url="example.com",
            title="Example",
        )
        assert citation.url == "https://example.com"

    def test_citation_to_html(self):
        """Test HTML output format."""
        citation = Citation(
            number=1,
            url="https://example.com",
            title="Example Source",
        )
        html = citation.to_html()
        assert "[1]:" in html
        assert "https://example.com" in html
        assert "Example Source" in html
        assert "<a href=" in html

    def test_citation_to_markdown(self):
        """Test Markdown output format."""
        citation = Citation(
            number=2,
            url="https://example.com",
            title="Example Source",
        )
        markdown = citation.to_markdown()
        assert "[2]:" in markdown
        assert "[Example Source]" in markdown
        assert "(https://example.com)" in markdown

    def test_citation_title_short_warning(self):
        """Test warning for very short title."""
        # Should not raise, just warn
        citation = Citation(
            number=1,
            url="https://example.com",
            title="Short",
        )
        assert citation.title == "Short"

    def test_citation_title_long_warning(self):
        """Test warning for very long title."""
        long_title = " ".join(["word"] * 30)
        # Should not raise, just warn
        citation = Citation(
            number=1,
            url="https://example.com",
            title=long_title,
        )
        assert len(citation.title.split()) > 25


class TestCitationList:
    """Test CitationList collection."""

    def test_citation_list_creation(self):
        """Test creating citation list."""
        citation_list = CitationList()
        assert citation_list.count() == 0

    def test_add_citation(self):
        """Test adding citations."""
        citation_list = CitationList()
        citation_list.add_citation("https://example.com", "Example")
        citation_list.add_citation("https://example.org", "Another")

        assert citation_list.count() == 2
        assert citation_list.citations[0].number == 1
        assert citation_list.citations[1].number == 2

    def test_to_html(self):
        """Test HTML output."""
        citation_list = CitationList()
        citation_list.add_citation("https://example.com", "Example")
        citation_list.add_citation("https://example.org", "Another")

        html = citation_list.to_html()
        assert "<div class=\"citations\">" in html
        assert "[1]:" in html
        assert "[2]:" in html
        assert "https://example.com" in html
        assert "https://example.org" in html

    def test_to_html_paragraph_list(self):
        """Test paragraph list HTML output."""
        citation_list = CitationList()
        citation_list.add_citation("https://example.com", "Example")

        html = citation_list.to_html_paragraph_list()
        assert "<p>" in html
        assert "[1]:" in html
        assert "</p>" in html

    def test_empty_list_html(self):
        """Test HTML output for empty list."""
        citation_list = CitationList()
        html = citation_list.to_html()
        assert html == ""

    def test_get_urls(self):
        """Test extracting URL list."""
        citation_list = CitationList()
        citation_list.add_citation("https://example.com", "Example")
        citation_list.add_citation("https://example.org", "Another")

        urls = citation_list.get_urls()
        assert len(urls) == 2
        assert "https://example.com" in urls
        assert "https://example.org" in urls

    def test_get_citation_by_number(self):
        """Test retrieving citation by number."""
        citation_list = CitationList()
        citation_list.add_citation("https://example.com", "Example")
        citation_list.add_citation("https://example.org", "Another")

        citation = citation_list.get_citation_by_number(2)
        assert citation is not None
        assert citation.url == "https://example.org"

    def test_get_citation_not_found(self):
        """Test retrieving non-existent citation."""
        citation_list = CitationList()
        citation_list.add_citation("https://example.com", "Example")

        citation = citation_list.get_citation_by_number(999)
        assert citation is None


class TestCitationsStage:
    """Test Stage 4: Citations."""

    @pytest.mark.asyncio
    async def test_execute_success(self, valid_context):
        """Test successful Stage 4 execution."""
        # Create config with validation disabled for faster tests
        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)
        result = await stage.execute(valid_context)

        assert "citations_html" in result.parallel_results
        assert len(result.parallel_results["citations_html"]) > 0
        assert "[1]:" in result.parallel_results["citations_html"]
        assert "[2]:" in result.parallel_results["citations_html"]

    @pytest.mark.asyncio
    async def test_execute_citations_disabled(self):
        """Test execution with citations disabled."""
        article = ArticleOutput(
            Headline="Test",
            Teaser="Hook",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="Meta",
            Meta_Description="Desc",
            Sources="[1]: https://example.com – Source",
        )

        context = ExecutionContext(
            job_id="test",
            job_config={"citations_disabled": True},
            company_data={},
            language="en",
            prompt="test",
            raw_article="test",
            structured_data=article,
        )

        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)
        result = await stage.execute(context)

        assert result.parallel_results["citations_html"] == ""

    @pytest.mark.asyncio
    async def test_execute_no_sources(self):
        """Test execution with no sources."""
        article = ArticleOutput(
            Headline="Test",
            Teaser="Hook",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="Meta",
            Meta_Description="Desc",
            Sources="",  # Empty
        )

        context = ExecutionContext(
            job_id="test",
            job_config={},
            company_data={},
            language="en",
            prompt="test",
            raw_article="test",
            structured_data=article,
        )

        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)
        result = await stage.execute(context)

        assert result.parallel_results["citations_html"] == ""

    def test_parse_sources_standard_format(self):
        """Test parsing standard format sources."""
        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)

        sources = """[1]: https://example.com – Description one
[2]: https://example.org – Description two
[3]: https://example.net – Description three"""

        citation_list = stage._parse_sources(sources)

        assert citation_list.count() == 3
        assert citation_list.citations[0].url == "https://example.com"
        assert citation_list.citations[0].title == "Description one"
        assert citation_list.citations[1].url == "https://example.org"
        assert citation_list.citations[2].url == "https://example.net"

    def test_parse_sources_with_dash_separator(self):
        """Test parsing with dash separator."""
        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)

        sources = "[1]: https://example.com - Description\n[2]: https://example.org - Another"

        citation_list = stage._parse_sources(sources)

        assert citation_list.count() == 2
        assert "Description" in citation_list.citations[0].title
        assert "Another" in citation_list.citations[1].title

    def test_parse_sources_empty_lines(self):
        """Test parsing with empty lines."""
        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)

        sources = """[1]: https://example.com – Description one

[2]: https://example.org – Description two

"""

        citation_list = stage._parse_sources(sources)

        assert citation_list.count() == 2

    def test_parse_sources_renumber(self):
        """Test that citations are renumbered sequentially."""
        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)

        sources = """[5]: https://example.com – Description
[10]: https://example.org – Another"""

        citation_list = stage._parse_sources(sources)

        # Should be renumbered to 1, 2
        assert citation_list.citations[0].number == 1
        assert citation_list.citations[1].number == 2

    def test_parse_sources_extract_url_only(self):
        """Test parsing when URL is embedded in text."""
        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)

        sources = "[1]: Check out https://example.com for more info"

        citation_list = stage._parse_sources(sources)

        assert citation_list.count() == 1
        assert citation_list.citations[0].url == "https://example.com"

    def test_parse_sources_invalid_format(self):
        """Test parsing invalid format (should skip)."""
        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)

        sources = """[1]: https://example.com – Valid citation
Just some random text without proper format
[2]: https://example.org – Another valid"""

        citation_list = stage._parse_sources(sources)

        # Should extract only valid ones
        assert citation_list.count() == 2

    @pytest.mark.asyncio
    async def test_execute_no_structured_data(self):
        """Test execution with no structured data."""
        context = ExecutionContext(
            job_id="test",
            job_config={},
            company_data={},
            language="en",
            prompt="test",
            raw_article="test",
            structured_data=None,
        )

        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)
        result = await stage.execute(context)

        assert result.parallel_results["citations_html"] == ""


class TestCitationsIntegration:
    """Integration tests for citations."""

    def test_parse_and_format_workflow(self):
        """Test complete parse and format workflow."""
        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)

        sources = """[1]: https://www.example.com – Example source with description
[2]: https://www.example.org – Another reference material
[3]: https://www.example.net – Third source"""

        citation_list = stage._parse_sources(sources)
        html = citation_list.to_html_paragraph_list()

        assert citation_list.count() == 3
        assert "[1]:" in html
        assert "[2]:" in html
        assert "[3]:" in html
        assert "Example source with description" in html
        assert "<a href=" in html
        assert "target=\"_blank\"" in html

    @pytest.mark.asyncio
    async def test_full_execution_workflow(self, valid_context):
        """Test complete execution workflow."""
        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)
        result = await stage.execute(valid_context)

        assert result.parallel_results["citations_html"]
        assert result.parallel_results["citations_count"] == 2
        assert result.parallel_results["citations_list"] is not None

        # Verify citations list
        citation_list = result.parallel_results["citations_list"]
        assert citation_list.count() == 2


class TestCitationURLValidation:
    """Test URL validation functionality."""

    @pytest.mark.asyncio
    async def test_validation_disabled_by_default_in_tests(self, valid_context):
        """Test that validation can be disabled."""
        config = Config()
        config.enable_citation_validation = False
        stage = CitationsStage(config=config)
        result = await stage.execute(valid_context)
        
        # Should still work without validation
        assert "citations_html" in result.parallel_results

    @pytest.mark.asyncio
    async def test_validation_skipped_without_company_url(self, valid_context):
        """Test that validation is skipped if no company_url."""
        config = Config()
        config.enable_citation_validation = True
        stage = CitationsStage(config=config)
        
        # Remove company_url - validation should skip without trying to init GeminiClient
        valid_context.company_data = {}
        result = await stage.execute(valid_context)
        
        # Should still work, just without validation
        assert "citations_html" in result.parallel_results

    @pytest.mark.asyncio
    @patch('pipeline.blog_generation.stage_04_citations.GeminiClient')
    @patch('pipeline.blog_generation.stage_04_citations.CitationURLValidator')
    async def test_validation_enabled_with_company_url(self, mock_validator_class, mock_gemini_class, valid_context):
        """Test that validation runs when enabled and company_url is present."""
        # Mock GeminiClient
        mock_gemini_instance = Mock()
        mock_gemini_class.return_value = mock_gemini_instance
        
        # Mock validator
        mock_validator = AsyncMock()
        mock_validator.validate_all_citations = AsyncMock(return_value=valid_context.structured_data.Sources)
        mock_validator_class.return_value = mock_validator
        
        config = Config()
        config.enable_citation_validation = True
        stage = CitationsStage(config=config)
        
        valid_context.company_data = {"company_url": "https://example.com"}
        result = await stage.execute(valid_context)
        
        # Validator should be called
        assert mock_validator.validate_all_citations.called or not config.enable_citation_validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
