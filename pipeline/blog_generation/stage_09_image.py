"""
Stage 9: Image Generation

Maps to v4.1 Phase 8, Steps 25-28: get-insights → image_empty? → execute_image_generation → store_image_in_blog

Generates article header image via Replicate API with detailed prompts.

Input:
  - ExecutionContext.structured_data (headline)
  - ExecutionContext.company_data (industry, description)
  - ExecutionContext.job_config (language)

Output:
  - ExecutionContext.parallel_results['image_url'] (CDN URL)
  - ExecutionContext.parallel_results['image_alt_text'] (max 125 chars)

Process:
1. Check if image_url already exists (conditional skip)
2. Get image generation insights from headline + company info
3. Call image generator (Replicate API)
4. Generate alt text from headline
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
    - Conditional skip (if image already exists)
    - Image prompt generation from headline + company info
    - Replicate API integration
    - Alt text generation
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
                logger.info("Using Google Imagen 4.0 for image generation")
            else:
                logger.info("Google Imagen in mock mode, will use fallback")
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
        Execute Stage 9: Generate article image.

        Input from context:
        - structured_data: ArticleOutput with headline
        - company_data: Company information
        - job_config: Job configuration with language

        Output to context:
        - parallel_results['image_url']: Image CDN URL
        - parallel_results['image_alt_text']: Alt text for image

        Args:
            context: ExecutionContext from parallel stages

        Returns:
            Updated context with parallel_results populated
        """
        logger.info(f"Stage 9: {self.stage_name}")

        # Validate input
        if not context.structured_data:
            logger.warning("No structured_data available for image generation")
            context.parallel_results["image_url"] = ""
            context.parallel_results["image_alt_text"] = ""
            return context

        # Check if image already exists (conditional skip)
        existing_image = getattr(context.structured_data, "image_url", None)
        if existing_image and existing_image.strip():
            logger.info(f"✅ Image already exists: {existing_image[:50]}...")
            context.parallel_results["image_url"] = existing_image
            # Generate alt text for existing image
            alt_text = self._generate_alt_text(context.structured_data.Headline)
            context.parallel_results["image_alt_text"] = alt_text
            return context

        headline = context.structured_data.Headline
        logger.info(f"Generating image for: {headline}")

        # Step 1: Generate image prompt from headline + company data
        image_prompt = generate_image_prompt(
            headline=headline,
            company_data=context.company_data,
            job_config=context.job_config,
        )
        logger.debug(f"Image prompt generated ({len(image_prompt)} chars)")

        # Step 2: Generate image with comprehensive error handling
        image_url = await self._generate_image_with_retry(image_prompt, context)

        # Step 3: Generate alt text
        alt_text = self._generate_alt_text(headline)

        # Store results in context
        context.parallel_results["image_url"] = image_url or ""
        context.parallel_results["image_alt_text"] = alt_text

        if image_url:
            logger.info(f"✅ Image generated successfully")
        else:
            logger.warning("⚠️  Image generation failed, continuing without image")

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
            logger.info("Attempting image generation with Google Imagen 4.0...")
            try:
                # Extract project folder ID if available
                project_folder_id = context.company_data.get("project_folder_id")
                image_url = self.primary_generator.generate_image(image_prompt, project_folder_id)
                if image_url:
                    logger.info("✅ Google Imagen 4.0 generation successful")
                    return image_url
                logger.warning("Google Imagen generation failed, trying fallback...")
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

    def __repr__(self) -> str:
        """String representation."""
        primary = "GoogleImagen4.0" if self.primary_generator and not self.primary_generator.mock_mode else "Mock"
        fallback = "Replicate" if self.fallback_generator and not getattr(self.fallback_generator, 'mock_mode', True) else "Mock"
        return f"ImageStage(primary={primary}, fallback={fallback})"
