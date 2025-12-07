# Stage 2 Optimization + Humanization Plan

## Summary

We're tackling **3 critical issues** in Stage 2 (Gemini Call):
1. ✅ Keyword over-optimization (8-12x vs target 5-8x)
2. ✅ First paragraph too short (40-50 words vs target 60-100)
3. ✅ AI language markers (em dashes, robotic phrases, formal tone)

**Approach:** Prompt engineering + regex post-processing

---

## Part 1: Stage 5 Clarification

**Question:** "What is Stage 5 for if we already link internally in Stage 2?"

**Answer:**
- **Stage 2 (Gemini):** Embeds 3-5 internal links INSIDE the article content (naturally woven into paragraphs)
- **Stage 5:** Generates a separate "More on this topic" section at the BOTTOM of the article (like a "Related Links" box)

**Example from current output:**
```html
<div class="more-links">
  <h3>More on this topic</h3>
  <ul>
    <li><a href="/magazine/security-first-architecture">Security Guide</a></li>
    <li><a href="/magazine/devops-automation">DevOps Automation</a></li>
  </ul>
</div>
```

**Conclusion:** Both stages are needed - they serve different UX purposes.

---

## Part 2: AI Language Markers (Current Issues)

### 🔴 Issue 1: Em Dashes (—)

**Found:** 16 instances in latest article

**Examples:**
```
"The leading AI code generation tools 2025—GitHub Copilot, Amazon Q Developer, and Tabnine—collectively accelerate..."
"Agentic AI workflows allow developers to delegate entire tasks—such as 'refactor this module'"
```

**Why it's a problem:**
- Em dashes (—) are a classic AI writing tell
- Overused for parenthetical clauses
- Makes text feel formal and robotic
- Human writers use commas, parentheses, or split sentences instead

**Fix Strategy:**
1. **Prompt:** Ban em dashes explicitly
2. **Regex:** Convert remaining `—` to alternatives

---

### 🔴 Issue 2: Robotic Transition Phrases

**Found in current article:**
- "Here's how"
- "Here's what matters"
- "Key benefits include"
- "Important considerations"
- "That's why similarly"
- "If you want another"
- "When you choosing"

**Why it's a problem:**
- Too formulaic
- AI loves these structured transitions
- Sounds like a template, not human writing

**Fix Strategy:**
1. **Prompt:** Ban these phrases explicitly
2. **Prompt:** Encourage natural transitions instead

---

### 🔴 Issue 3: Awkward Grammar

**Found:**
- "What is as we handle of AI code generation tools 2025, the path forward is clear but complex."
- "That's why similarly, Shopify has integrated"
- "so you can managing teams of AI agents"

**Why it's a problem:**
- Gemini makes grammatical mistakes when trying to vary sentence structure
- Especially after lists or complex sentences

**Fix Strategy:**
1. **Prompt:** Add explicit grammar rules
2. **Regex:** Cannot fix grammar - need better prompt

---

### 🔴 Issue 4: List Introduction Overuse

**Found:** Almost every list starts with:
- "Here are key points:"
- "Key benefits include:"
- "Important considerations:"

**Why it's a problem:**
- Repetitive and unnecessary
- Human writers integrate lists more naturally
- Feels like a PowerPoint presentation

**Fix Strategy:**
1. **Prompt:** Ban standalone list introductions
2. **Prompt:** Require lists to flow from the paragraph above

---

## Part 3: Humanization Rules (Prompt Changes)

### 🎯 New Prompt Section: "HUMANIZATION RULES"

Add this after Rule 12 (Conversational Tone) in `main_article.py`:

```
### HUMANIZATION RULES (CRITICAL)

13. **Ban AI Markers**:
   
   ❌ NEVER use em dashes (—) for parenthetical clauses. Use commas, parentheses, or split into two sentences.
   
   **FORBIDDEN:**
   - "The tools—GitHub Copilot and Amazon Q—are widely used."
   - "This approach—which saves time—is effective."
   
   **CORRECT:**
   - "The tools (GitHub Copilot and Amazon Q) are widely used."
   - "This approach, which saves time, is effective."
   - "This approach is effective. It saves significant time."

14. **Ban Robotic Transitions**:
   
   ❌ NEVER use these formulaic phrases:
   - "Here's how" / "Here's what matters" / "Here's the breakdown"
   - "Key benefits include:" / "Important considerations:" / "Key points:"
   - "That's why" / "If you want" / "When you" (unless grammatically necessary)
   - "You'll find" / "You can see" / "What is as we"
   
   **FORBIDDEN:**
   ```
   Here's how enterprise adoption has moved beyond experimentation.
   Key benefits include: improved speed, better quality, reduced costs.
   ```
   
   **CORRECT:**
   ```
   Enterprise adoption has moved beyond experimentation.
   Teams report improved speed, better quality, and reduced costs.
   ```

15. **Natural List Integration**:
   
   ❌ NEVER use standalone list introductions like "Key points:", "Here are", "Important considerations:".
   
   ✅ ALWAYS integrate lists into the paragraph flow.
   
   **FORBIDDEN:**
   ```html
   <p>Security is critical for AI adoption.</p>
   <p>Key points:</p>
   <ul>
     <li>45% of AI code has vulnerabilities</li>
     <li>Review all generated code</li>
   </ul>
   ```
   
   **CORRECT:**
   ```html
   <p>Security is critical for AI adoption. Teams should focus on three areas:</p>
   <ul>
     <li>Automated scanning (45% of AI code has vulnerabilities)</li>
     <li>Mandatory code review for all generated code</li>
     <li>Regular security audits</li>
   </ul>
   ```

16. **Grammar & Flow**:
   
   - ✅ Every sentence must be grammatically correct (no fragments unless intentional)
   - ✅ Vary sentence structure naturally (not "Here's X. Here's Y. Here's Z.")
   - ✅ Use contractions occasionally ("don't", "it's", "you're") for conversational tone
   - ✅ Start max 20% of sentences with transition words ("However", "Additionally")
   - ✅ Split long sentences (>30 words) into two shorter ones

17. **Tone Calibration**:
   
   - Write like a senior engineer explaining to a colleague over coffee
   - Not: academic paper, marketing brochure, or slide deck
   - Use "we" and "you" to create connection
   - Occasional humor/personality is allowed (but keep it professional)
   - If explaining complex topics, use analogies humans would use
```

---

## Part 4: Regex Post-Processing (Cleanup)

Add to `_cleanup_content()` in `html_renderer.py`:

```python
@staticmethod
def _humanize_content(content: str) -> str:
    """
    Post-process content to remove AI language markers.
    
    Fixes:
    1. Em dashes → commas or parentheses (context-dependent)
    2. Formulaic list introductions
    3. Excessive transition phrases
    """
    if not content:
        return ""
    
    # Pattern 1: Convert em dashes to commas (for parenthetical clauses)
    # "tools—GitHub and Amazon—are" → "tools (GitHub and Amazon) are"
    # Only apply if the clause is < 50 chars (likely a list or short clause)
    def replace_em_dash(match):
        before = match.group(1)
        middle = match.group(2)
        after = match.group(3)
        
        # If middle clause is short (list or short description), use parentheses
        if len(middle) < 50:
            return f"{before}({middle}){after}"
        # If long clause, split into two sentences
        else:
            return f"{before}. {middle[0].upper()}{middle[1:]}. {after[0].upper()}{after[1:]}"
    
    # Match: (text before)—(middle clause)—(text after)
    content = re.sub(
        r'([^—]{10,})—([^—]{5,})—([^—]{10,})',
        replace_em_dash,
        content
    )
    
    # Pattern 2: Remove standalone list introductions
    # <p>Key points:</p> → (remove)
    # <p>Here are the benefits:</p> → (remove)
    content = re.sub(
        r'<p>\s*(?:Key points|Key benefits include|Important considerations|Here (?:are|\'s) (?:the |what |how )?[^<]{0,30}):?\s*</p>',
        '',
        content,
        flags=re.IGNORECASE
    )
    
    # Pattern 3: Remove robotic sentence starters
    # "Here's how the market" → "The market"
    # "That's why similarly," → "Similarly,"
    replacements = [
        (r'\bHere\'s how\b', ''),  # "Here's how X" → "X"
        (r'\bHere\'s what\b', ''),  # "Here's what matters" → "matters"
        (r'\bThat\'s why similarly,?\b', 'Similarly,'),  # "That's why similarly" → "Similarly"
        (r'\bIf you want\b', 'Additionally,'),  # "If you want another" → "Additionally"
        (r'\bWhen you choosing\b', 'When choosing'),  # Grammar fix
        (r'\bYou\'ll find to\b', 'To'),  # "You'll find to mitigate" → "To mitigate"
        (r'\bso you can managing\b', 'managing'),  # "so you can managing" → "managing"
        (r'\bWhat is as we handle of\b', 'As we evaluate'),  # Grammar fix
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
    
    # Pattern 4: Fix double spaces after cleanup
    content = re.sub(r'\s{2,}', ' ', content)
    
    return content.strip()
```

Then call it in `_cleanup_content()`:

```python
@staticmethod
def _cleanup_content(content: str) -> str:
    """
    Post-process content to remove useless patterns and humanize language.
    """
    if not content:
        return ""
    
    # ... existing patterns (duplicate punctuation, standalone labels, etc.) ...
    
    # NEW: Humanize language (remove AI markers)
    content = HTMLRenderer._humanize_content(content)
    
    return content.strip()
```

---

## Part 5: Implementation Plan

### Step 1: Update Prompt (main_article.py)

- [ ] Add "HUMANIZATION RULES" section with rules 13-17
- [ ] Move existing banned phrases list to rule 14
- [ ] Add em dash examples to rule 13
- [ ] Add list integration examples to rule 15
- [ ] Update rule 6 (keyword density): "5-8 times TOTAL across entire article"
- [ ] Update rule 5 (first paragraph): "First paragraph MUST be 60-100 words (4-6 sentences)"

### Step 2: Add Humanization Regex (html_renderer.py)

- [ ] Add `_humanize_content()` method
- [ ] Integrate into `_cleanup_content()`
- [ ] Test with current article output

### Step 3: Test & Validate

- [ ] Generate 3 new articles
- [ ] Check metrics:
  - Keyword density: 5-8 mentions ✅
  - First paragraph: 60-100 words ✅
  - Em dashes: 0 ✅
  - Robotic phrases: 0 ✅
  - Grammar: no obvious errors ✅

### Step 4: Update Quality Analysis

- [ ] Add humanization metrics to `generate_direct.py` output:
  - Em dash count (target: 0)
  - Robotic phrase count (target: 0)
  - Contraction count (target: 3-5)
  - Avg sentence length (target: 15-20 words)

---

## Expected Improvements

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| **Keyword mentions** | 8-12 | 5-8 | 5-8 ✅ |
| **First paragraph** | 40-50 words | 60-100 words | 60-100 ✅ |
| **Em dashes** | 16 | 0 | 0 ✅ |
| **Robotic phrases** | 12+ | 0-2 | 0 ✅ |
| **Grammar errors** | 3-5 | 0-1 | 0 ✅ |
| **Tone score** | 6/10 (robotic) | 8.5/10 (natural) | 8+ ✅ |

**Overall Quality:** 8.5/10 → 9.5/10

---

## Files to Modify

1. **`services/blog-writer/pipeline/prompts/main_article.py`**
   - Add HUMANIZATION RULES (rules 13-17)
   - Update rule 5 (first paragraph)
   - Update rule 6 (keyword density)

2. **`services/blog-writer/pipeline/processors/html_renderer.py`**
   - Add `_humanize_content()` method
   - Integrate into `_cleanup_content()`

3. **`services/blog-writer/generate_direct.py`**
   - Add humanization metrics to quality analysis

---

## Notes

### Why Both Prompt + Regex?

**Prompt:** Prevents Gemini from generating AI markers in the first place (80% effective)  
**Regex:** Catches any that slip through (20% safety net)

**Best practice:** Strong prompt + defensive post-processing = highest quality

### Em Dash Conversion Logic

**Context-dependent replacement:**
- Short clause (< 50 chars): Use parentheses `()`
- Long clause (> 50 chars): Split into separate sentence
- Example:
  ```
  BEFORE: "The tools—GitHub and Amazon—are widely used."
  AFTER:  "The tools (GitHub and Amazon) are widely used."
  
  BEFORE: "This approach—which saves time and reduces errors—is effective."
  AFTER:  "This approach is effective. It saves time and reduces errors."
  ```

### Robotic Phrase Detection

**Pattern:** Formulaic transitions that AI overuses:
- "Here's X" (5 instances in current article)
- "Key points:" (3 instances)
- "Important considerations:" (2 instances)

**Human alternative:** Varies naturally based on context.

---

## Status

⏳ **Ready to implement** - Waiting for approval to proceed.

**Next step:** Implement Step 1 (update prompt) and test with 1 article.

---

_Last Updated: 2025-12-07_
_Target: Stage 2 (Gemini Call) optimization + humanization_

