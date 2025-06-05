
#!/usr/bin/env python3
"""
Test script to check raw API responses.
"""

import requests
import json

def test_raw_api():
    """Test the raw API response."""
    
    # Set up headers
    headers = {
        'Authorization': 'Basic b2NyZXN0YXBpX29hdXRoX2NsaWVudDpvY3Jlc3RhcGlfb2F1dGhfc2VjcmV0',
        'Content-Type': 'application/json'
    }
    
    # Test different search terms
    search_terms = ["", "test", "Denon", "AVR", "speaker"]
    
    for term in search_terms:
        print(f"\n{'='*50}")
        print(f"Testing search term: '{term}'")
        print(f"{'='*50}")
        
        url = f"https://www.audicoonline.co.za/index.php?route=ocrestapi/product/listing&search={term}"
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, headers=headers)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response keys: {list(data.keys())}")
                
                if 'products' in data:
                    products = data['products']
                    print(f"Number of products: {len(products)}")
                    
                    if products:
                        print("First product:")
                        first_product = products[0]
                        print(f"  Name: {first_product.get('name', 'N/A')}")
                        print(f"  Model: {first_product.get('model', 'N/A')}")
                        print(f"  Price: {first_product.get('price', 'N/A')}")
                        print(f"  Product ID: {first_product.get('product_id', 'N/A')}")
                    else:
                        print("No products found")
                else:
                    print("No 'products' key in response")
                    print(f"Full response: {json.dumps(data, indent=2)[:500]}...")
            else:
                print(f"Error response: {response.text[:200]}...")
                
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_raw_api()
