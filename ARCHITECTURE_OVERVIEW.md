# Pipeline Architecture Overview

**Complete architecture map of blog-writer**

---

## 🏗️ High-Level Architecture

```
blog-writer/
│
├── 📦 KEYWORD GENERATION (pipeline/keyword_generation/)
│   └── Standalone keyword research system
│
├── 📝 BLOG GENERATION (pipeline/blog_generation/)
│   └── 12-stage pipeline for article creation
│
├── 🔧 CORE INFRASTRUCTURE (pipeline/core/)
│   └── Workflow orchestration engine
│
└── 🛠️ SUPPORTING MODULES
    ├── pipeline/models/          # Data models & API clients
    ├── pipeline/processors/      # Data processors (sitemap, citations, etc.)
    ├── pipeline/prompts/         # Prompt templates
    └── pipeline/integrations/    # External API integrations
```

---

## 1️⃣ KEYWORD GENERATION (`pipeline/keyword_generation/`)

**Location**: `/pipeline/keyword_generation/`

**Purpose**: Generate SEO keywords for companies

**Architecture**:
```
pipeline/keyword_generation/
├── generator.py              # Main orchestrator (KeywordGeneratorV2)
├── ai_generator.py           # AI-based keyword generation
├── scorer.py                 # Keyword scoring with AI
├── adapter.py                # Adapter for different keyword sources
├── models.py                 # Data models (Keyword, CompanyInfo, etc.)
├── config.py                # Configuration
└── exceptions.py             # Custom exceptions
```

**Flow**:
```
1. Company Info Input
   ↓
2. AI Generator (50% keywords)
   ├── Seed keywords
   └── Long-tail expansion
   ↓
3. Gap Analyzer (50% keywords)
   ├── Competitor analysis
   └── SERanking API
   ↓
4. Merge & Deduplicate
   ↓
5. AI Scoring (all keywords)
   ↓
6. Filter & Sort
   ↓
7. Return KeywordGenerationResult
```

**Key Classes**:
- `KeywordGeneratorV2` - Main orchestrator
- `AIKeywordGenerator` - Generates keywords via Gemini
- `KeywordScorer` - Scores keywords with AI
- `GapAnalyzerWrapper` - Wraps SERanking API

**Integration Points**:
- `pipeline/integrations/seranking/` - SERanking API client
- `pipeline/models/gemini_client.py` - Gemini API for AI generation

**Usage**:
```python
from v2.keyword_generation import KeywordGeneratorV2

generator = KeywordGeneratorV2(
    google_api_key="...",
    seranking_api_key="..."
)

result = await generator.generate(
    company_info=CompanyInfo(name="...", url="..."),
    config=KeywordGenerationConfig()
)
```

---

## 2️⃣ BLOG GENERATION (`pipeline/blog_generation/`)

**Location**: `/pipeline/blog_generation/`

**Purpose**: Generate complete blog articles via 12-stage pipeline

**Architecture**:
```
pipeline/blog_generation/
├── stage_00_data_fetch.py      # Sequential: Fetch company data, sitemap
├── stage_01_prompt_build.py    # Sequential: Build prompt with variables
├── stage_02_gemini_call.py     # Sequential: Generate content (Gemini + tools)
├── stage_03_extraction.py      # Sequential: Extract structured data
├── stage_04_citations.py       # PARALLEL: Validate citations
├── stage_05_internal_links.py  # PARALLEL: Generate internal links
├── stage_06_toc.py             # PARALLEL: Table of contents
├── stage_07_metadata.py        # PARALLEL: Calculate metadata
├── stage_08_faq_paa.py         # PARALLEL: FAQ/PAA validation
├── stage_09_image.py           # PARALLEL: Generate image
├── stage_10_cleanup.py         # Sequential: Merge & validate
└── stage_11_storage.py         # Sequential: HTML & storage
```

**Execution Flow**:
```
┌─────────────────────────────────────────────────────────┐
│ SEQUENTIAL PHASE 1: Foundation (Stages 0-3)            │
└─────────────────────────────────────────────────────────┘

Stage 0: Data Fetch
  ├── Fetch company info from URL
  ├── Crawl sitemap (SitemapCrawler)
  └── Load job config
  ↓
Stage 1: Prompt Build
  ├── Load prompt template
  ├── Inject variables (keyword, company info, etc.)
  └── Create final prompt
  ↓
Stage 2: Gemini Call
  ├── Call Gemini 3 Pro with tools
  ├── Tools: googleSearch + urlContext
  └── Generate raw article (text/plain with JSON)
  ↓
Stage 3: Extraction
  ├── Parse JSON from text
  ├── Extract structured data
  └── Validate structure

┌─────────────────────────────────────────────────────────┐
│ PARALLEL PHASE 2: Enhancements (Stages 4-9)            │
└─────────────────────────────────────────────────────────┘

Stage 4: Citations          │  Stage 5: Internal Links
  ├── Validate URLs          │    ├── Generate "More Reading"
  ├── Check accessibility     │    └── Link to sitemap pages
  └── Format citations       │
                             │
Stage 6: ToC                 │  Stage 7: Metadata
  ├── Extract headers         │    ├── Calculate read time
  └── Generate ToC labels     │    └── Set publish date
                             │
Stage 8: FAQ/PAA             │  Stage 9: Image
  ├── Validate Q&A           │    ├── Generate prompt
  └── Enhance if needed       │    └── Generate image (Replicate)

┌─────────────────────────────────────────────────────────┐
│ SEQUENTIAL PHASE 3: Finalization (Stages 10-11)        │
└─────────────────────────────────────────────────────────┘

Stage 10: Cleanup
  ├── Merge parallel results
  ├── Validate completeness
  └── Final quality checks
  ↓
Stage 11: Storage
  ├── Generate HTML
  ├── Store in Supabase
  └── Return final article
```

**Key Classes**:
- Each stage inherits from `Stage` base class
- All stages receive/return `ExecutionContext`
- Stages 4-9 run in parallel via `asyncio.gather()`

**Integration Points**:
- `pipeline/core/workflow_engine.py` - Orchestrates execution
- `pipeline/models/gemini_client.py` - Gemini API calls
- `pipeline/processors/sitemap_crawler.py` - Sitemap crawling (Stage 0)
- `pipeline/processors/citation_sanitizer.py` - Citation validation (Stage 4)
- `pipeline/processors/html_renderer.py` - HTML generation (Stage 11)
- `pipeline/prompts/main_article.py` - Prompt templates (Stage 1)

**Usage**:
```python
from v2.core import WorkflowEngine

engine = WorkflowEngine()
context = await engine.execute(
    job_id="blog-123",
    job_config={
        "primary_keyword": "AI adoption",
        "company_url": "https://example.com",
    }
)
```

---

## 3️⃣ CORE INFRASTRUCTURE (`pipeline/core/`)

**Location**: `/pipeline/core/`

**Purpose**: Workflow orchestration and execution context

**Architecture**:
```
pipeline/core/
├── workflow_engine.py        # Main orchestrator
└── execution_context.py       # Shared data model
```

**WorkflowEngine**:
- Registers all 12 stages
- Executes stages in correct order (sequential → parallel → sequential)
- Handles errors and retries
- Manages execution context

**ExecutionContext**:
- Shared data model passed between stages
- Contains all intermediate results
- Fields: `prompt`, `raw_article`, `structured_data`, `citations`, etc.

---

## 4️⃣ SUPPORTING MODULES

### Models (`pipeline/models/`)
- `gemini_client.py` - Gemini API wrapper
- `sitemap_page.py` - SitemapPage, SitemapPageList models
- `citation.py` - Citation models
- `toc.py` - Table of contents models
- `metadata.py` - Metadata models
- `faq_paa.py` - FAQ/PAA models
- `image_generator.py` - Image generation client

### Processors (`pipeline/processors/`)
- `sitemap_crawler.py` - **Sitemap crawling** (used in Stage 0)
- `citation_sanitizer.py` - Citation validation (Stage 4)
- `cleanup.py` - Content cleanup (Stage 10)
- `html_renderer.py` - HTML generation (Stage 11)
- `quality_checker.py` - Quality validation
- `storage.py` - Supabase storage

### Prompts (`pipeline/prompts/`)
- `main_article.py` - Main article generation prompt (Stage 1)
- `image_prompt.py` - Image generation prompt (Stage 9)

### Integrations (`pipeline/integrations/`)
- `seranking/` - SERanking API client (for keyword generation)

---

## 🔄 Data Flow

### Keyword Generation Flow
```
Input: CompanyInfo
  ↓
KeywordGeneratorV2.generate()
  ├── AI Generator → 40 keywords
  ├── Gap Analyzer → 40 keywords
  ├── Merge & Deduplicate
  ├── Score all keywords
  └── Filter & Sort
  ↓
Output: KeywordGenerationResult
```

### Blog Generation Flow
```
Input: JobConfig (keyword, company_url, etc.)
  ↓
WorkflowEngine.execute()
  ├── Stage 0: Fetch data (sitemap, company info)
  ├── Stage 1: Build prompt
  ├── Stage 2: Generate content (Gemini + tools)
  ├── Stage 3: Extract structured data
  ├── Stages 4-9: Parallel enhancements
  ├── Stage 10: Cleanup & validate
  └── Stage 11: Generate HTML & store
  ↓
Output: ExecutionContext (with final_article)
```

---

## 📊 Key Differences: Pipeline vs V1

| Feature | V1 (src/) | Pipeline (pipeline/) |
|---------|-----------|----------|
| **Architecture** | Monolithic generators | 12-stage pipeline |
| **Keyword Gen** | Mixed with blog gen | Separate module |
| **Blog Gen** | Single ContentGenerator | 12 stages |
| **Sitemap** | Basic checker | Full crawler with classification |
| **Testing** | Limited | Comprehensive stage tests |
| **Modularity** | Low | High (each stage independent) |

---

## 🎯 Entry Points

### Keyword Generation
```python
from v2.keyword_generation import KeywordGeneratorV2

generator = KeywordGeneratorV2(...)
result = await generator.generate(company_info, config)
```

### Blog Generation
```python
from v2.core import WorkflowEngine

engine = WorkflowEngine()
context = await engine.execute(job_id, job_config)
```

### Combined (Future)
```python
# 1. Generate keywords
keywords = await keyword_generator.generate(...)

# 2. Generate blogs for each keyword
for keyword in keywords:
    blog = await workflow_engine.execute(job_id, {
        "primary_keyword": keyword.keyword,
        ...
    })
```

---

## 📁 Complete File Structure

```
pipeline/
├── core/
│   ├── workflow_engine.py          # Orchestrator
│   └── execution_context.py        # Shared data model
│
├── keyword_generation/              # KEYWORD GENERATION
│   ├── generator.py                # Main orchestrator
│   ├── ai_generator.py             # AI keyword gen
│   ├── scorer.py                   # Keyword scoring
│   ├── adapter.py                  # Source adapter
│   ├── models.py                   # Data models
│   └── config.py                   # Config
│
├── stages/                          # BLOG GENERATION (12 stages)
│   ├── stage_00_data_fetch.py      # Data fetch
│   ├── stage_01_prompt_build.py     # Prompt build
│   ├── stage_02_gemini_call.py      # Content generation
│   ├── stage_03_extraction.py      # Data extraction
│   ├── stage_04_citations.py       # Citations (parallel)
│   ├── stage_05_internal_links.py   # Internal links (parallel)
│   ├── stage_06_toc.py              # ToC (parallel)
│   ├── stage_07_metadata.py         # Metadata (parallel)
│   ├── stage_08_faq_paa.py         # FAQ/PAA (parallel)
│   ├── stage_09_image.py           # Image (parallel)
│   ├── stage_10_cleanup.py         # Cleanup
│   └── stage_11_storage.py         # Storage
│
├── models/                         # Data models & clients
│   ├── gemini_client.py            # Gemini API
│   ├── sitemap_page.py            # Sitemap models
│   ├── citation.py                # Citation models
│   └── ...
│
├── processors/                     # Data processors
│   ├── sitemap_crawler.py         # Sitemap crawler ⭐
│   ├── citation_sanitizer.py     # Citation validation
│   ├── html_renderer.py           # HTML generation
│   └── ...
│
├── prompts/                        # Prompt templates
│   ├── main_article.py            # Main prompt
│   └── image_prompt.py            # Image prompt
│
└── integrations/                   # External APIs
    └── seranking/                 # SERanking API
```

---

## ✅ Summary

**Keyword Generation**: `pipeline/keyword_generation/` - Standalone module  
**Blog Generation**: `pipeline/blog_generation/` - 12-stage pipeline  
**Orchestration**: `pipeline/core/workflow_engine.py` - Executes stages  
**Sitemap Crawler**: `pipeline/processors/sitemap_crawler.py` - Used in Stage 0

Both systems are **independent** but can be used together for complete blog generation workflows.

