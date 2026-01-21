# Genso Pen Pipeline Analysis

This document provides a detailed analysis of the business logic and implementation for each stage in the OpenBlog Neo pipeline.

## Stage 1: Set Context
**Goal**: Establish the "Ground Truth" and strategic foundation for the entire batch.

### Business Logic
1.  **Context Discovery**:
    *   Unlike generic writing tools, this stage first "learns" about the target company.
    *   It inputs the company URL into `OpenContext` (an AI module), which utilizes Google Search and Gemini to extract the Unique Selling Proposition (USP), target audience, product lines, and brand description.
2.  **Voice Cloning**:
    *   If existing blog posts are found in the sitemap, the system samples 3+ articles.
    *   It analyzes tone, sentence structure, and vocabulary (e.g., distinguishing between "professional & authoritative" vs. "casual & witty").
    *   This analysis results in a `VoicePersona` object used to guide generation in later stages.
3.  **Sitemap Mapping**:
    *   Crawls the existing website to build a comprehensive map of internal resources (products, services, existing blogs).
    *   This map is crucial for **Stage 5** (Internal Linking) to ensure new content connects to legacy content.
4.  **Job Preparation**:
    *   Converts input keywords into concrete `ArticleJob` objects, assigning URL slugs and specific writing instructions for each.

### Key Files
*   `stage1/stage_1.py`: Main orchestration for the stage.
*   `stage1/opencontext.py`: AI-driven company research module.
*   `stage1/voice_enhancer.py`: Logic for analyzing and cloning writing style.

---

## Stage 2: Blog Generation + Images
**Goal**: Generate the core content assets (Text + Visuals) in parallel.

### Business Logic
1.  **Deep Research Writing**:
    *   Uses Gemini (via `BlogWriter`) to write comprehensive articles (defaulting to 2000+ words).
    *   Structures content with proper HTML headings (`<h2>`, `<h3>`), bullet points, FAQ sections, and "People Also Ask" blocks to target SEO rich snippets.
2.  **Visual Generation**:
    *   Runs in **parallel** with text generation to optimize throughput.
    *   Constructs specific image prompts based on the article's topic and the Brand Visual Identity derived in Stage 1.
    *   Calls Google Imagen to generate 3 unique assets per article:
        *   **Hero Image**: For the top of the post.
        *   **Mid-article Image**: To break up dense text.
        *   **Bottom Image**: Often a Call-to-Action visual.
3.  **YouTube Integration**:
    *   If the AI suggests a video, the system validates that it is a proper YouTube URL format.
    *   Invalid URLs are automatically removed to prevent broken embedded players.

### Key Files
*   `stage2/stage_2.py`: Main orchestration for generation.
*   `stage2/blog_writer.py`: Handles prompting and text generation logic.
*   `stage2/image_creator.py`: Interface for Google Imagen and asset management.

---

## Stage 3: Quality Check
**Goal**: "De-robotize" the content and enforce Brand Voice.

### Business Logic
1.  **Surgical Editing**:
    *   Instead of rewriting the entire article (which risks introducing new hallucinations), this stage uses a **Structured Schema** approach.
    *   It asks Gemini to return a JSON list of specific deviations found in the text.
2.  **Find & Replace**:
    *   Performs exact string matching to find "robotic" phrases (e.g., "In the fast-paced world of...") and replaces them with more human-sounding alternatives defined by the `VoicePersona`.
3.  **Constraint Enforcement**:
    *   Explicitly checks for "Banned Words" or style violations defined in the context settings.
4.  **Safety Cap**:
    *   Limits edits to ~20 per article to prevent over-engineering or degrading the original cohesive structure.

### Key Files
*   `stage3/stage_3.py`: Logic for processing the critique and applying fixes.
*   `stage3/stage3_models.py`: Data models for quality validation.

---

## Stage 4: URL Verification
**Goal**: Ensure 100% technical accuracy and reference validity.

### Business Logic
1.  **Extraction & Testing**:
    *   Regex-scrapes every URL in the generated content (including citations, footnotes, and in-text links).
    *   Performs asynchronous HTTP `HEAD` or `GET` requests to verify they return a `200 OK` status.
2.  **Content Relevance (Optional)**:
    *   Can optionally read the content of the linked page to ensure it arguably supports the claim made in the article context.
3.  **Auto-Remediation**:
    *   **Dead Link Handling**: If a link returns a 404, it triggers an AI search agent to find a *working* replacement URL for the exact same topic.
    *   **Smart Replacement**: Updates the HTML `href` attribute while preserving the original natural anchor text.
    *   **Fallback**: If no replacement is found, it cleanly removes the anchor tag (leaving the plain text) or deletes the citation line entirely so the reader never encounters a broken experience.

### Key Files
*   `stage4/stage_4.py`: Main verification pipeline.
*   `stage4/url_verifier.py`: AI logic for finding replacement URLs.
*   `stage4/http_checker.py`: Async HTTP client for batch checking status codes.

---

## Stage 5: Internal Links
**Goal**: Maximize SEO value by interconnecting the content ecosystem.

### Business Logic
1.  **Link Pooling**:
    *   Aggregates a pool of linkable assets from two distinct sources:
        1.  **Legacy Content**: Relevant pages found during the Stage 1 Sitemap scan (Products, Service pages, old blogs).
        2.  **Batch Siblings**: Other articles being generated *in the current run* (enabling immediate cross-linking between new posts).
2.  **Contextual Embedding**:
    *   Feeds the article text and the Link Pool to Gemini.
    *   The model analyzes the prose to find *natural* phrases to turn into links (e.g., turning "Check out our latest AI tools" into a link to `/products/ai-tool`).
3.  **DOM Safety**:
    *   Uses strict regex and logic checks to ensure it *never* breaks HTML structure.
    *   Prevents inserting links inside Header tags (`<h1>`, etc.) or inside other existing links (`<a>`), ensuring valid HTML output.

### Key Files
*   `stage5/stage_5.py`: Logic for identifying anchor text and embedding links.
*   `stage5/stage5_models.py`: Data structures for link candidates and embeddings.
