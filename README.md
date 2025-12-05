# blog-writer

**AI-powered blog article generation system** - Stages-based architecture implementing the v4.1 n8n workflow in Python.

## 🎯 Overview

This is a complete rewrite of the blog writing system using a **12-stage pipeline architecture** that mirrors the v4.1 n8n workflow. Each stage is modular, testable, and follows clear separation of concerns.

## ✨ Features

- ✅ **12-Stage Pipeline**: Complete implementation of all stages (0-11)
- ✅ **v4.1 Workflow Parity**: Matches the n8n workflow exactly
- ✅ **Modular Design**: Each stage is independent and testable
- ✅ **Comprehensive Tests**: All stages have full test coverage
- ✅ **AEO Optimization**: Built-in quality checks and scoring
- ✅ **Auto-Detection**: Automatically detects company info from URL
- ✅ **Multi-language Support**: Supports multiple languages

## 📋 Stages Overview

### Sequential Stages (0-3)
- **Stage 0**: Data Fetch & Auto-Detection
- **Stage 1**: Prompt Construction
- **Stage 2**: Gemini Content Generation (with tools)
- **Stage 3**: Structured Data Extraction

### Parallel Stages (4-9)
- **Stage 4**: Citations Validation & Formatting
- **Stage 5**: Internal Links Generation
- **Stage 6**: Table of Contents Generation
- **Stage 7**: Metadata Calculation
- **Stage 8**: FAQ/PAA Validation & Enhancement
- **Stage 9**: Image Generation

### Sequential Stages (10-11)
- **Stage 10**: Cleanup & Validation
- **Stage 11**: HTML Generation & Storage

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd blog-writer

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Basic Usage

```python
from v2.core import WorkflowEngine, ExecutionContext

# Create workflow engine
engine = WorkflowEngine()

# Create execution context
context = ExecutionContext(
    job_id="test-123",
    job_config={
        "primary_keyword": "AI adoption in customer service",
        "company_url": "https://example.com",
    },
)

# Run workflow
result = await engine.execute(context)

# Access final article
article = result.final_article
print(article["Headline"])
```

## 📁 Project Structure

```
blog-writer/
├── pipeline/                          # Main code
│   ├── blog_generation/         # Blog generation (12 stages)
│   ├── core/                    # Core infrastructure
│   ├── models/                  # Data models
│   ├── processors/              # Data processors
│   ├── prompts/                 # Prompt templates
│   └── config.py               # Configuration
├── tests/                       # Test suite
│   └── stages/                  # Stage tests
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md         # Architecture details
│   ├── ROADMAP.md              # Implementation roadmap
│   └── STAGES_REVIEW.md        # Stages review
└── requirements.txt            # Dependencies
```

## 🔧 Configuration

### Required Environment Variables

- `GOOGLE_API_KEY`: Google AI API key (required)

### Optional Environment Variables

- `SUPABASE_URL`: Supabase URL (for storage)
- `SUPABASE_KEY`: Supabase key (for storage)
- `REPLICATE_API_TOKEN`: Replicate API token (for image generation)

## 📖 Documentation

- **[Architecture](docs/ARCHITECTURE.md)**: Complete architecture documentation
- **[Roadmap](docs/ROADMAP.md)**: Implementation roadmap
- **[Quick Reference](docs/QUICK_REFERENCE.md)**: Quick reference card
- **[Input Requirements](docs/INPUT_REQUIREMENTS.md)**: Input data requirements
- **[Stages Review](docs/STAGES_REVIEW.md)**: Complete stages review

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific stage tests
pytest tests/stages/test_stage_00.py -v

# Run with coverage
pytest tests/ --cov=v2 --cov-report=html
```

## 📊 Status

**Completion**: ✅ **100%** (12/12 stages implemented)

All stages are implemented, tested, and ready for production use.

## 🔄 Migration from blog-writer

This is a complete rewrite focusing on:
- Clean, modular architecture
- Stages-based pipeline
- Better testability
- Clear separation of concerns

See [MIGRATION_PLAN.md](MIGRATION_PLAN.md) for details.

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

