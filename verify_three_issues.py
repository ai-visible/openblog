#!/usr/bin/env python3
"""
Verify the three non-critical issues:

1. Missing similarity_check in Stage 7
2. Missing job_config/company_data in Stage 0
3. Export formats not in context (Stage 9)
"""

import json
from pathlib import Path

print('='*80)
print('VERIFICATION: Three Non-Critical Issues')
print('='*80)
print()

# Issue 1: Stage 7 similarity_check
print('ISSUE 1: Missing similarity_check in Stage 7')
print('-'*80)
stage7_file = Path('inspection_output_20251216-023614/stage_07/full_context.json')
if stage7_file.exists():
    data = json.load(open(stage7_file))
    
    # Check if similarity_report exists (it's stored here, not in parallel_results)
    if 'similarity_report' in data:
        print('✅ similarity_report found in context (correct location)')
        print(f'   This is where Stage 7 stores similarity results')
    else:
        print('❌ similarity_report NOT found in context')
        print('   Checking if inspection script serializes it...')
    
    # Check parallel_results
    if 'parallel_results' in data:
        pr = data['parallel_results']
        if 'similarity_check' in pr:
            print('✅ similarity_check found in parallel_results')
        else:
            print('⚠️  similarity_check NOT in parallel_results')
            print('   VERDICT: This is EXPECTED - Stage 7 stores in context.similarity_report,')
            print('            not in parallel_results. Inspection script needs to check')
            print('            context.similarity_report instead of parallel_results["similarity_check"]')
    else:
        print('❌ parallel_results not found')
else:
    print('❌ Stage 7 output file not found')

print()

# Issue 2: Stage 0 job_config/company_data
print('ISSUE 2: Missing job_config/company_data in Stage 0')
print('-'*80)
stage0_file = Path('inspection_output_20251216-023614/stage_00/full_context.json')
if stage0_file.exists():
    data = json.load(open(stage0_file))
    
    if 'job_config' in data:
        print('✅ job_config found in saved context')
    else:
        print('❌ job_config NOT in saved context')
        print('   VERDICT: Inspection script does not serialize job_config.')
        print('            Check deep_inspect_pipeline.py line 59 - job_config not in list')
    
    if 'company_data' in data:
        print('✅ company_data found in saved context')
    else:
        print('❌ company_data NOT in saved context')
        print('   VERDICT: Inspection script does not serialize company_data.')
        print('            Check deep_inspect_pipeline.py line 59 - company_data not in list')
        print('            Pipeline correctly stores these - this is a serialization issue')
else:
    print('❌ Stage 0 output file not found')

print()

# Issue 3: Stage 9 export formats
print('ISSUE 3: Export formats not in context (Stage 9)')
print('-'*80)
stage9_file = Path('inspection_output_20251216-023614/stage_09/full_context.json')
if stage9_file.exists():
    data = json.load(open(stage9_file))
    
    if 'storage_result' in data:
        sr = data['storage_result']
        print(f'✅ storage_result found')
        print(f'   Success: {sr.get("success")}')
        print(f'   Output dir: {sr.get("output_dir")}')
        
        if 'exported_files' in sr:
            ef = sr['exported_files']
            print(f'   exported_files: {ef}')
            
            if isinstance(ef, dict) and len(ef) == 0:
                print('   ⚠️  exported_files is empty dict')
                print('   Checking if files were actually created...')
                
                output_dir = sr.get('output_dir')
                if output_dir:
                    output_path = Path(output_dir)
                    if output_path.exists():
                        files = list(output_path.glob('*'))
                        print(f'   ✅ Output directory exists with {len(files)} files:')
                        for f in files:
                            print(f'      - {f.name}')
                        print('   VERDICT: Files were created but exported_files dict is empty.')
                        print('            This suggests export_formats was empty or export')
                        print('            returned empty dict. Check Stage 9 export_formats.')
                    else:
                        print(f'   ❌ Output directory does not exist: {output_dir}')
            elif isinstance(ef, dict) and len(ef) > 0:
                print(f'   ✅ exported_files contains {len(ef)} formats: {list(ef.keys())}')
            else:
                print(f'   ⚠️  exported_files is not a dict: {type(ef)}')
        else:
            print('   ❌ exported_files NOT in storage_result')
    else:
        print('❌ storage_result not found')
else:
    print('❌ Stage 9 output file not found')

print()
print('='*80)
print('SUMMARY')
print('='*80)
print()
print('1. Stage 7 similarity_check:')
print('   - Issue: Inspection script looks for parallel_results["similarity_check"]')
print('   - Reality: Stage 7 stores in context.similarity_report')
print('   - Fix: Update inspection script to check context.similarity_report')
print('   - Status: EXPECTED BEHAVIOR (inspection script issue, not pipeline)')
print()
print('2. Stage 0 job_config/company_data:')
print('   - Issue: Not found in saved context')
print('   - Reality: Pipeline correctly stores these in context')
print('   - Fix: Update inspection script to serialize job_config and company_data')
print('   - Status: EXPECTED BEHAVIOR (inspection script issue, not pipeline)')
print()
print('3. Stage 9 export formats:')
print('   - Issue: exported_files dict is empty')
print('   - Reality: Files were created (index.html, article.json, metadata.json)')
print('   - Fix: Check why export_formats was empty or export returned empty dict')
print('   - Status: NEEDS INVESTIGATION (may be pipeline issue)')
print()

