
from flask import Flask, render_template, request, jsonify, redirect, url_for
import requests
import json
import logging
import sys
import os
from datetime import datetime
import base64

# Add the product manager path to import the OpenCart client
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(project_root, 'audico_product_manager'))

try:
    from audico_product_manager.opencart_client import OpenCartAPIClient
except ImportError:
    from opencart_client import OpenCartAPIClient

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OpenCart API configuration
OPENCART_API_URL = os.getenv('OPENCART_API_URL', 'http://localhost:5000')

@app.route('/')
def dashboard():
    """Main dashboard page."""
    return render_template('dashboard.html')

@app.route('/api/test-connection')
def test_connection():
    """Test connection to OpenCart API."""
    try:
        response = requests.get(f'{OPENCART_API_URL}/test-connection', timeout=10)
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection test failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Connection failed: {str(e)}'
        }), 500

@app.route('/api/categories')
def get_categories():
    """Get categories from OpenCart API."""
    try:
        response = requests.get(f'{OPENCART_API_URL}/categories', timeout=10)
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get categories: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get categories: {str(e)}'
        }), 500

@app.route('/api/products')
def get_products():
    """Get products from OpenCart API."""
    try:
        limit = request.args.get('limit', 100)
        page = request.args.get('page', 1)
        
        response = requests.get(
            f'{OPENCART_API_URL}/products',
            params={'limit': limit, 'page': page},
            timeout=10
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get products: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to get products: {str(e)}'
        }), 500

@app.route('/api/products', methods=['POST'])
def create_product():
    """Create a new product via OpenCart API."""
    try:
        data = request.get_json()
        
        response = requests.post(
            f'{OPENCART_API_URL}/products',
            json=data,
            timeout=10
        )
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to create product: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Failed to create product: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
