# Stage Descriptions

## Sequential Stages (0-3)

**Stage 0: Data Fetch & Auto-Detection**
- Fetches job config, auto-detects company info (name, URL, language)
- Applies user overrides
- Builds initial ExecutionContext
- **Time**: 0.0001s ✅

**Stage 1: Prompt Build**
- Constructs main article prompt with variable injection
- Injects keyword, company info, language, instructions
- **Time**: 0.0003s ✅

**Stage 2: Gemini Call**
- Calls Gemini 3 Pro API with tools (googleSearch + urlContext)
- Generates raw article content with deep research
- **Time**: 128.26s ⚠️ **BOTTLENECK**

**Stage 3: Extraction**
- Extracts JSON from raw article response
- Validates and normalizes with Pydantic models
- **Time**: 0.0023s ✅

## Parallel Stages (4-9) - Run concurrently

**Stage 4: Citations Validation**
- Validates citation URLs (HTTP HEAD requests)
- Formats citations as HTML
- **Time**: 3.63s ✅

**Stage 5: Internal Links**
- Extracts topics from article (headline + sections)
- Generates internal link suggestions from sitemap
- Filters competitors, deduplicates, formats as HTML
- **Time**: TBD

**Stage 6: Table of Contents**
- Extracts section titles
- Generates short navigation labels
- Creates ToC dictionary (toc_01, toc_02, ...)
- **Time**: TBD

**Stage 7: Metadata**
- Calculates word count
- Computes reading time
- Generates publication date
- **Time**: TBD

**Stage 8: FAQ/PAA**
- Extracts FAQ and PAA items from structured data
- Validates and deduplicates
- Enforces minimum counts (5-6 FAQ, 3-4 PAA)
- **Time**: TBD

**Stage 9: Image Generation**
- Generates image prompt from headline + company info
- Calls Replicate API (Stable Diffusion)
- Generates alt text
- **Time**: TBD (likely slow - API call)

## Sequential Stages (10-11)

**Stage 10: Cleanup & Validation**
- Cleans HTML and normalizes content
- Merges all parallel results (stages 4-9)
- Validates citations, runs quality checks
- Generates quality report
- **Time**: TBD

**Stage 11: HTML Generation & Storage**
- Renders final HTML with schemas
- Extracts metadata
- Stores article to Supabase
- **Time**: TBD

