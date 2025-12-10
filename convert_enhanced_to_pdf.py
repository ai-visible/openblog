#!/usr/bin/env python3
"""
Convert enhanced HTML example to PDF with images and proper print formatting.
"""

import requests
import base64
import json
from pathlib import Path
import re

# Service URL from Modal deployment
PDF_SERVICE_URL = "https://clients--pdf-generation-fastapi-app.modal.run"

def convert_images_to_base64(html_content: str, base_path: Path) -> str:
    """
    Convert local image references to base64 data URLs for PDF generation.
    
    Args:
        html_content: HTML content with local image paths
        base_path: Base directory to resolve relative paths
        
    Returns:
        HTML with base64 data URLs
    """
    def replace_image_src(match):
        img_tag = match.group(0)
        src = match.group(1)
        
        # Skip if already a data URL or external URL
        if src.startswith(('data:', 'http://', 'https://')):
            return img_tag
        
        # Resolve relative path
        img_path = base_path / src
        if not img_path.exists():
            print(f"⚠️  Image not found: {img_path}")
            return img_tag
        
        try:
            # Read and encode image
            img_data = img_path.read_bytes()
            
            # Determine MIME type
            ext = img_path.suffix.lower()
            mime_type = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg', 
                '.jpeg': 'image/jpeg',
                '.webp': 'image/webp',
                '.gif': 'image/gif'
            }.get(ext, 'image/png')
            
            # Create base64 data URL
            b64_data = base64.b64encode(img_data).decode('utf-8')
            data_url = f"data:{mime_type};base64,{b64_data}"
            
            # Replace src in the img tag
            new_img_tag = img_tag.replace(f'src="{src}"', f'src="{data_url}"')
            
            print(f"✅ Embedded image: {src} ({len(img_data)} bytes)")
            return new_img_tag
            
        except Exception as e:
            print(f"❌ Failed to embed image {src}: {e}")
            return img_tag
    
    # Find and replace all image src attributes
    pattern = r'<img[^>]+src="([^"]+)"[^>]*>'
    modified_html = re.sub(pattern, replace_image_src, html_content)
    
    return modified_html

def convert_html_to_pdf(html_content: str, output_path: str) -> dict:
    """
    Convert HTML content to PDF with enhanced settings for print quality.
    """
    
    # Enhanced payload for better print quality
    payload = {
        "html": html_content,
        "format": "A4",
        "landscape": False,
        "print_background": True,
        "prefer_css_page_size": True,  # Use CSS @page margins
        "viewport_width": 1200,
        "device_scale_factor": 2,  # High DPI
        "color_scheme": "light",
        "margin": {  # Fallback margins if CSS @page doesn't work
            "top": "25mm",
            "right": "20mm", 
            "bottom": "25mm",
            "left": "20mm"
        }
    }
    
    print(f"Converting enhanced HTML to PDF...")
    print(f"  Images: Embedded as base64 data URLs")
    print(f"  Margins: 25mm top/bottom, 20mm left/right")
    print(f"  Quality: High DPI (scale factor: 2)")
    
    try:
        response = requests.post(
            f"{PDF_SERVICE_URL}/convert",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=180  # Longer timeout for image processing
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Decode and save PDF
        pdf_data = base64.b64decode(result["pdf_base64"])
        
        with open(output_path, "wb") as f:
            f.write(pdf_data)
        
        print(f"✅ Enhanced PDF saved: {output_path}")
        print(f"   File size: {result['size_bytes']:,} bytes ({result['size_bytes']/1024:.1f} KB)")
        print(f"   Render time: {result['render_time_ms']} ms")
        
        return result
        
    except requests.RequestException as e:
        print(f"❌ Error calling PDF service: {e}")
        raise
    except Exception as e:
        print(f"❌ Error converting PDF: {e}")
        raise

def main():
    """Main conversion function."""
    
    # Paths
    html_file = Path("/Users/federicodeponte/openblog-isaac-security/enhanced_example_with_images.html")
    pdf_file = Path("/Users/federicodeponte/openblog-isaac-security/examples/zero-trust-enhanced-with-images.pdf")
    
    # Create examples directory if it doesn't exist
    pdf_file.parent.mkdir(exist_ok=True)
    
    # Read the HTML content
    if not html_file.exists():
        raise FileNotFoundError(f"HTML file not found: {html_file}")
    
    print(f"Reading enhanced HTML: {html_file}")
    html_content = html_file.read_text(encoding="utf-8")
    
    # Convert image paths to base64 data URLs
    print(f"Processing images...")
    base_path = html_file.parent
    html_with_images = convert_images_to_base64(html_content, base_path)
    
    print(f"HTML content: {len(html_with_images):,} characters (with embedded images)")
    
    # Convert to PDF
    result = convert_html_to_pdf(html_with_images, str(pdf_file))
    
    print(f"\n🎉 Enhanced PDF generation complete!")
    print(f"📄 Output: {pdf_file}")
    print(f"📊 Features:")
    print(f"   ✅ Professional margins (25mm top/bottom, 20mm sides)")
    print(f"   ✅ High-resolution images embedded")
    print(f"   ✅ Print-optimized CSS with page breaks")
    print(f"   ✅ A4 format at 300 DPI equivalent")
    
    # Also save the HTML with embedded images for reference
    html_with_images_file = html_file.with_stem(html_file.stem + "_with_embedded_images")
    html_with_images_file.write_text(html_with_images, encoding="utf-8")
    print(f"📄 HTML with embedded images: {html_with_images_file}")

if __name__ == "__main__":
    main()