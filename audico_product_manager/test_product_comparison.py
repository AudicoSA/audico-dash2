
#!/usr/bin/env python3
"""
Test script to verify product comparison with live OpenCart data.
"""

import sys
import logging
from opencart_client import OpenCartAPIClient
from product_comparison import ProductComparator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_product_comparison():
    """Test the product comparison functionality with live data."""
    print("Testing Product Comparison with Live OpenCart Data...")
    print("=" * 60)
    
    try:
        # Initialize OpenCart client
        print("1. Initializing OpenCart client...")
        opencart_client = OpenCartAPIClient()
        
        # Initialize Product Comparator
        print("2. Initializing Product Comparator...")
        comparator = ProductComparator(opencart_client)
        
        # Load existing products
        print("3. Loading existing products from OpenCart...")
        success = comparator.load_existing_products()
        if success:
            print(f"✓ Successfully loaded {len(comparator.existing_products)} existing products")
        else:
            print("✗ Failed to load existing products")
            return False
        
        # Show some existing products
        print("\n4. Sample existing products:")
        for i, product in enumerate(comparator.existing_products[:10]):
            print(f"  {i+1}. {product.get('name', 'N/A')} (Model: {product.get('model', 'N/A')})")
        
        # Look specifically for Denon products
        print("\n4b. Looking for Denon products in existing inventory:")
        denon_products = [p for p in comparator.existing_products if 'denon' in p.get('name', '').lower()]
        if denon_products:
            print(f"Found {len(denon_products)} Denon products:")
            for i, product in enumerate(denon_products):
                print(f"  {i+1}. {product.get('name', 'N/A')} (Model: {product.get('model', 'N/A')})")
        else:
            print("No Denon products found in existing inventory")
        
        # Test comparison with sample products
        print("\n5. Testing product comparison...")
        test_products = [
            {
                "name": "Denon AVR-X1700H Test Product",
                "model": "AVR-X1700H",
                "sku": "AVR-X1700H",
                "price": 18000,
                "description": "Test Denon receiver"
            },
            {
                "name": "New Product Test",
                "model": "NEW-MODEL-123",
                "sku": "NEW-MODEL-123", 
                "price": 5000,
                "description": "A completely new product"
            }
        ]
        
        matches = comparator.compare_products(test_products)
        
        print(f"\n6. Comparison Results:")
        for i, match in enumerate(matches):
            print(f"\n  Product {i+1}: {match.parsed_product.get('name', 'N/A')}")
            print(f"    Match Type: {match.match_type.value}")
            print(f"    Action: {match.action}")
            print(f"    Confidence: {match.confidence_score:.2%}")
            if match.existing_product:
                print(f"    Matched with: {match.existing_product.get('name', 'N/A')}")
            else:
                print(f"    No existing match found")
        
        # Generate summary
        summary = comparator.get_comparison_summary(matches)
        print(f"\n7. Summary:")
        print(f"    Total products: {summary.get('total_products', 0)}")
        print(f"    New products: {summary.get('new_products', 0)}")
        print(f"    Updates: {summary.get('updates', 0)}")
        print(f"    Exact matches: {summary.get('exact_matches', 0)}")
        
        print("\n" + "=" * 60)
        print("✓ Product comparison test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_product_comparison()
    sys.exit(0 if success else 1)
