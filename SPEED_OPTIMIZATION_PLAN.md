# Keyword Generation Speed Optimization Plan

## Current Performance
- **Time**: ~150 seconds (~2.5 minutes)
- **Keywords**: ~17 keywords
- **Speed**: ~8.8 seconds per keyword
- **Bottleneck**: Sequential processing + rate limiting + retries

## Optimization Strategies

### 1. **Parallel Batch Processing** (Biggest Impact)
**Current**: Batches processed sequentially (batch 1 → batch 2 → batch 3)
**Optimized**: Process batches concurrently using `asyncio.gather()`
**Expected Speedup**: 3-5x faster (50-60s instead of 150s)

### 2. **Reduce Rate Limiting** (Quick Win)
**Current**: 0.5s delay between API calls
**Optimized**: 0.1-0.2s delay (Gemini API can handle faster)
**Expected Speedup**: 2-3x faster for batch processing

### 3. **Skip Structured Output** (Reliability)
**Current**: Using structured output causing JSON truncation → retries
**Optimized**: Use regular JSON parsing with better prompts
**Expected Speedup**: Eliminates retry delays (saves 20-30s)

### 4. **Parallel Scoring** (Medium Impact)
**Current**: Score keywords in sequential batches
**Optimized**: Score multiple batches concurrently
**Expected Speedup**: 2x faster scoring

### 5. **Shorter Prompts** (Small Impact)
**Current**: Verbose prompts with examples
**Optimized**: Concise prompts focusing on essentials
**Expected Speedup**: 10-20% faster API responses

### 6. **Reduce Batch Size** (Reliability)
**Current**: 10 keywords per batch
**Optimized**: 5-8 keywords per batch (more reliable, less retries)
**Expected Speedup**: Fewer retries = more consistent speed

## Combined Expected Performance
- **Before**: ~150s for 17 keywords
- **After**: ~30-50s for 50 keywords
- **Speedup**: 3-5x faster
- **Keywords/second**: ~1-1.7 keywords/second (vs current 0.11)

## Implementation Priority
1. ✅ Skip structured output (quick fix, eliminates retries)
2. ✅ Reduce rate limit delay (quick win)
3. ✅ Parallel batch processing (biggest impact)
4. ✅ Parallel scoring (medium impact)
5. ✅ Shorter prompts (polish)

