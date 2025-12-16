# PDF Margins Fix

**Date:** 2025-12-16  
**Issue:** PDF export needs margins/padding on all sides

---

## Fix Applied ✅

### Added PDF Margins

**File:** `pipeline/processors/article_exporter.py`

**Changes:**

1. **PDF Service Payload Margins:**
   ```python
   "margin": {
       "top": "25mm",
       "right": "20mm",
       "bottom": "25mm",
       "left": "20mm"
   }
   ```

2. **CSS @page Rules:**
   Added `_add_pdf_margins()` method that injects CSS:
   ```css
   @page {
       margin: 25mm 20mm;
   }
   body {
       padding: 20px;
   }
   ```

### Margin Settings

- **Top/Bottom:** 25mm (0.98 inches)
- **Left/Right:** 20mm (0.79 inches)
- **Body Padding:** 20px additional spacing

### Result

✅ PDFs will now have proper margins on all sides:
- Top: 25mm
- Bottom: 25mm  
- Left: 20mm
- Right: 20mm
- Plus 20px body padding for additional spacing

---

## Status

✅ **PDF margins added and ready for testing**

