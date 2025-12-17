#!/usr/bin/env python3
"""
Generate secure API keys for OpenBlog API authentication
"""

import secrets
import string
from datetime import datetime

def generate_api_key(length: int = 32, prefix: str = "ob_") -> str:
    """Generate a secure API key with optional prefix."""
    # Use URL-safe characters (no special chars that might cause issues)
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}{key}"

def generate_multiple_keys(count: int = 3) -> list:
    """Generate multiple API keys for different environments/users."""
    keys = []
    environments = ["prod", "staging", "dev"] if count <= 3 else [f"key{i+1}" for i in range(count)]
    
    for i, env in enumerate(environments[:count]):
        key = generate_api_key(prefix=f"ob_{env}_")
        keys.append({
            "environment": env,
            "key": key,
            "generated_at": datetime.now().isoformat()
        })
    
    return keys

if __name__ == "__main__":
    print("🔑 OpenBlog API Key Generator")
    print("=" * 40)
    
    # Generate 3 keys for different environments
    keys = generate_multiple_keys(3)
    
    # Display keys
    for key_info in keys:
        print(f"\n{key_info['environment'].upper()} API Key:")
        print(f"  {key_info['key']}")
    
    # Generate environment variable format
    all_keys = [k["key"] for k in keys]
    env_value = ",".join(all_keys)
    
    print(f"\n📝 Environment Variable:")
    print(f"OPENBLOG_API_KEYS=\"{env_value}\"")
    
    print(f"\n🔒 Security Notes:")
    print(f"  - Keys are cryptographically secure (256-bit entropy)")
    print(f"  - Store in environment variables, not code")
    print(f"  - Each key can be used independently")
    print(f"  - Generated at: {datetime.now().isoformat()}")
    
    print(f"\n📋 Usage Examples:")
    print(f"  curl -H \"Authorization: Bearer {keys[0]['key']}\" ...")
    print(f"  curl -H \"X-API-Key: {keys[0]['key']}\" ...")