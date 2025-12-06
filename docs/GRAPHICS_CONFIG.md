# Graphics Configuration System

The graphics generator now supports a **component-based, themeable system** that allows you to build custom graphics from JSON configuration.

## Overview

Instead of hardcoded templates, you can now:
- **Compose graphics** from reusable components
- **Customize themes** (colors, fonts, spacing) per business/client
- **Build any layout** by selecting and arranging components

## Quick Start

### Basic Example

```json
{
  "components": [
    {
      "type": "badge",
      "content": {
        "text": "Case Study",
        "icon": "case-study"
      }
    },
    {
      "type": "headline",
      "content": {
        "text": "Client achieved 10x growth",
        "size": "large",
        "bold_parts": ["Client", "10x growth"],
        "muted_parts": ["achieved"]
      }
    },
    {
      "type": "logo_card",
      "content": {
        "client_name": "TechCorp",
        "provider_name": "SCAILE"
      }
    }
  ]
}
```

### With Custom Theme

```json
{
  "theme": {
    "accent": "#ff6b6b",
    "accent_secondary": "#ee5a6f",
    "background": "#ffffff",
    "text_primary": "#1a1a1a"
  },
  "components": [
    {
      "type": "badge",
      "content": {"text": "Success Story", "icon": "case-study"}
    },
    {
      "type": "headline",
      "content": {"text": "Amazing Results", "size": "large"}
    }
  ]
}
```

## Available Components

### 1. Badge
Top badge/label component.

```json
{
  "type": "badge",
  "content": {
    "text": "Case Study",
    "icon": "case-study"  // or "process" or null
  }
}
```

### 2. Headline
Large headline text with optional styling.

```json
{
  "type": "headline",
  "content": {
    "text": "Amazing Results",
    "size": "small|medium|large|xlarge",  // default: "large"
    "align": "left|center|right",  // default: "center"
    "bold_parts": ["Amazing", "Results"],  // optional
    "muted_parts": []  // optional
  }
}
```

### 3. Quote Card
Testimonial/quote card with author info.

```json
{
  "type": "quote_card",
  "content": {
    "quote": "This platform transformed our workflow.",
    "author": "Jane Doe",
    "role": "CEO, StartupCo",
    "avatar": "https://...",  // optional image URL
    "emphasis": ["transformed"]  // optional parts to emphasize
  }
}
```

### 4. Metric Card
Statistics/metric display.

```json
{
  "type": "metric_card",
  "content": {
    "value": "10x",
    "label": "Growth Rate",
    "change": "+150% YoY",  // optional
    "change_type": "positive|negative"  // default: "positive"
  }
}
```

### 5. CTA Card
Call-to-action card.

```json
{
  "type": "cta_card",
  "content": {
    "headline": "Ready to Get Started?",
    "description": "Join hundreds of companies...",  // optional
    "button_text": "Get Started",
    "button_url": "https://..."  // optional
  }
}
```

### 6. Infographic Card
Process/steps display.

```json
{
  "type": "infographic_card",
  "content": {
    "title": "Our Process",
    "items": [
      "Step 1: Research",
      "Step 2: Analysis",
      "Step 3: Execution"
    ]
  }
}
```

### 7. Logo Card
Branding footer.

```json
{
  "type": "logo_card",
  "content": {
    "client_name": "Client Co",
    "provider_name": "SCAILE"
  }
}
```

## Theme Configuration

Customize colors, fonts, spacing, and more:

```json
{
  "theme": {
    // Colors
    "accent": "#6366f1",
    "accent_secondary": "#8b5cf6",
    "background": "#f8f8f8",
    "surface": "#ffffff",
    "text_primary": "#1a1a1a",
    "text_secondary": "#6b7280",
    "text_muted": "#b0b0b0",
    "border": "#e8e8e8",
    "border_light": "#f0f0f0",
    
    // Gradients
    "gradient_primary": "linear-gradient(135deg, #6366f1, #8b5cf6)",
    "gradient_text": "linear-gradient(135deg, #6366f1, #8b5cf6)",
    
    // Fonts
    "font_family": "'Inter', -apple-system, sans-serif",
    "font_headline": "800",
    "font_subheadline": "600",
    "font_body": "500",
    
    // Spacing
    "padding_large": "80px",
    "padding_medium": "60px",
    "padding_small": "40px",
    "gap_large": "50px",
    "gap_medium": "30px",
    "gap_small": "20px",
    
    // Border radius
    "radius_large": "28px",
    "radius_medium": "20px",
    "radius_small": "16px",
    "radius_pill": "100px",
    
    // Shadows
    "shadow_small": "0 1px 4px rgba(0,0,0,0.04)",
    "shadow_medium": "0 4px 12px rgba(99, 102, 241, 0.3)",
    
    // Grid pattern
    "grid_enabled": true,
    "grid_color": "rgba(0,0,0,0.025)",
    "grid_size": "20px"
  }
}
```

## API Usage

### Python

```python
from service.graphics_generator import GraphicsGenerator

generator = GraphicsGenerator()

config = {
    "theme": {"accent": "#ff6b6b"},
    "components": [
        {"type": "badge", "content": {"text": "Case Study"}},
        {"type": "headline", "content": {"text": "Amazing Results"}}
    ]
}

result = await generator.generate_from_config(config)
```

### HTTP API

```bash
curl -X POST https://your-api/generate-graphics-config \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "components": [
        {"type": "badge", "content": {"text": "Case Study"}},
        {"type": "headline", "content": {"text": "Amazing Results"}}
      ]
    }
  }'
```

## Examples

See `test_graphics_config.py` for complete examples including:
- Custom color themes
- Dark theme
- Complex multi-component layouts

## Benefits

✅ **Scalable**: Works for any business/client  
✅ **Flexible**: Compose any layout from components  
✅ **Themeable**: Custom colors, fonts, spacing per client  
✅ **Maintainable**: Single source of truth for components  
✅ **Backward Compatible**: Legacy API still works

