"""
Tests for Stage 5: Internal Links

Tests:
- InternalLink model
- InternalLinkList collection and operations
- Topic extraction
- Link suggestion generation
- Filtering and deduplication
- HTML formatting
- Stage execution
"""

import pytest
from pipeline.core import ExecutionContext
from pipeline.models.internal_link import InternalLink, InternalLinkList
from pipeline.models.output_schema import ArticleOutput
from pipeline.blog_generation.stage_05_internal_links import InternalLinksStage


@pytest.fixture
def valid_context():
    """Create valid ExecutionContext for Stage 5."""
    article = ArticleOutput(
        Headline="Getting Started with Python",
        Teaser="Python is popular.",
        Direct_Answer="Learn Python basics.",
        Intro="Introduction to Python.",
        Meta_Title="Python Guide",
        Meta_Description="Learn Python.",
        section_01_title="Installation Guide",
        section_01_content="<p>Install Python</p>",
        section_02_title="Basic Concepts",
        section_02_content="<p>Learn basics</p>",
        section_03_title="Best Practices",
        section_03_content="<p>Follow best practices</p>",
    )

    return ExecutionContext(
        job_id="test-job-123",
        job_config={"primary_keyword": "python"},
        company_data={"company_name": "Tech Co", "company_competitors": ["RivalCorp"]},
        language="en",
        prompt="Test prompt",
        raw_article="Test article",
        structured_data=article,
    )


class TestInternalLinkModel:
    """Test InternalLink model."""

    def test_valid_link_creation(self):
        """Test creating valid link."""
        link = InternalLink(url="/blog/python-basics", title="Python Basics Guide")
        assert link.url == "/blog/python-basics"
        assert link.title == "Python Basics Guide"
        assert link.relevance == 5  # Default

    def test_link_with_relevance(self):
        """Test link with custom relevance."""
        link = InternalLink(
            url="/blog/python",
            title="Python Guide",
            relevance=9,
        )
        assert link.relevance == 9

    def test_link_validity(self):
        """Test link validity check."""
        valid_link = InternalLink(url="/blog/test", title="Test", status=200)
        invalid_link = InternalLink(url="/blog/test", title="Test", status=404)

        assert valid_link.is_valid() is True
        assert invalid_link.is_valid() is False

    def test_link_to_html(self):
        """Test HTML output."""
        link = InternalLink(url="/blog/python", title="Python Guide")
        html = link.to_html()

        assert "<li>" in html
        assert "</li>" in html
        assert "<a href=" in html
        assert "/blog/python" in html
        assert "Python Guide" in html

    def test_link_repr(self):
        """Test string representation."""
        link = InternalLink(url="/blog/python", title="Python Guide", relevance=8)
        repr_str = repr(link)

        assert "InternalLink" in repr_str
        assert "/blog/python" in repr_str


class TestInternalLinkList:
    """Test InternalLinkList collection."""

    def test_list_creation(self):
        """Test creating link list."""
        link_list = InternalLinkList()
        assert link_list.count() == 0

    def test_add_link(self):
        """Test adding links."""
        link_list = InternalLinkList()
        link_list.add_link("/blog/python", "Python Guide")
        link_list.add_link("/blog/javascript", "JavaScript Tips")

        assert link_list.count() == 2
        assert "/blog/python" in link_list.get_urls()
        assert "/blog/javascript" in link_list.get_urls()

    def test_filter_valid(self):
        """Test filtering valid links."""
        link_list = InternalLinkList()
        link_list.add_link("/blog/python", "Python", status=200)
        link_list.add_link("/blog/dead", "Dead Link", status=404)
        link_list.add_link("/blog/java", "Java", status=200)

        filtered = link_list.filter_valid()
        assert filtered.count() == 2
        assert "/blog/python" in filtered.get_urls()
        assert "/blog/java" in filtered.get_urls()

    def test_sort_by_relevance(self):
        """Test sorting by relevance."""
        link_list = InternalLinkList()
        link_list.add_link("/blog/python", "Python", relevance=5)
        link_list.add_link("/blog/javascript", "JavaScript", relevance=9)
        link_list.add_link("/blog/java", "Java", relevance=7)

        sorted_list = link_list.sort_by_relevance()
        urls = sorted_list.get_urls()

        assert urls[0] == "/blog/javascript"  # 9
        assert urls[1] == "/blog/java"  # 7
        assert urls[2] == "/blog/python"  # 5

    def test_deduplicate_domains(self):
        """Test deduplicating by domain."""
        link_list = InternalLinkList()
        link_list.add_link("/blog/python", "Python", domain="/blog/")
        link_list.add_link("/blog/python-advanced", "Advanced", domain="/blog/")
        link_list.add_link("/docs/python", "Docs", domain="/docs/")

        deduped = link_list.deduplicate_domains()
        assert deduped.count() == 2  # Only one /blog/, plus /docs/

    def test_limit(self):
        """Test limiting link count."""
        link_list = InternalLinkList()
        for i in range(15):
            link_list.add_link(f"/blog/topic-{i}", f"Topic {i}")

        limited = link_list.limit(5)
        assert limited.count() == 5

    def test_to_html(self):
        """Test HTML output."""
        link_list = InternalLinkList()
        link_list.add_link("/blog/python", "Python Guide")
        link_list.add_link("/blog/javascript", "JavaScript Tips")

        html = link_list.to_html()

        assert '<div class="more-links">' in html
        assert "<h3>More on this topic</h3>" in html
        assert "<ul>" in html
        assert "</ul>" in html
        assert "<li>" in html
        assert "/blog/python" in html
        assert "/blog/javascript" in html

    def test_to_html_empty(self):
        """Test HTML output for empty list."""
        link_list = InternalLinkList()
        html = link_list.to_html()
        assert html == ""

    def test_custom_section_title(self):
        """Test custom section title."""
        link_list = InternalLinkList(section_title="Related Reading")
        link_list.add_link("/blog/test", "Test")

        html = link_list.to_html()
        assert "Related Reading" in html

    def test_chaining_operations(self):
        """Test chaining operations."""
        link_list = InternalLinkList()
        link_list.add_link("/blog/python", "Python", relevance=5, status=200, domain="/blog/")
        link_list.add_link("/blog/python-tips", "Tips", relevance=8, status=200, domain="/blog/")
        link_list.add_link("/blog/dead", "Dead", relevance=3, status=404, domain="/blog/")

        result = (
            link_list.filter_valid()
            .sort_by_relevance()
            .deduplicate_domains()
            .limit(5)
        )

        assert result.count() == 1  # Only one /blog/ domain after dedup
        assert result.links[0].url == "/blog/python-tips"  # Higher relevance


class TestInternalLinksStage:
    """Test Stage 5: Internal Links."""

    @pytest.mark.asyncio
    async def test_execute_success(self, valid_context):
        """Test successful Stage 5 execution."""
        stage = InternalLinksStage()
        result = await stage.execute(valid_context)

        assert "internal_links_html" in result.parallel_results
        assert len(result.parallel_results["internal_links_html"]) > 0
        assert "More on this topic" in result.parallel_results["internal_links_html"]

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

        stage = InternalLinksStage()
        result = await stage.execute(context)

        assert result.parallel_results["internal_links_html"] == ""

    def test_extract_topics(self, valid_context):
        """Test topic extraction from article."""
        stage = InternalLinksStage()
        topics = stage._extract_topics(valid_context.structured_data)

        assert len(topics) > 0
        assert "Getting Started with Python" in topics
        assert "Installation Guide" in topics
        assert "Basic Concepts" in topics

    def test_extract_topics_filters_empty(self):
        """Test that empty sections are filtered."""
        article = ArticleOutput(
            Headline="Test Article",
            Teaser="Hook",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="Meta",
            Meta_Description="Desc",
            section_01_title="Section 1",
            section_02_title="",  # Empty
            section_03_title="Section 3",
        )

        stage = InternalLinksStage()
        topics = stage._extract_topics(article)

        assert "Section 1" in topics
        assert "Section 3" in topics
        assert len([t for t in topics if t == ""]) == 0

    def test_generate_suggestions(self, valid_context):
        """Test suggestion generation."""
        stage = InternalLinksStage()
        topics = ["Python Basics", "Advanced Concepts"]

        link_list = stage._generate_suggestions(topics, valid_context)

        assert link_list.count() > 0
        assert all(link.status == 200 for link in link_list.links)

    def test_generate_suggestions_filters_competitors(self, valid_context):
        """Test that competitor names are filtered."""
        stage = InternalLinksStage()
        topics = ["Python Basics", "RivalCorp Integration"]  # RivalCorp is competitor

        link_list = stage._generate_suggestions(topics, valid_context)

        # Check that we skipped the competitor topic
        urls = link_list.get_urls()
        assert not any("rivalcorp" in url.lower() for url in urls)

    @pytest.mark.asyncio
    async def test_execute_filters_and_deduplicates(self, valid_context):
        """Test that execution filters and deduplicates links."""
        stage = InternalLinksStage()
        result = await stage.execute(valid_context)

        link_list = result.parallel_results.get("internal_links_list")
        if link_list and link_list.count() > 0:
            # Check that all remaining links are valid
            assert all(link.is_valid() for link in link_list.links)
            # Check reasonable number of links
            assert link_list.count() <= 10

    @pytest.mark.asyncio
    async def test_execute_stores_metadata(self, valid_context):
        """Test that execution stores metadata."""
        stage = InternalLinksStage()
        result = await stage.execute(valid_context)

        assert "internal_links_html" in result.parallel_results
        assert "internal_links_count" in result.parallel_results
        assert "internal_links_list" in result.parallel_results


class TestInternalLinksIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, valid_context):
        """Test complete workflow."""
        stage = InternalLinksStage()
        result = await stage.execute(valid_context)

        # Check HTML output
        html = result.parallel_results["internal_links_html"]
        assert html  # Not empty
        assert '<div class="more-links">' in html
        assert "<ul>" in html
        assert "<li>" in html

        # Check count
        count = result.parallel_results["internal_links_count"]
        assert count > 0
        assert count <= 10

        # Check link list
        link_list = result.parallel_results["internal_links_list"]
        assert link_list.count() == count

    def test_link_list_workflow(self):
        """Test typical link list workflow."""
        # Create link list
        link_list = InternalLinkList()

        # Add various links
        link_list.add_link("/blog/python", "Python Basics", relevance=8, status=200, domain="/blog/")
        link_list.add_link("/blog/python-advanced", "Advanced", relevance=9, status=200, domain="/blog/")
        link_list.add_link("/docs/python", "Docs", relevance=7, status=200, domain="/docs/")
        link_list.add_link("/tutorial/python", "Tutorial", relevance=6, status=404, domain="/tutorial/")
        link_list.add_link("/guides/javascript", "JavaScript", relevance=5, status=200, domain="/guides/")

        # Process
        result = (
            link_list.filter_valid()
            .sort_by_relevance()
            .deduplicate_domains()
            .limit(5)
        )

        # Verify
        assert result.count() == 3  # 3 different domains
        assert result.links[0].url == "/blog/python-advanced"  # Highest relevance
        assert result.to_html()  # Can generate HTML


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
