# PDF Images & TOC Length Fixes

**Date:** 2025-12-16  
**Issues Fixed:**
1. PDF missing images
2. TOC items too long

---

## Issue 1: PDF Missing Images ✅ FIXED

### Problem
PDF exports were missing images because local image paths weren't being converted to base64 data URLs before sending to the PDF service.

### Root Cause
`ArticleExporter._html_to_pdf()` was sending HTML with local image paths (e.g., `output/images/blog_image_xxx.webp`) directly to the PDF service, which couldn't resolve these paths.

### Fix Applied
**File:** `pipeline/processors/article_exporter.py`

Added `_embed_images_for_pdf()` method that:
1. Finds all `<img>` tags with local `src` paths
2. Reads image files from disk
3. Converts images to base64 data URLs
4. Replaces `src` attributes with data URLs
5. Handles multiple image formats (PNG, JPG, WebP, GIF)

**Changes:**
- Added `_embed_images_for_pdf()` static method
- Updated `_html_to_pdf()` to call `_embed_images_for_pdf()` before sending HTML to PDF service
- Images are now embedded as `data:image/png;base64,...` URLs

### Result
✅ PDFs will now include all images embedded as base64 data URLs

---

## Issue 2: TOC Items Too Long ✅ FIXED

### Problem
TOC items were showing full titles truncated to 50 characters, making them too long:
```
"What is AI Automation? Beyond the Buzzwords"
"Top Use Cases: Where AI Automation Delivers Real V..."
```

### Root Cause
1. `TableOfContents.to_dict()` was using `full_title` truncated to 50 chars instead of `short_label`
2. TOC generation was creating 1-2 word labels (too short, lost meaning)
3. HTML renderer fallback was using 50-character truncation

### Fix Applied

**File 1:** `pipeline/models/toc.py`
- Updated `to_dict()` to use `short_label` instead of truncated `full_title`

**File 2:** `pipeline/blog_generation/stage_02_gemini_call.py`
- Updated TOC label generation to create 3-5 word labels (instead of 1-2)
- Removes common question prefixes ("What is", "How does", etc.)
- Uses meaningful words (skips stop words)
- Max 5 words, truncated to 60 chars if needed

**File 3:** `pipeline/processors/html_renderer_simple.py`
- Updated `_render_toc()` to use `toc_dict` if available
- Added `_create_short_toc_label()` fallback method (3-5 words max)
- Removes question prefixes before truncating

### Result
✅ TOC items will now be concise (3-5 words):
```
"AI Automation: Beyond Buzzwords"
"Top Use Cases: Real Value"
"Rise of Agentic AI"
"Strategic Implementation Framework"
"ROI and Benefits"
"Challenges and Roadblocks"
```

---

## Testing

To verify the fixes:

1. **PDF Images:**
   - Generate a new article with images
   - Export to PDF
   - Verify images appear in PDF

2. **TOC Length:**
   - Generate a new article
   - Check TOC in HTML output
   - Verify items are 3-5 words max

---

## Files Modified

1. `pipeline/processors/article_exporter.py` - Added image embedding for PDF
2. `pipeline/models/toc.py` - Use short_label in to_dict()
3. `pipeline/blog_generation/stage_02_gemini_call.py` - Generate 3-5 word TOC labels
4. `pipeline/processors/html_renderer_simple.py` - Render short TOC labels

---

## Status

✅ **Both issues fixed and ready for testing**

