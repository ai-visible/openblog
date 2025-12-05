# Article Generation Output Locations

## Where to Find Generated Articles

When you run `view_article.py` or the full workflow, articles are saved in multiple formats:

### 1. **JSON Format** (Structured Data)
**Location**: `generated_article.json` (project root)

Contains the full article as structured JSON with all fields:
- Headline, Subtitle, Teaser
- Direct Answer
- All sections (section_01_title, section_01_content, etc.)
- FAQs (faq_01_question, faq_01_answer, etc.)
- PAAs (paa_01_question, paa_01_answer, etc.)
- Sources
- Metadata

**View**: `cat generated_article.json | python3.13 -m json.tool`

### 2. **Markdown Format** (Human-Readable)
**Location**: `generated_article.md` (project root)

Contains the article formatted as Markdown with:
- All sections
- FAQs
- PAAs
- Sources
- Key Takeaways

**View**: `cat generated_article.md` or open in any markdown viewer

### 3. **HTML Format** (Production-Ready)
**Location**: `output/{job_id}/index.html`

Contains the complete HTML document with:
- Full article content
- JSON-LD schema markup (Article, FAQPage, Organization, BreadcrumbList)
- Styled HTML with CSS
- FAQ/PAA sections
- Citations
- Internal links
- Meta tags for SEO

**View**: Open `output/{job_id}/index.html` in a web browser

**Example paths**:
- `output/view-article-test/index.html`
- `output/e2e-test-full/index.html`
- `output/integration-test-001/index.html`

### 4. **Metadata JSON**
**Location**: `output/{job_id}/metadata.json`

Contains article metadata:
- Headline, slug
- Word count, read time
- Section count
- FAQ/PAA counts
- Citation count
- Publication date

**View**: `cat output/{job_id}/metadata.json | python3.13 -m json.tool`

### 5. **Article JSON** (in output folder)
**Location**: `output/{job_id}/article.json`

Same as `generated_article.json` but stored in the output folder.

## Quick Access Commands

```bash
# View latest JSON article
cat generated_article.json | python3.13 -m json.tool | less

# View latest Markdown article
cat generated_article.md | less

# View latest HTML article (open in browser)
open output/view-article-test/index.html

# List all generated articles
ls -lh output/*/index.html

# View metadata
cat output/view-article-test/metadata.json | python3.13 -m json.tool
```

## Console Output

When running `view_article.py`, you'll also see:
- Full article printed to console (all sections)
- Word count
- Deep research confirmation
- AEO score (if full workflow)
- Execution times
- File save locations

## Full Workflow Output

When running `test_full_blog_generation_e2e.py`, additional output:
- `e2e_test_results.json` - Test results with metrics
- Console output with verification checklist
- All quality metrics (AEO score, critical issues, etc.)

