# Environment Variables Setup

## How Environment Variables Are Loaded

The code checks for environment variables in this order:

1. **`.env.local`** (checked first) - Local development overrides
2. **`.env`** (fallback) - Default environment file
3. **System environment variables** - If neither file exists

## Setup Instructions

### Option 1: Create `.env.local` (Recommended for Local Development)

```bash
cd blog-writer
cp .env.local.example .env.local
# Edit .env.local and add your API key
```

**Content of `.env.local`:**
```bash
GOOGLE_API_KEY=your_actual_api_key_here
# OR use GOOGLE_GEMINI_API_KEY instead
```

### Option 2: Create `.env` (Alternative)

```bash
cd blog-writer
cp .env.local.example .env
# Edit .env and add your API key
```

### Option 3: Export in Shell (Temporary)

```bash
export GOOGLE_API_KEY=your_actual_api_key_here
python3 test_local_blog_generation.py
```

## Code That Loads Environment Variables

### Test Scripts (`test_local_blog_generation.py`, `test_parity.py`)

```python
env_local = Path(__file__).parent / ".env.local"
if env_local.exists():
    load_dotenv(env_local)  # Loads .env.local first
else:
    load_dotenv()  # Falls back to .env
```

### API Service (`service/api.py`)

```python
load_dotenv()  # Loads .env by default
# Note: For production, use system environment variables or .env
```

### Core Config (`pipeline/config.py`)

```python
load_dotenv()  # Loads .env
# Then reads: os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_GEMINI_API_KEY")
```

## Required Variables

### Minimum Required
- `GOOGLE_API_KEY` OR `GOOGLE_GEMINI_API_KEY` - Google AI API key

### Optional (for full functionality)
- `SUPABASE_URL` - For storage (Stage 11)
- `SUPABASE_KEY` - For storage (Stage 11)
- `REPLICATE_API_TOKEN` - For image generation (Stage 9)

## Verification

Check if your API key is loaded:

```bash
# Test if .env.local exists and has API key
cd blog-writer
test -f .env.local && echo "✅ .env.local exists" || echo "❌ .env.local not found"
grep -q "GOOGLE_API_KEY\|GOOGLE_GEMINI_API_KEY" .env.local 2>/dev/null && echo "✅ API key found" || echo "❌ API key not found"
```

Or test in Python:

```python
import os
from dotenv import load_dotenv
load_dotenv('.env.local')  # or load_dotenv() for .env
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
print("✅ API key found" if api_key else "❌ API key not found")
```

## Security Note

⚠️ **Never commit `.env.local` or `.env` to git!**

These files should be in `.gitignore`:
```
.env
.env.local
.env*.local
```

## For Testing

Once `.env.local` is set up with your API key:

```bash
# Test local execution
python3 test_local_blog_generation.py

# Test API service (in another terminal)
cd service
python api.py

# Test parity
python3 test_parity.py
```

