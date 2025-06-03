from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import requests
import json
import logging
from datetime import datetime
import base64

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenCart API configuration
OPENCART_BASE_URL = os.getenv('OPENCART_BASE_URL', 'https://www.audicoonline.co.za/index.php?route=ocrestapi')
OPENCART_USERNAME = os.getenv('OPENCART_USERNAME', 'admin')
OPENCART_PASSWORD = os.getenv('OPENCART_PASSWORD', 'admin')

if OPENCART_USERNAME == 'admin' and OPENCART_PASSWORD == 'admin':
    logger.warning("Using default OpenCart credentials (admin/admin). Set OPENCART_USERNAME and OPENCART_PASSWORD in .env.")

# Application statistics
app_stats = {
    'products_processed': 0,
    'successful_uploads': 0,
    'failed_uploads': 0,
    'last_sync': None,
    'total_products': 0
}

# Default "Load" category if the API call fails
default_category = {
    'category_id': '967',
    'name': 'Load',
    'status': '1'
}


def get_api_headers():
    auth_string = base64.b64encode(f"{OPENCART_USERNAME}:{OPENCART_PASSWORD}".encode()).decode()
    return {
        'Authorization': f'Basic {auth_string}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }


def make_api_request(method, endpoint, data=None, params=None):
    headers = get_api_headers()
    url = f"{OPENCART_BASE_URL}/{endpoint}"

    try:
        logger.info(f"Making {method} request to: {url}")
        if data:
            logger.info(f"Request data: {json.dumps(data, indent=2)}")

        response = requests.request(method, url, headers=headers, json=data, params=params, timeout=30)

        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response text: {response.text[:500]}")

        return {
            'status_code': response.status_code,
            'data': response.json() if response.headers.get('Content-Type') == 'application/json' else response.text,
            'success': response.status_code in [200, 201]
        }

    except Exception as e:
        logger.error(f"HTTP request error: {str(e)}")
        return {'error': str(e), 'success': False}


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'Audico Product Manager API',
            'version': '3.0.0',
            'opencart_configured': OPENCART_USERNAME != 'admin'
        }
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Return application statistics"""
    return jsonify({
        'success': True,
        'data': {
            'status': 'connected',
            'products_processed': app_stats['products_processed'],
            'successful_uploads': app_stats['successful_uploads'],
            'failed_uploads': app_stats['failed_uploads'],
            'last_sync': app_stats['last_sync'],
            'total_products': app_stats['total_products'],
            'opencart_status': 'ready'
        }
    })


@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Test OpenCart API connection"""
    try:
        logger.info("Testing OpenCart API connection...")

        # Test with a simple product listing call
        api_result = make_api_request('GET', 'product/listing', params={'limit': 1})

        if api_result.get('success'):
            return jsonify({
                'success': True,
                'data': {
                    'status': 'connected',
                    'message': 'OpenCart API connection successful',
                    'url': OPENCART_BASE_URL,
                    'preview': api_result['data']
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f"OpenCart API connection failed: {api_result.get('error', 'Unknown error')}",
                'data': {
                    'status': 'error',
                    'url': OPENCART_BASE_URL,
                    'status_code': api_result.get('status_code')
                }
            })

    except Exception as e:
        logger.error(f"Connection test error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Connection test error: {str(e)}',
            'data': {
                'status': 'error'
            }
        })


@app.route('/api/get-categories', methods=['GET'])
def get_categories():
    """
    Returns a fixed category ('Load', category_id=967) without querying OpenCart.
    """
    logger.info("Returning default 'Load' category (ID 967) without querying OpenCart.")
    return jsonify({
        'success': True,
        'data': {
            'categories': [default_category]
        },
        'message': 'Default Load category (ID 967) returned intentionally.'
    })


@app.route('/api/create-product', methods=['POST'])
def create_product():
    """Create product using OpenCart API"""
    try:
        data = request.json
        logger.info(f"Creating product with data: {data}")

        # OpenCart API product structure
        product_data = {
            "name": data.get('name', ''),
            "model": data.get('sku', data.get('model', '')),
            "price": str(data.get('price', 0)),
            "quantity": str(data.get('stock', data.get('quantity', 0))),
            "status": "1",  # Active
            "description": data.get('description', ''),
            "meta_title": data.get('name', ''),
            "category_id": data.get('category_id', '967'),  # Default to Load category
            "weight": str(data.get('weight', 0))
        }

        logger.info(f"Sending product data: {json.dumps(product_data, indent=2)}")

        api_result = make_api_request('POST', 'create-product', data=product_data)

        if api_result.get('success'):
            result_data = api_result['data']

            # Update statistics
            app_stats['products_processed'] += 1
            app_stats['successful_uploads'] += 1
            app_stats['total_products'] += 1
            app_stats['last_sync'] = datetime.now().isoformat()

            return jsonify({
                'success': True,
                'data': {
                    'message': 'Product created successfully in OpenCart',
                    'product_id': result_data.get('product_id') if isinstance(result_data, dict) else None,
                    'response': result_data
                }
            })
        else:
            app_stats['failed_uploads'] += 1

            return jsonify({
                'success': False,
                'error': f'Failed to create product: {api_result.get("error", "Unknown error")}',
                'data': {
                    'status_code': api_result.get('status_code'),
                    'response': api_result.get('data')
                }
            })

    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        app_stats['failed_uploads'] += 1

        return jsonify({
            'success': False,
            'error': f'Error creating product: {str(e)}'
        })


@app.route('/api/process-pricelist', methods=['POST'])
def process_pricelist():
    """Process uploaded pricelist file"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            })

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            })

        logger.info(f"Processing pricelist file: {file.filename}")

        # For now, return a success message
        # You can integrate Document AI processing here later
        app_stats['last_sync'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'data': {
                'message': f'File {file.filename} received successfully',
                'filename': file.filename,
                'note': 'File processing functionality can be enhanced with Document AI'
            }
        })

    except Exception as e:
        logger.error(f"Error processing pricelist: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        })


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Audico Product Manager API Starting...")
    print("=" * 60)
    print(f"OpenCart API URL: {OPENCART_BASE_URL}")
    print(f"Username: {OPENCART_USERNAME}")
    print(f"Password: {'Configured' if OPENCART_PASSWORD != 'admin' else 'NOT CONFIGURED'}")
    print("=" * 60)

    app.run(debug=True, port=5000, host='0.0.0.0')