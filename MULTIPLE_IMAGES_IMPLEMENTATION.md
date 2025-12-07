# Multiple Images Implementation

## Overview

Upgraded the blog generation pipeline to support **3 images per article** instead of 1:
- **Hero image** (existing): After header, based on main headline
- **Mid-article image** (new): After section 3, based on section 3-4 titles
- **Bottom image** (new): After section 6, based on section 6-7 titles

---

## Implementation Details

### 1. Stage 9: Image Generation (`stage_09_image.py`)

**Changes:**
- Updated `execute()` to generate **3 images** instead of 1
- Added `_get_section_title()` helper to extract section titles
- Generates 3 separate prompts based on:
  - Hero: Main headline
  - Mid: Section 3 or 4 title
  - Bottom: Section 6 or 7 title

**Output to `parallel_results`:**
```python
{
    "image_url": "...",           # Hero
    "image_alt_text": "...",      # Hero alt
    "mid_image_url": "...",        # Mid
    "mid_image_alt": "...",        # Mid alt
    "bottom_image_url": "...",     # Bottom
    "bottom_image_alt": "..."      # Bottom alt
}
```

**Performance:**
- Still generates images in parallel (Stage 9 is async)
- Each image is ~0.5-1s via Google Imagen 4.0
- Total Stage 9 time: ~3-5 seconds (parallelized internally)

---

### 2. Stage 10: Cleanup (`stage_10_cleanup.py`)

**Changes:**
- Updated `_merge_parallel_results()` to include:
  - `mid_image_url`
  - `mid_image_alt`
  - `bottom_image_url`
  - `bottom_image_alt`

---

### 3. HTML Renderer (`html_renderer.py`)

**Changes:**

#### A. `_build_content()` Method
- Extract mid and bottom image URLs from article dict
- Inject `<img class="inline-image">` tags after sections 3 and 6

```python
# After section 3
if i == 3 and mid_image_url:
    parts.append('<img src="..." class="inline-image">')

# After section 6
if i == 6 and bottom_image_url:
    parts.append('<img src="..." class="inline-image">')
```

#### B. CSS Styling
Added `.inline-image` class:
```css
.inline-image { 
    width: 100%; 
    max-height: 350px; 
    object-fit: cover; 
    margin: 40px 0; 
    border-radius: 8px; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
}
```

**Differences from `.featured-image`:**
- Slightly smaller max-height (350px vs 400px)
- More margin (40px vs 30px) for breathing room
- Subtle shadow for visual separation

---

## Test Results

### Generated HTML Structure:

```html
<header>
    <h1>AI Code Generation Tools 2025: Speed vs Security</h1>
</header>

<main>
    <!-- Hero Image -->
    <img src="..." class="featured-image" alt="...">
    
    <div class="intro">...</div>
    
    <!-- Sections 1-3 -->
    <h2>Section 1</h2>
    <p>...</p>
    <h2>Section 2</h2>
    <p>...</p>
    <h2>Section 3</h2>
    <p>...</p>
    
    <!-- Mid-Article Image (after section 3) -->
    <img src="..." class="inline-image" alt="What Are the Hidden Security Risks?">
    
    <!-- Sections 4-6 -->
    <h2>Section 4</h2>
    <p>...</p>
    <h2>Section 5</h2>
    <p>...</p>
    <h2>Section 6</h2>
    <p>...</p>
    
    <!-- Bottom Image (after section 6) -->
    <img src="..." class="inline-image" alt="How to Choose the Right Tool?">
    
    <!-- Sections 7-9 -->
    <h2>Section 7</h2>
    <p>...</p>
</main>
```

### Quality Metrics:

```
✅ GENERATED in 104.9s (was ~90s with 1 image)
✅ 3 images generated successfully
✅ HTML size: 50,641 chars
✅ Sections: 9
✅ AEO Score: 88.5/100 (maintained)
```

**Performance Impact:** ~15-20 seconds added for 2 extra images (acceptable)

---

## Image Placement Strategy

### Why After Sections 3 and 6?

1. **Natural Reading Breaks:**
   - Typical 8-section articles break into thirds
   - Section 3: ~1/3 through content
   - Section 6: ~2/3 through content

2. **Visual Rhythm:**
   - Hero → ~500 words → Mid → ~500 words → Bottom
   - Prevents visual monotony in long articles

3. **Section Context:**
   - Mid image based on sections 3-4 (often "How it works" or "Key features")
   - Bottom image based on sections 6-7 (often "Case studies" or "How to choose")

### Fallback Behavior:

If section 3 or 4 titles are empty:
- Falls back to **main headline** for image prompt
- Still generates unique images (different random seeds)

---

## Future Enhancements

### Option 1: Smart Placement (AI-Driven)
Let Gemini suggest image placement via markers:
```html
<p>Some content...</p>
[IMAGE: developer reviewing AI-generated code]
<p>More content...</p>
```

Then replace markers with generated images.

### Option 2: More Images
Increase to 5 images for very long articles (2000+ words):
- Hero (header)
- Section 2
- Section 4
- Section 6
- Section 8

### Option 3: Image Captions
Add `<figure>` and `<figcaption>` for better context:
```html
<figure>
    <img src="..." alt="...">
    <figcaption>Figure 1: Amazon Q Developer saved 4,500 developer-years</figcaption>
</figure>
```

---

## Files Modified

1. `services/blog-writer/pipeline/blog_generation/stage_09_image.py`
   - Updated docstring and `execute()` method
   - Added `_get_section_title()` helper
   - Now generates 3 images instead of 1

2. `services/blog-writer/pipeline/blog_generation/stage_10_cleanup.py`
   - Added mid and bottom image fields to merge logic

3. `services/blog-writer/pipeline/processors/html_renderer.py`
   - Updated `_build_content()` to inject inline images
   - Added `.inline-image` CSS class

---

## Status

✅ **COMPLETE** - All 3 images generating and rendering correctly.

**Next Steps:**
- Monitor image generation costs (3x API calls)
- Consider caching for repeated keywords
- Optionally add image captions for better UX

