# Input Data Requirements - Complete Reference

**Date**: 2025-11-19 (Updated: Simplified to company_url only)  
**Workflow**: Content Gen v4.1 → Python Implementation

---

## 🎯 Simplified Input Approach

**Key Change**: Only **2 fields** are required:
- ✅ `primary_keyword` - Main topic/keyword
- ✅ `company_url` - Company website URL

**Everything else is auto-detected** from `company_url`:
- Company name, location, language → Auto-detected from website
- Company info (industry, business model, products) → Auto-detected via Gemini analysis
- Internal links → Auto-fetched from sitemap

**Why**: Deep research (googleSearch + urlContext tools) already finds company info during content generation, so pre-providing it is redundant. Auto-detection simplifies the API and improves UX.

**Optional Overrides**: All auto-detected fields can be manually overridden if needed.

---

## Executive Summary

**Required Input**: Only **2 fields** are strictly required:
- ✅ `primary_keyword` - Main topic/keyword for the blog article
- ✅ `company_url` - Company website URL (used for auto-detection)

**Auto-Detected from `company_url`**:
- ✅ `company_name` - Auto-detected from website (page title, meta tags)
- ✅ `company_location` - Auto-detected from website (address, hreflang, geo tags)
- ✅ `company_language` - Auto-detected from website (`lang` attribute, content analysis)
- ✅ `company_info` - Auto-detected via Gemini analysis (industry, business model, products, features)
- ✅ `links` - Auto-fetched from sitemap (for internal links)

**Optional Override Fields**: All auto-detected fields can be manually overridden if needed  
**Optional Customization**: **20+ fields** for advanced customization

---

## Input Data Sources

### v4.1 Workflow (Supabase-based)
- **Source**: Supabase `rapid-service` endpoint
- **Fetches**: `company_data`, `blog_page`, `gpt_language`
- **Normalized to**: `get-company-info`, `get-input`, `gpt_language`

### Python Implementation (Direct API)
- **Source**: Direct API call with `InputSchema`
- **Can work with**: Minimal input (just `primary_keyword`)
- **Recommended**: Full company info for quality

---

## Required Fields (Minimum)

### ✅ **1. PRIMARY KEYWORD** (Required)

**v4.1 Path**: `get-input.primary_keyword`  
**Python**: `primary_keyword: str`

**Purpose**: Main topic/keyword for the blog article

**Example**:
```json
{
  "primary_keyword": "AI adoption in customer service"
}
```

**Usage**: 
- Used in headline generation
- Must appear in headline (required)
- Must appear in first 100 words
- Used throughout content (1-2% density)

---

### ✅ **2. COMPANY URL** (Required)

**v4.1 Path**: `get-company-info.company_url`  
**Python**: `company_url: str`

**Purpose**: Company website URL - used for:
- Auto-detecting company information (name, location, language, industry)
- Fetching sitemap for internal links
- Filtering citations (exclude company domain)
- Competitor filtering

**Example**: `"https://example.com"`

**Auto-Detection**: When `company_url` is provided, the system automatically:
1. Scrapes the website to extract company information
2. Detects company name from page title, meta tags, structured data
3. Detects company location from address, hreflang, geo tags
4. Detects company language from `lang` attribute and content analysis
5. Analyzes company info (industry, business model, products) via Gemini
6. Fetches sitemap to build internal links pool

**Note**: All auto-detected fields can be manually overridden if needed (see Optional Override Fields below).

---

## Auto-Detected Fields (From `company_url`)

These fields are **automatically detected** from `company_url` and do **not** need to be provided:

### 2a. Company Name (Auto-Detected)
- **v4.1**: `get-company-info.company_name` (from `company_info`)
- **Python**: `company_name: Optional[str]` (auto-detected)
- **Detection Method**: Page title, meta tags, structured data, logo text
- **Fallback**: `"the company"` if detection fails
- **Example**: `"Example Corp"` (detected from website)

### 2b. Company Language (Auto-Detected)
- **v4.1**: `get-company-info.company_language`
- **Python**: `company_language: str` (auto-detected, default: `"en"`)
- **Detection Method**: `lang` attribute, content analysis, hreflang tags
- **Fallback**: `"en"` if detection fails
- **Example**: `"de"`, `"en"`, `"fr"` (detected from website)

### 2c. Company Location (Auto-Detected)
- **v4.1**: `get-company-info.company_location`
- **Python**: `company_location: Optional[str]` (auto-detected)
- **Detection Method**: Address, hreflang, geo tags, pricing currency
- **Fallback**: `"global"` if detection fails
- **Example**: `"Germany"`, `"EU"`, `"United States"` (detected from website)

### 2d. Company Info (Auto-Detected)
- **v4.1**: `get-company-info.company_info` (JSON object)
- **Python**: `company_info: dict` (auto-detected via Gemini analysis)
- **Detection Method**: Gemini analyzes website content (homepage, about, products, pricing pages)
- **Extracted Fields**: Industry, business model, products, features, use cases, target audience, regions
- **Fallback**: `{}` if detection fails
- **Example**:
```json
{
  "industry": "SaaS",
  "focus": "Customer experience",
  "target_audience": "B2B",
  "products": ["Product A", "Product B"],
  "business_model": "B2B"
}
```

### 2e. Internal Links (Auto-Fetched)
- **v4.1**: `get-input.links`
- **Python**: `links: List[str]` (auto-fetched from sitemap)
- **Detection Method**: Fetches sitemap.xml, identifies blog/product pages
- **Fallback**: `[]` if sitemap not found
- **Example**: `["/product", "/features", "/pricing"]` (fetched from sitemap)

---

## Optional Override Fields

These fields are **auto-detected** but can be **manually overridden** if needed:

### 3a. Company Name Override
- **Python**: `company_name: Optional[str] = None`
- **Purpose**: Override auto-detected company name
- **When to Use**: If auto-detection is incorrect or you want a specific name
- **Example**: `"Example Corp"` (overrides auto-detection)

### 3b. Company Location Override
- **Python**: `company_location: Optional[str] = None`
- **Purpose**: Override auto-detected company location
- **When to Use**: If auto-detection is incorrect or you want a specific location
- **Example**: `"Germany"` (overrides auto-detection)

### 3c. Company Language Override
- **Python**: `company_language: Optional[str] = None`
- **Purpose**: Override auto-detected company language
- **When to Use**: If auto-detection is incorrect or you want a specific language
- **Example**: `"de"` (overrides auto-detection)

### 3d. Company Competitors (Optional)
- **v4.1**: `get-company-info.company_competitors`
- **Python**: `company_competitors: List[str]` (default: `[]`)
- **Purpose**: Explicitly exclude competitors from citations and links
- **Note**: Deep research (googleSearch + urlContext) will naturally find competitors during generation, so this is optional
- **Example**: `["competitor1.com", "competitor2.io"]`

---

### 3e. Content Generation Instructions (Optional)

**v4.1 Path**: `get-company-info.content_generation_instruction`  
**Python**: `content_generation_instruction: str` (default: `""`)

**Purpose**: Custom instructions for content generation (user-specific, cannot be auto-detected)

**Example**:
```
"Focus on B2B use cases, emphasize ROI, include case studies"
```

**Note**: This field cannot be auto-detected as it's user-specific. Defaults to empty string if not provided.

---

### 3f. Internal Links Override (Optional)

**v4.1 Path**: `get-input.links`  
**Python**: `links: List[str]` (default: `[]`, auto-fetched from sitemap)

**Purpose**: Override auto-fetched internal links (1 per H2 section)

**When to Use**: If you want specific links instead of auto-fetched ones

**Example**:
```json
["/product", "/features", "/pricing"]
```

**Note**: If not provided, links are auto-fetched from sitemap. If provided, overrides auto-fetched links.

---

### 3g. GPT Language Settings (Auto-Detected)

**v4.1 Path**: `gpt_language[0]` (array, first element)  
**Python**: Uses `company_language` (auto-detected from `company_url`)

**Purpose**: Language-specific instructions for GPT

**Note**: In v4.1, this is an array. Python uses `company_language` string (auto-detected from website).

---

## Optional Fields (For Customization)

### 6. **CONTENT SETTINGS**

#### 6a. Tonality
- **Python**: `tonality: Literal["professional", "casual", "conversational", "academic", "technical"]`
- **Default**: `"professional"`
- **Purpose**: Writing tone/style

#### 6b. Output Length
- **Python**: `output_length: Literal["short", "medium", "long"]`
- **Default**: `"medium"`
- **Word counts**:
  - `short`: 800-1200 words
  - `medium`: 1200-1800 words
  - `long`: 1800-2500 words

#### 6c. Writing Style
- **Python**: `writing_style: Literal["mckinsey", "journalistic", "blog", "academic", "casual"]`
- **Default**: `"mckinsey"`
- **Purpose**: Writing approach (v4.1 uses McKinsey/BCG style)

#### 6d. Scope
- **Python**: `scope: Optional[str]`
- **Purpose**: Additional scope description
- **Example**: `"EU focus; B2C and B2B; service interactions"`

---

### 7. **CONTENT SECTIONS (Include/Exclude)**

#### 7a. Include FAQ
- **Python**: `include_faq: bool` (default: `True`)
- **Purpose**: Include FAQ section (target: 5 items)

#### 7b. Include PAA
- **Python**: `include_paa: bool` (default: `True`)
- **Purpose**: Include People Also Ask section (target: 3 items)

#### 7c. Include Key Takeaways
- **Python**: `include_key_takeaways: bool` (default: `True`)
- **Purpose**: Include key takeaways section (3 items)

---

### 8. **SOURCES CONFIGURATION**

#### 8a. Min Sources
- **Python**: `min_sources: int` (default: `8`)
- **Purpose**: Minimum number of citations (v4.1: 8 minimum)

#### 8b. Max Sources
- **Python**: `max_sources: int` (default: `20`)
- **Purpose**: Maximum number of citations (v4.1: MAX 20)

---

### 9. **QUALITY SETTINGS**

#### 9a. Skip Two-Pass
- **Python**: `skip_two_pass: bool` (default: `False`)
- **Purpose**: Skip quality regeneration if issues found
- **Warning**: Reduces quality from 110% to ~95%

#### 9b. Min AEO Score
- **Python**: `min_aeo_score: float` (default: `65.0`)
- **Purpose**: Minimum AEO score threshold (0-100)
- **Behavior**: Content below this triggers regeneration

---

### 10. **SEO/AEO OPTIMIZATION**

#### 10a. Canonical URL
- **Python**: `canonical_url: Optional[str]`
- **Purpose**: Canonical URL for article (auto-generated if not provided)

#### 10b. Image URL
- **Python**: `image_url: Optional[str]`
- **Purpose**: Article featured image URL for Open Graph

#### 10c. Image Dimensions
- **Python**: `image_width: Optional[int]`, `image_height: Optional[int]`
- **Purpose**: Image dimensions for Open Graph

---

### 11. **E-E-A-T AUTHOR FIELDS**

#### 11a. Author Name
- **Python**: `author_name: Optional[str]`
- **Purpose**: Author name for E-E-A-T optimization

#### 11b. Author Bio
- **Python**: `author_bio: Optional[str]`
- **Purpose**: Author bio/credentials (50-200 words)

#### 11c. Author URL
- **Python**: `author_url: Optional[str]`
- **Purpose**: Author profile URL

#### 11d. Author Role
- **Python**: `author_role: Optional[str]`
- **Purpose**: Author role/title (e.g., "Senior Marketing Manager")

---

### 12. **KEYWORD RESEARCH INTEGRATION** (Optional Feature)

#### 12a. Enable Keyword Research
- **Python**: `enable_keyword_research: bool` (default: `False`)
- **Purpose**: Run keyword research before blog generation

#### 12b. Keyword Research Config
- **Python**: `keyword_research_config: Optional[dict]`
- **Fields**:
  - `keyword_count`: Number of keywords to research (default: 80)
  - `cluster_count`: Number of clusters (default: 6)
  - `min_score`: Minimum keyword score (default: 40)

#### 12c. Use Researched Keyword
- **Python**: `use_researched_keyword: bool` (default: `False`)
- **Purpose**: Use highest-scored researched keyword instead of `primary_keyword`

---

## Complete Input Schema Reference

### Minimal Input (Required Fields Only)
```json
{
  "primary_keyword": "AI marketing automation",
  "company_url": "https://example.com"
}
```

**Note**: All other fields are auto-detected from `company_url`. This is sufficient for content generation.

### Recommended Input (With Optional Overrides)
```json
{
  "primary_keyword": "AI marketing automation",
  "company_url": "https://example.com",
  
  // Optional overrides (if auto-detection is incorrect)
  "company_name": "Example Corp",  // Override auto-detected name
  "company_location": "Germany",  // Override auto-detected location
  "company_language": "de",        // Override auto-detected language
  
  // Optional customization
  "company_url": "https://example.com",
  "company_name": "Example Corp",
  "company_language": "en",
  "company_location": "Germany",
  "company_competitors": ["competitor1.com"],
  "company_info": {
    "industry": "SaaS",
    "focus": "Marketing automation"
  },
  "content_generation_instruction": "Focus on B2B use cases",
  "links": ["/product", "/features"]
}
```

### Full Input (Maximum customization)
```json
{
  "primary_keyword": "AI marketing automation",
  
  "company_url": "https://example.com",
  "company_name": "Example Corp",
  "company_language": "en",
  "company_location": "Germany",
  "company_competitors": ["competitor1.com", "competitor2.io"],
  "company_info": {
    "industry": "SaaS",
    "focus": "Marketing automation",
    "target_audience": "B2B"
  },
  
  "content_generation_instruction": "Focus on B2B use cases, emphasize ROI",
  "links": ["/product", "/features", "/pricing"],
  "scope": "EU focus; B2B",
  
  "tonality": "professional",
  "output_length": "medium",
  "writing_style": "mckinsey",
  
  "include_faq": true,
  "include_paa": true,
  "include_key_takeaways": true,
  
  "min_sources": 8,
  "max_sources": 20,
  
  "min_aeo_score": 65.0,
  "skip_two_pass": false,
  
  "canonical_url": "https://example.com/blog/ai-marketing-automation",
  "image_url": "https://example.com/images/ai-marketing.jpg",
  "image_width": 1200,
  "image_height": 630,
  
  "author_name": "John Doe",
  "author_bio": "Senior Marketing Manager with 10+ years experience...",
  "author_url": "https://example.com/about/john-doe",
  "author_role": "Senior Marketing Manager"
}
```

---

## Field Mapping: v4.1 → Python

| v4.1 Path | Python Field | Required? | Auto-Detected? | Default/Override |
|-----------|--------------|-----------|----------------|------------------|
| `get-input.primary_keyword` | `primary_keyword` | ✅ **YES** | ❌ No | - |
| `get-company-info.company_url` | `company_url` | ✅ **YES** | ❌ No | - |
| `get-company-info.company_name` | `company_name` | ⚠️ Optional | ✅ **YES** (from `company_url`) | Auto-detected or override |
| `get-company-info.company_language` | `company_language` | ⚠️ Optional | ✅ **YES** (from `company_url`) | Auto-detected or override |
| `get-company-info.company_location` | `company_location` | ⚠️ Optional | ✅ **YES** (from `company_url`) | Auto-detected or override |
| `get-company-info.company_competitors` | `company_competitors` | ⚠️ Optional | ❌ No (deep research finds them) | `[]` or override |
| `get-company-info.company_info` | `company_info` | ⚠️ Optional | ✅ **YES** (from `company_url` via Gemini) | Auto-detected or override |
| `get-company-info.content_generation_instruction` | `content_generation_instruction` | ⚠️ Optional | ❌ No (user-specific) | `""` or override |
| `get-input.links` | `links` | ⚠️ Optional | ✅ **YES** (from sitemap) | Auto-fetched or override |
| `gpt_language[0]` | `company_language` | ⚠️ Optional | ✅ **YES** (from `company_url`) | Auto-detected or override |

---

## What Happens with Missing Fields?

### Missing Required Fields
- **`primary_keyword`**: ❌ **ERROR** - Cannot generate article (required)
- **`company_url`**: ❌ **ERROR** - Cannot auto-detect company info (required)

### Auto-Detected Fields (Missing = Auto-Detected)
- **`company_name`**: ✅ **OK** - Auto-detected from website (fallback: `"the company"`)
- **`company_location`**: ✅ **OK** - Auto-detected from website (fallback: `"global"`)
- **`company_language`**: ✅ **OK** - Auto-detected from website (fallback: `"en"`)
- **`company_info`**: ✅ **OK** - Auto-detected via Gemini analysis (fallback: `{}`)
- **`links`**: ✅ **OK** - Auto-fetched from sitemap (fallback: `[]`)

### Optional Fields (Missing = Uses Default)
- **`company_competitors`**: ✅ **OK** - Defaults to `[]` (deep research finds competitors naturally)
- **`content_generation_instruction`**: ✅ **OK** - Defaults to `""` (no custom instructions)
- **All other optional fields**: ✅ **OK** - Uses defaults, still generates quality content

**Key Point**: With only `primary_keyword` + `company_url`, the system auto-detects everything else and generates quality content. Optional overrides are only needed if auto-detection is incorrect or you want specific values.

---

## Input Data Flow

### v4.1 Workflow (Supabase)
```
Supabase Database
  ├─ blog_pages table
  │   └─ Contains: primary_keyword, links, id, etc.
  │
  └─ company_data table
      └─ Contains: company_url, company_name, company_info, etc.
  ↓
get_supabase_information (HTTP Request)
  ├─ Returns: company_data, blog_page, gpt_language
  ↓
set_field_names (Normalize)
  ├─ Maps to: get-company-info, get-input, gpt_language
  ↓
create_prompt (Build prompt)
  └─ Uses all fields to build comprehensive prompt
```

### Python Implementation (Direct API)
```
API Request (InputSchema)
  ├─ primary_keyword (required)
  ├─ company_* fields (optional but recommended)
  └─ Other optional fields
  ↓
ContentGenerator.generate()
  ├─ Uses input_data directly
  └─ Builds prompt from InputSchema fields
```

---

## Summary Table

| Category | Fields | Required? | Impact if Missing |
|----------|--------|-----------|-------------------|
| **Core** | `primary_keyword` | ✅ **YES** | ❌ Cannot generate |
| **Company** | `company_url`, `company_name`, `company_language` | ⚠️ **Recommended** | ⚠️ Lower quality, generic output |
| **Content** | `content_generation_instruction`, `links` | ❌ Optional | ✅ Uses defaults |
| **Style** | `tonality`, `output_length`, `writing_style` | ❌ Optional | ✅ Uses defaults |
| **Sections** | `include_faq`, `include_paa`, `include_key_takeaways` | ❌ Optional | ✅ Uses defaults (all true) |
| **Quality** | `min_aeo_score`, `skip_two_pass` | ❌ Optional | ✅ Uses defaults |
| **SEO** | `canonical_url`, `image_url` | ❌ Optional | ✅ Auto-generated if missing |
| **E-E-A-T** | `author_*` fields | ❌ Optional | ✅ Not included if missing |

---

## Quick Reference

### Minimum Input (Works)
```json
{ "primary_keyword": "your keyword" }
```

### Recommended Input (Good Quality)
```json
{
  "primary_keyword": "your keyword",
  "company_url": "https://company.com",
  "company_name": "Company Name",
  "company_language": "en"
}
```

### Full Input (Maximum Quality)
```json
{
  "primary_keyword": "your keyword",
  "company_url": "https://company.com",
  "company_name": "Company Name",
  "company_language": "en",
  "company_location": "Germany",
  "company_competitors": ["competitor.com"],
  "company_info": {"industry": "SaaS"},
  "content_generation_instruction": "Custom instructions",
  "links": ["/product"]
}
```

---

**Conclusion**: Only `primary_keyword` is strictly required, but providing company information significantly improves output quality and personalization.

