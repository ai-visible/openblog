"""
Tests for Stage 6: Table of Contents

Tests:
- TOC model
- Label generation from titles
- Section extraction
- Label validation
- Stage execution
"""

import pytest
from pipeline.core import ExecutionContext
from pipeline.models.toc import TOCEntry, TableOfContents
from pipeline.models.output_schema import ArticleOutput
from pipeline.blog_generation.stage_06_toc import TableOfContentsStage


@pytest.fixture
def valid_context():
    """Create valid ExecutionContext for Stage 6."""
    article = ArticleOutput(
        Headline="Advanced Python Programming",
        Teaser="Learn advanced Python.",
        Direct_Answer="Master Python.",
        Intro="Introduction.",
        Meta_Title="Python Advanced",
        Meta_Description="Advanced Python guide.",
        section_01_title="Getting Started with Python",
        section_01_content="<p>Python intro</p>",
        section_02_title="Advanced Object-Oriented Programming",
        section_02_content="<p>OOP content</p>",
        section_03_title="Design Patterns and Best Practices",
        section_03_content="<p>Patterns content</p>",
        section_04_title="Performance Optimization Techniques",
        section_04_content="<p>Optimization</p>",
        section_05_title="Testing and Quality Assurance",
        section_05_content="<p>Testing</p>",
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


class TestTOCEntry:
    """Test TOCEntry model."""

    def test_entry_creation(self):
        """Test creating TOC entry."""
        entry = TOCEntry(
            section_num=1,
            full_title="Getting Started with Python",
            short_label="Getting Started",
        )
        assert entry.section_num == 1
        assert entry.full_title == "Getting Started with Python"
        assert entry.short_label == "Getting Started"

    def test_toc_key(self):
        """Test toc_key property."""
        entry1 = TOCEntry(section_num=1, full_title="Title", short_label="Label")
        entry9 = TOCEntry(section_num=9, full_title="Title", short_label="Label")

        assert entry1.toc_key == "toc_01"
        assert entry9.toc_key == "toc_09"

    def test_word_count(self):
        """Test word count calculation."""
        entry1 = TOCEntry(section_num=1, full_title="Title", short_label="One")
        entry2 = TOCEntry(section_num=1, full_title="Title", short_label="One Two")
        entry3 = TOCEntry(section_num=1, full_title="Title", short_label="One Two Three")

        assert entry1.word_count() == 1
        assert entry2.word_count() == 2
        assert entry3.word_count() == 3

    def test_entry_repr(self):
        """Test string representation."""
        entry = TOCEntry(section_num=3, full_title="Title", short_label="Label")
        repr_str = repr(entry)

        assert "TOCEntry" in repr_str
        assert "3" in repr_str
        assert "Label" in repr_str


class TestTableOfContents:
    """Test TableOfContents collection."""

    def test_toc_creation(self):
        """Test creating ToC."""
        toc = TableOfContents()
        assert toc.count() == 0

    def test_add_entry(self):
        """Test adding entries."""
        toc = TableOfContents()
        toc.add_entry(1, "Getting Started", "Start")
        toc.add_entry(2, "Advanced Topics", "Advanced")

        assert toc.count() == 2

    def test_to_dict(self):
        """Test converting to dictionary."""
        toc = TableOfContents()
        toc.add_entry(1, "Getting Started", "Start")
        toc.add_entry(2, "Advanced Topics", "Advanced")

        toc_dict = toc.to_dict()

        assert toc_dict["toc_01"] == "Start"
        assert toc_dict["toc_02"] == "Advanced"
        assert len(toc_dict) == 2

    def test_get_entry(self):
        """Test retrieving entry by section number."""
        toc = TableOfContents()
        toc.add_entry(1, "Section 1", "Label 1")
        toc.add_entry(2, "Section 2", "Label 2")

        entry = toc.get_entry(2)
        assert entry is not None
        assert entry.short_label == "Label 2"

    def test_get_entry_not_found(self):
        """Test retrieving non-existent entry."""
        toc = TableOfContents()
        toc.add_entry(1, "Section 1", "Label 1")

        entry = toc.get_entry(5)
        assert entry is None

    def test_validate_labels_valid(self):
        """Test validation with valid labels."""
        toc = TableOfContents()
        toc.add_entry(1, "Section", "One")
        toc.add_entry(2, "Section", "One Two")

        assert toc.validate_labels() is True

    def test_validate_labels_too_many_words(self):
        """Test validation with too many words."""
        toc = TableOfContents()
        toc.add_entry(1, "Section", "One Two Three")

        # Should warn but still work
        assert toc.validate_labels() is False

    def test_validate_labels_empty(self):
        """Test validation with empty label."""
        toc = TableOfContents()
        toc.add_entry(1, "Section", "")

        assert toc.validate_labels() is False

    def test_validate_labels_too_long(self):
        """Test validation with very long label."""
        toc = TableOfContents()
        long_label = "A" * 60

        toc.add_entry(1, "Section", long_label)

        assert toc.validate_labels() is False


class TestTableOfContentsStage:
    """Test Stage 6: Table of Contents."""

    @pytest.mark.asyncio
    async def test_execute_success(self, valid_context):
        """Test successful Stage 6 execution."""
        stage = TableOfContentsStage()
        result = await stage.execute(valid_context)

        assert "toc_dict" in result.parallel_results
        assert len(result.parallel_results["toc_dict"]) > 0
        assert "toc_01" in result.parallel_results["toc_dict"]

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

        stage = TableOfContentsStage()
        result = await stage.execute(context)

        assert result.parallel_results["toc_dict"] == {}

    def test_extract_sections(self, valid_context):
        """Test section extraction."""
        stage = TableOfContentsStage()
        toc = stage._extract_sections(valid_context.structured_data)

        assert toc.count() == 5  # 5 non-empty sections
        assert toc.get_entry(1) is not None
        assert toc.get_entry(1).full_title == "Getting Started with Python"

    def test_extract_sections_filters_empty(self):
        """Test that empty sections are filtered."""
        article = ArticleOutput(
            Headline="Test",
            Teaser="Hook",
            Direct_Answer="Answer",
            Intro="Intro",
            Meta_Title="Meta",
            Meta_Description="Desc",
            section_01_title="Section 1",
            section_02_title="",  # Empty
            section_03_title="Section 3",
        )

        stage = TableOfContentsStage()
        toc = stage._extract_sections(article)

        assert toc.count() == 2
        assert toc.get_entry(1) is not None
        assert toc.get_entry(2) is None

    def test_generate_labels_basic(self):
        """Test label generation from titles."""
        toc = TableOfContents()
        toc.add_entry(1, "Getting Started with Python", "")
        toc.add_entry(2, "Advanced Object-Oriented Programming", "")

        stage = TableOfContentsStage()
        toc_with_labels = stage._generate_labels(toc)

        # Check labels are generated
        entry1 = toc_with_labels.get_entry(1)
        entry2 = toc_with_labels.get_entry(2)

        assert entry1.short_label != ""
        assert entry2.short_label != ""

    def test_generate_labels_removes_stop_words(self):
        """Test that stop words are removed."""
        toc = TableOfContents()
        toc.add_entry(1, "The Guide to Python Programming", "")

        stage = TableOfContentsStage()
        toc_with_labels = stage._generate_labels(toc)

        entry = toc_with_labels.get_entry(1)
        # Should not contain 'The' or 'to' (stop words)
        label_lower = entry.short_label.lower()
        assert "the" not in label_lower
        assert " to " not in label_lower

    def test_generate_labels_max_two_words(self):
        """Test that labels are max 2 words."""
        toc = TableOfContents()
        toc.add_entry(1, "The Best Guide to Advanced Python Programming", "")

        stage = TableOfContentsStage()
        toc_with_labels = stage._generate_labels(toc)

        entry = toc_with_labels.get_entry(1)
        assert entry.word_count() <= 2

    def test_generate_labels_preserves_section_numbers(self):
        """Test that section numbers are preserved."""
        toc = TableOfContents()
        toc.add_entry(5, "Some Title", "")
        toc.add_entry(8, "Another Title", "")

        stage = TableOfContentsStage()
        toc_with_labels = stage._generate_labels(toc)

        entry5 = toc_with_labels.get_entry(5)
        entry8 = toc_with_labels.get_entry(8)

        assert entry5 is not None
        assert entry5.section_num == 5
        assert entry8 is not None
        assert entry8.section_num == 8

    @pytest.mark.asyncio
    async def test_execute_stores_metadata(self, valid_context):
        """Test that execution stores metadata."""
        stage = TableOfContentsStage()
        result = await stage.execute(valid_context)

        assert "toc_dict" in result.parallel_results
        assert "toc_entries" in result.parallel_results
        assert result.parallel_results["toc_entries"] is not None

    def test_toc_dict_format(self):
        """Test that toc_dict has correct format."""
        toc = TableOfContents()
        toc.add_entry(1, "Section 1", "Label 1")
        toc.add_entry(3, "Section 3", "Label 3")
        toc.add_entry(9, "Section 9", "Label 9")

        toc_dict = toc.to_dict()

        # Check keys are properly formatted
        assert "toc_01" in toc_dict
        assert "toc_03" in toc_dict
        assert "toc_09" in toc_dict

        # Check values are the labels
        assert toc_dict["toc_01"] == "Label 1"
        assert toc_dict["toc_03"] == "Label 3"
        assert toc_dict["toc_09"] == "Label 9"


class TestTableOfContentsIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_full_workflow(self, valid_context):
        """Test complete workflow."""
        stage = TableOfContentsStage()
        result = await stage.execute(valid_context)

        # Check toc_dict
        toc_dict = result.parallel_results["toc_dict"]
        assert len(toc_dict) > 0
        assert all(k.startswith("toc_") for k in toc_dict.keys())
        assert all(isinstance(v, str) and len(v) > 0 for v in toc_dict.values())

        # Check toc_entries
        toc_entries = result.parallel_results["toc_entries"]
        assert toc_entries.count() == len(toc_dict)
        assert all(entry.word_count() >= 1 for entry in toc_entries.entries)

    def test_extract_and_generate_workflow(self, valid_context):
        """Test extract and generate workflow."""
        stage = TableOfContentsStage()

        # Extract sections
        toc = stage._extract_sections(valid_context.structured_data)
        assert toc.count() == 5

        # Generate labels
        toc_with_labels = stage._generate_labels(toc)
        assert toc_with_labels.count() == 5

        # Convert to dict
        toc_dict = toc_with_labels.to_dict()
        assert len(toc_dict) == 5

        # All keys should be toc_0X format
        expected_keys = {f"toc_0{i}" for i in range(1, 6)}
        assert set(toc_dict.keys()) == expected_keys


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
