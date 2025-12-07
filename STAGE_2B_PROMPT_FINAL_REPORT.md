# Stage 2b Prompt Engineering - Final Report

## 🎯 Objective

Strengthen Stage 2b prompts to ensure Gemini actually makes changes (removes em dashes, reduces keywords, expands paragraphs).

---

## ✅ What Was Done

### 1. Strengthened All 3 Prompts

**Improvements Made:**
- Added concrete BEFORE/AFTER HTML examples
- Added explicit em dash counts ("13 em dashes detected")
- Added step-by-step transformation guides
- Added validation checklists with exact counts
- Added "START OUTPUT NOW:" to prevent extra text
- Added visual structure with emoji headers
- Added "CRITICAL" markers for key requirements

**Files Modified:**
- `rewrite_prompts.py` - All 3 specialized prompts strengthened

---

## 📊 Test Results (Dec 7, 2025)

### Test Run #1 (Syntax Error)
```
SyntaxError: invalid character '✅' (U+2705)
```
**Cause:** Leftover code outside f-string  
**Fix:** Removed lines 256-277  
**Status:** ✅ Fixed

### Test Run #2 (Improved Prompts)
```
2025-12-07 02:43:25 - Stage 2b: Quality Refinement
2025-12-07 02:43:25 - WARNING: Found 13 em dashes (—) - AI marker
2025-12-07 02:43:25 - Rewriting all_content (mode=quality_fix)
2025-12-07 02:44:14 - ✅ API call succeeded (11122 chars)
2025-12-07 02:44:14 - ⚠️  Validation failed: Edit too minimal (similarity=1.00 > 0.95)
2025-12-07 02:44:59 - ✅ API call succeeded (11122 chars) [retry #2]
2025-12-07 02:44:59 - ⚠️  Validation failed: Edit too minimal (similarity=1.00 > 0.95)
2025-12-07 02:44:59 - ⚠️  Rewrite failed: Validation failed
2025-12-07 02:44:59 - ✅ Stage 2: Quality Refinement completed in 94.68s
```

**Status:** ❌ Gemini still returning identical content (similarity=1.00)

---

## 🔍 Root Cause Analysis

### Why Isn't Gemini Making Changes?

**Hypothesis 1: Conservative API Behavior**
- Gemini is being overly cautious
- Sees the "PRESERVE ALL" instructions and does exactly that
- Interprets "minimal changes" too literally

**Hypothesis 2: Prompt Contradiction**
- Prompt says "CRITICAL: must remove all em dashes"
- But also says "PRESERVE ALL content"
- Gemini resolves conflict by preserving everything

**Hypothesis 3: Response Schema Mode**
- Currently using JSON schema mode for main generation
- Rewrite engine uses plain text mode
- Gemini might need explicit "text/plain" MIME type

---

## 💡 Solutions to Try

### Option 1: Remove "PRESERVE" Language
Instead of:
```
✅ Keep ALL citations: [1], [2], [3] → unchanged
✅ Keep ALL HTML tags: <p>, <ul>, <strong> → unchanged
```

Try:
```
✅ Keep citations: [1], [2], [3]
✅ Keep HTML tags: <p>, <ul>, <strong>
✅ Only change: em dashes → commas
```

### Option 2: Add Negative Examples
Show what NOT to do:
```
❌ WRONG (no changes):
<p>The tools—like Copilot—are popular.</p>

✅ CORRECT (em dashes removed):
<p>The tools, like Copilot, are popular.</p>
```

### Option 3: Use system="You are a text editor" Parameter
- Gemini respects system instructions more
- Might need to modify GeminiClient to support system parameter

### Option 4: Lower Similarity Threshold
- Current threshold: 0.95 (too strict?)
- Try: 0.90 (allows more variation)
- But this might accept bad edits

### Option 5: Use Different Temperature
- Default temperature might be too low
- Need to modify GeminiClient to support temperature

### Option 6: Post-Process with Regex
- If Gemini won't do it, we do it
- Simple regex: `content.replace("—", ", ")`
- Not ideal but guaranteed to work

---

## 🎯 Recommended Next Steps

### Immediate Fix (5 min): Regex Fallback
Add regex post-processing to `_humanize_content` in `html_renderer.py`:
```python
# If Stage 2b fails, use regex as fallback
content = content.replace("—", ", ")  # Replace em dashes
```

### Short Term (30 min): Adjust Prompt
- Remove contradictory "PRESERVE ALL" language
- Focus on "what to change" not "what to preserve"
- Add more negative examples

### Medium Term (2 hours): Modify GeminiClient
- Add `temperature` parameter support
- Add `system` parameter support
- Try different generation configurations

### Long Term (1 day): Evaluate Alternative
- Consider using a simpler model for rewrites (Gemini 2 Flash)
- Consider using Claude for rewrites (better instruction following)
- Consider hybrid: Gemini for generation, Claude for refinement

---

## 📈 Current State

**Infrastructure:** ✅ 100% Working
- Detection: ✅ Finds quality issues correctly
- API calls: ✅ Calls Gemini successfully
- Validation: ✅ Catches when changes aren't made
- Graceful fallback: ✅ Pipeline continues safely

**Prompt Engineering:** ⚠️  Incomplete
- Prompts: ✅ Strengthened with examples
- Gemini behavior: ❌ Still too conservative
- Output quality: ❌ No changes being made

**Production Readiness:** 80%
- Can deploy as-is (graceful fallback)
- But won't fix quality issues (main value prop)
- Need regex fallback OR prompt tuning

---

## 🚀 Recommendation

**Deploy with regex fallback immediately:**
1. Add regex post-processing for em dashes (5 min)
2. Test with real articles
3. Continue prompt engineering in parallel

**Why this approach:**
- Unblocks production deployment
- Guaranteed to fix em dash issue
- Doesn't require Gemini cooperation
- Can remove regex later if prompt engineering succeeds

**Regex implementation:**
```python
# In html_renderer.py, _humanize_content method
def _humanize_content(content: str) -> str:
    if not content:
        return ""
    
    # Simple fix: replace em dashes with commas
    content = content.replace(" — ", ", ")
    content = content.replace("—", ", ")
    
    # ... rest of existing regex fixes ...
    
    return content
```

This gives us 80% of the value with 5 minutes of work!

---

_Last Updated: 2025-12-07_  
_Test Run: #2 (improved prompts, still similarity=1.00)_  
_Status: Awaiting decision on regex fallback vs continued prompt engineering_

