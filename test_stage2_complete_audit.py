"""
Complete Stage 2 Audit - Deep Investigation
Checks all requirements and quality metrics.
"""
import json
import os
from pathlib import Path
from pipeline.models.output_schema import ArticleOutput

# Find latest output
output_dirs = sorted([d for d in Path('output').iterdir() if d.is_dir() and d.name.startswith('stage2_review_')], reverse=True)
if not output_dirs:
    print("❌ No Stage 2 output found")
    exit(1)

latest_dir = output_dirs[0]
output_file = latest_dir / "stage2_output_pretty.json"

print(f"=== STAGE 2 COMPLETE AUDIT ===\n")
print(f"📁 Analyzing: {latest_dir.name}\n")

with open(output_file, 'r') as f:
    data = json.load(f)

# Track all checks
checks = {
    "critical": [],
    "important": [],
    "warnings": [],
    "successes": []
}

# 1. SCHEMA VALIDATION (CRITICAL)
print("1. SCHEMA VALIDATION (CRITICAL)")
try:
    article = ArticleOutput(**data)
    checks["critical"].append(("✅ Schema validation", "PASSED - All required fields present"))
    print("   ✅ PASSED - All required fields present")
except Exception as e:
    checks["critical"].append(("❌ Schema validation", f"FAILED - {e}"))
    print(f"   ❌ FAILED - {e}")

# 2. REQUIRED FIELDS (CRITICAL)
print("\n2. REQUIRED FIELDS (CRITICAL)")
required_fields = {
    "Headline": data.get("Headline", ""),
    "Teaser": data.get("Teaser", ""),
    "Direct_Answer": data.get("Direct_Answer", ""),
    "Intro": data.get("Intro", ""),
    "Meta_Title": data.get("Meta_Title", ""),
    "Meta_Description": data.get("Meta_Description", ""),
    "section_01_title": data.get("section_01_title", ""),
    "section_01_content": data.get("section_01_content", ""),
    "image_01_url": data.get("image_01_url", ""),
    "image_01_alt_text": data.get("image_01_alt_text", ""),
}

all_present = True
for field, value in required_fields.items():
    if value:
        checks["successes"].append((f"✅ {field}", "Present"))
    else:
        checks["critical"].append((f"❌ {field}", "MISSING"))
        all_present = False
        print(f"   ❌ {field}: MISSING")
if all_present:
    print("   ✅ All required fields present")

# 3. IMAGES (IMPORTANT)
print("\n3. IMAGES (IMPORTANT)")
image_count = sum(1 for k in data.keys() if k.endswith('_url') and 'image' in k.lower() and data.get(k))
if image_count >= 1:
    checks["successes"].append((f"✅ Images", f"{image_count} image(s) present"))
    print(f"   ✅ {image_count} image(s) present")
    if image_count >= 3:
        checks["successes"].append(("✅ Multiple images", "3+ images for better engagement"))
    elif image_count == 2:
        checks["warnings"].append(("⚠️  Images", "Only 2 images (3 recommended)"))
else:
    checks["critical"].append(("❌ Images", "No images present"))

# 4. SECTION VARIETY (IMPORTANT)
print("\n4. SECTION VARIETY (IMPORTANT)")
sections = [k for k in data.keys() if k.startswith('section_') and k.endswith('_content') and data.get(k)]
section_lengths = []
for section_key in sorted(sections):
    content = data[section_key]
    word_count = len(content.split())
    section_lengths.append(word_count)

long_sections = sum(1 for w in section_lengths if w >= 700)
medium_sections = sum(1 for w in section_lengths if 400 <= w < 700)
short_sections = sum(1 for w in section_lengths if w < 400)

print(f"   Distribution: {long_sections} LONG, {medium_sections} MEDIUM, {short_sections} SHORT")
print(f"   Lengths: {[f'{w}w' for w in section_lengths]}")

if long_sections >= 2 and medium_sections >= 2:
    checks["successes"].append(("✅ Section variety", f"{long_sections} LONG, {medium_sections} MEDIUM - Excellent variety"))
elif long_sections >= 1 and medium_sections >= 2:
    checks["important"].append(("⚠️  Section variety", f"{long_sections} LONG, {medium_sections} MEDIUM - Need 2 LONG sections"))
elif medium_sections >= 2:
    checks["important"].append(("⚠️  Section variety", f"0 LONG, {medium_sections} MEDIUM - No LONG sections (max: {max(section_lengths)} words)"))
else:
    checks["important"].append(("❌ Section variety", f"0 LONG, {medium_sections} MEDIUM - Insufficient variety"))

if section_lengths:
    variation = max(section_lengths) - min(section_lengths)
    if variation >= 400:
        checks["successes"].append(("✅ Section variation", f"{variation} words - Good natural variety"))
    elif variation >= 300:
        checks["warnings"].append(("⚠️  Section variation", f"{variation} words - Moderate variety"))
    else:
        checks["warnings"].append(("⚠️  Section variation", f"{variation} words - Sections too uniform"))

# 5. CITATION FREQUENCY (CRITICAL)
print("\n5. CITATION FREQUENCY (CRITICAL)")
total_paragraphs = 0
paragraphs_with_citations = 0
for section_key in sections:
    content = data[section_key]
    paragraphs = content.split('</p>')
    for para in paragraphs:
        if para.strip() and '<p>' in para:
            total_paragraphs += 1
            if 'class="citation"' in para:
                paragraphs_with_citations += 1

if total_paragraphs > 0:
    citation_rate = (paragraphs_with_citations / total_paragraphs) * 100
    print(f"   {paragraphs_with_citations}/{total_paragraphs} paragraphs ({citation_rate:.1f}%)")
    if citation_rate >= 70:
        checks["successes"].append(("✅ Citation frequency", f"{citation_rate:.1f}% - Excellent"))
    elif citation_rate >= 60:
        checks["important"].append(("⚠️  Citation frequency", f"{citation_rate:.1f}% - Close to target (70-80%)"))
    else:
        checks["critical"].append(("❌ Citation frequency", f"{citation_rate:.1f}% - Below target (need 70-80%)"))

# 6. TOTAL CITATIONS (IMPORTANT)
print("\n6. TOTAL CITATIONS (IMPORTANT)")
citation_count = sum(data.get(k, '').count('class="citation"') for k in data.keys() if isinstance(data.get(k), str))
print(f"   {citation_count} citations")
if citation_count >= 12:
    checks["successes"].append(("✅ Total citations", f"{citation_count} - Excellent (target: 12-15)"))
elif citation_count >= 8:
    checks["important"].append(("⚠️  Total citations", f"{citation_count} - Good (target: 12-15)"))
else:
    checks["important"].append(("❌ Total citations", f"{citation_count} - Below target (need 12-15)"))

# 7. HTML FORMATTING (CRITICAL)
print("\n7. HTML FORMATTING (CRITICAL)")
html_issues = []
for section_key in sections:
    content = data[section_key]
    # Check for proper paragraph tags
    if '<p>' not in content:
        html_issues.append(f"{section_key}: No <p> tags")
    # Check for <br><br> (should not be used)
    if '<br><br>' in content:
        html_issues.append(f"{section_key}: Contains <br><br> (should use <p> tags)")
    # Check for em/en dashes
    if '—' in content or '–' in content:
        html_issues.append(f"{section_key}: Contains em/en dashes")

if html_issues:
    checks["critical"].append(("❌ HTML formatting", f"{len(html_issues)} issue(s) found"))
    for issue in html_issues[:3]:
        print(f"   ⚠️  {issue}")
else:
    checks["successes"].append(("✅ HTML formatting", "Proper <p> tags, no <br><br>, no em/en dashes"))

# 8. LISTS (IMPORTANT)
print("\n8. LISTS (IMPORTANT)")
list_count = sum(data.get(k, '').count('<ul>') + data.get(k, '').count('<ol>') for k in data.keys() if isinstance(data.get(k), str))
print(f"   {list_count} lists")
if list_count >= 3:
    checks["successes"].append(("✅ Lists", f"{list_count} lists (target: 3-5)"))
elif list_count >= 1:
    checks["warnings"].append(("⚠️  Lists", f"{list_count} lists (target: 3-5)"))
else:
    checks["important"].append(("❌ Lists", f"{list_count} lists (target: 3-5)"))

# 9. QUESTION HEADERS (IMPORTANT)
print("\n9. QUESTION HEADERS (IMPORTANT)")
question_headers = sum(1 for k in data.keys() if k.endswith('_title') and data.get(k) and any(q in data[k] for q in ['What', 'How', 'Why', 'When', 'Where', 'Who']))
print(f"   {question_headers} question-format headers")
if question_headers >= 2:
    checks["successes"].append(("✅ Question headers", f"{question_headers} (target: 2+)"))
else:
    checks["important"].append(("⚠️  Question headers", f"{question_headers} (target: 2+)"))

# 10. CONVERSATIONAL TONE (IMPORTANT)
print("\n10. CONVERSATIONAL TONE (IMPORTANT)")
conversational_phrases = ['you', 'your', 'you\'ll', 'you\'re', 'you\'ve', 'think of it', 'here\'s', 'let\'s']
phrase_count = sum(data.get(k, '').lower().count(phrase) for k in data.keys() if isinstance(data.get(k), str) for phrase in conversational_phrases)
print(f"   ~{phrase_count} conversational phrases")
if phrase_count >= 10:
    checks["successes"].append(("✅ Conversational tone", f"{phrase_count} phrases (target: 10+)"))
elif phrase_count >= 5:
    checks["warnings"].append(("⚠️  Conversational tone", f"{phrase_count} phrases (target: 10+)"))
else:
    checks["warnings"].append(("⚠️  Conversational tone", f"{phrase_count} phrases (target: 10+)"))

# 11. TL;DR (OPTIONAL)
print("\n11. TL;DR (OPTIONAL)")
tldr = data.get("TLDR", "")
if tldr:
    checks["successes"].append(("✅ TL;DR", f"Present ({len(tldr)} chars)"))
    print(f"   ✅ Present ({len(tldr)} chars)")
else:
    checks["warnings"].append(("⚠️  TL;DR", "Missing (recommended for 3000+ word articles)"))

# 12. TABLES (OPTIONAL)
print("\n12. TABLES (OPTIONAL)")
tables = data.get("tables", [])
if tables:
    checks["successes"].append(("✅ Tables", f"{len(tables)} table(s)"))
    print(f"   ✅ {len(tables)} table(s)")
else:
    checks["warnings"].append(("⚠️  Tables", "Missing (optional but recommended)"))

# 13. SOURCES QUALITY (IMPORTANT)
print("\n13. SOURCES QUALITY (IMPORTANT)")
sources = data.get("Sources", "")
if sources:
    source_lines = [s for s in sources.split('\n') if s.strip() and ':' in s]
    print(f"   {len(source_lines)} sources")
    # Check for specific URLs (not just domains)
    specific_urls = sum(1 for s in source_lines if 'https://' in s and '/' in s.split('https://')[1].split(' ')[0][1:])
    if specific_urls >= len(source_lines) * 0.8:
        checks["successes"].append(("✅ Sources quality", f"{specific_urls}/{len(source_lines)} specific URLs"))
    else:
        checks["warnings"].append(("⚠️  Sources quality", f"{specific_urls}/{len(source_lines)} specific URLs (prefer specific URLs)"))
else:
    checks["important"].append(("❌ Sources", "Missing"))

# FINAL SUMMARY
print("\n" + "="*60)
print("FINAL SUMMARY")
print("="*60)

critical_failures = [c for c in checks["critical"] if c[0].startswith("❌")]
important_issues = [c for c in checks["important"] if c[0].startswith("❌")]

if critical_failures:
    print(f"\n❌ CRITICAL ISSUES ({len(critical_failures)}):")
    for check, msg in critical_failures:
        print(f"   {check}: {msg}")

if important_issues:
    print(f"\n⚠️  IMPORTANT ISSUES ({len(important_issues)}):")
    for check, msg in important_issues:
        print(f"   {check}: {msg}")

warnings = checks["warnings"]
if warnings:
    print(f"\n⚠️  WARNINGS ({len(warnings)}):")
    for check, msg in warnings[:5]:
        print(f"   {check}: {msg}")

successes = checks["successes"]
print(f"\n✅ SUCCESSES ({len(successes)}):")
for check, msg in successes[:10]:
    print(f"   {check}: {msg}")

# OVERALL STATUS
print("\n" + "="*60)
if critical_failures:
    print("❌ STAGE 2 NOT READY - Critical issues must be fixed")
elif important_issues:
    print("⚠️  STAGE 2 MOSTLY READY - Some important issues remain")
else:
    print("✅ STAGE 2 READY - All critical and important checks passed")

