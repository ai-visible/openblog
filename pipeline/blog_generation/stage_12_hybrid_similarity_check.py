"""
Stage 12: Hybrid Content Similarity Check with Regeneration

Enhanced similarity checking combining character shingles and semantic embeddings.
Includes automatic content regeneration when similarity is too high.

Features:
- Hybrid similarity detection (character + semantic)
- Automatic content regeneration workflow
- Batch-session memory management
- Performance analytics
- Gemini embeddings integration

Input:
  - ExecutionContext with final_article and metadata
  
Output:
  - Updated ExecutionContext with similarity_report
  - Regeneration recommendations and triggers
  - Batch similarity statistics

Usage in batch generation with regeneration:
  from pipeline.utils.gemini_embeddings import GeminiEmbeddingClient
  from pipeline.utils.hybrid_similarity_checker import HybridSimilarityChecker
  
  # Enhanced mode with semantic analysis
  embedding_client = GeminiEmbeddingClient(api_key="your-key")
  similarity_checker = HybridSimilarityChecker(
      embedding_client=embedding_client,
      enable_regeneration=True
  )
  
  batch_manager = HybridBatchSimilarityManager(similarity_checker)
  
  for article_config in batch:
      max_attempts = 3
      for attempt in range(max_attempts):
          # Generate article (Stages 0-12)
          context = await generate_article(article_config, attempt=attempt)
          
          # Check similarity with regeneration
          result = await batch_manager.check_article_with_regeneration(context)
          
          if result.approved:
              break  # Success
          elif result.regeneration_triggered:
              logger.info(f"Regenerating content (attempt {attempt + 1}/{max_attempts})")
              continue  # Try again
          else:
              logger.warning(f"Skipping article after {max_attempts} attempts")
              break
"""

import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

from ..core import ExecutionContext, Stage
from ..utils.hybrid_similarity_checker import HybridSimilarityChecker, SimilarityResult

logger = logging.getLogger(__name__)


@dataclass
class RegenerationResult:
    """Result of article check with regeneration workflow."""
    approved: bool
    regeneration_triggered: bool
    similarity_report: SimilarityResult
    attempt_number: int
    max_attempts_reached: bool
    final_decision: str  # "approved", "rejected", "regenerate"


class HybridSimilarityCheckStage(Stage):
    """
    Stage 12: Hybrid similarity check with semantic embeddings.
    
    Integrated into main pipeline workflow to detect content cannibalization.
    Runs after Stage 10 (cleanup) and before Stage 11 (storage).
    
    Combines character-level and semantic similarity analysis to detect
    content cannibalization and provide similarity reports.
    
    Features:
    - Character shingles for language-agnostic similarity
    - Semantic embeddings via Gemini API for topic similarity
    - Batch memory for detecting duplicates within a generation session
    - Non-blocking: logs warnings but doesn't block publication
    """

    stage_num = 12
    stage_name = "Hybrid Content Similarity Check"

    def __init__(self, similarity_checker: Optional[HybridSimilarityChecker] = None):
        """
        Initialize with hybrid similarity checker.
        
        Args:
            similarity_checker: HybridSimilarityChecker instance.
                              If None, creates checker with semantic embeddings if API key available.
        """
        # Import here to avoid circular imports
        import os
        from ..utils.gemini_embeddings import GeminiEmbeddingClient
        
        if similarity_checker is None:
            # Try to initialize with semantic embeddings if API key available
            api_key = (
                os.getenv("GEMINI_API_KEY") or 
                os.getenv("GOOGLE_API_KEY") or 
                os.getenv("GOOGLE_GEMINI_API_KEY")
            )
            
            if api_key:
                try:
                    embedding_client = GeminiEmbeddingClient(api_key=api_key)
                    similarity_checker = HybridSimilarityChecker(
                        embedding_client=embedding_client,
                        enable_regeneration=False  # Don't auto-regenerate in main pipeline
                    )
                    logger.info("✅ Initialized HybridSimilarityChecker with semantic embeddings")
                except Exception as e:
                    logger.warning(f"Failed to initialize semantic embeddings: {e}")
                    logger.info("Falling back to character-only similarity checking")
                    similarity_checker = HybridSimilarityChecker()
            else:
                logger.info("No Gemini API key found - using character-only similarity checking")
                similarity_checker = HybridSimilarityChecker()
        
        self.similarity_checker = similarity_checker
        self._standalone_mode = False  # Always integrated mode in main pipeline

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute hybrid similarity check.

        Args:
            context: ExecutionContext with generated article data

        Returns:
            Updated ExecutionContext with detailed similarity analysis
        """
        logger.info(f"Stage {self.stage_num}: {self.stage_name}")
        logger.info(f"Job ID: {context.job_id}")
        logger.info(f"Analysis mode: {'Hybrid (shingles + embeddings)' if self.similarity_checker.semantic_mode else 'Character shingles only'}")

        try:
            # Extract article data for similarity checking
            article_data = self._extract_article_data(context)
            
            if not article_data:
                logger.warning("No article data found for similarity check")
                context.similarity_report = SimilarityResult(
                    is_too_similar=False,
                    similarity_score=0.0,
                    issues=["No article data available"],
                    analysis_mode="none"
                )
                return context

            # Perform hybrid similarity check
            similarity_result = self.similarity_checker.check_content_similarity(
                article_data, 
                slug=context.job_id
            )

            # Store result in context
            context.similarity_report = similarity_result

            # Log detailed results
            self._log_hybrid_results(context.job_id, similarity_result)

            # Add enhanced recommendations to context
            context.similarity_recommendations = self._generate_hybrid_recommendations(similarity_result)

            # Get batch statistics with embedding info
            context.batch_stats = self.similarity_checker.get_batch_stats()

            # Store regeneration flag for workflow
            context.regeneration_needed = similarity_result.regeneration_needed

            logger.info("✅ Hybrid similarity check completed")
            return context

        except Exception as e:
            logger.error(f"Hybrid similarity check failed: {e}")
            # Don't fail the pipeline - provide empty result
            context.similarity_report = SimilarityResult(
                is_too_similar=False,
                similarity_score=0.0,
                issues=[f"Similarity check error: {str(e)}"],
                analysis_mode="error"
            )
            return context

    def _extract_article_data(self, context: ExecutionContext) -> Optional[Dict[str, Any]]:
        """
        Extract article data from ExecutionContext for similarity checking.
        
        Stage 12 runs after Stage 10, so validated_article should be available.
        Falls back to other sources if needed.
        """
        # Primary source: validated_article from Stage 10
        if hasattr(context, 'validated_article') and context.validated_article:
            article_data = dict(context.validated_article)
            # Ensure primary_keyword is set
            if 'primary_keyword' not in article_data:
                article_data['primary_keyword'] = context.job_config.get('primary_keyword', '')
            return article_data

        # Fallback: final_article (if available)
        if hasattr(context, 'final_article') and context.final_article:
            article_data = dict(context.final_article)
            if 'primary_keyword' not in article_data:
                article_data['primary_keyword'] = context.job_config.get('primary_keyword', '')
            return article_data

        # Fallback: Extract from job_config and parallel_results
        article_data = {}
        job_config = getattr(context, 'job_config', {})
        
        # Primary keyword
        article_data['primary_keyword'] = job_config.get('primary_keyword', '')
        
        # Extract content from parallel_results
        if hasattr(context, 'parallel_results') and context.parallel_results:
            pr = context.parallel_results
            
            # Sections
            if 'sections' in pr:
                sections = pr['sections']
                for i, section in enumerate(sections, 1):
                    if isinstance(section, dict):
                        article_data[f'section_{i:02d}_heading'] = section.get('heading', '')
                        article_data[f'section_{i:02d}_content'] = section.get('content', '')
            
            # ToC
            if 'toc' in pr:
                article_data['table_of_contents'] = pr['toc']
            
            # FAQ
            if 'faq' in pr:
                article_data['FAQ'] = pr['faq']
            
            # Intro
            if 'intro' in pr:
                article_data['Intro'] = pr['intro']

        # Fallback: extract from final_html if available
        if not article_data.get('Intro') and hasattr(context, 'final_html'):
            article_data = self._extract_from_html(context.final_html, article_data)

        # Must have at least keyword and some content
        if not article_data.get('primary_keyword') and not article_data.get('Headline'):
            return None

        return article_data

    def _extract_from_html(self, html: str, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract content from final HTML as fallback.
        
        Simple text extraction for similarity checking.
        """
        import re
        
        if not html:
            return base_data
        
        # Remove HTML tags for content extraction
        text_content = re.sub(r'<[^>]+>', ' ', html)
        text_content = re.sub(r'\s+', ' ', text_content).strip()
        
        # Store as generic content for analysis
        if not base_data.get('Intro') and text_content:
            # Take first 500 chars as intro
            base_data['Intro'] = text_content[:500]
        
        # Store full content in a generic field
        base_data['_full_content'] = text_content[:2000]  # Limit for performance
        
        return base_data

    def _log_hybrid_results(self, job_id: str, result: SimilarityResult):
        """Log detailed hybrid similarity results."""
        
        # Main result
        if result.is_too_similar:
            logger.warning(
                f"🚨 HIGH SIMILARITY DETECTED for '{job_id}': "
                f"{result.similarity_score:.1f}% similarity to '{result.similar_article}'"
            )
        elif result.similarity_score > 50:
            logger.info(
                f"⚠️ Moderate similarity for '{job_id}': "
                f"{result.similarity_score:.1f}% similarity to '{result.similar_article}'"
            )
        else:
            logger.info(
                f"✅ Unique content for '{job_id}': "
                f"{result.similarity_score:.1f}% similarity"
            )

        # Analysis breakdown
        if result.analysis_mode == "hybrid":
            logger.info(
                f"📊 Analysis breakdown - "
                f"Character: {result.shingle_score:.1f}%, "
                f"Semantic: {result.semantic_score:.1%}" if result.semantic_score else "Semantic: N/A"
            )
        else:
            logger.info(f"📊 Analysis mode: {result.analysis_mode}")

        # Regeneration status
        if result.regeneration_needed:
            logger.info("🔄 Regeneration triggered due to high similarity")

        # Issues
        if result.issues:
            logger.info(f"🔍 Similarity issues found:")
            for issue in result.issues:
                logger.info(f"  - {issue}")

    def _generate_hybrid_recommendations(self, result: SimilarityResult) -> Dict[str, Any]:
        """Generate enhanced recommendations for hybrid analysis."""
        
        recommendations = {
            "action": "proceed",  # proceed, modify, regenerate, skip
            "suggestions": [],
            "severity": "low",  # low, medium, high, critical
            "analysis_mode": result.analysis_mode,
            "regeneration_recommended": result.regeneration_needed
        }

        if result.is_too_similar:
            if result.regeneration_needed:
                recommendations["action"] = "regenerate"
                recommendations["severity"] = "critical"
                recommendations["suggestions"] = [
                    "Content is too similar to existing article",
                    "Automatic regeneration triggered",
                    f"Similar article: {result.similar_article}",
                    "Try different angle, examples, or focus area"
                ]
            else:
                recommendations["action"] = "skip"
                recommendations["severity"] = "critical"
                recommendations["suggestions"] = [
                    "Content is too similar to existing article",
                    f"Similar article: {result.similar_article}",
                    "Consider manual review or different topic"
                ]
        elif result.similarity_score > 60:
            recommendations["action"] = "modify"
            recommendations["severity"] = "high"
            recommendations["suggestions"] = [
                "High similarity detected",
                "Consider adjusting content angle or adding unique insights",
                "Review and enhance differentiating factors"
            ]
        elif result.similarity_score > 40:
            recommendations["action"] = "proceed"
            recommendations["severity"] = "medium"
            recommendations["suggestions"] = [
                "Moderate similarity detected - safe to proceed",
                "Consider adding more unique perspectives or examples"
            ]

        # Add analysis-specific suggestions
        if result.analysis_mode == "hybrid":
            if result.semantic_score and result.semantic_score > 0.85:
                recommendations["suggestions"].append("High semantic similarity - content covers very similar concepts")
            if result.shingle_score and result.shingle_score > 60:
                recommendations["suggestions"].append("High character similarity - content structure very similar")

        # Add specific issue-based suggestions
        if result.issues:
            for issue in result.issues:
                if "keyword" in issue.lower():
                    recommendations["suggestions"].append("Consider using different primary keyword or angle")
                elif "title" in issue.lower():
                    recommendations["suggestions"].append("Consider rephrasing the title and headlines")
                elif "semantic" in issue.lower():
                    recommendations["suggestions"].append("Content topic too similar - try different approach or examples")
                elif "character" in issue.lower():
                    recommendations["suggestions"].append("Text structure too similar - vary writing style and format")
                elif "faq" in issue.lower():
                    recommendations["suggestions"].append("FAQ questions overlap - create more specific questions")

        return recommendations

    def add_article_to_batch(self, context: ExecutionContext) -> Optional[str]:
        """
        Add the current article to batch memory for future comparisons.
        
        Should be called after similarity check if article is approved.
        """
        try:
            article_data = self._extract_article_data(context)
            if article_data:
                slug = self.similarity_checker.add_article(article_data, context.job_id)
                logger.info(f"Added '{slug}' to batch memory")
                return slug
        except Exception as e:
            logger.error(f"Failed to add article to batch: {e}")
        
        return None

    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get current batch statistics with embedding info."""
        return self.similarity_checker.get_batch_stats()

    def clear_batch(self):
        """Clear current batch (start new session)."""
        if not self._standalone_mode:
            self.similarity_checker.clear_batch()
            logger.info("Batch memory cleared")

    def remove_from_batch(self, slug: str) -> bool:
        """Remove article from batch memory."""
        return self.similarity_checker.remove_article(slug)


# ========== BATCH WORKFLOW WITH REGENERATION ==========

class HybridBatchSimilarityManager:
    """
    Enhanced batch manager with regeneration workflow.
    
    Handles automatic content regeneration when similarity is too high.
    """
    
    def __init__(self, similarity_checker: HybridSimilarityChecker, max_regeneration_attempts: int = 3):
        self.similarity_checker = similarity_checker
        self.similarity_stage = HybridSimilarityCheckStage(similarity_checker)
        self.max_regeneration_attempts = max_regeneration_attempts
        
        self.approved_articles = []
        self.rejected_articles = []
        self.regenerated_articles = []
    
    async def check_article(self, context: ExecutionContext) -> bool:
        """
        Basic article approval check (backward compatibility).
        
        Returns:
            True if article should be included, False if rejected
        """
        result = await self.check_article_with_regeneration(context)
        return result.approved
    
    async def check_article_with_regeneration(self, context: ExecutionContext, attempt: int = 1) -> RegenerationResult:
        """
        Check article with regeneration workflow support.
        
        Args:
            context: ExecutionContext with article data
            attempt: Current generation attempt (1-based)
            
        Returns:
            RegenerationResult with detailed workflow information
        """
        # Run similarity check
        context = await self.similarity_stage.execute(context)
        
        similarity_report = context.similarity_report
        max_attempts_reached = attempt >= self.max_regeneration_attempts
        
        # Decision logic
        if similarity_report.is_too_similar:
            if similarity_report.regeneration_needed and not max_attempts_reached:
                # Trigger regeneration
                self.regenerated_articles.append({
                    'job_id': context.job_id,
                    'attempt': attempt,
                    'reason': 'similarity_too_high',
                    'similarity_score': similarity_report.similarity_score,
                    'similar_to': similarity_report.similar_article
                })
                
                return RegenerationResult(
                    approved=False,
                    regeneration_triggered=True,
                    similarity_report=similarity_report,
                    attempt_number=attempt,
                    max_attempts_reached=False,
                    final_decision="regenerate"
                )
            else:
                # Reject (max attempts reached or regeneration disabled)
                self.rejected_articles.append({
                    'job_id': context.job_id,
                    'reason': 'max_attempts_reached' if max_attempts_reached else 'too_similar',
                    'similarity_score': similarity_report.similarity_score,
                    'similar_to': similarity_report.similar_article,
                    'attempts_made': attempt
                })
                
                return RegenerationResult(
                    approved=False,
                    regeneration_triggered=False,
                    similarity_report=similarity_report,
                    attempt_number=attempt,
                    max_attempts_reached=max_attempts_reached,
                    final_decision="rejected"
                )
        
        # Article approved - add to batch memory
        slug = self.similarity_stage.add_article_to_batch(context)
        if slug:
            self.approved_articles.append({
                'job_id': context.job_id,
                'slug': slug,
                'similarity_score': similarity_report.similarity_score,
                'attempts_made': attempt,
                'analysis_mode': similarity_report.analysis_mode
            })
        
        return RegenerationResult(
            approved=True,
            regeneration_triggered=False,
            similarity_report=similarity_report,
            attempt_number=attempt,
            max_attempts_reached=False,
            final_decision="approved"
        )
    
    def get_batch_summary(self) -> Dict[str, Any]:
        """Get comprehensive batch processing summary."""
        total_regenerations = len(self.regenerated_articles)
        unique_regenerated_jobs = len(set(r['job_id'] for r in self.regenerated_articles))
        
        return {
            'approved_count': len(self.approved_articles),
            'rejected_count': len(self.rejected_articles),
            'regeneration_count': total_regenerations,
            'unique_jobs_regenerated': unique_regenerated_jobs,
            'approved_articles': self.approved_articles,
            'rejected_articles': self.rejected_articles,
            'regenerated_articles': self.regenerated_articles,
            'batch_stats': self.similarity_stage.get_batch_statistics(),
            'regeneration_settings': {
                'max_attempts': self.max_regeneration_attempts,
                'regeneration_enabled': self.similarity_checker.enable_regeneration
            }
        }
    
    def clear_batch(self):
        """Start new batch session."""
        self.similarity_stage.clear_batch()
        self.approved_articles.clear()
        self.rejected_articles.clear()
        self.regenerated_articles.clear()
        logger.info("Batch session reset with regeneration tracking")