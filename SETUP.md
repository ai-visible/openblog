# Setup Guide: blog-writer

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required:
- `GOOGLE_API_KEY` - Google AI API key

Optional:
- `SUPABASE_URL` - For storage
- `SUPABASE_KEY` - For storage
- `REPLICATE_API_TOKEN` - For image generation

### 3. Verify Installation

```bash
# Run tests
pytest tests/ -v

# Check imports
python -c "from v2.core import WorkflowEngine; print('✅ Imports work!')"
```

## Project Structure

```
blog-writer/
├── pipeline/                    # Main code
│   ├── stages/           # 12 stages
│   ├── core/             # Core infrastructure
│   ├── models/           # Data models
│   ├── processors/       # Data processors
│   └── prompts/          # Prompt templates
├── tests/                # Test suite
└── docs/                 # Documentation
```

## Usage Example

```python
from v2.core import WorkflowEngine, ExecutionContext

# Create workflow
engine = WorkflowEngine()

# Create context
context = ExecutionContext(
    job_id="test-123",
    job_config={
        "primary_keyword": "AI adoption",
        "company_url": "https://example.com",
    },
)

# Execute
result = await engine.execute(context)

# Access result
print(result.final_article["Headline"])
```

## Next Steps

1. ✅ Repository created
2. ✅ Files migrated
3. ✅ Imports updated
4. ⚠️ Run tests to verify
5. ⚠️ Initialize git repository
6. ⚠️ Create entry point script

