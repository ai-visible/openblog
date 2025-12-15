"""
Full Audit of Stage 2b - Show Prompts and Outputs
"""

import json
from pathlib import Path

# Find the latest test output directory (not files)
test_dirs = [d for d in Path("output").glob("stage2b_real_test_*") if d.is_dir()]
test_dirs = sorted(test_dirs, reverse=True)
if not test_dirs:
    print("❌ No test output directory found")
    exit(1)

latest_dir = test_dirs[0]
print(f"📁 Using test output: {latest_dir}")
print()

# Load Stage 2 and Stage 2b outputs
stage2_file = latest_dir / "stage2_output.json"
stage2b_file = latest_dir / "stage2b_output.json"

with open(stage2_file, 'r') as f:
    stage2_output = json.load(f)

with open(stage2b_file, 'r') as f:
    stage2b_output = json.load(f)

# Extract the CHECKLIST from Stage 2b code
CHECKLIST = """You are an expert quality editor. Your job is to find and fix ALL issues using AI intelligence.
Be SURGICAL - only change what's broken, preserve everything else.

## Structural Issues (CRITICAL)

- **Truncated list items**: Items ending mid-word ("secur", "autom", "manag") - complete or remove
- **Fragment lists**: Single-item lists that are clearly part of a sentence - merge into paragraph
- **Duplicate summary lists**: Paragraph followed by "<ul>" repeating same content - remove duplicate list
- **Orphaned HTML tags**: </p>, </li>, </ul> in wrong places - fix HTML structure
- **Malformed HTML nesting**: <ul> inside <p>, </p> inside <li> - fix nesting
- **Empty paragraphs**: <p>This </p>, <p>. Also,</p> - remove or complete
- **Broken sentences**: "</p><p><strong>How can</strong> you..." - merge into single paragraph
- **Orphaned <strong> tags**: "<p><strong>If you</strong></p> want..." → "<p><strong>If you</strong> want...</p>"

## Capitalization Issues

- **Brand names**: "iBM" → "IBM", "nIST" → "NIST", "mCKinsey" → "McKinsey"
- **Lowercase after period**: "sentence. the next" → "sentence. The next"
- **All-caps words**: "THE BEST" → "the best"

## AI Marker Issues (CRITICAL - ZERO TOLERANCE)

- **Em dashes (—)**: MUST replace with " - " (space-hyphen-space) or comma - NEVER leave em dashes
- **En dashes (–)**: MUST replace with "-" (hyphen) or " to " - NEVER leave en dashes
- **Academic citations [N]**: Remove all [1], [2], [1][2] markers from body (keep natural language citations only)
- **Robotic phrases**: "delve into", "crucial to note", "it's important to understand" → rewrite naturally
- **Formulaic transitions**: "Here's how/what" → rewrite naturally
- **Redundant lists**: "Key points include:" followed by redundant bullets → remove redundant list
- **HTML in titles**: Section titles with <p> tags → remove all HTML tags

## Humanization (Natural Language)

Replace AI-typical phrases with natural alternatives:
- "seamlessly" → "smoothly" or "easily"
- "leverage" → "use" or "apply"
- "utilize" → "use"
- "impactful" → "effective" or "meaningful"
- "robust" → "strong" or "reliable"
- "comprehensive" → "full" or "complete"
- "empower" → "help" or "enable"
- "streamline" → "simplify" or "speed up"
- "cutting-edge" → "modern" or "new"
- "furthermore" → ". Also," or remove
- "moreover" → ". Plus," or remove
- "it's important to note that" → remove or rewrite
- "in conclusion" → remove
- "to summarize" → remove

Use contractions naturally: "it is" → "it's", "you are" → "you're", "do not" → "don't"

## Content Quality Issues

- **Incomplete sentences**: Ending abruptly without punctuation - complete or remove
- **Double prefixes**: "What is Why is X" → "Why is X"
- **Repeated content**: Redundant content in same section - remove duplicates
- **Broken grammar**: "You can to mitigate" → "To mitigate" or "You can mitigate"
- **Missing verbs/subjects**: Incomplete sentences - complete
- **Orphaned conjunctions**: ". Also, the" → ". The"

## Link Issues

- **Broken links**: Causing sentence fragmentation - fix
- **Wrong link text**: Domain name instead of title - fix
- **Split sentences**: External links splitting sentences - fix

## AEO Optimization (CRITICAL FOR SCORE 95+)

- **Citation distribution**: Ensure 40%+ paragraphs have natural language citations
  - Add: "According to [Source]...", "[Source] reports...", "Research by [Source]..."
  - Target: 12-15 citations across the article
- **Conversational phrases**: Ensure 8+ instances
  - "you can", "you'll", "here's", "let's", "this is", "when you", "if you"
  - Add naturally if missing (don't force)
- **Question patterns**: Ensure 5+ question patterns
  - "what is", "how does", "why does", "when should", "where can", "how can", "what are"
  - Add rhetorical questions naturally if missing
- **Direct language**: Use "is", "are", "does" not "might be", "could be"
  - Replace vague language with direct statements

## Your Task

1. Read the content carefully
2. Find ALL issues matching the checklist above
3. ALSO find any OTHER issues (typos, grammar, awkward phrasing)
4. Fix each issue surgically - complete broken sentences, remove duplicates, fix grammar
5. HUMANIZE language - replace AI-typical phrases with natural alternatives
6. ENHANCE AEO components - add citations, conversational phrases, question patterns where missing
7. Return the complete fixed content

**Be thorough. Production quality means ZERO defects AND AEO score 95+.**"""

# Show the full prompt structure
print("=" * 80)
print("STAGE 2B FULL PROMPT STRUCTURE")
print("=" * 80)
print()
print("The prompt sent to Gemini consists of:")
print("1. CHECKLIST (quality review instructions)")
print("2. FIELD name")
print("3. CONTENT TO REVIEW (the actual content)")
print()
print("=" * 80)
print("FULL CHECKLIST PROMPT:")
print("=" * 80)
print()
print(CHECKLIST)
print()

# Show example prompts for key fields
print("=" * 80)
print("EXAMPLE PROMPTS SENT TO GEMINI")
print("=" * 80)
print()

# Show Intro prompt example
intro_content = stage2_output.get('Intro', '')
if intro_content:
    intro_prompt = f"""{CHECKLIST}

FIELD: Intro

CONTENT TO REVIEW:
{intro_content}

Return JSON with: fixed_content, issues_fixed, fixes[]
If no issues, return original content unchanged with issues_fixed=0.
"""
    print("EXAMPLE 1: Intro Field Prompt")
    print("-" * 80)
    print(intro_prompt[:2000] + "..." if len(intro_prompt) > 2000 else intro_prompt)
    print()

# Show section_01_content prompt example
section1_content = stage2_output.get('section_01_content', '')
if section1_content:
    section1_prompt = f"""{CHECKLIST}

FIELD: section_01_content

CONTENT TO REVIEW:
{section1_content}

Return JSON with: fixed_content, issues_fixed, fixes[]
If no issues, return original content unchanged with issues_fixed=0.
"""
    print("EXAMPLE 2: section_01_content Field Prompt")
    print("-" * 80)
    print(section1_prompt[:2000] + "..." if len(section1_prompt) > 2000 else section1_prompt)
    print()

# Now show full before/after comparison
print("=" * 80)
print("FULL BEFORE/AFTER COMPARISON")
print("=" * 80)
print()

content_fields = ['Intro', 'Direct_Answer', 'section_01_content', 'section_02_content', 'section_03_content']

for field in content_fields:
    before = stage2_output.get(field, '')
    after = stage2b_output.get(field, '')
    
    if before or after:
        print(f"\n{'='*80}")
        print(f"FIELD: {field}")
        print(f"{'='*80}")
        print(f"\n📝 STAGE 2 OUTPUT ({len(before)} chars, {len(before.split())} words):")
        print("-" * 80)
        print(before)
        print()
        print(f"\n✅ STAGE 2B OUTPUT ({len(after)} chars, {len(after.split())} words):")
        print("-" * 80)
        print(after)
        print()
        
        if before != after:
            print(f"🔍 CHANGES DETECTED:")
            print(f"  - Length: {len(before)} → {len(after)} chars")
            print(f"  - Words: {len(before.split())} → {len(after.split())} words")
            print()

# Save full audit report
audit_file = latest_dir / "full_audit_report.md"
with open(audit_file, 'w') as f:
    f.write("# Stage 2b Full Audit Report\n\n")
    f.write("## Full Checklist Prompt\n\n")
    f.write("```\n")
    f.write(CHECKLIST)
    f.write("\n```\n\n")
    f.write("## Example Prompts\n\n")
    f.write("### Intro Field\n\n")
    f.write("```\n")
    f.write(intro_prompt[:2000] + "..." if len(intro_prompt) > 2000 else intro_prompt)
    f.write("\n```\n\n")
    f.write("## Full Before/After Comparison\n\n")
    for field in content_fields:
        before = stage2_output.get(field, '')
        after = stage2b_output.get(field, '')
        if before or after:
            f.write(f"### {field}\n\n")
            f.write(f"**Stage 2 Output:**\n\n")
            f.write(f"{before}\n\n")
            f.write(f"**Stage 2b Output:**\n\n")
            f.write(f"{after}\n\n")
            f.write("---\n\n")

print(f"\n✅ Full audit report saved to: {audit_file}")

