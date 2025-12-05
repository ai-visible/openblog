"""
Tests for Stage 7: Metadata

Tests:
- ArticleMetadata model
- MetadataCalculator (read time, date generation)
- Word counting (plain text and HTML)
- Stage execution
"""

import pytest
from datetime import datetime, timedelta
from pipeline.core import ExecutionContext
from pipeline.models.metadata import ArticleMetadata, MetadataCalculator
from pipeline.models.output_schema import ArticleOutput
from pipeline.blog_generation.stage_07_metadata import MetadataStage


@pytest.fixture
def valid_context():
    """Create valid ExecutionContext for Stage 7."""
    article = ArticleOutput(
        Headline="Advanced Python Guide",
        Teaser="Learn Python programming deeply and efficiently.",
        Direct_Answer="Python is a versatile programming language used for web development, data science, and automation.",
        Intro="This comprehensive guide covers advanced Python concepts for experienced developers.",
        Meta_Title="Advanced Python Programming",
        Meta_Description="Master advanced Python techniques.",
        section_01_title="Getting Started",
        section_01_content="<p>Python is easy to learn. It has a simple syntax. You can start coding quickly.</p><p>The language supports multiple programming paradigms.</p>",
        section_02_title="Advanced Topics",
        section_02_content="<p>Decorators are powerful tools. They modify functions. They enable aspect-oriented programming.</p><p>Context managers provide resource management. They ensure cleanup happens automatically.</p>",
        section_03_title="Best Practices",
        section_03_content="<p>Write clean code always. Follow PEP 8 guidelines. Use meaningful variable names.</p>",
    )

    return ExecutionContext(
        job_id="test-job-123",
        job_config={"primary_keyword": "python"},
        company_data={"company_name": "Tech Co"},
        language="en",
        prompt="Test prompt",
        raw_article="Test article",
        structured_data=article,
    )


class TestArticleMetadata:
    """Test ArticleMetadata model."""

    def test_metadata_creation(self):
        """Test creating metadata."""
        metadata = ArticleMetadata(
            read_time=5,
            publication_date="15.11.2025",
            word_count=1000,
        )
        assert metadata.read_time == 5
        assert metadata.publication_date == "15.11.2025"
        assert metadata.word_count == 1000

    def test_metadata_defaults(self):
        """Test metadata defaults."""
        metadata = ArticleMetadata()
        assert metadata.read_time == 5
        assert metadata.word_count == 0

    def test_read_time_validation_min(self):
        """Test read time minimum validation."""
        # Should not raise, but enforced by Pydantic
        with pytest.raises(ValueError):
            ArticleMetadata(read_time=0)

    def test_read_time_validation_max(self):
        """Test read time maximum validation."""
        with pytest.raises(ValueError):
            ArticleMetadata(read_time=31)

    def test_metadata_repr(self):
        """Test string representation."""
        metadata = ArticleMetadata(
            read_time=8,
            publication_date="20.11.2025",
            word_count=1500,
        )
        repr_str = repr(metadata)
        assert "ArticleMetadata" in repr_str
        assert "8" in repr_str


class TestMetadataCalculator:
    """Test MetadataCalculator utility."""

    def test_calculate_read_time_basic(self):
        """Test basic read time calculation."""
        # 200 words = 1 minute
        assert MetadataCalculator.calculate_read_time(200) == 1
        # 400 words = 2 minutes
        assert MetadataCalculator.calculate_read_time(400) == 2
        # 1000 words = 5 minutes
        assert MetadataCalculator.calculate_read_time(1000) == 5

    def test_calculate_read_time_rounding(self):
        """Test read time rounding."""
        # 300 words = 1.5 → rounds to 2
        assert MetadataCalculator.calculate_read_time(300) == 2
        # 250 words = 1.25 → rounds to 1
        assert MetadataCalculator.calculate_read_time(250) == 1

    def test_calculate_read_time_minimum(self):
        """Test read time minimum."""
        # Even 1 word should be 1 minute
        assert MetadataCalculator.calculate_read_time(1) == 1
        # Zero words should be 1 minute
        assert MetadataCalculator.calculate_read_time(0) == 1

    def test_calculate_read_time_maximum(self):
        """Test read time maximum."""
        # 10000 words should cap at 30 minutes
        assert MetadataCalculator.calculate_read_time(10000) == 30

    def test_generate_publication_date_format(self):
        """Test publication date format."""
        date_str = MetadataCalculator.generate_publication_date()
        # Should match DD.MM.YYYY format
        parts = date_str.split(".")
        assert len(parts) == 3
        assert len(parts[0]) == 2  # Day
        assert len(parts[1]) == 2  # Month
        assert len(parts[2]) == 4  # Year

    def test_generate_publication_date_range(self):
        """Test publication date is within range."""
        today = datetime.now()
        for _ in range(10):  # Test multiple times
            date_str = MetadataCalculator.generate_publication_date(days_back=90)
            # Parse date
            parts = date_str.split(".")
            date_obj = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            # Check it's not in future
            assert date_obj <= today
            # Check it's within 90 days
            days_diff = (today - date_obj).days
            assert 0 <= days_diff <= 90

    def test_generate_publication_date_custom_range(self):
        """Test publication date with custom range."""
        today = datetime.now()
        date_str = MetadataCalculator.generate_publication_date(days_back=30)
        parts = date_str.split(".")
        date_obj = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        days_diff = (today - date_obj).days
        assert days_diff <= 30

    def test_count_words_plain_text(self):
        """Test word counting on plain text."""
        assert MetadataCalculator.count_words("hello world") == 2
        assert MetadataCalculator.count_words("one two three four five") == 5
        assert MetadataCalculator.count_words("") == 0
        assert MetadataCalculator.count_words("single") == 1

    def test_count_words_with_whitespace(self):
        """Test word counting with extra whitespace."""
        assert MetadataCalculator.count_words("hello  world") == 2
        assert MetadataCalculator.count_words("  hello  ") == 1

    def test_count_words_html(self):
        """Test word counting in HTML content."""
        html = "<p>Hello world</p>"
        assert MetadataCalculator.count_words_from_html(html) == 2

        html = "<p>One</p><p>Two Three</p>"
        assert MetadataCalculator.count_words_from_html(html) == 3

    def test_count_words_html_complex(self):
        """Test word counting with complex HTML."""
        html = "<div><p>Hello <strong>world</strong></p></div>"
        assert MetadataCalculator.count_words_from_html(html) == 2

        html = "<p>First sentence.</p><p>Second sentence here.</p>"
        assert MetadataCalculator.count_words_from_html(html) == 5


class TestMetadataStage:
    """Test Stage 7: Metadata."""

    @pytest.mark.asyncio
    async def test_execute_success(self, valid_context):
        """Test successful Stage 7 execution."""
        stage = MetadataStage()
        result = await stage.execute(valid_context)

        assert "metadata" in result.parallel_results
        assert result.parallel_results["metadata"] is not None

        metadata = result.parallel_results["metadata"]
        assert metadata.read_time > 0
        assert metadata.publication_date != ""
        assert metadata.word_count > 0

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

        stage = MetadataStage()
        result = await stage.execute(context)

        metadata = result.parallel_results["metadata"]
        assert isinstance(metadata, ArticleMetadata)

    def test_count_article_words(self, valid_context):
        """Test word counting from article."""
        stage = MetadataStage()
        word_count = stage._count_article_words(valid_context.structured_data)

        # Should count all sections
        assert word_count > 0
        # Verify it's reasonable (roughly 50+ words minimum from our fixture)
        assert word_count > 50

    def test_count_article_words_empty_sections(self):
        """Test word counting with empty sections."""
        article = ArticleOutput(
            Headline="Title",
            Teaser="Teaser",
            Direct_Answer="Answer",
            Intro="Introduction",
            Meta_Title="Meta",
            Meta_Description="Desc",
            section_01_title="Section 1",
            section_01_content="<p>Content</p>",
            # Other sections empty
        )

        stage = MetadataStage()
        word_count = stage._count_article_words(article)

        # Should count headline + teaser + answer + intro + section 1
        assert word_count > 0

    @pytest.mark.asyncio
    async def test_execute_stores_metadata(self, valid_context):
        """Test that execution stores all metadata fields."""
        stage = MetadataStage()
        result = await stage.execute(valid_context)

        assert "metadata" in result.parallel_results
        assert "word_count" in result.parallel_results
        assert "read_time" in result.parallel_results
        assert "publication_date" in result.parallel_results

    @pytest.mark.asyncio
    async def test_execute_read_time_reasonable(self, valid_context):
        """Test that calculated read time is reasonable."""
        stage = MetadataStage()
        result = await stage.execute(valid_context)

        read_time = result.parallel_results["read_time"]
        word_count = result.parallel_results["word_count"]

        # Verify relationship: read_time should be roughly word_count / 200
        expected_read_time = max(1, round(word_count / 200))
        assert read_time == expected_read_time

    @pytest.mark.asyncio
    async def test_execute_date_format(self, valid_context):
        """Test that publication date is properly formatted."""
        stage = MetadataStage()
        result = await stage.execute(valid_context)

        date_str = result.parallel_results["publication_date"]

        # Check format DD.MM.YYYY
        parts = date_str.split(".")
        assert len(parts) == 3
        assert len(parts[0]) == 2
        assert len(parts[1]) == 2
        assert len(parts[2]) == 4


class TestMetadataIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, valid_context):
        """Test complete metadata workflow."""
        stage = MetadataStage()
        result = await stage.execute(valid_context)

        # Verify all fields populated
        metadata = result.parallel_results["metadata"]
        assert metadata.word_count > 0
        assert 1 <= metadata.read_time <= 30
        assert metadata.publication_date

        # Verify consistency
        expected_read_time = max(1, min(30, round(metadata.word_count / 200)))
        assert metadata.read_time == expected_read_time

    def test_metadata_calculation_workflow(self):
        """Test metadata calculation workflow."""
        # Create article content
        article = ArticleOutput(
            Headline="Test Article",
            Teaser="Hook text",
            Direct_Answer="Answer text",
            Intro="Introduction paragraph",
            Meta_Title="Meta",
            Meta_Description="Desc",
            section_01_content="<p>Section one content with multiple words</p>",
            section_02_content="<p>Section two content</p>",
        )

        # Count words
        stage = MetadataStage()
        word_count = stage._count_article_words(article)
        assert word_count > 0

        # Calculate read time
        read_time = MetadataCalculator.calculate_read_time(word_count)
        assert 1 <= read_time <= 30

        # Generate date
        pub_date = MetadataCalculator.generate_publication_date()
        assert pub_date

        # Create metadata
        metadata = ArticleMetadata(
            word_count=word_count,
            read_time=read_time,
            publication_date=pub_date,
        )

        assert metadata.word_count == word_count
        assert metadata.read_time == read_time
        assert metadata.publication_date == pub_date


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
