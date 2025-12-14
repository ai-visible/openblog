#!/bin/bash
# Simple test monitor - checks for Stage 12 execution

echo "=== BATCH TEST MONITOR ==="
echo "Monitoring for Stage 12 execution..."
echo "Press Ctrl+C to stop (test continues in background)"
echo ""

while true; do
    clear
    echo "=== $(date '+%H:%M:%S') - Test Monitor ==="
    echo ""
    
    # Check if test is running
    if ps aux | grep "test_full_pipeline_batch.py" | grep -v grep > /dev/null 2>&1; then
        echo "✅ Test Status: RUNNING"
    else
        echo "✅ Test Status: COMPLETED"
        echo ""
        echo "=== FINAL RESULTS ==="
        tail -100 batch_test_output.log 2>/dev/null | grep -E "(BATCH TEST|Article|Stage 12|similarity|Quality|✅|❌)" | tail -30
        break
    fi
    
    echo ""
    echo "=== Completed Stages ==="
    grep "✅.*completed" batch_test_output.log 2>/dev/null | tail -5
    
    echo ""
    echo "=== Stage 12 Status ==="
    if grep -q "Stage 12:" batch_test_output.log 2>/dev/null; then
        echo "✅ Stage 12 EXECUTED!"
        grep "Stage 12:" batch_test_output.log 2>/dev/null | tail -5
    else
        echo "⏳ Waiting for Stage 12 (currently in Stage 2b)"
        tail -3 batch_test_output.log 2>/dev/null | grep -E "(section_|Stage)" || tail -1 batch_test_output.log 2>/dev/null
    fi
    
    echo ""
    echo "=== Similarity Check ==="
    if grep -qi "similarity" batch_test_output.log 2>/dev/null; then
        grep -i "similarity" batch_test_output.log 2>/dev/null | tail -3
    else
        echo "⏳ Not yet executed"
    fi
    
    echo ""
    echo "Next check in 15 seconds... (Ctrl+C to stop monitoring)"
    sleep 15
done
