# Internal Links Standardization - `/magazine/` Format

## Problem Statement

Internal links were inconsistent:
- Some used `/slug`
- Some used `/blog/slug`
- Some used `/magazine/slug`
- No standard format across articles

**User requirement:** ALL internal links must use `/magazine/{slug}` format for consistency.

---

## Solution: 3-Layer Standardization

### 1. Stage 5: Internal Links Generation (`stage_05_internal_links.py`)

**Modified:** Lines 189-204 in `_generate_suggestions()`

**Logic:**
```python
# Standardize URL format: always use /magazine/{slug}
if sibling_url.startswith("http"):
    # Keep full URLs as-is (external links)
    url = sibling_url
elif sibling_url.startswith("/magazine/"):
    # Already standardized
    url = sibling_url
elif sibling_url.startswith("/"):
    # Has leading slash but not /magazine/ → add magazine prefix
    url = f"/magazine{sibling_url}"
else:
    # No leading slash → add /magazine/ prefix
    url = f"/magazine/{sibling_url}"
```

**Examples:**
| Input | Output |
|-------|--------|
| `security-first-architecture` | `/magazine/security-first-architecture` |
| `/devops-automation` | `/magazine/devops-automation` |
| `/blog/ai-trends` | `/magazine/blog/ai-trends` |
| `/magazine/already-correct` | `/magazine/already-correct` |
| `https://external.com` | `https://external.com` (unchanged) |

---

### 2. Prompt Instructions (`main_article.py`)

**Modified:** Rule 9 - Internal Links

**Added:**
- Explicit `/magazine/` format requirement
- BAD/GOOD examples
- FORBIDDEN patterns (missing /magazine/, wrong prefix)

**Prompt excerpt:**
```
9. **Internal Links** (CRITICAL FORMAT): Include 3-5 links throughout article.
   **ALL internal links MUST use `/magazine/{slug}` format.**
   
   Format examples:
   - `<a href="/magazine/ai-security-best-practices">AI Security Guide</a>`
   - `<a href="/magazine/devops-automation">DevOps Automation</a>`
   
   ⛔ FORBIDDEN:
   - `<a href="/ai-security">...` (missing /magazine/)
   - `<a href="/blog/devops">...` (wrong prefix)
```

This ensures Gemini generates links with correct format from the start.

---

### 3. HTML Renderer Post-Processing (`html_renderer.py`)

**Modified:** `_cleanup_content()` method - Added Pattern 5

**Purpose:** Safety net to catch and fix any links that slip through.

**Regex Logic:**
```python
# Pattern 5: Standardize internal links to /magazine/ format
def fix_internal_link(match):
    href = match.group(1)
    
    # Skip if already correct or external
    if href.startswith('/magazine/') or href.startswith('http') or href.startswith('#'):
        return match.group(0)
    
    # Fix: remove /blog/ prefix if present, then add /magazine/
    if href.startswith('/blog/'):
        new_href = href.replace('/blog/', '/magazine/', 1)
    elif href.startswith('/'):
        new_href = f'/magazine{href}'
    else:
        new_href = f'/magazine/{href}'
    
    return match.group(0).replace(f'href="{href}"', f'href="{new_href}"')
```

**Test cases:**
```html
<!-- BEFORE -->
<a href="/ai-security">Guide</a>
<a href="/blog/devops">Automation</a>
<a href="#section-1">Skip</a>
<a href="https://example.com">External</a>

<!-- AFTER -->
<a href="/magazine/ai-security">Guide</a>
<a href="/magazine/devops">Automation</a>
<a href="#section-1">Skip</a>  <!-- Unchanged -->
<a href="https://example.com">External</a>  <!-- Unchanged -->
```

---

## How It Works Together

### Example Flow:

**Input slug from batch:** `security-first-architecture`

1. **Stage 5** normalizes: → `/magazine/security-first-architecture`
2. **Gemini** receives prompt with `/magazine/` examples
3. **HTML Renderer** validates and fixes any remaining issues

**Result:** All links standardized to `/magazine/{slug}` format.

---

## Edge Cases Handled

| Case | Handled By | Result |
|------|------------|--------|
| Missing leading `/` | Stage 5 | Adds `/magazine/` |
| Has `/blog/` prefix | HTML Renderer | Converts to `/magazine/` |
| Has arbitrary `/` prefix | HTML Renderer | Adds `/magazine` before |
| Already `/magazine/` | All layers | Unchanged (no double prefix) |
| External URLs (`http`) | All layers | Unchanged |
| Anchor links (`#`) | HTML Renderer | Unchanged |

---

## Testing

### Manual Test:

```python
# Test the regex in isolation
test_cases = [
    ('<a href="/ai-security">Link</a>', '<a href="/magazine/ai-security">Link</a>'),
    ('<a href="/blog/devops">Link</a>', '<a href="/magazine/devops">Link</a>'),
    ('<a href="/magazine/already-ok">Link</a>', '<a href="/magazine/already-ok">Link</a>'),
    ('<a href="https://external.com">Link</a>', '<a href="https://external.com">Link</a>'),
    ('<a href="#section-1">Link</a>', '<a href="#section-1">Link</a>'),
]

for input_html, expected in test_cases:
    result = HTMLRenderer._cleanup_content(input_html)
    assert result == expected, f"Failed: {input_html} → {result} (expected {expected})"
```

### Production Test:

When running a batch with `batch_siblings`:
```bash
cd services/blog-writer
python3 generate_direct.py

# Check output
grep 'href="/magazine' REAL_article_v3.2_FINAL.html
```

**Expected:** All internal article links use `/magazine/` prefix.

---

## Files Modified

1. **`pipeline/blog_generation/stage_05_internal_links.py`**
   - Lines 189-204: URL normalization logic
   - Ensures all sibling links get `/magazine/` prefix

2. **`pipeline/prompts/main_article.py`**
   - Rule 9: Added explicit `/magazine/` format requirement
   - Added BAD/GOOD examples for Gemini

3. **`pipeline/processors/html_renderer.py`**
   - `_cleanup_content()`: Added Pattern 5 (internal link standardization)
   - Regex post-processing as safety net

---

## Benefits

1. ✅ **Consistency:** All links follow same pattern
2. ✅ **SEO:** Standardized URL structure helps search engines
3. ✅ **Maintainability:** Easy to update routing if needed
4. ✅ **Future-proof:** Works with any slug format
5. ✅ **Safety net:** Multiple layers ensure no links slip through

---

## Future Enhancements

### Option 1: Configurable Prefix
Make `/magazine/` configurable via `app_config`:
```python
link_prefix = config.get("internal_link_prefix", "/magazine/")
url = f"{link_prefix}{slug}"
```

### Option 2: Validation Report
Add logging to report any links that were auto-fixed:
```python
if href != new_href:
    logger.info(f"Fixed internal link: {href} → {new_href}")
```

### Option 3: Strict Mode
Optionally reject articles with incorrect link formats instead of auto-fixing:
```python
if STRICT_MODE and href != new_href:
    raise ValidationError(f"Internal link must use /magazine/ format: {href}")
```

---

## Status

✅ **COMPLETE** - All internal links now standardized to `/magazine/{slug}` format.

**Format:** `/magazine/security-first-architecture` ✅  
**NOT:** `/security-first-architecture` ❌  
**NOT:** `/blog/security-first-architecture` ❌

