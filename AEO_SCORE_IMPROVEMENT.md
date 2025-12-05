# AEO Score Improvement Plan - Reaching >90

## Current Status
- **Current Scores:** 71-76/100
- **Target:** >90/100
- **Gap:** 14-19 points needed

## AEO Scoring Components (100 points total)

### 1. Direct Answer (25 points) ✅
- **Current:** ~25/25 (usually perfect)
- **Status:** ✅ Good

### 2. Q&A Format (20 points) ⚠️
- **Current:** ~15-17/20
- **Missing:** 3-5 points
- **Issues:**
  - Need 2+ section titles in question format ("What is...", "How does...")
  - FAQ/PAA counts are good (5+ FAQs, 3+ PAAs)
- **Fix:** Ensure prompt enforces question-format headers

### 3. Citation Clarity (15 points) ⚠️
- **Current:** ~10-12/15
- **Missing:** 3-5 points
- **Issues:**
  - Need 60%+ paragraphs with 2+ citations
  - Current: ~0-20% paragraphs have 2+ citations
- **Fix:** Update prompt to require 2-3 citations per paragraph

### 4. Natural Language (15 points) ⚠️
- **Current:** ~10-12/15
- **Missing:** 3-5 points
- **Issues:**
  - Need 8+ conversational phrases ("how to", "you can", "here's")
  - Current: ~4-6 phrases
- **Fix:** Update prompt to require 8+ conversational phrases

### 5. Structured Data (10 points) ✅
- **Current:** ~7-8/10
- **Status:** ✅ Good (lists and headings present)

### 6. E-E-A-T (15 points) ❌ **CRITICAL**
- **Current:** 0/15 (not being scored)
- **Missing:** 15 points
- **Issue:** Requires `input_data` with:
  - `author_bio` (experience, credentials)
  - `author_url`
  - `author_name`
- **Fix:** Ensure `company_data` includes author information

## Action Plan

### Priority 1: Enable E-E-A-T Scoring (15 points)
**Impact:** +15 points → Score: 86-91/100

1. Ensure `company_data` includes:
   ```python
   company_data = {
       "author_bio": "John Doe has 10+ years of experience in...",
       "author_url": "https://example.com/author/john-doe",
       "author_name": "John Doe",
       # ... other company data
   }
   ```

2. Verify `input_data` is passed to `AEOScorer.score_article()`:
   ```python
   input_data = {
       "author_bio": company_data.get("author_bio"),
       "author_url": company_data.get("author_url"),
       "author_name": company_data.get("author_name"),
   }
   ```

### Priority 2: Improve Citation Distribution (3-5 points)
**Impact:** +3-5 points → Score: 89-96/100

1. Update prompt to require 2-3 citations per paragraph
2. Ensure citations are distributed evenly throughout content

### Priority 3: Add Question-Format Headers (3-5 points)
**Impact:** +3-5 points → Score: 92-101/100

1. Update prompt to require 3-4 section titles in question format
2. Examples: "What is...", "How does...", "Why does...", "When should..."

### Priority 4: Increase Conversational Phrases (3-5 points)
**Impact:** +3-5 points → Score: 95-106/100

1. Update prompt to require 8+ conversational phrases
2. Examples: "how to", "you can", "here's", "let's", "what is"

## Expected Results

After implementing all fixes:
- **E-E-A-T:** 0 → 10-15 points (+10-15)
- **Citation Clarity:** 10-12 → 13-15 points (+3-5)
- **Q&A Format:** 15-17 → 18-20 points (+3-5)
- **Natural Language:** 10-12 → 13-15 points (+3-5)

**Total Improvement:** +19-30 points
**New Score Range:** 90-106/100 ✅

## Testing

Run diagnostic script:
```bash
python3 diagnose_aeo_score.py
```

This will show exact breakdown and identify specific gaps.

