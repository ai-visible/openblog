# Diagnostic Plan: Why Only 12 Keywords Instead of 50?

## Problem Statement
- **Requesting**: 62 AI keywords (50 * 2.5 / 2) in 8 batches of 8 keywords each  
- **Getting**: Only 12 keywords
- **Expected**: ~50 keywords after filtering
- **Time**: ~96s (parallelization working)

## Root Cause Hypothesis

**Most Likely**: Logging not enabled in test script + logger name mismatch
- Test script doesn't call `setup_logging()`
- Logger uses `__name__` (`v2.keyword_generation.ai_generator`) 
- Logging config sets up `v2.keyword_generation` (parent logger)
- Result: No logs visible, batches failing silently

## Diagnostic Plan (Execute in Order)

### Step 1: Enable Logging in Test Script ⚡ CRITICAL
**File: `test_scaile.py`**
- Add: `from v2.keyword_generation.logging_config import setup_logging`
- Add: `setup_logging(level="INFO")` at start of script
- **Expected**: See batch execution logs immediately

### Step 2: Fix Logger Name Mismatch ⚡ CRITICAL  
**File: `pipeline/keyword_generation/logging_config.py`**
- Change logger name from `"v2.keyword_generation"` to `"v2"` (parent)
- OR ensure child loggers inherit from parent
- **Expected**: All module logs visible

### Step 3: Add Explicit Batch Start/End Logging
**File: `pipeline/keyword_generation/ai_generator.py`**
- In `generate_seed_keywords_async()`: Log "Starting batch N/M" before each batch
- In `_generate_batch_async()`: Log "Batch N starting" at function start
- In `_generate_batch_async()`: Log "Batch N completed: X keywords" before return
- **Expected**: See exactly which batches run and their results

### Step 4: Add Exception Logging at ERROR Level
**File: `pipeline/keyword_generation/ai_generator.py`**
- Change `logger.debug()` for exceptions to `logger.error()`
- Add `exc_info=True` to show full tracebacks
- **Expected**: See all batch failures with full details

### Step 5: Test Minimal Case (Verify Basic Functionality)
**File: `test_diagnostic.py`** (new)
- Request 8 keywords (1 batch)
- Verify: batch executes, returns keywords
- **Expected**: If this fails, issue is in batch generation itself

### Step 6: Test Parallel Case (Verify Concurrency)
**File: `test_diagnostic.py`**
- Request 16 keywords (2 batches)  
- Verify: both batches execute, both return keywords
- **Expected**: If this fails, issue is in parallel execution

## Implementation Order

**Phase 1: Make Logs Visible (Steps 1-2)**
- This will immediately reveal what's happening
- Should take <5 minutes
- Will show batch execution flow

**Phase 2: Add Detailed Tracking (Steps 3-4)**  
- This will show exact failure points
- Should take <10 minutes
- Will identify root cause

**Phase 3: Isolate Issue (Steps 5-6)**
- This will verify where problem occurs
- Should take <15 minutes
- Will confirm fix works

## Expected Findings After Phase 1

Once logging is enabled, we'll see:
- How many batches are created (should be 8)
- Which batches start executing
- Which batches complete successfully
- How many keywords each batch returns
- Which batches fail and why

This will immediately reveal:
- Are batches being created? ✓/✗
- Are batches executing? ✓/✗  
- Are batches returning keywords? ✓/✗
- Are batches failing? ✓/✗
- Are results being combined? ✓/✗

## Success Criteria

After Phase 1:
- See batch creation logs
- See batch execution logs  
- See batch completion logs
- See batch failure logs (if any)
- Identify exact point of failure

After Phase 2:
- Know exactly why batches fail
- See exception details
- See API response details

After Phase 3:
- Verify fix works for single batch
- Verify fix works for parallel batches
- Confirm 50 keywords generated
