# Prompt Engineering Plan - Blog Generation

## Overview
Comprehensive plan for testing, iterating, and optimizing the blog generation prompt for Gemini 3.0 Pro.

## Current State
- **Prompt File**: `pipeline/prompts/main_article.py`
- **Model**: Gemini 3.0 Pro (via `gemini-3-pro-preview`)
- **Style**: Simplified, concise (based on working prompt)
- **Status**: Ready for testing

## Phase 1: Baseline Testing

### 1.1 Test Setup
**Location**: `tests/prompt_engineering/`

Create test suite:
- `test_prompt_baseline.py` - Baseline quality metrics
- `test_prompt_quality.py` - Quality audit automation
- `test_prompt_variations.py` - A/B testing framework

### 1.2 Test Cases
**Test Set 1: Quality Fixes Verification**
- [ ] Grammar/typos: Verify no "speed upd", "applys", "Also,," errors
- [ ] Citation embedding: Verify citations embedded in sentences, not standalone
- [ ] Headline length: Verify ≤60 characters
- [ ] Intro length: Verify ≤300 words
- [ ] Empty headings: Verify all headings have 2-3 paragraphs
- [ ] Keyword density: Verify 8-12 natural mentions (not over-optimized)

**Test Set 2: Content Quality**
- [ ] Word count: Verify 2000-2500 words
- [ ] Structure: Verify 8-10 H2 sections
- [ ] Lists: Verify 12+ lists across article
- [ ] Citations: Verify 10-15 authoritative sources
- [ ] FAQ/PAA: Verify separation from main content
- [ ] Internal links: Verify 1-2 per section

**Test Set 3: Output Format**
- [ ] JSON validity: Verify valid JSON output
- [ ] Required fields: Verify all required fields present
- [ ] HTML structure: Verify proper HTML tags
- [ ] Schema markup: Verify JSON-LD schemas

### 1.3 Metrics to Track
**Quality Metrics:**
- Grammar error count (target: 0)
- Citation-only paragraph count (target: 0)
- Empty heading count (target: 0)
- Headline length (target: 50-60 chars)
- Intro length (target: 200-300 words)
- Keyword density (target: 8-12 mentions)

**Content Metrics:**
- Word count (target: 2000-2500)
- Section count (target: 8-10)
- List count (target: 12+)
- Citation count (target: 10-15)
- AEO score (target: ≥80%)

**Readability Metrics:**
- Average sentence length (target: 15-20 words)
- Flesch Reading Ease (target: ≥50)
- Active voice percentage (target: ≥90%)

## Phase 2: A/B Testing Framework

### 2.1 Prompt Variations
Create variations to test:

**Variation A: Current (Baseline)**
- Current simplified prompt

**Variation B: More Explicit Examples**
- Add 2-3 more citation examples
- Add headline examples

**Variation C: Stricter Constraints**
- Tighter length limits
- More explicit "NEVER" rules

**Variation D: More Trusting**
- Remove some constraints
- Trust model more

### 2.2 Test Methodology
1. Generate 5 articles per variation (same keywords)
2. Run quality audit on each
3. Compare metrics across variations
4. Statistical significance testing

### 2.3 Comparison Metrics
- Quality score (0-100)
- Grammar error rate
- Citation embedding success rate
- Length compliance rate
- AEO score
- Human evaluation (if possible)

## Phase 3: Iterative Improvement

### 3.1 Iteration Cycle
1. **Generate** - Create test articles
2. **Measure** - Run quality audit
3. **Analyze** - Identify patterns/issues
4. **Modify** - Update prompt
5. **Test** - Re-run tests
6. **Compare** - Compare to baseline

### 3.2 Prompt Modification Guidelines
- **One change at a time** - Isolate variables
- **Document changes** - Track what changed and why
- **Version control** - Tag prompt versions
- **Rollback plan** - Keep previous working version

### 3.3 Common Issues to Address
- **Grammar errors**: Add explicit proofreading instruction
- **Citation issues**: Strengthen citation embedding rule
- **Length issues**: Adjust constraints or examples
- **Structure issues**: Clarify section requirements
- **Keyword stuffing**: Adjust keyword guidance

## Phase 4: Production Testing

### 4.1 Pre-Deployment Checklist
- [ ] All quality tests passing
- [ ] AEO score ≥80% consistently
- [ ] Grammar error rate <1%
- [ ] Citation embedding success rate >95%
- [ ] Length compliance >90%
- [ ] Human review of 3 sample articles

### 4.2 Deployment Strategy
1. **Shadow Mode** (if possible)
   - Generate with new prompt
   - Compare to old prompt
   - Don't publish yet

2. **Gradual Rollout**
   - 10% of articles use new prompt
   - Monitor metrics
   - Increase gradually

3. **Full Deployment**
   - 100% new prompt
   - Monitor closely for 1 week
   - Have rollback ready

### 4.3 Monitoring
**Daily Metrics:**
- Quality score distribution
- Error rates
- AEO scores
- User feedback (if available)

**Weekly Review:**
- Compare to baseline
- Identify trends
- Plan improvements

## Phase 5: Continuous Improvement

### 5.1 Feedback Loop
1. Collect production data
2. Identify edge cases
3. Update test cases
4. Refine prompt
5. Re-test

### 5.2 Regular Reviews
- **Weekly**: Review metrics, identify issues
- **Monthly**: A/B test new variations
- **Quarterly**: Major prompt overhaul if needed

### 5.3 Documentation
- **Prompt changelog**: Track all changes
- **Test results**: Archive test outputs
- **Best practices**: Document learnings

## Testing Infrastructure

### Test Scripts to Create

**1. `tests/prompt_engineering/test_baseline.py`**
```python
"""
Baseline quality test for prompt.
Generates articles and runs quality audit.
"""
```

**2. `tests/prompt_engineering/test_quality_audit.py`**
```python
"""
Automated quality audit.
Checks grammar, citations, length, structure.
"""
```

**3. `tests/prompt_engineering/test_ab_variations.py`**
```python
"""
A/B testing framework.
Compares prompt variations.
"""
```

**4. `scripts/prompt_quality_audit.py`**
```python
"""
Standalone quality audit script.
Can be run on any generated article.
"""
```

### Test Data
- **Test Keywords**: 10 diverse keywords
- **Test Companies**: 3 different company profiles
- **Test Languages**: en, de, fr (if multilingual)

## Success Criteria

### Must Have (Blocking)
- ✅ Grammar error rate <1%
- ✅ Citation embedding success rate >95%
- ✅ Length compliance >90%
- ✅ AEO score ≥80%

### Should Have (Important)
- ✅ Readability score ≥50
- ✅ Human evaluation positive
- ✅ Consistent quality across keywords
- ✅ Fast generation time

### Nice to Have (Optional)
- ✅ Higher AEO scores (>85%)
- ✅ Better readability (>60)
- ✅ More natural keyword usage
- ✅ Better narrative flow

## Timeline

**Week 1: Setup & Baseline**
- Create test infrastructure
- Run baseline tests
- Document current state

**Week 2: A/B Testing**
- Create prompt variations
- Run A/B tests
- Analyze results

**Week 3: Iteration**
- Implement improvements
- Re-test
- Refine

**Week 4: Production Prep**
- Final testing
- Documentation
- Deployment plan

## Risk Mitigation

### Risks
1. **Prompt changes break existing functionality**
   - Mitigation: Comprehensive test suite
   - Rollback plan ready

2. **Quality degrades**
   - Mitigation: Gradual rollout
   - Continuous monitoring

3. **Over-optimization**
   - Mitigation: Trust model capabilities
   - Keep prompt simple

4. **Edge cases not covered**
   - Mitigation: Diverse test set
   - Production monitoring

## Next Steps

1. **Immediate** (Today):
   - Create test infrastructure
   - Run baseline test
   - Document current metrics

2. **Short-term** (This Week):
   - Create A/B testing framework
   - Run first A/B test
   - Analyze results

3. **Medium-term** (This Month):
   - Iterate based on results
   - Deploy to production
   - Monitor metrics

4. **Long-term** (Ongoing):
   - Continuous improvement
   - Regular reviews
   - Documentation updates

