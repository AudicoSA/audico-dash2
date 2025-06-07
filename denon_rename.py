#!/usr/bin/env python3
"""
Denon Product Renamer - Processes Denon product data and generates store-friendly names.

This script reads Denon product data (from CSV, JSON, or text) and uses the GPT-4 namer
to generate proper store names for all products.

Usage:
    python denon_rename.py input.csv > output.csv
    python denon_rename.py --json input.json > output.json
    python denon_rename.py --text "product1\nproduct2\n..." > output.csv
"""

import sys
import os
import csv
import json
import argparse
from typing import List, Dict, Any
from io import StringIO

# Import our GPT-4 namer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from gpt4_namer import generate_store_name, get_openai_client

def process_csv_data(input_file: str) -> List[Dict[str, Any]]:
    """
    Process CSV data and generate store names.
    
    Args:
        input_file: Path to CSV file
        
    Returns:
        List of processed products with store names
    """
    products = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            # Try to detect CSV format
            sample = f.read(1024)
            f.seek(0)
            
            # Detect delimiter
            delimiter = ','
            if '\t' in sample:
                delimiter = '\t'
            elif ';' in sample:
                delimiter = ';'
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row in reader:
                # Extract product name from various possible column names
                raw_name = (
                    row.get('name') or 
                    row.get('product_name') or 
                    row.get('Name') or 
                    row.get('Product Name') or
                    row.get('description') or
                    row.get('Description') or
                    list(row.values())[0]  # First column as fallback
                )
                
                if raw_name and raw_name.strip():
                    products.append({
                        'original_data': row,
                        'raw_name': raw_name.strip(),
                        'store_name': None  # Will be filled by GPT-4
                    })
    
    except Exception as e:
        print(f"Error reading CSV: {str(e)}", file=sys.stderr)
        return []
    
    return products

def process_json_data(input_file: str) -> List[Dict[str, Any]]:
    """
    Process JSON data and generate store names.
    
    Args:
        input_file: Path to JSON file
        
    Returns:
        List of processed products with store names
    """
    products = []
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            # List of products
            for item in data:
                if isinstance(item, dict):
                    raw_name = (
                        item.get('name') or 
                        item.get('product_name') or
                        item.get('description') or
                        str(item)
                    )
                elif isinstance(item, str):
                    raw_name = item
                else:
                    raw_name = str(item)
                
                if raw_name and raw_name.strip():
                    products.append({
                        'original_data': item,
                        'raw_name': raw_name.strip(),
                        'store_name': None
                    })
        
        elif isinstance(data, dict):
            # Single product or nested structure
            if 'products' in data:
                return process_json_data_from_dict(data['products'])
            else:
                raw_name = (
                    data.get('name') or 
                    data.get('product_name') or
                    data.get('description') or
                    str(data)
                )
                
                if raw_name and raw_name.strip():
                    products.append({
                        'original_data': data,
                        'raw_name': raw_name.strip(),
                        'store_name': None
                    })
    
    except Exception as e:
        print(f"Error reading JSON: {str(e)}", file=sys.stderr)
        return []
    
    return products

def process_text_data(text_input: str) -> List[Dict[str, Any]]:
    """
    Process text data (one product per line) and generate store names.
    
    Args:
        text_input: Text with one product per line
        
    Returns:
        List of processed products with store names
    """
    products = []
    
    lines = text_input.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if line:
            products.append({
                'original_data': line,
                'raw_name': line,
                'store_name': None
            })
    
    return products

def generate_store_names(products: List[Dict[str, Any]], client) -> List[Dict[str, Any]]:
    """
    Generate store names for all products using GPT-4.
    
    Args:
        products: List of products to process
        client: OpenAI client
        
    Returns:
        List of products with generated store names
    """
    print(f"Processing {len(products)} products...", file=sys.stderr)
    
    for i, product in enumerate(products, 1):
        try:
            print(f"Processing {i}/{len(products)}: {product['raw_name'][:50]}...", file=sys.stderr)
            
            store_name = generate_store_name(product['raw_name'], client)
            product['store_name'] = store_name
            
            if store_name:
                print(f"  ✅ Generated: {store_name}", file=sys.stderr)
            else:
                print(f"  ❌ Failed to generate name", file=sys.stderr)
                product['store_name'] = product['raw_name']  # Fallback
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}", file=sys.stderr)
            product['store_name'] = product['raw_name']  # Fallback
    
    return products

def output_csv(products: List[Dict[str, Any]]):
    """Output results as CSV."""
    if not products:
        return
    
    fieldnames = ['raw_name', 'store_name']
    
    # Add original data fields if they exist
    if products[0]['original_data'] and isinstance(products[0]['original_data'], dict):
        original_fields = list(products[0]['original_data'].keys())
        fieldnames = original_fields + ['store_name']
    
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    
    for product in products:
        row = {}
        
        if isinstance(product['original_data'], dict):
            row.update(product['original_data'])
        else:
            row['raw_name'] = product['raw_name']
        
        row['store_name'] = product['store_name']
        writer.writerow(row)

def output_json(products: List[Dict[str, Any]]):
    """Output results as JSON."""
    result = []
    
    for product in products:
        item = {
            'raw_name': product['raw_name'],
            'store_name': product['store_name'],
            'original_data': product['original_data']
        }
        result.append(item)
    
    json.dump(result, sys.stdout, indent=2, ensure_ascii=False)

def create_sample_denon_data():
    """Create sample Denon data for testing."""
    sample_data = [
        "5.2 Channel. 140W 8K AV Receiver AVRS-670H",
        "5.2 Ch. 130W 8K AV Receiver with Bluetooth AVRX-580BT",
        "7.2 Channel 165W 8K AV Receiver AVRX-1700H",
        "9.2 Channel 125W 8K AV Receiver AVRX-2700H",
        "11.2 Channel 140W 8K AV Receiver AVRX-3700H",
        "5.1 Channel 100W AV Receiver AVRS-540BT",
        "7.1 Channel 145W AV Receiver AVRX-1600H"
    ]
    
    return sample_data

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Process Denon product data and generate store names')
    parser.add_argument('input', nargs='?', help='Input file (CSV/JSON) or use --sample for test data')
    parser.add_argument('--json', action='store_true', help='Input is JSON format')
    parser.add_argument('--text', help='Process text input directly')
    parser.add_argument('--sample', action='store_true', help='Use sample Denon data for testing')
    parser.add_argument('--output-json', action='store_true', help='Output as JSON instead of CSV')
    
    args = parser.parse_args()
    
    # Initialize OpenAI client
    try:
        client = get_openai_client()
    except SystemExit:
        print("Error: OpenAI API key not configured. Run 'python setup_openai_key.py' first.", file=sys.stderr)
        return 1
    
    # Process input
    products = []
    
    if args.sample:
        # Use sample data
        sample_data = create_sample_denon_data()
        products = process_text_data('\n'.join(sample_data))
        print(f"Using sample Denon data ({len(products)} products)", file=sys.stderr)
    
    elif args.text:
        # Process text input
        products = process_text_data(args.text)
    
    elif args.input:
        # Process file input
        if not os.path.exists(args.input):
            print(f"Error: File '{args.input}' not found", file=sys.stderr)
            return 1
        
        if args.json or args.input.endswith('.json'):
            products = process_json_data(args.input)
        else:
            products = process_csv_data(args.input)
    
    else:
        # Read from stdin
        text_input = sys.stdin.read()
        products = process_text_data(text_input)
    
    if not products:
        print("No products found to process", file=sys.stderr)
        return 1
    
    # Generate store names
    products = generate_store_names(products, client)
    
    # Output results
    if args.output_json:
        output_json(products)
    else:
        output_csv(products)
    
    print(f"\n✅ Processed {len(products)} products successfully", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
