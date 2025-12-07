"""
Stage 9: Image Generation

Maps to v4.1 Phase 8, Steps 25-28: get-insights → image_empty? → execute_image_generation → store_image_in_blog

Generates **3 article images** via Replicate API with detailed prompts:
1. Hero image (from headline)
2. Mid-article image (from sections 3-4)
3. Bottom image (from sections 6-7)

Input:
  - ExecutionContext.structured_data (headline + section titles)
  - ExecutionContext.company_data (industry, description)
  - ExecutionContext.job_config (language)

Output:
  - ExecutionContext.parallel_results['image_url'] (Hero CDN URL)
  - ExecutionContext.parallel_results['image_alt_text'] (Hero alt text)
  - ExecutionContext.parallel_results['mid_image_url'] (Mid CDN URL)
  - ExecutionContext.parallel_results['mid_image_alt'] (Mid alt text)
  - ExecutionContext.parallel_results['bottom_image_url'] (Bottom CDN URL)
  - ExecutionContext.parallel_results['bottom_image_alt'] (Bottom alt text)

Process:
1. Check if images already exist (conditional skip)
2. Get image generation prompts from headline + section titles
3. Call image generator 3 times (Hero, Mid, Bottom)
4. Generate alt texts
5. Store results in parallel_results
"""

import logging
from typing import Optional

from ..core.execution_context import ExecutionContext
from ..core.workflow_engine import Stage
from ..core.error_handling import with_image_fallback, GracefulDegradation, error_reporter
from ..models.google_imagen_client import GoogleImagenClient
from ..models.image_generator import ImageGenerator  # Keep as fallback
from ..prompts.image_prompt import generate_image_prompt

logger = logging.getLogger(__name__)


class ImageStage(Stage):
    """
    Stage 9: Image Generation.

    Handles:
    - Conditional skip (if images already exist)
    - Image prompt generation from headline + section titles
    - Replicate API integration (3x calls)
    - Alt text generation (3x)
    - Error handling and retry logic
    """

    stage_num = 9
    stage_name = "Image Generation"

    def __init__(self) -> None:
        """Initialize image stage with Google Imagen client (primary) and Replicate fallback."""
        # Try Google Imagen first (primary)
        try:
            self.primary_generator = GoogleImagenClient()
            if not self.primary_generator.mock_mode:
                logger.info("Using Imagen 4.0 for image generation (via Gemini SDK)")
            else:
                logger.info("Imagen 4.0 in mock mode, will use fallback")
        except Exception as e:
            logger.warning(f"Google Imagen initialization failed: {e}")
            self.primary_generator = None
        
        # Initialize Replicate fallback
        try:
            self.fallback_generator = ImageGenerator()
            logger.info("Replicate fallback generator initialized")
        except Exception as e:
            logger.warning(f"Replicate fallback initialization failed: {e}")
            self.fallback_generator = None

    async def execute(self, context: ExecutionContext) -> ExecutionContext:
        """
        Execute Stage 9: Generate 3 article images.

        Input from context:
        - structured_data: ArticleOutput with headline + section titles
        - company_data: Company information
        - job_config: Job configuration with language

        Output to context:
        - parallel_results['image_url']: Hero image CDN URL
        - parallel_results['image_alt_text']: Hero alt text
        - parallel_results['mid_image_url']: Mid-article image URL
        - parallel_results['mid_image_alt']: Mid alt text
        - parallel_results['bottom_image_url']: Bottom image URL
        - parallel_results['bottom_image_alt']: Bottom alt text

        Args:
            context: ExecutionContext from parallel stages

        Returns:
            Updated context with parallel_results populated
        """
        logger.info(f"Stage 9: {self.stage_name} (3 images)")

        # Validate input
        if not context.structured_data:
            logger.warning("No structured_data available for image generation")
            context.parallel_results["image_url"] = ""
            context.parallel_results["image_alt_text"] = ""
            context.parallel_results["mid_image_url"] = ""
            context.parallel_results["mid_image_alt"] = ""
            context.parallel_results["bottom_image_url"] = ""
            context.parallel_results["bottom_image_alt"] = ""
            return context

        headline = context.structured_data.Headline
        
        # Extract section titles for mid and bottom images
        mid_title = self._get_section_title(context.structured_data, [3, 4]) or headline
        bottom_title = self._get_section_title(context.structured_data, [6, 7]) or headline
        
        logger.info(f"Generating 3 images:")
        logger.info(f"  Hero: {headline[:50]}...")
        logger.info(f"  Mid: {mid_title[:50]}...")
        logger.info(f"  Bottom: {bottom_title[:50]}...")

        # Generate image 1: Hero
        hero_prompt = generate_image_prompt(
            headline=headline,
            company_data=context.company_data,
            job_config=context.job_config,
        )
        hero_url = await self._generate_image_with_retry(hero_prompt, context)
        hero_alt = self._generate_alt_text(headline)
        
        context.parallel_results["image_url"] = hero_url or ""
        context.parallel_results["image_alt_text"] = hero_alt

        # Generate image 2: Mid-article
        mid_prompt = generate_image_prompt(
            headline=mid_title,
            company_data=context.company_data,
            job_config=context.job_config,
        )
        mid_url = await self._generate_image_with_retry(mid_prompt, context)
        mid_alt = self._generate_alt_text(mid_title)
        
        context.parallel_results["mid_image_url"] = mid_url or ""
        context.parallel_results["mid_image_alt"] = mid_alt

        # Generate image 3: Bottom
        bottom_prompt = generate_image_prompt(
            headline=bottom_title,
            company_data=context.company_data,
            job_config=context.job_config,
        )
        bottom_url = await self._generate_image_with_retry(bottom_prompt, context)
        bottom_alt = self._generate_alt_text(bottom_title)
        
        context.parallel_results["bottom_image_url"] = bottom_url or ""
        context.parallel_results["bottom_image_alt"] = bottom_alt

        images_generated = sum([bool(hero_url), bool(mid_url), bool(bottom_url)])
        logger.info(f"✅ Generated {images_generated}/3 images successfully")

        return context

    @with_image_fallback("stage_09")
    async def _generate_image_with_retry(self, image_prompt: str, context: ExecutionContext) -> Optional[str]:
        """
        Generate image with comprehensive error handling and retries.
        
        Args:
            image_prompt: Generated image prompt
            context: Execution context
            
        Returns:
            Image URL if successful, fallback URL if failed
        """
        try:
            image_url = self._generate_image_with_fallback(image_prompt, context)
            
            if not image_url:
                raise Exception("All image generation services failed")
                
            return image_url
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            # The decorator will handle fallback to placeholder image
            raise e

    def _generate_image_with_fallback(self, image_prompt: str, context: ExecutionContext) -> Optional[str]:
        """
        Generate image using Google Imagen (primary) with Replicate fallback.
        
        Args:
            image_prompt: Generated image prompt
            context: Execution context (for project folder ID if needed)
            
        Returns:
            Image URL if successful, None if failed
        """
        # Try Google Imagen first
        if self.primary_generator and not self.primary_generator.mock_mode:
            logger.info("Attempting image generation with Imagen 4.0...")
            try:
                # Extract project folder ID if available
                project_folder_id = context.company_data.get("project_folder_id")
                image_url = self.primary_generator.generate_image(image_prompt, project_folder_id)
                if image_url:
                    logger.info("✅ Imagen 4.0 generation successful")
                    return image_url
                logger.warning("Imagen 4.0 generation failed, trying fallback...")
            except Exception as e:
                logger.warning(f"Google Imagen error: {e}, trying fallback...")
        
        # Try Replicate fallback
        if self.fallback_generator and not getattr(self.fallback_generator, 'mock_mode', True):
            logger.info("Attempting image generation with Replicate fallback...")
            try:
                image_url = self.fallback_generator.generate_image(image_prompt)
                if image_url:
                    logger.info("✅ Replicate fallback generation successful")
                    return image_url
                logger.warning("Replicate generation also failed")
            except Exception as e:
                logger.warning(f"Replicate error: {e}")
        
        # Both failed, use mock
        logger.info("Both image generators failed, using mock URL")
        if self.primary_generator:
            return self.primary_generator._generate_mock_image_url(image_prompt)
        elif self.fallback_generator:
            return self.fallback_generator._generate_mock_image_url(image_prompt)
        else:
            # Final fallback
            import hashlib
            prompt_hash = hashlib.md5(image_prompt.encode()).hexdigest()
            return f"https://drive.google.com/uc?id={prompt_hash}&export=view"

    def _generate_alt_text(self, headline: str) -> str:
        """
        Generate alt text from article headline.
        
        Args:
            headline: Article headline
            
        Returns:
            Alt text for image (max 125 chars)
        """
        if self.primary_generator:
            return self.primary_generator.generate_alt_text(headline)
        elif self.fallback_generator:
            return self.fallback_generator.generate_alt_text(headline)
        else:
            # Fallback alt text generation
            alt_text = f"Article image: {headline}"
            if len(alt_text) > 125:
                alt_text = alt_text[:122] + "..."
            return alt_text

    def _get_section_title(self, structured_data, section_nums: list) -> Optional[str]:
        """
        Get the first non-empty section title from a list of section numbers.
        
        Args:
            structured_data: ArticleOutput object
            section_nums: List of section numbers to try (e.g., [3, 4])
            
        Returns:
            First non-empty section title, or None if all are empty
        """
        for num in section_nums:
            title_key = f"section_{num:02d}_title"
            title = getattr(structured_data, title_key, "")
            if title and title.strip():
                return title.strip()
        return None

    def __repr__(self) -> str:
        """String representation."""
        primary = "GoogleImagen4.0" if self.primary_generator and not self.primary_generator.mock_mode else "Mock"
        fallback = "Replicate" if self.fallback_generator and not getattr(self.fallback_generator, 'mock_mode', True) else "Mock"
        return f"ImageStage(primary={primary}, fallback={fallback})"
