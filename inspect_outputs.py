#!/usr/bin/env python3
"""
Deep Output Inspection Script

Inspects all saved stage outputs and performs comprehensive analysis.
"""

import json
from pathlib import Path
from datetime import datetime


def inspect_stage_output(stage_dir: Path, stage_num: int, stage_name: str):
    """Inspect a single stage's output."""
    print(f"\n{'='*80}")
    print(f"STAGE {stage_num}: {stage_name} - DEEP INSPECTION")
    print(f"{'='*80}\n")
    
    context_file = stage_dir / "full_context.json"
    if not context_file.exists():
        print(f"  ⚠️  No output file found: {context_file}")
        return None
    
    with open(context_file, 'r') as f:
        data = json.load(f)
    
    inspection = {
        'stage_num': stage_num,
        'stage_name': stage_name,
        'findings': []
    }
    
    # Basic checks
    print("📊 Basic Data:")
    print(f"  Job ID: {data.get('job_id', 'N/A')}")
    print(f"  Has structured_data: {data.get('has_structured_data', False)}")
    print(f"  Has validated_article: {data.get('has_validated_article', False)}")
    print(f"  Has parallel_results: {data.get('has_parallel_results', False)}")
    
    # Stage-specific deep inspection
    if stage_num == 2 and 'structured_data' in data:
        print("\n📄 Structured Data Analysis:")
        sd = data['structured_data']
        
        # Required fields
        required = ['Headline', 'Subtitle', 'Intro', 'Direct_Answer', 'Sources']
        for field in required:
            has_field = field in sd and sd[field]
            status = "✅" if has_field else "❌"
            print(f"  {status} {field}: {'Present' if has_field else 'Missing'}")
            if has_field:
                val = str(sd[field])
                print(f"      Length: {len(val)} chars")
                print(f"      Preview: {val[:100]}...")
                inspection['findings'].append({
                    'field': field,
                    'status': 'present',
                    'length': len(val)
                })
        
        # Sections
        sections = []
        for i in range(1, 10):
            key = f'section_{i:02d}_content'
            if key in sd and sd[key]:
                sections.append(i)
                content = str(sd[key])
                print(f"  ✅ Section {i}: {len(content)} chars")
        
        print(f"\n  📑 Total sections with content: {len(sections)}")
        inspection['findings'].append({
            'type': 'sections',
            'count': len(sections),
            'section_numbers': sections
        })
        
        # Sources
        if 'Sources' in sd and sd['Sources']:
            sources = str(sd['Sources'])
            citation_count = sources.count('[')
            print(f"\n  📎 Sources field:")
            print(f"      Citation markers: {citation_count}")
            print(f"      Length: {len(sources)} chars")
            print(f"      Preview: {sources[:200]}...")
            inspection['findings'].append({
                'type': 'sources',
                'citation_count': citation_count,
                'length': len(sources)
            })
    
    elif stage_num == 3 and 'structured_data' in data:
        print("\n🔧 Quality Refinement Analysis:")
        sd = data['structured_data']
        
        # Check if content was refined
        if 'Headline' in sd:
            headline = str(sd['Headline'])
            print(f"  ✅ Headline refined: {headline[:100]}...")
            inspection['findings'].append({
                'type': 'refinement',
                'headline_refined': True
            })
        
        # Check for conversational phrases
        if 'Intro' in sd:
            intro = str(sd['Intro'])
            phrases = ['you can', 'here\'s', 'let\'s', 'how to', 'what is']
            found_phrases = [p for p in phrases if p.lower() in intro.lower()]
            print(f"  ✅ Conversational phrases found: {len(found_phrases)}")
            if found_phrases:
                print(f"      Phrases: {', '.join(found_phrases[:3])}")
            inspection['findings'].append({
                'type': 'conversational_phrases',
                'count': len(found_phrases),
                'phrases': found_phrases
            })
        
        # Check sections
        sections_refined = []
        for i in range(1, 10):
            key = f'section_{i:02d}_content'
            if key in sd and sd[key]:
                sections_refined.append(i)
        
        print(f"  ✅ Sections refined: {len(sections_refined)}")
        inspection['findings'].append({
            'type': 'sections_refined',
            'count': len(sections_refined)
        })
    
    elif stage_num == 8 and 'validated_article' in data:
        print("\n🔗 Merge & Link Analysis:")
        va = data['validated_article']
        
        # Critical: Check for content manipulation fields
        content_manip_fields = [
            'humanized', 'normalized', 'sanitized',
            'conversational_phrases_added', 'aeo_enforced',
            'converted_to_questions', 'split_paragraphs'
        ]
        
        found_manip = []
        for field in va.keys():
            for manip in content_manip_fields:
                if manip in field.lower():
                    found_manip.append(field)
        
        if found_manip:
            print(f"  ❌ CRITICAL: Found content manipulation fields: {found_manip}")
            inspection['findings'].append({
                'type': 'content_manipulation',
                'status': 'FAIL',
                'found_fields': found_manip
            })
        else:
            print(f"  ✅ No content manipulation fields found (correct!)")
            inspection['findings'].append({
                'type': 'content_manipulation',
                'status': 'PASS',
                'found_fields': []
            })
        
        # Check citation linking
        has_citation_map = '_citation_map' in va
        if has_citation_map:
            citation_map = va['_citation_map']
            print(f"  ✅ Citation map present: {len(citation_map)} entries")
            print(f"      Sample: {list(citation_map.items())[:3]}")
            inspection['findings'].append({
                'type': 'citation_linking',
                'status': 'PASS',
                'citation_count': len(citation_map)
            })
        else:
            print(f"  ⚠️  No citation map found")
            inspection['findings'].append({
                'type': 'citation_linking',
                'status': 'WARN',
                'citation_count': 0
            })
        
        # Check parallel results merged
        has_image = 'image_url' in va
        has_toc = 'toc' in va or any('toc' in k for k in va.keys())
        print(f"  ✅ Image merged: {has_image}")
        print(f"  ✅ ToC merged: {has_toc}")
        inspection['findings'].append({
            'type': 'parallel_merge',
            'has_image': has_image,
            'has_toc': has_toc
        })
        
        # Check data flattening
        nested_dicts = sum(1 for v in va.values() if isinstance(v, dict))
        print(f"  ✅ Data flattened: {nested_dicts} nested dicts (should be < 5)")
        inspection['findings'].append({
            'type': 'data_flattening',
            'nested_dicts': nested_dicts,
            'total_fields': len(va)
        })
        
        # Show field count
        print(f"\n  📊 Total fields: {len(va)}")
        print(f"      Sample fields: {list(va.keys())[:10]}")
    
    elif stage_num == 9 and 'storage_result' in data:
        print("\n💾 Storage & Export Analysis:")
        sr = data['storage_result']
        
        if isinstance(sr, dict):
            success = sr.get('success', False)
            print(f"  {'✅' if success else '❌'} Storage success: {success}")
            
            if 'exported_files' in sr:
                files = sr['exported_files']
                print(f"  ✅ Exported formats: {list(files.keys())}")
                expected = ['html', 'markdown', 'pdf', 'csv', 'xlsx', 'json']
                missing = [f for f in expected if f not in files]
                if missing:
                    print(f"  ⚠️  Missing formats: {missing}")
                else:
                    print(f"  ✅ All expected formats present")
                
                inspection['findings'].append({
                    'type': 'export_formats',
                    'formats': list(files.keys()),
                    'all_present': len(missing) == 0
                })
    
    return inspection


def main():
    """Inspect all stage outputs."""
    print("="*80)
    print("DEEP OUTPUT INSPECTION")
    print("="*80)
    
    # Find latest inspection output
    output_dirs = sorted(Path('.').glob('inspection_output_*'))
    if not output_dirs:
        print("❌ No inspection output directories found")
        return
    
    latest_dir = output_dirs[-1]
    print(f"\n📁 Inspecting: {latest_dir}\n")
    
    stages = [
        (0, "Data Fetch"),
        (1, "Prompt Build"),
        (2, "Content Generation"),
        (3, "Quality Refinement"),
        (4, "Citations Validation"),
        (5, "Internal Links"),
        (6, "Image Generation"),
        (7, "Similarity Check"),
        (8, "Merge & Link"),
        (9, "Storage & Export"),
    ]
    
    all_inspections = []
    
    for stage_num, stage_name in stages:
        stage_dir = latest_dir / f"stage_{stage_num:02d}"
        inspection = inspect_stage_output(stage_dir, stage_num, stage_name)
        if inspection:
            all_inspections.append(inspection)
    
    # Summary
    print("\n" + "="*80)
    print("INSPECTION SUMMARY")
    print("="*80)
    
    # Critical checks
    stage_3_passed = any(
        i['stage_num'] == 3 and 
        any(f.get('type') == 'refinement' for f in i['findings'])
        for i in all_inspections
    )
    
    stage_8_passed = any(
        i['stage_num'] == 8 and
        any(f.get('type') == 'content_manipulation' and f.get('status') == 'PASS' 
            for f in i['findings'])
        for i in all_inspections
    )
    
    print(f"\n✅ Stage 3 Quality Refinement: {'PASS' if stage_3_passed else 'FAIL'}")
    print(f"✅ Stage 8 Simplified (No Content Manipulation): {'PASS' if stage_8_passed else 'FAIL'}")
    
    # Save inspection summary
    summary = {
        'inspection_date': datetime.now().isoformat(),
        'output_directory': str(latest_dir),
        'inspections': all_inspections,
        'critical_checks': {
            'stage_3_passed': stage_3_passed,
            'stage_8_passed': stage_8_passed
        }
    }
    
    summary_file = latest_dir / "inspection_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n📄 Inspection summary saved: {summary_file}")


if __name__ == "__main__":
    main()

