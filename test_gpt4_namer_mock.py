#!/usr/bin/env python3
"""
Mock test of GPT-4 namer to demonstrate expected behavior.

This shows what the output should look like when the API key is properly configured.
"""

def mock_gpt4_response(raw_product_name):
    """
    Mock GPT-4 responses for testing the naming logic.
    
    This simulates what GPT-4 would return for common product types.
    """
    
    # Mock responses based on your exact example and similar patterns
    mock_responses = {
        "5.2 Channel. 140W 8K AV Receiver AVRS-670H": "Denon AVR-S670H – 8K 140W 5.2 Channel AV Receiver with HEOS",
        "5.2 Ch. 130W 8K AV Receiver with Bluetooth AVRX-580BT": "Denon AVR-X580BT – 5.2 Channel AV Receiver 130W 8K Bluetooth",
        "SM58 Dynamic Vocal Microphone": "Shure SM58 – Dynamic Vocal Microphone",
        "K12.2 2000W 12-inch Powered Speaker": "QSC K12.2 – 2000W 12-inch Powered Speaker",
        "CDJ-3000 Professional Multi Player": "Pioneer CDJ-3000 – Professional DJ Media Player",
        "C414 XLS Large Diaphragm Condenser": "AKG C414 XLS – Large Diaphragm Condenser Microphone"
    }
    
    # Return exact match if available
    if raw_product_name in mock_responses:
        return mock_responses[raw_product_name]
    
    # Generate a reasonable mock response for unknown products
    if "av receiver" in raw_product_name.lower() or "receiver" in raw_product_name.lower():
        return f"Brand Model – AV Receiver with Features (Mock: {raw_product_name[:30]}...)"
    elif "microphone" in raw_product_name.lower() or "mic" in raw_product_name.lower():
        return f"Brand Model – Microphone Type (Mock: {raw_product_name[:30]}...)"
    elif "speaker" in raw_product_name.lower():
        return f"Brand Model – Speaker Type (Mock: {raw_product_name[:30]}...)"
    else:
        return f"Brand Model – Audio Equipment (Mock: {raw_product_name[:30]}...)"

def test_naming_examples():
    """Test the naming with your exact example and other common cases."""
    
    test_cases = [
        "5.2 Channel. 140W 8K AV Receiver AVRS-670H",
        "5.2 Ch. 130W 8K AV Receiver with Bluetooth AVRX-580BT", 
        "SM58 Dynamic Vocal Microphone",
        "K12.2 2000W 12-inch Powered Speaker",
        "CDJ-3000 Professional Multi Player"
    ]
    
    print("=== GPT-4 Namer Mock Test Results ===")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        result = mock_gpt4_response(test_case)
        print(f"{i}. Input:  {test_case}")
        print(f"   Output: {result}")
        print()
    
    print("✅ Mock test completed successfully!")
    print()
    print("To use with real GPT-4:")
    print("1. Run: python setup_openai_key.py")
    print("2. Then: python gpt4_namer.py \"5.2 Channel. 140W 8K AV Receiver AVRS-670H\"")

if __name__ == "__main__":
    test_naming_examples()
