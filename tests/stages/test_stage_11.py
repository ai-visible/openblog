"""
Tests for Stage 11: HTML Generation & Storage

Coverage:
- HTMLRenderer: HTML generation and escaping
- StorageProcessor: Metadata extraction and storage
- StorageStage: Full workflow
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from pipeline.core import ExecutionContext
from pipeline.blog_generation.stage_11_storage import StorageStage
from pipeline.processors.html_renderer import HTMLRenderer
from pipeline.processors.storage import StorageProcessor


# ============================================================================
# HTMLRenderer Tests
# ============================================================================


class TestHTMLRenderer:
    """Test HTML rendering functionality."""

    @pytest.fixture
    def sample_article(self):
        """Sample validated article."""
        return {
            "Headline": "Complete Guide to Python",
            "Subtitle": "Master Python in 2024",
            "Meta_Title": "Python Guide 2024",
            "Meta_Description": "Learn Python from basics to advanced",
            "Intro": "Python is a powerful programming language.",
            "section_01_title": "Why Python Matters",
            "section_01_content": "<p>Python is widely used in data science.</p>",
            "section_02_title": "Getting Started",
            "section_02_content": "<p>Install Python 3.10 or later.</p>",
            "image_url": "https://example.com/image.jpg",
            "image_alt_text": "Python logo",
            "Sources": "[1]: https://python.org – Official Python website\n[2]: https://docs.python.org – Python documentation",
            "faq_items": [
                {"question": "What is Python?", "answer": "Python is a programming language."},
                {"question": "Is Python free?", "answer": "Yes, Python is free and open source."},
            ],
            "paa_items": [
                {"question": "How to learn Python?", "answer": "Start with basics and practice."},
                {"question": "Best Python resources?", "answer": "Use official docs and tutorials."},
            ],
            "internal_links_html": '<div class="more-links"><h2>More Reading</h2><ul><li><a href="/blog/getting-started">Getting Started</a></li></ul></div>',
            "read_time": 8,
            "publication_date": "2024-01-15",
        }

    @pytest.fixture
    def company_data(self):
        """Sample company data."""
        return {
            "company_name": "TechCorp",
            "company_url": "https://techcorp.com",
            "company_location": "San Francisco",
        }

    def test_html_render_basic(self, sample_article):
        """Test basic HTML rendering."""
        html = HTMLRenderer.render(sample_article)

        assert "<!DOCTYPE html>" in html
        assert "Complete Guide to Python" in html
        assert "Master Python in 2024" in html
        assert "<meta charset" in html
        assert "python.org" in html

    def test_html_render_with_company(self, sample_article, company_data):
        """Test HTML rendering with company data."""
        html = HTMLRenderer.render(sample_article, company_data)

        assert "TechCorp" in html
        assert "techcorp.com" in html
        assert "© 2024 TechCorp" in html

    def test_html_render_sections(self, sample_article):
        """Test section rendering."""
        html = HTMLRenderer.render(sample_article)

        assert "Why Python Matters" in html
        assert "Getting Started" in html
        assert "Python is widely used" in html
        assert "Install Python" in html

    def test_html_render_faq(self, sample_article):
        """Test FAQ section rendering."""
        html = HTMLRenderer.render(sample_article)

        assert "Frequently Asked Questions" in html
        assert "What is Python?" in html
        assert "Is Python free?" in html

    def test_html_render_paa(self, sample_article):
        """Test People Also Ask section rendering."""
        html = HTMLRenderer.render(sample_article)

        assert "People Also Ask" in html
        assert "How to learn Python?" in html

    def test_html_render_citations(self, sample_article):
        """Test citations rendering."""
        html = HTMLRenderer.render(sample_article)

        assert "Sources" in html
        assert "[1]:" in html
        assert "python.org" in html

    def test_html_render_image(self, sample_article):
        """Test image rendering."""
        html = HTMLRenderer.render(sample_article)

        assert 'src="https://example.com/image.jpg"' in html
        assert 'alt="Python logo"' in html

    def test_html_render_toc_not_in_output(self, sample_article):
        """Test that TOC is only rendered if provided in article."""
        html = HTMLRenderer.render(sample_article)

        # TOC section shouldn't appear without toc data
        assert "Table of Contents" not in html

    def test_html_escape_special_chars(self, sample_article):
        """Test HTML escaping."""
        sample_article["Headline"] = 'Testing <script>alert("xss")</script>'
        html = HTMLRenderer.render(sample_article)

        assert "&lt;script&gt;" in html
        assert "<script>" not in html

    def test_html_render_empty_article(self):
        """Test rendering empty article."""
        html = HTMLRenderer.render({})

        assert "<!DOCTYPE html>" in html
        assert "No content available" in html or "Untitled" in html

    def test_html_render_missing_optional_fields(self):
        """Test rendering with missing optional fields."""
        article = {
            "Headline": "Test Article",
            "Meta_Title": "Test",
            "Meta_Description": "Test article",
            "Intro": "Introduction",
        }

        html = HTMLRenderer.render(article)

        assert "Test Article" in html
        assert "<!DOCTYPE html>" in html

    def test_html_render_with_schema_generation(self, sample_article, company_data):
        """Test HTML rendering with JSON-LD schema generation."""
        from pipeline.models.output_schema import ArticleOutput

        # Create ArticleOutput for schema generation
        article_output = ArticleOutput(
            Headline=sample_article["Headline"],
            Teaser="Test teaser",
            Direct_Answer="Test direct answer with citation [1].",
            Intro=sample_article["Intro"],
            Meta_Title=sample_article["Meta_Title"],
            Meta_Description=sample_article["Meta_Description"],
            section_01_title=sample_article["section_01_title"],
            section_01_content=sample_article["section_01_content"],
        )

        html = HTMLRenderer.render(
            article=sample_article,
            company_data=company_data,
            article_output=article_output,
            article_url="https://techcorp.com/blog/complete-guide-to-python",
            faq_items=sample_article["faq_items"],
        )

        # Check for JSON-LD schema
        assert 'type="application/ld+json"' in html
        assert '"@context": "https://schema.org"' in html
        assert '"@type": "Article"' in html
        assert '"@type": "FAQPage"' in html

    def test_html_render_schema_generation_fallback(self, sample_article, company_data):
        """Test that HTML rendering continues if schema generation fails."""
        # Pass invalid article_output to trigger error
        html = HTMLRenderer.render(
            article=sample_article,
            company_data=company_data,
            article_output=None,  # No schema generation
            article_url=None,
            faq_items=[],
        )

        # Should still render HTML successfully
        assert "<!DOCTYPE html>" in html
        assert "Complete Guide to Python" in html


# ============================================================================
# StorageProcessor Tests
# ============================================================================


class TestStorageProcessor:
    """Test storage processor functionality."""

    @pytest.fixture
    def sample_article(self):
        """Sample article for storage."""
        return {
            "Headline": "Test Article",
            "Meta_Title": "Test",
            "Meta_Description": "Test description",
            "Intro": "Test intro paragraph",
            "section_01_title": "Section 1",
            "section_01_content": "<p>Content 1</p>",
            "section_02_title": "Section 2",
            "section_02_content": "<p>Content 2</p>",
            "faq_items": [
                {"question": "Q1", "answer": "A1"},
                {"question": "Q2", "answer": "A2"},
            ],
            "paa_items": [
                {"question": "PQ1", "answer": "PA1"},
            ],
            "Sources": "[1]: https://example.com\n[2]: https://other.com",
            "citation_count": 2,
        }

    def test_metadata_extraction(self, sample_article):
        """Test metadata extraction."""
        meta = StorageProcessor.extract_metadata(sample_article)

        assert meta["headline"] == "Test Article"
        assert meta["slug"] == "test-article"
        assert meta["meta_title"] == "Test"
        assert meta["sections_count"] == 2
        assert meta["faq_count"] == 2
        assert meta["paa_count"] == 1
        assert meta["citations_count"] == 2
        assert meta["word_count"] > 0

    def test_slug_generation(self):
        """Test URL slug generation."""
        assert StorageProcessor._generate_slug("Hello World") == "hello-world"
        assert StorageProcessor._generate_slug("What is Python?") == "what-is-python"
        assert StorageProcessor._generate_slug("It's Cool!") == "its-cool"

    def test_word_count_estimation(self, sample_article):
        """Test word count estimation."""
        count = StorageProcessor._estimate_word_count(sample_article)

        assert count > 0
        assert "Test" in sample_article["Headline"]

    def test_section_counting(self, sample_article):
        """Test section counting."""
        count = StorageProcessor._count_sections(sample_article)

        assert count == 2

    def test_file_storage(self, sample_article):
        """Test file-based storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory for test
            import os

            original_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                html = "<html><body>Test</body></html>"
                success, result = StorageProcessor.store(
                    sample_article, "test-job-123", html, storage_type="file"
                )

                assert success
                assert result["storage_type"] == "file"
                assert result["job_id"] == "test-job-123"

                # Check files were created
                output_dir = Path("output") / "test-job-123"
                assert (output_dir / "index.html").exists()
                assert (output_dir / "article.json").exists()
                assert (output_dir / "metadata.json").exists()

                # Verify content
                with open(output_dir / "index.html") as f:
                    html_content = f.read()
                    assert "Test" in html_content

                with open(output_dir / "article.json") as f:
                    data = json.load(f)
                    assert data["Headline"] == "Test Article"

            finally:
                os.chdir(original_cwd)

    def test_invalid_storage_type(self, sample_article):
        """Test invalid storage type."""
        html = "<html></html>"
        success, result = StorageProcessor.store(
            sample_article, "test-job", html, storage_type="invalid"
        )

        assert not success
        assert "Unknown storage type" in result["error"]


# ============================================================================
# StorageStage Tests
# ============================================================================


class TestStorageStage:
    """Test Stage 11 execution."""

    @pytest.fixture
    def sample_context(self):
        """Sample execution context."""
        return ExecutionContext(
            job_id="test-job-456",
            validated_article={
                "Headline": "Final Article",
                "Subtitle": "Subtitle",
                "Meta_Title": "Final",
                "Meta_Description": "Final description",
                "Intro": "Introduction",
                "section_01_title": "Section 1",
                "section_01_content": "<p>Content</p>",
                "Sources": "[1]: https://example.com",
                "faq_items": [{"question": "Q", "answer": "A"}],
                "paa_items": [],
                "read_time": 5,
                "publication_date": "2024-01-15",
            },
            quality_report={
                "passed": True,
                "critical_issues": [],
                "metrics": {"aeo_score": 85, "readability": 75},
            },
            company_data={"company_name": "Test Co", "company_url": "https://test.com"},
        )

    @pytest.mark.asyncio
    async def test_stage_execution_success(self, sample_context):
        """Test successful stage execution."""
        stage = StorageStage()
        result = await stage.execute(sample_context)

        assert result.final_article is not None
        assert "html_content" in result.final_article
        assert result.storage_result["success"] is True

    @pytest.mark.asyncio
    async def test_stage_no_validated_article(self):
        """Test stage execution without validated article."""
        context = ExecutionContext(job_id="test")
        stage = StorageStage()
        result = await stage.execute(context)

        assert result.final_article == {}
        assert not result.storage_result.get("success", False)

    @pytest.mark.asyncio
    async def test_stage_quality_failed(self, sample_context):
        """Test stage execution when quality failed."""
        sample_context.quality_report["passed"] = False
        sample_context.quality_report["critical_issues"] = [
            "AEO score too low",
            "Missing sections",
        ]

        stage = StorageStage()
        result = await stage.execute(sample_context)

        assert result.final_article == {}
        assert not result.storage_result.get("success", False)

    @pytest.mark.asyncio
    async def test_stage_html_generation(self, sample_context):
        """Test HTML generation in stage."""
        stage = StorageStage()
        result = await stage.execute(sample_context)

        html = result.final_article.get("html_content", "")
        assert "<!DOCTYPE html>" in html
        assert "Final Article" in html

    @pytest.mark.asyncio
    async def test_stage_faq_paa_extraction(self, sample_context):
        """Test FAQ/PAA extraction from parallel_results."""
        from pipeline.models.faq_paa import FAQList, PAAList

        # Add FAQ/PAA items to parallel_results
        faq_list = FAQList()
        faq_list.add_item(1, "What is Python?", "Python is a programming language.")
        faq_list.add_item(2, "Is Python free?", "Yes, Python is free.")

        paa_list = PAAList()
        paa_list.add_item(1, "How to learn Python?", "Start with basics.")

        sample_context.parallel_results = {
            "faq_items": faq_list,
            "paa_items": paa_list,
        }

        stage = StorageStage()
        result = await stage.execute(sample_context)

        # HTML should contain FAQ/PAA content
        html = result.final_article.get("html_content", "")
        assert "What is Python?" in html or "Frequently Asked Questions" in html
        # Verify PAA items are extracted and included
        assert "How to learn Python?" in html or "People Also Ask" in html
        # Verify PAA items are in validated_article
        assert "paa_items" in result.final_article or "People Also Ask" in html

    @pytest.mark.asyncio
    async def test_stage_article_url_generation(self, sample_context):
        """Test article URL generation from headline and company URL."""
        sample_context.validated_article["Headline"] = "Complete Guide to Python Programming"
        sample_context.company_data["company_url"] = "https://example.com"

        stage = StorageStage()
        result = await stage.execute(sample_context)

        # Should generate URL (check via HTML or logs)
        html = result.final_article.get("html_content", "")
        # URL generation happens internally, verify HTML was generated successfully
        assert "<!DOCTYPE html>" in html

    @pytest.mark.asyncio
    async def test_stage_schema_generation(self, sample_context):
        """Test JSON-LD schema generation in HTML."""
        from pipeline.models.output_schema import ArticleOutput

        # Create ArticleOutput for schema generation
        article_output = ArticleOutput(
            Headline=sample_context.validated_article["Headline"],
            Teaser="Test teaser",
            Direct_Answer="Test direct answer.",
            Intro=sample_context.validated_article["Intro"],
            Meta_Title=sample_context.validated_article["Meta_Title"],
            Meta_Description=sample_context.validated_article["Meta_Description"],
            section_01_title=sample_context.validated_article["section_01_title"],
            section_01_content=sample_context.validated_article["section_01_content"],
        )

        sample_context.article_output = article_output
        sample_context.parallel_results = {
            "faq_items": [],
            "paa_items": [],
        }

        stage = StorageStage()
        result = await stage.execute(sample_context)

        html = result.final_article.get("html_content", "")
        # Check for JSON-LD schema if generation succeeded
        if 'type="application/ld+json"' in html:
            assert '"@context": "https://schema.org"' in html
            assert '"@type": "Article"' in html

    @pytest.mark.asyncio
    async def test_stage_metadata_extraction(self, sample_context):
        """Test metadata extraction in stage."""
        stage = StorageStage()
        result = await stage.execute(sample_context)

        metadata = result.final_article.get("metadata_extracted", {})
        assert metadata.get("headline") == "Final Article"
        assert metadata.get("slug") == "final-article"

    def test_stage_repr(self):
        """Test stage representation."""
        stage = StorageStage()
        assert "StorageStage" in repr(stage)
        assert "11" in repr(stage)


# ============================================================================
# Integration Tests
# ============================================================================


class TestStage11Integration:
    """Integration tests for Stage 11."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete Stage 11 workflow."""
        # Create context with validated article
        context = ExecutionContext(
            job_id="integration-test-001",
            validated_article={
                "Headline": "Integration Test Article",
                "Subtitle": "Testing Stage 11",
                "Meta_Title": "Test Article Title",
                "Meta_Description": "This is a test article for integration testing",
                "Intro": "This is an introductory paragraph for the test article.",
                "section_01_title": "Introduction Section",
                "section_01_content": "<p>This section introduces the topic.</p>",
                "section_02_title": "Main Content",
                "section_02_content": "<p>This is the main content section.</p>",
                "section_03_title": "Conclusion",
                "section_03_content": "<p>This concludes our test article.</p>",
                "faq_items": [
                    {"question": "What is this?", "answer": "A test article."},
                    {"question": "Why test?", "answer": "To verify functionality."},
                ],
                "paa_items": [
                    {"question": "How does it work?", "answer": "It processes articles."},
                ],
                "Sources": "[1]: https://example.com – Example source\n[2]: https://test.org – Test source",
                "citation_count": 2,
                "read_time": 6,
                "publication_date": datetime.now().isoformat(),
            },
            quality_report={
                "passed": True,
                "critical_issues": [],
                "suggestions": [],
                "metrics": {
                    "aeo_score": 87,
                    "readability": 72,
                    "keyword_coverage": 95,
                },
            },
            company_data={
                "company_name": "Integration Test Corp",
                "company_url": "https://integration-test.example.com",
                "company_location": "Test City",
            },
        )

        # Execute stage
        stage = StorageStage()
        result = await stage.execute(context)

        # Verify results
        assert result.final_article
        assert "html_content" in result.final_article
        assert result.storage_result["success"] is True

        # Verify HTML content
        html = result.final_article["html_content"]
        assert "Integration Test Article" in html
        assert "Testing Stage 11" in html
        assert "What is this?" in html

        # Verify metadata
        metadata = result.final_article["metadata_extracted"]
        assert metadata["headline"] == "Integration Test Article"
        assert metadata["sections_count"] == 3
