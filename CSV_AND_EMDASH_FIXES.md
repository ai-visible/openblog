# CSV Content & Em Dash Fixes

**Date:** 2025-12-16  
**Issues Fixed:**
1. CSV missing full content sections (truncated at 500 chars)
2. Em dashes (—) appearing in output

---

## Issue 1: CSV Content Truncation ✅ FIXED

### Problem
CSV export was truncating section content at 500 characters, making it incomplete.

### Root Cause
**File:** `pipeline/processors/article_exporter.py` line 293
```python
rows.append([f"Section {i}", title, content[:500]])  # Truncate long content
```

### Fix Applied
Removed truncation to export full content:
```python
rows.append([f"Section {i}", title, content])  # Full content, no truncation
```

### Result
✅ CSV will now contain complete section content

---

## Issue 2: Em Dashes in Output ✅ FIXED

### Problem
Em dashes (—) and en dashes (–) were appearing in the output instead of regular hyphens (-).

### Root Cause
AI-generated content includes Unicode em/en dashes which are not standard ASCII hyphens.

### Fix Applied
**File:** `pipeline/blog_generation/stage_08_cleanup.py`

Added em/en dash replacement to `_encode_html_entities_in_content()`:
```python
# Replace em dashes (—) and en dashes (–) with regular hyphens (-)
encoded_text = re.sub(r'[—–]', '-', encoded_text)
```

**Implementation:**
- Uses minimal regex: `r'[—–]'` to match both em dash (—) and en dash (–)
- Replaces with regular hyphen (-)
- Applied to all HTML content fields
- Preserves HTML tags (only replaces in text content)

### Result
✅ All em/en dashes will be replaced with regular hyphens (-)

---

## Files Modified

1. `pipeline/processors/article_exporter.py` - Removed CSV content truncation
2. `pipeline/blog_generation/stage_08_cleanup.py` - Added em/en dash replacement

---

## Status

✅ **Both issues fixed and ready for testing**

