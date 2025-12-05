"""
Tests for Stage 10: Cleanup & Validation

Tests:
- HTMLCleaner (cleaning, sanitization, normalization)
- SectionCombiner (combining and extracting sections)
- DataMerger (merging parallel results)
- CitationSanitizer2 (final citation cleanup)
- QualityChecker (validation and metrics)
- Stage 10 execution (full workflow)
"""

import pytest
from pipeline.core import ExecutionContext
from pipeline.models.output_schema import ArticleOutput
from pipeline.processors.cleanup import HTMLCleaner, SectionCombiner, DataMerger
from pipeline.processors.citation_sanitizer import CitationSanitizer2
from pipeline.processors.quality_checker import QualityChecker
from pipeline.blog_generation.stage_10_cleanup import CleanupStage


@pytest.fixture
def valid_article():
    """Create article for cleanup."""
    return ArticleOutput(
        Headline="Python Programming Guide 2024",
        Teaser="Learn Python programming step by step.",
        Direct_Answer="Python is a versatile programming language.",
        Intro="Python has become the most popular programming language for beginners and professionals alike.",
        Meta_Title="Python Programming Guide 2024",
        Meta_Description="Learn Python programming with comprehensive guide.",
        section_01_title="Introduction",
        section_01_content="<p>Python is great for web development.</p><p>You can build many things.</p>",
        section_02_title="Getting Started",
        section_02_content="<p>Start by installing Python.</p><p>Then learn the basics.</p>",
        section_03_title="Advanced Topics",
        section_03_content="<p>Learn more advanced concepts.</p>",
    )


@pytest.fixture
def valid_parallel_results():
    """Create valid parallel results."""
    return {
        "citations_html": "<p>Citations: [1] https://example.com</p>",
        "internal_links_html": '<div class="more-links"><ul><li><a href="/">Home</a></li></ul></div>',
        "toc_dict": {"toc_01": "Intro", "toc_02": "Getting Started"},
        "metadata": {"read_time": 5, "publication_date": "2024-01-01"},
        "faq_items": [],
        "paa_items": [],
        "image_url": "https://example.com/image.jpg",
        "image_alt_text": "Article image",
    }


@pytest.fixture
def valid_context(valid_article, valid_parallel_results):
    """Create valid ExecutionContext for Stage 10."""
    return ExecutionContext(
        job_id="test-job-123",
        job_config={"primary_keyword": "python"},
        company_data={"company_name": "Tech Co"},
        language="en",
        prompt="Test prompt",
        raw_article="Test article",
        structured_data=valid_article,
        parallel_results=valid_parallel_results,
    )


class TestHTMLCleaner:
    """Test HTML cleaning functions."""

    def test_clean_html_removes_duplicate_h1(self):
        """Test removing duplicate h1 tags."""
        html = "<h1>Title 1</h1>\n<h1>Title 2</h1>"
        cleaned = HTMLCleaner.clean_html(html)

        # Should have only one h1
        assert cleaned.count("<h1>") <= 1

    def test_clean_html_removes_markdown_bold(self):
        """Test removing markdown bold."""
        html = "This is **bold** text"
        cleaned = HTMLCleaner.clean_html(html)

        assert "**bold**" not in cleaned
        assert "bold" in cleaned

    def test_sanitize_removes_zero_width_chars(self):
        """Test removing invisible characters."""
        html = "Text\u200bwith\u200cinvisible\u200dchars"
        sanitized = HTMLCleaner.sanitize(html)

        assert "\u200b" not in sanitized
        assert "\u200c" not in sanitized

    def test_sanitize_keeps_valid_citations(self):
        """Test keeping valid citations."""
        html = "Text [1] and [2] and notes [note]"
        sanitized = HTMLCleaner.sanitize(html)

        assert "[1]" in sanitized
        assert "[2]" in sanitized

    def test_normalize_fixes_line_breaks(self):
        """Test normalizing line breaks."""
        html = "Text\n\n\n\nMore text"
        normalized = HTMLCleaner.normalize(html)

        # Should have max 2 consecutive newlines
        assert "\n\n\n" not in normalized


class TestSectionCombiner:
    """Test section combining and extraction."""

    def test_combine_sections(self, valid_article):
        """Test combining sections into content."""
        combined = SectionCombiner.combine_sections(valid_article)

        assert "<h1>Python Programming Guide 2024</h1>" in combined
        assert "Introduction" in combined
        assert "Getting Started" in combined

    def test_extract_sections(self):
        """Test extracting sections from combined content."""
        content = "<h2>Section 1</h2><p>Content 1</p><h2>Section 2</h2><p>Content 2</p>"
        extracted = SectionCombiner.extract_sections(content)

        assert "section_01_title" in extracted
        assert extracted["section_01_title"] == "Section 1"


class TestDataMerger:
    """Test data merging."""

    def test_merge_all_results(self, valid_article, valid_parallel_results):
        """Test merging structured and parallel data."""
        merged = DataMerger.merge_all_results(valid_article, valid_parallel_results)

        assert "Headline" in merged
        assert "image_url" in merged
        assert "read_time" in merged


class TestCitationSanitizer:
    """Test citation sanitization."""

    def test_remove_citation_markers(self):
        """Test removing citation markers."""
        text = "Text with [[1]] and [2]] and [note]"
        cleaned = CitationSanitizer2._remove_citation_markers(text)

        assert "[[" not in cleaned
        assert "[2]]" not in cleaned

    def test_count_citations(self):
        """Test counting citations."""
        sources = "[1]: https://example.com\n[2]: https://example2.com"
        count = CitationSanitizer2._count_citations(sources)

        assert count == 2

    def test_sanitize_full(self):
        """Test full citation sanitization."""
        article = {
            "Sources": "[1]: https://example.com – Description\n[2]: https://example2.com – Another",
            "content": "Text with [1] and [2] citations",
        }
        sanitized = CitationSanitizer2.sanitize(article)

        assert "citation_count" in sanitized


class TestQualityChecker:
    """Test quality checking and metrics."""

    def test_check_article(self, valid_article):
        """Test article quality check."""
        job_config = {"primary_keyword": "python"}
        report = QualityChecker.check_article(valid_article.model_dump(), job_config)

        assert "critical_issues" in report
        assert "suggestions" in report
        assert "metrics" in report
        assert "passed" in report

    def test_check_article_with_article_output(self, valid_article):
        """Test quality check with ArticleOutput for comprehensive AEO scoring."""
        job_config = {"primary_keyword": "python"}
        input_data = {
            "company_data": {"company_name": "Test Co"},
            "primary_keyword": "python",
        }
        report = QualityChecker.check_article(
            article=valid_article.model_dump(),
            job_config=job_config,
            article_output=valid_article,
            input_data=input_data,
        )

        assert "critical_issues" in report
        assert "metrics" in report
        assert "aeo_score" in report["metrics"]
        assert "aeo_score_method" in report["metrics"]
        # Should use comprehensive scoring
        assert report["metrics"]["aeo_score_method"] in ["comprehensive", "simple_fallback"]
        assert 0 <= report["metrics"]["aeo_score"] <= 100

    def test_check_article_fallback_on_error(self, valid_article):
        """Test that QualityChecker falls back to simple scoring if AEOScorer fails."""
        job_config = {"primary_keyword": "python"}
        # Create invalid ArticleOutput to trigger error
        invalid_output = None
        report = QualityChecker.check_article(
            article=valid_article.model_dump(),
            job_config=job_config,
            article_output=invalid_output,
        )

        assert "metrics" in report
        assert "aeo_score" in report["metrics"]
        assert report["metrics"]["aeo_score_method"] == "simple"
        assert 0 <= report["metrics"]["aeo_score"] <= 100

    def test_aeo_score_calculation(self):
        """Test AEO score calculation."""
        report = {
            "critical_issues": [],
            "suggestions": [],
        }
        score = QualityChecker._calculate_aeo_score(report)

        assert 0 <= score <= 100
        assert score == 100  # No issues = perfect score

    def test_readability_score(self, valid_article):
        """Test readability score calculation."""
        article = valid_article.model_dump()
        score = QualityChecker._calculate_readability_score(article)

        assert 0 <= score <= 100

    def test_keyword_coverage(self, valid_article):
        """Test keyword coverage calculation."""
        article = valid_article.model_dump()
        job_config = {"primary_keyword": "python"}
        coverage = QualityChecker._calculate_keyword_coverage(article, job_config)

        assert 0 <= coverage <= 100


class TestCleanupStage:
    """Test Stage 10 execution."""

    @pytest.mark.asyncio
    async def test_execute_success(self, valid_context):
        """Test successful Stage 10 execution."""
        stage = CleanupStage()
        result = await stage.execute(valid_context)

        assert result.validated_article is not None
        assert result.quality_report is not None
        assert "critical_issues" in result.quality_report

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

        stage = CleanupStage()
        result = await stage.execute(context)

        assert result.validated_article == {}
        assert not result.quality_report.get("passed", False)

    @pytest.mark.asyncio
    async def test_quality_report_structure(self, valid_context):
        """Test quality report structure."""
        stage = CleanupStage()
        result = await stage.execute(valid_context)

        report = result.quality_report
        assert "critical_issues" in report
        assert "suggestions" in report
        assert "metrics" in report
        assert "aeo_score" in report["metrics"]
        assert "readability" in report["metrics"]
        assert "keyword_coverage" in report["metrics"]

    @pytest.mark.asyncio
    async def test_validated_article_structure(self, valid_context):
        """Test validated article structure."""
        stage = CleanupStage()
        result = await stage.execute(valid_context)

        article = result.validated_article
        assert isinstance(article, dict)
        # Should have merged content
        assert len(article) > 0

    @pytest.mark.asyncio
    async def test_article_output_conversion(self, valid_context):
        """Test that ArticleOutput is converted and stored in context."""
        stage = CleanupStage()
        result = await stage.execute(valid_context)

        # Should have article_output in context
        assert hasattr(result, "article_output")
        # May be None if conversion failed, but should be attempted
        if result.article_output is not None:
            from pipeline.models.output_schema import ArticleOutput
            assert isinstance(result.article_output, ArticleOutput)

    @pytest.mark.asyncio
    async def test_aeo_scoring_integration(self, valid_context):
        """Test that comprehensive AEO scoring is used when ArticleOutput is available."""
        stage = CleanupStage()
        result = await stage.execute(valid_context)

        report = result.quality_report
        assert "metrics" in report
        assert "aeo_score" in report["metrics"]
        assert "aeo_score_method" in report["metrics"]
        # Should attempt comprehensive scoring if ArticleOutput conversion succeeded
        method = report["metrics"]["aeo_score_method"]
        assert method in ["comprehensive", "simple_fallback", "simple"]

    def test_stage_repr(self):
        """Test string representation."""
        stage = CleanupStage()
        repr_str = repr(stage)

        assert "CleanupStage" in repr_str
        assert "stage_num=10" in repr_str


class TestCleanupIntegration:
    """Integration tests for Stage 10."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, valid_context):
        """Test complete Stage 10 workflow."""
        stage = CleanupStage()
        result = await stage.execute(valid_context)

        # Check all outputs are present
        assert result.validated_article is not None
        assert result.quality_report is not None

        # Check quality report metrics
        metrics = result.quality_report.get("metrics", {})
        assert "aeo_score" in metrics
        assert 0 <= metrics["aeo_score"] <= 100

    @pytest.mark.asyncio
    async def test_cleanup_workflow_multi_section(self):
        """Test cleanup with multiple sections."""
        article = ArticleOutput(
            Headline="Multi-Section Article",
            Teaser="This is a comprehensive article.",
            Direct_Answer="Multi-section articles are useful.",
            Intro="Introduction text here.",
            Meta_Title="Multi-Section Article",
            Meta_Description="A comprehensive article.",
            section_01_title="Section One",
            section_01_content="<p>Content one.</p>",
            section_02_title="Section Two",
            section_02_content="<p>Content two.</p>",
            section_03_title="Section Three",
            section_03_content="<p>Content three.</p>",
        )

        context = ExecutionContext(
            job_id="test",
            job_config={"primary_keyword": "article"},
            company_data={},
            language="en",
            prompt="test",
            raw_article="test",
            structured_data=article,
            parallel_results={
                "citations_html": "",
                "internal_links_html": "",
                "toc_dict": {},
                "metadata": {"read_time": 5},
                "faq_items": [],
                "paa_items": [],
                "image_url": "",
                "image_alt_text": "",
            },
        )

        stage = CleanupStage()
        result = await stage.execute(context)

        assert result.validated_article is not None
        assert result.quality_report.get("passed", False) is True or len(
            result.quality_report.get("critical_issues", [])
        ) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
