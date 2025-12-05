#!/usr/bin/env python3
"""
Deep quality audit - manually inspect article and calculate AEO score breakdown.
"""

import json
import re
from pathlib import Path

# Load article output
with open("article_output_full.json", "r") as f:
    data = json.load(f)

article = data.get("validated_article", {})
quality_report = data.get("quality_report", {})
structured_data = data.get("structured_data", {})

print("=" * 80)
print("DEEP QUALITY AUDIT - MANUAL INSPECTION")
print("=" * 80)
print()

# Extract key content
headline = article.get("Headline", "")
intro = article.get("Intro", "")
direct_answer = article.get("Direct_Answer", "")
meta_title = article.get("Meta_Title", "")
meta_desc = article.get("Meta_Description", "")
sources = article.get("Sources", "")

print("1. HEADLINE & META")
print("-" * 80)
print(f"Headline: {headline}")
print(f"Length: {len(headline)} chars")
print()
print(f"Meta Title: {meta_title}")
print(f"Length: {len(meta_title)} chars {'⚠️ EXCEEDS 60' if len(meta_title) > 60 else '✅'}")
print()
print(f"Meta Description: {meta_desc}")
print(f"Length: {len(meta_desc)} chars {'⚠️ EXCEEDS 160' if len(meta_desc) > 160 else '✅'}")
print()

print("2. DIRECT ANSWER")
print("-" * 80)
if direct_answer:
    word_count = len(direct_answer.split())
    print(f"Direct Answer: {direct_answer[:200]}...")
    print(f"Word count: {word_count} {'✅' if 40 <= word_count <= 60 else '⚠️ OUT OF RANGE (40-60)'}")
    
    # Check for keyword
    keyword = "AI adoption in customer service"
    if keyword.lower() in direct_answer.lower():
        print("✅ Contains primary keyword")
    else:
        print("❌ Missing primary keyword")
    
    # Check for citation
    if re.search(r'\[1\]', direct_answer):
        print("✅ Contains citation [1]")
    else:
        print("❌ Missing citation [1]")
else:
    print("❌ NO DIRECT ANSWER")
print()

print("3. INTRO SECTION")
print("-" * 80)
if intro:
    intro_words = len(intro.split())
    print(f"Intro word count: {intro_words}")
    print(f"Preview: {intro[:300]}...")
    
    # Check paragraph length
    paragraphs = re.findall(r'<p[^>]*>([^<]+)</p>', intro)
    print(f"Paragraphs: {len(paragraphs)}")
    for i, para in enumerate(paragraphs[:3], 1):
        words = len(para.split())
        status = "✅" if words <= 50 else "⚠️" if words <= 100 else "❌"
        print(f"  Para {i}: {words} words {status}")
else:
    print("❌ NO INTRO")
print()

print("4. SECTIONS")
print("-" * 80)
sections_found = 0
total_words = 0
all_paragraphs = []
for i in range(1, 10):
    title = article.get(f"section_{i:02d}_title", "")
    content = article.get(f"section_{i:02d}_content", "")
    if title or content:
        sections_found += 1
        words = len(re.sub(r'<[^>]+>', '', content).split())
        total_words += words
        
        # Extract paragraphs
        paras = re.findall(r'<p[^>]*>([^<]+)</p>', content)
        all_paragraphs.extend(paras)
        
        print(f"Section {i}: {title}")
        print(f"  Words: {words}")
        print(f"  Paragraphs: {len(paras)}")
        if paras:
            para_words = [len(p.split()) for p in paras]
            avg_words = sum(para_words) / len(para_words)
            max_words = max(para_words)
            print(f"  Avg para length: {avg_words:.1f} words")
            print(f"  Max para length: {max_words} words {'⚠️' if max_words > 50 else '✅'}")
print()
print(f"Total sections: {sections_found}")
print(f"Total words: {total_words}")
print()

print("5. PARAGRAPH LENGTH ANALYSIS")
print("-" * 80)
if all_paragraphs:
    para_lengths = [len(p.split()) for p in all_paragraphs]
    avg_length = sum(para_lengths) / len(para_lengths)
    max_length = max(para_lengths)
    over_50 = sum(1 for w in para_lengths if w > 50)
    over_100 = sum(1 for w in para_lengths if w > 100)
    
    print(f"Total paragraphs: {len(all_paragraphs)}")
    print(f"Average length: {avg_length:.1f} words")
    print(f"Max length: {max_length} words")
    print(f"Paragraphs >50 words: {over_50} ({over_50/len(all_paragraphs)*100:.1f}%)")
    print(f"Paragraphs >100 words: {over_100} ({over_100/len(all_paragraphs)*100:.1f}%)")
    
    # Show examples of long paragraphs
    if over_50:
        print("\nLong paragraphs (>50 words):")
        for i, para in enumerate(all_paragraphs[:10], 1):
            words = len(para.split())
            if words > 50:
                preview = " ".join(para.split()[:15])
                print(f"  Para {i}: {words} words - {preview}...")
else:
    print("❌ NO PARAGRAPHS FOUND")
print()

print("6. CITATIONS")
print("-" * 80)
# Get all content
all_content = intro + " " + " ".join([article.get(f"section_{i:02d}_content", "") for i in range(1, 10)])

# Find citations
citations = re.findall(r'\[(\d+)\]', all_content)
citation_numbers = set(int(c) for c in citations)
print(f"Citation references found: {len(citations)}")
print(f"Unique citation numbers: {sorted(citation_numbers)}")

# Parse sources
if sources:
    source_lines = [s.strip() for s in sources.split('\n') if s.strip()]
    print(f"Sources listed: {len(source_lines)}")
    
    # Extract source numbers
    source_numbers = set()
    for line in source_lines:
        match = re.search(r'\[(\d+)\]', line)
        if match:
            source_numbers.add(int(match.group(1)))
    
    print(f"Source numbers: {sorted(source_numbers)}")
    
    # Check match
    if citation_numbers.issubset(source_numbers):
        print("✅ All citations have matching sources")
    else:
        missing = citation_numbers - source_numbers
        if missing:
            print(f"❌ Citations without sources: {sorted(missing)}")
        extra = source_numbers - citation_numbers
        if extra:
            print(f"⚠️ Sources without citations: {sorted(extra)}")
    
    # Check citation distribution
    paragraphs = re.findall(r'<p[^>]*>.*?</p>', all_content, re.DOTALL)
    paras_with_citations = sum(1 for para in paragraphs if re.search(r'\[\d+\]', para))
    paras_with_2plus = sum(1 for para in paragraphs if len(re.findall(r'\[\d+\]', para)) >= 2)
    
    print(f"\nCitation distribution:")
    print(f"  Paragraphs with citations: {paras_with_citations}/{len(paragraphs)} ({paras_with_citations/len(paragraphs)*100:.1f}%)")
    print(f"  Paragraphs with 2+ citations: {paras_with_2plus}/{len(paragraphs)} ({paras_with_2plus/len(paragraphs)*100:.1f}%)")
    print(f"  Target: 60%+ paragraphs with 2+ citations")
else:
    print("❌ NO SOURCES")
print()

print("7. FAQ/PAA")
print("-" * 80)
faq_items = article.get("faq_items", [])
paa_items = article.get("paa_items", [])

print(f"FAQ items: {len(faq_items) if isinstance(faq_items, list) else 0}")
if isinstance(faq_items, list) and faq_items:
    for i, faq in enumerate(faq_items[:3], 1):
        q = faq.get("question", "")[:60]
        print(f"  FAQ {i}: {q}...")

print(f"PAA items: {len(paa_items) if isinstance(paa_items, list) else 0}")
if isinstance(paa_items, list) and paa_items:
    for i, paa in enumerate(paa_items[:3], 1):
        q = paa.get("question", "")[:60]
        print(f"  PAA {i}: {q}...")
print()

print("8. NATURAL LANGUAGE PATTERNS")
print("-" * 80)
all_text = re.sub(r'<[^>]+>', '', all_content).lower()

conversational_phrases = [
    "how to", "what is", "why does", "when should", "where can",
    "you can", "you should", "let's", "here's", "this is",
    "how can", "what are", "how do", "why should", "where are",
]
phrase_count = sum(1 for phrase in conversational_phrases if phrase in all_text)
print(f"Conversational phrases: {phrase_count}")

question_patterns = ["what is", "how do", "why does", "when should", "where can", "how can", "what are"]
question_count = sum(1 for pattern in question_patterns if re.search(pattern, all_text))
print(f"Question patterns: {question_count}")

direct_patterns = ["is ", "are ", "does ", "provides ", "enables ", "allows ", "helps "]
direct_count = sum(1 for pattern in direct_patterns if re.search(pattern, all_text))
print(f"Direct statements: {direct_count}")
print()

print("9. STRUCTURED DATA")
print("-" * 80)
list_count = all_content.count("<ul>") + all_content.count("<ol>")
h2_count = all_content.count("<h2>")
h3_count = all_content.count("<h3>")

print(f"Lists (ul/ol): {list_count}")
print(f"H2 headings: {h2_count}")
print(f"H3 headings: {h3_count}")
print()

print("10. AEO SCORE BREAKDOWN (MANUAL CALCULATION)")
print("-" * 80)
print("Based on AEOScorer logic:")
print()

# Direct Answer (25 points)
direct_answer_score = 0.0
if direct_answer:
    direct_answer_score += 10.0
    word_count = len(direct_answer.split())
    if 40 <= word_count <= 60:
        direct_answer_score += 5.0
    elif 30 <= word_count < 40 or 60 < word_count <= 80:
        direct_answer_score += 2.5
    
    keyword = "AI adoption in customer service"
    if keyword.lower() in direct_answer.lower():
        direct_answer_score += 5.0
    
    if re.search(r'\[1\]', direct_answer):
        direct_answer_score += 5.0
print(f"1. Direct Answer: {direct_answer_score:.1f}/25")

# Q&A Format (20 points)
qa_score = 0.0
faq_count = len(faq_items) if isinstance(faq_items, list) else 0
paa_count = len(paa_items) if isinstance(paa_items, list) else 0

if faq_count >= 5:
    qa_score += 10.0
elif faq_count >= 3:
    qa_score += 7.0
elif faq_count > 0:
    qa_score += 3.0

if paa_count >= 3:
    qa_score += 5.0
elif paa_count >= 2:
    qa_score += 3.0
elif paa_count > 0:
    qa_score += 1.0

# Question headers
sections = [article.get(f"section_{i:02d}_title", "") for i in range(1, 10)]
question_headers = sum(1 for title in sections if title and any(q in title.lower() for q in ["what is", "how does", "why does", "when should", "where can", "what are", "how can"]))
if question_headers >= 2:
    qa_score += 5.0
elif question_headers >= 1:
    qa_score += 2.5

print(f"2. Q&A Format: {qa_score:.1f}/20 (FAQ: {faq_count}, PAA: {paa_count}, Question headers: {question_headers})")

# Citation Clarity (15 points)
citation_score = 0.0
if citations:
    citation_score += 5.0
    
    if sources and citation_numbers.issubset(source_numbers):
        citation_score += 5.0
    elif citation_numbers & source_numbers:
        citation_score += 2.5
    
    # Distribution
    if paragraphs:
        distribution_ratio = paras_with_2plus / len(paragraphs)
        if distribution_ratio >= 0.6:
            citation_score += 5.0
        elif distribution_ratio >= 0.4:
            citation_score += 3.0
        elif distribution_ratio >= 0.2:
            citation_score += 1.0

print(f"3. Citation Clarity: {citation_score:.1f}/15")

# Natural Language (15 points)
natural_score = 0.0
if phrase_count >= 8:
    natural_score += 6.0
elif phrase_count >= 5:
    natural_score += 4.0
elif phrase_count >= 2:
    natural_score += 2.0

vague_patterns = ["might be", "could be", "possibly", "perhaps", "maybe"]
vague_count = sum(1 for pattern in vague_patterns if re.search(pattern, all_text))
if direct_count > vague_count * 2:
    natural_score += 5.0
elif direct_count > vague_count:
    natural_score += 3.0
elif direct_count > 0:
    natural_score += 1.0

if question_count >= 5:
    natural_score += 4.0
elif question_count >= 3:
    natural_score += 3.0
elif question_count >= 1:
    natural_score += 1.5

print(f"4. Natural Language: {natural_score:.1f}/15")

# Structured Data (10 points)
structured_score = 0.0
if list_count >= 3:
    structured_score += 5.0
elif list_count >= 1:
    structured_score += 2.5

if h2_count >= 3 and h3_count >= 2:
    structured_score += 5.0
elif h2_count >= 2:
    structured_score += 2.5

print(f"5. Structured Data: {structured_score:.1f}/10")

# E-E-A-T (15 points) - likely 0 without input_data
eat_score = 0.0
print(f"6. E-E-A-T: {eat_score:.1f}/15 (no input_data provided)")

total_score = direct_answer_score + qa_score + citation_score + natural_score + structured_score + eat_score
print()
print(f"TOTAL AEO SCORE: {total_score:.1f}/100")
print(f"Reported AEO Score: {quality_report.get('metrics', {}).get('aeo_score', 0)}/100")
print()

print("=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)

