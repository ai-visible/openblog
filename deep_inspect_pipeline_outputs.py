#!/usr/bin/env python3
"""
Deep Inspection of Pipeline Stage Outputs

Analyzes JSON and HTML outputs from each stage to identify:
- Content quality issues
- Changes between stages
- Where issues are introduced
- HTML structure problems

Usage:
    python3 deep_inspect_pipeline_outputs.py [pipeline_stages_directory]
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict


def analyze_content_quality(content: str, field_name: str = "") -> Dict[str, Any]:
    """Deep analysis of content quality."""
    if not content:
        return {"empty": True}
    
    analysis = {
        "length": len(content),
        "word_count": len(content.split()),
        "em_dashes": len(re.findall(r'—', content)),
        "en_dashes": len(re.findall(r'–', content)),
        "academic_citations": len(re.findall(r'\[\d+\]', content)),
        "bullet_lists": content.count('<ul>'),
        "numbered_lists": content.count('<ol>'),
        "list_items": content.count('<li>'),
        "paragraphs": content.count('<p>'),
        "strong_tags": content.count('<strong>'),
        "em_tags": content.count('<em>'),
        "links": content.count('<a '),
        "citation_links": len(re.findall(r'<a[^>]*class="citation"', content)),
        "malformed_citation_after_p": len(re.findall(r'</p>\s*[A-Z][A-Za-z]+\s+(reports?|notes?|predicts?)', content)),
        "citation_wrapped_in_p": len(re.findall(r'<p>\s*(<a[^>]*class="citation"[^>]*>[^<]+</a>)\s*</p>', content)),
        "broken_html_tags": len(re.findall(r'<[^>]+(?<!>)$', content, re.MULTILINE)),
        "nested_p_tags": len(re.findall(r'<p>.*?<p>', content)),
        "p_inside_li": len(re.findall(r'<li>.*?<p>', content)),
        "ul_inside_p": len(re.findall(r'<p>.*?<ul>', content)),
        "robotic_phrases": {
            "delve into": content.lower().count("delve into"),
            "crucial to note": content.lower().count("crucial to note"),
            "it's important to understand": content.lower().count("it's important to understand"),
            "here's how": content.lower().count("here's how"),
            "here's what": content.lower().count("here's what"),
            "key points include": content.lower().count("key points include"),
        },
        "capitalization_issues": {
            "ibm_lowercase": len(re.findall(r'\biBM\b', content)),
            "gartner_lowercase": len(re.findall(r'\bgartner\b', content)),
            "nist_lowercase": len(re.findall(r'\bnIST\b', content)),
        },
        "incomplete_sentences": len(re.findall(r'[^.!?]\s*$', content.split('\n'), re.MULTILINE)),
    }
    
    # Calculate issues score
    issues = []
    if analysis["em_dashes"] > 0:
        issues.append(f"{analysis['em_dashes']} em dashes")
    if analysis["en_dashes"] > 0:
        issues.append(f"{analysis['en_dashes']} en dashes")
    if analysis["academic_citations"] > 0:
        issues.append(f"{analysis['academic_citations']} academic citations")
    if analysis["malformed_citation_after_p"] > 0:
        issues.append(f"{analysis['malformed_citation_after_p']} citations after </p>")
    if analysis["citation_wrapped_in_p"] > 0:
        issues.append(f"{analysis['citation_wrapped_in_p']} citations wrapped in <p>")
    if analysis["nested_p_tags"] > 0:
        issues.append(f"{analysis['nested_p_tags']} nested <p> tags")
    if analysis["p_inside_li"] > 0:
        issues.append(f"{analysis['p_inside_li']} <p> inside <li>")
    if analysis["ul_inside_p"] > 0:
        issues.append(f"{analysis['ul_inside_p']} <ul> inside <p>")
    
    analysis["issues"] = issues
    analysis["issue_count"] = len(issues)
    
    return analysis


def extract_field_content(data: Dict, field: str) -> str:
    """Extract content from structured_data or preview."""
    if "structured_data" in data:
        return data["structured_data"].get(field, "")
    if "preview" in data:
        return data["preview"].get(field, "")
    return ""


def compare_stages(stage1_data: Dict, stage2_data: Dict, field: str) -> Dict[str, Any]:
    """Compare a field between two stages."""
    content1 = extract_field_content(stage1_data, field)
    content2 = extract_field_content(stage2_data, field)
    
    analysis1 = analyze_content_quality(content1, f"{field}_stage1")
    analysis2 = analyze_content_quality(content2, f"{field}_stage2")
    
    changes = {
        "length_change": analysis2["length"] - analysis1["length"],
        "word_count_change": analysis2["word_count"] - analysis1["word_count"],
        "em_dash_change": analysis2["em_dashes"] - analysis1["em_dashes"],
        "en_dash_change": analysis2["en_dashes"] - analysis1["en_dashes"],
        "list_change": (analysis2["bullet_lists"] + analysis2["numbered_lists"]) - (analysis1["bullet_lists"] + analysis1["numbered_lists"]),
        "issue_count_change": analysis2["issue_count"] - analysis1["issue_count"],
        "new_issues": [i for i in analysis2["issues"] if i not in analysis1["issues"]],
        "fixed_issues": [i for i in analysis1["issues"] if i not in analysis2["issues"]],
    }
    
    return {
        "stage1": analysis1,
        "stage2": analysis2,
        "changes": changes,
    }


def inspect_pipeline_outputs(directory: Path):
    """Deep inspection of all stage outputs."""
    
    print("=" * 80)
    print("DEEP PIPELINE OUTPUT INSPECTION")
    print("=" * 80)
    print(f"\n📁 Directory: {directory}")
    print()
    
    # Find all stage output files
    stage_files = sorted(directory.glob("stage_*.json"))
    
    if not stage_files:
        print("❌ No stage output files found")
        return
    
    print(f"Found {len(stage_files)} stage output files")
    print()
    
    # Load all stage outputs
    stages = {}
    for file in stage_files:
        try:
            with open(file) as f:
                data = json.load(f)
            stage_num = data.get("stage_num")
            stage_name = data.get("stage_name", "Unknown")
            stages[stage_num] = {
                "file": file.name,
                "data": data,
                "name": stage_name,
            }
        except Exception as e:
            print(f"⚠️  Error loading {file.name}: {e}")
    
    # Sort by stage number
    sorted_stages = sorted(stages.items())
    
    print("=" * 80)
    print("STAGE-BY-STAGE ANALYSIS")
    print("=" * 80)
    print()
    
    # Analyze each stage
    for stage_num, stage_info in sorted_stages:
        print(f"\n{'='*80}")
        print(f"STAGE {stage_num}: {stage_info['name']}")
        print("=" * 80)
        
        data = stage_info["data"]
        
        # Check if structured_data exists
        if "structured_data" in data:
            structured = data["structured_data"]
            
            # Analyze key fields
            fields_to_check = [
                ("Intro", "intro"),
                ("section_01_content", "section_01"),
                ("section_02_content", "section_02"),
                ("section_03_content", "section_03"),
            ]
            
            for field_key, field_label in fields_to_check:
                content = structured.get(field_key, "")
                if content:
                    analysis = analyze_content_quality(content, field_label)
                    
                    print(f"\n📋 {field_label.upper()}:")
                    print(f"   Length: {analysis['length']} chars, {analysis['word_count']} words")
                    print(f"   Lists: {analysis['bullet_lists']} <ul>, {analysis['numbered_lists']} <ol>, {analysis['list_items']} items")
                    print(f"   Links: {analysis['links']} total, {analysis['citation_links']} citations")
                    
                    if analysis['issue_count'] > 0:
                        print(f"   ⚠️  Issues ({analysis['issue_count']}):")
                        for issue in analysis['issues']:
                            print(f"      - {issue}")
                    else:
                        print(f"   ✅ No issues detected")
                    
                    # Show preview
                    preview = content[:200].replace('\n', ' ')
                    print(f"   Preview: {preview}...")
        
        # Check parallel_results if available
        if "parallel_results_keys" in data:
            print(f"\n📊 Parallel Results: {', '.join(data['parallel_results_keys'])}")
    
    # Compare consecutive stages
    print("\n" + "=" * 80)
    print("STAGE-TO-STAGE COMPARISON")
    print("=" * 80)
    print()
    
    for i in range(len(sorted_stages) - 1):
        stage1_num, stage1_info = sorted_stages[i]
        stage2_num, stage2_info = sorted_stages[i + 1]
        
        print(f"\n{'─'*80}")
        print(f"STAGE {stage1_num} → STAGE {stage2_num}")
        print(f"{stage1_info['name']} → {stage2_info['name']}")
        print("─" * 80)
        
        # Compare Intro
        if "structured_data" in stage1_info["data"] and "structured_data" in stage2_info["data"]:
            comparison = compare_stages(
                stage1_info["data"],
                stage2_info["data"],
                "Intro"
            )
            
            changes = comparison["changes"]
            
            if any(changes.values()):
                print(f"\n📋 Intro Changes:")
                if changes["length_change"] != 0:
                    print(f"   Length: {changes['length_change']:+d} chars")
                if changes["em_dash_change"] != 0:
                    print(f"   Em dashes: {changes['em_dash_change']:+d}")
                if changes["en_dash_change"] != 0:
                    print(f"   En dashes: {changes['en_dash_change']:+d}")
                if changes["list_change"] != 0:
                    print(f"   Lists: {changes['list_change']:+d}")
                if changes["new_issues"]:
                    print(f"   ⚠️  New issues: {', '.join(changes['new_issues'])}")
                if changes["fixed_issues"]:
                    print(f"   ✅ Fixed issues: {', '.join(changes['fixed_issues'])}")
            else:
                print(f"   No changes detected")
    
    # Find HTML output
    print("\n" + "=" * 80)
    print("HTML OUTPUT INSPECTION")
    print("=" * 80)
    print()
    
    html_files = list(directory.glob("*.html")) + list(directory.parent.glob("**/*.html"))
    
    if html_files:
        print(f"Found {len(html_files)} HTML files")
        for html_file in html_files[:3]:  # Check first 3
            print(f"\n📄 {html_file.name}")
            try:
                with open(html_file) as f:
                    html_content = f.read()
                
                analysis = analyze_content_quality(html_content, "html")
                
                print(f"   Length: {analysis['length']} chars")
                print(f"   Paragraphs: {analysis['paragraphs']}")
                print(f"   Lists: {analysis['bullet_lists']} <ul>, {analysis['numbered_lists']} <ol>")
                print(f"   Links: {analysis['links']} total, {analysis['citation_links']} citations")
                
                if analysis['issue_count'] > 0:
                    print(f"   ⚠️  Issues ({analysis['issue_count']}):")
                    for issue in analysis['issues']:
                        print(f"      - {issue}")
                else:
                    print(f"   ✅ No issues detected")
                
                # Extract article content
                article_match = re.search(r'<article>(.*?)</article>', html_content, re.DOTALL)
                if article_match:
                    article_content = article_match.group(1)
                    article_analysis = analyze_content_quality(article_content, "article")
                    print(f"\n   Article Content:")
                    print(f"      Paragraphs: {article_analysis['paragraphs']}")
                    print(f"      Lists: {article_analysis['bullet_lists']} <ul>, {article_analysis['numbered_lists']} <ol>")
                    if article_analysis['issue_count'] > 0:
                        print(f"      ⚠️  Issues: {', '.join(article_analysis['issues'])}")
                
            except Exception as e:
                print(f"   ⚠️  Error reading HTML: {e}")
    else:
        print("No HTML files found in output directory")
        print("Checking parent directories...")
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    print()
    
    # Find final stage with structured_data
    final_stage = None
    for stage_num, stage_info in reversed(sorted_stages):
        if "structured_data" in stage_info["data"]:
            final_stage = stage_info
            break
    
    if final_stage:
        print(f"Final Stage: {final_stage['name']} (Stage {final_stage['data']['stage_num']})")
        structured = final_stage["data"]["structured_data"]
        
        # Analyze all sections
        total_lists = 0
        total_issues = 0
        all_issues = []
        
        for i in range(1, 10):
            content = structured.get(f"section_{i:02d}_content", "")
            if content:
                analysis = analyze_content_quality(content)
                total_lists += analysis["bullet_lists"] + analysis["numbered_lists"]
                total_issues += analysis["issue_count"]
                all_issues.extend(analysis["issues"])
        
        intro_analysis = analyze_content_quality(structured.get("Intro", ""))
        total_issues += intro_analysis["issue_count"]
        all_issues.extend(intro_analysis["issues"])
        
        print(f"\n📊 Final Content Statistics:")
        print(f"   Total lists: {total_lists}")
        print(f"   Total issues: {total_issues}")
        
        if all_issues:
            issue_counts = defaultdict(int)
            for issue in all_issues:
                issue_counts[issue] += 1
            
            print(f"\n⚠️  Issue Summary:")
            for issue, count in sorted(issue_counts.items()):
                print(f"   - {issue}: {count} occurrence(s)")
        else:
            print(f"\n✅ No issues found in final content!")
    
    print(f"\n📁 Full inspection complete. Check individual stage files for details.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])
    else:
        # Find latest pipeline_stages directory
        dirs = sorted(Path("output").glob("pipeline_stages_*"))
        if dirs:
            directory = dirs[-1]
        else:
            print("❌ No pipeline_stages directory found")
            print("Usage: python3 deep_inspect_pipeline_outputs.py [directory]")
            sys.exit(1)
    
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        sys.exit(1)
    
    inspect_pipeline_outputs(directory)

