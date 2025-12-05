#!/usr/bin/env python3
"""
Step 3: Compare URL Success Before vs After Validation

This compares:
- Raw URLs from Stage 2 (before validation): 6.0% success
- Final URLs after Stage 4 validation: ?% success

This will definitively show if validation helps or hurts.
"""

import json
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def compare_before_after_validation():
    """Compare URL success rates before and after validation."""
    logger.info("🔍 STEP 3: Comparing Before vs After Validation")
    logger.info("=" * 80)
    
    # Load raw URL test results (before validation)
    try:
        with open("raw_urls_test_results.json", "r") as f:
            before_results = json.load(f)
    except FileNotFoundError:
        logger.error("❌ raw_urls_test_results.json not found. Run test_raw_urls_before_validation.py first.")
        return
    
    # Load our previous citation validation test results (after validation)
    try:
        with open("citation_validation_report_20251202_232103.json", "r") as f:
            after_results = json.load(f)
    except FileNotFoundError:
        logger.error("❌ citation_validation_report_20251202_232103.json not found.")
        return
    
    # Extract key metrics
    before_success = before_results["success_rate"]
    before_total = before_results["total_urls"]
    before_valid = before_results["valid_urls"]
    
    after_success = after_results["validation_metrics"]["overall_citation_success_rate"]
    after_total = after_results["validation_metrics"]["total_citations_tested"]
    after_valid = after_results["validation_metrics"]["total_valid_citations"]
    
    logger.info("📊 COMPARISON RESULTS:")
    logger.info("=" * 60)
    logger.info(f"🔍 BEFORE Validation (Stage 2 Raw Output):")
    logger.info(f"   Total URLs: {before_total}")
    logger.info(f"   Valid URLs: {before_valid}")
    logger.info(f"   Success Rate: {before_success:.1f}%")
    logger.info("")
    logger.info(f"🔧 AFTER Validation (Stage 4 Output):")
    logger.info(f"   Total URLs: {after_total}")
    logger.info(f"   Valid URLs: {after_valid}")
    logger.info(f"   Success Rate: {after_success:.1f}%")
    logger.info("")
    
    # Calculate improvement/degradation
    improvement = after_success - before_success
    improvement_pct = (improvement / before_success) * 100 if before_success > 0 else float('inf')
    
    logger.info("📈 VALIDATION IMPACT:")
    logger.info("=" * 60)
    logger.info(f"Success rate change: {before_success:.1f}% → {after_success:.1f}% ({improvement:+.1f} points)")
    logger.info(f"Relative improvement: {improvement_pct:+.0f}%")
    
    if improvement > 5:
        logger.info("✅ VALIDATION HELPS - Significant improvement!")
        verdict = "HELPFUL"
    elif improvement > 0:
        logger.info("⚠️  VALIDATION HELPS SLIGHTLY - Minor improvement")
        verdict = "SLIGHTLY_HELPFUL"
    elif improvement > -2:
        logger.info("➖ VALIDATION NEUTRAL - No meaningful change")
        verdict = "NEUTRAL"
    elif improvement > -10:
        logger.info("⚠️  VALIDATION HURTS SLIGHTLY - Minor degradation")
        verdict = "SLIGHTLY_HARMFUL"
    else:
        logger.info("❌ VALIDATION HURTS - Significant degradation!")
        verdict = "HARMFUL"
    
    # Analyze the real problem
    logger.info("")
    logger.info("🎯 ROOT CAUSE ANALYSIS:")
    logger.info("=" * 60)
    
    if before_success < 20:
        logger.error("🚨 CRITICAL: URLs from Stage 2 are mostly broken BEFORE validation!")
        logger.error("   This means the web search tools are NOT working properly.")
        logger.error("   Gemini is generating hallucinated URLs, not using real search results.")
        primary_issue = "TOOLS_NOT_WORKING"
    else:
        logger.info("✅ URLs from Stage 2 are mostly working")
        primary_issue = "VALIDATION_ISSUE"
    
    if verdict in ["HARMFUL", "SLIGHTLY_HARMFUL"]:
        logger.warning("⚠️  Validation is making broken URLs even worse!")
        secondary_issue = "VALIDATION_HARMFUL"
    elif verdict in ["HELPFUL", "SLIGHTLY_HELPFUL"]:
        logger.info("✅ Validation is helping to some degree")
        secondary_issue = "VALIDATION_HELPFUL"
    else:
        logger.info("➖ Validation has no meaningful impact")
        secondary_issue = "VALIDATION_NEUTRAL"
    
    # Final assessment
    logger.info("")
    logger.info("🏁 FINAL ASSESSMENT:")
    logger.info("=" * 60)
    
    if primary_issue == "TOOLS_NOT_WORKING":
        logger.error("🚨 ROOT CAUSE: Web search tools (googleSearch + urlContext) are NOT working!")
        logger.error("   - Gemini is generating hallucinated URLs instead of using real search results")
        logger.error("   - 94% of URLs are broken straight from Stage 2")
        logger.error("   - This is the fundamental problem that must be fixed first")
        
        if secondary_issue == "VALIDATION_HARMFUL":
            logger.error("   - PLUS: Validation is making the already-bad situation worse")
        elif secondary_issue == "VALIDATION_HELPFUL":
            logger.warning("   - Validation is trying to help but can't fix the core tool issue")
        
        logger.info("")
        logger.info("🔧 RECOMMENDED ACTIONS:")
        logger.info("1. 🚨 URGENT: Fix web search tool integration in Stage 2")
        logger.info("2. 🔍 Debug why googleSearch + urlContext tools are failing")
        logger.info("3. 🧪 Test that tools actually return real URLs")
        logger.info("4. ⚠️  Consider disabling validation until tools work")
        
    else:
        logger.info("✅ Web search tools appear to be working")
        if secondary_issue == "VALIDATION_HARMFUL":
            logger.warning("🚨 Main issue: Validation is making good URLs worse")
        else:
            logger.info("✅ System is working as intended")
    
    # Save comparison results
    comparison = {
        "comparison_type": "Before vs After Validation",
        "timestamp": "2025-12-03",
        "before_validation": {
            "source": "Stage 2 Raw Output",
            "success_rate": before_success,
            "total_urls": before_total,
            "valid_urls": before_valid
        },
        "after_validation": {
            "source": "Stage 4 Final Output", 
            "success_rate": after_success,
            "total_urls": after_total,
            "valid_urls": after_valid
        },
        "impact": {
            "improvement_points": improvement,
            "improvement_percent": improvement_pct,
            "verdict": verdict
        },
        "root_cause": {
            "primary_issue": primary_issue,
            "secondary_issue": secondary_issue
        }
    }
    
    with open("validation_comparison_results.json", "w") as f:
        json.dump(comparison, f, indent=2)
    
    logger.info("📁 Comparison saved: validation_comparison_results.json")

if __name__ == "__main__":
    compare_before_after_validation()