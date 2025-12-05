"""
Tests for Stage 8: FAQ/PAA Validation

Tests:
- FAQItem and PAAItem models
- FAQList and PAAList collections
- FAQ/PAA extraction
- Validation and deduplication
- Stage execution
"""

import pytest
from pipeline.core import ExecutionContext
from pipeline.models.faq_paa import FAQItem, PAAItem, FAQList, PAAList
from pipeline.models.output_schema import ArticleOutput
from pipeline.blog_generation.stage_08_faq_paa import FAQPAAStage


@pytest.fixture
def valid_article():
    """Create article with FAQ/PAA items."""
    return ArticleOutput(
        Headline="Python Guide",
        Teaser="Learn Python.",
        Direct_Answer="Python is great.",
        Intro="Introduction.",
        Meta_Title="Python",
        Meta_Description="Guide",
        faq_01_question="What is Python?",
        faq_01_answer="Python is a programming language used for web development, data science, and automation.",
        faq_02_question="How do I learn Python?",
        faq_02_answer="Start with basics, practice coding, use online resources, and build projects.",
        faq_03_question="Is Python free?",
        faq_03_answer="Yes, Python is free and open-source software available for download.",
        faq_04_question="Can I use Python for web development?",
        faq_04_answer="Yes, Python has excellent frameworks like Django and Flask for web development.",
        faq_05_question="What are Python libraries?",
        faq_05_answer="Libraries are pre-written code collections that extend Python functionality.",
        paa_01_question="Should I learn Python?",
        paa_01_answer="Python is beginner-friendly and widely used in industry.",
        paa_02_question="How long to learn Python?",
        paa_02_answer="Basics take weeks, proficiency takes months of consistent practice.",
        paa_03_question="Python vs JavaScript which is better?",
        paa_03_answer="Both are useful; Python for data science, JavaScript for web.",
    )


@pytest.fixture
def valid_context(valid_article):
    """Create valid ExecutionContext for Stage 8."""
    return ExecutionContext(
        job_id="test-job-123",
        job_config={"primary_keyword": "python"},
        company_data={"company_name": "Tech Co"},
        language="en",
        prompt="Test prompt",
        raw_article="Test article",
        structured_data=valid_article,
    )


class TestFAQItem:
    """Test FAQItem model."""

    def test_faq_creation(self):
        """Test creating FAQ item."""
        item = FAQItem(
            number=1,
            question="What is Python?",
            answer="Python is a programming language.",
        )
        assert item.number == 1
        assert "Python" in item.question

    def test_faq_word_counts(self):
        """Test word count calculation."""
        item = FAQItem(
            number=1,
            question="What is Python programming language?",
            answer="Python is a widely used programming language for multiple purposes.",
        )
        assert item.word_count_question() == 5
        assert item.word_count_answer() == 10

    def test_faq_validation_valid(self):
        """Test validation of valid item."""
        item = FAQItem(
            number=1,
            question="What is Python?",
            answer="Python is a programming language used for web development, data science, and more.",
        )
        assert item.is_valid() is True

    def test_faq_validation_short_question(self):
        """Test validation fails with short question."""
        item = FAQItem(
            number=1,
            question="What?",
            answer="A programming language with adequate length for the answer here.",
        )
        assert item.is_valid() is False

    def test_faq_validation_short_answer(self):
        """Test validation fails with short answer."""
        item = FAQItem(
            number=1,
            question="What is Python?",
            answer="A language",
        )
        assert item.is_valid() is False

    def test_faq_repr(self):
        """Test string representation."""
        item = FAQItem(
            number=2,
            question="How do I learn Python?",
            answer="Study the basics and practice coding.",
        )
        repr_str = repr(item)
        assert "FAQItem" in repr_str
        assert "2" in repr_str


class TestPAAItem:
    """Test PAAItem model."""

    def test_paa_creation(self):
        """Test creating PAA item."""
        item = PAAItem(
            number=1,
            question="Should I learn Python?",
            answer="Python is beginner-friendly and widely used.",
        )
        assert item.number == 1
        assert "Python" in item.question

    def test_paa_word_counts(self):
        """Test word count calculation."""
        item = PAAItem(
            number=1,
            question="Should I learn Python?",
            answer="Python is beginner-friendly and widely used in industry.",
        )
        assert item.word_count_question() == 4
        assert item.word_count_answer() == 8

    def test_paa_validation_valid(self):
        """Test validation of valid item."""
        item = PAAItem(
            number=1,
            question="Should I learn Python?",
            answer="Python is beginner-friendly and widely used in industry today.",
        )
        assert item.is_valid() is True

    def test_paa_validation_short_question(self):
        """Test validation fails with short question."""
        item = PAAItem(
            number=1,
            question="Why?",
            answer="Because it is beginner friendly and widely used.",
        )
        assert item.is_valid() is False

    def test_paa_validation_short_answer(self):
        """Test validation fails with short answer."""
        item = PAAItem(
            number=1,
            question="Should I learn Python?",
            answer="Yes",
        )
        assert item.is_valid() is False


class TestFAQList:
    """Test FAQList collection."""

    def test_faq_list_creation(self):
        """Test creating FAQ list."""
        faq_list = FAQList()
        assert faq_list.count() == 0
        assert faq_list.min_items == 5

    def test_faq_list_add_items(self):
        """Test adding items."""
        faq_list = FAQList()
        faq_list.add_item(
            1,
            "What is Python?",
            "Python is a programming language used widely.",
        )
        faq_list.add_item(
            2,
            "How do I learn Python?",
            "Start with basics and practice coding regularly.",
        )

        assert faq_list.count() == 2

    def test_faq_list_minimum_met(self):
        """Test minimum requirement check."""
        faq_list = FAQList(min_items=5)
        for i in range(5):
            faq_list.add_item(
                i + 1,
                f"Question {i + 1} about programming?",
                f"Answer {i + 1} with sufficient content about the topic.",
            )

        assert faq_list.is_minimum_met() is True

    def test_faq_list_minimum_not_met(self):
        """Test minimum not met."""
        faq_list = FAQList(min_items=5)
        faq_list.add_item(1, "Question?", "Answer content here now.")

        assert faq_list.is_minimum_met() is False

    def test_faq_list_count_valid(self):
        """Test counting valid items."""
        faq_list = FAQList()
        faq_list.add_item(1, "What is Python?", "Valid answer with enough content about programming and its uses.")
        faq_list.add_item(2, "How to learn programming language?", "Short")  # Invalid

        assert faq_list.count() == 2
        assert faq_list.count_valid() == 1

    def test_faq_list_renumber(self):
        """Test renumbering items."""
        faq_list = FAQList()
        faq_list.add_item(1, "Question one?", "Answer content here and more.")
        faq_list.add_item(2, "Question two?", "Answer content here and more.")

        faq_list.renumber()

        assert faq_list.items[0].number == 1
        assert faq_list.items[1].number == 2

    def test_faq_list_to_dict_list(self):
        """Test conversion to dict list."""
        faq_list = FAQList()
        faq_list.add_item(1, "What is Python?", "Python is a language.")

        dict_list = faq_list.to_dict_list()

        assert len(dict_list) == 1
        assert dict_list[0]["number"] == 1
        assert "What" in dict_list[0]["question"]


class TestPAAList:
    """Test PAAList collection."""

    def test_paa_list_creation(self):
        """Test creating PAA list."""
        paa_list = PAAList()
        assert paa_list.count() == 0
        assert paa_list.min_items == 3

    def test_paa_list_minimum_met(self):
        """Test minimum requirement check."""
        paa_list = PAAList(min_items=3)
        for i in range(3):
            paa_list.add_item(
                i + 1,
                f"Question {i + 1} about topic?",
                f"Answer {i + 1} with adequate content.",
            )

        assert paa_list.is_minimum_met() is True

    def test_paa_list_renumber(self):
        """Test renumbering items."""
        paa_list = PAAList()
        paa_list.add_item(1, "Question one?", "Answer content here.")
        paa_list.add_item(2, "Question two?", "Answer content here.")

        paa_list.renumber()

        assert paa_list.items[0].number == 1
        assert paa_list.items[1].number == 2


class TestFAQPAAStage:
    """Test Stage 8: FAQ/PAA."""

    @pytest.mark.asyncio
    async def test_execute_success(self, valid_context):
        """Test successful Stage 8 execution."""
        stage = FAQPAAStage()
        result = await stage.execute(valid_context)

        assert "faq_items" in result.parallel_results
        assert "paa_items" in result.parallel_results

        faq_list = result.parallel_results["faq_items"]
        paa_list = result.parallel_results["paa_items"]

        assert faq_list.count() > 0
        assert paa_list.count() > 0

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

        stage = FAQPAAStage()
        result = await stage.execute(context)

        assert isinstance(result.parallel_results["faq_items"], FAQList)
        assert isinstance(result.parallel_results["paa_items"], PAAList)

    def test_extract_faq(self, valid_context):
        """Test FAQ extraction."""
        stage = FAQPAAStage()
        faq_list = stage._extract_faq(valid_context.structured_data)

        # Article has 5 FAQ items
        assert faq_list.count() == 5
        assert faq_list.items[0].question == "What is Python?"

    def test_extract_paa(self, valid_context):
        """Test PAA extraction."""
        stage = FAQPAAStage()
        paa_list = stage._extract_paa(valid_context.structured_data)

        # Article has 3 PAA items
        assert paa_list.count() == 3
        assert paa_list.items[0].question == "Should I learn Python?"

    def test_extract_faq_with_empty_fields(self):
        """Test extraction skips empty fields."""
        article = ArticleOutput(
            Headline="Test",
            Teaser="Hook",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="Meta",
            Meta_Description="Desc",
            faq_01_question="Question 1?",
            faq_01_answer="Answer 1 with content.",
            faq_02_question="",  # Empty
            faq_02_answer="",
            faq_03_question="Question 3?",
            faq_03_answer="Answer 3 with content.",
        )

        stage = FAQPAAStage()
        faq_list = stage._extract_faq(article)

        # Should extract only 2 (skipping empty faq_02)
        assert faq_list.count() == 2

    def test_validate_and_clean_removes_duplicates(self):
        """Test deduplication."""
        faq_list = FAQList()
        faq_list.add_item(1, "What is Python?", "Python is a popular programming language used widely in many industries.")
        faq_list.add_item(2, "What is Python?", "Python is another description of the Python language and its uses.")  # Duplicate
        faq_list.add_item(3, "How to learn programming?", "Start with basics and practice coding regularly to improve skills.")

        stage = FAQPAAStage()
        cleaned = stage._validate_and_clean(faq_list)

        # Should have 2 (removed duplicate)
        assert cleaned.count() == 2

    def test_validate_and_clean_removes_invalid(self):
        """Test removal of invalid items."""
        faq_list = FAQList()
        faq_list.add_item(1, "What is a valid question?", "Valid answer with enough content here to meet minimum requirements.")
        faq_list.add_item(2, "Too short question?", "Short")  # Invalid - answer too short

        stage = FAQPAAStage()
        cleaned = stage._validate_and_clean(faq_list)

        # Should have 1 (removed invalid)
        assert cleaned.count() == 1

    @pytest.mark.asyncio
    async def test_execute_stores_counts(self, valid_context):
        """Test that counts are stored."""
        stage = FAQPAAStage()
        result = await stage.execute(valid_context)

        assert "faq_count" in result.parallel_results
        assert "paa_count" in result.parallel_results


class TestFAQPAAIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, valid_context):
        """Test complete workflow."""
        stage = FAQPAAStage()
        result = await stage.execute(valid_context)

        faq_list = result.parallel_results["faq_items"]
        paa_list = result.parallel_results["paa_items"]

        # Check structure
        assert isinstance(faq_list, FAQList)
        assert isinstance(paa_list, PAAList)

        # Check items are renumbered
        for i, item in enumerate(faq_list.items, 1):
            assert item.number == i

        for i, item in enumerate(paa_list.items, 1):
            assert item.number == i


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
