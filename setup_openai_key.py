#!/usr/bin/env python3
"""
Setup script to configure OpenAI API key for the GPT-4 namer.

Run this script to set up your OpenAI API key:
    python setup_openai_key.py
"""

import os
import sys

def setup_openai_key():
    """Interactive setup for OpenAI API key."""
    
    print("=== OpenAI API Key Setup ===")
    print()
    print("To use the GPT-4 naming functionality, you need an OpenAI API key.")
    print("You can get one from: https://platform.openai.com/account/api-keys")
    print()
    
    # Check if key already exists
    existing_key = os.getenv('OPENAI_API_KEY')
    if existing_key and existing_key != "your_openai_api_key_here":
        print(f"Found existing API key: {existing_key[:8]}...")
        use_existing = input("Use existing key? (y/n): ").lower().strip()
        if use_existing == 'y':
            return existing_key
    
    # Get new key from user
    api_key = input("Enter your OpenAI API key: ").strip()
    
    if not api_key:
        print("No API key provided. Exiting.")
        return None
    
    # Create .env file
    env_path = "/home/ubuntu/workspace/audico-dash2/.env"
    
    # Read existing .env if it exists
    env_content = ""
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.read()
    
    # Update or add OPENAI_API_KEY
    lines = env_content.split('\n')
    updated = False
    
    for i, line in enumerate(lines):
        if line.startswith('OPENAI_API_KEY='):
            lines[i] = f'OPENAI_API_KEY={api_key}'
            updated = True
            break
    
    if not updated:
        lines.append(f'OPENAI_API_KEY={api_key}')
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"API key saved to {env_path}")
    
    # Set environment variable for current session
    os.environ['OPENAI_API_KEY'] = api_key
    
    return api_key

def test_api_key(api_key):
    """Test the API key with a simple request."""
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Say 'API key works!'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ API key test successful: {result}")
        return True
        
    except Exception as e:
        print(f"❌ API key test failed: {str(e)}")
        return False

if __name__ == "__main__":
    api_key = setup_openai_key()
    
    if api_key:
        print("\nTesting API key...")
        if test_api_key(api_key):
            print("\n🎉 Setup complete! You can now use the GPT-4 namer:")
            print('    python gpt4_namer.py "5.2 Channel. 140W 8K AV Receiver AVRS-670H"')
        else:
            print("\n⚠️  API key test failed. Please check your key and try again.")
    else:
        print("\nSetup cancelled.")
