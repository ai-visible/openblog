"""AEO (Agentic Search Optimization) scoring utility."""

import logging
import re
from typing import Dict, List, Optional, Any

from ..models.output_schema import ArticleOutput

logger = logging.getLogger(__name__)


class AEOScorer:
    """
    Score content for AEO (Agentic Search Optimization).
    
    AEO optimizes content for AI search engines like Google AI Overviews,
    ChatGPT, Perplexity, etc.
    """

    def __init__(self):
        """Initialize AEO scorer."""
        self.max_score = 100.0

    def score_article(
        self,
        output: ArticleOutput,
        primary_keyword: str,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> float:
        """
        Calculate AEO optimization score for an article.
        
        Args:
            output: Article output schema
            primary_keyword: Primary keyword/topic
            input_data: Optional input schema for E-E-A-T scoring
            
        Returns:
            AEO score (0-100)
        """
        scores = {}
        
        # 1. Direct Answer (25 points)
        scores['direct_answer'] = self._score_direct_answer(output, primary_keyword)
        
        # 2. Q&A Format (20 points)
        scores['qa_format'] = self._score_qa_format(output)
        
        # 3. Citation Clarity (15 points)
        scores['citation_clarity'] = self._score_citation_clarity(output)
        
        # 4. Natural Language (15 points)
        scores['natural_language'] = self._score_natural_language(output, primary_keyword)
        
        # 5. Structured Data (10 points)
        scores['structured_data'] = self._score_structured_data(output)
        
        # 6. E-E-A-T (15 points)
        scores['eat'] = self._score_eat(output, input_data) if input_data else 0.0
        
        # Total score
        total_score = sum(scores.values())
        
        logger.debug(f"AEO scores: {scores}, total: {total_score}")
        
        return min(total_score, self.max_score)

    def _score_direct_answer(
        self,
        output: ArticleOutput,
        primary_keyword: str,
    ) -> float:
        """
        Score direct answer presence and quality (25 points).
        
        Checks:
        - Direct answer field exists (10 points)
        - Direct answer length 40-60 words (5 points)
        - Direct answer contains primary keyword (5 points)
        - Direct answer contains citation [1] (5 points)
        """
        score = 0.0
        
        # Check if direct answer exists
        if output.Direct_Answer and output.Direct_Answer.strip():
            score += 10.0
            
            direct_answer_lower = output.Direct_Answer.lower()
            
            # Check length (40-60 words ideal)
            word_count = len(output.Direct_Answer.split())
            if 40 <= word_count <= 60:
                score += 5.0
            elif 30 <= word_count < 40 or 60 < word_count <= 80:
                score += 2.5
            
            # Check if contains primary keyword
            if primary_keyword.lower() in direct_answer_lower:
                score += 5.0
            
            # Check if contains citation [1]
            if re.search(r'\[1\]', output.Direct_Answer):
                score += 5.0
        else:
            # Fallback: check if intro starts with direct answer
            if output.Intro:
                intro_words = output.Intro.split()[:60]
                if len(intro_words) >= 30:
                    # Check if intro directly answers (contains question words or definitive statements)
                    intro_text = " ".join(intro_words).lower()
                    if primary_keyword.lower() in intro_text:
                        score += 5.0  # Partial credit
        
        return min(score, 25.0)

    def _score_qa_format(self, output: ArticleOutput) -> float:
        """
        Score Q&A format presence (20 points).
        
        Checks:
        - FAQ section exists with 5-6 items (10 points)
        - PAA section exists with 3-4 items (5 points)
        - Question-format headers in content (5 points)
        """
        score = 0.0
        
        # FAQ section (target: 5-6 items)
        faq_count = output.get_active_faqs()
        if faq_count >= 5:
            score += 10.0
        elif faq_count >= 3:
            score += 7.0  # Partial credit for 3-4 FAQ
        elif faq_count > 0:
            score += 3.0
        
        # PAA section (target: 3-4 items)
        paa_count = output.get_active_paas()
        if paa_count >= 3:
            score += 5.0
        elif paa_count >= 2:
            score += 3.0  # Partial credit for 2 PAA
        elif paa_count > 0:
            score += 1.0
        
        # Question-format headers in content (H2/H3 with questions)
        all_content = output.Intro + " " + self._get_all_section_content(output)
        # Check section titles for question format
        question_headers = 0
        sections = [
            output.section_01_title, output.section_02_title, output.section_03_title,
            output.section_04_title, output.section_05_title, output.section_06_title,
            output.section_07_title, output.section_08_title, output.section_09_title,
        ]
        for section_title in sections:
            if section_title:
                title_lower = section_title.lower()
                if any(q in title_lower for q in ["what is", "how does", "why does", "when should", "where can", "what are", "how can"]):
                    question_headers += 1
        
        if question_headers >= 2:
            score += 5.0
        elif question_headers >= 1:
            score += 2.5
        
        return min(score, 20.0)

    def _score_citation_clarity(self, output: ArticleOutput) -> float:
        """
        Score citation clarity for AI extraction (15 points).
        
        Checks:
        - Citations formatted as [1], [2] (5 points)
        - Sources list exists and matches citations (5 points)
        - Citations distributed per-paragraph (5 points)
        """
        score = 0.0
        
        all_content = output.Intro + " " + self._get_all_section_content(output)
        
        # Check citation format [1], [2], etc.
        citation_pattern = r'\[\d+\]'
        citations = re.findall(citation_pattern, all_content)
        
        if citations:
            score += 5.0
            
            # Check if sources match citations
            if output.Sources and output.Sources.strip():
                # Extract citation numbers
                citation_numbers = set()
                for citation in citations:
                    num = re.search(r'\d+', citation)
                    if num:
                        citation_numbers.add(int(num.group()))
                
                # Count sources (parse Sources string)
                source_lines = [line.strip() for line in output.Sources.split('\n') if line.strip() and line.strip().startswith('[')]
                source_indices = set()
                for line in source_lines:
                    match = re.search(r'\[(\d+)\]', line)
                    if match:
                        source_indices.add(int(match.group(1)))
                
                # Score based on match
                if citation_numbers.issubset(source_indices) and len(source_indices) > 0:
                    score += 5.0
                elif len(citation_numbers & source_indices) > 0:
                    score += 2.5
            
            # Check citation distribution per-paragraph
            # Extract paragraphs from content
            paragraphs = re.findall(r'<p[^>]*>.*?</p>', all_content, re.DOTALL)
            paragraphs_with_citations = 0
            for para in paragraphs:
                para_citations = re.findall(citation_pattern, para)
                if len(para_citations) >= 2:  # 2-3 citations per paragraph
                    paragraphs_with_citations += 1
            
            # Score based on distribution (target: 60%+ paragraphs have 2+ citations)
            if paragraphs:
                distribution_ratio = paragraphs_with_citations / len(paragraphs)
                if distribution_ratio >= 0.6:
                    score += 5.0
                elif distribution_ratio >= 0.4:
                    score += 3.0
                elif distribution_ratio >= 0.2:
                    score += 1.0
        else:
            # No citations found
            if output.Sources and output.Sources.strip():
                score += 2.5  # Sources exist but not cited
        
        return min(score, 15.0)

    def _score_natural_language(
        self,
        output: ArticleOutput,
        primary_keyword: str,
    ) -> float:
        """
        Score natural language usage (15 points).
        
        Checks:
        - Conversational phrases (6 points)
        - Direct statements (not vague) (5 points)
        - Natural question patterns (4 points)
        """
        score = 0.0
        
        all_content = output.Intro + " " + self._get_all_section_content(output)
        content_lower = all_content.lower()
        
        # Conversational phrases (enhanced scoring)
        # Extended conversational phrase list (matches injection list)
        conversational_phrases = [
            "how to", "what is", "why does", "when should", "where can",
            "you can", "you'll", "you should", "let's", "here's", "this is",
            "how can", "what are", "how do", "why should", "where are",
            "we'll", "that's", "when you", "if you", "so you can", "which means",
        ]
        phrase_count = sum(1 for phrase in conversational_phrases if phrase in content_lower)
        if phrase_count >= 8:
            score += 6.0
        elif phrase_count >= 5:
            score += 4.0
        elif phrase_count >= 2:
            score += 2.0
        
        # Direct statements (not vague)
        vague_patterns = [
            r"might be",
            r"could be",
            r"possibly",
            r"perhaps",
            r"maybe",
        ]
        vague_count = sum(1 for pattern in vague_patterns if re.search(pattern, content_lower))
        
        # Direct statements
        direct_patterns = [
            r"is ",
            r"are ",
            r"does ",
            r"provides ",
            r"enables ",
            r"allows ",
            r"helps ",
        ]
        direct_count = sum(1 for pattern in direct_patterns if re.search(pattern, content_lower))
        
        if direct_count > vague_count * 2:
            score += 5.0
        elif direct_count > vague_count:
            score += 3.0
        elif direct_count > 0:
            score += 1.0
        
        # Natural question patterns (enhanced)
        question_patterns = [
            r"what is",
            r"how do",
            r"why does",
            r"when should",
            r"where can",
            r"how can",
            r"what are",
        ]
        question_count = sum(1 for pattern in question_patterns if re.search(pattern, content_lower))
        if question_count >= 5:
            score += 4.0
        elif question_count >= 3:
            score += 3.0
        elif question_count >= 1:
            score += 1.5
        
        return min(score, 15.0)

    def _score_structured_data(self, output: ArticleOutput) -> float:
        """
        Score structured data presence (10 points).
        
        Checks:
        - Lists (ul/ol) present (5 points)
        - Headings structure (H2/H3) (5 points)
        
        Note: Section titles are stored in section_XX_title fields and count as H2 equivalents.
        """
        score = 0.0
        
        all_content = output.Intro + " " + self._get_all_section_content(output)
        
        # Lists
        list_count = all_content.count("<ul>") + all_content.count("<ol>")
        if list_count >= 3:
            score += 5.0
        elif list_count >= 1:
            score += 2.5
        
        # Headings structure - count both HTML tags AND section titles
        # Section titles are equivalent to H2 tags
        section_titles = [
            output.section_01_title, output.section_02_title, output.section_03_title,
            output.section_04_title, output.section_05_title, output.section_06_title,
            output.section_07_title, output.section_08_title, output.section_09_title,
        ]
        section_title_count = sum(1 for t in section_titles if t and t.strip())
        
        # Count explicit H2/H3 tags in content
        h2_in_content = all_content.count("<h2>")
        h3_in_content = all_content.count("<h3>")
        
        # Total H2 count = section titles + explicit H2 tags
        h2_count = section_title_count + h2_in_content
        h3_count = h3_in_content
        
        if h2_count >= 3 and (h3_count >= 2 or h2_count >= 5):
            score += 5.0
        elif h2_count >= 2:
            score += 2.5
        
        return min(score, 10.0)
    
    def _score_eat(self, output: ArticleOutput, input_data: Dict[str, Any]) -> float:
        """
        Score E-E-A-T (Experience, Expertise, Authoritativeness, Trustworthiness) (15 points).
        
        Checks:
        - Experience: Author bio mentions experience (4 points)
        - Expertise: Credentials/qualifications mentioned (4 points)
        - Authoritativeness: Author URL/social proof (4 points)
        - Trustworthiness: Source credibility (3 points)
        """
        score = 0.0
        
        # Experience: Author bio mentions experience
        author_bio = input_data.get('author_bio')
        if author_bio:
            experience_keywords = ["experience", "worked", "years", "expertise", "background"]
            if any(keyword in str(author_bio).lower() for keyword in experience_keywords):
                score += 4.0
            else:
                score += 2.0  # Partial credit if bio exists
        
        # Expertise: Credentials/qualifications
        if author_bio:
            expertise_keywords = ["degree", "certified", "phd", "master", "bachelor", "qualification", "certification"]
            if any(keyword in str(author_bio).lower() for keyword in expertise_keywords):
                score += 4.0
            else:
                score += 1.0  # Partial credit
        
        # Authoritativeness: Author URL/social proof
        author_url = input_data.get('author_url')
        author_name = input_data.get('author_name')
        if author_url:
            score += 4.0
        elif author_name:
            score += 2.0  # Partial credit if name exists
        
        # Trustworthiness: Source credibility
        if output.Sources and output.Sources.strip():
            # Check if sources are from credible domains
            credible_domains = [".edu", ".gov", ".org", "wikipedia", "research", "study"]
            source_lines = [line.strip() for line in output.Sources.split('\n') if line.strip()]
            credible_count = sum(
                1 for line in source_lines
                if any(domain in line.lower() for domain in credible_domains)
            )
            if credible_count >= 2:
                score += 3.0
            elif credible_count >= 1:
                score += 1.5
            elif len(source_lines) >= 5:
                score += 1.0  # Partial credit for multiple sources
        
        return min(score, 15.0)
    
    def _get_all_section_content(self, output: ArticleOutput) -> str:
        """Get all section content as a single string."""
        sections = [
            output.section_01_content, output.section_02_content, output.section_03_content,
            output.section_04_content, output.section_05_content, output.section_06_content,
            output.section_07_content, output.section_08_content, output.section_09_content,
        ]
        return " ".join(s for s in sections if s)

