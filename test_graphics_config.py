#!/usr/bin/env python3
"""
Test script for JSON config-based graphics generation.
Demonstrates the new component-based, themeable system.
"""

import asyncio
import sys
import base64
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from service.graphics_generator import GraphicsGenerator
from service.graphics_components import Theme


async def test_config_based_graphics():
    """Test graphics generation from JSON config."""
    print("🎨 Testing JSON Config-Based Graphics Generation")
    print("=" * 70)
    
    generator = GraphicsGenerator()
    
    # Example 1: Custom theme (red accent)
    print("\n📝 Test 1: Custom Theme (Red Accent)")
    print("-" * 70)
    
    config_red = {
        "theme": {
            "accent": "#ff6b6b",
            "accent_secondary": "#ee5a6f",
            "gradient_primary": "linear-gradient(135deg, #ff6b6b, #ee5a6f)",
            "gradient_text": "linear-gradient(135deg, #ff6b6b, #ee5a6f)",
        },
        "components": [
            {
                "type": "badge",
                "content": {"text": "Success Story", "icon": "case-study"}
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
    
    result1 = await generator.generate_from_config(config_red)
    if result1.success:
        if result1.image_url.startswith('data:image'):
            header, encoded = result1.image_url.split(',', 1)
            image_data = base64.b64decode(encoded)
            output_path = Path.home() / "Desktop" / "test_config_red.png"
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"✅ Generated! Saved to: {output_path}")
    
    # Example 2: Dark theme
    print("\n📝 Test 2: Dark Theme")
    print("-" * 70)
    
    config_dark = {
        "theme": {
            "background": "#1a1a1a",
            "surface": "#2a2a2a",
            "text_primary": "#ffffff",
            "text_secondary": "#b0b0b0",
            "text_muted": "#666666",
            "border": "#333333",
            "border_light": "#2a2a2a",
        },
        "components": [
            {
                "type": "badge",
                "content": {"text": "Case Study", "icon": "case-study"}
            },
            {
                "type": "quote_card",
                "content": {
                    "quote": "This platform transformed our workflow completely.",
                    "author": "Jane Doe",
                    "role": "CEO, StartupCo",
                    "emphasis": ["transformed", "completely"]
                }
            },
            {
                "type": "logo_card",
                "content": {
                    "client_name": "StartupCo",
                    "provider_name": "SCAILE"
                }
            }
        ]
    }
    
    result2 = await generator.generate_from_config(config_dark)
    if result2.success:
        if result2.image_url.startswith('data:image'):
            header, encoded = result2.image_url.split(',', 1)
            image_data = base64.b64decode(encoded)
            output_path = Path.home() / "Desktop" / "test_config_dark.png"
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"✅ Generated! Saved to: {output_path}")
    
    # Example 3: Complex composition
    print("\n📝 Test 3: Complex Composition")
    print("-" * 70)
    
    config_complex = {
        "theme": {
            "accent": "#10b981",
            "accent_secondary": "#059669",
            "gradient_primary": "linear-gradient(135deg, #10b981, #059669)",
        },
        "components": [
            {
                "type": "badge",
                "content": {"text": "Process", "icon": "process"}
            },
            {
                "type": "headline",
                "content": {
                    "text": "Our 4-Step Approach",
                    "size": "medium",
                    "align": "center"
                }
            },
            {
                "type": "infographic_card",
                "content": {
                    "title": "Content Pipeline",
                    "items": [
                        "Research & Analysis",
                        "AI Content Generation",
                        "Quality Review",
                        "Publication & Distribution"
                    ]
                }
            },
            {
                "type": "logo_card",
                "content": {
                    "client_name": "Client",
                    "provider_name": "SCAILE"
                }
            }
        ]
    }
    
    result3 = await generator.generate_from_config(config_complex)
    if result3.success:
        if result3.image_url.startswith('data:image'):
            header, encoded = result3.image_url.split(',', 1)
            image_data = base64.b64decode(encoded)
            output_path = Path.home() / "Desktop" / "test_config_complex.png"
            with open(output_path, 'wb') as f:
                f.write(image_data)
            print(f"✅ Generated! Saved to: {output_path}")
            import subprocess
            subprocess.run(['open', str(output_path)])
    
    print("\n" + "=" * 70)
    print("✅ Testing complete!")
    print("📁 Check your Desktop for generated graphics")


if __name__ == "__main__":
    asyncio.run(test_config_based_graphics())

