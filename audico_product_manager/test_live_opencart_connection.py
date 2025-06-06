
#!/usr/bin/env python3
"""
Test script to verify OpenCart API connection with live data.
"""

import sys
import logging
from opencart_client import OpenCartAPIClient

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_opencart_connection():
    """Test the OpenCart API connection and search functionality."""
    print("Testing OpenCart API Connection...")
    print("=" * 50)
    
    try:
        # Initialize the client
        client = OpenCartAPIClient()
        print(f"✓ OpenCart client initialized")
        print(f"  Base URL: {client.base_url}")
        print(f"  Auth Token: {client.auth_token[:20]}...")
        
        # Test connection
        print("\n1. Testing connection...")
        if client.test_connection():
            print("✓ Connection test passed")
        else:
            print("✗ Connection test failed")
            return False
        
        # Test searching for "test" products (this worked in connection test)
        print("\n2. Testing search for 'test' products...")
        test_products = client.search_products("test")
        print(f"DEBUG: test_products type: {type(test_products)}")
        print(f"DEBUG: Found {len(test_products) if test_products else 0} test products")
        
        if test_products and len(test_products) > 0:
            print(f"✓ Found {len(test_products)} test products")
            # Show first 5 products
            for i, product in enumerate(test_products[:5]):
                if isinstance(product, dict):
                    print(f"  {i+1}. {product.get('name', 'N/A')} (Model: {product.get('model', 'N/A')})")
                else:
                    print(f"  {i+1}. {product}")
        else:
            print("✗ No test products found")
        
        # Test searching for "AVR" products (broader search)
        print("\n2b. Testing search for 'AVR' products...")
        avr_products_broad = client.search_products("AVR")
        if avr_products_broad:
            print(f"✓ Found {len(avr_products_broad)} AVR products")
            for i, product in enumerate(avr_products_broad[:3]):
                if isinstance(product, dict):
                    print(f"  {i+1}. {product.get('name', 'N/A')} (Model: {product.get('model', 'N/A')})")
        else:
            print("✗ No AVR products found")
        
        # Test searching for Denon products
        print("\n2c. Testing search for 'Denon' products...")
        denon_products = client.search_products("Denon")
        if denon_products:
            print(f"✓ Found {len(denon_products)} Denon products")
            for i, product in enumerate(denon_products[:3]):
                if isinstance(product, dict):
                    print(f"  {i+1}. {product.get('name', 'N/A')} (Model: {product.get('model', 'N/A')})")
        else:
            print("✗ No Denon products found")
        
        # Test searching for specific model
        print("\n3. Testing search for 'AVR-S540H'...")
        avr_products = client.search_products("AVR-S540H")
        print(f"DEBUG: avr_products type: {type(avr_products)}")
        print(f"DEBUG: avr_products content: {avr_products}")
        
        if avr_products:
            print(f"✓ Found {len(avr_products)} AVR-S540H products")
            # Handle both list and dict responses
            if isinstance(avr_products, list):
                products_to_show = avr_products
            else:
                products_to_show = [avr_products]  # Single product
            
            for i, product in enumerate(products_to_show):
                print(f"DEBUG: product type: {type(product)}, content: {product}")
                if isinstance(product, dict):
                    print(f"  {i+1}. {product.get('name', 'N/A')} (Model: {product.get('model', 'N/A')})")
                else:
                    print(f"  {i+1}. {product}")
        else:
            print("✗ No AVR-S540H products found")
        
        # Test get_product_by_model with an existing model
        print("\n4. Testing get_product_by_model for 'AVR-X1700H'...")
        specific_product = client.get_product_by_model("AVR-X1700H")
        if specific_product:
            print("✓ Found specific product:")
            print(f"  Name: {specific_product.get('name', 'N/A')}")
            print(f"  Model: {specific_product.get('model', 'N/A')}")
            print(f"  Price: {specific_product.get('price', 'N/A')}")
            print(f"  Product ID: {specific_product.get('product_id', 'N/A')}")
        else:
            print("✗ Specific product not found")
        
        # Test get_product_by_model with a non-existing model
        print("\n5. Testing get_product_by_model for 'AVR-S540H' (non-existing)...")
        non_existing_product = client.get_product_by_model("AVR-S540H")
        if non_existing_product:
            print("✓ Found product (unexpected):")
            print(f"  Name: {non_existing_product.get('name', 'N/A')}")
            print(f"  Model: {non_existing_product.get('model', 'N/A')}")
        else:
            print("✓ Correctly returned None for non-existing product")
        
        print("\n" + "=" * 50)
        print("✓ OpenCart API test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_opencart_connection()
    sys.exit(0 if success else 1)
