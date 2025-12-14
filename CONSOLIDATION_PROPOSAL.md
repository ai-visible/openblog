# Stage 2b Consolidation Proposal

## Current Architecture

**Stage 2b (Quality Refinement):**
- Regex cleanup (em dashes, citations, duplicate lists)
- Gemini quality review with JSON schema
- Fixes structural issues (truncated lists, broken sentences)
- ~10 fields processed

**Stage 4 (Citations):**
- Extracts citations from Sources field
- Validates URLs (HTTP checks, DOI validation)
- Uses Gemini for alternative URL search (SmartCitationValidator)
- Resolves proxy URLs
- Formats as HTML

**Stage 5 (Internal Links):**
- Extracts topics from article
- Uses simple keyword matching (no Gemini)
- Generates suggestions from batch siblings + sitemap
- Validates URLs with HTTP HEAD checks
- Assigns links per section

---

## Proposed Consolidation

### Option A: Full Consolidation (Aggressive)

**Move into Stage 2b:**
1. ✅ Citation validation & enhancement (Gemini-powered)
2. ✅ Internal link suggestion (Gemini-powered semantic matching)
3. ❌ HTTP URL validation (keep separate - fast, deterministic)

**Pros:**
- Fewer API calls (cost savings)
- More coherent fixes (Gemini sees everything at once)
- Better semantic matching for internal links
- Simpler pipeline

**Cons:**
- Stage 2b becomes very complex (~500+ lines)
- Harder to debug (mixed concerns)
- Token limits (need to pass sitemap data, citation URLs)
- Different failure modes (citation validation might fail, but quality fixes succeed)

**Token Estimate:**
- Article content: ~20k tokens
- Sitemap URLs (100 links): ~5k tokens
- Citation URLs (15 links): ~1k tokens
- **Total: ~26k tokens** (within Gemini 3 Pro's 1M context window ✅)

---

### Option B: Hybrid Approach (Recommended)

**Move into Stage 2b:**
1. ✅ Citation validation & enhancement (Gemini-powered)
2. ✅ Internal link suggestion (Gemini-powered semantic matching)
3. ❌ HTTP URL validation (keep separate - fast, deterministic)

**Keep Separate:**
- HTTP validation (Stage 4b, Stage 5b) - fast, deterministic, can run in parallel

**Architecture:**
```
Stage 2b (Enhanced):
├── Regex cleanup (existing)
├── Gemini quality review (existing)
├── Citation validation & enhancement (NEW - Gemini)
└── Internal link suggestion (NEW - Gemini)

Stage 4b (Lightweight):
└── HTTP validation for citations (fast, parallel)

Stage 5b (Lightweight):
└── HTTP validation for internal links (fast, parallel)
```

**Pros:**
- Best of both worlds (Gemini intelligence + fast validation)
- Easier to debug (clear separation)
- Can parallelize HTTP validation
- Gemini focuses on semantic tasks

**Cons:**
- Still 2 stages (but Stage 4b/5b are lightweight)

---

### Option C: Citation Only (Conservative)

**Move into Stage 2b:**
1. ✅ Citation validation & enhancement (Gemini-powered)
2. ❌ Internal links (keep separate - simpler)

**Pros:**
- Lower risk (smaller change)
- Citations are already Gemini-powered
- Internal links stay simple

**Cons:**
- Less consolidation benefit
- Still have separate stages

---

## Recommendation: **Option B (Hybrid)**

### Why Hybrid?

1. **Gemini 3 Pro can handle it:**
   - 1M context window (we use ~26k tokens)
   - Multi-step reasoning (quality fixes + citations + links)
   - Structured output (JSON schema)

2. **HTTP validation should stay separate:**
   - Fast (100ms vs 5s for Gemini)
   - Deterministic (no API costs)
   - Can parallelize (100 URLs in parallel)

3. **Better semantic matching:**
   - Gemini can understand article context
   - Better internal link suggestions
   - More coherent citation enhancement

### Implementation Plan

**Phase 1: Citation Consolidation**
1. Move citation validation into Stage 2b
2. Use Gemini to validate/enhance citations in same pass as quality fixes
3. Keep HTTP validation separate (Stage 4b)

**Phase 2: Internal Link Consolidation**
1. Move internal link suggestion into Stage 2b
2. Use Gemini for semantic matching (better than keyword matching)
3. Keep HTTP validation separate (Stage 5b)

**Phase 3: Optimization**
1. Batch Gemini calls (if possible)
2. Cache sitemap data
3. Optimize prompts

---

## Code Changes Required

### Stage 2b Enhancements

```python
class QualityRefinementStage(Stage):
    async def execute(self, context: ExecutionContext):
        # 1. Regex cleanup (existing)
        article_dict = self._apply_regex_cleanup(article_dict)
        
        # 2. Gemini quality review (existing)
        article_dict = await self._gemini_full_review(article_dict)
        
        # 3. Citation validation & enhancement (NEW)
        if "Sources" in article_dict:
            citations = self._extract_citations(article_dict["Sources"])
            enhanced_citations = await self._gemini_validate_citations(
                citations, 
                context.grounding_urls
            )
            article_dict["Sources"] = self._format_citations(enhanced_citations)
        
        # 4. Internal link suggestion (NEW)
        if context.sitemap_data:
            internal_links = await self._gemini_suggest_internal_links(
                article_dict,
                context.sitemap_data,
                context.job_config.get("batch_siblings", [])
            )
            context.parallel_results["section_internal_links"] = internal_links
```

### New Gemini Prompts

**Citation Validation:**
```
You are validating citations for an article. For each citation:
1. Check if URL is valid (not 404, not proxy URL)
2. If invalid, suggest alternative URL using Google Search
3. Enhance title if needed
4. Filter out low-quality sources

Return validated citations with enhanced URLs and titles.
```

**Internal Link Suggestion:**
```
You are suggesting internal links for an article. Given:
- Article content and sections
- Available internal URLs (sitemap + batch siblings)
- Section titles

Suggest 1-2 relevant internal links per section based on semantic relevance.
Return links assigned to each section number.
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Token limit exceeded | Low | High | Monitor token usage, truncate sitemap if needed |
| Gemini API failures | Medium | Medium | Fallback to existing stages |
| Debugging complexity | Medium | Medium | Add detailed logging, keep stages modular |
| Performance degradation | Low | Low | HTTP validation still parallel |

---

## Success Metrics

- **API Calls:** Reduce from ~15 calls to ~5 calls per article
- **Cost:** Reduce by ~60% (fewer Gemini calls)
- **Quality:** Maintain or improve citation quality and internal link relevance
- **Performance:** No degradation (HTTP validation still parallel)

---

## Next Steps

1. ✅ Get user approval for Option B
2. Implement Phase 1 (Citation consolidation)
3. Test thoroughly
4. Implement Phase 2 (Internal link consolidation)
5. Monitor performance and costs

