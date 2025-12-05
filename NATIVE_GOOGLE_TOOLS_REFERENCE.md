# Native Google Tools - Correct Implementation Reference

## 🚨 CRITICAL: Use Native Google Tools, Not Custom Fallbacks

The blog writer should use Google's **native grounding tools** which are 100% reliable. Custom fallbacks should only be used when native tools fail.

## ✅ Correct Google Search Tool Usage

```python
from google import genai
from google.genai import types

client = genai.Client()

grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Who won the euro 2024?",
    config=config,
)

print(response.text)
```

## ✅ Correct URL Context Tool Usage

```python
from google import genai
from google.genai.types import Tool, GenerateContentConfig

client = genai.Client()
model_id = "gemini-2.5-flash"

tools = [
  {"url_context": {}},
]

url1 = "https://www.foodnetwork.com/recipes/ina-garten/perfect-roast-chicken-recipe-1940592"
url2 = "https://www.allrecipes.com/recipe/21151/simple-whole-roast-chicken/"

response = client.models.generate_content(
    model=model_id,
    contents=f"Compare the ingredients and cooking times from the recipes at {url1} and {url2}",
    config=GenerateContentConfig(
        tools=tools,
    )
)

for each in response.candidates[0].content.parts:
    print(each.text)

# For verification, you can inspect the metadata to see which URLs the model retrieved
print(response.candidates[0].url_context_metadata)
```

## 🎯 Implementation Requirements

1. **Primary:** Use native Google tools (googleSearch + url_context) 
2. **Secondary:** Custom fallbacks ONLY when native tools fail
3. **Evidence:** Response should include `url_context_metadata` showing real URLs retrieved
4. **Verification:** Search Queries field should be populated with actual search terms

## 🚨 Current Problem

The blog writer appears to be:
- NOT using native Google tools correctly
- Falling back to custom implementations that hallucinate URLs
- Missing the `url_context_metadata` verification
- Not populating Search Queries field

## 🔧 Fix Required

Stage 2 content generation must be updated to:
1. Use the exact native tool patterns shown above
2. Verify `url_context_metadata` is populated
3. Log actual search queries being made
4. Only fallback to custom tools when native tools explicitly fail