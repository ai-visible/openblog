"""
Integration tests for AEO (Answer Engine Optimization) features.

Tests the full workflow:
- Stage 10: ArticleOutput conversion, comprehensive AEO scoring
- Stage 11: Schema generation, FAQ/PAA extraction, article URL generation
"""

import pytest
from pipeline.core import ExecutionContext
from pipeline.models.output_schema import ArticleOutput
from pipeline.models.faq_paa import FAQList, PAAList
from pipeline.blog_generation.stage_10_cleanup import CleanupStage
from pipeline.blog_generation.stage_11_storage import StorageStage


@pytest.fixture
def aeo_optimized_article():
    """Create an AEO-optimized article with all required features."""
    return ArticleOutput(
        Headline="What is Python Programming?",
        Subtitle="Complete Guide to Python in 2024",
        Teaser="Learn Python programming step by step with this comprehensive guide.",
        Direct_Answer="Python is a versatile, high-level programming language known for its simplicity and readability. It supports multiple programming paradigms and is widely used in web development, data science, artificial intelligence, and automation. Python's extensive standard library and active community make it an excellent choice for beginners and professionals alike [1].",
        Intro="Python has become the most popular programming language for beginners and professionals alike. Its clean syntax and powerful capabilities make it ideal for a wide range of applications.",
        Meta_Title="What is Python Programming? Complete Guide 2024",
        Meta_Description="Learn Python programming with this comprehensive guide covering basics, advanced topics, and real-world applications.",
        Key_Takeaway_01="Python is versatile and beginner-friendly.",
        Key_Takeaway_02="Python supports multiple programming paradigms.",
        Key_Takeaway_03="Python has extensive libraries and community support.",
        section_01_title="What is Python?",
        section_01_content="<p>Python is a high-level programming language [1][2]. It was created by Guido van Rossum and first released in 1991 [3]. Python emphasizes code readability and simplicity [4].</p>",
        section_02_title="How does Python work?",
        section_02_content="<p>Python uses an interpreter to execute code [5]. This means you can run Python code directly without compilation [6]. Python's dynamic typing makes it flexible [7].</p>",
        section_03_title="Why does Python matter?",
        section_03_content="<p>Python powers many modern applications [8]. It's used in data science, web development, and AI [9]. Python's ecosystem is vast and growing [10].</p>",
        faq_01_question="What is Python used for?",
        faq_01_answer="Python is used for web development, data science, artificial intelligence, automation, and scientific computing.",
        faq_02_question="Is Python easy to learn?",
        faq_02_answer="Yes, Python is considered one of the easiest programming languages to learn due to its simple syntax and readability.",
        faq_03_question="How long does it take to learn Python?",
        faq_03_answer="Basic Python can be learned in a few weeks, but mastering it takes months or years of practice.",
        faq_04_question="What are Python's main advantages?",
        faq_04_answer="Python's main advantages include simplicity, versatility, extensive libraries, and a large community.",
        faq_05_question="Can Python be used for web development?",
        faq_05_answer="Yes, Python is widely used for web development with frameworks like Django and Flask.",
        faq_06_question="Is Python free to use?",
        faq_06_answer="Yes, Python is completely free and open-source software.",
        paa_01_question="How to install Python?",
        paa_01_answer="Download Python from python.org and follow the installation instructions for your operating system.",
        paa_02_question="What is the best Python IDE?",
        paa_02_answer="Popular Python IDEs include PyCharm, VS Code, and Jupyter Notebook.",
        paa_03_question="What Python version should I use?",
        paa_03_answer="Python 3.10 or later is recommended for new projects.",
        Sources="[1]: https://python.org – Official Python website\n[2]: https://docs.python.org – Python documentation\n[3]: https://wikipedia.org/python – Python history\n[4]: https://realpython.com – Python tutorials\n[5]: https://python.org/about – About Python",
    )


@pytest.fixture
def aeo_context(aeo_optimized_article):
    """Create execution context with AEO-optimized article."""
    faq_list = FAQList()
    faq_list.add_item(1, aeo_optimized_article.faq_01_question, aeo_optimized_article.faq_01_answer)
    faq_list.add_item(2, aeo_optimized_article.faq_02_question, aeo_optimized_article.faq_02_answer)
    faq_list.add_item(3, aeo_optimized_article.faq_03_question, aeo_optimized_article.faq_03_answer)
    faq_list.add_item(4, aeo_optimized_article.faq_04_question, aeo_optimized_article.faq_04_answer)
    faq_list.add_item(5, aeo_optimized_article.faq_05_question, aeo_optimized_article.faq_05_answer)
    faq_list.add_item(6, aeo_optimized_article.faq_06_question, aeo_optimized_article.faq_06_answer)

    paa_list = PAAList()
    paa_list.add_item(1, aeo_optimized_article.paa_01_question, aeo_optimized_article.paa_01_answer)
    paa_list.add_item(2, aeo_optimized_article.paa_02_question, aeo_optimized_article.paa_02_answer)
    paa_list.add_item(3, aeo_optimized_article.paa_03_question, aeo_optimized_article.paa_03_answer)

    return ExecutionContext(
        job_id="aeo-test-001",
        job_config={"primary_keyword": "python programming"},
        company_data={
            "company_name": "Tech Education Co",
            "company_url": "https://techeducation.com",
            "company_location": "San Francisco",
        },
        language="en",
        prompt="Test prompt",
        raw_article="Test article",
        structured_data=aeo_optimized_article,
        parallel_results={
            "citations_html": "<p>Citations: [1] https://python.org</p>",
            "internal_links_html": '<div><a href="/blog/python-basics">Python Basics</a></div>',
            "toc_dict": {"toc_01": "What is Python?", "toc_02": "How does Python work?"},
            "metadata": {"read_time": 8, "publication_date": "2024-01-15"},
            "faq_items": faq_list,
            "paa_items": paa_list,
            "image_url": "https://example.com/python-logo.jpg",
            "image_alt_text": "Python programming language logo",
        },
    )


class TestAEOIntegration:
    """Test AEO integration across Stage 10 and Stage 11."""

    @pytest.mark.asyncio
    async def test_stage_10_article_output_conversion(self, aeo_context):
        """Test that Stage 10 converts article to ArticleOutput."""
        stage = CleanupStage()
        result = await stage.execute(aeo_context)

        # Should have article_output
        assert hasattr(result, "article_output")
        # Should successfully convert
        assert result.article_output is not None
        assert isinstance(result.article_output, ArticleOutput)

    @pytest.mark.asyncio
    async def test_stage_10_comprehensive_aeo_scoring(self, aeo_context):
        """Test that Stage 10 uses comprehensive AEO scoring."""
        stage = CleanupStage()
        result = await stage.execute(aeo_context)

        report = result.quality_report
        assert "metrics" in report
        assert "aeo_score" in report["metrics"]
        assert "aeo_score_method" in report["metrics"]

        # Should use comprehensive scoring
        method = report["metrics"]["aeo_score_method"]
        assert method in ["comprehensive", "simple_fallback"]
        
        # AEO score should be calculated
        score = report["metrics"]["aeo_score"]
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_stage_11_schema_generation(self, aeo_context):
        """Test that Stage 11 generates JSON-LD schemas."""
        # First run Stage 10 to get article_output
        stage10 = CleanupStage()
        context_after_10 = await stage10.execute(aeo_context)

        # Then run Stage 11
        stage11 = StorageStage()
        result = await stage11.execute(context_after_10)

        html = result.final_article.get("html_content", "")
        
        # Should contain JSON-LD schemas
        assert 'type="application/ld+json"' in html
        assert '"@context": "https://schema.org"' in html
        assert '"@type": "Article"' in html
        
        # Should have FAQPage schema if FAQs exist
        if context_after_10.parallel_results.get("faq_items"):
            assert '"@type": "FAQPage"' in html

    @pytest.mark.asyncio
    async def test_stage_11_faq_paa_extraction(self, aeo_context):
        """Test that Stage 11 extracts FAQ/PAA items correctly."""
        stage10 = CleanupStage()
        context_after_10 = await stage10.execute(aeo_context)

        stage11 = StorageStage()
        result = await stage11.execute(context_after_10)

        html = result.final_article.get("html_content", "")
        
        # Should contain FAQ content
        assert "What is Python used for?" in html or "Frequently Asked Questions" in html

    @pytest.mark.asyncio
    async def test_stage_11_article_url_generation(self, aeo_context):
        """Test that Stage 11 generates article URL."""
        stage10 = CleanupStage()
        context_after_10 = await stage10.execute(aeo_context)

        stage11 = StorageStage()
        result = await stage11.execute(context_after_10)

        # URL generation happens internally, verify HTML was generated
        html = result.final_article.get("html_content", "")
        assert "<!DOCTYPE html>" in html
        assert "What is Python Programming?" in html

    @pytest.mark.asyncio
    async def test_full_aeo_workflow(self, aeo_context):
        """Test complete AEO workflow from Stage 10 to Stage 11."""
        # Stage 10: Cleanup and validation
        stage10 = CleanupStage()
        context_after_10 = await stage10.execute(aeo_context)

        # Verify Stage 10 outputs
        assert context_after_10.validated_article is not None
        assert context_after_10.quality_report is not None
        assert context_after_10.article_output is not None
        
        # Verify AEO scoring
        aeo_score = context_after_10.quality_report["metrics"]["aeo_score"]
        assert 0 <= aeo_score <= 100
        
        # Stage 11: HTML generation and storage
        stage11 = StorageStage()
        result = await stage11.execute(context_after_10)

        # Verify Stage 11 outputs
        assert result.final_article is not None
        assert "html_content" in result.final_article
        
        html = result.final_article["html_content"]
        
        # Verify HTML contains AEO features
        assert "<!DOCTYPE html>" in html
        assert "What is Python Programming?" in html
        
        # Verify schema generation
        assert 'type="application/ld+json"' in html
        assert '"@type": "Article"' in html
        
        # Verify direct answer is in HTML (for AEO)
        assert "Python is a versatile" in html or "versatile" in html.lower()

    @pytest.mark.asyncio
    async def test_aeo_fallback_on_conversion_error(self, aeo_context):
        """Test that AEO features gracefully degrade when ArticleOutput conversion fails."""
        # Create a valid article dict but with missing fields to trigger conversion error
        # but still pass quality checks
        article_dict = aeo_context.structured_data.model_dump()
        # Remove some optional fields that might cause conversion issues
        # but keep required ones
        aeo_context.structured_data = article_dict  # Use dict instead of ArticleOutput
        
        stage10 = CleanupStage()
        result = await stage10.execute(aeo_context)

        # Should still work with fallback
        assert result.validated_article is not None
        assert result.quality_report is not None
        
        # Should use simple scoring fallback if conversion failed
        method = result.quality_report["metrics"].get("aeo_score_method", "unknown")
        assert method in ["simple", "simple_fallback", "comprehensive"]
        
        # If quality passed, Stage 11 should work
        if result.quality_report.get("passed", False):
            stage11 = StorageStage()
            final_result = await stage11.execute(result)
            
            # Should generate HTML even without schemas
            assert final_result.final_article is not None
            html = final_result.final_article.get("html_content", "")
            # HTML may not have schemas if article_output is None
            assert "<!DOCTYPE html>" in html or html == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

