#!/usr/bin/env python3
"""
GPT-4 Product Namer - Demo Version

This version shows the difference between mock and real results,
and helps you set up genuine GPT-4 API calls.

Usage:
    python gpt4_namer_demo.py --mock "product name"     # Mock results
    python gpt4_namer_demo.py --real "product name"     # Real GPT-4 calls
    python gpt4_namer_demo.py --setup                   # Setup API key
"""

import sys
import os
import argparse
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

def mock_gpt4_response(raw_product_name):
    """Mock responses for demonstration."""
    mock_responses = {
        "5.2 Channel. 140W 8K AV Receiver AVRS-670H": "Denon AVR-S670H – 8K 140W 5.2 Channel AV Receiver with HEOS",
        "SM58 Dynamic Vocal Microphone": "Shure SM58 – Dynamic Vocal Microphone",
        "K12.2 2000W 12-inch Powered Speaker": "QSC K12.2 – 2000W 12-inch Powered Speaker"
    }
    
    if raw_product_name in mock_responses:
        return mock_responses[raw_product_name]
    
    # Generate reasonable mock for unknown products
    if "receiver" in raw_product_name.lower():
        return f"Brand Model – AV Receiver with Features [MOCK]"
    elif "microphone" in raw_product_name.lower():
        return f"Brand Model – Microphone Type [MOCK]"
    elif "speaker" in raw_product_name.lower():
        return f"Brand Model – Speaker Type [MOCK]"
    else:
        return f"Brand Model – Audio Equipment [MOCK]"

def real_gpt4_response(raw_product_name):
    """Make real GPT-4 API call."""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key or api_key == 'your-openai-api-key-here':
        return None, "No valid API key found. Run with --setup to configure."
    
    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""You are an expert at creating product names for an audio equipment online store. Convert this technical product specification into a customer-friendly product name that follows store naming conventions.

NAMING GUIDELINES:
- Start with Brand and Model (e.g., "Denon AVR-S670H")
- Use proper formatting with dashes and descriptive text
- Include key specifications (channels, power, resolution, features)
- Make it searchable and customer-friendly
- Follow pattern: "Brand Model – Key Specs Product Type with Features"

EXAMPLES:
- "5.2 Channel. 140W 8K AV Receiver AVRS-670H" → "Denon AVR-S670H – 8K 140W 5.2 Channel AV Receiver with HEOS"
- "SM58 Dynamic Vocal Microphone" → "Shure SM58 – Dynamic Vocal Microphone"

PRODUCT TO CONVERT:
{raw_product_name}

Generate ONLY the store-friendly product name, nothing else:"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert product naming specialist for audio equipment stores."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip().strip('"\''), None
        
    except Exception as e:
        return None, f"API Error: {str(e)}"

def setup_api_key():
    """Interactive setup for OpenAI API key."""
    print("🔧 OpenAI API Key Setup")
    print("=" * 50)
    print()
    print("To use real GPT-4 calls, you need an OpenAI API key:")
    print("1. Go to: https://platform.openai.com/account/api-keys")
    print("2. Create a new API key")
    print("3. Copy the key (starts with 'sk-')")
    print()
    
    api_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
    
    if not api_key:
        print("Setup skipped. You can manually edit the .env file later.")
        return
    
    if not api_key.startswith('sk-'):
        print("⚠️  Warning: API key should start with 'sk-'")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Setup cancelled.")
            return
    
    # Update .env file
    env_path = Path(__file__).parent / '.env'
    env_content = f"""# OpenAI configuration for gpt4_namer.py
OPENAI_API_KEY={api_key}

# Note: Keep this key secure and never share it publicly
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"✅ API key saved to {env_path}")
    print("You can now use --real mode for genuine GPT-4 calls!")

def main():
    parser = argparse.ArgumentParser(description='GPT-4 Product Namer Demo')
    parser.add_argument('--mock', metavar='PRODUCT', help='Generate mock response')
    parser.add_argument('--real', metavar='PRODUCT', help='Generate real GPT-4 response')
    parser.add_argument('--setup', action='store_true', help='Setup OpenAI API key')
    parser.add_argument('--compare', metavar='PRODUCT', help='Compare mock vs real responses')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_api_key()
        return
    
    if args.mock:
        print("🎭 MOCK RESPONSE (Hardcoded)")
        print("=" * 50)
        result = mock_gpt4_response(args.mock)
        print(f"Input:  {args.mock}")
        print(f"Output: {result}")
        print("\n💡 This is a hardcoded response, not from GPT-4")
        
    elif args.real:
        print("🤖 REAL GPT-4 RESPONSE")
        print("=" * 50)
        result, error = real_gpt4_response(args.real)
        print(f"Input:  {args.real}")
        if error:
            print(f"Error:  {error}")
        else:
            print(f"Output: {result}")
            print("\n✅ This response was generated by GPT-4o")
            
    elif args.compare:
        print("🔄 MOCK vs REAL COMPARISON")
        print("=" * 50)
        
        # Mock response
        print("🎭 Mock Response:")
        mock_result = mock_gpt4_response(args.compare)
        print(f"   {mock_result}")
        print()
        
        # Real response
        print("🤖 Real GPT-4 Response:")
        real_result, error = real_gpt4_response(args.compare)
        if error:
            print(f"   Error: {error}")
        else:
            print(f"   {real_result}")
        print()
        
        if not error:
            print("📊 Analysis:")
            print(f"   Mock length: {len(mock_result)} characters")
            print(f"   Real length: {len(real_result)} characters")
            print(f"   Same result: {'Yes' if mock_result == real_result else 'No'}")
    
    else:
        parser.print_help()
        print("\nExamples:")
        print('  python gpt4_namer_demo.py --mock "5.2 Channel. 140W 8K AV Receiver AVRS-670H"')
        print('  python gpt4_namer_demo.py --real "5.2 Channel. 140W 8K AV Receiver AVRS-670H"')
        print('  python gpt4_namer_demo.py --compare "SM58 Dynamic Vocal Microphone"')
        print('  python gpt4_namer_demo.py --setup')

if __name__ == "__main__":
    main()
